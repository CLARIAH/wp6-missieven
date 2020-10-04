import sys
import os
import collections
import re
from itertools import chain

import yaml
import xml.etree.ElementTree as ET


def ucfirst(x, lower=True):
    return (x[0].upper() + (x[1:].lower() if lower else x[1:])) if x else x


# SOURCE CORRECTIONS

HARD_CORRECTIONS = {
    "04:p0496": (
        (
            re.compile(
                r"""I en 9 maart 1683""",
                re.S,
            ),
            r"""1 en 9 maart 1683""",
        ),
    ),
    "07:p0003": (
        (
            re.compile(
                r"""(<head\b[^>]*>)(CHRIS)""",
                re.S,
            ),
            r"""\1I. \2""",
        ),
    ),
    "07:p0660": (
        (
            re.compile(
                r"""(<head\b[^>]*>XX)L""",
                re.S,
            ),
            r"""\1II""",
        ),
    ),
    "10:p0857": (
        (
            re.compile(
                r"""decem¬ber""",
                re.S,
            ),
            r"""december""",
        ),
    ),
    "10:p0749": (
        (
            re.compile(
                r"""(<pb n="799"[^>]*>\s*<fw\b[^>]*>.*?</fw>\s*)(</p>\s*)""",
                re.S,
            ),
            r"""\2\1""",
        ),
        (
            re.compile(
                r"""(<pb n="997"[^>]*>\s*<fw\b[^>]*>.*?</fw>\s*)(</p>\s*)""",
                re.S,
            ),
            r"""\2\1""",
        ),
    ),
}


ADD_META_KEYS = {"authorFull"}

