import sys
import os
import collections
import re
from itertools import chain

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
REPORT_DIR = f"{REPO_DIR}/trimreport"

TF_DIR = f"{REPO_DIR}/tf"
OUT_DIR = f"{TF_DIR}/{VERSION_TF}"

MERGE_DOCS = {
    "06:p0406": ("06:p0407",),
}
SKIP_DOCS = {x for x in chain.from_iterable(MERGE_DOCS.values())}

HI_CLEAN_STRONG_RE = re.compile(r"""<hi\b[^>]*>([^<]*)</hi>""", re.S)

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
        if subdir == "rest":
            os.rmdir(f"{path}/{subdir}")


# SOURCE READING


PAGENUM_RE = re.compile(
    r"""<interpGrp type="page"><interp>([0-9]+)</interp></interpGrp>""", re.S
)


def getPage(path):
    with open(path) as fh:
        text = fh.read()
    match = PAGENUM_RE.search(text)
    return f"p{int(match.group(1)):>04}" if match else None


def getVolumes(srcDir):
    volumes = []
    with os.scandir(srcDir) as dh:
        for entry in dh:
            if entry.is_dir():
                vol = entry.name
                if not vol.isdigit():
                    continue
                volumes.append(f"{int(vol):>02}")
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
                    pureName = name[0:-4]
                    if idMap is not None:
                        lid = getPage(f"{srcDir}/{name}")
                        if lid in lidSet:
                            collisions += 1
                        lidSet.add(lid)
                        idMap[pureName] = lid
                    letters.append(pureName)
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


BODY_RE = re.compile(r"""<body[^>]*>(.*?)</body>""", re.S)


def combineTexts(first, following):
    bodies = []

    for text in following:
        match = BODY_RE.search(text)
        bodies.append(match.group(1))

    return first.replace("</body", ("\n".join(bodies)) + "</body>")


# TOP-LEVEL TRIM

HARD_CORRECTIONS = {
    "10:p0749": (
        (
            re.compile(
                r"""(<pb n="799"[^>]*>\s*<fw\b[^>]*>.*?</fw>\s*<note\b[^>]*>.*?</note>\s*)""",
                re.S,
            ),
            r"""</p>\n\1<p>""",
        ),
        (
            re.compile(
                r"""(<pb n="997"[^>]*>\s*<fw\b[^>]*>.*?</fw>\s*)(</p>\s*)""",
                re.S,
            ),
            r"""\2\1""",
        ),
        (
            re.compile(
                r"""(<pb n="1016"[^>]*>\s*<fw\b[^>]*>.*?</fw>\s*<note\b[^>]*>.*?</note>\s*)""",
                re.S,
            ),
            r"""</p>\n\1<p>""",
        ),
    ),
    "12:p0281": (
        (
            re.compile(
                r"""(<pb n="403"[^>]*>\s*<fw\b[^>]*>.*?</fw>\s*<note\b[^>]*>.*?</note>\s*)""",
                re.S,
            ),
            r"""</p>\n\1<p>""",
        ),
        (
            re.compile(
                r"""(<pb n="509"[^>]*>\s*<fw\b[^>]*>.*?</fw>\s*<note\b[^>]*>.*?</note>\s*)""",
                re.S,
            ),
            r"""</p>\n\1<p>""",
        ),
    ),
}


"""
<pb n="997" tpl="2" vol="10" facs="250_0997"/>
<fw place="top" type="head" facs="#zone.4470651">VI. JOHANNES THEDENS, DANIËL NOLTHENIUS, PIETER ROCHUS PAS-QUES DE CHAVONNES, JACOB LAKEMAN, ELIAS GUILLOT, THOMASVAN SPREEKENS, NICOLAAS VAN BERENDREGT, JOHANNES MAT-THEUS CLUYSENAAR, MAURITS VAN AERDEN en NICOLAAS CRUL,BATAVIA 17 december 1742.Kol. Arch. 2444, VOC 2552, fol. 1274-1290.
</fw>
</p>

"""


