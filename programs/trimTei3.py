import re

from lib import WHITE_RE


"""
Notes.

"""

CORRECTIONS_DEF = {
    "01:p0004-0004": (
        (
            r"""\^4J\^ \.(</remark>)""",
            r"""^4^)\1""",
        ),
    ),
    "05:p0099-0100": (
        (
            r"""\s*(</remark>)\s*<para>\s*<emph>(is)</emph>\s* (-) ;<lb/>\s*</para>""",
            r""" \2\3)\1""",
        ),
    ),
    "05:p0099-0135": (
        (
            r"""(Padang te vestigen\.)(</remark>)""",
            r"""\1)\2""",
        ),
    ),
    "05:p0099-0149": (
        (
            r"""(Pits vernam te Bantam,)(</remark>)"""
            r"""\s*<para>\s*(dat\s*-\s*\))<lb/>\s*</para>""",
            r"""\1\3\2""",
        ),
    ),
}
CORRECTIONS = {
    page: tuple((re.compile(spec[0], re.S), spec[1]) for spec in specs)
    for (page, specs) in CORRECTIONS_DEF.items()
}

REMARK_SPURIOUS_RE = re.compile(r"""<remark>(y[y ]*)</remark>""", re.S)
REMARK_END_CORR_RE = re.compile(r"""\)\.\s*\*\s*(</remark>)""", re.S)

MARK_NUM_RE = re.compile(r"""\s*([xi*0-9]{1,2})\s*\)?\s*(.*)""", re.S)
COMMENT_RE = re.compile(r"""<(fnote|remark)\b([^>]*)>(.*?)</\1>""", re.S)
REMARK_START_RE = re.compile(r"""^[({]\s*""", re.S)
REMARK_END_RE = re.compile(
    r"""
        (?:
            (?:
                [)}]-*
            )
            |
            (?:
                -
                [\ -]*
                (?:
                    \*j\*
                    |
                    [;-]
                )
            )
        )
        \s*
        \.?
        $
    """,
    re.S | re.X,
)
REMARK_RE = re.compile(r"""<remark>(.*?)</remark>""", re.S)
REMARK_MULTIPLE_RE = re.compile(
    r"""
        (?:
            <remark>
                [^<]*
            </remark>
            \s*
        ){2,}
    """,
    re.S | re.X,
)

REMARK_FIRST_REMOVE_RE = re.compile(r"""<remark\b[^>]*>.*?</remark>""", re.S)

REMARK_LAST_REMOVE_RE = re.compile(
    r"""
        <remark\b[^>]*>
            (
                (?:
                    .
                    (?!<remark)
                )*
            )
        </remark>
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

REMARK_PRE_POST_RE = re.compile(
    r"""
        ^
        (.*?)
        <remark>
        .*
        </remark>
        (.*)
        $
    """,
    re.S | re.X,
)

REMARK_PRE_RE = re.compile(
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
        \s*
        (.*)
        $
    """,
    re.S | re.X,
)

