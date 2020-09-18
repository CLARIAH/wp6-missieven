import sys
import os
import re
import collections

import xml.etree.ElementTree as ET

from lib import (
    TRIM1_DIR,
    TRIM2_DIR,
    REPO,
    VERSION_SRC,
    clearTree,
    getVolumes,
    getLetters,
)


HELP = """

Convert trim stage1 to simplified trim stage2

python3 trimTei2.py [volume] [page] [--help]

--help: print this text amd exit

volume: only process this volume; default: all volumes
page  : only process letter that starts at this page; default: all letters
"""

# SOURCE READING


PAGENUM_RE = re.compile(
    r"""<interpGrp type="page"><interp>([0-9]+)</interp></interpGrp>""", re.S
)


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

    if os.path.exists(TRIM2_DIR):
        clearTree(TRIM2_DIR)
    os.makedirs(TRIM2_DIR, exist_ok=True)

    volumes = getVolumes(TRIM1_DIR)

    analysis = collections.Counter()
    analysisAfter = collections.Counter()

    for vol in volumes:
        if givenVol is not None and givenVol != vol:
            continue
        print(f"\rvolume {vol:>2}" + " " * 70)

        thisInDir = f"{TRIM1_DIR}/{vol}"
        letters = getLetters(thisInDir)
        thisTrimDir = f"{TRIM2_DIR}/{vol}"
        os.makedirs(thisTrimDir, exist_ok=True)

        for name in letters:
            lid = int(name[1:5].lstrip("0"))
            if givenLid is not None and givenLid != lid:
                continue
            sys.stderr.write(f"\r\t{name[0:5]}      ")
            with open(f"{thisInDir}/{name}") as fh:
                text = fh.read()

            thisAnalysis = analyse(text)
            for (path, count) in thisAnalysis.items():
                analysis[path] += count
            text = trimDocument(text)

            with open(f"{thisTrimDir}/{name}", "w") as fh:
                fh.write(text)

            thisAnalysisAfter = analyse(text, after=True)
            for (path, count) in thisAnalysisAfter.items():
                analysisAfter[path] += count

    print("\rdone" + " " * 70)

    with open(f"{TRIM2_DIR}/elementsIn.tsv", "w") as fh:
        for (path, amount) in sorted(analysis.items()):
            fh.write(f"{path}\t{amount}\n")

    with open(f"{TRIM2_DIR}/elementsOut.tsv", "w") as fh:
        for (path, amount) in sorted(analysisAfter.items()):
            fh.write(f"{path}\t{amount}\n")
    return True


BODY_RE = re.compile(r"""<body[^>]*>(.*?)</body>""", re.S)
HEADER_RE = re.compile(r"""<header>(.*?)</header>""", re.S)


def trimDocument(text):
    match = HEADER_RE.search(text)
    header = match.group(1)
    match = BODY_RE.search(text)
    body = trimBody(match)

    return f"""<teiTrim>\n{header}\n<body>\n{body}\n</body>\n</teiTrim>"""


PAGE_RE = re.compile(r"""(<pb\b[^>]*/>.*?)(?=<pb\b|$)""", re.S)
WHITE_NLNL_RE = re.compile(r"""\n{3,}""", re.S)


def trimBody(match):
    counts = dict(table=0)

    text = match.group(1)

    lastNote = []

    result = []
    for page in PAGE_RE.findall(text):
        processPage(page, lastNote, result, counts)

    if len(lastNote):
        result.append(lastNote[0])
        result.append("\n")

    body = "".join(result)

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
                # print(f"\nCOMBINE {lastNote[0]}\n+++\n{firstNote}")
                lastNote[0] = lastNote[0].replace(
                    "</fnote>", f"{firstNote[7:-8]}</fnote>"
                )
                notes.pop(0)
            result.append(lastNote[0])
            result.append("\n")
            lastNote.clear()
        if notes:
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


HI_CLEAN_RE = re.compile(r"""<hi\b[^>]*>([^a-zA-Z0-9]*?)</hi>""", re.S)


def mergeFolio(match):
    text = match.group(0)
    text = HI_CLEAN_RE.sub(r"""\1""", text)
    return f"<folio>{text}</folio>"


NOTE_RENAME_P_RE = re.compile(r"""<fnote\b[^>]*>(.*?)</fnote>""", re.S)


def filterNotes(match):
    notes = match.group(1)
    word = match.group(2)
    if word:
        notes = NOTE_RENAME_P_RE.sub(r"""<p>\1</p>""", notes)
    return f"""{notes}{word}"""


MARK_DWN_RE = re.compile(r"""<fref ref="([^"]*)"/>""", re.S)
FOLIO_DWN_RE = re.compile(r"""<folio>\s*(.*?)\s*</folio>""", re.S)
WHITE_RE = re.compile(r"""\s\s+""", re.S)


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


