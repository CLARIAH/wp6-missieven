import sys
import os
import collections
import re
from itertools import chain

import yaml
import xml.etree.ElementTree as ET


# CONFIG READING


def readYaml(fileName):
    if os.path.exists(fileName):
        with open(fileName) as y:
            y = yaml.load(y, Loader=yaml.FullLoader)
    else:
        y = {}
    return y


# LOCATIONS

LOCAL = os.path.expanduser("~/local")
BASE = os.path.expanduser("~/github")
ORG = "Dans-labs"
REPO = "clariah-gm"

REPO_DIR = f"{BASE}/{ORG}/{REPO}"
SOURCE_DIR = f"{LOCAL}/{REPO}"

DECL_PATH = f"{REPO_DIR}/yaml"
META_DECL_FILE = f"{DECL_PATH}/meta.yaml"

META_DECL = readYaml(META_DECL_FILE)

VERSION_SRC = META_DECL["versionSrc"]
VERSION_TF = META_DECL["versionTf"]

IN_DIR = f"{SOURCE_DIR}/{VERSION_SRC}/tei"
TRIM_DIR = f"{SOURCE_DIR}/{VERSION_SRC}/trim"
REPORT_DIR = f"{REPO_DIR}/trimreport"

TF_DIR = f"{REPO_DIR}/tf"
OUT_DIR = f"{TF_DIR}/{VERSION_TF}"

MERGE_DOCS = {
    "06:p0406": ("06:p0407",),
}
SKIP_DOCS = {x for x in chain.from_iterable(MERGE_DOCS.values())}

HI_CLEAN_STRONG_RE = re.compile(r"""<hi\b[^>]*>([^<]*)</hi>""", re.S)

# FILESYSTEM OPERATIONS


def clearTree(path):
    """Remove all files from a directory, recursively, but leave subdirs.

    Reason: we want to inspect output in an editor.
    But if we remove the directories, the editor looses its current directory
    all the time.
    """

    subdirs = []
    with os.scandir(path) as dh:
        for (i, entry) in enumerate(dh):
            name = entry.name
            if name.startswith("."):
                continue
            if entry.is_file():
                os.remove(f"{path}/{name}")
            elif entry.is_dir():
                subdirs.append(name)

    for subdir in subdirs:
        clearTree(f"{path}/{subdir}")


# SOURCE READING


PAGENUM_RE = re.compile(
    r"""<interpGrp type="page"><interp>([0-9]+)</interp></interpGrp>""", re.S
)


def getPage(path):
    with open(path) as fh:
        text = fh.read()
    match = PAGENUM_RE.search(text)
    return f"p{int(match.group(1)):>04}" if match else None


def getVolumes(srcDir):
    volumes = []
    with os.scandir(srcDir) as dh:
        for entry in dh:
            if entry.is_dir():
                vol = entry.name
                if not vol.isdigit():
                    continue
                volumes.append(f"{int(vol):>02}")
    return sorted(volumes)


def getLetters(srcDir, idMap=None):
    letters = []
    collisions = 0
    lidSet = set()

    with os.scandir(srcDir) as dh:
        for entry in dh:
            if entry.is_file():
                name = entry.name
                if name.endswith(".xml"):
                    pureName = name[0:-4]
                    if idMap is not None:
                        lid = getPage(f"{srcDir}/{name}")
                        if lid in lidSet:
                            collisions += 1
                        lidSet.add(lid)
                        idMap[pureName] = lid
                    letters.append(pureName)
    if collisions:
        print(f"MAPPING from letter ids to first pages: {collisions} collisions")
        return ()
    return tuple(sorted(letters))


# ANALYSIS


NUM_RE = re.compile(r"""[0-9]""", re.S)


def nodeInfo(node, analysis, after=False):
    tag = node.tag
    atts = node.attrib

    if not atts:
        analysis[f"{tag}.."] += 1
    else:
        for (k, v) in atts.items():
            vTrim = NUM_RE.sub("n", v)
            if k == "value":
                vTrim = "x"
            isLayout = k == "rend"
            if after:
                if isLayout:
                    analysis[f" {tag}.{k}={v}"] += 1
                else:
                    analysis[f"{tag}.{k}={vTrim}"] += 1
            else:
                if not isLayout:
                    analysis[f"{tag}.{k}={vTrim}"] += 1

    for child in node:
        nodeInfo(child, analysis, after=after)


