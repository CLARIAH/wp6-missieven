import sys
import os
import re
import collections

import xml.etree.ElementTree as ET

from lib import IN_DIR, TRIM_DIR, REPO, VERSION_SRC, clearTree, getVolumes


HELP = """

Convert TEI source to simplified pseudo TEI

python3 trimTei.py [volume] [page] [--help]

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

    if os.path.exists(TRIM_DIR):
        clearTree(TRIM_DIR)
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


CLEAR_DATE_RE = re.compile(r"""<date>.*?</date>""", re.S)
CLEAR_TITLE_RE = re.compile(r"""<title>.*?</title>""", re.S)
DELETE_ELEM_RE = re.compile(
    r"""</?(?:TEI|text|bibl|"""
    r"""fileDesc|listBibl|notesStmt|publicationStmt|sourceDesc|titleStmt)\b[^>]*>"""
)
DELETE_EMPTY_RE = re.compile(r"""<note[^>]*/>""", re.S)
DELETE_P_RE = re.compile(r"""</?p>""", re.S)
IDNO_RE = re.compile(r"""<idno (.*?)</idno>""", re.S)
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
WHITE_NLNL_RE = re.compile(r"""\n{3,}""", re.S)


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


P_LB_RE = re.compile(r"""<lb/>\s*(</p>)""", re.S)
P_INTERRUPT_RE = re.compile(
    r"""
        </p>
        (
            (?:
                (?:
                    <note
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
                    <pb[ ][^>]*/>
                )
            )*
        )
        <p[ ]resp="int_paragraph_joining"[^>]*>
    """,
    re.S | re.X,
)
P_JOIN_RE = re.compile(r"""(<p) resp="int_paragraph_joining"([^>]*>)""", re.S)
PB_RE = re.compile(r"""<pb\b[^>]*/>""", re.S)


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
DIV_CLEAN_RE = re.compile(r"""<\/?div\b[^>]*>""", re.S)


def checkPb(text):
    breaks = collections.Counter()

    for match in CHECK_PB_RE.finditer(text):
        elem = match.group(1)
        material = match.group(2)
        if "<pb" in material:
            breaks[elem] += 1
    return breaks


def trimBody(match):
    counts = dict(table=0)

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
    lastNote = []

    result = []
    for match in PB_RE.finditer(text):
        b = match.start()
        thisPage = text[prevMatch:b].strip()
        processPage(thisPage, lastNote, result, counts)
        prevMatch = b

    if prevMatch < len(text):
        thisPage = text[prevMatch:].strip()
        processPage(thisPage, lastNote, result, counts)
    if len(lastNote):
        result.append(lastNote[0])
        result.append("\n")

    body = "".join(result)

    match = PB_RE.search(body)
    prePage = body[0 : match.start()].strip()
    if prePage:
        print(f"\nMaterial in before first page\n\t=={prePage}==")

    body = WHITE_NLNL_RE.sub("\n\n", body.strip())
    return body


def processPage(page, lastNote, result, counts):
    if not page:
        if len(lastNote):
            result.append(lastNote[0])
            lastNote.clear()
        result.append("\n\n")
        return

    (text, notes) = trimPage(page, counts)

    if notes:
        if len(lastNote):
            firstNote = notes[0]
            if firstNote.startswith("<fnote>"):
                print(f"\nCOMBINE {lastNote[0]}\n+++\n{firstNote}")
                lastNote[0] = lastNote[0].replace(
                    "</fnote>", f"{firstNote[7:-8]}</fnote>"
                )
                notes.pop(0)
            result.append(lastNote[0])
            result.append("\n")
            lastNote.clear()
        lastNote.append(notes[-1])
        result.append("\n")
    else:
        if len(lastNote):
            result.append(lastNote[0])
            result.append("\n")
            lastNote.clear()
        result.append("\n")

    result.append(text)
    result.append("\n")
    if notes:
        result.append("\n".join(note for note in notes[0:-1]))
    result.append("\n")


ALIGN_RE = re.compile(r"""text-align:\s*justify[^;"']*;?""", re.S)
ALIGN_H_RE = re.compile(r"""text-align:\s*([^;"']+)[^;'"]*;?""", re.S)
ALIGN_V_RE = re.compile(r"""vertical-align:\s*([^;"']+)[^;'"]*;?""", re.S)
CHECK_RE = re.compile(r"""<hi rend="(?:small-caps|sub|large)">(.*?)</hi>""", re.S)
CLEAR_FW_RE = re.compile(r"""<fw\b[^>]*>(.*?)</fw>""", re.S)


