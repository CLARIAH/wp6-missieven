import sys
import os
import collections
import re

import xml.etree.ElementTree as ET

from tf.fabric import Fabric
from tf.convert.walker import CV

from lib import (
    TRIM2_DIR,
    OUT_DIR,
    REPO,
    VERSION_SRC,
    VERSION_TF,
    META_DECL,
    clearTree,
    getVolumes,
    getLetters,
)


HELP = """

Convert simplified pseudo TEI to TF and optionally loads the TF.

python3 tfFromTrim.py ["load"] [volume] [page] [--help]

--help: print this text amd exit

"load": loads the generated TF; if missing this step is not performed
volume: only process this volume; default: all volumes
page  : only process letter that starts at this page; default: all letters
"""

# TF CONFIGURATION

slotType = "word"

generic = {
    k: META_DECL[k]
    for k in """
    name
    title
    editor
    published
    period
    language
    institute
    project
    researcher
    converters
""".strip().split()
}

otext = {
    "fmt:text-orig-full": "{trans}{punc}",
    "sectionFeatures": "n,n,n",
    "sectionTypes": "volume,page,line",
    "structureFeatures": "n,title,n",
    "structureTypes": "volume,letter,para",
}

intFeatures = set(
    """
        n
        tpl
        vol
        row
        col
    """.strip().split()
)

featureMeta = {
    "authors": {
        "description": "authors of the letter",
        "format": "comma-separated values",
    },
    "place": {
        "description": "place from where the letter was sent",
    },
    "rawdate": {
        "description": "the date the letter was sent",
        "format": "informal Dutch date notation",
    },
    "dayFrom": {
        "description": "day part of the date the letter was sent",
        "format": "numeral between 1 and 31 inclusive",
    },
    "dayTo": {
        "description": "day part of the date the letter was received",
        "format": "numeral between 1 and 31 inclusive",
    },
    "monthFrom": {
        "description": "month part of the date the letter was sent",
        "format": "numeral between 1 and 12 inclusive",
    },
    "monthTo": {
        "description": "month part of the date the letter was received",
        "format": "numeral between 1 and 12 inclusive",
    },
    "yearFrom": {
        "description": "year part of the date the letter was sent",
        "format": "numeral between 1600 and 1800",
    },
    "yearTo": {
        "description": "year part of the date the letter was received",
        "format": "numeral between 1600 and 1800",
    },
    "page": {
        "description": "number of the first page of this letter in this volume",
        "format": "numeral (at most 4 digits)",
    },
    "seq": {
        "description": (
            "sequence number of this letter among the letters of"
            " the same author in this volume",
        ),
        "format": "roman numeral (capitalized)",
    },
    "pid": {
        "description": (
            "abstract identifier, corresponding with the file name of the"
            " TEI source file of the letter"
        ),
        "format": "'INT_' plus '-' separated hex numbers",
    },
    "title": {"description": "short title of letter, from fileDesc element"},
    "location": {"description": "location from letter was sent, from fileDesc element"},
    "vol": {"description": "volume number", "format": "positive integer"},
    "data": {"description": "date when letter was sent, from fileDesc element"},
    "lid": {"description": "ID of letter, from fileDesc element"},
    "n": {"description": "number of a volume, letter, page, para, line, table"},
    "row": {"description": "row number of a row of column in a table"},
    "col": {"description": "column number of a column in a row in a table"},
    "facs": {
        "description": (
            "url part of the corresponding online facsimile page;"
            " the url itself can be constructed using a hard coded template."
            " See also the tpl feature"
        )
    },
    "tpl": {
        "description": (
            "url template number of the corresponding online facsimile page;"
            "the url itself can be constructed using this template,"
            " filled with the contents of the facs attribute."
        ),
        "format": (
            "either 1 or 2:"
            " template 1 = http://resources.huygens.knaw.nl/"
            "retroapp/service_generalemissiven/gm_{vol:>02}/"
            "images/gm_{facs}.tif "
            " template 2 = http://resources.huygens.knaw.nl/"
            "retroapp/service_generalemissiven/gm_{vol:>02}/"
            "images/generale_missiven_gs{facs}.tif"
        ),
    },
    "folio": {
        "description": "label indicating a folio break",
        "format": (
            "string of the form `Fol. {n} {rv}` where rv is a recto/verso indication"
        ),
    },
    "fref": {
        "description": "foot note mark as it occurs in the text",
        "format": "string",
    },
    "flabel": {
        "description": "foot note mark as it occurs in the footnote",
        "format": "string",
    },
    "fnum": {
        "description": "foot note number (interpreted and corrected)",
        "format": "integer",
    },
    "fnote": {
        "description": "foot note text",
        "format": "string with mark down formatting",
    },
    "trans": {"description": "transcription of a word"},
    "punc": {
        "description": "whitespace and/or punctuation following a word"
        "up to the next word"
    },
    "emph": {
        "description": "whether a word is emphasized by typography",
        "format": "integer 1 or absent",
    },
    "und": {
        "description": "whether a word is underlined by typography",
        "format": "integer 1 or absent",
    },
    "super": {
        "description": (
            "whether a word has superscript typography"
            " possibly indicating the numerator of a fraction"
        ),
        "format": "integer 1 or absent",
    },
    "special": {
        "description": (
            "whether a word has special typography"
            " possibly with OCR mistakes as well"
        ),
        "format": "integer 1 or absent",
    },
    "remark": {
        "description": "editorial remark after this word position",
        "format": "full text, with markdown and without XML mark up",
    },
}