def trim(stage, givenVol, givenLid, trimPage, processPage, *args, **kwargs):
    if stage == 0:
        SRC = IN_DIR
    else:
        SRC = f"{TRIM_DIR}{stage - 1}"
    DST = f"{TRIM_DIR}{stage}"
    REP = f"{REPORT_DIR}{stage}"

    if os.path.exists(DST):
        clearTree(DST)
    os.makedirs(DST, exist_ok=True)
    os.makedirs(REP, exist_ok=True)

    volumes = getVolumes(SRC)

    analysis = collections.Counter()
    analysisAfter = collections.Counter()

    info = dict(
        table=0,
        docs=[],
        metasGood=[],
        metasUnknown=[],
        metasDistilled=collections.defaultdict(dict),
        captionInfo=collections.defaultdict(list),
        captionNorm=collections.defaultdict(list),
        captionVariant=collections.defaultdict(list),
        captionRoman=collections.defaultdict(list),
        folioResult=collections.defaultdict(list),
        folioTrue=collections.defaultdict(list),
        folioFalse=collections.defaultdict(list),
        folioUndecided=collections.defaultdict(lambda: collections.defaultdict(list)),
        headInfo=collections.defaultdict(list),
        heads={},
        bigTitle={},
        splits=[],
        splitsX=[],
    )

    mergeText = {}
    previousDoc = None

    for vol in volumes:
        if givenVol is not None and vol not in givenVol:
            continue
        print(f"\rvolume {vol}" + " " * 70)

        volDir = vol.lstrip("0") if stage == 0 else vol
        thisSrcDir = f"{SRC}/{volDir}"
        thisDstDir = f"{DST}/{vol}"
        rest = "/rest" if stage == 1 else ""
        os.makedirs(f"{thisDstDir}{rest}", exist_ok=True)

        info["vol"] = vol
        idMap = {} if stage == 0 else None
        letters = getLetters(thisSrcDir, idMap)

        if stage == 1:
            for name in letters:
                lid = name if idMap is None else idMap[name]
                if givenLid is not None and lid not in givenLid:
                    continue
                doc = f"{vol}:{lid}"
                if doc in SKIP_DOCS:
                    continue
                if doc in MERGE_DOCS:
                    with open(f"{thisSrcDir}/{name}.xml") as fh:
                        text = fh.read()
                    followTexts = []
                    for followDoc in MERGE_DOCS[doc]:
                        followName = followDoc.split(":", 1)[1] + ".xml"
                        with open(f"{thisSrcDir}/{followName}") as fh:
                            followTexts.append(fh.read())
                    mergeText[doc] = combineTexts(text, followTexts)

        for name in letters:
            lid = name if idMap is None else idMap[name]
            if givenLid is not None and lid not in givenLid:
                continue
            doc = f"{vol}:{lid}"
            if stage == 1 and doc in SKIP_DOCS:
                continue
            sys.stderr.write(f"\r\t{lid}      ")
            info["doc"] = doc
            info["docs"].append(doc)

            if stage == 1 and doc in mergeText:
                text = mergeText[doc]
            else:
                with open(f"{thisSrcDir}/{name}.xml") as fh:
                    text = fh.read()

            if stage == 1:
                if doc in HARD_CORRECTIONS:
                    for (pattern, replacement) in HARD_CORRECTIONS[doc]:
                        (text, n) = pattern.subn(replacement, text)
                        if not n:
                            print(f"\nHARD REPLACEMENT FAILED on {doc}:")
                            print(f"\t{pattern} => {replacement}")

            origText = text

            thisAnalysis = analyse(text)
            for (path, count) in thisAnalysis.items():
                analysis[path] += count
            text = trimDocument(
                stage, text, trimPage, info, processPage, previousDoc, *args, **kwargs
            )
            if text is None:
                dstName = f"{lid}.xml"
                with open(f"{thisDstDir}/rest/{dstName}", "w") as fh:
                    fh.write(origText)
                continue

            dstName = f"{lid}.xml"
            with open(f"{thisDstDir}/{dstName}", "w") as fh:
                fh.write(text)

            thisAnalysisAfter = analyse(text, after=True)
            for (path, count) in thisAnalysisAfter.items():
                analysisAfter[path] += count

            previousDoc = doc

    print("\rdone" + " " * 70)

    docs = info["docs"]
    totalDocs = len(docs)
    print(f"{totalDocs} documents")

    with open(f"{REP}/elementsIn.tsv", "w") as fh:
        for (path, amount) in sorted(analysis.items()):
            fh.write(f"{path}\t{amount}\n")

    with open(f"{REP}/elementsOut.tsv", "w") as fh:
        for (path, amount) in sorted(analysisAfter.items()):
            fh.write(f"{path}\t{amount}\n")

    if stage == 1:
        captionInfo = info["captionInfo"]
        captionNorm = info["captionNorm"]
        captionVariant = info["captionVariant"]
        captionRoman = info["captionRoman"]
        if captionNorm or captionVariant or captionInfo or captionRoman:
            print("CAPTIONS:")
            print(f"\t{len(captionNorm):>3} verified names")
            print(f"\t{len(captionVariant):>3} unresolved variants")
            print(f"\t{len(captionRoman):>3} malformed roman numerals")
            with open(f"{REP}/fwh-yes.tsv", "w") as fh:
                for (captionSrc, tag) in (
                    (captionNorm, "OK"),
                    (captionVariant, "XX"),
                    (captionInfo, "II"),
                    (captionRoman, "RR"),
                ):
                    for caption in sorted(captionSrc):
                        theseDocs = captionSrc[caption]
                        firstDoc = theseDocs[0]
                        nDocs = len(theseDocs)
                        fh.write(f"{firstDoc} {nDocs:>4}x {tag} {caption}\n")

        folioUndecided = info["folioUndecided"]
        folioTrue = info["folioTrue"]
        folioFalse = info["folioFalse"]
        folioResult = info["folioResult"]
        if folioUndecided or folioTrue or folioFalse:
            with open(f"{REP}/folio.txt", "w") as fh:
                for (folioSrc, tag) in (
                    (folioFalse, "NO "),
                    (folioTrue, "YES"),
                    (folioResult, "FF"),
                ):
                    triggers = 0
                    occs = 0
                    for folio in sorted(folioSrc):
                        theseDocs = folioSrc[folio]
                        firstDoc = theseDocs[0]
                        nDocs = len(theseDocs)
                        triggers += 1
                        occs += nDocs
                        fh.write(f"{firstDoc} {nDocs:>4}x {tag} {folio}\n")
                    print(f"FOLIO {tag}:")
                    print(f"\t{tag}: {triggers:>2} with {occs:>4} occurrences")
                if folioUndecided:
                    totalContexts = sum(len(x) for x in folioUndecided.values())
                    totalOccs = sum(
                        sum(len(x) for x in folioInfo.values())
                        for folioInfo in folioUndecided.values()
                    )
                    print(
                        f"FOLIOS (undecided): {len(folioUndecided)} triggers,"
                        f" {totalContexts} contexts,"
                        f" {totalOccs} occurrences"
                    )
                    for (fol, folInfo) in sorted(
                        folioUndecided.items(), key=lambda x: (len(x[1]), x[0])
                    ):
                        nContexts = len(folInfo)
                        nOccs = sum(len(x) for x in folInfo.values())
                        msg = (
                            f"{fol:<20} {nContexts:>3} contexts, {nOccs:>4} occurrences"
                        )
                        print(f"\t{msg}")
                        fh.write(f"{msg}\n")
                        for (context, pages) in sorted(
                            folInfo.items(), key=lambda x: (len(x[1]), x[0])
                        ):
                            fh.write(f"\t{pages[0]} {len(pages):>4}x: {context}\n")

        splits = info["splits"]
        splitsX = info["splitsX"]
        headInfo = info["headInfo"]
        bigTitle = info["bigTitle"]

        for doc in docs:
            if doc not in headInfo:
                headInfo[doc] = []

        noHeads = []
        singleHeads = []
        shortHeads = []

        for doc in sorted(docs):
            if doc in bigTitle:
                continue
            heads = headInfo[doc]
            nHeads = len(heads)
            if nHeads == 0:
                noHeads.append(doc)
            else:
                for (fullDoc, head) in heads:
                    if len(head) < 40 and "BIJLAGE" not in head:
                        shortHeads.append((fullDoc, head))
                if nHeads > 1:
                    theseSplits = splitDoc(doc)
                    for ((startDoc, newDoc, sHead), (fullDoc, mHead)) in zip(
                        theseSplits, heads
                    ):
                        newPage = newDoc[4:]
                        expPage = fullDoc[9:]
                        if newPage == expPage and sHead == mHead:
                            singleHeads.append((newDoc, sHead))
                            splits.append((startDoc, newDoc, sHead))
                        else:
                            splitsX.append((startDoc, newPage, expPage, sHead, mHead))
                else:
                    singleHeads.append((doc, heads[0][1]))

        print(f"\t: {len(shortHeads):>3} short headings")
        print(f"\t: {len(noHeads):>3} without heading")
        print(f"\t: {len(singleHeads):>3} with single heading")
        print(f"\t: {len(noHeads) + len(singleHeads):>3} letters")
        print(f"\t: {len(splits):>3} split-off letters")
        print(f"\t: {len(splitsX):>3} split-off errors")
        print(f"\t: {len(bigTitle):>3} rest documents")

        with open(f"{REP}/heads.tsv", "w") as fh:
            for doc in noHeads:
                fh.write(f"{doc} NO\n")
            for (mainDoc, (doc, head)) in shortHeads:
                fh.write(f"{doc} =SHORT=> {head}\n")
            for (doc, head) in singleHeads:
                etc = " ... " if len(head) > 70 else ""
                fh.write(f"{doc} => {head[0:70]}{etc}\n")

        with open(f"{REP}/rest.tsv", "w") as fh:
            for (doc, head) in sorted(bigTitle.items()):
                msg = f"{doc} => {head}"
                fh.write(f"{msg}\n")

        with open(f"{REP}/splits.tsv", "w") as fh:
            for (startDoc, newDoc, sHead) in splits:
                etc = " ... " if len(sHead) > 50 else ""
                fh.write(f"{startDoc} =OK=> {newDoc} {sHead[0:50]}\n")
            for (startDoc, newPage, expPage, sHead, mHead) in splitsX:
                label = "===" if newPage == expPage else "=/="
                fh.write(f"{startDoc} =XX=> {newPage} {label} {expPage}\n")
                if sHead != mHead:
                    fh.write(f"\t{sHead}\n\t===versus===\n\t{mHead}\n")

    elif stage == 2:
        metasGood = info["metasGood"]
        metasUnknown = info["metasUnknown"]
        metasDistilled = info["metasDistilled"]
        metasStats = collections.defaultdict(collections.Counter)

        metasMap = {
            "xx": "inconsistencies",
            "+-": "not based on distillation",
            "-+": "supplied by distillation",
            "--": "missing",
            "OK": "correct",
        }
        metasOrder = {label: i for (i, label) in enumerate(metasMap)}

        heads = info["heads"]
        print("METADATA:")
        print(f"\t{len(metasGood):>3} docs with complete metadata")
        print(f"\t{len(metasUnknown):>3} docs with unrecognized metadata")
        if metasUnknown:
            with open(f"{REP}/metaUnrecognized.txt", "w") as fh:
                for (doc, meta) in sorted(metasUnknown):
                    fh.write(f"{doc}\n")
                    for (k, v) in meta.items():
                        fh.write(f"\t{k:<10} = {v}\n")
                    fh.write("\n")

        with open(f"{REP}/meta.txt", "w") as fh:
            for (doc, meta) in sorted(metasGood):
                fh.write(f"{doc}\n")
                fh.write(f"{heads[doc]}\n")
                for (k, v) in meta.items():
                    if k == "pid":
                        fh.write(f"\tOK {k:<10} = {v}\n")
                    else:
                        distilled = metasDistilled[doc].get(k, "")
                        if distilled != normVal(k, v) or (not distilled and not v):
                            if doc in FROM_PREVIOUS and k in COLOFON_KEYS:
                                fh.write(f"\tOK {k:<10} {v:<10} =PDx {distilled}\n")
                                metasStats[k]["OK"] += 1
                            elif (
                                doc in CORRECTION_ALLOWED
                                and k in CORRECTION_ALLOWED[doc]
                            ):
                                fh.write(f"\tOK {k:<10} {v:<10} xVD= {distilled}\n")
                                metasStats[k]["OK"] += 1
                            elif (
                                doc in CORRECTION_FORBIDDEN
                                and k in CORRECTION_FORBIDDEN[doc]
                            ):
                                fh.write(f"\tOK {k:<10} {v:<10} =VDx {distilled}\n")
                                metasStats[k]["OK"] += 1
                            elif doc in ABSENT_ALLOWED and k in ABSENT_ALLOWED[doc]:
                                fh.write(f"\tOK {k:<10} {v:<10} -VD- {distilled}\n")
                                metasStats[k]["OK"] += 1
                            else:
                                if distilled and v:
                                    fh.write(f"\txx {k:<10} {v:<10} ?VD? {distilled}\n")
                                    metasStats[k]["xx"] += 1
                                elif distilled and not v:
                                    fh.write(
                                        f"\t-+ {k:<10} {'':<10} <VD= {distilled}\n"
                                    )
                                    metasStats[k]["-+"] += 1
                                elif not distilled and v:
                                    fh.write(f"\t+- {k:<10} {v:<10} =VD> {''}\n")
                                    metasStats[k]["+-"] += 1
                                else:
                                    fh.write(f"\t-- {k:<10} {'':<10} ???? {''}\n")
                                    metasStats[k]["--"] += 1
                        else:
                            fh.write(f"\tOK {k:<10} = {v:<10} =VD= {distilled}\n")
                            metasStats[k]["OK"] += 1
                fh.write("\n")

        for k in META_KEY_ORDER:
            if k not in metasStats:
                continue
            print(f"\t\t{k}")
            labelInfo = metasStats[k]
            for label in sorted(labelInfo, key=lambda x: metasOrder[x]):
                print(f"\t\t\t{label}: {labelInfo[label]:>3} x {metasMap[label]}")

        with open(f"{REP}/heads.tsv", "w") as fh:
            for (doc, head) in heads.items():
                fh.write(f"{doc} {head}\n")

    return True