def checkFw(match):
    text = match.group(1)
    if len(text) > 80:
        return f"<p>{text}</p>"
    else:
        return ""


COMMENT_RE = re.compile(r"""<(fnote|remark)\b([^>]*)>(.*?)</\1>""", re.S)
DECORATION_RE = re.compile(r"""text-decoration:\s*([^;"']+)[^;'"]*;?""", re.S)
DEG_RE = re.compile(r"""(°)(</hi>)""", re.S)
DELETE_REND_RE = re.compile(r"""(<(?:note|head|p)\b[^>]*?) rend=['"][^'"]*['"]""", re.S)
EMPH_RE = re.compile(r"""<hi rend="emphasis">(.*?)</hi>""", re.S)
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

FOLIO_RE = re.compile(
    r"""
        (?:<hi\b[^>]*>)?
            [Ff]ol\.?(?:io)?(?:.s)?\s*
        (?:</hi>)?
        (
            (?:<hi\b[^>]*>)?
                \s*[0-9RrVv][0-9RrVv. -]*
            (?:</hi>)?
            \s*
        )+
    """,
    re.S | re.X,
)


FOLIO_C_RE = re.compile(
    r"""
        ([0-9][0-9, ]*)
        <folio>(.*?)</folio>
    """,
    re.S | re.X,
)


def mergeFolio(match):
    text = match.group(0)
    text = HI_CLEAN_RE.sub(r"""\1""", text)
    return f"<folio>{text}</folio>"


FOLIO_DWN_RE = re.compile(r"""<folio>\s*(.*?)\s*</folio>""", re.S)
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
MARK_DWN_RE = re.compile(r"""<fref ref="([^"]*)"/>""", re.S)
NOTE_RENAME_P_RE = re.compile(r"""<fnote\b[^>]*>(.*?)</fnote>""", re.S)
NOTES_FILTER_RE = re.compile(r"""((?:<fnote[^>]*>.*?</fnote>\s*)+)(\S*)""", re.S)
NOTES_ALL_RE = re.compile(r"""^(.*?)((?:<fnote.*?</fnote>\s*)+)(.*?)$""", re.S)
NOTE_RE = re.compile(r"""<fnote.*?</fnote>""", re.S)


def filterNotes(match):
    notes = match.group(1)
    word = match.group(2)
    if word:
        notes = NOTE_RENAME_P_RE.sub(r"""<p>\1</p>""", notes)
    return f"""{notes}{word}"""


OUTDENT_RE = re.compile(r"""text-indent:\s*-[^;"']*;?""", re.S)
P_RE = re.compile(r"""(<\/?)p\b""", re.S)
REF_RE = re.compile(r"""<hi>(.*?)</hi>""", re.S)
REMARK_NOTE_RE = re.compile(r"""<note\b[^>]*?\bresp="editor"[^>]*>(.*?)</note>""", re.S)


def cleanOther(match):
    tag = match.group(1)
    atts = match.group(2)
    text = match.group(3)
    text = text.replace("<lb/>", " ")
    text = text.replace("<emph>", "*")
    text = text.replace("</emph>", "*")
    text = text.replace("<und>", "_")
    text = text.replace("</und>", "_")
    text = text.replace("<super>", "^")
    text = text.replace("</super>", "^")
    text = text.replace("<special>", "`")
    text = text.replace("</special>", "`")
    text = MARK_DWN_RE.sub(r"[=\1]", text)
    text = FOLIO_DWN_RE.sub(r" {\1} ", text)
    text = text.replace("\n", " ")
    text = text.strip()

    text = WHITE_RE.sub(" ", text)
    if "<" in text:
        print(f"\nunclean {tag}")
        print(f"\t==={text}===")
    return f"<{tag}{atts}>{text}</{tag}>"


