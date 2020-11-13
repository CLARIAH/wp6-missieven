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
"loadOnly": does not generate TF; loads previously generated TF
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
    "fmt:text-orig-source": "{transo}{punco}",
    "fmt:text-orig-remark": "{transr}{puncr}",
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
        day
        month
        year
        remark
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
    "emph": {
        "description": "whether a word is emphasized by typography",
        "format": "integer 1 or absent",
    },
    "facs": {
        "description": (
            "url part of the corresponding online facsimile page;"
            " the url itself can be constructed using a hard coded template."
            " See also the tpl feature"
        )
    },
    "fnote": {
        "description": "all footnotes at that position",
        "format": "string with mark down formatting, separated by newlines",
    },
    "folio": {
        "description": "label indicating a folio break",
        "format": (
            "string of the form `Fol. {n} {rv}` where rv is a recto/verso indication"
        ),
    },
    "month": {
        "description": "month part of the date of the letter",
        "format": "numeral between 1 and 12 inclusive",
    },
    "n": {"description": "number of a volume, letter, page, para, line, table"},
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
    "rawdate": {
        "description": "the date the letter was sent",
        "format": "informal Dutch date notation",
    },
    "ref": {
        "description": "whether a word belongs to the text of reference",
        "format": "integer 1 or absent",
    },
    "remark": {
        "description": "whether a word belongs to the text of editorial remarks",
        "format": "integer 1 or absent",
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
    "special": {
        "description": (
            "whether a word has special typography"
            " possibly with OCR mistakes as well"
        ),
        "format": "integer 1 or absent",
    },
    "status": {
        "description": "status of the letter, e.g. secret, copy",
        "format": "keyword",
    },
    "sub": {
        "description": (
            "whether a word has subscript typography"
            " possibly indicating the denominator of a fraction"
        ),
        "format": "integer 1 or absent",
    },
    "super": {
        "description": (
            "whether a word has superscript typography"
            " possibly indicating the numerator of a fraction"
        ),
        "format": "integer 1 or absent",
    },
    "title": {
        "description": "title of the letter",
        "format": "comma-separated values",
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
    "trans": {"description": "transcription of a word"},
    "transo": {"description": "transcription of a word, only for original text"},
    "transr": {"description": "transcription of a word, only for remark text"},
    "und": {
        "description": "whether a word is underlined by typography",
        "format": "integer 1 or absent",
    },
    "vol": {"description": "volume number", "format": "positive integer"},
    "year": {
        "description": "year part of the date of the letter",
        "format": "numeral between 1600 and 1800",
    },
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
    notes = dict(
        marks={},
        markOrder=[],
        bodies={},
        bodyOrder=[],
        totalMarks=0,
        totalBodies=0,
        ambiguousMarks={},
        ambiguousBodies={},
        unresolvedMarks={},
        unresolvedBodies={},
        unmarkedBodies={},
    )

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
            if givenLid is not None and lid not in givenLid:
                continue
            sys.stderr.write(f"\r\t{lid}      ")
            with open(f"{thisSrcDir}/{name}.xml") as fh:
                text = fh.read()
                root = ET.fromstring(text)
            walkLetter(cv, doc, root, cur, notes)

        cv.terminate(cur["volume"])
        cur["volume"] = None

    print("\rdone" + " " * 70)

    reportNotes(notes)

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


def walkLetter(cv, doc, root, cur, notes):
    cur["letter"] = cv.node("letter")
    cur["ln"] = 0
    cur["p"] = 0
    cur["fn"] = None

    for child in root:
        if child.tag == "header":
            collectMeta(cv, child, cur)
        if child.tag == "body":
            walkNode(cv, doc, child, cur, notes)

    curLine = cur.get("line", None)
    if curLine:
        linkIfEmpty(cv, curLine)
        cv.terminate(curLine)
        cur["line"] = None
    doNotes(cv, cur, notes)
    curPage = cur.get("page", None)
    if curPage:
        linkIfEmpty(cv, curPage)
        cv.terminate(curPage)
        cur["page"] = None
    cv.terminate(cur["letter"])
    cur["letter"] = None


TEXT_ATTRIBUTES = """
    emph
    remark
    special
    sub
    super
    und
    ref
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
    folio
    ref
    remark
""".strip().split()
)

DO_TEXT_ELEMENTS = set(
    """
    cell
    emph
    folio
    head
    para
    ref
    remark
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
    folio
    fref
    lb
    pb
    table
    ref
    remark
    special
    subhead
    sub
    super
    und
""".strip().split()
)

DOWN_REF_RE = re.compile(r"""\[=([^\]]*)\]""")


def linkIfEmpty(cv, node):
    if not cv.linked(node):
        emptySlot = cv.slot()
        cv.feature(emptySlot, trans="", punc="")


def walkNode(cv, doc, node, cur, notes):
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
    sub | inline formatting (subscript) | binary feature sub
    super | inline formatting (superscript) | binary feature super
    und | inline formatting (underline) | binary feature und
    special | inline formatting | binary feature special
    folio | reference to a folio page | feature folio
    remark | editorial text in the text flow | feature remark
    fnote.ref | footnote text at the end of a page | feature footnote at place of fref
    fref.ref | footnote reference within the text flow | used to bind fnote to this spot
    """

    tag = node.tag
    atts = node.attrib

    if tag in PREVENT_NEST:
        if cur.get(tag, None):
            cv.terminate(cur[tag])
            cur[tag] = None
            warnings[f"nested: {tag}"].add(doc)

    if tag in BREAKS:
        curLine = cur.get("line", None)
        curFn = cur.get("fn", None)
        if curLine:
            linkIfEmpty(cv, curLine)
            cv.terminate(curLine)
        if tag == "pb":
            doNotes(cv, cur, notes)
            curPage = cur.get("page", None)
            if curPage:
                linkIfEmpty(cv, curPage)
                cv.terminate(curPage)
            cur["page"] = cv.node("page")
            cv.feature(cur["page"], **featsFromAtts(atts))
            cur["pg"] = f"{cur['vol']:>02}:p{atts['n']:>04}"
            if not curFn:
                cur["ln"] = 1
        elif tag == "lb":
            if not curFn:
                cur["ln"] += 1
        if not curFn:
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
        curNode = cv.node(tag)
        cur[tag] = curNode
        cur[f"is_{tag}"] = 1
        if atts:
            cv.feature(curNode, **featsFromAtts(atts))

    elif tag in TEXT_ATTRIBUTES:
        cur[tag] = 1

    elif tag == "fref":
        notes["marks"].setdefault(atts.get("ref", ""), []).append(
            (cur["word"], cur["ln"])
        )
        notes["totalMarks"] += 1

    elif tag == "fnote":
        bodies = notes["bodies"]
        fref = atts.get("ref", "")
        notes["totalBodies"] += 1
        if fref in bodies:
            curPg = cur.get("pg", None)
            notes["ambiguousBodies"].setdefault(fref, {})[curPg] = len(bodies)
        else:
            bodies[fref] = []
        bodies[fref].append(node.text or "")
        cur["fn"] = bodies[fref]

    elif tag in TRANSPARENT_ELEMENTS:
        pass

    else:
        errors[f"unrecognized: {tag}"].add(doc)

    if tag in DO_TEXT_ELEMENTS:
        addText(cv, node.text, cur)

    for child in node:
        walkNode(cv, doc, child, cur, notes)

    curNode = cur.get(tag, None)

    if tag in NODE_ELEMENTS:
        if curNode:
            linkIfEmpty(cv, curNode)
            cv.terminate(cur[tag])
            cur[tag] = None

    elif tag in COMMENT_ELEMENTS:
        if cur.get(tag, None):
            linkIfEmpty(cv, curNode)
            cv.terminate(cur[tag])
            cur[tag] = None
        cur[f"is_{tag}"] = None

    elif tag in TEXT_ATTRIBUTES:
        cur[tag] = None

    elif tag == "fnote":
        cur["fn"] = None

    if tag in ADD_LB_ELEMENTS:
        curLine = cur.get("line", None)
        curFn = cur.get("fn", None)
        if curLine:
            linkIfEmpty(cv, curLine)
            cv.terminate(curLine)
        if not curFn:
            cur["ln"] += 1

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
        feat: int(value.lstrip("0")) if feat in intFeatures else value
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

NON_WORD_CHAR = r",./\\<>;:'\"\[\]{}()!@#$%^&*+=_«» \t\n-"
WORD_CHAR = f"^{NON_WORD_CHAR}"
WORD_RE = re.compile(
    fr"""
        ([{WORD_CHAR}]+)
        ([{NON_WORD_CHAR}]*)
    """,
    re.S | re.X,
)


def addText(cv, text, cur):
    if text:
        dest = cur["fn"]
        if dest is not None:
            dest.append(text)
        else:
            for match in WORD_RE.finditer(text):
                (trans, punc) = match.group(1, 2)
                trans = trans.strip("«»")
                if punc:
                    punc = WHITE_RE.sub(" ", punc)
                    punc = punc.replace("\n", " ")
                curWord = cv.slot()
                cur["word"] = curWord
                cv.feature(curWord, trans=trans, punc=punc)
                for tag in TEXT_ATTRIBUTES:
                    if cur.get(tag, None):
                        cv.feature(curWord, **{tag: 1})
                isComment = False
                for tag in COMMENT_ELEMENTS:
                    if cur.get(f"is_{tag}", None):
                        isComment = True
                        cv.feature(curWord, **{tag: 1})
                if isComment:
                    cv.feature(curWord, transr=trans, puncr=punc)
                else:
                    cv.feature(curWord, transo=trans, punco=punc)


def doNotes(cv, cur, notes):
    if "word" not in cur:
        return

    markInfo = notes["marks"]
    markOrder = notes["markOrder"]
    bodyInfo = notes["bodies"]
    bodyOrder = notes["bodyOrder"]

    curPg = cur.get("pg", None)

    wordNotes = collections.defaultdict(list)

    # for (word, noteTexts) in wordNotes.items():
    #    cv.feature(word, fnote="\n\n".join(noteTexts))

    for (mark, occs) in markInfo.items():
        bodiesText = "\n\n".join(bodyInfo[mark]) if mark in bodyInfo else ""
        for (word, line) in occs:
            wordNotes[word].append(f"{mark}. {bodiesText}")

        if len(occs) > 1:
            notes["ambiguousMarks"].setdefault(mark, {})[curPg] = occs
        if mark not in bodyInfo:
            notes["unresolvedMarks"].setdefault(mark, {})[curPg] = occs

    word = cur["word"]
    for (mark, bodies) in bodyInfo.items():
        if mark == "":
            notes["unmarkedBodies"][curPg] = len(bodies)
        if mark not in markInfo:
            notes["unresolvedBodies"].setdefault(mark, {})[curPg] = len(bodies)
            bodiesText = "\n\n".join(bodies)
            markRep = mark if mark else "??"
            wordNotes[word].append(f"{markRep}. {bodiesText}")

    for (word, texts) in wordNotes.items():
        cv.feature(word, fnote="\n\n".join(texts))

    markInfo.clear()
    markOrder.clear()

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
        print("Frequency of author")
        print(api.F.author.freqList()[0:20])
        print("Frequency of words")
        print(api.F.trans.freqList()[0:20])


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