REMARK_POST_RE = re.compile(
    r"""
        ^
        \s*
        (.*?)
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


def processPage(text, previous, result, info, *args, **kwargs):
    remarkInfo = info["remarkInfo"]
    page = info["page"]
    prevRemark = previous.get("remark", None)
    prevNotes = previous.get("notes", None)
    prevPage = previous.get("page", None)

    if not text:
        if prevRemark is not None:
            result.append(prevRemark[0])
            previous["remark"] = None
        if prevNotes is not None:
            result.append("\n".join(prevNotes))
            previous["notes"] = None
        result.append("\n\n")
        return

    (text, current) = trimPage(text, info, previous, *args, **kwargs)

    onlyRemark = current["onlyRemark"]
    firstRemark = current["firstRemark"]
    lastRemark = current["lastRemark"]
    startRemark = onlyRemark if onlyRemark else firstRemark if firstRemark else None

    if startRemark:
        (curContent, curSummary) = startRemark

    if prevRemark is None:
        if startRemark:
            remarkInfo["<"][curSummary].append(page)
    else:
        (prevContent, prevSummary) = prevRemark
        if startRemark:
            (thisSummary, thisTrimmed) = summarize(prevSummary + curSummary)
            prevRemark = (prevContent + curContent, thisSummary)
        else:
            remarkInfo[">"][prevSummary].append(prevPage)

        result.append(prevRemark[0])
        result.append("\n")

    firstNote = current["firstNote"]
    if prevNotes is not None:
        if firstNote is not None:
            prevNotes[-1] = prevNotes[-1].replace("</fnote>", firstNote[7:])
        result.append("\n".join(prevNotes))

    previous["remark"] = onlyRemark if onlyRemark else lastRemark
    previous["notes"] = current["notes"]
    previous["page"] = page

    result.append(text)
    result.append("\n")


def remarkMultiplePre(info):
    return lambda match: remarkMultiple(match, info)


def remarkMultiple(match, info):
    remarkInfo = info["remarkInfo"]
    page = info["page"]
    text = match.group(0)
    result = []

    for remarks in REMARK_MULTIPLE_RE.findall(text):
        mRemarks = []
        prevClosed = False

        for match in REMARK_RE.finditer(remarks):
            content = match.group(1)
            content = cleanText(content, "remark")
            (summary, trimmed) = summarize(content)
            thisOpen = trimmed.startswith("(")
            thisClosed = trimmed.endswith(")")

            if prevClosed or thisOpen:
                if mRemarks:
                    mText = (
                        "<remark>\n"
                        + (" ".join(r[0] for r in mRemarks))
                        + "</remark>\n"
                    )
                    result.append(mText)
                    if len(mRemarks) > 1:
                        summary = "\n\t".join(r[1] for r in mRemarks)
                        remarkInfo["m"][f"{len(mRemarks)}\t{summary}"].append(page)
                    mRemarks = []
            mRemarks.append((content, summary))
            prevClosed = thisClosed

        if mRemarks:
            mText = "<remark>\n" + (" ".join(r[0] for r in mRemarks)) + "</remark>\n"
            result.append(mText)
            if len(mRemarks) > 1:
                summary = "\n\t".join(r[1] for r in mRemarks)
                remarkInfo["m"][f"{len(mRemarks)}\t{summary}"].append(page)

    return "".join(result)


def trimPage(text, info, previous, *args, **kwargs):
    remarkInfo = info["remarkInfo"]
    page = info["page"]

    text = REMARK_SPURIOUS_RE.sub(r"<special>\1</special>", text)
    text = COMMENT_RE.sub(cleanTag, text)
    text = REMARK_END_CORR_RE.sub(r"*).\1", text)

    if page in CORRECTIONS:
        for (correctRe, correctRepl) in CORRECTIONS[page]:
            (text, n) = correctRe.subn(correctRepl, text)
            if n == 0:
                print(text)
                print(f"\tCORRECTION {page} {correctRe.pattern} did not apply")
            elif n > 1:
                print(text)
                print(f"\tCORRECTION {page} {correctRe.pattern} applied {n} times")

    text = REMARK_MULTIPLE_RE.sub(remarkMultiplePre(info), text)

    current = {}

    onlyRemark = None
    firstRemark = None
    lastRemark = None
    prevRemark = previous.get("remark", None)

    ppMatch = REMARK_PRE_POST_RE.search(text)
    if ppMatch:
        (beforeFirst, afterLast) = ppMatch.groups([1, 2])
        pre = REMARK_PRE_RE.match(beforeFirst).group(1).strip()
        post = REMARK_POST_RE.match(afterLast).group(1).strip()

        matches = tuple(REMARK_RE.finditer(text))
        for (i, match) in enumerate(matches):
            content = match.group(1)
            content = cleanText(content, "remark")
            (summary, trimmed) = summarize(content)
            startBracket = trimmed.startswith("(")
            endBracket = trimmed.endswith(")")
            isFirst = i == 0 and not pre and not startBracket
            isLast = i == len(matches) - 1 and not post and not endBracket
            if isFirst and isLast:
                onlyRemark = (content, summary)
            elif isFirst:
                firstRemark = (content, summary)
            elif isLast:
                lastRemark = (content, summary)
            label = (
                "1"
                if isFirst and isLast
                else "F"
                if isFirst
                else "L"
                if isLast
                else "v"
                if startBracket and endBracket
                else "("
                if startBracket
                else ")"
                if endBracket
                else "x"
            )
            remarkInfo[label][summary].append(page)
    else:
        remarkInfo["0"][""].append(page)

    current["onlyRemark"] = onlyRemark
    current["firstRemark"] = firstRemark
    current["lastRemark"] = lastRemark

    for (condition, removeRe, msg) in (
        (onlyRemark and prevRemark, REMARK_RE, "only remark"),
        (firstRemark and prevRemark, REMARK_FIRST_REMOVE_RE, "first remark"),
        (lastRemark, REMARK_LAST_REMOVE_RE, "last remark"),
    ):
        if condition:
            (text, n) = removeRe.subn("", text, count=1)
            if not n:
                print(f"\n{page} removal of {msg} failed")

    # text = formatNotes(text)
    # text = NOTES_FILTER_RE.sub(filterNotes, text)
    text = COMMENT_RE.sub(cleanTag, text)

    notes = None
    firstNote = None
    # match = NOTES_ALL_RE.match(text)
    match = None
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

# CELL_NOTES_RE = re.compile(r"""<fnote[^>]*>(.*?)</fnote>""", re.S)
# cell = CELL_NOTES_RE.sub(r"""\1""", cell)


NOTE_COLLAPSE_RE = re.compile(
    r"""(<fnote ref=[^>]*>)(.*?)(</fnote>)((?:\s*<fnote>.*?</fnote>)+)""", re.S
)


FOLIO_DWN_RE = re.compile(r"""<folio>\s*(.*?)\s*</folio>""", re.S)
MARK_DWN_RE = re.compile(r"""<fref ref="([^"]*)"/>""", re.S)


def cleanTag(match):
    tag = match.group(1)
    atts = match.group(2)
    text = match.group(3)
    text = cleanText(text, tag)
    return f"<{tag}{atts}>{text}</{tag}>"


def cleanText(text, tag):
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
    if tag == "remark":
        text = REMARK_START_RE.sub(r"(", text)
        text = REMARK_END_RE.sub(r")", text)

    if "<" in text:
        print(f"\nunclean {tag}")
        print(f"\t==={text}===")
    return text


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


def summarize(text, limit=20):
    lText = len(text)
    if lText <= limit:
        start = text
        inter = ""
        end = ""
    elif lText <= 2 * limit:
        start = text[0:limit]
        inter = ""
        end = text[limit:]
    else:
        start = text[0:limit]
        inter = " ... "
        end = text[-limit:]

    summary = f"{start:<{limit}}{inter:<5}{end:>{limit}}"
    trimmed = f"{start}{inter}{end}"

    return (summary, trimmed)
