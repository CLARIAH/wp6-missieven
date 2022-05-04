import sys
import collections
import re

import xml.etree.ElementTree as ET

from tf.fabric import Fabric
from tf.convert.walker import CV


from lib import (
    XML_DIR,
    OUT_DIR,
    REPO,
    META_DECL,
    WHITE_RE,
    ADD_LB_ELEMENTS,
    ENSURE_LB_ELEMENTS,
    A2Z,
    parseArgs,
    initTree,
    getVolumes,
    getLetters,
    docSummary
)

SRC = f"{XML_DIR}"
VERSION_SRC = META_DECL["versionSrc"]
VERSION_TF = META_DECL["versionTf"]


HELP = """

Convert simplified pseudo TEI to TF and optionally loads the TF.

python3 tfFromTrim.py ["load"] ["loadonly"] [volume] [page] [--help]

--help: print this text and exit

"load": loads the generated TF; if missing this step is not performed
"loadonly": does not generate TF; loads previously generated TF
volume: only process this volume; default: all volumes
page  : only process letter that starts at this page; default: all letters
"""

PAGE_OFFSETS = {
    "01": 23,
    "02": 13,
    "03": 13,
    "04": 15,
    "05": 15,
    "06": 15,
    "07": 11,
    "08": 11,
    "09": 13,
    "10": 11,
    "11": 11,
    "12": 11,
    "13": 11,
}

NOTE = "note"

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
    sourceFormat
    descriptionTf
