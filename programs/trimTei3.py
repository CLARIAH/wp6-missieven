import re
import collections

from distill import MONTH_DETECT_PAT
from lib import REPORT_DIR, WHITE_RE, applyCorrections, docSummary

corpusPre = None
trimVolume = None
trimDocBefore = None
trimDocPrep = None
trimDocPost = None

STAGE = 3
REP = f"{REPORT_DIR}{STAGE}"

"""
Main function of this stage: move pieces of remarks and footnotes
across page boundaries to the page where their main fragment is.

"""

CORRECTIONS_DEF = {
    "01:p0004-0004": (
        (
            r"""<super>4J</super> \.<lb/>\s*(</remark>)""",
            r"""<super>4)</super>\1""",
        ),
    ),
    "01:p0204-0224": (
        (
            r"""(<super>3\)</super>)""",
            r"""\1 <super>4)</super>""",
        ),
    ),
    "01:p0279-0279": ((r"""(baey )(\*)\)""", r"\1⌊\2⌋"),),
    "01:p0663-0683": ((r"""(Hensen)(1\))""", r"\1"),),
    "05:p0099-0100": (
        (
            r"""\s*(</remark>)\s*<para>\s*<emph>(is)</emph>\s* (-) ;<lb/>\s*</para>""",
            r""" \2\3)\1""",
        ),
    ),
    "05:p0099-0135": (
        (
            r"""(Padang te vestigen\.<lb/>\s*)(</remark>)""",
            r"""\1)\2""",
        ),
    ),
    "05:p0099-0149": (
        (
            r"""(Pits vernam te Bantam,<lb/>\s*)(</remark>)"""
            r"""\s*<para>\s*(dat\s*-\s*\))<lb/>\s*</para>""",
            r"""\1\3\2""",
        ),
    ),
    "07:p0610-0639": ((r"""(<remark>)6 ml\.""", r"\1(vnl."),),
    "08:p0003-0004": ((r"""\b(1706)(6\))""", r"\1⌊\2⌋"),),
    "08:p0003-0005": ((r"""\b(70)(8\))""", r"\1⌊\2⌋"),),
    "09:p0365-0387": ((r"""(ƒ 7823)""", r"(\1"),),
    "10:p0175-0228": (
        (
            r"""(<remark>)<special>([^<]*)</special> \( """,
            r"<subhead>\2</subhead>\n\1( ",
        ),
    ),
    "10:p0496-0518": (
        (
            r"""(<remark>)<special>([^<]*)</special> \( """,
            r"<subhead>\2</subhead>\n\1( ",
        ),
    ),
    "10:p0633-0700": (
        (
            r"""(<remark>)<special>\((Bandar[^<]*)</special> """,
            r"<subhead>\2</subhead>\n\1( ",
        ),
    ),
    "10:p0807-0814": (
        (
            r"""(<remark>)<special>(Menado[^<]*)</special> """,
            r"<subhead>\2</subhead>\n\1( ",
        ),
    ),
    "10:p0807-0820": (
        (
            r"""(<remark>)<special>(Bima)</special>""",
            r"<subhead>\2</subhead>\n\1",
        ),
    ),
    "11:p0207-0209": ((r"""(traffique )\\(<lb/>)""", r"\1)\2"),),
    "11:p0226-0270": ((r"""<super>1</super>( overstromingen)""", r"'\1"),),
    "11:p0363-0409": (
        (
            r"""(<remark>)<special>(Hooghly)</special>""",
            r"<subhead>\2</subhead>\n\1",
        ),
    ),
    "11:p0641-0670": (
        (
            r"""(<remark>)(Kasimbazar)\n<emph>([^<]*)</emph>""",
            r"<subhead>\2</subhead>\n\1\3",
        ),
    ),
}
CORRECTIONS = {
    page: tuple((re.compile(spec[0], re.S), spec[1]) for spec in specs)
    for (page, specs) in CORRECTIONS_DEF.items()
}
OVERRIDE_START = {
    "02:p0770-0813": "«3\\ ton)",
    "07:p0534-0535": "«Kamer Zeeland)",
}

