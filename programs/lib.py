import sys
import os
import collections
import re
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
CHANGE_DIR = f"{REPO_DIR}/change"
REPORT_DIR = f"{REPO_DIR}/trimreport"
XML_DIR = f"{REPO_DIR}/xml"

LAST_STAGE = 3

TF_DIR = f"{REPO_DIR}/tf"
OUT_DIR = f"{TF_DIR}/{VERSION_TF}"

CELL_RE = re.compile(r"""<cell>(.*?)</cell>""", re.S)


def parseArgs(args):
    vol = None
    lid = None

    kwargs = {}
    pargs = []

    good = True

    for arg in args:
        if arg.isdigit() or "-" in arg:
            if "-" in arg:
                (b, e) = arg.split("-", 1)
                if b.isdigit() and e.isdigit():
                    values = set(range(int(b), int(e) + 1))
                else:
                    print(f"Unrecognized argument `{arg}`")
                    good = False
                    continue
            else:
                values = {int(arg)}
            if vol is None:
                vol = values
            elif lid is None:
                lid = values
        else:
            kv = arg.split("=", 1)
            if len(kv) == 1:
                pargs.append(arg)
            else:
                (k, v) = kv
                if k == "orig":
                    v = set(v.split(","))
                kwargs[k] = v

    if vol is not None:
        vol = {f"{i:>02}" for i in vol}
    if lid is not None:
        lid = {f"p{i:>04}" for i in lid}

    return (good, vol, lid, kwargs, pargs)


# FILESYSTEM OPERATIONS


def docSummary(docs):
    nDocs = len(docs)
    rep = "  0x" if not nDocs else f"  1x {docs[0]}" if nDocs == 1 else ""
    if not rep:
        examples = " ".join(docs[0:2])
        rest = " ..." if nDocs > 2 else ""
        rep = f"{nDocs:>4}x {examples}{rest}"
    return f"{rep:<30}"


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
        if subdir == "rest":
            os.rmdir(f"{path}/{subdir}")


def initTree(path, fresh=False):
    exists = os.path.exists(path)
    if fresh:
        if exists:
            clearTree(path)

    if not exists:
        os.makedirs(path, exist_ok=True)


# SOURCE READING


META_PAGE_NUM_RE = re.compile(
    r"""<interpGrp type="page"><interp>([0-9]+)</interp></interpGrp>""", re.S
)


def getPage(path):
    with open(path) as fh:
        text = fh.read()
    match = META_PAGE_NUM_RE.search(text)
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


# TOP-LEVEL TRIM