SIZE_RE = re.compile(r"""font-size:\s*(?:9\.5|10\.5|10)\s*[^;"']*;?""", re.S)
SIZE_BIG_RE = re.compile(r"""font-size:\s*(?:20|(?:1[1-9]))\.?5?[^;"']*;?""", re.S)
SIZE_SMALL_RE = re.compile(r"""font-size:\s*(?:9|(?:[6-8]))\.?5?[^;"']*;?""", re.S)
SIZE_XSMALL_RE = re.compile(r"""font-size:\s*(?:[1-5])\.?5?[^;"']*;?""", re.S)
SMALL_RE = re.compile(r"""<hi rend="small[^"]*">(.*?)</hi>""", re.S)
SMALLX_RE = re.compile(r"""<hi rend="xsmall[^"]*">(.*?)</hi>""", re.S)
SPACING_RE = re.compile(r"""letter-spacing:[^;"']*;?""", re.S)
STRIP_RE = re.compile(r""" rend=['"]([^'"]*)['"]""", re.S)


def stripRendAtt(match):
    material = match.group(1).replace(";", " ")
    if material == "" or material == " ":
        return ""
    material = WHITE_RE.sub(" ", material)
    material = material.strip()
    return f''' rend="{material}"'''


SUPER_RE = re.compile(r"""<hi rend="super[^"]*">(.*?)</hi>(\s*\)?\s*)""", re.S)
MARK_NUM_RE = re.compile(r"""\s*([xi*0-9]{1,2})\s*\)?\s*(.*)""", re.S)
MARK_PLAIN_RE = re.compile(r"""\b([xi*0-9]{1,2})\s*\)\s*""", re.S)


def parseSuper(match):
    material = match.group(1)
    after = match.group(2)
    return (
        MARK_NUM_RE.sub(parseMark, material)
        if MARK_NUM_RE.search(material)
        else f"""<super>{material}</super>{after}"""
    )


def parseMark(match):
    num = match.group(1)
    after = match.group(2)
    return f"""<fref ref="{parseNum(num)}"/>{after} """


def parseMarkPlain(match):
    num = match.group(1)
    return f"""<fref ref="{parseNum(num)}"/> """


def parseNum(text):
    if text == "i":
        return "1"
    return text


def trimPage(text, counts):
    for trimRe in (
        FAMILY_RE,
        SPACING_RE,
        HEIGHT_RE,
        MARGIN_RE,
        ALIGN_RE,
        SIZE_RE,
        CLEAR_FW_RE,
    ):
        text = trimRe.sub("", text)

    text = CLEAR_FW_RE.sub(checkFw, text)
    text = DEG_RE.sub(r"\2\1", text)

    for trimRe in (DELETE_REND_RE,):
        text = trimRe.sub(r"\1", text)

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
    text = EMPH_RE.sub(r"<emph>\1</emph>", text)
    text = CHECK_RE.sub(r"<special>\1</special>", text)
    text = SUPER_RE.sub(parseSuper, text)
    text = SMALL_RE.sub(r"\1", text)
    text = SMALLX_RE.sub(r"<special>\1</special>", text)
    text = FOLIO_RE.sub(mergeFolio, text)
    text = FOLIO_C_RE.sub(r"""<folio>\1\2</folio>""", text)

    text = FACS_REF1_RE.sub(r'''tpl="1" vol="\1" facs="\2"''', text)
    text = FACS_REF2_RE.sub(r'''tpl="2" vol="\1" facs="\2"''', text)

    text = HALF_RE.sub(r"½\1", text)

    text = REMARK_NOTE_RE.sub(r"""\n<remark>\1</remark>\n""", text)
    text = formatNotes(text)
    text = TABLE_RE.sub(formatTablePre(counts), text)
    text = NOTES_FILTER_RE.sub(filterNotes, text)

    text = text.replace("<lb/>", "<lb/>\n")
    text = PB_RE.sub(r"""\n\n\g<0>\n\n""", text)
    text = P_LB_RE.sub(r"""\1""", text)
    text = text.replace("<p>", "\n<p>")
    text = text.replace("</p>", "</p>\n")

    text = REF_RE.sub(r"""[\1]""", text)
    text = COMMENT_RE.sub(cleanOther, text)
    text = P_RE.sub(r"""\1para""", text)

    text = WHITE_NL_RE.sub("\n", text.strip())
    text = SPACE_RE.sub(" ", text)

    match = NOTES_ALL_RE.match(text)
    if not match:
        return (text, [])

    body = match.group(1)
    notes = match.group(2)
    post = match.group(3)
    print(f"NOTES==={notes}===\nPOST==={post}===")

    if post:
        print("\nMaterial after foornotes:")
        print(f"\t==={post}")

    return (body, NOTE_RE.findall(notes))


