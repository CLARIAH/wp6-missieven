import sys
import os
import re
import collections

import xml.etree.ElementTree as ET

from lib import IN_DIR, TRIM1_DIR, REPO, VERSION_SRC, clearTree, getVolumes


HELP = """

Convert TEI source to simplified pseudo TEI, stage1

python3 trimTei1.py [volume] [page] [--help]

--help: print this text amd exit

volume: only process this volume; default: all volumes
page  : only process letter that starts at this page; default: all letters
"""

# SOURCE READING


PAGENUM_RE = re.compile(
    r"""<interpGrp type="page"><interp>([0-9]+)</interp></interpGrp>""", re.S
)


def getPage(text):
    match = PAGENUM_RE.search(text)
    return int(match.group(1)) if match else 0


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


# TRIMMING


def trim(givenVol, givenLid):
    # reduce the big, opaque file names to shorter file names
    # using the page number
    # check whether there are collisions
    # remove abundant namespaces and xml:ids

    if os.path.exists(TRIM1_DIR):
        clearTree(TRIM1_DIR)
    os.makedirs(TRIM1_DIR, exist_ok=True)

    volumes = getVolumes(IN_DIR)

    collisions = 0
    analysis = collections.Counter()
    analysisAfter = collections.Counter()

    for vol in volumes:
        if givenVol is not None and givenVol != vol:
            continue

        thisInDir = f"{IN_DIR}/{vol}"
        thisTrimDir = f"{TRIM1_DIR}/{vol}"
        os.makedirs(thisTrimDir, exist_ok=True)

        idMap = {}

        print(f"\rvolume {vol:>2}" + " " * 70)
        with os.scandir(thisInDir) as vdh:
            for entry in vdh:
                if entry.is_file():
                    name = entry.name
                    if name.endswith(".xml"):
                        text = trimNameSpaces(f"{thisInDir}/{name}")
                        lid = getPage(text)
                        if givenLid is not None and givenLid != lid:
                            continue
                        sys.stderr.write(f"\r\tp{lid:>04} = {name}      ")
                        thisAnalysis = analyse(text)
                        for (path, count) in thisAnalysis.items():
                            analysis[path] += count
                        text = trimDocument(text)
                        with open(f"{thisTrimDir}/p{lid:>04}.xml", "w") as fh:
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
        print(f"MAPPING from letter ids to first pages: {collisions} collisions")
        return False
    else:
        print("No collisions while mapping letter ids to first pages")

    with open(f"{TRIM1_DIR}/elementsIn.tsv", "w") as fh:
        for (path, amount) in sorted(analysis.items()):
            fh.write(f"{path}\t{amount}\n")

    with open(f"{TRIM1_DIR}/elementsOut.tsv", "w") as fh:
        for (path, amount) in sorted(analysisAfter.items()):
            fh.write(f"{path}\t{amount}\n")
    return True


X_RE = re.compile(r"""\s*xml:?[a-z]+=['"][^'"]*['"]""", re.S)


def trimNameSpaces(path):
    with open(path) as fh:
        text = fh.read()
    return X_RE.sub("", text)


BODY_RE = re.compile(r"""<body[^>]*>(.*?)</body>""", re.S)
HEADER_RE = re.compile(r"""<teiHeader[^>]*>(.*?)</teiHeader>""", re.S)


def trimDocument(text):
    match = HEADER_RE.search(text)
    meta = trimHeader(match)
    match = BODY_RE.search(text)
    body = trimBody(match)

    return f"""<teiTrim>\n{meta}\n<body>\n{body}\n</body>\n</teiTrim>"""


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
WHITE_NL_RE = re.compile(r"""(?:[ \t]*\n[ \t\n]*)""", re.S)


def trimHeader(match):
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


DIV_CLEAN_RE = re.compile(r"""<\/?div\b[^>]*>""", re.S)
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
        <p[ ]resp="int_paragraph_joining"[^>]*>
    """,
    re.S | re.X,
)
PB_RE = re.compile(r"""<pb\b[^>]*/>""", re.S)
P_JOIN_RE = re.compile(r"""(<p) resp="int_paragraph_joining"([^>]*>)""", re.S)
WHITE_NLNL_RE = re.compile(r"""\n{3,}""", re.S)


def trimBody(match):
    text = match.group(1)

    text = DIV_CLEAN_RE.sub(r"", text)

    breaks = checkPb(text)
    if breaks:
        print("\nsensitive page breaks")
        for (elem, n) in sorted(breaks.items()):
            print(f"\t{n:>3} x {elem}")

    text = P_INTERRUPT_RE.sub(r"""\1""", text)
    text = P_JOIN_RE.sub(r"""\1\2""", text)
    prevMatch = 0

    result = []
    for match in PB_RE.finditer(text):
        b = match.start()
        thisPage = text[prevMatch:b].strip()
        result.append(trimPage(thisPage))
        result.append("\n")
        prevMatch = b

    if prevMatch < len(text):
        thisPage = text[prevMatch:].strip()
        result.append(trimPage(thisPage))

    body = "".join(result)

    match = PB_RE.search(body)
    prePage = body[0 : match.start()].strip()
    if prePage:
        print(f"\nMaterial in before first page\n\t=={prePage}==")

    body = WHITE_NLNL_RE.sub("\n\n", body.strip())
    return body


WHITE_RE = re.compile(r"""\s\s+""", re.S)


def stripRendAtt(match):
    material = match.group(1).replace(";", " ")
    if material == "" or material == " ":
        return ""
    material = WHITE_RE.sub(" ", material)
    material = material.strip()
    return f''' rend="{material}"'''


CLEAR_FW_RE = re.compile(r"""<fw\b[^>]*>(.*?)</fw>""", re.S)


def checkFw(match):
    text = match.group(1)
    if len(text) > 100:
        return f"<p>{text}</p>"
    else:
        return ""


ALIGN_RE = re.compile(r"""text-align:\s*justify[^;"']*;?""", re.S)
ALIGN_H_RE = re.compile(r"""text-align:\s*([^;"']+)[^;'"]*;?""", re.S)
ALIGN_V_RE = re.compile(r"""vertical-align:\s*([^;"']+)[^;'"]*;?""", re.S)
DECORATION_RE = re.compile(r"""text-decoration:\s*([^;"']+)[^;'"]*;?""", re.S)
DEG_RE = re.compile(r"""(°)(</hi>)""", re.S)
F_RE = re.compile(r"""<hi\b[^>]*>f</hi>""", re.S)
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
FAMILY_RE = re.compile(r"""font-family:[^;"']*;?""", re.S)

