import sys
import os
from textwrap import dedent

from tf.app import use
from tf.core.helpers import initTree, xmlEsc, unexpanduser as ux

from lib import (
    ORG,
    REPO,
    VERSION_TF,
    TF_DIR,
    ENTITY_TF,
    ENTITY_MOD,
    XMLOUT_DIR,
)

HELP = """

Convert TF to simplified TEI including the named entities, if present.

python3 xmlFromTf.py [version] [--help]

--help: print this text and exit

version: the tf data version to use as input.
         If left out, the most recent version will be chosen.

The result ends up in directory

/xmlout/version

of this repo, and is filled with files 01.xml, ..., 14.xml,
one file for each volume.
"""


HEADER_FEATURES = """
    page
    title
    rawdate
    seq
    place
    year
    month
    day
    author
    authorFull
""".strip().split()

ATTS_PROTO = dict(
    page=["n"],
    note=[("mark", "n")],
    remark=[("", "resp", "#editor")],
    folio=[("", "type", "folio")],
    cell=[("col", "n"), ("x", "rend", "offset-")],
    row=[("row", "n")],
)
ATTS = {
    elem: [
        (att, att, None) if type(att) is str else (*att, None) if len(att) == 2 else att
        for att in atts
    ]
    for (elem, atts) in ATTS_PROTO.items()
}

RENAME_PROTO = dict(
    page=("", "pb"),
    line=("", "lb"),
    para="p",
    head="opener",
    subhead="head",
    remark="note",
    folio="ref",
)
RENAME = {
    orig: (newName, newName) if type(newName) is str else newName
    for (orig, newName) in RENAME_PROTO.items()
}

NO_NEWLINE_BEFORE = set(
    """
    folio
    line
""".strip().split()
)

NO_NEWLINE_AFTER = set(
    """
    folio
""".strip().split()
)