OVERRIDE_FIRST = {
    "01:p0247-0247": {"Inleiding afgedrukt  ... ertrek van schepen »"},
    "05:p0388-0400": {"- maar het werkt stu ... n; de Sultan heeft »"},
    "09:p0112-0116": {"De Huis te Assenburg ... e Machilipatnam af »"},
    "09:p0294-0324": {"uitrustingsgoederen                debiteuren"},
    "09:p0548-0562": {"Op 8 juli zijn nog 2 ... an de Compagnie. Wat"},
}
OVERRIDE_LAST = {
    "09:p0112-0115": {"«Het schip Linschote ... ober zou vertrekken."},
    "09:p0131-0174": {"«Ondanks deze overwe ... omst zorg te draaien"},
    "09:p0702-0731": {"«Personalia. De Midd ... oor de retourlading."},
    "11:p0217-0219": {"«Hoewel het bestuur  ... 1 745 verwacht werd."},
    "11:p0481-0494": {"Men werkt aan het we ... eper geen gebrek is."},
    "13:p0001-0001": {"«Dat uit Palembang v ... ld naartoe gezonden."},
    "13:p0217-0228": {"Naar Bengalen is rui ... rland zijn gezonden."},
    "13:p0340-0340": {"De Mossel is naar Be ... chepen zullen komen."},
    "13:p0483-0494": {"«Gouverneur Roelof B ... anten teruggezonden."},
    "13:p0501-0559": {"«Voor huishoudelijke ... en 21 augustus 1760."},
    "13:p0501-0590": {"«Het bestuur is van  ... oopman werd benoemd."},
    "13:p0620-0620": {"«Van resident Ajax F ... mbang is vertrokken."},
}
OVERRIDE_NOTE_START = {
    "08:p0003-0004": 4,
}
OVERRIDE_NOTE_TEXT = {}
OVERRIDE_NOTE_BODY = {
    "01:p0204-0224": {4: "3"},
}
REMARK_SPURIOUS_RE = re.compile(r"""<remark>(y[y ]*)</remark>""", re.S)
REMARK_END_CORR_RE = re.compile(r"""\)\s*\.\s*([*\]^])\s*(</remark>)""", re.S)

