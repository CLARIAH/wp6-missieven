import sys
import os
import re
import collections
from shutil import rmtree

import yaml

import xml.etree.ElementTree as ET

from tf.fabric import Fabric
from tf.convert.walker import CV

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
    "sectionFeatures": "title,number,number",
    "sectionTypes": "letter,section,p",
}

intFeatures = set(
    """
        number
        vol
    """.strip().split()
)

featureMeta = {
    "title": {"description": "short title of letter, from fileDesc element"},
    "location": {"description": "location from letter was sent, from fileDesc element"},
    "vol": {"description": "volume number"},
    "data": {"description": "date when letter was sent, from fileDesc element"},
    "lid": {"description": "ID of letter, from fileDesc element"},
    "number": {"description": "number of a letter, page, paragraph"},
    "trans": {"description": "transcription of a word"},
    "punc": {
        "description": "whitespace and/or punctuation following a word"
        "up to the next word"
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


def convert(generateTf):
    if generateTf:
        if os.path.exists(OUT_DIR):
            rmtree(OUT_DIR)
        os.makedirs(OUT_DIR, exist_ok=True)

    cv = getConverter()

    return cv.walk(
        director,
        slotType,
        otext=otext,
        generic=generic,
        intFeatures=intFeatures,
        featureMeta=featureMeta,
        generateTf=generateTf,
    )


# DIRECTOR


LINE_LENGTH = 100


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


def getLetters(srcDir):
    letters = []

    with os.scandir(srcDir) as dh:
        for entry in dh:
            if entry.is_file():
                name = entry.name
                if name.endswith(".txt"):
                    lid = name[0:-4]
                    letters.append(lid)
    return tuple(sorted(letters))


PAGENUM_RE = re.compile(
    r"""<interpGrp type="page"><interp>([0-9]+)</interp></interpGrp>""", re.S
)
NUM_RE = re.compile(r"""[0-9]""", re.S)


def getPage(text):
    match = PAGENUM_RE.search(text)
    return int(match.group(1)) if match else 0


X_RE = re.compile(r"""\s*xml:?[a-z]+=['"][^'"]*['"]""", re.S)


def trimDoc(path):
    with open(path) as fh:
        text = fh.read()
    return X_RE.sub("", text)


DEG_RE = re.compile(r"""(°)(</hi>)""", re.S)

NOTE_RE = re.compile(r"""(<note\b[^>]*?) rend=['"][^'"]*['"]""", re.S)
F_RE = re.compile(r"""<hi\b[^>]*>f</hi>""", re.S)
HI_SUBSUPER_RE = re.compile(
    r"""(<hi\b[^>]*?rend=['"])[^'"]*?(super|sub|small-caps)[^'"]*(['"])[^>]*>""", re.S
)
HI_EMPH_RE = re.compile(
    r"""(<hi\b[^>]*?rend=['"])[^'"]*?(?:bold|italic)[^'"]*(['"])[^>]*>""", re.S
)
EMPH_RE = re.compile(r"""<hi rend="(?:emphasis|underline)">(.*?)</hi>""", re.S)
CHECK_RE = re.compile(r"""<hi rend="(?:small-caps|sub|large)">(.*?)</hi>""", re.S)
MARK_RE = re.compile(r"""<hi rend="super[^"]*">(.*?)</hi>""", re.S)
SMALL_RE = re.compile(r"""<hi rend="small[^"]*">([^A-Za-z0-9]*?)</hi>""", re.S)
FOLIO_RE = re.compile(r"""<hi rend="small[^"]*">(.*?)</hi>""", re.S)

FAMILY_RE = re.compile(r"""font-family:[^;"']*;?""", re.S)
SPACING_RE = re.compile(r"""letter-spacing:[^;"']*;?""", re.S)
HEIGHT_RE = re.compile(r"""line-height:[^;"']*;?""", re.S)
MARGIN_RE = re.compile(r"""margin-(?:[^:'"]*):[^;"']*;?""", re.S)
ALIGN_RE = re.compile(r"""text-align:\s*justify[^;"']*;?""", re.S)

SIZE_RE = re.compile(r"""font-size:\s*(?:9\.5|10\.5|10)\s*[^;"']*;?""", re.S)
SIZE_BIG_RE = re.compile(r"""font-size:\s*(?:20|(?:1[1-9]))\.?5?[^;"']*;?""", re.S)
SIZE_SMALL_RE = re.compile(r"""font-size:\s*(?:9|(?:[1-8]))\.?5?[^;"']*;?""", re.S)
OUTDENT_RE = re.compile(r"""text-indent:\s*-[^;"']*;?""", re.S)
INDENT_RE = re.compile(r"""text-indent:\s*[^-][^;"']*;?""", re.S)

FONT_STYLE_RE = re.compile(
    r"""font-(?:style|weight|variant):\s*([^;"' ]+)[^;"']*;?""", re.S
)
VALIGN_RE = re.compile(r"""vertical-align:\s*([^;"']+)[^;'"]*;?""", re.S)
HALIGN_RE = re.compile(r"""text-align:\s*([^;"']+)[^;'"]*;?""", re.S)
DECORATION_RE = re.compile(r"""text-decoration:\s*([^;"']+)[^;'"]*;?""", re.S)

STRIP_RE = re.compile(r""" rend=['"]([^'"]*)['"]""", re.S)
WHITE_RE = re.compile(r"""\s\s+""", re.S)

HALF_RE = re.compile(r"""1\s*/?\s*<hi rend="sub">\s*2([^<]*)</hi>""", re.S)


def stripRend(match):
    material = match.group(1).replace(";", " ")
    if material == "" or material == " ":
        return ""
    material = WHITE_RE.sub(" ", material)
    material = material.strip()
    return f''' rend="{material}"'''


def trimLayout(text):
    text = DEG_RE.sub(r"\2\1", text)

    for trimRe in (NOTE_RE,):
        text = trimRe.sub(r"\1", text)

    for (trimRe, val) in ((F_RE, "ƒ"),):
        text = trimRe.sub(val, text)

    text = HI_SUBSUPER_RE.sub(r"\1\2\3>", text)
    text = HI_EMPH_RE.sub(r"\1emphasis\2>", text)

    for trimRe in (FAMILY_RE, SPACING_RE, HEIGHT_RE, MARGIN_RE, ALIGN_RE, SIZE_RE):
        text = trimRe.sub("", text)

    for (trimRe, val) in (
        (SIZE_BIG_RE, "large"),
        (SIZE_SMALL_RE, "small"),
        (OUTDENT_RE, "outdent"),
        (INDENT_RE, "indent"),
    ):
        text = trimRe.sub(val, text)

    for trimRe in (FONT_STYLE_RE, VALIGN_RE, HALIGN_RE, DECORATION_RE):
        text = trimRe.sub(r"\1", text)

    text = STRIP_RE.sub(stripRend, text)
    text = text.replace(''' rend=""''', "")
    text = text.replace(''' rend=" "''', "")

    text = EMPH_RE.sub(r"<emph>\1</emph>", text)
    text = CHECK_RE.sub(r"<special>\1</special>", text)
    text = MARK_RE.sub(r"<mark>\1</mark>", text)
    text = SMALL_RE.sub(r"\1", text)
    text = FOLIO_RE.sub(r"<folio>\1</folio>", text)

    text = HALF_RE.sub(r"½\1", text)
    text = text.replace('<TEI', '<teitrim')
    text = text.replace('</TEI', '</teitrim')
    return text


def analyseLayout(v, analysis):
    for css in v.split(";"):
        trait = css.strip().split(":", 1)
        (prop, val) = (trait[0], "") if len(trait) == 1 else trait

        analysis[f"layout.{prop.strip()}={val.strip()}"] += 1


def nodeInfo(node, analysis, after=False):
    tag = node.tag
    atts = node.attrib

    if not atts:
        analysis[f"{tag}.."] += 1
    else:
        for (k, v) in atts.items():
            vTrim = NUM_RE.sub("n", v)
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


def trim(givenVol):
    # reduce the big, opaque file names to shorter file names
    # using the page number
    # check whether there are collisions
    # remove abundant namespaces and xml:ids

    if os.path.exists(TRIM_DIR):
        rmtree(TRIM_DIR)
    os.makedirs(TRIM_DIR, exist_ok=True)

    volumes = getVolumes(IN_DIR)

    collisions = 0
    analysis = collections.Counter()
    analysisAfter = collections.Counter()

    for vol in volumes:
        if givenVol is not None and givenVol != vol:
            continue

        thisInDir = f"{IN_DIR}/{vol}"
        thisTrimDir = f"{TRIM_DIR}/{vol}"
        os.makedirs(thisTrimDir)

        idMap = {}

        print(f"\rvolume {vol:>2}" + " " * 70)
        with os.scandir(thisInDir) as vdh:
            for entry in vdh:
                if entry.is_file():
                    name = entry.name
                    if name.endswith(".xml"):
                        text = trimDoc(f"{thisInDir}/{name}")
                        lid = getPage(text)
                        sys.stderr.write(f"\r\tp{lid:>04} = {name}      ")
                        thisAnalysis = analyse(text)
                        for (path, count) in thisAnalysis.items():
                            analysis[path] += count
                        text = trimLayout(text)
                        with open(f"{TRIM_DIR}/{vol}/p{lid:>04}.xml", "w") as fh:
                            fh.write(text)
                        if lid in idMap:
                            collisions += 1
                        else:
                            idMap[lid] = name
                        thisAnalysisAfter = analyse(text, after=True)
                        for (path, count) in thisAnalysisAfter.items():
                            analysisAfter[path] += count

    print("\rdone" + " " * 70)
    if collisions:
        print(f"MAPPING to short letter ids: {collisions} collisions")
        return False
    else:
        print("No collisions while constructing short letter ids")

    with open(f"{TRIM_DIR}/analysis.tsv", "w") as fh:
        for (path, amount) in sorted(analysis.items()):
            fh.write(f"{path}\t{amount}\n")

    with open(f"{TRIM_DIR}/layout.tsv", "w") as fh:
        for (path, amount) in sorted(analysisAfter.items()):
            fh.write(f"{path}\t{amount}\n")
    return True


def director(cv):

    warnings = collections.defaultdict(lambda: collections.defaultdict(set))
    errors = collections.defaultdict(lambda: collections.defaultdict(set))

    # delete meta data of unused features
    for feat in featureMeta:
        if not cv.occurs(feat):
            print(f"WARNING: feature {feat} does not occur")
            cv.meta(feat)

    if warnings:
        showDiags(warnings, "WARNING")
    if errors:
        showDiags(errors, "ERROR")


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

    doTrim = "trim" in args
    doWalk = "walk" in args
    doLoad = "load" in args

    vol = None

    for arg in args:
        if arg.isdigit():
            vol = arg

    if vol is not None:
        vol = int(vol)

    print(f"TEI to TF converter for {REPO}")
    print(f"TEI source version = {VERSION_SRC}")
    print(f"TF  target version = {VERSION_TF}")

    if doTrim:
        result = trim(vol)
        if not result:
            return False

    if doWalk:
        if not convert(doLoad):
            return False

    if doLoad:
        loadTf()

    return True


sys.exit(0 if main() else 1)