SPLIT_DOC_RE = re.compile(
    r"""
        <pb\b[^>]*?\bn="([0-9]+)"[^>]*>\s*
        (?:
            <pb\b[^>]*>\s*
        )*
        (?:
            <p\b[^>]*>.*?</p>\s*
        )?
        <head\b[^>]*>(.*?)</head>
    """,
    re.S | re.X,
)
HEADER_RE = re.compile(r"""^.*?</header>\s*""", re.S)
HEADER_PAGE_RE = re.compile(r"""<meta key="page" value="[^"]*"/>""", re.S)
HEADER_SEQ_RE = re.compile(r"""<meta key="seq" value="[^"]*"/>""", re.S)


def splitDoc(doc):
    stage = 1
    (vol, startPage) = doc.split(":")
    path = f"{TRIM_DIR}{stage}/{doc.replace(':', '/')}.xml"
    with open(path) as fh:
        text = fh.read()

    match = HEADER_RE.match(text)
    origHeader = match.group(0)

    match = BODY_RE.search(text)
    body = match.group(1)

    lastPageNum = None
    lastHead = None
    lastSeq = None
    lastIndex = 0
    splits = []

    for (i, match) in enumerate(SPLIT_DOC_RE.finditer(body)):
        pageNum = int(match.group(1))
        head = HI_CLEAN_STRONG_RE.sub(
            r"""\1""", match.group(2).replace("<lb/>", " ").replace("\n", " ")
        )
        sMatch = SEQ_RE.match(head)
        if sMatch:
            seq = sMatch.group(0)
        else:
            print(f"\nnNO SEQ: {head}")
            seq = ""

        if i == 0:
            lastPageNum = pageNum
            lastHead = head
            lastSeq = seq
            continue

        (b, e) = match.span()
        lastText = body[lastIndex:b]
        lastText = P_INTERRUPT_RE.sub(r"""\1""", lastText)
        lastText = P_JOIN_RE.sub(r"""\1\2""", lastText)

        header = HEADER_PAGE_RE.sub(
            f"""<meta key="page" value="{lastPageNum}"/>""", origHeader, count=1
        )
        header = HEADER_SEQ_RE.sub(
            f"""<meta key="seq" value="{lastSeq}"/>""", origHeader, count=1
        )
        writeDoc(vol, lastPageNum, header, lastText)
        splits.append((doc, f"{vol}:p{lastPageNum:>04}", lastHead))
        lastPageNum = pageNum
        lastHead = head
        lastSeq = seq
        lastIndex = b

    if i > 0:
        header = HEADER_PAGE_RE.sub(
            f"""<meta key="page" value="{lastPageNum}"/>""", origHeader, count=1
        )
        header = HEADER_SEQ_RE.sub(
            f"""<meta key="seq" value="{lastSeq}"/>""", origHeader, count=1
        )
        lastText = body[lastIndex:]
        writeDoc(vol, lastPageNum, header, lastText)
        splits.append((doc, f"{vol}:p{lastPageNum}", lastHead))

    return splits