""".strip().split()
}

otext = {
    "fmt:text-orig-full": "{trans}{punc}",
    "fmt:text-orig-source": "{transo}{punco}",
    "fmt:text-orig-remark": "{transr}{puncr}",
    "fmt:text-orig-note": "{transn}{puncn}",
    "sectionFeatures": "n,n,n",
    "sectionTypes": "volume,page,line",
    "structureFeatures": "n,title,n",
    "structureTypes": "volume,letter,para",
}

intFeatures = set(
    """
        n
        vol
        row
        col
        x
        day
        mark
        month
        year
        isfolio
        isnote
        isorig
        isq
        isnum
        isden
        isref
        isremark
        isspecial
        issub
        issuper
    """.strip().split()
)

featureMeta = {
    "author": {
        "description": "authors of the letter, surnames only",
        "format": "comma-space-separated values",
    },
    "authorFull": {
        "description": "authors of the letter, full names",
        "format": "comma-space-separated values",
    },
    "col": {"description": "column number of a column in a row in a table"},
    "day": {
        "description": "day part of the date of the letter",
        "format": "numeral between 1 and 31 inclusive",
    },
    "isemph": {
        "description": "whether a word is emphasized by typography",
        "format": "integer 1 or absent",
    },
    "isfolio": {
        "description": "a folio reference",
        "format": "integer 1 or absent",
    },
    "isorig": {
        "description": "whether a word belongs to original text",
        "format": "integer 1 or absent",
    },
    "isnote": {
        "description": "whether a word belongs to footnote text",
        "format": "integer 1 or absent",
    },
    "isq": {
        "description": "whether a word is a numerical fraction, e.g. 1/4",
        "format": "integer 1 or absent",
    },
    "isnum": {
        "description": "whether a word is the numerator in fraction, e.g. 1 in 1/4",
        "format": "integer 1 or absent",
    },
    "isden": {
        "description": "whether a word is the denominator in fraction, e.g. 4 in 1/4",
        "format": "integer 1 or absent",
    },
    "isref": {
        "description": "whether a word belongs to the text of reference",
        "format": "integer 1 or absent",
    },
    "isremark": {
        "description": "whether a word belongs to the text of editorial remarks",
        "format": "integer 1 or absent",
    },
    "issub": {
        "description": (
            "whether a word has subscript typography"
            " possibly indicating the denominator of a fraction"
        ),
        "format": "integer 1 or absent",
    },
    "issuper": {
        "description": (
            "whether a word has superscript typography"
            " possibly indicating the numerator of a fraction"
        ),
        "format": "integer 1 or absent",
    },
    "isspecial": {
        "description": (
            "whether a word has special typography"
            " possibly with OCR mistakes as well"
        ),
        "format": "integer 1 or absent",
    },
    "isund": {
        "description": "whether a word is underlined by typography",
        "format": "integer 1 or absent",
    },
    "mark": {
        "description": (
            "footnote mark (not necessarily the same as shown on the printed page"
        ),
        "format": "integer",
    },
    "month": {
        "description": "month part of the date of the letter",
        "format": "numeral between 1 and 12 inclusive",
    },
    "n": {"description": "number of a volume, letter, page, para, line, table"},
    "note": {
        "description": "edge between a word and the footnotes associated with it",
        "format": "no values",
    },
    "page": {
        "description": "number of the first page of this letter in this volume",
        "format": "numeral (at most 4 digits)",
    },
    "place": {
        "description": "place from where the letter was sent",
    },
    "punc": {
        "description": "punctuation and/or whitespace following a word"
        "up to the next word"
    },
    "punco": {
        "description": "punctuation and/or whitespace following a word,"
        "up to the next word, original text only"
    },
    "puncr": {
        "description": "punctuation and/or whitespace following a word,"
        "up to the next word, remark text only"
    },
    "puncn": {
        "description": "punctuation and/or whitespace following a word,"
        "up to the next word, footnote text only"
    },
    "rawdate": {
        "description": "the date the letter was sent",
        "format": "informal Dutch date notation",
    },
    "rest": {
        "description": "unidentified metadata of the letter",
        "format": "string",
    },
    "row": {"description": "row number of a row of column in a table"},
    "seq": {
        "description": (
            "sequence number of this letter among the letters of"
            " the same author in this volume",
        ),
        "format": "roman numeral (capitalized)",
    },
    "status": {
        "description": "status of the letter, e.g. secret, copy",
        "format": "keyword",
    },
    "title": {
        "description": "title of the letter",
        "format": "comma-separated values",
    },
    "trans": {"description": "transcription of a word"},
    "transo": {"description": "transcription of a word, only for original text"},
    "transr": {"description": "transcription of a word, only for remark text"},
    "transn": {"description": "transcription of a word, only for footnote text"},
    "vol": {"description": "volume number", "format": "positive integer"},
    "x": {"description": "column offset of a column in a row in a table"},
    "year": {
        "description": "year part of the date of the letter",
        "format": "numeral between 1600 and 1800",
    },
    "weblink": {"description": "the page-specific part of web links for page nodes"},
}

# ERROR HANDLING


def showDiags(diags, kind, batch=20):
    if not diags:
        print("No diags")
    else:
        for (diag, docs) in sorted(diags.items()):
            docRep = docSummary(sorted(docs))
            print(f"{kind} {diag} {len(docs):>4}x {docRep}")


# SET UP CONVERSION


def getConverter():
    TF = Fabric(locations=OUT_DIR)
    return CV(TF)


def convert(vol, lid):
    global givenVol
    global givenLid

    givenVol = vol
    givenLid = lid

    initTree(OUT_DIR, fresh=True)

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


warnings = collections.defaultdict(set)
errors = collections.defaultdict(set)


def director(cv):
    volumes = getVolumes(SRC)

    cur = {}

    for vol in volumes:
        if givenVol is not None and vol not in givenVol:
            continue
        print(f"\rvolume {vol:>2}" + " " * 70)

        cur["volume"] = cv.node("volume")
        cur["vol"] = vol

        cv.feature(cur["volume"], n=vol)

        thisSrcDir = f"{SRC}/{vol}"
        letters = getLetters(thisSrcDir)

        for name in letters:
            lid = name
            doc = f"{vol:>2}:{name}"
            if givenLid is not None and lid.rstrip(A2Z) not in givenLid:
                continue
            sys.stderr.write(f"\r\t{lid}      ")
            with open(f"{thisSrcDir}/{name}.xml") as fh:
                text = fh.read()
                root = ET.fromstring(text)
            walkLetter(cv, doc, root, cur)

        curPage = cur.get("page", None)
        if curPage:
            linkIfEmpty(cv, curPage)
            cv.terminate(curPage)
            cur["page"] = None
        cv.terminate(cur["volume"])
        cur["volume"] = None

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
        cv.stop("because of irregularities")


# WALKERS


def walkLetter(cv, doc, root, cur):
    cur["letter"] = cv.node("letter")
    cur["ln"] = 0
    cur["p"] = 0

    for child in root:
        if child.tag == "header":
            collectMeta(cv, child, cur)
        if child.tag == "body":
            walkNode(cv, doc, child, cur)

    curLine = cur.get("line", None)
    if curLine:
        linkIfEmpty(cv, curLine)
        cv.terminate(curLine)
        cur["line"] = None
    curPage = cur.get("page", None)
    if curPage and False:
        linkIfEmpty(cv, curPage)
        cv.terminate(curPage)
        cur["page"] = None
    cv.terminate(cur["letter"])
    cur["letter"] = None


TEXT_ATTRIBUTES = """
    emph
    ref
    remark
    q
    num
    den
    special
    sub
    super
    und
