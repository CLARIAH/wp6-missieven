import sys
import os
import collections
import re
from glob import glob

import fitz
import pprint as pp

from lib import (
    PDF_DIR,
    PDF_REPORT_DIR,
    TEXT_DIR,
    TEXT_FILE,
    FMT_FILE,
    STRUCT_FILE,
    FINE_FILE,
    HEAD_FILE,
    FN_BODY_FILE,
    FN_MARK_FILE,
    TIT_FILE,
    XML_DIR,
    PDF_VOL,
    BAND_OFFSET,
    RESUME_TABLE,
    initTree,
    ucFirst,
)


FAMILY = {
    "TimesTenLTStd": "",
    "Garamond": "",
    "Nutso3": "sym",
    "SymbolMT": "sym",
}

SIZE = {
    130: "",
    127: "",
    120: "",
    119: "",
    110: "",
    95: "",
    90: "",
    85: "",
    80: "small",
    52: "xsmall",
    49: "xsmall",
    46: "xsmall",
}

STYLE = {
    "Bold": "",
    "Italic": "i",
    "Italic-SC7": "i",
    "BoldItalic": "i",
    "Roman": "n",
    "Regular": "",
}

FLAGS = {
    0: "",
    4: "",
    5: "sup",
    6: "i",
    7: "fn",
    20: "",
    22: "i",
}

PAGE_INFO = dict(
    i=dict(
        start=15,
        end=550,
        offset=-14,
    ),
    ii=dict(
        start=11,
        end=550,
        offset=526,
    ),
)

XS = {
    0: dict(start=94, indent=116),
    1: dict(start=71, indent=94),
}
YS = dict(
    start=76,
    offset=11,
)

CODES = set(
    """
    ==
    TI
    HD
    PE
    PO
    LE
    LO
    SE
    SO
    FM
    FB
""".strip().split()
)

CODES_TABLE = set(
    """
    TB
    TE
    RB
    RE
""".strip().split()
)

CODES_SKIP = set(
    """
    ==
    FB
    """.strip().split()
)

CODES_NO_FMT = set(
    """
    ==
    TI
    HD
    FM
    FB
""".strip().split()
)

CODES_SPAN = set(
    """
    SE
    SO
""".strip().split()
)

CODES_OUT_TABLE = set(
    """
    TI
    HD
    FB
    PE
    LE
    SE
""".strip().split()
)

CORRECTIONS = {
    "Bengaaij4": dict(text="Bengaaij\n  4 \n", fmt=(None, dict(st="fn"), None)),
    "[fol. 208)": dict(text="[fol. 208]", fmt=(None,)),
    "8e>": dict(text="83", fmt=(None,)),
    "<r>": dict(text="", fmt=(None,)),
    "</>": dict(text=" ", fmt=(None,)),
}
CORRECTIONS_APPLIED = collections.defaultdict(list)

PAGE_CORRECTIONS = {
    667: dict(
        text=(("[fol. 2094\n  b\n  ] ", "[fol. 2094b]\n  "),),
        fmt=(("  x=161,y=-3,st=fn,s=xsmall\n  x=164,", "  "),),
    ),
}
PAGE_CORRECTIONS_APPLIED = collections.defaultdict(lambda: collections.defaultdict(set))

LETTERS = r"""[^A-Za-z0-9 \t.,<>;:'"/?%\[\](){}=+!&…ƒ´`’‘′“”„¼½äáàâëéèêïöóüæç_–-]"""

TRANS = str.maketrans(
    """´„`“’”‘′–""",
    """'"`"'"''-""",
)
WORD_CHARS = r"""[a-zäáàâëéèêïíìîöóòôüúùûæœøãñõç]"""


def pprint(x, fh=None):
    pp.pprint(x, stream=fh, indent=2)


def chars(sourceLines):
    newSourceLines = []
    for item in sourceLines:
        (code, *data) = item
        text = data[-1].translate(TRANS)
        newSourceLines.append([code, *data[0:-1], text])

    sourceLines.clear()
    sourceLines.extend(newSourceLines)


