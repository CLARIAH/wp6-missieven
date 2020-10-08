import re

from lib import WHITE_RE


"""
Notes and Tables.

"""


MARK_NUM_RE = re.compile(r"""\s*([xi*0-9]{1,2})\s*\)?\s*(.*)""", re.S)
COMMENT_RE = re.compile(r"""<(fnote|remark)\b([^>]*)>(.*?)</\1>""", re.S)
REMARK_FIRST_REMOVE_RE = re.compile(r"""<remark\b[^>]*>.*?</remark>""", re.S)

REMARK_FIRST_RE = re.compile(
    r"""
    <pb\b[^>]*>\s*
    (?:
        (?:
            (?:
                <head\b[^>]*>.*?</head>
            )
            |
            (?:
                <folio\b[^>]*>.*?</folio>
            )
        )
        \s*
    )*
    (.*?)
    (<remark\b[^>]*>(.*?)</remark>)
    """,
    re.S | re.X,
)

testRe = re.compile(
    r"""
        a
        (?=
            b
        )
    """,
    re.S | re.X,
)

REMARK_LAST_REMOVE_RE = re.compile(
    r"""
        <remark\b[^>]*>.*?</remark>
        (?=
            \s*
            (?:
                (?:
                    (?:
                        <note\b[^>]*>.*?</note>
                    )
                    |
                    (?:
                        <folio\b[^>]*>.*?</folio>
                    )
                )
                \s*
            )*
            $
        )
    """,
    re.S | re.X,
)

REMARK_LAST_RE = re.compile(
    r"""
        .*
        (<remark\b[^>]*>(.*?)</remark>)
        (.*)
        (?:
            (?:
                (?:
                    <note\b[^>]*>.*?</note>
                )
                |
                (?:
                    <folio\b[^>]*>.*?</folio>
                )
            )
            \s*
        )*
        $
    """,
    re.S | re.X,
)


def processPage(page, previous, result, info, *args, **kwargs):
    prevRemark = previous.get("remark", None)
    prevNotes = previous.get("notes", None)

    if not page:
        if prevRemark is not None:
            result.append(prevRemark)
            previous["remark"] = None
        if prevNotes is not None:
            result.append("\n".join(prevNotes))
            previous["notes"] = None
        result.append("\n\n")
        return

    (text, current) = trimPage(page, info, previous, *args, **kwargs)

    firstRemark = current["firstRemark"]
    if prevRemark is not None:
        if firstRemark is not None:
            prevRemark += firstRemark
        result.append(prevRemark)

    firstNote = current["firstNote"]
    if prevNotes is not None:
        if firstNote is not None:
            prevNotes[-1] = prevNotes[-1].replace("</fnote>", firstNote[7:])
        result.append("\n".join(prevNotes))

    previous["remark"] = current["lastRemark"]
    previous["notes"] = current["notes"]

    result.append(text)
    result.append("\n")


def trimPage(text, info, previous, *args, **kwargs):
    current = {}

    prevRemark = previous.get("remark", None)
    firstRemark = None
    if prevRemark:
        match = REMARK_FIRST_RE.search(text)
        if match:
            (pre, firstRemark, content) = match.groups([1, 2, 3])
            if pre.strip() or not content.startswith("("):
                firstRemark = None
            else:
                text = REMARK_FIRST_REMOVE_RE.sub("", text, count=1)
    current["firstRemark"] = firstRemark

    match = REMARK_LAST_RE.search(text)
    lastRemark = None
    if match:
        (lastRemark, content, post) = match.groups([1, 2, 3])
        if post.strip() or not content.rstrip().rstrip(".").rstrip().endswith(")"):
            lastRemark = None
        else:
            text = REMARK_LAST_REMOVE_RE.sub("", text, count=1)
    current["lastRemark"] = lastRemark

    text = formatNotes(text)
    text = NOTES_FILTER_RE.sub(filterNotes, text)
    text = COMMENT_RE.sub(cleanOther, text)

    notes = None
    firstNote = None
    match = NOTES_ALL_RE.match(text)
    if match:
        text = match.group(1)
        notesStr = match.group(2)
        notes = NOTE_RE.findall(notesStr)
        firstNote = notes[0]
        post = match.group(3)

        if post:
            print("\nMaterial after footnotes:")
            print(f"\t==={post}")

    current["notes"] = notes
    current["firstNote"] = firstNote
    analyseRemarks(text, info)
    return (text, current)