COMMENT_RE = re.compile(r"""<(fnote|remark)\b([^>]*)>(.*?)</\1>""", re.S)
REMARK_START_RE = re.compile(
    r"""
        ^
        -*
        \s*
        \*?
        [({]
        \s*
    """,
    re.S | re.X,
)
REMARK_END_RE = re.compile(
    r"""
        [ -]*
        (?:
            [ :)}][;\]]
            |
            [:)}]
        )
        [ -]*
        \s*
        [:;.,]?
        \s*
        (
            (?:
                </
                    (?:
                        ref
                        |
                        super
                        |
                        emph
                    )>
                \s*
            )?
            (?:
                <lb/>
                \s*
            )?
        )
        $
    """,
    re.S | re.X,
)
REMARK_RE = re.compile(r"""<remark>(.*?)</remark>""", re.S)
REMARK_MULTIPLE_RE = re.compile(
    r"""
        (?:
            <remark>
                (?:
                    .
                    (?!
                        <remark
                    )
                )*
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

PARA_END_BEFORE_NOTES_RE = re.compile(
    r"""
        (
            <fnote\b
                .*
            </fnote>
            \s*
        )
        (</para>)
    """,
    re.S | re.X,
)

EMPTY_PARA_RE = re.compile(r"""<para>\s*</para>\s*""", re.S)

NOTES_PER_PAGE = {1, 2, 3, 4, 5, 6, 7}
NOTES_BRACKET = {1, 2, 3, 4, 5, 6, 7, 8}
NOTE_START = 0


def processPage(text, previous, result, info, *args, **kwargs):
    global NOTE_START
    remarkInfo = info["remarkInfo"]
    noteInfo = info["noteInfo"]
    page = info["page"]
    prevRemark = previous.get("remark", None)
    prevNotes = previous.get("notes", [])
    prevPage = previous.get("page", None)

    if not text:
        if prevNotes is not None:
            for (ref, body, summary) in prevNotes:
                mark = "" if ref is None else f' ref="{ref}"'
                result.append(f"<fnote{mark}>{body}</fnote>\n")
            previous["notes"] = []
        result.append("\n\n")
        return

    vol = int(info["vol"].lstrip("0"))
    first = info["first"]
    if page in OVERRIDE_NOTE_START:
        NOTE_START = OVERRIDE_NOTE_START[page] - 1
    elif vol in NOTES_PER_PAGE or first:
        NOTE_START = 0

    (text, current) = trimPage(text, info, previous, *args, **kwargs)

    onlyRemark = current["onlyRemark"]
    firstRemark = current["firstRemark"]
    lastRemark = current["lastRemark"]
    startRemark = onlyRemark if onlyRemark else firstRemark if firstRemark else None

    if startRemark:
        (curContent, curSummary) = startRemark

    if prevRemark is None:
        if startRemark:
            remarkInfo["≮"][curSummary].append(page)
    else:
        (prevContent, prevSummary) = prevRemark
        if not startRemark:
            remarkInfo["≯"][prevSummary].append(prevPage)

    previous["remark"] = onlyRemark if onlyRemark else lastRemark

    onlyNote = current["onlyNote"]
    firstNote = current["firstNote"]
    startNote = onlyNote if onlyNote else firstNote if firstNote else None

    if startNote:
        (curRef, curBody, curSummary) = startNote

    if not prevNotes:
        if startNote:
            (curRef, curBody, curSummary) = startNote
            noteInfo[page].append(("≮", curSummary))
    else:
        (prevRef, prevBody, prevSummary) = prevNotes[-1]
        if startNote:
            (thisSummary, thisTrimmed) = summarize(prevSummary + curSummary)
            prevNotes[-1] = (prevRef, prevBody + curBody, thisSummary)
        for (ref, body, summary) in prevNotes:
            mark = "" if ref is None else f' ref="{ref}"'
            result.append(f"<fnote{mark}>{body}</fnote>\n")
        result.append("\n")

    previous["notes"] = current["notes"]
    previous["page"] = page

    result.append(text)
    result.append("\n")


def trimVolume(vol, letters, info, idMap, givenLid, mergeText):
    vol = info["vol"]
    info["noteBrackets"] = int(vol.lstrip("0")) in NOTES_BRACKET


def trimPage(text, info, previous, *args, **kwargs):
    global NOTE_START

    remarkInfo = info["remarkInfo"]
    page = info["page"]

    overrideFirst = OVERRIDE_FIRST.get(page, set())
    overrideLast = OVERRIDE_LAST.get(page, set())
    overrideStart = OVERRIDE_START.get(page, None)

    text = REMARK_SPURIOUS_RE.sub(r"<special>\1</special>", text)
    text = COMMENT_RE.sub(cleanTag, text)
    text = REMARK_END_CORR_RE.sub(r"\1).\2", text)

    text = EMPTY_PARA_RE.sub(r"", text)

    text = applyCorrections(CORRECTIONS, page, text)

    text = REMARK_MULTIPLE_RE.sub(remarkMultiplePre(info), text)

    current = {}

    onlyRemark = None
    firstRemark = None
    lastRemark = None

    ppMatch = REMARK_PRE_POST_RE.search(text)
    if ppMatch:
        (beforeFirst, afterLast) = ppMatch.group(1, 2)
        pre = REMARK_PRE_RE.match(beforeFirst)
        pre = "" if pre is None else pre.group(1).strip()
        post = REMARK_POST_RE.match(afterLast)
        post = "" if post is None else post.group(1).strip()

        matches = tuple(REMARK_RE.finditer(text))
        for (i, match) in enumerate(matches):
            content = match.group(1)
            (summary, trimmed) = summarize(cleanText(content, "remark", full=True))
            startBracket = trimmed.startswith("«")
            endBracket = trimmed.endswith("»")
            isFirst = (
                i == 0
                and not pre
                and (
                    (not startBracket and summary not in overrideFirst)
                    or (overrideStart and content.startswith(overrideStart))
                )
            )
            isLast = (
                i == len(matches) - 1
                and not post
                and (not endBracket and summary not in overrideLast)
            )
            content = cleanText(content, "remark")
            if overrideStart and content.startswith(overrideStart):
                content = "(" + content[1:]
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

    noteInfo = info["noteInfo"]
    (text, marks, notesStr) = formatNotes(text, info)

    notes = []
    onlyNote = None
    firstNote = None

    bodies = {}
    thisNoteInfo = []

    if notesStr:
        matches = tuple(NOTE_RE.finditer(notesStr))
        ref = NOTE_START
        for (i, match) in enumerate(matches):
            atts = match.group(1)
            body = match.group(2)
            mmatch = NOTE_ATT_REF_RE.search(atts)
            markBody = mmatch.group(1) if mmatch else ""
            (summary, trimmed) = summarize(cleanText(body, "fnote", full=True))
            isFirst = True if i == 0 and not mmatch else False
            isLast = i == len(matches) - 1
            body = cleanText(body, "fnote")
            if isFirst:
                firstNote = (ref, body, summary)
                if isLast:
                    onlyNote = firstNote
                    firstNote = None
                    label = "1"
                else:
                    label = "F"
                thisNoteInfo.append((label, summary))
            else:
                ref += 1
                notes.append((ref, body, summary))
                bodies[ref] = (markBody, summary)

    NOTE_START += max((len(marks), len(bodies)))

    if not bodies and not marks:
        label = "0"
        thisNoteInfo.append((label, ""))
        for x in reversed(thisNoteInfo):
            noteInfo[page].insert(0, x)
    else:
        allRefs = sorted(set(marks) | set(bodies))
        for ref in allRefs:
            markText = marks.get(ref, "")
            (markBody, summary) = bodies.get(ref, ("", ""))

            thisNoteInfo.append((ref, markText, markBody, summary))
        noteInfo[page].extend(thisNoteInfo)

    current["notes"] = notes
    current["onlyNote"] = onlyNote
    current["firstNote"] = firstNote
    return (text, current)


LEGEND_REMARK = {
    "≮": "continuing remark without previous remark on preceding page",
    "≯": "to-be-continued remark without next remark on following page",
    "x": "remark without opening and without closing",
    "(": "remark with opening and without closing",
    ")": "remark without opening and with closing",
    "m": "multiple remarks combined into one",
    "1": "single remark continuing from previous page and extending to next page",
    "F": "first remark on page continuing from previous page",
    "L": "last remark on page continuing to next page",
    "0": "page without remarks",
    "v": "remark without issues",
}

LEGEND_NOTE = {
    "≮": (None, "continuing note without previous note on preceding page"),
    "1": (None, "single note continuing from previous page and extending to next page"),
    "F": (None, "first note on page continuing from previous page"),
    "0": (None, "page without notes"),
    "!": (0, "missing mark in body or text bot not both"),
    "≠": (0, "mark in conflict with sequence number"),
    "↓": (0, "no mark in text"),
    "°": (0, "indefinite mark in body and text"),
    "+": (20, "mark is one more than sequence number"),
    "-": (20, "mark is one less than sequence number"),
    "→": (40, "no mark in body"),
    "∉": (40, "sequence number not contained in mark"),
    "∈": (80, "sequence number contained in mark"),
    "*": (50, "mark is * or x, will be filled in by sequence number"),
    "<": (50, "indefinite mark in body only"),
    ">": (80, "indefinite mark in text only"),
    ":": (100, "mark overridden to be good"),
    "∷": (100, "mark exactly equal to sequence number"),
    "≡": (100, "mark text and body exactly equal"),
    "=": (100, "mark text and body exactly equal after overriding"),
    "x": (100, "mark text and body clearly unequal"),
}
LEGEND_SCORE = {x[0]: x[1][0] for x in LEGEND_NOTE.items()}

INDEF = {"*", "x"}


def corpusPost(info):
    print("REMARKS:\n")
    remarkInfo = info["remarkInfo"]
    totalPatterns = 0
    totalRemarks = 0
    with open(f"{REP}/remarks.tsv", "w") as fh:
        for (label, legend) in LEGEND_REMARK.items():
            thisRemarkInfo = remarkInfo.get(label, {})

            nPatterns = len(thisRemarkInfo)
            nRemarks = sum(len(x) for x in thisRemarkInfo.values())
            if label not in {"m", "1", "F", "L", "0"}:
                totalPatterns += nPatterns
                totalRemarks += nRemarks

            msg = f"{label}: {nPatterns:>5} in {nRemarks:>5} x {legend}"
            print(f"\t{msg}")
            fh.write(f"\n-------------------\n{msg}\n\n")

            for (summary, docs) in sorted(thisRemarkInfo.items(), key=byOcc):
                fh.write(f"{summary} {docSummary(docs).rstrip()}\n")

        msg = f"T: {totalPatterns:>5} in {totalRemarks:>5} x in total"
        print(f"\t{msg}")

    noteInfo = info["noteInfo"]

    totalNotes = 0
    totalPages = len(noteInfo)
    totalScore = 0
    scores = collections.defaultdict(list)

    noteLog = collections.defaultdict(dict)

    for page in sorted(noteInfo):
        report = []
        overrideMarkText = OVERRIDE_NOTE_TEXT.get(page, {})
        overrideMarkBody = OVERRIDE_NOTE_BODY.get(page, {})
        entries = noteInfo[page]

        score = 0
        nNotes = 0

        for entry in entries:
            if len(entry) == 2:
                (label, summary) = entry
                report.append(f"\t{label} «{summary or ''}»\n")
                continue

            nNotes += 1
            (ref, markTextOrig, markBodyOrig, summary) = entry
            markText = normalize(markTextOrig)
            markBody = normalize(markBodyOrig)

            textParts = tuple(n for n in markText.split())
            bodyParts = tuple(n for n in markBody.split())

            textNums = {int(n) for n in textParts if n.isdigit()}
            bodyNums = {int(n) for n in bodyParts if n.isdigit()}

            polyTextNums = len(textParts) > 1
            polyBodyNums = len(bodyParts) > 1

            labelText = (
                "↓"
                if not markText
                else "∷"
                if str(ref) == markText
                else ":"
                if overrideMarkText.get(ref, None) == markText
                else "∈"
                if ref in textNums
                else "∉"
                if polyTextNums and ref not in textNums
                else "*"
                if markText == "*" or markText == "x"
                else "-"
                if str(ref + 1) == markText
                else "+"
                if str(ref - 1) == markText
                else "≠"
            )
            labelBody = (
                "→"
                if not markBody
                else "∷"
                if str(ref) == markBody
                else ":"
                if overrideMarkBody.get(ref, None) == markBody
                else "≃"
                if ref in bodyNums
                else "∉"
                if polyBodyNums and ref not in bodyNums
                else "*"
                if markBody == "*" or markBody == "x"
                else "-"
                if str(ref - 1) == markBody
                else "+"
                if str(ref + 1) == markBody
                else "≠"
            )
            label = (
                "!"
                if not markText and markBody or markText and not markBody
                else "°"
                if markText in INDEF and markBody in INDEF
                else "<"
                if markBody in INDEF
                else ">"
                if markText in INDEF
                else "≡"
                if markText == markBody
                else "="
                if overrideMarkText.get(ref, markText)
                == overrideMarkBody.get(ref, markBody)
                else "x"
            )
            thisScore = (
                LEGEND_SCORE[labelText] + LEGEND_SCORE[labelBody] + LEGEND_SCORE[label]
            ) / 3
            score += thisScore
            markTextRep = f"⌈{markText}⌉"
            markBodyRep = f"⌈{markBody}⌉"
            report.append(
                f"\t{label}"
                f" {ref:>2}"
                f" {labelText}{markTextRep:>12}"
                f" {markBodyRep:<4}{labelText}"
                f" «{summary}»\n"
            )
        score = 100 if nNotes == 0 else int(round(score / nNotes))
        scoreThreshold = int((score // 10) * 10)
        scores[scoreThreshold].append(page)
        totalScore += score
        totalNotes += nNotes
        avScore = 100 if totalNotes == 0 else int(round(totalScore / totalPages))

        heading = f"score={score:>3} for {page}\n"
        log = "".join(report)
        noteLog[score][page] = f"{heading}{log}"

    with open(f"{REP}/notes.tsv", "w") as fh:
        for score in sorted(noteLog):
            pages = noteLog[score]
            for page in sorted(pages):
                fh.write(pages[page])

    minScore = min(noteLog)
    print(
        f"NOTES: {totalNotes} notes on {totalPages} pages"
        f" with score: average={avScore}, minimum={minScore}"
    )
    for score in sorted(scores):
        pages = scores[score]
        pagesRep = docSummary(pages)
        print(f"\tscore {score:>3} ({pagesRep})")


def byOcc(x):
    (summary, docs) = x
    return (docs[0], summary) if docs else ("", summary)


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
            (summary, trimmed) = summarize(cleanText(content, "remark", full=True))
            content = cleanText(content, "remark")
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


REF_RE = re.compile(
    fr"""
        (<ref>)
        ([^<]*)
        (</ref>)
        (
            (?:
                [XIVLMC]*
                \s*
                (?:
                    [0-9]{{1,2}}
                    \s+
                    {MONTH_DETECT_PAT}
                    \s+
                    1[6-8][0-9][0-9]
                    \s*
                )?
                \s*
                (?:
                    ,
                    |
                    p\.
                    |
                    [0-9rv]+
                    |
                    -
                    |
                    (?:
                        </?emph>
                        |
                        <lb/>
                    )
                    |
                    \s+
                )
            )+
        )
        (
            (?:
                [^<]*
                </emph>
            )?
        )
    """,
    re.S | re.X,
)


def refRepl(match):
    (start, inside, end, trail, tail) = match.group(1, 2, 3, 4, 5)
    trail = trail.replace("<emph>", "").replace("</emph>", "").replace("<lb/>", " ")
    tail = tail.replace("</emph>", "")
    inside = (inside + trail).replace("\n", " ")
    inside = WHITE_RE.sub(" ", inside)
    return f"{start}{inside}{end}{tail}"


NOTE_RENAME_P_RE = re.compile(r"""<fnote\b[^>]*>(.*?)</fnote>""", re.S)


def filterNotes(match):
    notes = match.group(1)
    word = match.group(2)
    if word:
        notes = NOTE_RENAME_P_RE.sub(r"""<para>\1</para>""", notes)
    return f"""{notes}{word}"""


def filterNotes2(match):
    pre = match.group(1)
    notes = match.group(2)
    notes = NOTE_RENAME_P_RE.sub(r"""<para>\1</para>""", notes)
    return f"""{pre}{notes}"""


NOTES_FILTER1 = (
    (
        re.compile(
            r"""
                (
                    </table>
                    \s*
                    (?:
                        </para>
                        \s*
                    )?
                )
                (
                    (?:
                        <fnote>
                            .*?
                        </fnote>
                        \s*
                    )+
                )
            """,
            re.S | re.X,
        ),
        filterNotes2,
    ),
)
NOTES_FILTER2 = (
    (
        re.compile(
            r"""
                (
                    (?:
                        <fnote[^>]*>
                            .*?
                        </fnote>
                        \s*
                    )+
                )
                (\S*)
            """,
            re.S | re.X,
        ),
        filterNotes,
    ),
)
NOTES_ALL_RE = re.compile(
    r"""
        ^
            (.*?)
            (
                (?:
                    <fnote.*?</fnote>
                    \s*
                )+
            )
            (.*?)
        $
    """,
    re.S | re.X,
)
NOTE_RE = re.compile(r"""<fnote\b([^>]*)>(.*?)</fnote>""", re.S)

NOTE_COLLAPSE_RE = re.compile(
    r"""
    (<fnote\ ref=[^>]*>)
    (.*?)
    (</fnote>)
    (
        (?:
            \s*
            <(
                fnote
                |
                para
            )>
            .*?
            </\5>
        )+
    )
    """,
    re.S | re.X,
)


def collapseNotes(match):
    (firstNoteStart, firstNoteText, firstNoteEnd, restNotes) = match.group(1, 2, 3, 4)
    restNotes = restNotes.replace("<fnote>", " ")
    restNotes = restNotes.replace("</fnote>", " ")
    restNotes = restNotes.replace("<para>", " ")
    restNotes = restNotes.replace("</para>", " ")
    return f"""{firstNoteStart}{firstNoteText} {restNotes}{firstNoteEnd}"""


NOTE_MARK_RE = re.compile(r"""<fnote ref="([^"]*)">""", re.S)
NOTE_ATT_REF_RE = re.compile(r"""\bref="([^"]*)["]""", re.S)

