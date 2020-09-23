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

TF_DIR = f"{REPO_DIR}/tf"
OUT_DIR = f"{TF_DIR}/{VERSION_TF}"


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
    return int(match.group(1)) if match else 0


def getVolumes(srcDir):
    volumes = []
    with os.scandir(srcDir) as dh:
        for entry in dh:
            if entry.is_dir():
                vol = entry.name
                if not vol.isdigit():
                    continue
                volumes.append(int(vol))
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
                    if idMap is not None:
                        lid = getPage(f"{srcDir}/{name}")
                        if lid in lidSet:
                            collisions += 1
                        lidSet.add(lid)
                        idMap[name] = lid
                    letters.append(name)
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


def trim(stage, givenVol, givenLid, trimPage, processPage, *args, **kwargs):
    if stage == 0:
        SRC = IN_DIR
    else:
        SRC = f"{TRIM_DIR}{stage - 1}"
    DST = f"{TRIM_DIR}{stage}"

    if os.path.exists(DST):
        clearTree(DST)
    os.makedirs(DST, exist_ok=True)

    volumes = getVolumes(SRC)

    analysis = collections.Counter()
    analysisAfter = collections.Counter()

    info = dict(
        table=0,
        captionInfo=collections.defaultdict(list),
        captionNorm=collections.defaultdict(list),
        captionVariant=collections.defaultdict(list),
    )

    for vol in volumes:
        if givenVol is not None and givenVol != vol:
            continue
        print(f"\rvolume {vol:>2}" + " " * 70)

        thisSrcDir = f"{SRC}/{vol}"
        thisDstDir = f"{DST}/{vol}"
        os.makedirs(thisDstDir, exist_ok=True)

        idMap = {} if stage == 0 else None
        letters = getLetters(thisSrcDir, idMap)

        for name in letters:
            lid = idMap[name] if idMap is not None else int(name[1:5].lstrip("0"))
            if givenLid is not None and givenLid != lid:
                continue
            sys.stderr.write(f"\r\tp{lid:>04}      ")
            info["doc"] = f"{vol:>02}:p{lid:>04}"
            with open(f"{thisSrcDir}/{name}") as fh:
                text = fh.read()

            thisAnalysis = analyse(text)
            for (path, count) in thisAnalysis.items():
                analysis[path] += count
            text = trimDocument(
                stage, text, trimPage, info, processPage, *args, **kwargs
            )

            dstName = f"p{lid:>04}.xml"
            with open(f"{thisDstDir}/{dstName}", "w") as fh:
                fh.write(text)

            thisAnalysisAfter = analyse(text, after=True)
            for (path, count) in thisAnalysisAfter.items():
                analysisAfter[path] += count

    print("\rdone" + " " * 70)

    with open(f"{DST}/elementsIn.tsv", "w") as fh:
        for (path, amount) in sorted(analysis.items()):
            fh.write(f"{path}\t{amount}\n")

    with open(f"{DST}/elementsOut.tsv", "w") as fh:
        for (path, amount) in sorted(analysisAfter.items()):
            fh.write(f"{path}\t{amount}\n")

    captionInfo = info["captionInfo"]
    captionNorm = info["captionNorm"]
    captionVariant = info["captionVariant"]
    if captionNorm or captionVariant or captionInfo:
        print("NAMES:")
        print(f"\t{len(captionNorm):>3} verified names")
        print(f"\t{len(captionVariant):>3} unresolved variants")
        fh = open(f"{TRIM_DIR}{stage}/fwh-yes.tsv", "w")
        for (captionSrc, tag) in ((captionNorm, "OK"), (captionVariant, "XX"), (captionInfo, "II")):
            for caption in sorted(captionSrc):
                docs = captionSrc[caption]
                firstDoc = docs[0]
                nDocs = len(docs)
                fh.write(f"{firstDoc} {nDocs:>3}x {tag} {caption}\n")
    return True


def trimDocument(stage, text, trimPage, info, processPage, *args, **kwargs):
    headElem = "teiHeader" if stage == 0 else "header"
    headerRe = re.compile(rf"""<{headElem}[^>]*>(.*?)</{headElem}>""", re.S)
    match = headerRe.search(text)
    header = (
        trimHeader(match, *args, **kwargs)
        if stage == 0
        else f"""<header>\n{match.group(1)}\n</header>"""
    )

    bodyRe = re.compile(r"""<body[^>]*>(.*?)</body>""", re.S)
    match = bodyRe.search(text)
    body = trimBody(stage, match.group(1), trimPage, info, processPage, *args, **kwargs)

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