MARKED_NOTE_DBL_RE = re.compile(r"""(<lb/></note>)(<note>)""", re.S)
MARKED_NOTE_RE = re.compile(r"""<note>\s*([0-9]{1,2}|[a-z])\s*\)\s*""", re.S)
MARKED_UN_NOTE_RE = re.compile(
    r"""(<(?:(?:lb/)|(?:/note))>)\s*([0-9]{1,2}|[a-z])\s*\)\s*(.*?)(?=<lb/>)""", re.S
)
NOTE_RENAME_RE = re.compile(r"""<note\b([^>]*)>(.*?)</note>""", re.S)
SPURIOUS_P_RE = re.compile(r"""(<lb/>)\s*</p><p>\s*([0-9]{1,2}|[a-z])\s*\)\s*""", re.S)
SWITCH_NOTE_RE = re.compile(r"""(</note>)\s*(<lb/>)""", re.S)


def formatNotes(text):
    text = SPURIOUS_P_RE.sub(r"""\1\2) """, text)
    text = MARKED_NOTE_DBL_RE.sub(r"""\1\n\2""", text)
    text = MARKED_UN_NOTE_RE.sub(r"""\1<note>\2) \3</note>""", text)
    text = SWITCH_NOTE_RE.sub(r"""\2\1""", text)
    text = MARKED_NOTE_RE.sub(r"""<note ref="\1">""", text)
    text = NOTE_RENAME_RE.sub(r"""<fnote\1>\2</fnote>""", text)
    text = NOTE_COLLAPSE_RE.sub(collapseNotes, text)
    text = MARK_PLAIN_RE.sub(parseMarkPlain, text)
    return text


NOTE_COLLAPSE_RE = re.compile(
    r"""(<fnote ref=[^>]*>)(.*?)(</fnote>)((?:\s*<fnote>.*?</fnote>)+)""", re.S
)


def collapseNotes(match):
    firstNoteStart = match.group(1)
    firstNoteText = match.group(2)
    firstNoteEnd = match.group(3)
    restNotes = match.group(4)
    restNotes = restNotes.replace("<fnote>", " ")
    restNotes = restNotes.replace("</fnote>", " ")
    return f"""{firstNoteStart}{firstNoteText} {restNotes}{firstNoteEnd}"""


def formatTablePre(counts):
    return lambda match: formatTable(match, counts)


CELL_RE = re.compile(r"""<cell>(.*?)</cell>""", re.S)
CELL_NOTES_RE = re.compile(r"""<fnote[^>]*>(.*?)</fnote>""", re.S)
DEL_TBL_ELEM = re.compile(r"""</?(?:lb|p)/?>""", re.S)
ROW_RE = re.compile(r"""<row>(.*?)</row>""", re.S)
TABLE_RE = re.compile(r"""<table>(.*?)</table>""", re.S)
WHITE_B_RE = re.compile(r"""(>)\s+""", re.S)
WHITE_E_RE = re.compile(r"""\s+(<)""", re.S)
WHITE_RE = re.compile(r"""\s\s+""", re.S)
SPACE_RE = re.compile(r"""  +""", re.S)


def formatTable(match, counts):
    counts["table"] += 1
    n = counts["table"]

    table = match.group(1)
    table = DEL_TBL_ELEM.sub(r" ", table)
    for trimRe in (WHITE_B_RE, WHITE_E_RE):
        table = trimRe.sub(r"""\1""", table)
    table = WHITE_RE.sub(r" ", table)

    result = []
    result.append(f"""\n<table n="{n}">""")
    rows = ROW_RE.findall(table)

    for (r, row) in enumerate(rows):
        result.append(f"""<row n="{n}" row="{r + 1}">""")
        cells = CELL_RE.findall(row)

        for (c, cell) in enumerate(cells):
            cell = CELL_NOTES_RE.sub(r"""\1""", cell)
            result.append(
                f"""<cell n="{n}" row="{r + 1}" col="{c + 1}">{cell}</cell>"""
            )
        result.append("</row>")

    result.append("</table>\n")

    return "\n".join(result)


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