FOLIO_DWN_RE = re.compile(r"""<folio>\s*(.*?)\s*</folio>""", re.S)
MARK_DWN_RE = re.compile(r"""<fref ref="([^"]*)"/>""", re.S)
TABLE_DWN_RE = re.compile(r"""<table\b[^>]*>\s*(.*?)\s*</table>""", re.S)
ROW_DWN_RE = re.compile(r"""<row\b[^>]*>\s*(.*?)\s*</row>""", re.S)
CELL_DWN_RE = re.compile(r"""<cell\b[^>]*>\s*(.*?)\s*</cell>""", re.S)


def tableDown(match):
    text = match.group(1)
    rows = []
    for rowStr in ROW_DWN_RE.findall(text):
        rows.append(CELL_DWN_RE.findall(rowStr))
    columns = max(len(row) for row in rows)

    result = []
    result.append(
        "".join((("" if i == 0 else " | ") + f" {i + 1} ") for i in range(columns))
    )
    result.append(
        "".join((("" if i == 0 else " | ") + " --- ") for i in range(columns))
    )
    for row in rows:
        result.append(
            "".join(
                (("" if i == 0 else " | ") + f" {cell} ")
                for (i, cell) in enumerate(row)
            )
        )
    return "\\n".join(result)


def cleanTag(match):
    tag = match.group(1)
    atts = match.group(2)
    text = match.group(3)
    text = cleanText(text, tag)
    return f"<{tag}{atts}>{text}</{tag}>"