def dataFromPdf(export=False):
    styleFlags = collections.Counter()
    sizeFlags = collections.Counter()
    xS = collections.Counter()
    yS = collections.Counter()

    def readPdf(pageNum, pdfPath, mainTitle=False, export=False):
        doc = fitz.open(pdfPath)
        headText = []
        texts = []
        fmts = []
        pg = None
        nBlocks = 0
        newLines = 0

        xInfo = XS[pageNum % 2]
        xStart = xInfo["start"]
        xIndent = xInfo["indent"]

        titleLine = mainTitle

        for page in doc:
            prevY = 0
            firstLine = True
            firstSpan = True
            headLine = False
            textPage = page.get_textpage()
            data = textPage.extractDICT()
            if export:
                pageStr = f"{pageNum:>04}"
                subDir = pageStr[0:2]
                targetDir = f"{TEXT_DIR}/individual/{subDir}"
                initTree(targetDir)
                with open(f"{targetDir}/{pageStr}.txt", "w") as ph:
                    pprint(data, fh=ph)
            blocks = data["blocks"]
            nBlocks += len(blocks)
            for block in blocks:
                lines = block["lines"]
                for line in lines:
                    lineText = []
                    lineFmt = []
                    spans = line["spans"]
                    firstSpanInLine = True
                    for span in spans:
                        text = span["text"]
                        if text == " ":
                            continue
                        fontInfo = span["font"]
                        parts = fontInfo.split("-", 1)
                        if len(parts) < 2:
                            parts.append("Regular")
                        (family, style) = parts
                        familyShort = FAMILY.get(family, None)
                        if familyShort is None:
                            print(f"\nUNKNOWN FAMILY: {family}")
                            quit()
                        styleShort = STYLE.get(style, None)
                        if styleShort is None:
                            print(f"\nUNKNOWN STYLE: {style}")
                            quit()
                        size = int(round(10 * span["size"]))
                        sizeShort = SIZE.get(size, None)
                        if sizeShort is None:
                            print(f"\nUNKNOWN SIZE: {size}")
                            quit()
                        flags = span["flags"]
                        flagsShort = FLAGS.get(flags, None)
                        if flagsShort is None:
                            print(f"\nUNKNOWN FLAGS: {flags}")
                            quit()
                        text = span["text"]
                        if "\n" in text:
                            newLines += 1
                        if firstLine and firstSpan:
                            pg = int(text)
                            headLine = True
                            firstSpan = False
                            continue

                        if headLine:
                            if styleShort == "i":
                                lineText.append(text)
                                firstSpan = False
                                continue

                            headLine = False

                        if titleLine:
                            firstSpan = False
                            continue

                        fmt = dict()
                        (x, y) = span["origin"]
                        x = int(round(x))
                        if x != xStart:
                            if x == xIndent:
                                fmt["in"] = ">"
                            else:
                                newX = x - xStart
                                fmt["x"] = newX
                                xS[newX] += 1
                        y = int(round(y))
                        newY = y - prevY
                        if firstSpanInLine:
                            if (
                                prevY == 0
                                and newY != YS["start"]
                                or prevY != 0
                                and newY != YS["offset"]
                            ):
                                fmt["y"] = newY
                                yS[newY] += 1
                            prevY = y
                            firstSpanInLine = False
                        else:
                            if newY != 0:
                                fmt["y"] = newY
                                yS[newY] += 1
                        if familyShort:
                            fmt["f"] = familyShort
                        if flagsShort:
                            fmt["st"] = flagsShort
                        elif styleShort:
                            fmt["st"] = styleShort
                        if sizeShort:
                            fmt["s"] = sizeShort

                        lineText.append(text)
                        lineFmt.append(fmt)
                        styleFlags[(styleShort, flagsShort)] += 1
                        sizeFlags[(sizeShort, flagsShort)] += 1
                        firstSpan = False

                    if firstLine:
                        firstLine = False
                    else:
                        if headLine:
                            headText = lineText
                            headLine = False
                        elif titleLine:
                            titleLine = False
                        else:
                            newLineText = []
                            newLineFmt = []

                            for (span, fmt) in zip(lineText, lineFmt):
                                corrected = False
                                newSpan = span
                                for (pattern, replacement) in CORRECTIONS.items():
                                    pos = newSpan.find(pattern)
                                    if pos >= 0:
                                        replText = replacement["text"]
                                        newSpan = newSpan.replace(pattern, replText, 1)
                                        replFmt = replacement.get("fmt", [fmt])

                                        CORRECTIONS_APPLIED[pattern].append(
                                            (replText, pageNum, newSpan)
                                        )
                                        corrected = True

                                if corrected:
                                    for s in newSpan.split("\n"):
                                        newLineText.append(s)
                                    for f in replFmt:
                                        newLineFmt.append(fmt if f is None else f)
                                else:
                                    newLineText.append(span)
                                    newLineFmt.append(fmt)

                            texts.append(newLineText)
                            fmts.append(newLineFmt)

        if pg is None:
            if nBlocks > 0:
                print(f"\nPAGE WITHOUT PAGE NUMBER: {pageNum}")
                quit()
            pg = pageNum
        if pg != pageNum:
            print(f"\nDISCREPANCY in PAGE NUMBERS {pg} =/= {pageNum}")
            quit()

        return (pg, headText, texts, fmts, newLines)

    initTree(PDF_REPORT_DIR, fresh=False)

    if export:
        initTree(f"{TEXT_DIR}/individual", fresh=True)

    pages = []

    prevPageNum = None
    prevFilePageNum = None

    for subDir in sorted(glob(f"{PDF_DIR}/*")):
        if not os.path.isdir(subDir):
            continue
        band = subDir.rsplit("-", 1)[1]
        thisPageInfo = PAGE_INFO[band]
        start = thisPageInfo["start"]
        end = thisPageInfo["end"]
        offset = thisPageInfo["offset"]
        for pdfPath in sorted(glob(f"{subDir}/*.pdf")):
            filePageNum = int(pdfPath.rsplit(".", 1)[0].rsplit("_", 1)[1].lstrip("0"))
            if filePageNum < start or filePageNum > end:
                continue

            pageNum = filePageNum + offset
            if prevPageNum is not None:
                expectedPageNum = prevPageNum + 1
                if expectedPageNum != pageNum:
                    fileName = pdfPath.split("/")[-1]
                    print(
                        f"\nWARNING Irregualar page sequence before {fileName}: "
                        f"from {prevPageNum} to {pageNum}"
                    )
                    textPath = f"{PDF_DIR}/{expectedPageNum:>04}.txt"
                    fmtPath = f"{PDF_DIR}/{expectedPageNum:>04}.fmt"
                    if os.path.exists(textPath) and os.path.exists(fmtPath):
                        fileSpec = (textPath, fmtPath)
                        print(
                            f"\nREPLACE MISSING PAGE {expectedPageNum}"
                            f" (band {band} {prevFilePageNum + 1:>03})"
                            f"by supplied {expectedPageNum:>04}.txt/fmt"
                        )
                        pages.append(
                            (band, prevFilePageNum + 1, expectedPageNum, fileSpec)
                        )
                    else:
                        print(
                            f"\nSKIP MISSING PAGE {expectedPageNum}"
                            f" (band {band} {prevFilePageNum + 1:>03})"
                        )
            prevPageNum = pageNum
            prevFilePageNum = filePageNum

            if os.path.getsize(pdfPath) == 0:
                textPath = f"{PDF_DIR}/{pageNum}.txt"
                fmtPath = f"{PDF_DIR}/{pageNum}.fmt"
                if os.path.exists(textPath) and os.path.exists(fmtPath):
                    fileSpec = (textPath, fmtPath)
                    print(f"\nREPLACE EMPTY {pdfPath} by supplied {pageNum}.txt/fmt")
                else:
                    print(f"\nSKIP EMPTY {pdfPath}")
                    continue
            else:
                fileSpec = pdfPath
            pages.append((band, filePageNum, pageNum, fileSpec))

    textLines = []
    fmtLines = []
    headLines = []
    newLines = 0

    mainTitle = True
    for (band, filePageNum, pageNum, fileSpec) in pages:
        sys.stderr.write(f"\r{band:>2} {filePageNum:>04} = {pageNum:>04}")
        if type(fileSpec) is tuple:
            (textPath, fmtPath) = fileSpec
            with open(textPath) as ih:
                for line in ih:
                    textLines.append(line)
            with open(fmtPath) as ih:
                for line in ih:
                    fmtLines.append(line)
            continue

        pdfPath = fileSpec
        (pg, headText, texts, fmts, theseNewLines) = readPdf(
            pageNum, pdfPath, mainTitle=mainTitle, export=export
        )
        mainTitle = False
        newLines += theseNewLines
        ok = pageNum == pg
        extra = "" if ok else f"={pg}"
        label = "====" if ok else "==XX"
        pageIdent = f"{label}{pageNum:>04}{extra} file={band} {filePageNum:>04}"

        textLines.append(f"{pageIdent}\n")
        fmtLines.append(f"{pageIdent}\n")

        for line in texts:
            firstSpan = True
            for span in line:
                code = "> " if firstSpan else "  "
                firstSpan = False
                newLine = f"{code}{span}\n"
                textLines.append(newLine)

        for line in fmts:
            firstSpan = True
            for span in line:
                code = "> " if firstSpan else "  "
                firstSpan = False
                fmt = ",".join(f"{k}={v}" for (k, v) in span.items())
                newLine = f"{code}{fmt}\n"
                fmtLines.append(newLine)

        headTextStr = "".join(headText)
        headLines.append(f"{pageIdent} {headTextStr}\n")
    sys.stderr.write("\n")
    print(f"{newLines} new lines in spans")

    # apply page corrections

    newTextLines = []
    newFmtLines = []

    def doPage(kind, pageNum, lines, dest):
        corrected = False
        pageCorrections = PAGE_CORRECTIONS.get(pageNum, {}).get(kind, ())
        if pageCorrections:
            page = "".join(lines)
            for (pattern, replacement) in pageCorrections:
                pos = page.find(pattern)
                if pos >= 0:
                    newPage = page.replace(pattern, replacement, 1)
                    PAGE_CORRECTIONS_APPLIED[pageNum][kind].add((pattern, replacement))
                    corrected = True
        dest.extend(
            [f"{line}\n" for line in newPage.split("\n")] if corrected else lines
        )

    for (kind, source, dest) in (
        ("text", textLines, newTextLines),
        ("fmt", fmtLines, newFmtLines),
    ):
        lines = []
        for line in source:
            if line.startswith("===="):
                doPage(kind, pageNum, lines, dest)
                lines = [line]
                pageNum = int(line[4:].split(" ", 1)[0].lstrip("0"))
            else:
                lines.append(line)
        doPage(kind, pageNum, lines, dest)

    textLines = newTextLines
    fmtLines = newFmtLines

    with open(TEXT_FILE, "w") as th:
        for line in textLines:
            th.write(line)
    with open(FMT_FILE, "w") as fh:
        for line in fmtLines:
            fh.write(line)
    with open(HEAD_FILE, "w") as hh:
        for line in headLines:
            hh.write(line)

    print("STYLE vs FLAGS")
    for ((st, fl), n) in sorted(styleFlags.items(), key=lambda x: (-x[1], x[0])):
        print(f"\t{st:<6} x {fl:<6} = {n:>5} x")

    print("SIZE vs FLAGS")
    for ((st, fl), n) in sorted(sizeFlags.items(), key=lambda x: (-x[1], x[0])):
        print(f"\t{st:<6} x {fl:<6} = {n:>5} x")

    print("XS")
    nXs = len(xS)
    for (k, n) in sorted(xS.items(), key=lambda x: (-x[1], x[0]))[0:10]:
        print(f"\t{k:<3} = {n:>5} x")
    if nXs > 10:
        print(f"\t... and {nXs - 10} more ...")

    print("YS")
    nYs = len(yS)
    for (k, n) in sorted(yS.items(), key=lambda x: (-x[1], x[0]))[0:10]:
        print(f"\t{k:<3} = {n:>5} x")
    if nYs > 10:
        print(f"\t... and {nYs - 10} more ...")

    for pattern in CORRECTIONS:
        if pattern not in CORRECTIONS_APPLIED:
            print(f"CORRECTION NOT APPLIED: `{pattern}`")
        else:
            applications = CORRECTIONS_APPLIED[pattern]
            nApps = len(applications)
            for (repl, pageNum, span) in applications:
                print(
                    f"CORRECTION APPLIED: `{pattern}` => "
                    f"`{repl}` to `{span}` on page {pageNum}"
                )
            if nApps > 1:
                print(
                    f"CORRECTION APPLIED MULTIPLE TIMES: `{pattern}` => "
                    f"`{repl}` {nApps}x"
                )

    for (pageNum, kindInfo) in PAGE_CORRECTIONS.items():
        for (kind, commands) in kindInfo.items():
            for command in commands:
                (pattern, replacement) = command
                pattern = pattern.replace("\n", "‣")
                replacement = replacement.replace("\n", "‣")
                if command in PAGE_CORRECTIONS_APPLIED[pageNum][kind]:
                    print(
                        "PAGE CORRECTION APPLIED: "
                        f"`{pattern}` to `{replacement}` on page {pageNum}"
                    )
                else:
                    print(
                        "PAGE CORRECTION NOT APPLIED: "
                        f"`{pattern}` to `{replacement}` on page {pageNum}"
                    )