def analyse(text, after=False):
    analysis = collections.Counter()
    root = ET.fromstring(text)
    nodeInfo(root, analysis, after=after)
    return analysis


BODY_RE = re.compile(r"""<body[^>]*>(.*?)</body>""", re.S)


def combineTexts(first, following):
    bodies = []

    for text in following:
        match = BODY_RE.search(text)
        bodies.append(match.group(1))

    return first.replace("</body", ("\n".join(bodies)) + "</body>")


# TOP-LEVEL TRIM


def trim(stage, givenVol, givenLid, trimPage, processPage, *args, **kwargs):
    if stage == 0:
        SRC = IN_DIR
    else:
        SRC = f"{TRIM_DIR}{stage - 1}"
    DST = f"{TRIM_DIR}{stage}"
    REP = f"{REPORT_DIR}{stage}"

    if os.path.exists(DST):
        clearTree(DST)
    os.makedirs(DST, exist_ok=True)
    os.makedirs(REP, exist_ok=True)

    volumes = getVolumes(SRC)

    analysis = collections.Counter()
    analysisAfter = collections.Counter()

    info = dict(
        table=0,
        docs=[],
        captionInfo=collections.defaultdict(list),
        captionNorm=collections.defaultdict(list),
        captionVariant=collections.defaultdict(list),
        captionRoman=collections.defaultdict(list),
        folioResult=collections.defaultdict(list),
        folioTrue=collections.defaultdict(list),
        folioFalse=collections.defaultdict(list),
        folioUndecided=collections.defaultdict(lambda: collections.defaultdict(list)),
        headInfo=collections.defaultdict(list),
        bigTitle={},
        splits=[],
        splitsX=[],
    )

    mergeText = {}

    for vol in volumes:
        if givenVol is not None and givenVol != vol:
            continue
        print(f"\rvolume {vol}" + " " * 70)

        volDir = vol.lstrip("0") if stage == 0 else vol
        thisSrcDir = f"{SRC}/{volDir}"
        thisDstDir = f"{DST}/{vol}"
        os.makedirs(f"{thisDstDir}/rest", exist_ok=True)

        info["vol"] = vol
        idMap = {} if stage == 0 else None
        letters = getLetters(thisSrcDir, idMap)

        if stage == 1:
            for name in letters:
                lid = name if idMap is None else idMap[name]
                if givenLid is not None and givenLid != lid:
                    continue
                doc = f"{vol}:{lid}"
                if doc in SKIP_DOCS:
                    continue
                if doc in MERGE_DOCS:
                    with open(f"{thisSrcDir}/{name}.xml") as fh:
                        text = fh.read()
                    followTexts = []
                    for followDoc in MERGE_DOCS[doc]:
                        followName = followDoc.split(":", 1)[1] + ".xml"
                        with open(f"{thisSrcDir}/{followName}") as fh:
                            followTexts.append(fh.read())
                    mergeText[doc] = combineTexts(text, followTexts)

        for name in letters:
            lid = name if idMap is None else idMap[name]
            if givenLid is not None and givenLid != lid:
                continue
            doc = f"{vol}:{lid}"
            if stage == 1 and doc in SKIP_DOCS:
                continue
            sys.stderr.write(f"\r\t{lid}      ")
            info["doc"] = doc
            info["docs"].append(doc)

            if stage == 1 and doc in mergeText:
                text = mergeText[doc]
            else:
                with open(f"{thisSrcDir}/{name}.xml") as fh:
                    text = fh.read()
            origText = text

            thisAnalysis = analyse(text)
            for (path, count) in thisAnalysis.items():
                analysis[path] += count
            text = trimDocument(
                stage, text, trimPage, info, processPage, *args, **kwargs
            )
            if text is None:
                dstName = f"{lid}.xml"
                with open(f"{thisDstDir}/rest/{dstName}", "w") as fh:
                    fh.write(origText)
                continue

            dstName = f"{lid}.xml"
            with open(f"{thisDstDir}/{dstName}", "w") as fh:
                fh.write(text)

            thisAnalysisAfter = analyse(text, after=True)
            for (path, count) in thisAnalysisAfter.items():
                analysisAfter[path] += count

    print("\rdone" + " " * 70)

    with open(f"{REP}/elementsIn.tsv", "w") as fh:
        for (path, amount) in sorted(analysis.items()):
            fh.write(f"{path}\t{amount}\n")

    with open(f"{REP}/elementsOut.tsv", "w") as fh:
        for (path, amount) in sorted(analysisAfter.items()):
            fh.write(f"{path}\t{amount}\n")

    captionInfo = info["captionInfo"]
    captionNorm = info["captionNorm"]
    captionVariant = info["captionVariant"]
    captionRoman = info["captionRoman"]
    if captionNorm or captionVariant or captionInfo or captionRoman:
        print("CAPTIONS:")
        print(f"\t{len(captionNorm):>3} verified names")
        print(f"\t{len(captionVariant):>3} unresolved variants")
        print(f"\t{len(captionRoman):>3} malformed roman numerals")
        with open(f"{REP}/fwh-yes.tsv", "w") as fh:
            for (captionSrc, tag) in (
                (captionNorm, "OK"),
                (captionVariant, "XX"),
                (captionInfo, "II"),
                (captionRoman, "RR"),
            ):
                for caption in sorted(captionSrc):
                    docs = captionSrc[caption]
                    firstDoc = docs[0]
                    nDocs = len(docs)
                    fh.write(f"{firstDoc} {nDocs:>4}x {tag} {caption}\n")

    folioUndecided = info["folioUndecided"]
    folioTrue = info["folioTrue"]
    folioFalse = info["folioFalse"]
    folioResult = info["folioResult"]
    if folioUndecided or folioTrue or folioFalse:
        with open(f"{REP}/folio.txt", "w") as fh:
            for (folioSrc, tag) in (
                (folioFalse, "NO "),
                (folioTrue, "YES"),
                (folioResult, "FF"),
            ):
                triggers = 0
                occs = 0
                for folio in sorted(folioSrc):
                    docs = folioSrc[folio]
                    firstDoc = docs[0]
                    nDocs = len(docs)
                    triggers += 1
                    occs += nDocs
                    fh.write(f"{firstDoc} {nDocs:>4}x {tag} {folio}\n")
                print(f"FOLIO {tag}:")
                print(f"\t{tag}: {triggers:>2} with {occs:>4} occurrences")
            if folioUndecided:
                totalContexts = sum(len(x) for x in folioUndecided.values())
                totalOccs = sum(
                    sum(len(x) for x in folioInfo.values())
                    for folioInfo in folioUndecided.values()
                )
                print(
                    f"FOLIOS (undecided): {len(folioUndecided)} triggers,"
                    f" {totalContexts} contexts,"
                    f" {totalOccs} occurrences"
                )
                for (fol, folInfo) in sorted(
                    folioUndecided.items(), key=lambda x: (len(x[1]), x[0])
                ):
                    nContexts = len(folInfo)
                    nOccs = sum(len(x) for x in folInfo.values())
                    msg = f"{fol:<20} {nContexts:>3} contexts, {nOccs:>4} occurrences"
                    print(f"\t{msg}")
                    fh.write(f"{msg}\n")
                    for (context, pages) in sorted(
                        folInfo.items(), key=lambda x: (len(x[1]), x[0])
                    ):
                        fh.write(f"\t{pages[0]} {len(pages):>4}x: {context}\n")

    docs = info["docs"]
    totalDocs = len(docs)
    print(f"{totalDocs} documents")

    if stage == 1:
        splits = info["splits"]
        splitsX = info["splitsX"]
        headInfo = info["headInfo"]
        bigTitle = info["bigTitle"]

        for doc in docs:
            if doc not in headInfo:
                headInfo[doc] = []

        noHeads = []
        singleHeads = []
        shortHeads = []

        for doc in sorted(docs):
            if doc in bigTitle:
                continue
            heads = headInfo[doc]
            nHeads = len(heads)
            if nHeads == 0:
                noHeads.append(doc)
            else:
                for (fullDoc, head) in heads:
                    if len(head) < 40 and "BIJLAGE" not in head:
                        shortHeads.append((fullDoc, head))
                if nHeads > 1:
                    theseSplits = splitDoc(doc)
                    for ((startDoc, newDoc, sHead), (fullDoc, mHead)) in zip(
                        theseSplits, heads
                    ):
                        newPage = newDoc[4:]
                        expPage = fullDoc[9:]
                        if newPage == expPage and sHead == mHead:
                            singleHeads.append((newDoc, sHead))
                            splits.append((startDoc, newDoc, sHead))
                        else:
                            splitsX.append((startDoc, newPage, expPage, sHead, mHead))
                else:
                    singleHeads.append((doc, heads[0][1]))

        print(f"\t: {len(shortHeads):>3} short headings")
        print(f"\t: {len(noHeads):>3} without heading")
        print(f"\t: {len(singleHeads):>3} with single heading")
        print(f"\t: {len(noHeads) + len(singleHeads):>3} letters")
        print(f"\t: {len(splits):>3} split-off letters")
        print(f"\t: {len(splitsX):>3} split-off errors")
        print(f"\t: {len(bigTitle):>3} rest documents")

        with open(f"{REP}/heads.tsv", "w") as fh:
            for doc in noHeads:
                fh.write(f"{doc} NO\n")
            for (mainDoc, (doc, head)) in shortHeads:
                fh.write(f"{doc} =SHORT=> {head}\n")
            for (doc, head) in singleHeads:
                etc = " ... " if len(head) > 70 else ""
                fh.write(f"{doc} => {head[0:70]}{etc}\n")

        with open(f"{REP}/rest.tsv", "w") as fh:
            for (doc, head) in sorted(bigTitle.items()):
                msg = f"{doc} => {head}"
                fh.write(f"{msg}\n")

        with open(f"{REP}/splits.tsv", "w") as fh:
            for (startDoc, newDoc, sHead) in splits:
                etc = " ... " if len(sHead) > 50 else ""
                fh.write(f"{startDoc} =OK=> {newDoc} {sHead[0:50]}\n")
            for (startDoc, newPage, expPage, sHead, mHead) in splitsX:
                label = "===" if newPage == expPage else "=/="
                fh.write(f"{startDoc} =XX=> {newPage} {label} {expPage}\n")
                if sHead != mHead:
                    fh.write(f"\t{sHead}\n\t===versus===\n\t{mHead}\n")

    return True