def cleanText(text, tag, full=False):
    if full:
        text = text.replace("<lb/>", " ")
        text = text.replace("<emph>", "*")
        text = text.replace("</emph>", "*")
        text = text.replace("<und>", "_")
        text = text.replace("</und>", "_")
        text = text.replace("<super>", "^")
        text = text.replace("</super>", "^")
        text = text.replace("<special>", "`")
        text = text.replace("</special>", "`")
        text = text.replace("<ref>", "[")
        text = text.replace("</ref>", "]")
        text = MARK_DWN_RE.sub(r"[=\1]", text)
        text = FOLIO_DWN_RE.sub(r" {\1} ", text)
        text = text.replace("\n", " ")
        text = text.strip()
        text = WHITE_RE.sub(" ", text)
        text = TABLE_DWN_RE.sub(tableDown, text)

    if tag == "remark":
        text = REMARK_START_RE.sub(r"«", text)
        text = REMARK_END_RE.sub(r"\1»", text)
    text = REF_RE.sub(refRepl, text)

    if full:
        if "<" in text:
            print(f"\nunclean {tag}")
            print(f"\t==={text}===")
    return text


def markedUnNoteRepl(match):
    (pre, num, text) = match.group(1, 2, 3)
    pre = pre.replace("<lb/>", "")
    text = text.strip()
    if text.endswith("<lb/>"):
        text = text[0:-5].rstrip()
    if text and num == "0":
        print(f"X {pre=}, {num=} {text=}")
    return f"{pre}\n<note>{num}) {text}</note>\n" if text else match.group(0)