def writeDoc(vol, pageNum, header, text):
    stage = 1
    with open(f"{TRIM_DIR}{stage}/{vol}/p{pageNum:>04}.xml", "w") as fh:
        fh.write(f"{header}<body>\n{text}</body>\n</teiTrim>")


HEADER_TITLE_RE = re.compile(
    r"""
        <meta\s+
        key="title"\s+
        value="([^"]*)"
    """,
    re.S | re.X,
)


REST_RE = re.compile(
    r"""
    ^
    (?:
        index
        |
        indices
        |
        toelichting
    )
    """,
    re.S | re.I | re.X,
)


BIG_TITLE_PART_RE = re.compile(
    r"""
    (
        \s*
        <pb\b[^>]*?\bn="([^"]*)"[^>]*>
        \s*
        (?:
            <pb\b[^>]*?\bn="[^"]*"[^>]*>
            \s*
        )*
        <bigTitle>(.*?)</bigTitle>
        \s*
        (?:
            (?:
                (?:
                    <p\b[^>]*>.*?</p>
                )
                |
                (?:
                    <pb\b[^>]*>
                )
            )
            \s*
        )*
        \s*
    )
    """,
    re.S | re.X,
)


BIG_TITLE_RE = re.compile(r"""<bigTitle>(.*?)</bigTitle>""", re.S)
PB_P_PERM_RE = re.compile(
    r"""
    (
        (?:
            <pb\b[^>]*>\s*
        )+
    )
    (
        </p>
    )
    """,
    re.S | re.X,
)