def getStructure():
    with open(TEXT_FILE) as th:
        textLines = list(th)
    with open(FMT_FILE) as fh:
        fmtLines = list(fh)

    blankLines = []
    bracketLines = []
    dashLines = []
    fnBodyIndex = {}
    fnMarkIndex = {}
    fnBodies = []
    fnMarks = []
    titles = []
    structLines = []

    prevS = ""
    prevFnum = 0

    band = ""
    pageNum = ""
    filePageNum = ""

    titleRe = re.compile(r"""^([IVX]+)\.? ([A-Z0-9, -]+)(\.?)$""")
    titleContRe = re.compile(r"""^([A-Z0-9, -]+)(\.?)$""")

    folioLineRe = re.compile(
        r"""
        ^
        \s*
        (?:
            (?:VOC\s+[0-9]+\s*
            (?:\(Kol\.\s*Arch\.\s*[0-9]+\)\s*))?
            ,\s*
        )?
        [Ff]ol\.
        \s*
        (?:
            [0-9]+(?:bis|[AaBb])?
            |
            \(ongenummerd\)
            |
            ongepagineerd
            |
        )
        \s*
        [rv]?
        \s*
        (?:
            -
            (?:
                fol\.
                \s*
            )?
            [0-9]*(?:bis|[AaBb])?
            \s*
            [rv]?
        )?
        \.?
        \s*
        $
    """,
        re.X,
    )

    theTitleNum = ""
    curTitleNum = ""
    curTitleText = ""
    curDot = ""
    titleStart = -1

    curFnNum = 0
    curFnText = ""
    curGap = None
    fnStart = -1

    gaps = 0

    def finishTitle():
        nonlocal theTitleNum
        nonlocal curTitleNum
        nonlocal curTitleText
        nonlocal curDot
        nonlocal titleStart

        titles.append(
            (
                band,
                pageNum,
                filePageNum,
                titleStart,
                i,
                curTitleNum,
                curTitleText,
            )
        )
        theTitleNum = curTitleNum
        curTitleNum = ""
        curTitleText = ""
        curDot = ""
        titleStart = -1

    def finishFn():
        nonlocal curFnNum
        nonlocal curFnText
        nonlocal curGap
        nonlocal fnStart

        fnBodies.append(
            (
                band,
                pageNum,
                filePageNum,
                fnStart,
                i - 1,
                theTitleNum,
                curFnNum,
                curFnText,
                curGap,
            )
        )
        curFnNum = ""
        curFnText = ""
        curGap = None
        fnStart = -1

    def doNewLine(data, currentTextKind, force=False):
        fmtChanged = False
        textKind = currentTextKind
        if not force and st:
            textKind = "E" if st == "i" else "O"
            fmtChanged = True
            if "st" in data:
                del data["st"]
        unusualIndent = 0 < int(data.get("x", "0")) <= 50
        sameLine = data.get("y", None) == "0"
        if (textKind == "E" or not sameLine) and (ind == ">" or unusualIndent):
            lineKind = "P"
            if "in" in data:
                del data["in"]
                fmtChanged = True
            if "x" in data:
                del data["x"]
                fmtChanged = True
            if "y" in data:
                del data["y"]
                fmtChanged = True
        else:
            lineKind = "L"
        return (lineKind, textKind, fmtChanged)

    textKind = None
    inFnBody = False
    connect = False
    uncatchedFolios = []

    for (i, textLine) in enumerate(textLines):
        textLine = textLine.rstrip("\n")

        if textLine.startswith("=="):
            if fnStart >= 0:
                finishFn()
            inFnBody = False
            (pageNum, band, filePageNum) = textLine.split()
            pageNum = pageNum.lstrip("=")
            band = band.split("=")[1]
            filePageNum = filePageNum.lstrip("0")
            structLines.append(["==", pageNum, band, filePageNum])
            continue
        if textLine == "":
            continue

        maybeNewLine = textLine[0] == ">"
        textLine = textLine[2:]

        fmtLine = fmtLines[i][2:].rstrip("\n")

        match = titleRe.match(textLine)
        if match:
            curTitleNum = match.group(1)
            curTitleText = match.group(2)
            curDot = match.group(3)
            titleStart = i + 1
            prevFnum = 0
            structLines.append(["TI", curTitleNum, curDot, curTitleText])
            continue
        else:
            if titleStart >= 0:
                if curDot == ".":
                    finishTitle()
                else:
                    match = titleContRe.match(textLine)
                    if match:
                        thisTitleText = match.group(1)
                        curTitleText += f" {thisTitleText}"
                        curDot = match.group(2)
                        structLines.append(["TI", curTitleNum, curDot, thisTitleText])
                        continue
                    else:
                        finishTitle()

        match = folioLineRe.match(textLine)
        if match:
            structLines.append(["LE", "", f"<folio>{textLine}</folio>"])
            continue

        if (
            textLine.lower().startswith("fol.")
            and "is bij nummering overgeslagen" not in textLine
        ):
            uncatchedFolios.append((i, textLine))

        data = dict(item.split("=") for item in fmtLine.split(",") if item)

        y = data.get("y", None)
        if y is not None:
            y = int(y)
        s = data.get("s", "")
        indent = data.get("in", "")

        if prevS == "small" and s == "small" and indent == ">":
            if y == 0:
                fNum = textLines[i - 1][2:].rstrip()
                if fNum.isdigit():
                    structLines.pop()
                    if fnStart >= 0:
                        finishFn()
                    curFnNum = int(fNum)
                    curFnText = textLine
                    curGap = curFnNum != prevFnum + 1
                    fnStart = i - 1
                    prevFnum = curFnNum
                    structLines.append(["FB", curFnNum, curFnText])
                    prevS = s
                    inFnBody = True
                    continue
            else:
                if fnStart >= 0:
                    curFnText += textLine
                    structLines.append(["FB", curFnNum, textLine])
                    prevS = s
                    inFnBody = True
                    continue

        st = data.get("st", "")

        if inFnBody:
            if st == "i":
                thisText = f"<ref>{textLine}</ref>"
            else:
                thisText = textLine
            curFnText += thisText
            structLines.append(["FB", curFnNum, thisText])
            prevS = s
            continue

        if st in {"fn", "sup"}:
            fnNum = textLine.strip()
            if fnNum.isdigit():
                fnNum = int(fnNum)
                fnMarks.append((band, pageNum, filePageNum, i, theTitleNum, fnNum))
                structLines.append(["FM", fnNum])
                prevS = s
                continue

        fmtChanged = False
        forceTextKind = False
        textLineStripped = textLine.strip()

        if textLineStripped == "(":
            textKind = "E"
            forceTextKind = True

            if st != "i":
                bracketLines.append(i + 1)

            if "st" in data:
                del data["st"]
                fmtChanged = True
            if "x" in data:
                del data["x"]
                fmtChanged = True

        elif textLineStripped == "---":
            textKind = "O"
            forceTextKind = True

            if st != "n":
                dashLines.append(i + 1)

            if "st" in data:
                del data["st"]
                fmtChanged = True
            if "x" in data:
                del data["x"]
                fmtChanged = True

        elif textLineStripped in {".", ","}:
            connect = True
            if "st" in data:
                del data["st"]
                fmtChanged = True
            if "x" in data:
                del data["x"]
                fmtChanged = True

        ind = data.get("in", "")

        sameLine = data.get("y", None) == "0"
        # if sameLine:
        #    del data["y"]

        isNewLine = maybeNewLine and not sameLine
        if isNewLine:
            (lineKind, textKind, thisFmtChanged) = doNewLine(
                data, textKind, force=forceTextKind
            )
        else:
            lineKind = "S"
            thisFmtChanged = False
            blankLine = False
            if structLines:
                prevStructLine = structLines[-1]
                prevLabel = prevStructLine[0]
                prevLineKind = prevLabel[0]
                if prevLineKind in {"S", "L", "P"}:
                    prevTextLine = prevStructLine[-1]
                    prevLineStripped = prevTextLine.strip()
                    prevFmt = prevStructLine[1]
                    if prevLineStripped == "" and "y=0" not in prevFmt:
                        structLines.pop()
                        blankLines.append(i + 1)
                        blankLine = True
                        (lineKind, textKind, thisFmtChanged) = doNewLine(
                            data, textKind, force=forceTextKind
                        )
                    elif prevLineStripped in {"(", "---", ".", ","}:
                        prevStructLine[-1] += textLine
                        prevS = s
                        continue
                    elif connect:
                        prevStructLine[-1] += textLine
                        prevS = s
                        continue
            if not blankLine:
                if "st" in data and (
                    textKind == "E" and st == "i" or textKind == "O" and st == "n"
                ):
                    del data["st"]
                    thisFmtChanged = True
        label = f"{lineKind}{textKind}"
        if thisFmtChanged:
            fmtChanged = True

        if fmtChanged:
            fmtLine = ",".join(f"{k}={v}" for (k, v) in data.items())
        structLines.append([label, fmtLine, textLine])
        prevS = s
        connect = False

    if fnStart >= 0:
        finishFn()

    with open(TIT_FILE, "w") as th:
        for (band, pageNum, filePageNum, start, end, titleNum, titleText) in titles:
            th.write(
                f"{titleNum:<5} {titleText}\n"
                f"\t{pageNum:>4} band {band:<2} {filePageNum:>3} "
                f"lines {start:>5}-{end:>5}\n\n"
            )
    print(f"{len(titles)} titles")

    with open(FN_MARK_FILE, "w") as fh:
        for (
            i,
            (
                band,
                pageNum,
                filePageNum,
                line,
                tNum,
                fNum,
            ),
        ) in enumerate(fnMarks):
            entry = (
                f"{tNum:<5} [{fNum:>2}] {pageNum:>4} band {band:<2} {filePageNum:>3} "
                f"line {line + 1:>5}"
            )
            fh.write(f"{entry}\n")
            fnMarkIndex.setdefault(tNum, {}).setdefault(fNum, []).append(i)

    print(f"{len(fnMarks)} footnote marks")

    with open(FN_BODY_FILE, "w") as fh:
        gaps = 0
        for (
            i,
            (
                band,
                pageNum,
                filePageNum,
                start,
                end,
                tNum,
                fNum,
                fText,
                hasGap,
            ),
        ) in enumerate(fnBodies):
            gapBefore = "GAP BEFORE\n" if hasGap else ""
            entry = (
                f"{gapBefore}{tNum:<5} {pageNum:>4} band {band:<2} {filePageNum:>3} "
                f"lines {start + 1:>5}-{end + 1:>5}\n"
                f"\t{fNum}. {fText}\n"
            )
            if hasGap:
                gaps += 1
                print(entry)
            fh.write(f"{entry}\n")
            fnBodyIndex.setdefault(tNum, {}).setdefault(fNum, []).append(i)

    # Join words that are hyphenated around a new line
    # and join folio references

    with open(STRUCT_FILE, "w") as fh:
        for row in structLines:
            fh.write(("\t".join(str(c) for c in row)) + "\n")

    print(f"{len(fnBodies)} footnote bodies with {gaps} gaps")

    print("CHECKING CONSISTENCY FOOTNOTE BODIES AND MARKS:")

    ok = True
    for (tNum, fnInfo) in sorted(fnBodyIndex.items()):
        for (fNum, iis) in sorted(fnInfo.items()):
            if len(iis) > 1:
                print(f"MULTIPLE FOOTNOTE BODIES in {tNum} for [{fNum}]: {len(iis)}x")
                ok = False
            if fNum not in fnMarkIndex.get(tNum, {}):
                entry = fnBodies[iis[0]]
                (band, pageNum, filePageNum) = entry[0:3]
                ident = f"{pageNum:>04} file={band} {filePageNum:>04}"
                print(f"FOOTNOTE BODY in {tNum} not referenced: [{fNum}] ({ident})")
                ok = False

    for (tNum, fnInfo) in sorted(fnMarkIndex.items()):
        for (fNum, iis) in sorted(fnInfo.items()):
            if len(iis) > 1:
                print(f"MULTIPLE FOOTNOTE MARKS in {tNum} for [{fNum}]: {len(iis)}x")
                ok = False
            if fNum not in fnBodyIndex.get(tNum, {}):
                entry = fnMarks[iis[0]]
                (band, pageNum, filePageNum) = entry[0:3]
                ident = f"{pageNum:>04} file={band} {filePageNum:>04}"
                print(f"FOOTNOTE MARK in {tNum} has no body: [{fNum}] ({ident})")
                ok = False
    if ok:
        print("\tCONSISTENT")
    print(f"BLANK LINES: {len(blankLines)} x")
    if blankLines:
        print(", ".join(str(b) for b in blankLines[0:5]))
    print(f"BRACKET LINES: {len(bracketLines)} x")
    if bracketLines:
        print(", ".join(str(b) for b in bracketLines))
    print(f"DASHED LINES: {len(dashLines)} x")
    if dashLines:
        print(", ".join(str(b) for b in dashLines))
    print(f"FOLIO REFS (uncatched): {len(uncatchedFolios)}")
    for (i, text) in uncatchedFolios:
        print(f"{i:>5} `{text}`")