MARKED_NOTE_DBL_RE = re.compile(r"""(<lb/></note>)(<note>)""", re.S)
MARK_LETTERS_BODY = "[a-eg-oq-z]"
MARKED_NOTE = (
    (
        re.compile(
            fr"""
                <note>
                \s*
                <super>
                \s*
                (
                    [0-9]{{1,2}}
                    |
                    {MARK_LETTERS_BODY}
                )
                \s*
                \)?
                </super>
                \s*
                \)?
                \s*
            """,
            re.S | re.X,
        ),
        r"""<note ref="\1">""",
    ),
    (
        re.compile(
            fr"""
                <note>
                \s*
                (
                    [0-9]{{1,2}}
                    |
                    {MARK_LETTERS_BODY}
                )
                \b
                \s*
                \)?
                \s*
            """,
            re.S | re.X,
        ),
        r"""<note ref="\1">""",
    ),
    (
        re.compile(
            fr"""
                <note>
                \s*
                <emph>
                (
                    [0-9]{{1,2}}
                    |
                    {MARK_LETTERS_BODY}
                )
                \b
                \s*
                \)?
                ([^<]*)
                </emph>
                \s*
            """,
            re.S | re.X,
        ),
        r"""<note ref="\1">\2""",
    ),
)

MARKED_UN_NOTE = (
    (
        re.compile(
            fr"""
            \s*
            (
                (?:
                    <lb/>
                    |
                    <para>
                )
            )
            \s*
            (
                [0-9]{{1,2}}
                |
                {MARK_LETTERS_BODY}
            )
            \s*
            \)
            \s*
            (.*?)
            (?=
                (?:
                    <lb/>
                    \s*
                    (?:
                        [0-9]{{1,2}}
                        |
                        {MARK_LETTERS_BODY}
                    )
                    \s*
                    \)
                )
                |
                (?:
                    (?:
                        <lb/>
                    )?
                    (?:
                        <note\b
                        |<para
                        |</para
                        |<remark
                        |$
                    )
                )
            )
        """,
            re.S | re.X,
        ),
        markedUnNoteRepl,
    ),
    (
        re.compile(
            r"""
                <para\b[^>]*>
                \s*
                (
                    <note\b[^>]*>
                    (?:
                        .
                        (?!
                            <para\b
                        )
                    )*
                    </note>
                )
                \s*
                </para>
                \s*
            """,
            re.S | re.X,
        ),
        r"\1\n",
    ),
    (
        re.compile(
            r"""
                (
                    <note\b[^>]*>
                    (?:
                        .
                        (?!
                            <para\b
                        )
                    )*
                    </note>
                )
                \s*
                (</para>)
                \s*
            """,
            re.S | re.X,
        ),
        r"\2\n\1\n",
    ),
)


