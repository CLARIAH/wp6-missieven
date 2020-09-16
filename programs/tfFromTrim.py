import sys
import os
import collections

import xml.etree.ElementTree as ET

from tf.fabric import Fabric
from tf.convert.walker import CV

from lib import (
    TRIM_DIR,
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

    volumes = getVolumes(TRIM_DIR)

    cur = {}

    for vol in volumes:
        if givenVol is not None and givenVol != vol:
            continue
        print(f"\rvolume {vol:>2}" + " " * 70)

        cur["volume"] = cv.node("volume")
        cv.feature(cur["volume"], n=vol)

        thisTrimDir = f"{TRIM_DIR}/{vol}"
        letters = getLetters(thisTrimDir)

        for name in letters:
            lid = int(name[1:5].lstrip("0"))
            if givenLid is not None and givenLid != lid:
                continue
            sys.stderr.write(f"\r\t{name[0:5]}      ")
            with open(f"{thisTrimDir}/{name}") as fh:
                text = fh.read()
                root = ET.fromstring(text)
            walkLetter(cv, root, cur)

        cv.terminate(cur["volume"])

    print("\rdone" + " " * 70)

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


def walkLetter(cv, root, cur):
    cur["letter"] = cv.node("letter")
    cur["ln"] = 0
    cur["p"] = 0

    for child in root:
        if child.tag == "header":
            collectMeta(cv, child, cur)
        if child.tag == "body":
            walkNode(cv, child, cur)

    cv.terminate(cur.get("line", None))
    cv.terminate(cur.get("page", None))
    cv.terminate(cur.get("para", None))
    cv.terminate(cur["letter"])


PB_ATTS = """
    n
    vol
    facs
    tpl
""".strip().split()

TEXT_ATTRIBUTES = """
    emph
    special
    super
    und
""".strip().split()

NODE_ELEMENTS = set("""
    head
    table
    row
    cell
""".strip().split())


COMMENT_ELEMENTS = set("""
    folio
    remark
""".strip().split())


def walkNode(cv, node, cur):
    tag = node.tag
    atts = node.attrib

    if tag == "pb":
        cv.terminate(cur.get("line", None))
        cv.terminate(cur.get("page", None))
        cur["page"] = cv.node("page")
        cur["line"] = cv.node("line")
        cur["ln"] = 1
        cv.feature(cur["page"], **featsFromAtts(node, PB_ATTS))
        cv.feature(cur["line"], n=cur["ln"])
        addText(cv, node.text, cur)
    elif tag == "lb":
        cv.terminate(cur.get("line", None))
        cur["line"] = cv.node("line")
        cur["ln"] += 1
        cv.feature(cur["line"], n=cur["ln"])
        addText(cv, node.text, cur)
    elif tag == "p":
        cur["p"] += 1
        cur["para"] = cv.node("para")
        cv.feature(cur["para"], n=cur["p"])
        addText(cv, node.text, cur)
    elif tag == "head":
        cur["head"] = cv.node("head")
        addText(cv, node.text, cur)
    elif tag == "table":
        cur["table"] = cv.node("table")
        cv.feature(cur["table"], n=atts.get("n", None))
    elif tag == "row":
        cur["row"] = cv.node("row")
        cv.feature(cur["row"], row=atts.get("row", None))
    elif tag == "cell":
        cur["cell"] = cv.node("cell")
        cv.feature(cur["cell"], row=atts.get("row", None), col=atts.get("col", None))
        addText(cv, node.text, cur)
    elif tag in COMMENT_ELEMENTS:
        cv.feature(cur["word"], **{tag: node.text})
    elif tag in TEXT_ATTRIBUTES:
        cur[tag] = 1
        addText(cv, node.text, cur)

    for child in node:
        walkNode(cv, child, cur)

    if tag == "p":
        cv.terminate(cur["para"])
    elif tag in NODE_ELEMENTS:
        cv.terminate(cur[tag])
    elif tag in TEXT_ATTRIBUTES:
        cur[tag] = None

    addText(cv, node.tail, cur)


# AUXILIARY


def collectMeta(cv, node, cur):
    info = {
        meta.attrib["key"]: meta.attrib["value"] for meta in node if meta.tag == "meta"
    }
    cv.feature(cur["letter"], **info)


def featsFromAtts(node, feats):
    return {
        feat: int(atts[feat].lstrip("0")) if feat in intFeatures else atts[feat]
        for feat in feats
        if feat in (atts := node.attrib)
    }


def addText(cv, text, cur):
    if text:
        for word in text.split():
            curWord = cv.slot()
            cur["word"] = curWord
            cv.feature(curWord, trans=word, punc=" ")
            for tag in TEXT_ATTRIBUTES:
                if cur.get(tag, None):
                    cv.feature(curWord, **{tag: 1})


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