SPLIT_DOC_RE = re.compile(
    r"""
        <pb\b[^>]*?\bn="([0-9]+)"[^>]*>\s*
        (?:
            <pb\b[^>]*>\s*
        )*
        (?:
            <p\b[^>]*>.*?</p>\s*
        )?
        <head\b[^>]*>(.*?)</head>
    """,
    re.S | re.X,
)
HEADER_RE = re.compile(r"""^.*?</header>\s*""", re.S)


def splitDoc(doc):
    stage = 1
    (vol, startPage) = doc.split(":")
    path = f"{TRIM_DIR}{stage}/{doc.replace(':', '/')}.xml"
    with open(path) as fh:
        text = fh.read()

    match = HEADER_RE.match(text)
    header = match.group(0)

    match = BODY_RE.search(text)
    body = match.group(1)

    lastPage = None
    lastHead = None
    lastIndex = 0
    splits = []

    for (i, match) in enumerate(SPLIT_DOC_RE.finditer(body)):
        pageNum = f"{int(match.group(1)):>04}"
        page = f"p{pageNum}"
        head = HI_CLEAN_STRONG_RE.sub(
            r"""\1""", match.group(2).replace("<lb/>", " ").replace("\n", " ")
        )

        if i == 0:
            lastPage = page
            lastHead = head
            continue

        (b, e) = match.span()
        lastText = body[lastIndex:b]

        writeDoc(vol, lastPage, header, lastText)
        splits.append((doc, f"{vol}:{lastPage}", lastHead))
        lastPage = page
        lastHead = head
        lastIndex = b

    if i > 0:
        lastText = body[lastIndex:]
        writeDoc(vol, lastPage, header, lastText)
        splits.append((doc, f"{vol}:{lastPage}", lastHead))

    return splits