NOTE_RENAME_P_RE = re.compile(r"""<fnote\b[^>]*>(.*?)</fnote>""", re.S)


def parseNum(text):
    if text == "i":
        return "1"
    return text


def parseMark(match):
    num = match.group(1)
    after = match.group(2)
    return f"""<fref ref="{parseNum(num)}"/>{after} """


def parseSuper(match):
    material = match.group(1)
    after = match.group(2)
    return (
        MARK_NUM_RE.sub(parseMark, material)
        if MARK_NUM_RE.search(material)
        else f"""<super>{material}</super>{after}"""
    )


def filterNotes(match):
    notes = match.group(1)
    word = match.group(2)
    if word:
        notes = NOTE_RENAME_P_RE.sub(r"""<para>\1</para>""", notes)
    return f"""{notes}{word}"""


NOTES_FILTER_RE = re.compile(r"""((?:<fnote[^>]*>.*?</fnote>\s*)+)(\S*)""", re.S)
NOTES_ALL_RE = re.compile(r"""^(.*?)((?:<fnote.*?</fnote>\s*)+)(.*?)$""", re.S)
NOTE_RE = re.compile(r"""<fnote.*?</fnote>""", re.S)
OUTDENT_RE = re.compile(r"""text-indent:\s*-[^;"']*;?""", re.S)

# CELL_NOTES_RE = re.compile(r"""<fnote[^>]*>(.*?)</fnote>""", re.S)
# cell = CELL_NOTES_RE.sub(r"""\1""", cell)


NOTE_COLLAPSE_RE = re.compile(
    r"""(<fnote ref=[^>]*>)(.*?)(</fnote>)((?:\s*<fnote>.*?</fnote>)+)""", re.S
)


FOLIO_DWN_RE = re.compile(r"""<folio>\s*(.*?)\s*</folio>""", re.S)
MARK_DWN_RE = re.compile(r"""<fref ref="([^"]*)"/>""", re.S)
REMARK_RE = re.compile(r"""<remark>(.*?)</remark>""", re.S)


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


def parseMarkPlain(match):
    num = match.group(1)
    return f"""<fref ref="{parseNum(num)}"/> """


def collapseNotes(match):
    firstNoteStart = match.group(1)
    firstNoteText = match.group(2)
    firstNoteEnd = match.group(3)
    restNotes = match.group(4)
    restNotes = restNotes.replace("<fnote>", " ")
    restNotes = restNotes.replace("</fnote>", " ")
    return f"""{firstNoteStart}{firstNoteText} {restNotes}{firstNoteEnd}"""


MARK_PLAIN_RE = re.compile(r"""\b([xi*0-9]{1,2})\s*\)\s*""", re.S)
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


def analyseRemarks(text, info):
    doc = info["doc"]
    remarkInfo = info["remarkInfo"]
    limit = 20

    for match in REMARK_RE.finditer(text):
        remark = match.group(1)
        remark = FOLIO_DWN_RE.sub(r" {\1} ", remark)
        remark = (
            remark.replace("<lb/>", " ")
            .replace("<super>", "^")
            .replace("</super>", "^")
            .replace(")</emph>", "</emph>)")
            .replace("\n", " ")
            .replace("( ", "(")
            .replace(" )", ")")
            .replace(" .", ".")
        )
        remark = " ".join(remark.strip().split())
        lRemark = len(remark)
        if lRemark <= limit:
            start = remark
            inter = ""
            end = ""
        elif lRemark <= 2 * limit:
            start = remark[0:limit]
            inter = ""
            end = remark[limit:]
        else:
            start = remark[0:limit]
            inter = " ... "
            end = remark[-limit:]

        summary = f"{start:<20}{inter:<5}{end:>20}"
        trimmed = f"{start}{inter}{end}"
        label = "ok" if trimmed.startswith("(") and trimmed.endswith(").") else "xx"
        remarkInfo[label][summary].append(doc)
