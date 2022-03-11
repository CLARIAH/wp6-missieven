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
    HEAD_FILE,
    FN_BODY_FILE,
    FN_MARK_FILE,
    TIT_FILE,
    initTree,
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
    "Roman": "",
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

CORRECTIONS = {
    "Bengaaij4": dict(text="Bengaaij\n  4 \n", fmt=(None, dict(st="fn"), None)),
}
CORRECTIONS_APPLIED = collections.defaultdict(list)


def pprint(x, fh=None):
    pp.pprint(x, stream=fh, indent=2)


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
                                for (pattern, replacement) in CORRECTIONS.items():
                                    pos = span.find(pattern)
                                    if pos == -1:
                                        newLineText.append(span)
                                        newLineFmt.append(fmt)
                                    else:
                                        replText = replacement["text"]
                                        newSpan = span.replace(pattern, replText)
                                        for s in newSpan.split("\n"):
                                            newLineText.append(s)

                                        replFmt = [
                                            fmt if f is None else f
                                            for f in replacement["fmt"]
                                        ]
                                        for ft in replFmt:
                                            newLineFmt.append(ft)

                                        CORRECTIONS_APPLIED[pattern].append(
                                            (pageNum, span)
                                        )
                                        break

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

    fh = open(FMT_FILE, "w")
    hh = open(HEAD_FILE, "w")
    newLines = 0

    with open(TEXT_FILE, "w") as th:
        mainTitle = True
        for (band, filePageNum, pageNum, fileSpec) in pages:
            sys.stderr.write(f"\r{band:>2} {filePageNum:>04} = {pageNum:>04}")
            if type(fileSpec) is tuple:
                (textPath, fmtPath) = fileSpec
                with open(textPath) as ih:
                    for line in ih:
                        th.write(line)
                with open(fmtPath) as ih:
                    for line in ih:
                        fh.write(line)
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

            th.write(f"{pageIdent}\n")
            fh.write(f"{pageIdent}\n")

            for line in texts:
                firstSpan = True
                for span in line:
                    code = "> " if firstSpan else "  "
                    firstSpan = False
                    th.write(f"{code}{span}\n")

            for line in fmts:
                firstSpan = True
                for span in line:
                    code = "> " if firstSpan else "  "
                    firstSpan = False
                    fmt = ",".join(f"{k}={v}" for (k, v) in span.items())
                    fh.write(f"{code}{fmt}\n")

            headTextStr = "".join(headText)
            hh.write(f"{pageIdent} {headTextStr}\n")
        sys.stderr.write("\n")
    fh.close()
    hh.close()
    print(f"{newLines} new lines in spans")

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
            print(f"CORRECTION NOT APPLIED: {pattern}")
        else:
            applications = CORRECTIONS_APPLIED[pattern]
            nApps = len(applications)
            for (pageNum, span) in applications:
                print(f"CORRECTION APPLIED: {pattern} to `{span}` on page {pageNum}")
            if nApps > 1:
                print(f"CORRECTION APPLIED MULTIPLE TIMES: {pattern} {nApps}x")


def getTitlesFootnotes():
    with open(TEXT_FILE) as th:
        textLines = list(th)
    with open(FMT_FILE) as fh:
        formatLines = list(fh)

    fnBodyIndex = {}
    fnMarkIndex = {}
    fnBodies = []
    fnMarks = []
    titles = []

    prevS = ""
    prevFnum = 0

    band = ""
    pageNum = ""
    filePageNum = ""

    titleRe = re.compile(r"""^([IVX]+)\.? ([A-Z0-9, -]+)(\.?)$""")
    titleContRe = re.compile(r"""^([A-Z0-9, -]+)(\.?)$""")

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

    for (i, textLine) in enumerate(textLines):
        textLine = textLine.rstrip("\n")

        if textLine.startswith("=="):
            if fnStart >= 0:
                finishFn()
            (pageNum, band, filePageNum) = textLine.split()
            pageNum = pageNum.lstrip("=")
            band = band.split("=")[1]
            filePageNum = filePageNum.lstrip("0")
            continue
        if textLine == "":
            continue

        textLine = textLine[2:]
        fmtLine = formatLines[i][2:].rstrip("\n")

        match = titleRe.match(textLine)
        if match:
            curTitleNum = match.group(1)
            curTitleText = match.group(2)
            curDot = match.group(3)
            titleStart = i + 1
            prevFnum = 0
        else:
            if titleStart >= 0:
                if curDot == ".":
                    finishTitle()
                else:
                    match = titleContRe.match(textLine)
                    if match:
                        curTitleText += f" {match.group(0)}"
                        curDot = match.group(1)
                    else:
                        finishTitle()

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
                    if fnStart >= 0:
                        finishFn()
                    curFnNum = int(fNum)
                    curFnText = textLine
                    curGap = curFnNum != prevFnum + 1
                    fnStart = i - 1
                    prevFnum = curFnNum
            else:
                if fnStart >= 0:
                    curFnText += textLine

        st = data.get("st", "")
        if st in {"fn", "sup"}:
            fnNum = textLine.strip()
            if fnNum.isdigit():
                fnNum = int(fnNum)
                fnMarks.append((band, pageNum, filePageNum, i, theTitleNum, fnNum))
        prevS = s

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
                f"line {line:>5}"
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
                f"lines {start:>5}-{end:>5}\n"
                f"\t{fNum}. {fText}\n"
            )
            if hasGap:
                gaps += 1
                print(entry)
            fh.write(f"{entry}\n")
            fnBodyIndex.setdefault(tNum, {}).setdefault(fNum, []).append(i)

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


commands = set(sys.argv[1:])

if "pdf" in commands:
    dataFromPdf(export=False)
if "pdfe" in commands:
    dataFromPdf(export=True)
if "tfn" in commands:
    getTitlesFootnotes()