def trimDocument(
    stage, text, trimPage, info, processPage, previousDoc, *args, **kwargs
):
    headElem = "teiHeader" if stage == 0 else "header"
    headerRe = re.compile(rf"""<{headElem}[^>]*>(.*?)</{headElem}>""", re.S)
    match = headerRe.search(text)
    metaText = match.group(1)
    match = BODY_RE.search(text)
    bodyText = match.group(1)

    header = (
        trimHeader(metaText)
        if stage == 0
        else checkMeta(metaText, bodyText, info)
        if stage == 2
        else f"""<header>\n{metaText}\n</header>"""
    )
    if stage == 1:
        doc = info["doc"]
        bigTitle = info["bigTitle"]
        match = HEADER_TITLE_RE.search(header)
        if match:
            title = match.group(1)
            if REST_RE.match(title):
                bigTitle[doc] = HI_CLEAN_STRONG_RE.sub(
                    r"""\1""", title.replace("<lb/>", " ").replace("\n", " ")
                )
                return None

        if doc in CORRECTION_HEAD:
            (corrRe, corrText) = CORRECTION_HEAD[doc]
            (bodyText, n) = corrRe.subn(f"<head>{corrText}</head>\n", bodyText, count=1)
            if not n:
                print(f"\nWarning: head correction failed on `{doc}`")

    body = trimBody(stage, bodyText, trimPage, info, processPage, *args, **kwargs)

    if stage == 1:
        body = PB_P_PERM_RE.sub(r"""\2\n\1""", body)
        match = BIG_TITLE_PART_RE.search(body)

        if match:
            vol = info["vol"]
            doc = info["doc"]

            text = match.group(1)

            if text == body:
                head = match.group(3)
                bigTitle[doc] = HI_CLEAN_STRONG_RE.sub(
                    r"""\1""", head.replace("<lb/>", " ").replace("\n", " ")
                )
                return None

            bigTitles = BIG_TITLE_PART_RE.findall(body)
            for (page, pnum, head) in bigTitles:
                pnum = f"p{int(pnum):>04}"
                doc = f"{vol}:{pnum}"
                bigTitle[doc] = HI_CLEAN_STRONG_RE.sub(
                    r"""\1""", head.replace("<lb/>", " ").replace("\n", " ")
                )
                fileName = f"{pnum}.xml"
                path = f"{TRIM_DIR}{stage}/{vol}/rest/{fileName}"
                with open(path, "w") as fh:
                    fh.write(page)

            body = BIG_TITLE_PART_RE.sub("", body)

        headInfo = info["headInfo"]
        heads = headInfo[doc]
        if len(heads) <= 1:
            body = P_INTERRUPT_RE.sub(r"""\1""", body)
            body = P_JOIN_RE.sub(r"""\1\2""", body)

    return f"""<teiTrim>\n{header}\n<body>\n{body}\n</body>\n</teiTrim>"""