# ERROR HANDLING


def showDiags(diags, kind, batch=20):
    if not diags:
        print("No diags")
    else:
        for (diag, srcs) in sorted(diags.items()):
            print(f"{kind} {diag}")
            for (src, data) in sorted(srcs.items()):
                print(f"\t{src} ({len(data)}x)")
                for (l, line, doc, sore) in sorted(data)[0:batch]:
                    soreRep = "" if sore is None else f'"{sore}" in '
                    print(f"\t\t{l} in {doc}: {soreRep}{line}")
                if len(data) > batch:
                    print("\t\t + more")


# SET UP CONVERSION


def getConverter():
    TF = Fabric(locations=OUT_DIR)
    return CV(TF)


def convert(vol, lid, doLoad):
    global givenVol
    global givenLid

    givenVol = vol
    givenLid = lid

    if doLoad:
        if os.path.exists(OUT_DIR):
            clearTree(OUT_DIR)
        os.makedirs(OUT_DIR, exist_ok=True)

    cv = getConverter()

    return cv.walk(
        director,
        slotType,
        otext=otext,
        generic=generic,
        intFeatures=intFeatures,
        featureMeta=featureMeta,
        generateTf=True,
    )


# DIRECTOR


def director(cv):

    warnings = collections.defaultdict(lambda: collections.defaultdict(set))
    errors = collections.defaultdict(lambda: collections.defaultdict(set))

    volumes = getVolumes(TRIM2_DIR)

    cur = {}
    notes = dict(
        marks={},
        markOrder=[],
        bodies={},
        bodyOrder=[],
        lastMark=None,
        totalMarks=0,
        totalBodies=0,
        ambiguousMarks={},
        ambiguousBodies={},
        unresolvedMarks={},
        unresolvedBodies={},
        unmarkedBodies={},
    )

    for vol in volumes:
        if givenVol is not None and givenVol != vol:
            continue
        print(f"\rvolume {vol:>2}" + " " * 70)

        cur["volume"] = cv.node("volume")
        cur["vol"] = vol

        cv.feature(cur["volume"], n=vol)

        thisTrimDir = f"{TRIM2_DIR}/{vol}"
        letters = getLetters(thisTrimDir)

        for name in letters:
            lid = int(name[1:5].lstrip("0"))
            if givenLid is not None and givenLid != lid:
                continue
            sys.stderr.write(f"\r\t{name[0:5]}      ")
            with open(f"{thisTrimDir}/{name}") as fh:
                text = fh.read()
                root = ET.fromstring(text)
            walkLetter(cv, root, cur, notes)

        cv.terminate(cur["volume"])

    print("\rdone" + " " * 70)

    reportNotes(notes)
    sys.exit()

    # delete meta data of unused features

    for feat in featureMeta:
        if not cv.occurs(feat):
            print(f"WARNING: feature {feat} does not occur")
            cv.meta(feat)

    if warnings:
        showDiags(warnings, "WARNING")
    if errors:
        showDiags(errors, "ERROR")