FONT_STYLE_RE = re.compile(
    r"""font-(?:style|weight|variant):\s*([^;"' ]+)[^;"']*;?""", re.S
)
HALF_RE = re.compile(r"""1\s*/?\s*<hi rend="sub">\s*2([^<]*)</hi>""", re.S)
HEIGHT_RE = re.compile(r"""line-height:[^;"']*;?""", re.S)
HI_CLEAN_RE = re.compile(r"""<hi\b[^>]*>([^a-zA-Z0-9]*?)</hi>""", re.S)
HI_EMPH_RE = re.compile(
    r"""(<hi\b[^>]*?rend=['"])[^'"]*?(?:bold|italic)[^'"]*(['"])[^>]*>""", re.S
)
HI_SUBSUPER_RE = re.compile(
    r"""(<hi\b[^>]*?rend=['"])[^'"]*?(super|sub|small-caps)[^'"]*(['"])[^>]*>""", re.S
)
HI_UND_RE = re.compile(
    r"""<hi\b[^>]*?rend=['"][^'"]*?underline[^'"]*['"][^>]*>(.*?)</hi>""", re.S
)
INDENT_RE = re.compile(r"""text-indent:\s*[^-][^;"']*;?""", re.S)
MARGIN_RE = re.compile(r"""margin-(?:[^:'"]*):[^;"']*;?""", re.S)
OUTDENT_RE = re.compile(r"""text-indent:\s*-[^;"']*;?""", re.S)
SIZE_RE = re.compile(r"""font-size:\s*(?:9\.5|10\.5|10)\s*[^;"']*;?""", re.S)
SIZE_BIG_RE = re.compile(r"""font-size:\s*(?:20|(?:1[1-9]))\.?5?[^;"']*;?""", re.S)
SIZE_SMALL_RE = re.compile(r"""font-size:\s*(?:9|(?:[6-8]))\.?5?[^;"']*;?""", re.S)
SIZE_XSMALL_RE = re.compile(r"""font-size:\s*(?:[1-5])\.?5?[^;"']*;?""", re.S)
SPACE_RE = re.compile(r"""  +""", re.S)
SPACING_RE = re.compile(r"""letter-spacing:[^;"']*;?""", re.S)
STRIP_RE = re.compile(r""" rend=['"]([^'"]*)['"]""", re.S)
P_LB_RE = re.compile(r"""<lb/>\s*(</p>)""", re.S)


def trimPage(text):
    text = CLEAR_FW_RE.sub(checkFw, text)

    for trimRe in (
        FAMILY_RE,
        SPACING_RE,
        HEIGHT_RE,
        MARGIN_RE,
        ALIGN_RE,
        SIZE_RE,
    ):
        text = trimRe.sub("", text)

    text = DEG_RE.sub(r"\2\1", text)

    for (trimRe, val) in ((F_RE, "ƒ"),):
        text = trimRe.sub(val, text)

    text = HI_SUBSUPER_RE.sub(r"\1\2\3>", text)
    text = HI_EMPH_RE.sub(r"\1emphasis\2>", text)
    text = HI_UND_RE.sub(r"<und>\1</und>", text)

    for (trimRe, val) in (
        (SIZE_BIG_RE, "large"),
        (SIZE_SMALL_RE, "small"),
        (SIZE_XSMALL_RE, "xsmall"),
        (OUTDENT_RE, "outdent"),
        (INDENT_RE, "indent"),
    ):
        text = trimRe.sub(val, text)

    for trimRe in (FONT_STYLE_RE, ALIGN_V_RE, ALIGN_H_RE, DECORATION_RE):
        text = trimRe.sub(r"\1", text)

    text = STRIP_RE.sub(stripRendAtt, text)
    text = text.replace(''' rend=""''', "")
    text = text.replace(''' rend=" "''', "")

    text = HI_CLEAN_RE.sub(r"""\1""", text)
    text = text.replace("<hi/>", "")

    text = FACS_REF1_RE.sub(r'''tpl="1" vol="\1" facs="\2"''', text)
    text = FACS_REF2_RE.sub(r'''tpl="2" vol="\1" facs="\2"''', text)

    text = HALF_RE.sub(r"½\1", text)

    text = text.replace("<lb/>", "<lb/>\n")
    text = PB_RE.sub(r"""\n\n\g<0>\n\n""", text)
    text = P_LB_RE.sub(r"""\1""", text)
    text = text.replace("<p>", "\n<p>")
    text = text.replace("</p>", "</p>\n")

    text = WHITE_NL_RE.sub("\n", text.strip())
    text = SPACE_RE.sub(" ", text)

    return text


# MAIN


def main():
    args = () if len(sys.argv) == 1 else tuple(sys.argv[1:])

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

    print(f"TEI trimmer for {REPO}")
    print(f"TEI source version = {VERSION_SRC}")

    return trim(vol, lid)


sys.exit(0 if main() else 1)