# TRIM HEADER


META_KEY_TRANS_DEF = tuple(
    x.strip().split()
    for x in """
    pid pid
    page page
    seq n
    title titleLevel1
    author authorLevel1
    rawdate dateLevel1
    place localization_placeLevel1
    yearFrom witnessYearLevel1_from
    yearTo witnessYearLevel1_to
    monthFrom witnessMonthLevel1_from
    monthTo witnessMonthLevel1_to
    dayFrom witnessDayLevel1_from
    dayTo witnessDayLevel1_to
""".strip().split(
        "\n"
    )
)

META_KEY_TRANS = {old: new for (new, old) in META_KEY_TRANS_DEF}
META_KEY_ORDER = tuple(x[0] for x in META_KEY_TRANS_DEF)
COLOFON_KEYS = META_KEY_ORDER[4:]
META_KEYS = {x[1] for x in META_KEY_TRANS_DEF}

META_KV_RE = re.compile(
    r"""
        <interpGrp
            \b[^>]*?\b
            type="([^"]*)"
            [^>]*
        >
            (.*?)
        </interpGrp>
    """,
    re.S | re.X,
)

META_KV_2_RE = re.compile(r"""<meta key="([^"]*)" value="([^"]*)"/>""", re.S)

META_VAL_RE = re.compile(
    r"""
        (?:
            <interp>
                (.*?)
            </interp>
        )*
    """,
    re.S | re.X,
)


