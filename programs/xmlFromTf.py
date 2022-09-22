import sys
import os
from textwrap import dedent

from tf.app import use
from tf.core.helpers import initTree, htmlEsc

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
)
ATTS = {
    elem: [(att, att) if type(att) is str else att for att in atts]
    for (elem, atts) in ATTS_PROTO.items()
}

RENAME = dict(
    page="pb",
    line="lb",
    para="p",
    note="mark",
    head="opener",
)

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


def convertLetter(A, letter):
    """Convert individual letter to XML.

    Note on entities.
    Every word that is part of an entity will be wrapped in `<e>` elements
    separately. This is because we cannot guarantees that entities respect
    boundaries of other elements.
    The `eid` attribute can be used to string entity words that belong to the
    same entity together.
    """
    N = A.api.N
    L = A.api.L
    F = A.api.F
    Fs = A.api.Fs
    header = []
    for feat in HEADER_FEATURES:
        value = htmlEsc(Fs(feat).v(letter))
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
            body.append(f"{eBefore}{trans}{eAfter}{punc}")
        else:
            elem = F.otype.v(node)
            elemOut = RENAME.get(elem, elem)
            attStr = ""
            for (attName, attNameOut) in ATTS.get(elem, []):
                attValue = Fs(attName).v(node)
                attStr += f''' {attNameOut}="{attValue}"'''
            if boundary:
                newLine = "" if elem in NO_NEWLINE_AFTER else "\n"
                body.append(f"</{elemOut}>{newLine}")
            else:
                newLine = "" if elem in NO_NEWLINE_BEFORE else "\n"
                body.append(f"{newLine}<{elemOut}{attStr}>")
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


def convertVolume(A, v, title):
    print(title)

    L = A.api.L

    letters = L.d(v, otype="letter")
    letterText = "\n\n".join(convertLetter(A, letter) for letter in letters)
    return dedent(
        """\
    <TEI xmlns="http://www.tei-c.org/ns/1.0">
    <teiHeader>
    <fileDesc><titleStmt>Generale Missieven, volume {}</titleStmt></fileDesc>
    </teiHeader>
    {}
    </TEI>
    """
    ).format(title, letterText)


def convertWork(A):
    F = A.api.F

    destDir = f"{XMLOUT_DIR}/{A.version}"
    initTree(destDir, fresh=True, gentle=True)

    for v in F.otype.s("volume"):
        title = A.sectionStrFromNode(v)
        destFile = f"{destDir}/{title}.xml"
        with open(destFile, "w") as fh:
            fh.write(convertVolume(A, v, title))


def main():
    args = () if len(sys.argv) == 1 else tuple(sys.argv[1:])

    if "--help" in args:
        print(HELP)
        return True

    version = VERSION_TF if len(args) == 0 else args[0]

    tfInDir = f"{TF_DIR}/{version}"
    if not os.path.isdir(tfInDir):
        print(f"No TF input in in version {version}")
        return False

    entityTfDir = f"{ENTITY_TF}/{version}"

    doEntities = os.path.exists(entityTfDir)
    doEntitiesRep = "WITH" + ("" if doEntities else "OUT") + " entities"

    mods = dict(mod=f"{ENTITY_MOD}:clone") if doEntities else {}

    A = use(
        f"{ORG}/{REPO}:clone", checkout="clone", **mods, version=version, silent="deep"
    )

    print(f"Converting TF version {version} to XML {doEntitiesRep}")

    convertWork(A)


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