def writeDoc(vol, page, header, text):
    stage = 1
    with open(f"{TRIM_DIR}{stage}/{vol}/{page}.xml", "w") as fh:
        fh.write(f"{header}{text}</body>\n</teiTrim>")


HEADER_TITLE_RE = re.compile(
    r"""
        <meta\s+
        key="title"\s+
        value="([^"]*)"
    """,
    re.S | re.X,
)


REST_RE = re.compile(
    r"""
    ^
    (?:
        index
        |
        indices
        |
        toelichting
    )
    """,
    re.S | re.I | re.X,
)


BIG_TITLE_PART_RE = re.compile(
    r"""
    (
        \s*
        <pb\b[^>]*?\bn="([^"]*)"[^>]*>
        \s*
        (?:
            <pb\b[^>]*?\bn="[^"]*"[^>]*>
            \s*
        )*
        <bigTitle>(.*?)</bigTitle>
        \s*
        (?:
            (?:
                (?:
                    <p\b[^>]*>.*?</p>
                )
                |
                (?:
                    <pb\b[^>]*>
                )
            )
            \s*
        )*
        \s*
    )
    """,
    re.S | re.X,
)


BIG_TITLE_RE = re.compile(r"""<bigTitle>(.*?)</bigTitle>""", re.S)
PB_P_PERM_RE = re.compile(
    r"""
    (
        (?:
            <pb\b[^>]*>\s*
        )+
    )
    (
        </p>
    )
    """,
    re.S | re.X,
)