""".strip().split()

SURROUND_SPACE = """
    q
""".strip().split()

TRANSPARENT_ELEMENTS = set(
    """
    body
""".strip().split()
)

NODE_ELEMENTS = set(
    """
    para
    head
    subhead
    table
    row
    cell
""".strip().split()
)

PREVENT_NEST = set(
    """
    para
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
    note
    folio
    remark
""".strip().split()
)

DO_TEXT_ELEMENTS = set(
    """
    cell
    emph
    note
    folio
    head
    para
    ref
    remark
    q
    num
    den
    special
    subhead
    sub
    super
    und
""".strip().split()
)

DO_TAIL_ELEMENTS = set(
    """
    emph
    note
    folio
    lb
    para
    pb
    table
    ref
    remark
    q
    num
    den
    special
    subhead
    sub
    super
    und
""".strip().split()
)

DOWN_REF_RE = re.compile(r"""\[=([^\]]*)\]""")

weblink = None


def linkIfEmpty(cv, node):
    if not cv.linked(node):
        emptySlot = cv.slot()
        cv.feature(emptySlot, trans="", punc="")


def addSpaceBefore(cv, cur):
    if WORD in cur:
        lastPunc = cv.get("punc", cur["word"])
        if not lastPunc.endswith(" "):
            lastPunc += " "
            cv.feature(cur["word"], punc=lastPunc)


def walkNode(cv, doc, node, cur):
    """Handle all elements in the XML file.

    """

    global weblink

    tag = node.tag
    atts = node.attrib

    if tag in PREVENT_NEST:
        if cur.get(tag, None):
            cv.terminate(cur[tag])
            cur[tag] = None
            warnings[f"nested: {tag}"].add(doc)

    if tag in ENSURE_LB_ELEMENTS:
        curLine = cur.get("line", None)
        if not curLine:
            cur["line"] = cv.node("line")
            cur["ln"] += 1
            cv.feature(cur["line"], n=cur["ln"])
            if weblink is not None:
                cv.feature(cur["line"], weblink=weblink)

    if tag in BREAKS:
        curLine = cur.get("line", None)
        if curLine:
            linkIfEmpty(cv, curLine)
            cv.terminate(curLine)
        if tag == "pb":
            curPage = cur.get("page", None)
            if curPage:
                linkIfEmpty(cv, curPage)
                cv.terminate(curPage)
            cur["page"] = cv.node("page")
            featAtts = featsFromAtts(atts)
            cv.feature(cur["page"], **featAtts)
            weblink = featAtts.get("weblink", None)
            cur["pg"] = f"{cur['vol']:>02}:p{atts['n']:>04}"
            cur["ln"] = 1
        elif tag == "lb":
            cur["ln"] += 1
        cur["line"] = cv.node("line")
        cv.feature(cur["line"], n=cur["ln"])
        if weblink is not None:
            cv.feature(cur["line"], weblink=weblink)

    elif tag in NODE_ELEMENTS:
        curNode = cv.node(tag)
        cur[tag] = curNode
        if atts:
            cv.feature(curNode, **featsFromAtts(atts))
        if tag == "para":
            cur["p"] += 1
            cv.feature(cur["para"], n=cur["p"])

    elif tag in COMMENT_ELEMENTS:
        curNode = cv.node(tag)
        cur[tag] = curNode
        cur[f"is_{tag}"] = 1
        if atts:
            cv.feature(curNode, **featsFromAtts(atts))
        if tag == NOTE:
            # edge feature between word that has footnote and its footnote(s)
            cv.edge(cur["word"], curNode, note=None)

    elif tag in TEXT_ATTRIBUTES:
        cur[tag] = 1

    elif tag in TRANSPARENT_ELEMENTS:
        pass

    else:
        errors[f"unrecognized: {tag}"].add(doc)

    if tag in DO_TEXT_ELEMENTS:
        if tag in SURROUND_SPACE:
            addSpaceBefore(cv, cur)

        addText(cv, node.text, cur)

    for child in node:
        walkNode(cv, doc, child, cur)

    curNode = cur.get(tag, None)

    if tag in NODE_ELEMENTS:
        if curNode:
            linkIfEmpty(cv, curNode)
            cv.terminate(curNode)
            cur[tag] = None

    elif tag in COMMENT_ELEMENTS:
        if curNode:
            linkIfEmpty(cv, curNode)
            cv.terminate(curNode)
            cur[tag] = None
        cur[f"is_{tag}"] = None

    elif tag in TEXT_ATTRIBUTES:
        if tag in SURROUND_SPACE:
            addSpaceBefore(cv, cur)
        cur[tag] = None

    if tag in ADD_LB_ELEMENTS:
        curLine = cur.get("line", None)
        if curLine:
            linkIfEmpty(cv, curLine)
            cv.terminate(curLine)
        cur["ln"] += 1
        cur["line"] = cv.node("line")
        cv.feature(cur["line"], n=cur["ln"])
        if weblink is not None:
            cv.feature(cur["line"], weblink=weblink)

    if tag in DO_TAIL_ELEMENTS:
        addText(cv, node.tail, cur)


# AUXILIARY


def collectMeta(cv, node, cur):
    info = {
        meta.attrib["key"]: meta.attrib["value"]
        for meta in node
        if meta.tag == "meta" and meta.attrib["key"] != "pid" and meta.attrib["value"]
    }

    cv.feature(cur["letter"], **info)


def featsFromAtts(atts):
    return {
        feat: int(value.lstrip("0") or 0) if feat in intFeatures else value
        for (feat, value) in atts.items()
        if value is not None
    }


WORD_PARTS_RE = re.compile(
    r"""
    ^
    (.*?)
        (
            \W
            .*
        )
    (\w*)
    (.*)
    $
    """,
    re.S | re.I | re.X,
)

PUNC_DELIM_BEFORE = r"\[{(«<"
PUNC_DELIM_AFTER = r",.;:!\]})»>"
NON_WORD_CHAR = r",./\\<>;:'\"\[\]{}()!@#$%^&*+=_«» \t\n-"
WORD_CHAR = f"^{NON_WORD_CHAR}"
WORD_RE = re.compile(
    fr"""
        ([{WORD_CHAR}]+)
        ([{NON_WORD_CHAR}]*)
    """,
    re.S | re.X,
)
PUNC_RE = re.compile(
    fr"""
        ^
        ([{NON_WORD_CHAR}]+)
        $
    """,
    re.S | re.X,
)
PUNC_DELIM_BEFORE_RE = re.compile(fr"""^[{PUNC_DELIM_BEFORE}]""")
PUNC_DELIM_AFTER_RE = re.compile(fr"""[{PUNC_DELIM_AFTER}]$""")
WORD = "word"


def addText(cv, text, cur):
    if text:
        # check first if there is only punctuation and white space
        # in that case: one slot
        match = PUNC_RE.match(text)
        if match:
            punc = match.group(1)
            punc = WHITE_RE.sub(" ", punc)
            punc = punc.replace("\n", " ")
            if PUNC_DELIM_BEFORE_RE.search(punc):
                punc = f" {punc}"
            if PUNC_DELIM_AFTER_RE.search(punc):
                punc += " "
            if punc and WORD in cur:
                lastPunc = cv.get("punc", cur["word"])
                lastPunc += punc
                cv.feature(cur["word"], punc=lastPunc.replace("  ", " "))
            return

        # if the text starts with white space, strip it and add it to the current word

        bareText = text.lstrip()
        if bareText != text:
            addSpaceBefore(cv, cur)
            text = bareText

        # if there is a mixture between word characters and the rest
        # group them in pieces consisting of word characters with trailing
        # punctuation and white space

        for match in WORD_RE.finditer(text):
            (trans, punc) = match.group(1, 2)
            trans = trans.strip("«»")
            if punc:
                punc = WHITE_RE.sub(" ", punc)
                punc = punc.replace("\n", " ")
                if PUNC_DELIM_BEFORE_RE.search(punc):
                    punc = f" {punc}"
                if PUNC_DELIM_AFTER_RE.search(punc):
                    punc += " "
            curWord = cv.slot()
            cur["word"] = curWord
            cv.feature(curWord, trans=trans, punc=punc)

            for tag in TEXT_ATTRIBUTES:
                if cur.get(tag, None):
                    cv.feature(curWord, **{f"is{tag}": 1})

            isComment = False

            for tag in COMMENT_ELEMENTS:
                if cur.get(f"is_{tag}", None):
                    cv.feature(curWord, **{f"is{tag}": 1})
                    if tag == NOTE:
                        cv.feature(curWord, transn=trans, puncn=punc)
                    else:
                        cv.feature(curWord, transr=trans, puncr=punc)
                    isComment = True

            if not isComment:
                cv.feature(curWord, transo=trans, punco=punc)
                cv.feature(curWord, isorig=1)


# TF LOADING (to test the generated TF)


def loadTf():
    TF = Fabric(locations=[OUT_DIR])
    allFeatures = TF.explore(silent=True, show=True)
    loadableFeatures = allFeatures["nodes"] + allFeatures["edges"]
    api = TF.load(loadableFeatures, silent=False)
    if api:
        print(f"max node = {api.F.otype.maxNode}")
        # print("Frequency of author")
        # print(api.F.author.freqList()[0:20])
        # print("Frequency of words")
        # print(api.F.trans.freqList()[0:20])


# MAIN


def main():
    args = () if len(sys.argv) == 1 else tuple(sys.argv[1:])

    doLoad = "load" in args or "loadonly" in args
    doConvert = "loadonly" not in args

    vol = None
    lid = None

    for arg in args:
        if arg == "--help":
            print(HELP)
            return True

    (good, vol, lid, kwargs, pargs) = parseArgs(args)

    print(f"trimmed TEI to TF converter for {REPO}")
    print(f"TEI source version = {VERSION_SRC}")
    print(f"TF  target version = {VERSION_TF}")

    if doConvert:
        if not convert(vol, lid):
            return False

    if doLoad:
        loadTf()

    return True


sys.exit(0 if main() else 1)