# WALKERS


def walkLetter(cv, root, cur, notes):
    cur["letter"] = cv.node("letter")
    cur["ln"] = 0
    cur["p"] = 0
    cur["fn"] = None

    for child in root:
        if child.tag == "header":
            collectMeta(cv, child, cur)
        if child.tag == "body":
            walkNode(cv, child, cur, notes)

    cv.terminate(cur.get("line", None))
    doNotes(cv, cur, notes)
    cv.terminate(cur.get("page", None))
    cv.terminate(cur["letter"])


TEXT_ATTRIBUTES = """
    emph
    special
    super
    und
""".strip().split()

NODE_ELEMENTS = set(
    """
    para
    head
    table
    row
    cell
""".strip().split()
)

BREAKS = set(
    """
    pb
    lb
""".strip().split()
)

COMMENT_ELEMENTS = set(
    """
    folio
    remark
""".strip().split()
)

DO_TEXT_ELEMENTS = set(
    """
    head
    para
    cell
    emph
    super
    und
    special
""".strip().split()
)

DO_TAIL_ELEMENTS = set(
    """
    pb
    lb
    table
    emph
    super
    und
    special
    folio
    remark
    fref
""".strip().split()
)

DOWN_REF_RE = re.compile(r"""\[=([^\]]*)\]""")


def walkNode(cv, node, cur, notes):
    """Handle all elements in the XML file.

    List of all elements and attributes.
    All attributes will translate to features.
    Some node types get extra features.
    Feature n is a sequence number relative to a bigger unit

    elem | kind | converts to
    --- | --- | ---
    teiTrim | top-level element of a letter | --
    header | holds metadata elements of a letter | --
    meta.key,value | holds a piece of metadata | feature key with value on letter node
    body | holds all text of a letter | --
    head | heading in the text | node type head, no features
    para | paragraph | node type para, n within letter
    pb.facs,n,tpl,vol |page break (empty element) | node type page, n within letter
    lb | line break (empty element) | node type line, n within page
    table.n | holds a table with rows and cells | node type table, n within corpus
    row.n,row | holds a table row with cells | node type row
    cell.n,row,col | holds material in a table cell node type cell
    emph | inline formatting (italic-bold-large mixture) | binary feature emph
    super | inline formatting (superscript) | binary feature supe
    und | inline formatting (underline) | binary feature und
    special | inline formatting | binary feature special
    folio | reference to a folio page | feature folio
    remark | editorial text in the text flow | feature remark
    fnote.ref | footnote text at the end of a page | feature footnote at place of fref
    fref.ref | footnote reference within the text flow | used to bind fnote to this spot
    """

    tag = node.tag
    atts = node.attrib

    if tag in BREAKS:
        cv.terminate(cur.get("line", None))
        if tag == "pb":
            doNotes(cv, cur, notes)
            cv.terminate(cur.get("page", None))
            cur["page"] = cv.node("page")
            cv.feature(cur["page"], **featsFromAtts(atts))
            cur["pg"] = f"{cur['vol']:>02}:p{atts['n']:>04}"
            cur["ln"] = 1
        elif tag == "lb":
            cur["ln"] += 1
        cur["line"] = cv.node("line")
        cv.feature(cur["line"], n=cur["ln"])

    elif tag in NODE_ELEMENTS:
        curNode = cv.node(tag)
        cur[tag] = curNode
        if atts:
            cv.feature(curNode, **featsFromAtts(atts))
        if tag == "para":
            cur["p"] += 1
            cv.feature(cur["para"], n=cur["p"])

    elif tag in COMMENT_ELEMENTS:
        curWord = cur["word"]
        text = node.text
        cv.feature(curWord, **{tag: text})
        for ref in DOWN_REF_RE.findall(text):
            notes["marks"].setdefault(ref, []).append((curWord, cur["ln"]))

    elif tag in TEXT_ATTRIBUTES:
        cur[tag] = 1

    elif tag == "fref":
        notes["marks"].setdefault(atts.get("ref", None), []).append((cur["word"], cur["ln"]))
        notes["totalMarks"] += 1

    elif tag == "fnote":
        bodies = notes["bodies"]
        fref = atts.get("ref", None)
        if fref is None and notes["lastMark"] is not None:
            lastBody = notes["lastBody"]
            lastBody[-1] += node.text
            cur["fn"] = bodies[notes["lastMark"]]
        else:
            notes["totalBodies"] += 1
            bodies.setdefault(fref, []).append(node.text)
            notes["lastMark"] = fref
            cur["fn"] = bodies[fref]

    if tag in DO_TEXT_ELEMENTS:
        addText(cv, node.text, cur)

    for child in node:
        walkNode(cv, child, cur, notes)

    if tag in NODE_ELEMENTS:
        cv.terminate(cur[tag])

    elif tag in TEXT_ATTRIBUTES:
        cur[tag] = None

    elif tag == "fnote":
        cur["fn"] = None

    if tag in DO_TAIL_ELEMENTS:
        addText(cv, node.tail, cur)