NOTE_RENAME_RE = re.compile(r"""<note\b([^>]*)>(.*?)</note>""", re.S)
SPURIOUS_PARA_RE = re.compile(
    fr"""
        (
            <lb/>
            \s*
        )
        </para>
        \s*
        <para>
        \s*
        (
            [0-9]{{1,2}}
            |
            {MARK_LETTERS_BODY}
        )
        \s*
        \)
        \s*
    """,
    re.S | re.X,
)
DEL_LB_RE = re.compile(r"""(</note>)\s*<lb/>\s*""", re.S)


def formatNotes(text, info):
    # 01:p02024

    showPage = False and 'n="534"' in text
    (tb, te) = (-500, -100)
    if showPage:
        print(
            "=== [AAAA] ==============================================================="
        )
        print(text[tb:te])
    text = SPURIOUS_PARA_RE.sub(r"""\1\2) """, text)
    if showPage:
        print(
            "=== [BBBB] ==============================================================="
        )
        print(text[tb:te])
    text = MARKED_NOTE_DBL_RE.sub(r"""\1\n\2""", text)
    if showPage:
        print(
            "=== [CCCC] ==============================================================="
        )
        print(text[tb:te])
    for (convertRe, convertRepl) in MARKED_UN_NOTE:
        text = convertRe.sub(convertRepl, text)
    if showPage:
        print(
            "=== [DDDD] ==============================================================="
        )
        print(text[tb:te])
    text = DEL_LB_RE.sub(r"""\1\n""", text)
    if showPage:
        print(
            "=== [EEEE] ==============================================================="
        )
        print(text[tb:te])
    for (trimRe, trimRepl) in MARKED_NOTE:
        text = trimRe.sub(trimRepl, text)
    if showPage:
        print(
            "=== [FFFF] ==============================================================="
        )
        print(text[tb:te])
    text = NOTE_RENAME_RE.sub(r"""<fnote\1>\2</fnote>""", text)
    if showPage:
        print(
            "=== [GGGG] ==============================================================="
        )
        print(text[tb:te])
    text = PARA_END_BEFORE_NOTES_RE.sub(r"\2\n\1", text)
    if showPage:
        print(
            "=== [HHHH] ==============================================================="
        )
        print(text[tb:te])
    for (trimRe, trimRepl) in NOTES_FILTER1:
        text = trimRe.sub(trimRepl, text)
    if showPage:
        print(
            "=== [IIII] ==============================================================="
        )
        print(text[tb:te])
    text = NOTE_COLLAPSE_RE.sub(collapseNotes, text)
    if showPage:
        print(
            "=== [JJJJ] ==============================================================="
        )
        print(text[tb:te])
    for (trimRe, trimRepl) in NOTES_FILTER2:
        text = trimRe.sub(trimRepl, text)
    if showPage:
        print(
            "=== [KKKK] ==============================================================="
        )
        print(text[tb:te])
    text = COMMENT_RE.sub(cleanTag, text)
    if showPage:
        print(
            "=== [LLLL] ==============================================================="
        )
        print(text[tb:te])
    nmatch = NOTES_ALL_RE.match(text)
    if nmatch:
        (text, notesStr, post) = nmatch.group(1, 2, 3)

        if post:
            print("\nMaterial after footnotes:")
            print(f"\tNOTES==={notesStr}")
            print(f"\tPOST ==={post}")
    else:
        notesStr = ""

    noteBrackets = info["noteBrackets"]
    markDetectRe = MARK_PLAIN_BR_RE if noteBrackets else MARK_PLAIN_RE

    text = CL_BR_ESCAPE_RE.sub(r"←\1→", text)
    text = FL_RE.sub(r"ƒ \1", text)

    if not noteBrackets:
        for (escRe, escRepl) in CL_BR_NO:
            text = escRe.sub(escRepl, text)

    matches = tuple(markDetectRe.finditer(text))
    replacements = []
    marks = {}
    ref = NOTE_START
    for (i, match) in enumerate(matches):
        complete = match.group(0)
        if noteBrackets:
            (mark, trail) = match.group(1, 2)
        else:
            mark = match.group(1)
            trail = ""
        if noteBrackets:
            if "<super>" in complete:
                trail = trail.replace("</super>", "")
            else:
                mark = (
                    mark.replace("<super>", "")
                    .replace("</super>", "")
                    .replace("⌊", "")
                    .replace("⌋", "")
                )
        (b, e) = match.span()
        ref += 1
        marks[ref] = mark
        if showPage:
            print(f"=== [MARK RESOLUTION]=======\n{mark=} ==> {ref=}")
        replacement = f"""<fref ref="{ref}"/> {trail}"""
        replacements.append((b, e, replacement))
    for (b, e, r) in reversed(replacements):
        text = text[0:b] + r + text[e:]
    text = CL_BR_RESTORE_RE.sub(r"(\1)", text)
    if showPage:
        print(
            "=== [LLLL] ==============================================================="
        )
        print(f"{text}{notesStr}"[tb:te])
    return (text, marks, notesStr)