def trimDocument(stage, text, trimPage, info, processPage, *args, **kwargs):
    headElem = "teiHeader" if stage == 0 else "header"
    headerRe = re.compile(rf"""<{headElem}[^>]*>(.*?)</{headElem}>""", re.S)
    match = headerRe.search(text)
    header = (
        trimHeader(match, *args, **kwargs)
        if stage == 0
        else f"""<header>\n{match.group(1)}\n</header>"""
    )
    if stage == 1:
        doc = info["doc"]
        bigTitle = info["bigTitle"]
        match = HEADER_TITLE_RE.search(header)
        if match:
            title = match.group(1)
            if REST_RE.match(title):
                bigTitle[doc] = HI_CLEAN_STRONG_RE.sub(
                    r"""\1""", title.replace("<lb/>", " ").replace("\n", " ")
                )
                return None

    match = BODY_RE.search(text)
    text = match.group(1)

    body = trimBody(stage, text, trimPage, info, processPage, *args, **kwargs)

    if stage == 1:
        body = PB_P_PERM_RE.sub(r"""\2\n\1""", body)
        match = BIG_TITLE_PART_RE.search(body)

        if match:
            vol = info["vol"]
            doc = info["doc"]

            text = match.group(1)

            if text == body:
                head = match.group(3)
                bigTitle[doc] = HI_CLEAN_STRONG_RE.sub(
                    r"""\1""", head.replace("<lb/>", " ").replace("\n", " ")
                )
                return None

            bigTitles = BIG_TITLE_PART_RE.findall(body)
            for (page, pnum, head) in bigTitles:
                pnum = f"p{int(pnum):>04}"
                doc = f"{vol}:{pnum}"
                bigTitle[doc] = HI_CLEAN_STRONG_RE.sub(
                    r"""\1""", head.replace("<lb/>", " ").replace("\n", " ")
                )
                fileName = f"{pnum}.xml"
                path = f"{TRIM_DIR}{stage}/{vol}/rest/{fileName}"
                with open(path, "w") as fh:
                    fh.write(page)

            body = BIG_TITLE_PART_RE.sub("", body)

    return f"""<teiTrim>\n{header}\n<body>\n{body}\n</body>\n</teiTrim>"""


