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

ATTS = dict(
    page=["n"],
)

RENAME = dict(
    page="pb",
    line="lb",
    para="p",
    note="mark",
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
    N = A.api.N
    L = A.api.L
    F = A.api.F
    Fs = A.api.Fs
    header = []
    for feat in HEADER_FEATURES:
        value = htmlEsc(Fs(feat).v(letter))
        header.append(f"""<meta key="{feat}" value="{value}"/>""")

    header = "\n".join(header)

    # walk through the nodes and insert entity start and end events
    # to the relevant slots.
    # in this pass, the entity nodes will not be tightly wrapped
    # around slots, because it is only at the next slot that we know
    # that a current entity has stopped at the previous slot.
    # Between that previous slot and the current slot,
    # other node events may have occurred.

    curEnt = []
    spicedNodes = []

    def startEntity():
        curSlot.extend([False, entityId, entityKind])
        curEnt.append(curSlot, curSlot)

    def getEntity():
        thisSlot = curEnt[-1]

    def continueEntity():
        curEnt[-1] = curSlot

    def endEntity():
        lastSlot = curEnt[-1]
        lastSlot.extend([True])
        curEnt.clear()

    for (node, boundary) in N.walk(nodes=L.d(letter), events=True):
        if boundary is None:
            # dealing with slots
            curSlot = [node, boundary]
            entityId = F.entityId.v(node)
            entityKind = F.entityKind.v(node)

            if curEnt:
                if entityId is None and entityKind is None:
                    endEntity()
                else:
                    (curEntId, curEntKind) = curEnt
                    if entityId == curEntId and entityKind == curEntKind:
                        pass
                    else:
                        endEntity()
                        startEntity(entityId, entityKind)
            else:
                if entityId is None and entityKind is None:
                    pass
                else:
                    startEntity(entityId, entityKind)

            spicedNodes.append([node, boundary, trans, punc])

        else:
            # dealing with non-slot nodes
            elem = F.otype.v(node)
            elemRep = RENAME.get(elem, elem)
            attStr = ""
            for attName in ATTS.get(elem, []):
                attValue = Fs(attName).v(node)
                attStr += f''' {attName}="{attValue}"'''
            if boundary:
                newLine = "" if elem in NO_NEWLINE_AFTER else "\n"
                body.append(f"</{elemRep}>{newLine}")
            else:
                newLine = "" if elem in NO_NEWLINE_BEFORE else "\n"
                body.append(f"{newLine}<{elemRep}{attStr}>")

        if curEnt:
            endEntity()

    body = []

    for (node, boundary) in N.walk(nodes=L.d(letter), events=True):
        trans = F.trans.v(node) or ""
        punc = F.punc.v(node) or ""

        if boundary is None:
            entityId = F.entityId.v(node)
            entityKind = F.entityKind.v(node)
            if curEnt:
                if entityId is None and entityKind is None:
                    addEntity()
                else:
                    (curEntId, curEntKind, curEntMaterial) = curEnt
                    if entityId == curEntId and entityKind == curEntKind:
                        curEntMaterial.append((trans, punc))
                    else:
                        addEntity()
                        curEnt.extend([entityId, entityKind, [trans, punc]])
            else:
                if entityId is None and entityKind is None:
                    body.append(f"{trans}{punc}")
                else:
                    curEnt.extend([entityId, entityKind, [trans, punc]])
        else:
            elem = F.otype.v(node)
            elemRep = RENAME.get(elem, elem)
            attStr = ""
            for attName in ATTS.get(elem, []):
                attValue = Fs(attName).v(node)
                attStr += f''' {attName}="{attValue}"'''
            if boundary:
                newLine = "" if elem in NO_NEWLINE_AFTER else "\n"
                body.append(f"</{elemRep}>{newLine}")
            else:
                newLine = "" if elem in NO_NEWLINE_BEFORE else "\n"
                body.append(f"{newLine}<{elemRep}{attStr}>")
    body = "".join(body)

    return dedent(
        """\
    <letter>
    <header>
    {}
    </header>
    <body>
    {}
    </body>
    </letter>
    """
    ).format(header, body)


def convertVolume(A, v, title):
    print(title)

    L = A.api.L

    letters = L.d(v, otype="letter")
    letterText = "\n\n".join(convertLetter(A, letter) for letter in letters)
    return dedent(
        """\
    <teiTrim>
    {}
    </teiTrim>
    """
    ).format(letterText)


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