# AUXILIARY


def collectMeta(cv, node, cur):
    info = {
        meta.attrib["key"]: meta.attrib["value"] for meta in node if meta.tag == "meta"
    }
    cv.feature(cur["letter"], **info)


def featsFromAtts(atts):
    return {
        feat: int(value.lstrip("0")) if feat in intFeatures else value
        for (feat, value) in atts.items()
        if value is not None
    }


def addText(cv, text, cur):
    if text:
        dest = cur["fn"]
        if dest:
            dest[-1] += text
        else:
            for word in text.split():
                curWord = cv.slot()
                cur["word"] = curWord
                cv.feature(curWord, trans=word, punc=" ")
                for tag in TEXT_ATTRIBUTES:
                    if cur.get(tag, None):
                        cv.feature(curWord, **{tag: 1})


def doNotes(cv, cur, notes):
    markInfo = notes["marks"]
    markOrder = notes["markOrder"]
    bodyInfo = notes["bodies"]
    bodyOrder = notes["bodyOrder"]
    lastMark = notes["lastMark"]

    curPg = cur.get("pg", None)

    for (mark, occs) in markInfo.items():
        if len(occs) > 1:
            notes["ambiguousMarks"].setdefault(mark, {})[curPg] = occs
        if mark not in bodyInfo:
            notes["unresolvedMarks"].setdefault(mark, {})[curPg] = occs

    for (mark, bodies) in bodyInfo.items():
        if mark is None:
            notes["unmarkedBodies"][curPg] = len(bodies)
        else:
            if len(bodies) > 1:
                notes["ambiguousBodies"].setdefault(mark, {})[curPg] = len(bodies)
            if mark not in markInfo:
                notes["unresolvedBodies"].setdefault(mark, {})[curPg] = len(bodies)

    markInfo.clear()
    markOrder.clear()

    if not bodyInfo:
        notes["lastMark"] = None
        notes["lastBody"] = None
    else:
        notes["lastBody"] = bodyInfo[lastMark]

    bodyInfo.clear()
    bodyOrder.clear()