# TRIM HEADER


META_AUTHOR_RE = re.compile(
    r"""<interpGrp type="authorLevel1">\s*((?:<interp>.*?</interp>\s*)*)</interpGrp>""",
    re.S,
)


def getAuthors(match):
    material = match.group(1)
    material = material.replace("<interp>", "")
    material = material.replace("</interp>", ", ")
    material = material.strip()
    material = material.strip(",")
    material = material.strip()
    return f"""<meta key="authors" value="{material}"/>"""


CLEAR_DATE_RE = re.compile(r"""<date>.*?</date>""", re.S)
CLEAR_TITLE_RE = re.compile(r"""<title>.*?</title>""", re.S)
DELETE_ELEM_RE = re.compile(
    r"""</?(?:TEI|text|bibl|"""
    r"""fileDesc|listBibl|notesStmt|publicationStmt|sourceDesc|titleStmt)\b[^>]*>"""
)
DELETE_EMPTY_RE = re.compile(r"""<note[^>]*/>""", re.S)
DELETE_P_RE = re.compile(r"""</?p>""", re.S)
IDNO_RE = re.compile(r"""<idno (.*?)</idno>""", re.S)
META_DELETE_RE = re.compile(
    r"""<interpGrp type="(?:tocLevel|volume)">\s*<interp>.*?</interp></interpGrp>""",
    re.S,
)
META_RES = {
    newKey: re.compile(
        rf"""<interpGrp type="{oldKey}">\s*<interp>(.*?)</interp></interpGrp>""", re.S
    )
    for (newKey, oldKey) in (
        ("pid", "pid"),
        ("page", "page"),
        ("seq", "n"),
        ("title", "titleLevel1"),
        ("rawdate", "dateLevel1"),
        ("place", "localization_placeLevel1"),
        ("yearFrom", "witnessYearLevel1_from"),
        ("yearTo", "witnessYearLevel1_to"),
        ("monthFrom", "witnessMonthLevel1_from"),
        ("monthTo", "witnessMonthLevel1_to"),
        ("dayFrom", "witnessDayLevel1_from"),
        ("dayTo", "witnessDayLevel1_to"),
    )
}
WHITE_NLNL_RE = re.compile(r"""\n{3,}""", re.S)
WHITE_NL_RE = re.compile(r"""(?:[ \t]*\n[ \t\n]*)""", re.S)
SPACE_RE = re.compile(r"""  +""", re.S)
WHITE_RE = re.compile(r"""\s\s+""", re.S)
PB_RE = re.compile(r"""<pb\b[^>]*/>""", re.S)


def trimHeader(match, *args, **kwargs):
    text = match.group(1)
    for trimRe in (
        CLEAR_TITLE_RE,
        CLEAR_DATE_RE,
        DELETE_ELEM_RE,
        DELETE_EMPTY_RE,
    ):
        text = trimRe.sub("", text)

    text = IDNO_RE.sub(r"", text)

    for (val, trimRe) in META_RES.items():
        text = trimRe.sub(rf"""<meta key="{val}" value="\1"/>""", text)

    text = META_AUTHOR_RE.sub(getAuthors, text)

    for trimRe in (META_DELETE_RE, DELETE_P_RE):
        text = trimRe.sub("", text)
    text = WHITE_NL_RE.sub("\n", text)
    return f"<header>\n{text}\n</header>\n"


PB_CHECK_PAT = "|".join(
    """
    fw
    head
    hi
    table
    cell
    row
    note
""".strip().split()
)
CHECK_PB_RE = re.compile(rf"""<({PB_CHECK_PAT})\b[^>]*>(.*?)</\1>""", re.S)


def checkPb(text):
    breaks = collections.Counter()

    for match in CHECK_PB_RE.finditer(text):
        elem = match.group(1)
        material = match.group(2)
        if "<pb" in material:
            breaks[elem] += 1
    return breaks