CORRECTION_ALLOWED = {
    "01:p0007": {"place"},
    "01:p0105": {"place", "author"},
    "01:p0106": {"author"},
    "01:p0121": {"author"},
    "01:p0129": {"author"},
    "01:p0247": {"author"},
    "01:p0302": {"place", "author"},
    "01:p0433": {"place", "author"},
    "01:p0482": {"place", "author"},
    "01:p0152": {"rawdate", "day", "month", "year"},
    "02:p0311": {"author"},
    "03:p0192": {"rawdate", "day"},
    "04:p0241": {"rawdate", "day"},
    "04:p0493": {"author"},
    "04:p0496": {"month"},
    "06:p0065": {"author"},
    "06:p0275": {"author"},
    "06:p0402": {"author"},
    "06:p0406": {"author"},
    "06:p0750": {"author"},
    "06:p0897": {"author"},
    "07:p0003": {"seq"},
    "07:p0290": {"author"},
    "07:p0353": {"author"},
    "07:p0381": {"author"},
    "07:p0396": {"author"},
    "07:p0413": {"author"},
    "07:p0456": {"author"},
    "07:p0467": {"author"},
    "07:p0479": {"author"},
    "07:p0485": {"author"},
    "07:p0517": {"author"},
    "07:p0534": {"author"},
    "07:p0537": {"author"},
    "07:p0547": {"author"},
    "07:p0552": {"author"},
    "07:p0583": {"author"},
    "07:p0596": {"author"},
    "07:p0607": {"author"},
    "07:p0610": {"author"},
    "07:p0640": {"author"},
    "07:p0651": {"author"},
    "07:p0657": {"author"},
    "07:p0660": {"seq", "author"},
    "07:p0661": {"author"},
    "07:p0684": {"author"},
    "07:p0693": {"author"},
    "07:p0706": {"author"},
    "07:p0707": {"author"},
    "07:p0710": {"author"},
    "07:p0744": {"author"},
    "07:p0745": {"author"},
    "07:p0746": {"rawdate", "day", "author"},
    "07:p0754": {"author"},
    "08:p0234": {"rawdate", "day"},
    "08:p0235": {"seq"},
    "09:p0070": {"rawdate", "day", "month", "year"},
    "09:p0344": {"seq", "rawdate", "day", "month", "year"},
    "09:p0628": {"seq", "rawdate", "day", "month", "year"},
    "10:p0297": {"rawdate", "day", "month", "year"},
    "10:p0399": {"rawdate", "day", "month", "year"},
    "11:p0224": {"seq"},
}
CORRECTION_FORBIDDEN = {
    "01:p0008": {"place"},
    "01:p0087": {"place"},
}
ABSENT_ALLOWED = {
    "01:p0018": {"rawdate", "day", "month", "year", "place"},
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

DISTIL_SPECIALS = {
    "01:p0007": dict(
        place=("AAN BOORD VAN DE VERE, VOOR MALEYO", "Schip Vere voor Maleyo")
    ),
    "01:p0247": dict(place=("Batavia", "Batavia")),
    "01:p0082": dict(rawdate=("7 mei 161 8", "7 mei 1618")),
    "08:p0171": dict(place=("Batavia", "Batavia")),
    "08:p0224": dict(place=("Batavia", "Batavia")),
    "09:p0070": dict(
        rawdate=("zonder datum 1729 (vermoedelijk 30 november)", "30 november 1729?")
    ),
    "10:p0633": dict(rawdate=("6 november1741", "6 november 1741")),
    "11:p0115": dict(rawdate=("8 oktober 1 744", "8 oktober 1744")),
}


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
    october

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
    for abb in (intention, intention[0:3], f"{intention[0:3]}.", f"{intention[0:4]}."):
        MONTH_VARIANTS[abb] = intention
    for variant in variants:
        for abb in (
            variant,
            variant[0:3],
            f"{variant[0:3]}.",
            f"{variant[0:4]}.",
        ):
            MONTH_VARIANTS[abb] = intention

MONTH_DETECT_PAT = "|".join(
    set(re.escape(mv) for mv in chain(MONTH_NUM, MONTH_VARIANTS))
)

PLACE_DEF = """
Banda-Neira
    bandaneira
    banda-neira
    banda

Batavia
    batavia
    ratavia
    ba¬tavia

Fort
    eort

Kasteel
    kasteel

Mauritius
    mauritius

Rede
    rede

Schip
    schip

""".strip().split(
    "\n\n"
)

PLACE_VARIANTS = {}
PLACES = set()

for (i, nameInfo) in enumerate(PLACE_DEF):
    (intention, *variants) = nameInfo.strip().split()
    PLACES.add(intention)
    PLACE_VARIANTS[intention] = intention
    for variant in variants:
        PLACE_VARIANTS[variant] = intention


DETECT_AUTHOR = re.compile(
    r"""
        ^
        \s*
        (.*)?
        \s*
        $
    """,
    re.S | re.X,
)
DETECT = dict(
    seq=re.compile(
        r"""
            ^
            (
                [IVXLCDM1]+
                \s*
                [IVXLCDMm1liTUH]*
                (?:
                    \s*
                    [aA]
                )?
                \b
            )
            \.?
        """,
        re.S | re.X,
    ),
    rawdate=re.compile(
        fr"""
            \(?
            \s*
            (
                (?:
                    [0-9I]{{1,2}}
                    |
                    (?:[0-9I]\ [0-9I])
                )
                (?:
                    \s+en\s+
                    (?:
                        [0-9I]{{1,2}}
                        |
                        (?:[0-9I]\ [0-9I])
                    )
                )?
                \s+
                (?: {MONTH_DETECT_PAT} )
                \s+
                1[6-8]
                [0-9]{{2}}
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
    ),
    place=re.compile(
        r"""
        [,.]
        \s*
        (
            (?:
                (?:
                    aan\ boord
                    |deventer
                    |in\ het\ schip
                    |kasteel
                )
                .*?
            )
            |
            [^.,]*?
        )
        \s*
        $
        """,
        re.S | re.I | re.X,
    ),
    author=DETECT_AUTHOR,
    authorFull=DETECT_AUTHOR,
)

LOWERS = set(
    """
    aan
    boord
    de
    eiland
    het
    in
    nabij
    op
    rede
    schip
    ter
    van
    voor
    zuidpunt
    """.strip().split()
)

NUM_SANITIZE_RE = re.compile(r"""[0-9][0-9 ]*[0-9]""", re.S)

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
        authorInfo=collections.defaultdict(lambda: collections.defaultdict(list)),
        placeInfo=collections.defaultdict(lambda: collections.defaultdict(list)),
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

    if stage == 0:
        metasUnknown = info["metasUnknown"]
        print(f"\t{len(metasUnknown):>3} docs with unrecognized metadata")
        with open(f"{REP}/metaUnrecognized.txt", "w") as fh:
            for (doc, meta) in sorted(metasUnknown):
                fh.write(f"{doc}\n")
                for (k, v) in meta.items():
                    fh.write(f"\t{k:<10} = {v}\n")
                fh.write("\n")
    elif stage == 1:
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
                    theseSplits = splitDoc(doc, info)
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
        authorInfo = info["authorInfo"]
        placeInfo = info["placeInfo"]
        metasGood = info["metasGood"]
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

        with open(f"{REP}/meta.txt", "w") as fh:
            for (doc, meta) in sorted(metasGood):
                fh.write(f"{doc}\n")
                fh.write(f"{heads[doc]}\n")
                for (k, v) in meta.items():
                    if k == "pid":
                        fh.write(f"\tOK {k:<10} = {v}\n")
                    else:
                        lb = "OK"
                        distilled = metasDistilled[doc].get(k, "")
                        if distilled != normVal(k, v, doc, info, None) or (
                            not distilled and not v
                        ):
                            if doc in FROM_PREVIOUS and k in COLOFON_KEYS:
                                fh.write(
                                    f"\t{lb} {k:<10} =PxD {v}\n"
                                    f"\t     {'':<8}    D {distilled}\n"
                                )
                                metasStats[k][lb] += 1
                            elif k in ADD_META_KEYS or (
                                doc in CORRECTION_ALLOWED
                                and k in CORRECTION_ALLOWED[doc]
                            ):
                                if distilled and v:
                                    fh.write(
                                        f"\t{lb} {k:<10} xV=D {distilled}\n"
                                        f"\t     {'':<8}    V {v}\n"
                                    )
                                elif distilled and not v:
                                    fh.write(f"\t{lb} {k:<10} -V=D {distilled}\n")
                                elif not distilled and v:
                                    fh.write(
                                        f"\t{lb} {k:<10} xV-D\n"
                                        f"\t     {'':<8}    V {v}\n"
                                    )
                                metasStats[k][lb] += 1
                            elif (
                                doc in CORRECTION_FORBIDDEN
                                and k in CORRECTION_FORBIDDEN[doc]
                            ):
                                if distilled and v:
                                    fh.write(
                                        f"\t{lb} {k:<10} =VxD {v}\n"
                                        f"\t     {'':<8}    D {distilled}\n"
                                    )
                                elif distilled and not v:
                                    fh.write(
                                        f"\t{lb} {k:<10} -VxD\n"
                                        f"\t     {'':<8}    D {distilled}\n"
                                    )
                                elif not distilled and v:
                                    fh.write(f"\t{lb} {k:<10} =V-D {distilled}\n")
                                metasStats[k][lb] += 1
                            elif doc in ABSENT_ALLOWED and k in ABSENT_ALLOWED[doc]:
                                if not distilled and not v:
                                    fh.write(f"\t{lb} {k:<10} -V-D\n")
                                elif distilled and not v:
                                    fh.write(
                                        f"\t{lb} {k:<10} -VxD\n"
                                        f"\t     {'':<8}    D {distilled}\n"
                                    )
                                elif not distilled and v:
                                    fh.write(
                                        f"\t{lb} {k:<10} xV-D\n"
                                        f"\t     {'':<8}    V {distilled}\n"
                                    )
                                metasStats[k][lb] += 1
                            else:
                                if distilled and v:
                                    lb = "xx"
                                    fh.write(
                                        f"\t{lb} {k:<10} ?V?D {v}\n"
                                        f"\t     {'':>8}    D {distilled}\n"
                                    )
                                    metasStats[k][lb] += 1
                                elif distilled and not v:
                                    if (
                                        k == "place"
                                        and distilled in PLACES
                                        or k == "author"
                                        and distilled in AUTHORS
                                    ):
                                        fh.write(f"\t{lb} {k:<10} -V=D {distilled}\n")
                                        metasStats[k][lb] += 1
                                    else:
                                        lb = "-+"
                                        fh.write(f"\t{lb} {k:<10} -V?D {distilled}\n")
                                        metasStats[k][lb] += 1
                                elif not distilled and v:
                                    lb = "+-"
                                    fh.write(f"\t{lb} {k:<10} ?V-D {v}\n")
                                    metasStats[k][lb] += 1
                                else:
                                    lb = "--"
                                    fh.write(f"\t{lb} {k:<10} -V-D\n")
                                    metasStats[k][lb] += 1
                        else:
                            fh.write(f"\t{lb} {k:<10} =V=D {v}\n")
                            metasStats[k][lb] += 1
                fh.write("\n")

        for k in META_KEY_ORDER:
            if k not in metasStats:
                continue
            print(f"\t\t{k}")
            labelInfo = metasStats[k]
            for label in sorted(labelInfo, key=lambda x: metasOrder[x]):
                print(f"\t\t\t{label}: {labelInfo[label]:>3} x {metasMap[label]}")

        for (label, infoSrc, fileName) in (
            ("PLACES", placeInfo, "places"),
            ("AUTHORS", authorInfo, "authors"),
        ):
            with open(f"{REP}/{fileName}.tsv", "w") as fh:
                print(f"\t{label}:")
                for category in sorted(infoSrc):
                    fh.write(f"\n{category}:\n\n")
                    categoryInfo = infoSrc[category]
                    amount = len(categoryInfo)
                    docs = set(chain.from_iterable(categoryInfo.values()))
                    print(
                        f"\t\t{category:<15}: {amount:>3} values"
                        f" in {len(docs):>3} documents"
                    )
                    for value in sorted(categoryInfo):
                        docs = categoryInfo[value]
                        docsRep = " ".join(docs[0:2])
                        fh.write(f"{value:<30}: {len(docs):>3}x : {docsRep}\n")

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


def doSplitPage(
    vol, doc, info, lastPageNum, i, body, lastIndex, b, lastHead, metadata, splits
):
    metadata = (
        metadata if i == 1 else distill(doc, info, lastHead, lastPageNum, force=True)
    )
    lastText = body[lastIndex:b]
    lastText = P_INTERRUPT_RE.sub(r"""\1""", lastText)
    lastText = P_JOIN_RE.sub(r"""\1\2""", lastText)

    page = f"p{lastPageNum:>04}"
    writeDoc(vol, page, metadata, lastText)
    splits.append((doc, f"{vol}:{page}", lastHead))


def splitDoc(doc, info):
    stage = 1
    (vol, startPage) = doc.split(":")
    path = f"{TRIM_DIR}{stage}/{doc.replace(':', '/')}.xml"
    with open(path) as fh:
        text = fh.read()

    match = HEADER_RE.match(text)
    header = match.group(0)
    metadata = {k: v for (k, v) in META_KV_2_RE.findall(header)}

    match = BODY_RE.search(text)
    body = match.group(1)

    lastPageNum = None
    lastHead = None
    lastIndex = 0
    splits = []

    i = -1

    for (i, match) in enumerate(SPLIT_DOC_RE.finditer(body)):
        pageNum = int(match.group(1))
        head = HI_CLEAN_STRONG_RE.sub(
            r"""\1""", match.group(2).replace("<lb/>", " ").replace("\n", " ")
        )
        if i == 0:
            lastPageNum = pageNum
            lastHead = head
            continue

        (b, e) = match.span()
        doSplitPage(
            vol,
            doc,
            info,
            lastPageNum,
            i,
            body,
            lastIndex,
            b,
            lastHead,
            metadata,
            splits,
        )
        lastPageNum = pageNum
        lastHead = head
        lastIndex = b

    i += 1
    if i > 0:
        b = None
        doSplitPage(
            vol,
            doc,
            info,
            lastPageNum,
            i,
            body,
            lastIndex,
            b,
            lastHead,
            metadata,
            splits,
        )

    return splits


def writeDoc(vol, pageNum, metadata, text):
    stage = 1
    header = "\n".join(
        f"""<meta key="{k}" value="{v}"/>""" for (k, v) in sorted(metadata.items())
    )
    header = f"<header>\n{header}\n</header>\n"
    body = f"<body>\n{text}\n</body>\n"

    with open(f"{TRIM_DIR}{stage}/{vol}/{pageNum:>04}.xml", "w") as fh:
        fh.write(f"<teiTrim>\n{header}{body}</teiTrim>")


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
        trimHeader(metaText, info)
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
    authorFull authorLevel1
    rawdate dateLevel1
    place localization_placeLevel1
    year witnessYearLevel1_from
    month witnessMonthLevel1_from
    day witnessDayLevel1_from
""".strip().split(
        "\n"
    )
)
META_KEY_IGNORE = set(
    """
        tocLevel
        volume
        witnessDayLevel1_to
        witnessMonthLevel1_to
        witnessYearLevel1_to
    """.strip().split()
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
        <interp>
            (.*?)
        </interp>
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


def trimHeader(text, info):
    origMetadata = {k: v for (k, v) in META_KV_RE.findall(text)}
    metadata = {
        META_KEY_TRANS[k]: transVal(v)
        for (k, v) in origMetadata.items()
        if k in META_KEY_TRANS
    }
    unknownMetadata = {
        k: v
        for (k, v) in origMetadata.items()
        if k not in META_KEYS and k not in META_KEY_IGNORE
    }

    doc = info["doc"]
    metasUnknown = info["metasUnknown"]
    if unknownMetadata:
        metasUnknown.append((doc, unknownMetadata))

    newText = "\n".join(
        f"""<meta key="{k}" value="{v}"/>""" for (k, v) in metadata.items()
    )

    return f"<header>\n{newText}\n</header>\n"


FIRST_PAGE_RE = re.compile(r"""<pb\b[^>]*?\bn="([^"]*)"[^>]*>""", re.S)


previousMeta = {}


def checkMeta(metaText, bodyText, info):
    doc = info["doc"]
    metasGood = info["metasGood"]
    metasDistilled = info["metasDistilled"]

    metadata = {k: v for (k, v) in META_KV_2_RE.findall(metaText)}
    metaGood = {k: metadata.get(k, "") for k in META_KEY_ORDER}
    if doc in FROM_PREVIOUS:
        for k in COLOFON_KEYS:
            metaGood[k] = previousMeta[k]
    metasGood.append((doc, metaGood))

    match = HEAD_RE.search(bodyText)
    head = HI_CLEAN_STRONG_RE.sub(
        r"""\1""", match.group(1).replace("<lb/>", " ").replace("\n", " ")
    )
    doc = info["doc"]
    info["heads"][doc] = head
    match = FIRST_PAGE_RE.search(bodyText)
    firstPage = match.group(1) if match else ""

    distilled = distill(doc, info, head, firstPage)
    metasDistilled[doc] = distilled

    metaResult = {}
    for (k, v) in metaGood.items():
        if v.startswith("!"):
            CORRECTION_FORBIDDEN.setdefault(doc, set()).add(k)
            v = v[1:]
        else:
            v = normVal(k, v, doc, info, "meta")
        metaResult[k] = v

        if doc not in FROM_PREVIOUS and (
            (
                k in ADD_META_KEYS
                or (doc in CORRECTION_ALLOWED and k in CORRECTION_ALLOWED[doc])
            )
            or (
                k in distilled
                and distilled[k]
                and not v
                and (
                    k == "place"
                    and distilled[k] in PLACES
                    or k == "author"
                    and distilled[k] in AUTHORS
                )
            )
        ):
            metaResult[k] = distilled[k]

    previousMeta.clear()
    for (k, v) in metaResult.items():
        previousMeta[k] = v

    newMeta = "\n".join(
        f"""<meta key="{k}" value="{v}"/>""" for (k, v) in metaResult.items()
    )

    return f"<header>\n{newMeta}\n</header>\n"


def numSanitize(match):
    return match.group(0).replace(" ", "")


AUTHOR_SANITY = tuple(
    entry[0:-1].split("=")
    for entry in """
antoniocaenenjoan=antonio caen en joan .
bijlage van ii=.
c astelijn=castelijn .
christoffelvan=christoffel van .
constant! jn=constantijn .
cornelisd'ableing=cornelis d'ableing .
cornelisspeelman=cornelis speelman .
d’ ableing=d'ableing .
dehaan=de haan .
dehaeze=de haeze .
devlaming=de vlaming .
dirckjansz=dirck jansz .
ferdin  and=ferdinand .
grcx)t=groot .
huysm  an=huysman .
j acob=jacob .
joanmaetsuycker=joan maetsuycker .
joh annes=johannes .
m attheus=mattheus .
maetsuy cker=maetsuycker .
maetsu yker=maetsuycker .
manuelbornezee=manuel bornezee .
mattheusde=mattheus de .
out  hoorn=outhoorn .
pi eter=pieter .
pietervan=pieter van .
ryckloffvan=ryckloff van .
raden van indië=raden_van_^indië .
saint martin=saint-martin .
salomonsweers=salomon sweers .
sibrantabbema=sibrant abbema .
zw aardecroon=zwaardecroon .
z w a ardecröon=zwaardecroon .
z w a ardecröon=zwaardecroon .
""".strip().split(
        "\n"
    )
)
AUTHOR_DEF = """
abbema      s

abraham     f

adam        f

adriaan     f

adriaen     f

aernout     f
    arnoud

alphen      s

antonio     f

anthonio    f
    anthonto

anthonisz   f

anthony     s
    antony

arent       f

arnold      f

artus       f

backer      s

balthasar   f

barendsz    s

becker      s

beecken     s
    beecke

bent        s

bergman     s

bernard     f

beveren     s

blom        s

bogaerde    s

bornezee    s

bort        s

both        s

broeckum    s

brouck      s

brouwer     s

burch       s

caen        s

caesar      s

camphuys    s
    camphuys]

carel       f
    cakel
    gabel

caron       s

carpentier  s

castelyn   s
    castelijn

chasteleyn  s
    chastelein

chavonnes   s2

christoffel f
    chistoffel

coen        s

comans      s

constantijn f

constantin  f
    constanten

cops        s

cornelis    f
    cornèlis

crijn       f

croocq      s

crudop      s

cunaeus     s

dam         s

&d'^ableing   s
    d'ableing
    d’ableing

de          i
    ue

dedel       s

demmer      s

den         i
    dex

der         i

diderik     f

diemen      s

dirk        f

dirck       f

dircq       f

dishoeck    s

douglas     s

dr          x

durven      s

dutecum     s

ewout       f

faes        s

ferdinand   f

françois    f
    erangois
    eranqois
    frangois
    franqois

frans       f

frederick   f
    erederick

frederik    f

gardenijs   s

gaspar      f

geleynsz    s1

gerard      f
    gekard
    gerarjd

gijsels     s

goens       s

gorcom      s

gouverneur-generaal s

groot       s

haan        s

haas        s

haeze       s

hans        f

hartsinck   s
    hartzinck
    harts1nck

hasselaar   s

hendrick    f

hendrik     f

henrick     f

henrik      f

herman      f

heussen     s

heuvel      s

hoorn       s

houtman     s

hulft       s
    hulet

hurdt       s

hustaert    s

huysman     s

isaac       f

jacob       f

jacobsz     sf

jacques     f

jan         f

jansz       fs
    janz

joachim     f

joan        f
    joajst
    jüan

joannes     f
    johannes

jochem      f

johan       f

jongh       s2

justus      f

laurens     f

leene       s

lijn        s
    letn

lucasz      s

lycochthon  s

maerten     f

maetsuycker s
    maetsuyker
    maetsijyker

manuel      f

marten      f
    makten

martinus    f

mattheus    f

meyde       s

mr          x

nicolaas    f

nicolaes    f

nieustadt   s

nobel       s

nuyts       s

ottens      s

outhoorn    s

oudtshoorn  s2

overtwater  s

padtbrugge  s

pasques     s1

paviljoen   s
    pavilioen

paulus      f

petrus      f

philips     f

philippus   f

phoonsen    s

pieter      f
    fieter
    p1eter

pietersz    f

pijl        s

pit         s

pits        s

putmans     s

quaelbergh  s

raden       s

raden_van_^indië s

raemburch   s

ranst       s

reael       s

reede       s

reniers     s

reyersz     s

reynst      s

rhee        s

riebeeck    s

rijn        s

robert      f

roelofsz    f
    roeloesz
    roeloeesz
    roeloffsz

roo         s

rooselaar   s

ryckloff    f
    rijckloff

saint-martin s
    saintmartin

salomon     f

samuel      f

sarcerius   s

schaghen    s

schouten    s

schram      s

sibrant     f
    sibrand

simon       f

sipman      s

six         s

slicher     s

sonck       s

speelman    s

steelant    s

stel        s

sterthemius s

steur       s

specx       s

sweers      s

swoll       s

teylingen   s

thedens     s
    the-dens

theodorus   f

thijsz      s
    thijsen

thomas      f

timmerman   s

tolling     s

twist       s

uffelen     s

valckenier  s

van         i
    vax
    vak

verburch    s
    verburech

versteghen  s

vlack       s

vlaming     s1
    vlam1ng
    vlameng

volger      s

vos         s

vuyst       s

welsing     s

wijbrant    f

wijngaerden s
    wijngaarden
    wungaerden

wilde       s

willem      f
    wilhem

winkelman   s

with        s

witsen      s

wollebrant  f

wouter      f

wybrand     f
    wijbrand
    wtjbrand
    wybrant

ysbrantsz   s
    ijsbrantsz

zwaardecroon    s
""".strip().split(
    "\n\n"
)


BRACKET_RE = re.compile(r"""\s*\([^)]*\)\s*""", re.S)

AUTHOR_VARIANTS = {}
AUTHOR_IGNORE = set()
AUTHORS = set()

for (i, nameInfo) in enumerate(AUTHOR_DEF):
    (main, *variants) = nameInfo.strip().split("\n")
    (intention, category) = main.split()
    replacement = intention if category == "i" else ucfirst(intention)
    if category == "x":
        AUTHOR_IGNORE.add(intention)
    else:
        AUTHOR_VARIANTS[intention] = (replacement, category)
        if category == "s":
            AUTHORS.add(replacement)
    for variant in variants:
        variant = variant.strip()
        if category == "x":
            AUTHOR_IGNORE.add(variant)
        else:
            AUTHOR_VARIANTS[variant] = (replacement, category)


EN_RE = re.compile(r""",?\s*\ben\b\s*""", re.S)


def normVal(k, val, doc, info, countLabel):
    val = val.strip()

    if k == "seq":
        return (
            val.replace("T", "I")
            .replace("m", "III")
            .replace("U", "II")
            .replace("H", "II")
            .replace("l", "I")
            .replace("i", "I")
            .replace("VIL", "VII")
            .replace("LIL", "LII")
            .replace("IH", "III")
            .replace(".", "")
            .replace(" ", "")
            .replace("A", "a")
        )

    if k == "rawdate":
        val = val.rstrip(".")
        val = NUM_SANITIZE_RE.sub(numSanitize, val)
        newVal = " ".join(MONTH_VARIANTS.get(w, w) for w in val.split())
        if "?" in newVal and "(?)" not in newVal:
            newVal = newVal.replace("?", " (?)")

        return newVal

    if k == "place":
        val = val.rstrip(".")
        val = val.replace(",", "")
        words = (w.lower() for w in val.split())
        casedWords = (
            PLACE_VARIANTS[word]
            if word in PLACE_VARIANTS
            else word
            if word in LOWERS
            else ucfirst(word, lower=True)
            for word in words
        )
        place = " ".join(casedWords)
        placeInfo = info["placeInfo"]
        if countLabel is not None:
            placeInfo[f"{countLabel}:{'found' if place else 'not-found'}"][
                place
            ].append(doc)
        return place

    if k in {"author", "authorFull"}:
        stripFirst = k == "author"

        val = val.rstrip(".")
        val = val.lower()
        val = BRACKET_RE.sub(" ", val)

        for (variant, intention) in AUTHOR_SANITY:
            val = val.replace(variant, intention)

        val = val.replace("[", "")
        val = val.replace("]", "")
        val = EN_RE.sub(" ", val)
        val = val.replace(",", " ")
        val = val.replace(".", " ")

        words = (w for w in val.split() if w not in AUTHOR_IGNORE)
        names = (
            AUTHOR_VARIANTS[word] if word in AUTHOR_VARIANTS else (word, "unknown")
            for word in words
        )

        authorInfo = info["authorInfo"]
        interpretedNames = []
        curName = []
        lastCat = None
        seenS1 = False
        seenS2 = False
        seenS = False
        seenFS = False
        seenSF = False

        for (name, cat) in names:
            if (
                cat == "unknown"
                or cat == "f"
                and lastCat != "f"
                or cat == "fs"
                and lastCat not in {"f", "i"}
                or cat == "i"
                and lastCat not in {"f", "fs", "i", "s1"}
                or cat == "s"
                and lastCat not in {"f", "fs", "i"}
                or cat == "s1"
                and lastCat not in {"f", "fs", "i"}
                or cat == "s2"
                and lastCat not in {"i", "s1"}
                or cat == "sf"
                and lastCat not in {"s", "s2"}
            ):
                if curName:
                    label = (
                        "no-surname"
                        if not seenS and not seenFS and not seenS1 and not seenS2
                        else "missing-s1"
                        if not seenS1 and seenS2
                        else "missing-s2"
                        if seenS1 and not seenS2
                        else "ok"
                    )
                    if seenS:
                        if stripFirst:
                            if seenFS:
                                curName.pop(0)
                            if seenSF:
                                curName.pop()
                    theName = makeName(curName)
                    if countLabel is not None:
                        authorInfo[f"{countLabel}:{label}"][theName].append(doc)
                    interpretedNames.append(theName)
                    curName = []
                if cat == "unknown":
                    theName = ucfirst(name)
                    if countLabel is not None:
                        authorInfo[f"{countLabel}:unkown"][theName].append(doc)
                    interpretedNames.append(theName)
                    seenS = False
                    seenS1 = False
                    seenS2 = False
                    seenFS = False
                    seenSF = False
                else:
                    if not stripFirst or cat != "f":
                        curName.append(name)
                    seenS = cat == "s"
                    seenS1 = cat == "s1"
                    seenS2 = cat == "s2"
                    seenFS = cat == "fs"
                    seenSF = cat == "sf"
            else:
                if not stripFirst or cat != "f":
                    curName.append(name)
                if cat == "s":
                    seenS = True
                elif cat == "s1":
                    seenS1 = True
                elif cat == "s2":
                    seenS2 = True
                elif cat == "fs":
                    seenFS = True
                elif cat == "sf":
                    seenSF = True

            lastCat = None if cat == "unknown" else cat

        if curName:
            label = (
                "no-surname"
                if not seenS and not seenS1 and not seenS2
                else "missing-s1"
                if not seenS1 and seenS2
                else "missing-s2"
                if seenS1 and not seenS2
                else "ok"
            )
            if seenS:
                if stripFirst:
                    if seenFS:
                        curName.pop(0)
                    if seenSF:
                        curName.pop()
            theName = makeName(curName)
            if countLabel is not None:
                authorInfo[f"{countLabel}:{label}"][theName].append(doc)
            interpretedNames.append(theName)

        return ",".join(interpretedNames)

    return val


UPPER_RE = re.compile(r"""\^(.)""", re.S)
LOWER_RE = re.compile(r"""&(.)""", re.S)


def upperRepl(match):
    return match.group(1).upper()


def lowerRepl(match):
    return match.group(1).lower()


def makeName(parts):
    name = " ".join(
        ucfirst(part) if i == 0 else part
        for (i, part) in enumerate(parts)
    )
    name = name.replace("_", " ")
    name = UPPER_RE.sub(upperRepl, name)
    name = LOWER_RE.sub(lowerRepl, name)
    return name


NOTEMARK_RE = re.compile(
    r"""
        \s*
        (?:
            (?:
                &[^;]*;
            )
            |
            [iJlx0-9*']
        )
        \)
    """,
    re.S | re.X,
)

TRAIL_RE = re.compile(r"""[ \n.,]+$""", re.S)
HEAD_REMOVE_RE = re.compile(
    r"""
        [ck]opie\.
        |geheim\.
        |secreet\.
    """,
    re.S | re.I | re.X,
)


def distill(doc, info, head, firstPage, force=False):
    metadata = dict(page=firstPage)

    source = head
    source = HEAD_REMOVE_RE.sub("", source)

    source = NOTEMARK_RE.sub("", source)

    specials = DISTIL_SPECIALS.get(doc, None)

    for k in ("seq", "rawdate", "place", "author"):
        source = TRAIL_RE.sub("", source)

        if specials and k in specials:
            (orig, special) = specials[k]
            source = source.replace(orig, "")
            thisVal = special
            if k == "author":
                kp = "authorFull"
                metadata[kp] = special
        else:
            detectRe = DETECT[k]
            match = detectRe.search(source)
            if match:
                v = match.group(1)
                if k == "seq":
                    v = v.replace(" ", "").replace("1", "I")
                source = detectRe.sub("", source, count=1)
            else:
                v = ""
            thisVal = normVal(k, v, doc, info, "dstl")
            if k == "author":
                kp = "authorFull"
                metadata[kp] = normVal(kp, v, doc, info, "dstl")
        metadata[k] = thisVal

        if k == "rawdate":
            datePure = thisVal.replace(" en ", "_en_").replace(" (?)", "")
            datePure = normVal(k, datePure, doc, info, None)

            parts = datePure.split()
            if len(parts) == 3:
                (day, month, year) = parts
                month = MONTH_NUM[month]
                metadata["day"] = day.split("_")[0]
                metadata["month"] = str(month)
                metadata["year"] = year
            else:
                metadata["day"] = ""
                metadata["month"] = ""
                metadata["year"] = ""

    return {k: f"!{v}" for (k, v) in metadata.items()} if force else metadata


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
        \ resp="int_paragraph_joining"
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