def normalize(text):
    return (
        text.replace("i", "1")
        .replace("'", "1")
        .replace("l", "1")
        .replace("L", "1")
        .replace("b", "6")
        .replace("y", "9")
        .replace("z", "3")
        .replace("n", "11")
    )


MARK_LETTERS_TEXT_BR = "xyziLlbn"
MARK_LETTERS_TEXT = "i"
MARK_SIGNS_TEXT = "*'"

MARK_PLAIN_BR_RE = re.compile(
    fr"""
        (?:
            ⌊
            |
            <super>
        )?
        (
            (?:
                (?:
                    \b
                    [{MARK_LETTERS_TEXT_BR}]
                )
                |
                [*'0-9]
            )
            [{MARK_LETTERS_TEXT_BR}{MARK_SIGNS_TEXT}0-9]?
            (?:
                \s+
                [{MARK_LETTERS_TEXT_BR}{MARK_SIGNS_TEXT}0-9]{{1,2}}
            )*
        )
        (?:</super>\ ?)?
        (?:
            \)
            |
            ⌋
        )
        (
            (?:
                [^<]*
                </super>
            )?
        )
    """,
    re.S | re.X,
)

# Lots of <super>1</super> are really apostrophes.
# But they can also be frefs. Sigh
# We can try to weed them out at the moment when we know the note bodies.
# If then the number in the super element does not correspond to a note body
# we turn it into an apostrophe

MARK_PLAIN_RE = re.compile(
    r"""
        (
            (?:
               <super>
               [0-9]{1,2}
               </super>
            )
            |
            (?:
               ⌊
               [0-9]{1,2}
               ⌋
            )
            |
            (?:
                (?<=[a-z])
                [0-9]{1,2}
                \b
            )
        )
    """,
    re.S | re.X,
)

CL_BR_ESCAPE_RE = re.compile(
    r"""
        \(
        (
            [^)]*
        )
        \)
    """,
    re.S | re.X,
)
CL_BR_RESTORE_RE = re.compile(r"""←([^→]*)→""", re.S)

CL_BR_NO = (
    (
        re.compile(
            r"""
                ([a-z”,]{3,})
                ([0-9]{1,2})
                \b
            """,
            re.S | re.X,
        ),
        r"\1⌊\2⌋",
    ),
    (
        re.compile(
            r"""
                <super>
                ([0-9]{1,2})
                </super>
            """,
            re.S | re.X,
        ),
        r"⌊\1⌋",
    ),
)

FL_RE = re.compile(r"""\bf([0-9]+)""", re.S)


MARK_PLAIN_AFTER_RE = re.compile(
    r"""
        <super>
        \s*
        (
            <fref[^>]*/>
            .*?
        )
        </super>
    """,
    re.S | re.X,
)


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