MARK_NUM_RE = re.compile(r"""\s*([xi*0-9]{1,2})\s*\)?\s*(.*)""", re.S)


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


MARK_PLAIN_RE = re.compile(r"""\b([xi*0-9]{1,2})\s*\)\s*""", re.S)


def parseMarkPlain(match):
    num = match.group(1)
    return f"""<fref ref="{parseNum(num)}"/> """


def parseNum(text):
    if text == "i":
        return "1"
    return text


CHECK_RE = re.compile(r"""<hi rend="(?:small-caps|sub|large)">(.*?)</hi>""", re.S)
COMMENT_RE = re.compile(r"""<(fnote|remark)\b([^>]*)>(.*?)</\1>""", re.S)
DELETE_REND_RE = re.compile(r"""(<(?:note|head|p)\b[^>]*?) rend=['"][^'"]*['"]""", re.S)
EMPH_RE = re.compile(r"""<hi rend="emphasis">(.*?)</hi>""", re.S)
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
NOTES_FILTER_RE = re.compile(r"""((?:<fnote[^>]*>.*?</fnote>\s*)+)(\S*)""", re.S)
NOTES_ALL_RE = re.compile(r"""^(.*?)((?:<fnote.*?</fnote>\s*)+)(.*?)$""", re.S)
NOTE_RE = re.compile(r"""<fnote.*?</fnote>""", re.S)
OUTDENT_RE = re.compile(r"""text-indent:\s*-[^;"']*;?""", re.S)
P_RE = re.compile(r"""(<\/?)p\b""", re.S)
REF_RE = re.compile(r"""<hi>(.*?)</hi>""", re.S)
REMARK_NOTE_RE = re.compile(r"""<note\b[^>]*?\bresp="editor"[^>]*>(.*?)</note>""", re.S)
SIZE_RE = re.compile(r"""font-size:\s*(?:9\.5|10\.5|10)\s*[^;"']*;?""", re.S)
SIZE_BIG_RE = re.compile(r"""font-size:\s*(?:20|(?:1[1-9]))\.?5?[^;"']*;?""", re.S)
SIZE_SMALL_RE = re.compile(r"""font-size:\s*(?:9|(?:[6-8]))\.?5?[^;"']*;?""", re.S)
SIZE_XSMALL_RE = re.compile(r"""font-size:\s*(?:[1-5])\.?5?[^;"']*;?""", re.S)
SMALL_RE = re.compile(r"""<hi rend="small[^"]*">(.*?)</hi>""", re.S)
SMALLX_RE = re.compile(r"""<hi rend="xsmall[^"]*">(.*?)</hi>""", re.S)
SPACE_RE = re.compile(r"""  +""", re.S)
SPACING_RE = re.compile(r"""letter-spacing:[^;"']*;?""", re.S)
STRIP_RE = re.compile(r""" rend=['"]([^'"]*)['"]""", re.S)
SUPER_RE = re.compile(r"""<hi rend="super[^"]*">(.*?)</hi>(\s*\)?\s*)""", re.S)
TABLE_RE = re.compile(r"""<table>(.*?)</table>""", re.S)
WHITE_NL_RE = re.compile(r"""(?:[ \t]*\n[ \t\n]*)""", re.S)


def trimPage(text, counts):
    for trimRe in (DELETE_REND_RE,):
        text = trimRe.sub(r"\1", text)

    text = EMPH_RE.sub(r"<emph>\1</emph>", text)
    text = CHECK_RE.sub(r"<special>\1</special>", text)
    text = SUPER_RE.sub(parseSuper, text)
    text = SMALL_RE.sub(r"\1", text)
    text = SMALLX_RE.sub(r"<special>\1</special>", text)
    text = FOLIO_RE.sub(mergeFolio, text)
    text = FOLIO_C_RE.sub(r"""<folio>\1\2</folio>""", text)

    text = REMARK_NOTE_RE.sub(r"""\n<remark>\1</remark>\n""", text)
    text = formatNotes(text)
    text = TABLE_RE.sub(formatTablePre(counts), text)
    text = NOTES_FILTER_RE.sub(filterNotes, text)

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

    if post:
        print("\nMaterial after footnotes:")
        print(f"\t==={post}")

    return (body, NOTE_RE.findall(notes))


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


def formatTablePre(counts):
    return lambda match: formatTable(match, counts)


CELL_RE = re.compile(r"""<cell>(.*?)</cell>""", re.S)
CELL_NOTES_RE = re.compile(r"""<fnote[^>]*>(.*?)</fnote>""", re.S)
DEL_TBL_ELEM = re.compile(r"""</?(?:lb|p)/?>""", re.S)
ROW_RE = re.compile(r"""<row>(.*?)</row>""", re.S)
WHITE_B_RE = re.compile(r"""(>)\s+""", re.S)
WHITE_E_RE = re.compile(r"""\s+(<)""", re.S)


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