def transVal(value):
    values = META_VAL_RE.findall(value)
    return ",".join(v for v in values if v)


WHITE_NLNL_RE = re.compile(r"""\n{3,}""", re.S)
WHITE_NL_RE = re.compile(r"""(?:[ \t]*\n[ \t\n]*)""", re.S)
SPACE_RE = re.compile(r"""  +""", re.S)
WHITE_RE = re.compile(r"""\s\s+""", re.S)
PB_RE = re.compile(r"""<pb\b[^>]*/>""", re.S)
HEAD_RE = re.compile(r"""<head\b[^>]*>(.*?)</head>""", re.S)


def trimHeader(text):
    metadata = {
        META_KEY_TRANS.get(k, k): transVal(v) for (k, v) in META_KV_RE.findall(text)
    }

    newText = "\n".join(
        f"""<meta key="{k}" value="{v}"/>""" for (k, v) in metadata.items()
    )

    return f"<header>\n{newText}\n</header>\n"


FIRST_PAGE_RE = re.compile(r"""<pb\b[^>]*?\bn="([^"]*)"[^>]*>""", re.S)


def checkMeta(metaText, bodyText, info):
    doc = info["doc"]
    metasGood = info["metasGood"]
    metasUnknown = info["metasUnknown"]
    metasDistilled = info["metasDistilled"]

    metadata = {k: v for (k, v) in META_KV_2_RE.findall(metaText)}
    metaGood = {k: metadata.get(k, "") for k in META_KEY_ORDER}
    if doc in FROM_PREVIOUS:
        for k in COLOFON_KEYS:
            metaPrevious = metasGood[-1][1]
            metaGood[k] = metaPrevious[k]
    metaUnknown = {k: metadata[k] for k in sorted(metadata) if k not in META_KEYS}
    metasGood.append((doc, metaGood))
    if metasUnknown:
        metasUnknown.append((doc, metaUnknown))

    match = HEAD_RE.search(bodyText)
    head = HI_CLEAN_STRONG_RE.sub(
        r"""\1""", match.group(1).replace("<lb/>", " ").replace("\n", " ")
    )
    doc = info["doc"]
    info["heads"][doc] = head
    match = FIRST_PAGE_RE.search(bodyText)
    firstPage = match.group(1) if match else ""

    distilled = distill(head, firstPage)
    metasDistilled[doc] = distilled

    metaResult = {k: normVal(k, v) for (k, v) in metaGood.items()}

    if doc in CORRECTION_ALLOWED:
        for k in CORRECTION_ALLOWED[doc]:
            metaResult[k] = distilled[k]
    else:
        metaResult = metaGood

    newMeta = "\n".join(
        f"""<meta key="{k}" value="{v}"/>""" for (k, v) in metaResult.items()
    )

    return f"<header>\n{newMeta}\n</header>\n"


SEQ_RE = re.compile(
    r"""
        ^
        (
            [IVXLCDM1]+
            (?:
                \s*
                a
            )?
        )
        \.?
    """,
    re.S | re.X,
)
DATE_RE = re.compile(
    r"""
        \(?
        \s*
        (
            [0-9]{1,2}
            \s+
            (?:
                januari
                |februari
                |maart
                |april
                |mei
                |juni
                |juli
                |augustus
                |september
                |oktober
                |november
                |december
            )
            \s+
            1[6-8]
            [0-9 ]*
            \s*
            \??
        )
        \s*
        \)?
        \s*
        \.?
        \s*
    """,
    re.S | re.X,
)