X_RE = re.compile(r"""\s*xml:?[a-z]+=['"][^'"]*['"]""", re.S)
FACS_REF1_RE = re.compile(
    r"""facs=['"]http://resources.huygens.knaw.nl/"""
    r"""retroapp/service_generalemissiven/gm_(.+?)/"""
    r"""images/gm_(.+?).tif['"]""",
    re.S,
)
FACS_REF2_RE = re.compile(
    r"""facs=['"]http://resources.huygens.knaw.nl/"""
    r"""retroapp/service_generalemissiven/gm_(.+?)/"""
    r"""images/generale_missiven_gs(.+?).tif['"]""",
    re.S,
)
PAGE_NUM_RE = re.compile(r"""<pb[^>]*?\bn=['"]([0-9]+)['"]""", re.S)

NL_B_RE = re.compile(r"""\n*<(p|para|note|fw|table|row)\b([^>]*)>""", re.S)
NL_E_RE = re.compile(r"""</(p|para|note|fw|table|row)\b>\n*""", re.S)
LB_RE = re.compile(r"""<lb/>\n*""", re.S)
DIV_CLEAN_RE = re.compile(r"""</?div\b[^>]*>""", re.S)
P_INTERRUPT_RE = re.compile(
    r"""
        </p>
        (
            (?:
                (?:
                    <note\b
                        (?:
                            .
                            (?<!
                                <note
                            )
                        )+?
                    </note>
                )
                |
                (?:
                    <fw\b[^>]*>[^<]*?</fw>
                )
                |
                (?:
                    <pb\b[^>]*/>
                )
            )*
        )
        <p\b[^>]*\bresp="int_paragraph_joining"[^>]*>
    """,
    re.S | re.X,
)
P_JOIN_RE = re.compile(r"""(<p\b[^>]*)\bresp="int_paragraph_joining"([^>]*>)""", re.S)


def trimBody(stage, text, trimPage, info, processPage, *args, **kwargs):

    if stage == 0:
        breaks = checkPb(text)
        if breaks:
            print("\nsensitive page breaks")
            for (elem, n) in sorted(breaks.items()):
                print(f"\t{n:>3} x {elem}")

        text = DIV_CLEAN_RE.sub(r"", text)
        text = P_INTERRUPT_RE.sub(r"""\1""", text)
        text = P_JOIN_RE.sub(r"""\1\2""", text)

    prevMatch = 0
    lastNote = []
    result = []

    def doPage(page, *args, **kwargs):
        match = PAGE_NUM_RE.search(page)
        pageNum = f"-{match.group(1):>04}" if match else ""
        info["page"] = f"{info['doc']}{pageNum}"
        if stage == 0:
            page = X_RE.sub("", page)
            page = FACS_REF1_RE.sub(r'''tpl="1" vol="\1" facs="\2"''', page)
            page = FACS_REF2_RE.sub(r'''tpl="2" vol="\1" facs="\2"''', page)
        if processPage is None:
            page = trimPage(page, info, *args, **kwargs)
        else:
            processPage(page, lastNote, result, info, *args, **kwargs)

        page = LB_RE.sub(r"""<lb/>\n""", page)
        page = PB_RE.sub(r"""\n\n\g<0>\n\n""", page)
        page = NL_B_RE.sub(r"""\n<\1\2>""", page)
        page = NL_E_RE.sub(r"""\n</\1>\n""", page)
        if stage == 0:
            page = page.replace(" <hi", "\n<hi")
        page = WHITE_NL_RE.sub("\n", page.strip())
        page = SPACE_RE.sub(" ", page)
        result.append(page)

    for match in PB_RE.finditer(text):
        b = match.start()
        thisPage = text[prevMatch:b].strip()
        doPage(thisPage, *args, **kwargs)
        result.append("\n")
        prevMatch = b

    if prevMatch < len(text):
        thisPage = text[prevMatch:].strip()
        doPage(thisPage, *args, **kwargs)

    body = "".join(result)

    match = PB_RE.search(body)
    prePage = body[0 : match.start()].strip()
    if prePage:
        print(f"\nMaterial in before first page\n\t=={prePage}==")

    body = WHITE_NLNL_RE.sub("\n\n", body.strip())
    return body