def trim(
    stage,
    givenVol,
    givenLid,
    corpusPre,
    trimVolume,
    trimDocBefore,
    trimDocPrep,
    trimPage,
    processPage,
    trimDocPost,
    corpusPost,
    *args,
    **kwargs,
):
    if corpusPre:
        corpusPre(givenVol)

    SRC = IN_DIR if stage == 0 else f"{TRIM_DIR}{stage - 1}"
    DST = XML_DIR if stage == LAST_STAGE else f"{TRIM_DIR}{stage}"
    REP = f"{REPORT_DIR}{stage}"
    initTree(REP)

    volumes = getVolumes(SRC)

    analysis = collections.Counter()
    analysisAfter = collections.Counter()

    info = dict(
        table=0,
        tableDiag={},
        docs=[],
        pageDiag=collections.defaultdict(dict),
        metas=0,
        metasUnknown=[],
        metasDistilled=collections.defaultdict(dict),
        nameDiag=collections.defaultdict(
            lambda: collections.defaultdict(lambda: collections.defaultdict(list))
        ),
        metaValues=collections.defaultdict(
            lambda: collections.defaultdict(lambda: collections.defaultdict(list))
        ),
        metaDiag=collections.defaultdict(dict),
        captionInfo=collections.defaultdict(list),
        captionNorm=collections.defaultdict(list),
        captionVariant=collections.defaultdict(list),
        captionRoman=collections.defaultdict(list),
        folioResult=collections.defaultdict(list),
        folioTrue=collections.defaultdict(list),
        folioFalse=collections.defaultdict(list),
        folioUndecided=collections.defaultdict(lambda: collections.defaultdict(list)),
        headInfo=collections.defaultdict(list),
        remarks=collections.Counter(),
        remarkInfo=collections.defaultdict(lambda: collections.defaultdict(list)),
        noteInfo=collections.defaultdict(list),
        heads={},
        bigTitle={},
        splits=[],
        splitsX=[],
    )

    mergeText = {}
    previousDoc = None

    for vol in volumes:
        if givenVol is not None and vol not in givenVol:
            continue
        print(f"\rvolume {vol}" + " " * 70)

        volDir = vol.lstrip("0") if stage == 0 else vol
        thisSrcDir = f"{SRC}/{volDir}"
        thisDstDir = f"{DST}/{vol}"
        rest = "/rest" if stage == 1 else ""
        initTree(thisDstDir, fresh=True)
        initTree(f"{thisDstDir}{rest}", fresh=True)

        info["vol"] = vol
        idMap = {} if stage == 0 else None
        letters = getLetters(thisSrcDir, idMap=idMap)

        if trimVolume:
            trimVolume(vol, letters, info, idMap, givenLid, mergeText)

        for name in letters:
            lid = name if idMap is None else idMap[name]
            if givenLid is not None and lid not in givenLid:
                continue
            doc = f"{vol}:{lid}"

            if trimDocBefore is None:
                with open(f"{thisSrcDir}/{name}.xml") as fh:
                    text = fh.read()
            else:
                text = trimDocBefore(doc, name, thisSrcDir, mergeText)
                if text is None:
                    continue

            sys.stderr.write(f"\r\t{lid}      ")
            info["doc"] = doc
            info["docs"].append(doc)

            origText = text

            thisAnalysis = analyse(text)
            for (path, count) in thisAnalysis.items():
                analysis[path] += count
            text = trimDocument(
                stage,
                text,
                trimPage,
                info,
                processPage,
                trimDocPrep,
                trimDocPost,
                previousDoc,
                *args,
                **kwargs,
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

            previousDoc = doc

    print("\rdone" + " " * 70)

    docs = info["docs"]
    totalDocs = len(docs)
    print(f"{totalDocs} documents")

    with open(f"{REP}/elementsIn.tsv", "w") as fh:
        for (path, amount) in sorted(analysis.items()):
            fh.write(f"{path}\t{amount}\n")

    with open(f"{REP}/elementsOut.tsv", "w") as fh:
        for (path, amount) in sorted(analysisAfter.items()):
            fh.write(f"{path}\t{amount}\n")

    if corpusPost:
        corpusPost(info)


BODY_RE = re.compile(r"""<body[^>]*>(.*?)</body>""", re.S)


def trimDocument(
    stage,
    text,
    trimPage,
    info,
    processPage,
    trimDocPrep,
    trimDocPost,
    previousDoc,
    *args,
    **kwargs,
):
    headElem = "teiHeader" if stage == 0 else "header"
    headerRe = re.compile(rf"""<{headElem}[^>]*>(.*?)</{headElem}>""", re.S)
    match = headerRe.search(text)
    metaText = match.group(1)
    match = BODY_RE.search(text)
    bodyText = match.group(1)

    if trimDocPrep:
        (header, bodyText) = trimDocPrep(info, metaText, bodyText, previousMeta)
    else:
        header = f"""<header>\n{metaText}\n</header>"""

    if bodyText is None:
        return None

    body = trimBody(stage, bodyText, trimPage, info, processPage, *args, **kwargs)

    if trimDocPost:
        body = trimDocPost(info, body)

    return (
        f"""<teiTrim>\n{header}\n<body>\n{body}\n</body>\n</teiTrim>"""
        if body
        else None
    )


# TRIM HEADER


WHITE_NLNL_RE = re.compile(r"""\n{3,}""", re.S)
WHITE_NL_RE = re.compile(r"""(?:[ \t]*\n[ \t\n]*)""", re.S)
SPACE_RE = re.compile(r"""  +""", re.S)
WHITE_RE = re.compile(r"""\s\s+""", re.S)
PB_RE = re.compile(r"""<pb\b[^>]*/>""", re.S)


previousMeta = {}


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


def trimBody(stage, text, trimPage, info, processPage, *args, **kwargs):
    if stage == 0:
        breaks = checkPb(text)
        if breaks:
            print("\nsensitive page breaks")
            for (elem, n) in sorted(breaks.items()):
                print(f"\t{n:>3} x {elem}")

        text = DIV_CLEAN_RE.sub(r"", text)

    prevMatch = 0
    previous = {}
    result = []
    first = True

    def doPage(page, *args, **kwargs):
        nonlocal first

        if page is None:
            if processPage is not None:
                processPage(None, previous, result, info, *args, **kwargs)
                first = False
            return

        match = PAGE_NUM_RE.search(page)
        pageNum = f"-{match.group(1):>04}" if match else ""
        info["page"] = f"{info['doc']}{pageNum}"
        info["pageNum"] = pageNum.lstrip("-")
        info["first"] = first
        first = False
        if stage == 0:
            page = X_RE.sub("", page)
            page = FACS_REF1_RE.sub(r'''tpl="1" vol="\1" facs="\2"''', page)
            page = FACS_REF2_RE.sub(r'''tpl="2" vol="\1" facs="\2"''', page)
        if processPage is None:
            page = trimPage(page, info, *args, **kwargs)
            page = LB_RE.sub(r"""<lb/>\n""", page)
            page = PB_RE.sub(r"""\n\n\g<0>\n\n""", page)
            page = NL_B_RE.sub(r"""\n<\1\2>""", page)
            page = NL_E_RE.sub(r"""\n</\1>\n""", page)
            if stage == 0:
                page = page.replace(" <hi", "\n<hi")
            page = WHITE_NL_RE.sub("\n", page.strip())
            page = SPACE_RE.sub(" ", page)
            result.append(page)
        else:
            processPage(page, previous, result, info, *args, **kwargs)

    for match in PB_RE.finditer(text):
        b = match.start()
        thisPage = text[prevMatch:b].strip()
        if not thisPage:
            continue
        doPage(thisPage, *args, **kwargs)
        result.append("\n")
        prevMatch = b

    if prevMatch < len(text):
        thisPage = text[prevMatch:].strip()
        doPage(thisPage, *args, **kwargs)
    doPage(None, *args, kwargs)

    body = "".join(result)

    match = PB_RE.search(body)
    prePage = body[0 : match.start()].strip() if match else ""
    if prePage:
        print(f"\nMaterial before first page\n\t=={prePage}==")

    body = WHITE_NLNL_RE.sub("\n\n", body.strip())
    return body


def applyCorrections(corrections, doc, text):
    if doc in corrections:
        for (correctRe, correctRepl) in corrections[doc]:
            (text, n) = correctRe.subn(correctRepl, text)
            if n == 0:
                print(text)
                print(f"\tCORRECTION {doc} {correctRe.pattern} did not apply")
            elif n > 1:
                print(text)
                print(f"\tCORRECTION {doc} {correctRe.pattern} applied {n} times")
    return text


def rangesFromList(nodeList):  # the list must be sorted
    curstart = None
    curend = None
    for n in nodeList:
        if curstart is None:
            curstart = n
            curend = n
        elif n == curend + 1:
            curend = n
        else:
            yield (curstart, curend)
            curstart = n
            curend = n
    if curstart is not None:
        yield (curstart, curend)


def specFromRanges(ranges):  # ranges must be normalized
    return ",".join(
        "{}".format(r[0]) if r[0] == r[1] else "{}-{}".format(*r) for r in ranges
    )