def reportNotes(notes):
    markAmb = notes["ambiguousMarks"]
    nMarkAmb = 0
    if markAmb:
        nMarkAmb = sum(
            sum(len(occs) for occs in pages.values()) for pages in markAmb.values()
        )
        print(f"{nMarkAmb:>5} AMBIGUOUS REFERENCES TO FOOTNOTES:")
        for (mark, pages) in sorted(markAmb.items()):
            print(f"\t{mark})")
            for (page, occs) in sorted(pages.items()):
                occsRep = ", ".join(str(occ[1]) for occ in occs)
                print(f"\t\t{page}: {occsRep}")

    bodyUnmarked = notes["unmarkedBodies"]
    nBodyUnmarked = 0
    if bodyUnmarked:
        nBodyUnmarked = sum(bodyUnmarked.values())
        print(f"{nBodyUnmarked:>5} FOOTNOTE BODIES WITHOUT REFERENCE:")
        for (page, n) in sorted(bodyUnmarked.items()):
            print(f"\t{page}: {n:>3} x")

    bodyAmb = notes["ambiguousBodies"]
    nBodyAmb = 0
    if bodyAmb:
        nBodyAmb = sum(sum(pages.values()) for pages in bodyAmb.values())
        print(f"{nBodyAmb:>5} AMBIGUOUS REFERENCES IN FOOTNOTE BODIES:")
        for (mark, pages) in sorted(bodyAmb.items()):
            print(f"\t{mark})")
            for (page, n) in sorted(pages.items()):
                print(f"\t\t{page}: {n:>3} x")

    markUnres = notes["unresolvedMarks"]
    nMarkUnres = 0
    if markUnres:
        nMarkUnres = sum(
            sum(len(occs) for occs in pages.values()) for pages in markUnres.values()
        )
        print(f"{nMarkUnres:>5} UNRESOLVED REFERENCES TO FOOTNOTES:")
        for (mark, pages) in sorted(markUnres.items()):
            print(f"\t{mark})")
            for (page, occs) in sorted(pages.items()):
                occsRep = ", ".join(str(occ[1]) for occ in occs)
                print(f"\t\t{page}: {occsRep}")

    bodyUnres = notes["unresolvedBodies"]
    nBodyUnres = 0
    if bodyUnres:
        nBodyUnres = sum(sum(pages.values()) for pages in bodyUnres.values())
        print(f"{nBodyUnres:>5} UNRESOLVED REFERENCES IN FOOTNOTE BODIES:")
        for (mark, pages) in sorted(bodyUnres.items()):
            print(f"\t{mark})")
            for (page, n) in sorted(pages.items()):
                print(f"\t\t{page}: {n:>3} x")

    print("NOTES SUMMARY")
    print(f"{notes['totalMarks']:>5} FOOTNOTE REFERENCES")
    print(f"{notes['totalBodies']:>5} FOOTNOTE BODIES")
    print(f"{nMarkAmb:>5} AMBIGUOUS REFERENCES TO FOOTNOTES")
    print(f"{nBodyUnmarked:>5} FOOTNOTE BODIES WITHOUT REFERENCE")
    print(f"{nBodyAmb:>5} AMBIGUOUS REFERENCES IN FOOTNOTE BODIES")
    print(f"{nMarkUnres:>5} UNRESOLVED REFERENCES TO FOOTNOTES")
    print(f"{nBodyUnres:>5} UNRESOLVED REFERENCES IN FOOTNOTE BODIES")


# TF LOADING (to test the generated TF)


def loadTf():
    TF = Fabric(locations=[OUT_DIR])
    allFeatures = TF.explore(silent=True, show=True)
    loadableFeatures = allFeatures["nodes"] + allFeatures["edges"]
    api = TF.load(loadableFeatures, silent=False)
    if api:
        print(f"max node = {api.F.otype.maxNode}")
        print("Frequency of readings")
        print(api.F.reading.freqList()[0:20])
        print("Frequency of grapheme")
        print(api.F.grapheme.freqList()[0:20])


# MAIN


def main():
    args = () if len(sys.argv) == 1 else tuple(sys.argv[1:])

    doLoad = "load" in args

    vol = None
    lid = None

    for arg in args:
        if arg == "--help":
            print(HELP)
            return True
        if arg.isdigit():
            if vol is None:
                vol = arg
            elif lid is None:
                lid = arg

    if vol is not None:
        vol = int(vol)
    if lid is not None:
        lid = int(lid)

    print(f"trimmed TEI to TF converter for {REPO}")
    print(f"TEI source version = {VERSION_SRC}")
    print(f"TF  target version = {VERSION_TF}")

    if not convert(vol, lid, doLoad):
        return False

    if doLoad:
        loadTf()

    return True


sys.exit(0 if main() else 1)