def sections(sourceLines):
    nStruct = len(sourceLines)
    newSourceLines = []
    nSections = collections.Counter()

    for (i, item) in enumerate(sourceLines[0:-1]):
        (code, *data) = item
        if code == "LO":
            fmtStr = data[0]
            fmt = dict(item.split("=") for item in fmtStr.split(",") if item)
            y = fmt.get("y", None)
            if y is not None and int(y) >= 22:
                j = i + 1
                nextItem = sourceLines[j]
                (nextCode, *nextData) = nextItem
                while j < nStruct and nextCode in CODES_SKIP:
                    j += 1
                    nextItem = sourceLines[j]
                    (nextCode, *nextData) = nextItem

                if nextCode[0] == "P" or "<folio>" in nextData[-1]:
                    newCode = "HD"
                    del fmt["y"]
                    newFmt = ",".join(f"{k}={v}" for (k, v) in fmt.items() if k != "st")
                    section = ucFirst(data[-1])
                    nSections[section] += 1
                    data[-1] = section
                    newSourceLines.append([newCode, newFmt, *data[1:]])
                    continue

        newSourceLines.append(item)

    sourceLines.clear()
    sourceLines.extend(newSourceLines)

    # We may have failed to detect sections: looking for isolated LO-s.

    newSourceLines = []

    prevKind = None
    probableHeadings = []

    for (i, item) in enumerate(sourceLines[0:-1]):
        (code, *data) = item
        inEditorial = prevKind == "E"
        curKind = code[1]
        if curKind != prevKind and curKind in {"E", "O"}:
            prevKind = curKind

        if inEditorial and code == "LO":
            j = i + 1
            nextItem = sourceLines[j]
            (nextCode, *nextData) = nextItem
            while j < nStruct and nextCode in CODES_SKIP:
                j += 1
                nextItem = sourceLines[j]
                (nextCode, *nextData) = nextItem

            nextKind = nextCode[1]
            if nextKind == "E":
                section = ucFirst(data[-1])
                nSections[section] += 1
                probableHeadings.append((i, section))
                newSourceLines.append(["HD", "", section])
                continue

        newSourceLines.append(item)

    sourceLines.clear()
    sourceLines.extend(newSourceLines)

    print("SECTIONS:")
    for (section, amount) in sorted(nSections.items(), key=lambda x: (-x[1], x[0])):
        print(f"{amount:>3}x {section}")

    print(f"CORRECTED MISSED SECTIONS: {len(probableHeadings)}x")
    for (i, text) in probableHeadings:
        print(f"{i:>5} `{text}`")


def glue(sourceLines):
    folioInlinePre = re.compile(
        r"""
        ^
        (.*?)
        (
            \[
            \s*
            fol\.
            [^]]*
        )
        $
        """,
        re.X | re.I | re.M,
    )

    wordPrev = re.compile(
        rf"""
        ^
        (.*?)
        ({WORD_CHARS}+)
        -
        $
        """,
        re.X | re.M | re.I,
    )

    nStruct = len(sourceLines)
    newSourceLines = []
    passCodes = {"==", "FM", "HD"}

    for (i, item) in enumerate(sourceLines[0:-1]):
        (code, *data) = item
        if code in passCodes:
            newSourceLines.append(item)
            continue

        j = i + 1
        nextItem = sourceLines[j]
        (nextCode, *nextData) = nextItem
        while j < nStruct and nextCode in CODES_SKIP:
            j += 1
            nextItem = sourceLines[j]
            (nextCode, *nextData) = nextItem
        if nextCode in passCodes:
            newSourceLines.append(item)
            continue

        text = data[-1]
        matchPre = folioInlinePre.search(text)
        if matchPre:
            (before, broken) = matchPre.group(1, 2)
            newText = before
            newSourceLines.append([code, *data[0:-1], newText])
            nextItem[-1] = broken + nextItem[-1]
            continue

        if text.endswith("-"):
            matchPre = wordPrev.match(text)
            if matchPre:
                (before, broken) = matchPre.group(1, 2)
                newText = before
                newSourceLines.append([code, *data[0:-1], newText])
                nextItem[-1] = broken + nextItem[-1]
                continue

        newSourceLines.append(item)

    sourceLines.clear()
    sourceLines.extend(newSourceLines)

    for item in sourceLines:
        (code, *data) = item
        if code == "TI":
            textLine = data[-1]
            curDot = data[-2]
            item[-2:] = [f"{textLine}{curDot}"]