class Convert:
    def __init__(self, version):
        self.good = True
        self.literal = False

        tfInDir = f"{TF_DIR}/{version}"

        if not os.path.isdir(tfInDir):
            print(f"No TF input in in version {version}")
            self.good = False
            return

        entityTfDir = f"{ENTITY_TF}/{version}"

        doEntities = os.path.exists(entityTfDir)
        doEntitiesRep = "WITH" + ("" if doEntities else "OUT") + " entities"

        mods = dict(mod=f"{ENTITY_MOD}:clone") if doEntities else {}

        print(f"Converting TF version {version} to XML {doEntitiesRep}")

        A = use(
            f"{ORG}/{REPO}:clone",
            checkout="clone",
            **mods,
            version=version,
            silent="terse",
        )
        self.A = A
        self.destDir = f"{XMLOUT_DIR}/{A.version}"

    def doLetter(self, letter, literal=None):
        """Convert individual letter to XML.

        Note on entities.
        Every word that is part of an entity will be wrapped in `<e>` elements
        separately. This is because we cannot guarantees that entities respect
        boundaries of other elements.
        The `eid` attribute can be used to string entity words that belong to the
        same entity together.
        """
        if not self.good:
            return

        if literal is not None:
            self.literal = literal

        literal = self.literal

        A = self.A
        N = A.api.N
        L = A.api.L
        F = A.api.F
        Fs = A.api.Fs

        header = []

        pNest = 0
        cellNest = 0
        hasP = False
        allNest = 0
        inExtraP = False
        elemStack = []

        for feat in HEADER_FEATURES:
            value = xmlEsc(Fs(feat).v(letter))
            header.append(f"""<interp type="{feat}">{value}</interp>""")

        header = "\n".join(header)

        body = []

        for (node, boundary) in N.walk(nodes=L.d(letter), events=True):
            trans = F.trans.v(node) or ""
            punc = F.punc.v(node) or ""

            if boundary is None:
                entityId = F.entityId.v(node) or ""
                entityKind = F.entityKind.v(node) or ""
                if entityId or entityKind:
                    eBefore = f"""<name key="{entityId}" type="{entityKind}">"""
                    eAfter = """</name>"""
                else:
                    eBefore = ""
                    eAfter = ""
                if allNest == 0:
                    if not inExtraP and (trans + punc).strip():
                        body.append("<p>")
                        inExtraP = True
                trans = xmlEsc(trans)
                if F.isnum.v(node):
                    trans = f'<num type="numerator">{trans}</num>'
                elif F.isden.v(node):
                    trans = f'<num type="denominator">{trans}</num>'
                elif F.isq.v(node):
                    trans = f'<num type="fraction">{trans}</num>'
                elif F.isemph.v(node):
                    trans = f"<emph>{trans}</emph>"
                elif F.issub.v(node):
                    trans = f'<hi rend="sub">{trans}</hi>'
                elif F.issuper.v(node):
                    trans = f'<hi rend="super">{trans}</hi>'
                elif F.isund.v(node):
                    trans = f'<hi rend="underline">{trans}</hi>'
                elif F.isref.v(node):
                    trans = f"<ref>{trans}</ref>"
                elif F.isspecial.v(node):
                    trans = f"<distinct>{trans}</distinct>"
                body.append(f"{eBefore}{trans}{eAfter}{xmlEsc(punc)}")
            else:
                elem = F.otype.v(node)
                (elemStartOut, elemEndOut) = (
                    (elem, elem) if literal else RENAME.get(elem, (elem, elem))
                )
                if boundary and not elemStartOut or not boundary and elemStartOut:
                    attStr = ""
                    for (attName, attNameOut, attValue) in ATTS.get(elem, []):
                        if attValue is None:
                            attValue = Fs(attName).v(node)
                        elif attValue.endswith("-"):
                            rawValue = Fs(attName).v(node)
                            attValue = (
                                None if rawValue is None else f"{attValue}{rawValue}"
                            )
                        if attValue is not None:
                            attStr += (
                                f' {attName if literal else attNameOut}="{attValue}"'
                            )
                if boundary:
                    newLine = "" if elem in NO_NEWLINE_AFTER else "\n"
                    if literal or elemStartOut:
                        if cellNest and elemEndOut == "head":
                            elemEndOut = "label"
                        elemOutRep = f"</{elemEndOut}>"
                        allNest -= 1
                        if elemEndOut == "p":
                            pNest -= 1
                        elif elemEndOut == "cell":
                            cellNest -= 1
                        elemStack.pop()
                    else:
                        if elemEndOut == "lb" and elemStack and elemStack[-1] == "row":
                            elemOutRep = ""
                            newLine = ""
                        else:
                            elemOutRep = f"<{elemEndOut}{attStr}/>"
                    body.append(f"{elemOutRep}{newLine}")
                    if elemEndOut == "ref":
                        if pNest == 0:
                            body.append("</p>\n")
                else:
                    newLine = "" if elem in NO_NEWLINE_BEFORE else "\n"
                    if literal or elemStartOut:
                        if cellNest and elemStartOut == "head":
                            elemStartOut = "label"
                        elemOutRep = f"<{elemStartOut}{attStr}>"
                        if allNest == 0 and inExtraP:
                            body.append("</p>\n")
                            inExtraP = False
                        allNest += 1
                        if elemEndOut == "p":
                            pNest += 1
                            hasP = True
                        elif elemEndOut == "cell":
                            cellNest += 1
                        elemStack.append(elemStartOut)
                    else:
                        elemOutRep = ""
                    if elemEndOut == "ref":
                        if pNest == 0:
                            body.append("<p>")
                    body.append(f"{newLine}{elemOutRep}")

        if not hasP:
            body.append("<p/>")

        body = "".join(body)

        return dedent(
            """\
        <text>
        {}
        <body>
        {}
        </body>
        </text>
        """
        ).format(header, body)

    def doVolume(self, v, literal=None):
        if not self.good:
            return

        if literal is not None:
            self.literal = literal

        A = self.A
        L = A.api.L

        title = A.sectionStrFromNode(v)

        destDir = self.destDir
        destFile = f"{destDir}/{title}.xml"

        letters = L.d(v, otype="letter")
        letterText = "\n\n".join(self.doLetter(letter) for letter in letters)

        xml = dedent(
            """\
        <TEI xmlns="http://www.tei-c.org/ns/1.0">
        <teiHeader>
            <fileDesc>
                <titleStmt>
                    <title>Generale Missieven, volume {}</title>
                </titleStmt>
                <publicationStmt>
                    <p>More info on https://github.com/CLARIAH/wp6-missieven
                       and https://github.com/cltl/voc-missives
                   </p>
                </publicationStmt>
                <sourceDesc>
                    <p>Text and markup of General Missieven,
                       after extensive cleaning of structure,
                       still with many OCR errors,
                       and with named entities marked.
                    </p>
                    <p>The structure cleaning has been carried out by Dirk Roorda,
                       and the result is delivered as a text-fabric dataset.
                    </p>
                    <p>The named entities are marked by means of a workflow
                       carried out by Sophie Arnoult, and the results are delivered
                       as text-fabric features.
                    </p>
                    <p>The combination of cleaned text and entities have been converted
                       to this TEI-XML by means of a program.
                    </p>
                </sourceDesc>
            </fileDesc>
        </teiHeader>
        {}
        </TEI>
        """
        ).format(title, letterText)

        with open(destFile, "w") as fh:
            fh.write(xml)
        print(f"volume {title} => {ux(destFile)}")

    def doWork(self, literal=None):
        if not self.good:
            return

        if literal is not None:
            self.literal = literal

        A = self.A
        F = A.api.F

        destDir = self.destDir
        initTree(destDir, fresh=True, gentle=True)

        for v in F.otype.s("volume"):
            self.doVolume(v)


def main():
    args = () if len(sys.argv) == 1 else tuple(sys.argv[1:])
    version = VERSION_TF if len(args) == 0 else args[0]

    if "--help" in args:
        print(HELP)
        return True

    CV = Convert(version)
    CV.doWork()


if __name__ == "__main__":
    sys.exit(main())