MONTH_DEF = """
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

""".strip().split(
    "\n\n"
)

MONTH_VARIANTS = {}
MONTHS = set()
MONTH_NUM = {}

for (i, nameInfo) in enumerate(MONTH_DEF):
    (intention, *variants) = nameInfo.strip().split()
    MONTH_NUM[intention] = i + 1
    MONTHS.add(intention)
    for variant in variants + (
        [intention[0:3], f"{intention[0:3]}.", f"{intention[0:4]}."]
    ):
        MONTH_VARIANTS[variant] = intention


NUM_SANITIZE_RE = re.compile(r"""[0-9][0-9 ]*[0-9]""", re.S)


def numSanitize(match):
    return match.group(0).replace(" ", "")


def normVal(k, val):
    val = val.strip()

    if k == "seq":
        return val.replace("VIL", "VII")

    if k == "rawdate":
        val = NUM_SANITIZE_RE.sub(numSanitize, val)
        newVal = " ".join(MONTH_VARIANTS.get(w, w) for w in val.split())
        if "?" in newVal and "(?)" not in newVal:
            newVal = newVal.replace("?", " (?)")

        return newVal

    return val


CORRECTION_ALLOWED = {
    "01:p0152": {"rawdate", "dayFrom", "dayTo"},
}
CORRECTION_FORBIDDEN = {}
ABSENT_ALLOWED = {
    "01:p0018": {
        "rawdate",
        "dayFrom",
        "dayTo",
        "monthFrom",
        "monthTo",
        "yearFrom",
        "yearTo",
        "place",
    },
}
FROM_PREVIOUS = {"01:p0056"}

CORRECTION_HEAD = {
    "01:p0734": (
        re.compile(r"""<head .*?</p>""", re.S),
        (
            "VI. "
            "ANTONIO VAN DIEMEN, PHILIPS LUCASZ, CAREL RENIERS "
            "(EN DE GEASSUMEERDE RADEN) "
            "ABRAHAM WELSING EN CORNELIS VAN DER LIJN, "
            "BATAVIA. "
            "30 december 1638."
        ),
    ),
}


TAIL_RE = re.compile(
    r"""
        \s*
        (?:
            (?:
                &[^;]*;
            )
            |
            .
        )
        \)
        \s*
        \.?
        \s*
        $
    """,
    re.S | re.X,
)


def distill(head, firstPage):
    metadata = dict(page=firstPage)

    source = head

    match = TAIL_RE.search(head)
    if match:
        b = match.start()
        source = head[0:b]

    source = source.rstrip(".").rstrip()

    k = "seq"
    detectRe = SEQ_RE

    match = detectRe.search(source)
    if match:
        v = match.group(1).replace(" ", "").replace("1", "I")
        source = detectRe.sub("", source, count=1)
    else:
        v = ""
    metadata[k] = normVal(k, v)

    k = "rawdate"
    detectRe = DATE_RE

    match = detectRe.search(source)
    if match:
        v = match.group(1)
        source = detectRe.sub("", source, count=1)
    else:
        v = ""
    datePure = normVal(k, v.replace("?", ""))
    dateFrom = normVal(k, v)
    metadata[k] = dateFrom

    dateTo = datePure
    for (date, label) in ((datePure, "From"), (dateTo, "To")):
        parts = date.split()
        if len(parts) != 3:
            continue
        (day, month, year) = parts
        month = MONTH_NUM[month]
        metadata[f"day{label}"] = day
        metadata[f"month{label}"] = str(month)
        metadata[f"year{label}"] = year

    return metadata


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
P_JOIN_RE = re.compile(
    r"""
        (
            <p\b[^>]*
        )
        \b
        resp="int_paragraph_joining"
        ([^>]*>)
    """,
    re.S | re.X,
)


def trimBody(stage, text, trimPage, info, processPage, *args, **kwargs):
    if stage == 0:
        breaks = checkPb(text)
        if breaks:
            print("\nsensitive page breaks")
            for (elem, n) in sorted(breaks.items()):
                print(f"\t{n:>3} x {elem}")

        text = DIV_CLEAN_RE.sub(r"", text)

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