def folios(sourceLines):
    folioInlineRe = re.compile(
        r"""
        \[
        \s*
        (
            (?:
                [fF]ol\.
                \s*
                [0-9]+[rv]?
                \s*
                (?:
                    -[0-9]*[rv]?
                )?
            )
            |
            (?:
                ongenummerd folio
            )
        )
        \s*
        \]
    """,
        re.X,
    )

    newSourceLines = []

    nFolios = 0

    for item in sourceLines:
        (code, *fields) = item

        if code != "==":
            text = fields[-1]
            (newText, n) = folioInlineRe.subn(r"<folio>\1</folio>", text)
            if n:
                newSourceLines.append([code, *fields[0:-1], newText])
                nFolios += n
                continue

        newSourceLines.append(item)

    print(f"FOLIO REFS (inline): {nFolios}x")
    sourceLines.clear()
    sourceLines.extend(newSourceLines)


def parseFrac(frac):
    parts = frac.split("/")

    if len(parts) == 1:
        part = parts[0]
        nDigits = len(part)
        hDigits = int(round(nDigits // 2))
        num = part[0:hDigits]
        den = part[hDigits:]
    else:
        num = "".join(parts[0:-1])
        den = parts[-1]
        if num == "":
            num = "1"
        if den == "":
            den = "1"

    if not num.isdigit() or not den.isdigit():
        return None

    if len(num) == 4 and num.startswith("17"):
        return None

    while len(num) > 1 and den[0] == "0" or int(num) > int(den):
        den = num[-1] + den
        num = num[0:-1]

    if int(num) < int(den):
        return (num, den)

    return None


def getSymSups(sourceLines):
    fracRe = re.compile(
        r"""
        ^
        ([0-9]+)
        /
        ([0-9]+)
        ([.,;:]?\s*)
        $
    """,
        re.X | re.M,
    )
    fracInRe = re.compile(
        r"""
        [0-9]+
        /
        [0-9]+
    """,
        re.X | re.M,
    )

    remFracs = {}

    def fracInRepl(match):

        fracStr = match.group(0)
        result = parseFrac(fracStr)
        if result is None:
            return fracStr
        else:
            (num, den) = result
            remFracs[fracStr] = f"{num}/{den}"
            return f"<q><num>{num}</num>/<den>{den}</den></q>"

    KNOWN_SYMS = {"'"}
    KNOWN_SUPS = {"e", "rm", "de", "sten", "ra", "t", "a", "s"}
    IGNORED_SUPS = {"}", "in een kas"}
    KNOWN_FRACS = {
        "4": ("3", "4"),
        "ver4/5": ("4", "5"),
    }

    # first double fractions like:
    # SO	x=18,f=sym	1/ 4 3/ 5
    # LO	x=18,y=0,f=sym	1536
    #
    # triggered by: second f=sym has y=0 and same x as previous
    # slashes in the numerator can be ignored

    stats = dict(
        code=("CODES", collections.Counter()),
        totalSup=("TOTAL SUP", collections.Counter()),
        knownSup=("KNOWN SUP", collections.Counter()),
        ignoredSup=("IGNORED SUP", collections.Counter()),
        nonSup=("WRONG SUP", collections.Counter()),
        totalSym=("TOTAL SYM", collections.Counter()),
        knownSym=("KNOWN SYM", collections.Counter()),
        nonSym=("WRONG SYM", collections.Counter()),
        totalFrac=("TOTAL FRAC", collections.Counter()),
        knownFrac=("KNOWN FRAC", collections.Counter()),
        doubleFrac=("DOUBLE FRAC", collections.Counter()),
        pureFrac=("PURE FRAC", collections.Counter()),
        computedFrac=("COMPUTED FRAC", collections.Counter()),
        remainingFrac=("REMAINING FRAC", collections.Counter()),
    )

    newSourceLines = []
    skipNext = False

    for (i, item) in enumerate(sourceLines):
        if skipNext:
            skipNext = False
            continue

        (code, *fields) = item
        if code != "==":
            fmtStr = fields[0]
            if "f=sym" in fmtStr:
                fmt = dict(item.split("=") for item in fmtStr.split(",") if item)
                nextItem = sourceLines[i + 1]
                (nextCode, *nextFields) = nextItem
                if nextCode != "==":
                    nextFmtStr = nextFields[0]
                    if "f=sym" in nextFmtStr:
                        nextFmt = dict(
                            item.split("=") for item in nextFmtStr.split(",") if item
                        )
                        nextY = nextFmt.get("y", None)
                        if nextY in {"0", None}:
                            x = fmt.get("x", None)
                            nextX = nextFmt.get("x", None)
                            if x is not None and nextX is not None and x == nextX:
                                text = fields[-1]
                                num = text.replace(" ", "").replace("/", "")
                                if num.isdigit():
                                    nextText = nextFields[-1]
                                    den = nextText.strip()
                                    if den.isdigit():
                                        prevItem = sourceLines[i - 1]
                                        prevItem[
                                            -1
                                        ] += f"<q><num>{num}</num>/<den>{den}</den></q>"
                                        skipNext = True
                                        stats["totalFrac"][1][text] += 1
                                        stats["doubleFrac"][1][
                                            f"{text} + {nextText} = {num}/{den}"
                                        ] += 1
                                        continue
        newSourceLines.append(item)

    sourceLines.clear()
    sourceLines.extend(newSourceLines)

    newSourceLines = []
    skipNext = False

    for (i, item) in enumerate(sourceLines):
        if skipNext:
            skipNext = False
            continue

        (code, *fields) = item

        if code != "==":
            fmt = fields[0]
            isSym = "f=sym" in fmt
            isSup = "st=sup" in fmt or "st=fn" in fmt

            if isSup or isSym:
                stats["code"][1][code] += 1
                text = fields[-1]

                parts = text.split("<", 1)
                if len(parts) == 1:
                    signPart = parts[0]
                    markup = ""
                else:
                    (signPart, markup) = parts
                    markup = "<" + markup
                bareSign = signPart.replace(" ", "")

                ok = False

                if isSup:
                    bareSup = text.strip()
                    if bareSup in KNOWN_SUPS:
                        spaceBefore = " " if text.startswith(" ") else ""
                        spaceAfter = " " if text.endswith(" ") else ""
                        stats["totalSup"][1][bareSup] += 1
                        stats["knownSup"][1][bareSup] += 1
                        attachItem = newSourceLines[-1]
                        attachText = (
                            f"{spaceBefore}<super>{bareSup}</super>{spaceAfter}"
                        )
                        ok = True
                    elif bareSup in IGNORED_SUPS:
                        stats["totalSup"][1][text] += 1
                        stats["ignoredSup"][1][text] += 1
                        attachItem = newSourceLines[-1]
                        attachText = text
                        ok = True
                    else:
                        stats["totalSup"][1][text] += 1
                        stats["nonSup"][1][text] += 1

                elif isSym:
                    if bareSign in KNOWN_SYMS:
                        stats["totalSym"][1][text] += 1
                        stats["knownSym"][1][text] += 1
                        attachItem = newSourceLines[-1]
                        attachText = text
                        ok = True
                    else:
                        fracOk = False
                        match = fracRe.match(bareSign)
                        if match:
                            stats["pureFrac"][1][text] += 1
                            (numerator, denominator, rest) = match.group(1, 2, 3)
                            fracOk = True
                        else:
                            rest = ""
                            result = parseFrac(bareSign)
                            if result is not None:
                                (numerator, denominator) = result
                                stats["computedFrac"][1][
                                    f"{text:<20} => {numerator}/{denominator}"
                                ] += 1
                                fracOk = True
                            elif bareSign in KNOWN_FRACS:
                                (numerator, denominator) = KNOWN_FRACS[bareSign]
                                stats["knownFrac"][1][
                                    f"{text} => {numerator}/{denominator}"
                                ] += 1
                                fracOk = True

                        if fracOk:
                            stats["totalFrac"][1][text] += 1
                            attachItem = newSourceLines[-1]
                            attachText = (
                                f"<q><num>{numerator}</num>/"
                                f"<den>{denominator}</den></q>{markup}{rest}"
                            )
                            ok = True
                        else:
                            stats["totalSym"][1][text] += 1
                            stats["nonSym"][1][text] += 1

                if ok:
                    if code[0] == "S":
                        attachItem[-1] += attachText
                    else:
                        item[-1] = attachText
                        fmtStr = item[1]
                        fmt = dict(
                            item.split("=") for item in fmtStr.split(",") if item
                        )
                        for key in ("f", "s"):
                            if key in fmt:
                                del fmt[key]
                        item[1] = ",".join(f"{k}={v}" for (k, v) in fmt.items())
                        newSourceLines.append(item)
                        attachItem = newSourceLines[-1]

                    nextItem = sourceLines[i + 1]
                    (nextCode, *nextFields) = nextItem
                    if nextCode[0] == "S":
                        nextFmtStr = nextFields[0]
                        fmt = dict(
                            item.split("=") for item in nextFmtStr.split(",") if item
                        )
                        fmtKeys = list(fmt)
                        if len(fmtKeys) == 1 and fmtKeys[0] == "x":
                            attachItem[-1] += nextFields[-1]
                            skipNext = True
                    continue

        newSourceLines.append(item)

    sourceLines.clear()
    sourceLines.extend(newSourceLines)

    newSourceLines = []

    for (i, item) in enumerate(sourceLines):
        (code, *fields) = item

        if code != "==":
            text = fields[-1]
            remFracs.clear()
            # newText = fracInRe.sub(fracInRepl, text)
            if len(remFracs):
                for (fracStr, repl) in remFracs.items():
                    stats["remainingFrac"][1][f"{fracStr} => {repl}"] += 1
                # item[-1] = newText

        newSourceLines.append(item)

    sourceLines.clear()
    sourceLines.extend(newSourceLines)

    print("SUPS, SYMBOLS, FRACTIONS")
    for key in stats:
        (label, diags) = stats[key]
        if key.startswith("total"):
            continue
        if len(diags):
            print(f"{label}:")
            for (sign, n) in sorted(diags.items(), key=lambda x: (-x[1], x[0])):
                print(f"\t{n:>5}x `{sign}`")
        else:
            print(f"{label}: None")
    for key in stats:
        (label, diags) = stats[key]
        distinct = len(diags)
        distinctPl = " " if distinct == 1 else "s"
        amount = sum(diags.values())
        amountPl = " " if amount == 1 else "s"
        print(
            f"{label:<15}: {distinct:>4} value{distinctPl} in "
            f"{amount:>5} occurrence{amountPl}"
        )


def refs(sourceLines):
    newSourceLines = []

    nTweaks = 0
    nEmphasis = 0

    doEmph = False
    makeE = False

    for (i, item) in enumerate(sourceLines[0:-2]):
        (code, *fields) = item

        if code == "SE":
            nextItem = sourceLines[i + 1]
            (nextCode, *nextFields) = nextItem
            if nextCode == "LO":
                nnextItem = sourceLines[i + 2]
                (nnextCode, *nnextFields) = nnextItem
                if nnextCode == "SO":
                    doEmph = True
                    nTweaks += 1
                    continue

        if doEmph:
            newSourceLines.append(["LE", "", f"<ref>{fields[-1]}</ref>"])
            makeE = True
            doEmph = False
            continue

        if makeE:
            newSourceLines.append(["LE", "", fields[-1]])
            makeE = False
            continue

        textKind = code[-1]
        fmt = fields[0]
        if textKind == "E" and "st=n" in fmt or textKind == "O" and "st=i" in fmt:
            newSourceLines.append([code, "", f"<ref>{fields[-1]}</ref>"])
            nEmphasis += 1
            continue

        newSourceLines.append(item)

    print(f"TWEAKS (SE-LO-SO): {nTweaks}x")
    print(f"EMPHASIS: {nEmphasis}x")

    sourceLines.clear()
    sourceLines.extend(newSourceLines)


def xyCleanup(sourceLines):
    if False:
        newSourceLines = []

        nTweaks = 0

        for item in sourceLines:
            (code, *fields) = item
            if code not in CODES_NO_FMT:
                fmtStr = fields[0]
                fmt = dict(f.split("=") for f in fmtStr.split(",") if f)

                # remove superfluous x= and in= keys
                # superfluous is now: if not used for table columns
                # and the criterion is: y=0 is not present

                if code == "SE" or (
                    "y=0" not in fmtStr and ("x" in fmtStr or "in" in fmtStr)
                ):
                    prevLine = newSourceLines[-1]
                    prevCode = prevLine[0]
                    if prevCode not in CODES_SKIP:
                        newSourceLines[-1][-1] += f" {fields[-1]}"
                        nTweaks += 1
                        continue

            newSourceLines.append(item)

        print(f"TWEAKS (remove x=): {nTweaks}x")

        sourceLines.clear()
        sourceLines.extend(newSourceLines)

    newSourceLines = []
    indentValue = 0

    for item in sourceLines:

        # change back ln= values to x= values

        (code, *fields) = item
        if code == "==":
            pageNum = int(fields[0].lstrip("0"))
            xInfo = XS[pageNum % 2]
            xStart = xInfo["start"]
            xIndent = xInfo["indent"]
            indentValue = xIndent - xStart

        if code not in CODES_NO_FMT:
            fmtStr = fields[0]
            fmt = dict(f.split("=") for f in fmtStr.split(",") if f)

            fmtChanged = False

            key = "in"
            if key in fmt:
                fmt["x"] = indentValue
                del fmt[key]
                fmtChanged = True

            # remove all y= keys from the format
            key = "y"
            if key in fmt:
                del fmt[key]
                fmtChanged = True

            if fmtChanged:
                fmtStr = ",".join(f"{k}={v}" for (k, v) in fmt.items())
                item = [code, fmtStr, *fields[1:]]

        newSourceLines.append(item)

    sourceLines.clear()
    sourceLines.extend(newSourceLines)

    newSourceLines = []

    prevCode = False
    prevText = None

    nTweaks = []

    for item in sourceLines:
        (code, *fields) = item

        # remove x=... in list items

        if code[0] in {"L", "P"}:
            prevCode = True
            prevText = fields[-1]
        elif code in {"==", "TI", "HD"}:
            prevCode = False
            prevText = None

        if code[0] == "S":
            if prevCode:
                prevText = prevText.strip()
                fmtStr = fields[0]
                if (
                    fmtStr == ""
                    or "x=" in fmtStr
                    and prevText.endswith(".")
                    and prevText[0:-1].rstrip().isdigit()
                ):
                    text = f" {fields[-1]}"
                    newSourceLines[-1][-1] += text
                    nTweaks.append(
                        (len(newSourceLines), f"{prevCode} {prevText}{text}")
                    )
                    continue

        newSourceLines.append(item)

    sourceLines.clear()
    sourceLines.extend(newSourceLines)

    print(f"TWEAKED LIST ITEMS: {len(nTweaks)}x")
    for (i, text) in nTweaks[0:10]:
        print(f"{i:>5} {text}")

    newSourceLines = []

    noXbefore = 0

    nTweaks = []

    for (i, item) in enumerate(sourceLines[0:-4]):
        (code, *fields) = item

        # remove isolated x=...
        # i.e. those that have at least 2 non x= lines before and 4 such lines after
        # and whose x value is less than 70.

        fmtStr = fields[0]
        currentNoXbefore = noXbefore
        hasX = "x=" in fmtStr
        if hasX:
            noXbefore = 0
        else:
            noXbefore += 1

        if hasX and code[0] in {"L", "S"}:
            x = int(fmtStr[2:])
            if (x < 70 or x == 180 or x > 300) and currentNoXbefore >= 2:
                if all("x=" not in sourceLines[i + 1 + j][1] for j in range(4)):
                    text = fields[-1]
                    if code[0] == "L":
                        newSourceLines.append([code, "", text])
                    else:
                        newSourceLines[-1][-1] += f" {text}"
                    nTweaks.append((len(newSourceLines), f"{x=} {code} {text}"))
                    continue

        newSourceLines.append(item)

    sourceLines.clear()
    sourceLines.extend(newSourceLines)

    print(f"REMOVED ISOLATED X=: {len(nTweaks)}x")
    for (i, text) in nTweaks[0:10]:
        print(f"{i:>5} {text}")


def tables(sourceLines):
    MAX_X_LESS = 6

    newSourceLines = []

    tableInfo = []

    lastX = -MAX_X_LESS - 1

    nLines = len(sourceLines)

    curTable = None

    workTable = []

    def mapStops(tabStops):
        positions = []
        positionMap = {}

        for (r, row) in enumerate(tabStops):
            for stop in row:
                mapped = False
                p = -1
                for (p, pos) in enumerate(positions):
                    if pos < stop:
                        continue
                    if pos == stop:
                        positionMap[(r, stop)] = stop
                        mapped = True
                        break
                    positions[p:p] = [stop]
                    positionMap[(r, stop)] = stop
                    mapped = True
                    break
                if not mapped:
                    positions.append(stop)
                    positionMap[(r, stop)] = stop

        positionRank = {pos: p + 1 for (p, pos) in enumerate(positions)}
        columnMap = {
            (r, stop): positionRank[pos] for ((r, stop), pos) in positionMap.items()
        }

        return (positions, columnMap)

    def computeTable(i):
        tabStops = []

        for item in workTable:
            (code, *fields) = item
            if code in CODES_SKIP or code == "RE":
                continue
            if code == "RB":
                tabStops.append([])
            else:
                x = fields[0]
                tabStops[-1].append(x)

        (positions, columnMap) = mapStops(tabStops)

        r = -1
        for item in workTable:
            (code, *fields) = item
            if code in CODES_SKIP or code == "RE":
                continue
            if code == "RB":
                r += 1
                item[-1] = ", ".join(f"{columnMap[(r, x)]}:{x}" for x in tabStops[r])
            else:
                x = fields[0]
                item[1] = f"c={columnMap[(r, x)]},x={x}"
        return (positions, tabStops)

    def processRow(r, material):
        workTable.append(["RB", f"r={r}", ""])

        for item in material:
            workTable.append(item)

        workTable.append(["RE", f"r={r}", ""])

    def processTable(i, material):
        tableInfo.append(material)
        workTable.clear()

        curRow = []
        r = 0

        for item in material:
            (code, *fields) = item
            if code in CODES_SKIP:
                curRow.append(item)
            else:
                mayHaveX = code not in CODES_NO_FMT
                fmtStr = fields[0]
                x = int(fmtStr[2:]) if mayHaveX and "x=" in fmtStr else 0
                newItem = [code, x, fields[-1]]

                newItem[0] = "TC"
                if code[0] == "S":
                    curRow.append(newItem)
                else:
                    if len(curRow):
                        processRow(r, curRow)
                    r += 1
                    curRow = [newItem]
        if len(curRow):
            processRow(r, curRow)

        (positions, tabStops) = computeTable(i)
        nTables = len(tableInfo) + RESUME_TABLE
        nRows = len(tabStops)
        nCols = len(positions)

        newSourceLines.append(["TB", f"t={nTables}", f"rows={nRows},cols={nCols}"])
        newSourceLines.extend(workTable)
        newSourceLines.append(["TE", f"t={nTables}", ""])

    def doTable(i):
        nTail = i - 1 - lastX
        nReal = None if nTail == 0 else -nTail
        nRest = len(curTable) - nTail
        realTable = curTable[0:nReal]
        restTable = curTable[nRest:]
        if len(realTable) + len(restTable) != len(curTable) or len(realTable) == 0:
            print(
                "TABLE ERROR: "
                f"{len(curTable)=} {nTail=} {len(realTable)=} {len(restTable)=}"
            )
        processTable(i, realTable)
        newSourceLines.extend(restTable)

    for (i, item) in enumerate(sourceLines):
        (code, *fields) = item
        allowedInTable = code not in CODES_OUT_TABLE
        mayHaveX = code not in CODES_NO_FMT
        fmtStr = fields[0]
        x = int(fmtStr[2:]) if mayHaveX and "x=" in fmtStr else None
        if x is not None:
            lastX = i

        nextX = None

        j = i + 1
        if j < nLines:
            nextItem = sourceLines[j]
            (nextCode, *nextFields) = nextItem
            while j < nLines and nextCode in CODES_SKIP:
                j += 1
                nextItem = sourceLines[j]
                (nextCode, *nextFields) = nextItem
            nextMayHaveX = nextCode not in CODES_NO_FMT
            nextFmtStr = nextFields[0]
            nextX = int(nextFmtStr[2:]) if nextMayHaveX and "x=" in nextFmtStr else None

        inTable = allowedInTable and (
            x is not None
            or nextX is not None
            or (curTable is not None and i - lastX < MAX_X_LESS)
        )

        if inTable:
            if curTable is None:
                curTable = [item]
            else:
                curTable.append(item)
            continue
        else:
            if curTable is not None:
                doTable(i)
                curTable = None

        newSourceLines.append(item)

    if curTable is not None:
        doTable(i + 1)
        curTable = None

    print(f"TABLES: {len(tableInfo)}x")

    sourceLines.clear()
    sourceLines.extend(newSourceLines)


def footnotes(sourceLines):
    pageNum = None
    footnoteBodies = collections.defaultdict(
        lambda: collections.defaultdict(lambda: "")
    )

    for (i, item) in enumerate(sourceLines[0:-2]):
        (code, *fields) = item
        if code == "==":
            pageNum = int(fields[0].lstrip("0"))

        elif code == "FB":
            fNum = fields[0]
            text = fields[-1]
            footnoteBodies[pageNum][fNum] += text

    newSourceLines = []
    pageNum = None

    footnoteRefs = collections.defaultdict(set)

    FOOTNOTE_RE = re.compile(r"<note>([0-9]+)</note>")

    def footnoteRepl(match):
        fNum = match.group(1)
        if fNum in footnoteRefs[pageNum]:
            print(f"ERROR: duplicate footnote {fNum} on page {pageNum}")
        else:
            footnoteRefs[pageNum].add(fNum)
        if fNum not in footnoteBodies[pageNum]:
            print(f"ERROR: no footnote body for {fNum} on page {pageNum}")
            fText = ""
        else:
            fText = footnoteBodies[pageNum][fNum]
        return f"""<note mark="{fNum}">{fText}</note>"""

    for (i, item) in enumerate(sourceLines[0:-2]):
        (code, *fields) = item

        if code == "==":
            pageNum = int(fields[0].lstrip("0"))

        if code == "FB":
            continue

        text = fields[-1]
        (newText, n) = FOOTNOTE_RE.subn(footnoteRepl, text)
        if n:
            item[-1] = newText
            newSourceLines.append(item)
            continue

        newSourceLines.append(item)

    print(
        f"FOOTNOTEBODIES: {sum(len(perPage) for perPage in footnoteBodies.values())}x"
    )
    print(f"FOOTNOTEREFS:   {sum(len(perPage) for perPage in footnoteRefs.values())}x")

    sourceLines.clear()
    sourceLines.extend(newSourceLines)


def cleanSpans(sourceLines):
    newSourceLines = []

    nCleans = 0

    for item in sourceLines:
        (code, *fields) = item
        if code == "SE":
            newSourceLines[-1][-1] += f" {fields[-1]}"
            nCleans += 1
            continue

        fmtStr = fields[0]
        text = fields[-1]

        if code == "LE":
            textBare = text.lstrip()
            if "x=" in fmtStr or textBare.startswith("("):
                item[0] = "PE"
                item[1] = ""
                item[-1] = textBare

        newSourceLines.append(item)

    print(f"CLEANED SPANS: {nCleans}x")

    sourceLines.clear()
    sourceLines.extend(newSourceLines)


def getFineStructure():
    fineLines = []
    wrongCodes = collections.Counter()

    with open(STRUCT_FILE) as fh:
        structLines = list(fh)
        seenFm = False

        for (i, line) in enumerate(structLines):
            (code, *fields) = line.rstrip("\n").split("\t")

            if seenFm:
                seenFm = False
                if code not in CODES_NO_FMT:
                    if code in CODES_SPAN:
                        prev = fineLines[-1]
                        prev[-1] += fields[-1]
                        continue
                    else:
                        fmtStr = fields[0]
                        fmt = dict(
                            item.split("=") for item in fmtStr.split(",") if item
                        )
                        if "x" in fmt:
                            del fmt["x"]
                        fields[0] = ",".join(f"{k}={v}" for (k, v) in fmt.items())

            if code not in CODES:
                fineLines.append(["XX", *fields])
                wrongCodes[code] += 1
                continue

            if code == "FM":
                numRep = f"<note>{fields[0]}</note>"
                prev = fineLines[-1]
                prev[-1] += numRep
                seenFm = True
                continue

            fineLines.append([code, *fields])

    if len(wrongCodes) > 0:
        print("ERROR: wrong codes:")
        for (code, n) in sorted(wrongCodes.items(), key=lambda x: (-x[1], x[0])):
            print(f"\t{n:>5}x {code}")

    else:
        print("All codes correct")

    glue(fineLines)
    chars(fineLines)
    folios(fineLines)
    sections(fineLines)
    getSymSups(fineLines)
    refs(fineLines)
    xyCleanup(fineLines)
    tables(fineLines)
    footnotes(fineLines)
    cleanSpans(fineLines)

    with open(FINE_FILE, "w") as fh:
        for row in fineLines:
            fh.write(("\t".join(str(c) for c in row)) + "\n")


def getXml():
    with open(FINE_FILE) as fh:
        fineLines = list(fh)

    footnoteRe = re.compile(r"""<note.*?</note>""")

    targetDir = f"{XML_DIR}/{PDF_VOL}"
    initTree(targetDir, fresh=True)
    inTitle = False
    title = []
    meta = []
    body = []
    pageNum = None
    letterPageNum = None
    seq = None
    pendingPageBreak = None
    inRemark = False
    inParaO = False
    nTable = None
    nRow = None

    metadata = dict(
        author=collections.Counter(),
        place=collections.Counter(),
        date=collections.Counter(),
    )

    def finishLetter():
        nonlocal inRemark

        if len(meta):
            fh = open(f"{targetDir}/{letterPageNum}.xml", "w")
            fh.write("".join(meta))
            if inRemark:
                body.append("</remark>\n")
                inRemark = False
            if inParaO:
                body.append("</para>\n")
            body.append("</body>\n</teiTrim>\n")
            fh.write("".join(body))
            fh.close()

    def startLetter():
        title.clear()
        meta.clear()
        meta.append("""<teiTrim>\n<header>\n""")
        body.clear()
        body.append("""<body>\n""")

    noName = set(
        """
        van
        der
        de
    """.strip().split()
    )

    months = """
        januari
        februari
        maart
        april
        mei
        juni
        juli
        augustus
        september
        oktober
        november
        december
    """.strip().split()

    monthIndex = {month: i + 1 for (i, month) in enumerate(months)}

    def capName(name, first, short):
        return (
            name
            if name in noName and not (short and first)
            else (name[0].upper() + name[1:])
        )

    def formatAuthor(authorStr, short=False):
        names = [auth.lower() for auth in authorStr.split()]
        if short:
            inter = [nm for nm in names if nm in noName]
            inter.append(names[-1])
            names = inter
        return " ".join(
            capName(name.lower(), i == 0, short) for (i, name) in enumerate(names)
        )

    def distill():

        titleStr = "".join(title).replace("\n", " ").strip()
        (authorStr, placeDate) = titleStr.rsplit(",", 1)
        authors = authorStr.split(",")
        if " EN " in authors[-1]:
            lastAuthors = authors[-1].split(" EN ")
        authors[-1:] = lastAuthors

        for auth in authors:
            metadata["author"][formatAuthor(auth)] += 1

        author = ", ".join(formatAuthor(auth, short=True) for auth in authors)
        authorFull = ", ".join(formatAuthor(auth) for auth in authors)

        placeDate = placeDate.strip().rstrip(".").rstrip()
        (place, rawdate) = placeDate.split(" ", 1)

        place = place[0].upper() + place[1:].lower()
        metadata["place"][place] += 1
        rawdate = rawdate.lower()
        metadata["date"][rawdate] += 1
        (day, month, year) = rawdate.split(" ")
        month = monthIndex[month]

        meta.append(f"""<meta key="page" value="{letterPageNum}"/>\n""")
        meta.append(f"""<meta key="title" value="{author}; {place}, {rawdate}"/>\n""")
        meta.append(f"""<meta key="rawdate" value="{rawdate}"/>\n""")
        meta.append(f"""<meta key="seq" value="{seq}"/>\n""")
        meta.append(f"""<meta key="place" value="{place}"/>\n""")
        meta.append(f"""<meta key="year" value="{year}"/>\n""")
        meta.append(f"""<meta key="month" value="{month}"/>\n""")
        meta.append(f"""<meta key="day" value="{day}"/>\n""")
        meta.append(f"""<meta key="author" value="{author}"/>\n""")
        meta.append("""<meta key="pid" value=""/>\n""")
        meta.append("""<meta key="status" value=""/>\n""")
        meta.append(f"""<meta key="authorFull" value="{authorFull}"/>\n""")
        meta.append("""</header>\n""")

    for (i, line) in enumerate(fineLines):
        (code, *fields) = line.rstrip("\n").split("\t")
        if code == "==":
            pageNum = fields[0]
            band = fields[1]
            bandRep = "1" if band == "i" else "2"
            weblink = (
                f"""/#page={int(pageNum) + BAND_OFFSET[bandRep]}"""
                f"""&amp;source={PDF_VOL}_{bandRep}"""
            )
            pendingPageBreak = (
                f"""<pb n="{pageNum}" vol="{PDF_VOL}" weblink="{weblink}"/>\n"""
            )

        else:
            fmtStr = fields[0]
            text = fields[-1].replace("&", "&amp;")
            # body.append(f"XX {inRemark=}\n")

            if code == "TI":
                if not inTitle:
                    finishLetter()
                    startLetter()
                    if pendingPageBreak is not None:
                        body.append(pendingPageBreak)
                        pendingPageBreak = None
                    letterPageNum = pageNum
                    seq = fmtStr
                    inTitle = True
                title.append(text)
            else:
                if pendingPageBreak is not None:
                    body.append(pendingPageBreak)
                    pendingPageBreak = None

                if inTitle:
                    distill()
                    inTitle = False
                    body.append("""<head>""")
                    for tit in title:
                        body.append(f"""{tit}<lb/>\n""")
                    body.append("""</head>\n""")

                if (code == "HD" or code not in {"PE", "LE"}) and inRemark:
                    body.append("</remark>\n")
                    inRemark = False

                if code in {"TI", "PE", "LE", "HD"} and inParaO:
                    body.append("</para>\n")
                    inParaO = False

                textBare = text.strip()
                if textBare.startswith("<folio>"):
                    textTest = footnoteRe.sub("", textBare).strip(".,:;!?").strip()
                    if textTest.endswith("</folio>"):
                        body.append(f"{textBare}\n")
                    else:
                        if not inRemark:
                            body.append("<remark>")
                            inRemark = True
                            inParaO = False
                        body.append(f"{text}<lb/>\n")
                    continue

                if code == "PE":
                    body.append(f"<remark>{text}<lb/>\n")
                    inRemark = True
                    continue

                if code == "LE":
                    if not inRemark:
                        print(f"WARNING: line {i + 1} {code} outside <remark>: {text}")
                        body.append("<remark>")
                        inRemark = True
                        inParaO = False
                    body.append(f"{text}<lb/>\n")
                    continue

                if code == "HD":
                    body.append(f"<subhead>{text}</subhead>\n")
                    continue

                if code == "PO":
                    if inParaO:
                        body.append("</para>\n")
                    body.append(f"<para>{text}<lb/>\n")
                    inParaO = True
                    continue

                if code == "LO":
                    if not inParaO:
                        body.append("<para>")
                        inParaO = True
                    body.append(f"{text}<lb/>\n")
                    continue

                if code == "TB":
                    if inRemark:
                        body.append("</remark>\n")
                        inRemark = False
                    if inParaO:
                        body.append("</para>\n")
                        inParaO = False
                    nTable = fmtStr[2:]
                    body.append(f"""<table n="{nTable}">\n""")
                    continue

                if code == "TE":
                    body.append("</table>\n")
                    nTable = None
                    continue

                if code == "RB":
                    nRow = fmtStr[2:]
                    body.append(f"""<row n="{nTable}" row="{nRow}">\n""")
                    continue

                if code == "RE":
                    body.append("</row>\n")
                    nRow = None
                    continue

                if code == "TC":
                    atts = fmtStr.split(",")
                    nCol = "1"
                    x = "0"
                    for att in atts:
                        if att.startswith("c"):
                            nCol = att[2:]
                        elif att.startswith("x"):
                            x = att[2:]
                    body.append(
                        f"""<cell n="{nTable}" row="{nRow}" col="{nCol}" x="{x}">"""
                        f"""{text}</cell>\n"""
                    )
                    continue

                body.append(line)

    finishLetter()

    for (mKey, mData) in metadata.items():
        print(f"{mKey}:")
        for (ent, freq) in sorted(mData.items()):
            print(f"\t{freq:>2}x {ent}")


commands = set(sys.argv[1:])

if "pdf" in commands:
    dataFromPdf(export=False)
if "pdfe" in commands:
    dataFromPdf(export=True)
if "struct" in commands:
    getStructure()
if "fine" in commands:
    getFineStructure()
if "xml" in commands:
    getXml()
