import sys
import os
import collections
import re
from itertools import chain

import yaml
import xml.etree.ElementTree as ET


def parseArgs(args):
    vol = None
    lid = None

    kwargs = {}
    pargs = []

    good = True

    for arg in args:
        if arg.isdigit() or '-' in arg:
            if '-' in arg:
                (b, e) = arg.split('-', 1)
                if b.isdigit() and e.isdigit():
                    values = set(range(int(b), int(e) + 1))
                else:
                    print(f"Unrecognized argument `{arg}`")
                    good = False
                    continue
            else:
                values = {int(arg)}
            if vol is None:
                vol = values
            elif lid is None:
                lid = values
        else:
            kv = arg.split("=", 1)
            if len(kv) == 1:
                pargs.append(arg)
            else:
                (k, v) = kv
                if k == "orig":
                    v = set(v.split(","))
                kwargs[k] = v

    if vol is not None:
        vol = {f"{i:>02}" for i in vol}
    if lid is not None:
        lid = {f"p{i:>04}" for i in lid}

    return (good, vol, lid, kwargs, pargs)


def ucfirst(x, lower=True):
    return (x[0].upper() + (x[1:].lower() if lower else x[1:])) if x else x


def longestFirst(x):
    return -len(x)


def applyCorrections(corrections, doc, text):
    if doc in corrections:
        for (correctRe, correctRepl) in corrections[doc]:
            (text, n) = correctRe.subn(correctRepl, text)
            if n == 0:
                print(text)
                print(f"\tCORRECTION {doc} {correctRe.pattern} did not apply")
            elif n > 1:
                print(text)
                print(f"\tCORRECTION {doc} {correctRe.pattern} applied {n} times")
    return text


# SOURCE CORRECTIONS

CORRECTIONS = {
    "01:p0203": ((re.compile(r"""(<p\ rend="font-size:)\ 8\.5;""", re.S), r"\1 12;"),),
    "01:p0663": ((re.compile(r""">\(1\) Dirck""", re.S), r">1) Dirck"),),
    "02:p0480": ((re.compile(r"""<p\b[^>]*>p\.r cento<lb/>\s*</p>\s*""", re.S), r""),),
    "04:p0496": ((re.compile(r"""I( en 9 maart 1683)""", re.S), r"""1\1"""),),
    "05:p0439": ((re.compile(r"""<p\b[^>]*>i<lb/>\s*</p>\s*""", re.S), r""),),
    "05:p0779": (
        (
            re.compile(
                r"""
                    (
                        <pb\ n="793"[^>]*>
                        \s*
                        <fw\b[^>]*>[^<]*</fw>
                        \s*
                    )
                    <note\b[^>]*>(.*?)</note>
                """,
                re.S | re.X,
            ),
            r"\1<p>\2</p>",
        ),
    ),
    "06:p0844": (
        (
            re.compile(
                r"""
                    <p\b[^>]*>([^<]*)<lb/>\s*</p>
                    (
                        \s*
                        <pb\ n="894"[^>]*>
                    )
                """,
                re.S | re.X,
            ),
            r"<note>\1</note>\2",
        ),
    ),
    "07:p0003": ((re.compile(r"""(<head\b[^>]*>)(CHRIS)""", re.S), r"""\1I. \2"""),),
    "07:p0660": ((re.compile(r"""(<head\b[^>]*>XX)L""", re.S), r"""\1II"""),),
    "09:p0233": (
        (
            re.compile(
                r"""
                    <head\b[^>]*>
                        [^<]*
                        <lb/>
                        \s*
                    </head>
                    \s*
                    <p\b[^>]*>
                        [^<]*
                        <lb/>
                        \s*
                    </p>
                    \s*
                    <fw\b[^>]*>
                        [^<]*
                    </fw>
                    \s*
                    (<pb\ n="254")
                """,
                re.S | re.X,
            ),
            r"\1",
        ),
    ),
    "10:p0857": ((re.compile(r"""decem¬ber""", re.S), r"""december"""),),
    "10:p0749": (
        (
            re.compile(
                r"""(<pb n="799"[^>]*>\s*<fw\b[^>]*>.*?</fw>\s*)(</p>\s*)""", re.S
            ),
            r"""\2\1""",
        ),
        (
            re.compile(
                r"""(<pb n="997"[^>]*>\s*<fw\b[^>]*>.*?</fw>\s*)(</p>\s*)""", re.S
            ),
            r"""\2\1""",
        ),
    ),
    "11:p0226": (
        (re.compile(r"""\((niet getekend wegens ziekte)\]""", re.S), r"""(\1)"""),
    ),
}


CORRECTION_ALLOWED = {
    "01:p0004": {"author"},
    "01:p0007": {"place", "title"},
    "01:p0018": {"title"},
    "01:p0056": {"title"},
    "01:p0105": {"place", "author", "title"},
    "01:p0106": {"author", "title"},
    "01:p0121": {"author", "title"},
    "01:p0129": {"author"},
    "01:p0247": {"author"},
    "01:p0302": {"place", "author", "title"},
    "01:p0433": {"place", "author", "title"},
    "01:p0482": {"place", "author", "title"},
    "01:p0152": {"rawdate", "day", "month", "year", "title"},
    "02:p0311": {"author", "title"},
    "03:p0192": {"rawdate", "day", "title"},
    "04:p0241": {"rawdate", "day", "title"},
    "04:p0493": {"author"},
    "04:p0496": {"month", "title"},
    "06:p0065": {"author"},
    "06:p0275": {"author"},
    "06:p0402": {"author"},
    "06:p0406": {"author", "title"},
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
    "07:p0746": {"rawdate", "day", "author", "title"},
    "07:p0754": {"author"},
    "08:p0128": {"author"},
    "08:p0224": {"author"},
    "08:p0234": {"rawdate", "day", "title"},
    "08:p0235": {"seq"},
    "09:p0070": {"rawdate", "day", "month", "year"},
    "09:p0344": {"seq", "rawdate", "day", "month", "year", "author", "title"},
    "09:p0628": {"seq", "rawdate", "day", "month", "year", "author", "title"},
    "10:p0087": {"author"},
    "10:p0297": {"rawdate", "day", "month", "year"},
    "10:p0399": {"rawdate", "day", "month", "year"},
    "11:p0224": {"seq"},
    "11:p0226": {"author"},
    "12:p0001": {"author"},
    "12:p0003": {"author"},
    "12:p0083": {"author"},
    "12:p0183": {"author"},
    "13:p0340": {"author"},
    "13:p0362": {"author"},
    "13:p0626": {"author", "title"},
}
CORRECTION_FORBIDDEN = {
    "01:p0008": {"place"},
    "01:p0087": {"place"},
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

TITLE_REST = {
    "zonder plaats datum": dict(place="zonder plaats", rawdate="zonder datum"),
    "ongedateerd zonder plaats": dict(place="zonder plaats", rawdate="zonder datum"),
    "het cachet van die door ziekte niet zelf kon tekenen": {},
    "zonder datum 1729": {},
}
TITLE_BRACKETS = {
    f"({x.strip()})"
    for x in """
  EN de GEASSUMEERDE RADEN
  niet getekend wegens ziekte
  vermoedelijk 30 november
        """.strip().split(
        "\n"
    )
}
DISTILL_SPECIALS = {
    "13:p0626": dict(
        title="Bijlage ladinglijst van twaalf retourschepen vertrokken op 15 en 30 oktober, 6 november 1760, 19 januari en 25 april 1761",
        rawdate="25 april 1761",
        place="Batavia",
        author="",
        authorFull="",
        rest="",
    )
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
    decem¬ber

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
    for abb in (intention, intention[0:3], intention[0:4]):
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
    sorted(
        set(re.escape(mv) for mv in chain(MONTH_NUM, MONTH_VARIANTS)), key=longestFirst
    )
)

PLACE_DEF = """
Afrika

Amboina

Amsterdam

Banda-Neira
    bandaneira
    banda-neira
    banda

Bantam

Batavia
    ratavia
    ba¬tavia

Deventer

Fort
    eort

Hoek

Hollandia

Jakatra

Kasteel

Makéan

Maleyo

Mauritius

Nassau

_
    neira

Ngofakiaha

Nieuw

Nieuw Hollandia
    nieuw-hollandia

Rede

Schip

Straat

Sunda

Ternate

Utrecht

Vere

Vlakke

Wapen

Wesel

""".strip().split(
    "\n\n"
)

PLACE_LOWERS = set(
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

PLACE_VARIANTS = {}
PLACES_LOWER = set()

for (i, nameInfo) in enumerate(PLACE_DEF):
    (intention, *variants) = nameInfo.strip().split()
    if intention == "_":
        intention = ""
    else:
        PLACES_LOWER.add(intention.lower())
        PLACE_VARIANTS[intention] = intention
        PLACE_VARIANTS[intention.lower()] = intention
    for variant in variants:
        PLACE_VARIANTS[variant] = intention


PLACE_DETECT_PAT = "|".join(
    sorted(set(re.escape(mv) for mv in chain(PLACE_VARIANTS)), key=longestFirst)
)

LOWERS_PAT = "|".join(
    sorted(set(re.escape(mv) for mv in PLACE_LOWERS), key=longestFirst)
)


DETECT_STATUS_RE = re.compile(
    r"""
        \(?
        (
            [ck]opie
            |geheim
            |secreet
        )
        \.?
        \)?
        \.?
    """,
    re.S | re.I | re.X,
)
DETECT_AUTHOR_RE = re.compile(
    r"""
        ^
        \s*
        (.*)?
        \s*
        $
    """,
    re.S | re.X,
)
DETECT_SEQ_RE = re.compile(
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
)
DETECT_DATE_RE = re.compile(
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
            \s*
            1
            \s*
            [6-8]
            \s*
            [0-9]
            \s*
            [0-9]
            \s*
            (?:
                \?
                |
                \s*\(\?\)
            )?
        )
        \s*
        \)?
        \s*
        \.?
        \s*
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
                (?:
                    \?
                    |
                    \s*\(\?\)
                )?
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
        fr"""
        (
            (?:
                \b
                (?: {PLACE_DETECT_PAT} | {LOWERS_PAT})
                \b
                [ .,]*
            )*
            (?:
                \b
                (?: {PLACE_DETECT_PAT} )
                \b
                [ .,]*
            )
            (?:
                \b
                (?: {PLACE_DETECT_PAT} | {LOWERS_PAT})
                \b
                [ .,]*
            )*
        )
        """,
        re.S | re.I | re.X,
    ),
    author=DETECT_AUTHOR_RE,
    authorFull=DETECT_AUTHOR_RE,
)

NUM_SANITIZE_RE = re.compile(r"""[0-9][0-9 ]*[0-9]""", re.S)


def numSanitize(match):
    return f" {match.group(0).replace(' ', '')} "


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
XML_DIR = f"{REPO_DIR}/xml"

LAST_STAGE = 3

TF_DIR = f"{REPO_DIR}/tf"
OUT_DIR = f"{TF_DIR}/{VERSION_TF}"

MERGE_DOCS = {
    "06:p0406": ("06:p0407",),
}
SKIP_DOCS = {x for x in chain.from_iterable(MERGE_DOCS.values())}

HI_CLEAN_STRONG_RE = re.compile(r"""<hi\b[^>]*>([^<]*)</hi>""", re.S)

# FILESYSTEM OPERATIONS


def docSummary(docs):
    nDocs = len(docs)
    rep = "  0x" if not nDocs else f"  1x {docs[0]}" if nDocs == 1 else ""
    if not rep:
        examples = " ".join(docs[0:2])
        rest = " ..." if nDocs > 2 else ""
        rep = f"{nDocs:>3}x {examples}{rest}"
    return f"{rep:<30}"


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


def initTree(path, fresh=False):
    exists = os.path.exists(path)
    if fresh:
        if exists:
            clearTree(path)

    if not exists:
        os.makedirs(path, exist_ok=True)


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
    SRC = IN_DIR if stage == 0 else f"{TRIM_DIR}{stage - 1}"
    DST = XML_DIR if stage == LAST_STAGE else f"{TRIM_DIR}{stage}"
    REP = f"{REPORT_DIR}{stage}"
    initTree(REP)

    volumes = getVolumes(SRC)

    analysis = collections.Counter()
    analysisAfter = collections.Counter()

    info = dict(
        table=0,
        docs=[],
        metas=0,
        metasUnknown=[],
        metasDistilled=collections.defaultdict(dict),
        nameDiag=collections.defaultdict(
            lambda: collections.defaultdict(lambda: collections.defaultdict(list))
        ),
        metaValues=collections.defaultdict(
            lambda: collections.defaultdict(lambda: collections.defaultdict(list))
        ),
        metaDiag=collections.defaultdict(dict),
        captionInfo=collections.defaultdict(list),
        captionNorm=collections.defaultdict(list),
        captionVariant=collections.defaultdict(list),
        captionRoman=collections.defaultdict(list),
        folioResult=collections.defaultdict(list),
        folioTrue=collections.defaultdict(list),
        folioFalse=collections.defaultdict(list),
        folioUndecided=collections.defaultdict(lambda: collections.defaultdict(list)),
        headInfo=collections.defaultdict(list),
        remarks=collections.Counter(),
        remarkInfo=collections.defaultdict(lambda: collections.defaultdict(list)),
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
        initTree(thisDstDir, fresh=True)
        initTree(f"{thisDstDir}{rest}", fresh=True)

        info["vol"] = vol
        idMap = {} if stage == 0 else None
        letters = getLetters(thisSrcDir, idMap=idMap)

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
                text = applyCorrections(CORRECTIONS, doc, text)

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

        print("SPLITS:")
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
            for (doc, head) in shortHeads:
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
        remarkInfo = info["remarks"]

        print("REMARKS:")
        for (label, amount) in remarkInfo.items():
            print(f"\t{label:<5}: {amount:>5} generated")

        nameDiag = info["nameDiag"]
        metaValues = info["metaValues"]
        metaDiag = info["metaDiag"]
        metaStats = collections.defaultdict(collections.Counter)
        nameStats = collections.Counter()

        heads = info["heads"]
        metas = info["metas"]
        print("METADATA:")
        print(f"\t{metas:>3} docs with metadata")

        for (k, labelInfo) in nameDiag.items():
            with open(f"{REP}/meta-{k}-diag.txt", "w") as fh:
                for label in sorted(labelInfo):
                    fh.write(f"{label}------------------\n")
                    nameInfo = labelInfo[label]
                    for name in sorted(nameInfo):
                        docs = nameInfo[name]
                        docRep = docSummary(docs)
                        fh.write(f"{docRep} {name}\n")
                        if k == "authorFull":
                            nameStats[label] += len(docs)
        print("\t\tNAMES:")
        for label in sorted(nameStats):
            print(f"\t\t\t\t{label:<4}: {nameStats[label]:>3}x")

        fh = {}
        for kind in sorted(metaValues):
            keyInfo = metaValues[kind]
            for (k, valInfo) in keyInfo.items():
                if kind in fh:
                    thisFh = fh[k]
                else:
                    thisFh = fh.get(k, open(f"{REP}/meta-{k}-values.txt", "w"))
                    fh[k] = thisFh
                thisFh.write(f"{kind}\n---------------\n")
                for val in sorted(valInfo):
                    docs = valInfo[val]
                    docRep = docSummary(docs)
                    thisFh.write(f"{docRep} {val}\n")

        for thisFh in fh.values():
            thisFh.close()

        with open(f"{REP}/metaDiagnostics.txt", "w") as fh:
            for doc in sorted(metaDiag):
                fh.write(f"{doc}\n")
                fh.write(f"{heads[doc]}\n")

                keyInfo = metaDiag[doc]
                for k in META_KEY_ORDER + EXTRA_META_KEYS:
                    if k not in keyInfo:
                        continue
                    (lb, ov, v, d) = keyInfo[k]
                    metaStats[k][lb] += 1
                    lines = []
                    if v == d:
                        if ov != v:
                            lines.append(f"OD= {ov}")
                        lines.append(f"VD= {v}")
                    elif v and not d:
                        if ov != v:
                            lines.append(f"O = {ov}")
                        lines.append(f"V = {v}")
                    elif not v and d:
                        lines.append(f" D= {d}")
                    else:
                        if ov != v:
                            lines.append(f"O = {ov}")
                        lines.append(f"V = {v}")
                        lines.append(f" D= {d}")
                    fh.write(f"{lb} {k:<10} ={lines[0]}\n")
                    for line in lines[1:]:
                        fh.write(f"{lb} {'':<10} ={line}\n")
                fh.write("\n")

        for k in META_KEY_ORDER + EXTRA_META_KEYS:
            if k == "pid" or k in DERIVED_META_KEYS or k not in metaStats:
                continue
            print(f"\t\t{k}")
            labelInfo = metaStats[k]
            for label in sorted(labelInfo):
                print(f"\t\t\t\t{label:<4}: {labelInfo[label]:>3}x")

        with open(f"{REP}/heads.tsv", "w") as fh:
            for (doc, head) in heads.items():
                fh.write(f"{doc} {head}\n")

    elif stage == 3:
        print("REMARKS:\n")
        remarkInfo = info["remarkInfo"]
        totalPatterns = 0
        totalRemarks = 0
        with open(f"{REP}/remarks.tsv", "w") as fh:
            for (label, legend) in LEGEND.items():
                thisRemarkInfo = remarkInfo.get(label, {})

                nPatterns = len(thisRemarkInfo)
                nRemarks = sum(len(x) for x in thisRemarkInfo.values())
                if label not in {"m", "1", "F", "L", "0"}:
                    totalPatterns += nPatterns
                    totalRemarks += nRemarks

                msg = f"{label}: {nPatterns:>5} " f"in {nRemarks:>5} x {legend}"
                print(f"\t{msg}")
                fh.write(f"\n-------------------\n{msg}\n\n")

                for (summary, docs) in sorted(thisRemarkInfo.items(), key=byOcc):
                    fh.write(f"{summary} {docSummary(docs).rstrip()}\n")

            msg = f"T: {totalPatterns:>5} " f"in {totalRemarks:>5} x in total"
            print(f"\t{msg}")
    return True


LEGEND = {
    "<": "continuing remark without previous remark on preceding page",
    ">": "to-be-continued remark without next remark on following page",
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


def byOcc(x):
    (summary, docs) = x
    return (docs[0], summary) if docs else ("", summary)


SPLIT_DOC_RE = re.compile(
    r"""
        <pb\b[^>]*?\bn="([0-9]+)"[^>]*>
        \s*
        (?:
            <pb\b[^>]*>\s*
        )*
        (?:
            <p\b[^>]*>.*?</p>
            \s*
        )?
        <head\b[^>]*>(.*?)</head>
    """,
    re.S | re.X,
)
HEADER_RE = re.compile(r"""^.*?</header>\s*""", re.S)


def splitPage(
    dst, vol, doc, info, lastPageNum, i, body, lastIndex, b, lastHead, metadata, splits
):
    page = f"p{lastPageNum:>04}"
    sDoc = f"{vol}:{page}"

    if i > 1:
        metadata = distillHead(sDoc, info, lastHead, force=True)
        metadata["page"] = lastPageNum
    lastText = body[lastIndex:b]
    lastText = P_INTERRUPT_RE.sub(r"""\1""", lastText)
    lastText = P_JOIN_RE.sub(r"""\1\2""", lastText)

    writeDoc(dst, vol, page, metadata, lastText)
    splits.append((doc, sDoc, lastHead))


def splitDoc(doc, info):
    (vol, startPage) = doc.split(":")
    stage = 1
    DST = XML_DIR if stage == LAST_STAGE else f"{TRIM_DIR}{stage}"
    path = f"{DST}/{doc.replace(':', '/')}.xml"
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
        splitPage(
            DST,
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
        splitPage(
            DST,
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


def writeDoc(dst, vol, pageNum, metadata, text):
    header = "\n".join(
        f"""<meta key="{k}" value="{v}"/>""" for (k, v) in sorted(metadata.items())
    )
    header = f"<header>\n{header}\n</header>\n"
    body = f"<body>\n{text}\n</body>\n"

    with open(f"{dst}/{vol}/{pageNum:>04}.xml", "w") as fh:
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

    DST = XML_DIR if stage == LAST_STAGE else f"{TRIM_DIR}{stage}"

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
                path = f"{DST}/{vol}/rest/{fileName}"
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
    status titleLevel1
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

META_KEY_NO_TRANS = {"authorFull", "status"}

META_KEY_IGNORE = set(
    """
        tocLevel
        volume
        witnessDayLevel1_to
        witnessMonthLevel1_to
        witnessYearLevel1_to
    """.strip().split()
)

META_KEY_TRANS = {
    old: new for (new, old) in META_KEY_TRANS_DEF if new not in META_KEY_NO_TRANS
}
META_KEY_ORDER = tuple(x[0] for x in META_KEY_TRANS_DEF)
COLOFON_KEYS = META_KEY_ORDER[5:]
META_KEYS = {x[1] for x in META_KEY_TRANS_DEF}

ADD_META_KEYS = {"authorFull", "status"}

EXTRA_META_KEYS = ("brackets", "rest")

DERIVED_META_KEYS = set(
    """
    day
    month
    year
    authorFull
""".strip().split()
)

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


def roughlyEqual(v, d, lax=False):
    # print("RE v", v)
    # print("RE d", d)
    vWords = set(SEP_RE.sub(" ", v.lower()).split())
    dWords = set(SEP_RE.sub(" ", d.lower()).split())

    if lax:
        vWords = vWords - PLACES_LOWER - AUTHORS_LOWER
        dWords = dWords - PLACES_LOWER - AUTHORS_LOWER

    return vWords == dWords


AUTHOR_SANITY = tuple(
    entry[0:-1].split("=")
    for entry in """
adri aan=adriaan .
adriaan denijs=adriaan de nijs .
albertusvan=albertus van .
andreasvan=andreas van .
antoniocaenenjoan=antonio caen en joan .
ba yen=bayen .
baer- le=baerle .
bijlage van ii=.
c astelijn=castelijn .
christi aan=christiaan .
christoffelvan=christoffel van .
cluysenaaren=cluysenaar en .
constant! jn=constantijn .
cornelisd'ableing=cornelis d'ableing .
cornelisspeelman=cornelis speelman .
d’ ableing=d'ableing .
daniëlnolthenius=daniël nolthenius .
dehaan=de haan .
dehaeze=de haeze .
derparra=der parra .
derwaeyen=der waeyen .
devlaming=de vlaming .
dirckjansz=dirck jansz .
dithardvan=dithard van .
eli as=elias .
enelias=en elias .
enjan=en jan .
enjeremias=en jeremias .
enmaurits=en maurits .
ferdin and=ferdinand .
gideonloten=gideon loten .
grcx)t=groot .
gusta af=gustaaf .
het cachet van=het_cachet_van .
huijbertwillem=huijbert willem .
huysm an=huysman .
isa ac=isaac .
j acob=jacob .
janelias=jan elias .
jo an=joan .
joanmaetsuycker=joan maetsuycker .
joh annes=johannes .
johannesthedens=johannes thedens .
juliuscoyett=julius coyett .
juliusvalentijn=julius valentijn .
librechthooreman=librecht hooreman .
m attheus=mattheus .
mac are=macaré
maetsuy cker=maetsuycker .
maetsu yker=maetsuycker .
manuelbornezee=manuel bornezee .
mattheuscluysenaar=mattheus cluysenaar .
mattheusde=mattheus de .
noltheniusen=nolthenius en .
out hoorn=outhoorn .
pi eter=pieter .
pietervan=pieter van .
rochuspasques=rochus pasques .
ryckloffvan=ryckloff van .
raden van indië=raden_van_^indië .
saint martin=saint-martin .
salomonsweers=salomon sweers .
sibrantabbema=sibrant abbema .
steijnvan=steijn van .
steunvan=steun van .
thomasvan=thomas van .
vanbazel=van bazel .
vanbroyel=van broyel .
vander=van der .
vanhohendorf=van hohendorf .
vanrheede=van rheede .
vanriemsdijk=van riemsdijk .
vanspreekens=van spreekens .
willemvan=willem van .
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

aerden      s

aernout     f
    arnoud

albert      f

albertus    f

alphen      s

andreas     f

antonio     f

anthonio    f
    anthonto

anthonisz   f

anthony     f
    antony

arent       f

arend       f

arnold      f

arrewijne   s

artus       f

backer      s

baerle      s

balthasar   f

barendsz    s

bayen       s

bazel       s

becker      s

beecken     s
    beecke

bent        s

berendregt  s
    beren-dregt

bergman     s

bernard     fs

beveren     s

blom        s

bogaerde    s

bornezee    s

bort        s

bosch       s

both        s

broeckum    s

brouck      s

brouwer     s

broyel      s

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
    cha-vonnes

christiaan  f

christoffel f
    chistoffel

cloon       s

cluysenaar  s

coen        s

comans      s

constantijn f

constantin  f
    constanten

cops        s

cornelis    f
    cornèlis
    cornel1s

coyett      s

crijn       f

croocq      s

crudop      s

crul       s

cunaeus     s

dam         s

&d'^ableing   s
    d'ableing
    d’ableing

daniël      f

de          i
    ue

dedel       s

demmer      s

den         i
    dex

der         i

diderik     f
    d1derik
    dider1k

diemen      s

dirk        f

dirck       f

dircq       f

dishoeck    s

dithard     f

douglas     s

dr          x

dubbeldekop s
    dubbeldecop

duquesne    s

durven      s

dutecum     s

elias       fs

everard     f

ewout       f

faes        s

ferdinand   f

françois    f
    erangois
    eranqois
    frangois
    franqois
    fran^ois
    francois
    fran£ois

frans       f

frederick   f
    erederick

frederik    f

gabry       s

galenus     f

gardenijs   s

gaspar      f

geleynsz    s1

gerard      f
    gekard
    gerarjd

gideon      f

gijsbertus  f

gijsels     s

goens       s

gollenesse  s
    gol-lenesse
    golle-nesse

gorcom      s

gouverneur-generaal s

groot       s

guillot     s

gualterus   f

gustaaf     f

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
    hendri

hendrix     s

henrick     f

henrik      f

herman      f

heussen     s

heuvel      s

heyningen   s

hohendorf   s

hooreman    s

hoorn       s

houtman     s

hugo        f

huijbert    f
    huij-bert

hulft       s
    hulet

hurdt       s

hustaert    s

huyghens    s

huysman     s

imhoff      s

isaac       f

jacob       f

jacobsz     sf

jacques     f

jan         f

jansz       fs
    janz

jeremias    f

joachim     f

joan        f
    joajst
    jüan

joannes     f
    johannes

jochem      f

johan       f

jongh       s2

josua       f

julius      f

jurgen      f
    jur-gen

justus      f

klerk       s

lakeman     s
    lake-man

laurens     f

leene       s

librecht    f

lijn        s
    letn

loten       s

lucasz      s

lycochthon  s

maas        s

macaré      s
    macare
    macar

maerten     f

maetsuycker s
    maetsuyker
    maetsijyker

manuel      f

marten      f
    makten

martinus    f

mattheus    f
    mat-theus

maurits     f

mersen      s

meyde       s

michiel     f

mijlendonk  s

mossel      s

mr          x

nicolaas    f
    nico-laas

nicolaes    f

nieustadt   s

nijs        s

nobel       s

nolthenius  s

nuyts       s

oostwalt    s

ottens      s

outhoorn    s

oudtshoorn  s2

overbeek    s
    over-beek

overtwater  s

padtbrugge  s

parra       s

pasques     s1
    pas-ques
    pasoues

patras      s

paviljoen   s
    pavilioen

paul        f

paulus      f

petrus      f

philips     f

philippus   f

phoonsen    s

pielat      s

pieter      f
    fieter
    p1eter
    pie-ter

pietersz    f

pijl        s

pit         s

pits        s

putmans     s

quaelbergh  s

raden       s

raden_van_^indië s

raemburch   s
    raemsburch

ranst       s

reael       s

reede       s

reniers     s

reyersz     s

reynier     f

reynst      s

rhee        s

rheede      s

riebeeck    s

riemsdijk   s
    riems¬dijk

rijn        s

robert      f

rochus      f

roelofsz    f
    roeloesz
    roeloeesz
    roeloffsz

rogier      f

roo         s

rooselaar   s

ryckloff    f
    rijckloff

saint-martin s
    saintmartin

salomon     f

samuel      f

sarcerius   s

sautijn     s

schaghen    s

schinne     s

schooten    s

schouten    s

schram      s

schreuder   s

schuer      s

schuylenburg s

sibrant     f
    sibrand

sichterman  s

simon       f

sipman      s

six         s

slicher     s

sonck       s

spar        s

specx       s

speelman    s

spreekens   s

steelant    s

steijn      f
    steun

stel        s

stephanus   f

sterthemius s

steur       s

suchtelen   s
    suchte-len

sweers      s

swoll       s

teylingen   s

thedens     s
    the-dens

theling     s

theodorus   f

thijsz      s
    thijsen

thomas      f

timmerman   s

tolling     s

twist       s

uffelen     s

valckenier  s

valentijn   f

van         i
    vax
    vak

velde       s

verburch    s
    verburech

verijssel   s

versluys    s

versteghen  s

vlack       s

vlaming     s1
    vlam1ng
    vlameng

volger      s

vos         s

vuyst       s

waeyen      s

welsing     s

westpalm    s

wijbrant    f

wijngaerden s
    wijngaarden
    wungaerden

wilde       s

willem      f
    wilhem
    wil¬lem

winkelman   s

with        s

witsen      s

witte       s

wollebrant  f

wouter      f

wouters     s

wybrand     f
    wijbrand
    wtjbrand
    wybrant
    w1jbrant

ysbrantsz   s
    ijsbrantsz

zwaardecroon    s
""".strip().split(
    "\n\n"
)


BRACKET_RE = re.compile(r"""\s*\([^)]*\)\s*""", re.S)

AUTHOR_VARIANTS = {}
AUTHOR_IGNORE = set()
AUTHORS_LOWER = set()

for (i, nameInfo) in enumerate(AUTHOR_DEF):
    (main, *variants) = nameInfo.strip().split("\n")
    (intention, category) = main.split()
    replacement = intention if category == "i" else ucfirst(intention)

    if category == "x":
        AUTHOR_IGNORE.add(intention)

    AUTHOR_VARIANTS[intention] = (replacement, category)

    if category in {"s", "fs"}:
        AUTHORS_LOWER.add(replacement.lower())

    for variant in variants:
        variant = variant.strip()
        if category == "x":
            AUTHOR_IGNORE.add(variant)
        AUTHOR_VARIANTS[variant] = (replacement, category)


EN_RE = re.compile(r""",?\s*\ben\b\s*,?""", re.S | re.I)

UPPER_RE = re.compile(r"""\^(.)""", re.S)
LOWER_RE = re.compile(r"""&(.)""", re.S)


def upperRepl(match):
    return match.group(1).upper()


def lowerRepl(match):
    return match.group(1).lower()


def makeName(parts):
    name = " ".join(ucfirst(part) if i == 0 else part for (i, part) in enumerate(parts))
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
            [iJlx0-9*'!]
        )
        \)
    """,
    re.S | re.X,
)

SEP_RE = re.compile(r"""[ \n.,;]+""", re.S)


def distillSeq(source):
    match = DETECT_SEQ_RE.search(source)
    if match:
        v = match.group(1)
        v = v.replace(" ", "").replace("1", "I")
        rest = DETECT_SEQ_RE.sub("", source, count=1)
    else:
        v = ""
        rest = source

    v = (
        v.replace("T", "I")
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
    return (v, rest)


UNCERTAIN_RE = re.compile(r"""\s*\(?(\?)\)?\s*""", re.S)


def distillDate(source):
    match = DETECT_DATE_RE.search(source)
    if match:
        v = match.group(1)
        source = DETECT_DATE_RE.sub("", source, count=1)
        v = v.rstrip(".")
        v = NUM_SANITIZE_RE.sub(numSanitize, v)
        v = " ".join(MONTH_VARIANTS.get(w.rstrip("."), w) for w in v.split())
        v = UNCERTAIN_RE.sub(r""" \1""", v)
        if "(?)" in v:
            v = v.replace("(?)", "?")
    else:
        v = ""

    return (v, source)


def distillPlace(source):
    inWords = source.split()
    valWords = []
    outWords = []
    placeCandidate = []
    isPlace = False

    for word in inWords:
        wordL = word.lower()
        if placeCandidate is None:
            outWords.append(word)
        elif wordL in PLACE_VARIANTS:
            placeCandidate.append(PLACE_VARIANTS[wordL])
            isPlace = True
        elif wordL in PLACE_LOWERS:
            placeCandidate.append(wordL)
        else:
            if placeCandidate:
                if isPlace:
                    valWords.extend(placeCandidate)
                    placeCandidate = None
                else:
                    outWords.extend(placeCandidate)
                    placeCandidate = []
            outWords.append(word)

    if placeCandidate:
        if isPlace:
            valWords.extend(placeCandidate)
        else:
            outWords.extend(placeCandidate)

    return (" ".join(valWords), " ".join(outWords))


def distillAuthor(source, shortIn=False, shortOut=False):
    inWords = source.split()
    valWords = []
    outWords = []

    for word in inWords:
        wordL = word.lower()
        if wordL in AUTHOR_VARIANTS:
            valWords.append(AUTHOR_VARIANTS[wordL])
        else:
            outWords.append(word)

    interpretedNames = []

    curName = []
    lastCat = None
    seenS1 = False
    seenS2 = False
    seenS = False
    seenFS = False
    seenSF = False

    def addName():
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
                if shortOut and not shortIn:
                    if seenFS:
                        curName.pop(0)
                    if seenSF:
                        curName.pop()
            theName = makeName(curName)
            interpretedNames.append((theName, label))
            curName.clear()

    if shortIn:
        for (name, cat) in valWords:
            if cat == "f":
                cat = "x"
            contributes = cat != "x"
            noI = lastCat != "i"
            noIS1 = lastCat not in {"i", "s1"}

            if (
                cat == "fs"
                and noI
                or cat == "i"
                and noIS1
                or cat == "s"
                and noI
                or cat == "s1"
                and noI
                or cat == "s2"
                and noIS1
            ):
                addName()
                if contributes:
                    curName.append(name)
                seenS = cat == "s"
                seenS1 = cat == "s1"
                seenS2 = cat == "s2"
                seenFS = cat == "fs"
                seenSF = cat == "sf"
            else:
                if contributes:
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
            lastCat = cat
    else:
        for (name, cat) in valWords:
            contributes = not shortOut or cat not in {"f", "x"}
            if (
                cat == "f"
                and lastCat not in {"f"}
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
                addName()
                if contributes:
                    curName.append(name)
                seenS = cat == "s"
                seenS1 = cat == "s1"
                seenS2 = cat == "s2"
                seenFS = cat == "fs"
                seenSF = cat == "sf"
            else:
                if contributes:
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

            lastCat = cat

    addName()

    return (interpretedNames, " ".join(outWords))


def distillTitle(source):
    m = {}

    source = SEP_RE.sub(" ", source)
    status = DETECT_STATUS_RE.findall(source)
    if status:
        val = " ".join(x.lower() for x in status)
        m["status"] = val
        source = DETECT_STATUS_RE.sub("", source)
    source = source.replace("[", "")
    source = source.replace("]", "")
    source = EN_RE.sub(" ", source)

    for k in ("rawdate", "place"):
        (val, source) = DISTILL[k](source)
        m[k] = val

    (names, source) = distillAuthor(source, shortIn=True, shortOut=True)
    val = ", ".join(n[0] for n in names)
    m["author"] = val

    t = {k: v for (k, v) in m.items() if k in {"author", "place", "rawdate"}}

    if source:
        source = source.replace("_", " ")
        if source in TITLE_REST:
            for (k, v) in TITLE_REST[source].items():
                t[k] = v
        source = ""
    return (f"{t['author']}; {t['place']}, {t['rawdate']}", source)


DISTILL = dict(
    seq=distillSeq,
    rawdate=distillDate,
    place=distillPlace,
    author=distillAuthor,
    title=distillTitle,
)


def distillHead(doc, info, source, force=False):
    m = {}

    if doc in DISTILL_SPECIALS:
        for (k, v) in DISTILL_SPECIALS[doc].items():
            m[k] = v

    source = SEP_RE.sub(" ", source)
    source = NOTEMARK_RE.sub("", source)

    status = DETECT_STATUS_RE.findall(source)
    if status:
        val = " ".join(x.lower() for x in status)
        m["status"] = val
        source = DETECT_STATUS_RE.sub("", source)

    source = source.replace("[", "")
    source = source.replace("]", "")

    metaValues = info["metaValues"]["head"]
    metaDiag = info["metaDiag"]
    nameDiag = info["nameDiag"]

    for k in ("seq", "rawdate", "place"):
        if k in m:
            continue
        (val, source) = DISTILL[k](source)
        metaValues[k][val].append(doc)
        m[k] = val

    brackets = BRACKET_RE.findall(source)
    if brackets:
        brackets = " ".join(brackets).strip()
        if brackets not in TITLE_BRACKETS:
            metaValues["brackets"][brackets].append(doc)
            metaDiag[doc]["brackets"] = ("()", "", "", brackets)
        source = BRACKET_RE.sub(" ", source)

    source = source.lower()
    for (variant, intention) in AUTHOR_SANITY:
        source = source.replace(variant, intention)
    source = EN_RE.sub(" ", source)

    data = source

    for (k, shortOut) in (("author", True), ("authorFull", False)):
        if k in m:
            continue
        (names, data) = distillAuthor(source, shortIn=False, shortOut=shortOut)
        val = ", ".join(n[0] for n in names)
        for (name, label) in names:
            metaValues[k][name].append(doc)
            nameDiag[k][label][name].append(doc)
        m[k] = val

    source = data

    datePure = m["rawdate"].replace(" en ", "_en_").replace("?", "")

    parts = datePure.split()
    if len(parts) == 3:
        (day, month, year) = parts
        month = MONTH_NUM[month]
        m["day"] = day.split("_")[0]
        m["month"] = str(month)
        m["year"] = year
    else:
        m["day"] = ""
        m["month"] = ""
        m["year"] = ""

    t = {k: v for (k, v) in m.items() if k in {"author", "place", "rawdate"}}

    if "rest" in m:
        source = m["rest"]
    if source:
        source = source.replace("_", " ")
        if source in TITLE_REST:
            for (k, v) in TITLE_REST[source].items():
                t[k] = v
        else:
            metaValues["rest"][source].append(doc)
            metaDiag[doc]["rest"] = ("!!", "", "", source)
        source = ""

    if "title" in m:
        title = m["title"]
    else:
        title = f"{t['author']}; {t['place']}, {t['rawdate']}"
        m["title"] = title
    metaValues["title"][title].append(doc)

    return {k: f"!{v}" for (k, v) in m.items()} if force else m


previousMeta = {}


def checkMeta(metaText, bodyText, info):
    doc = info["doc"]
    metaValues = info["metaValues"]["meta"]
    metaDiag = info["metaDiag"]

    origMetadata = {k: source for (k, source) in META_KV_2_RE.findall(metaText)}
    if doc in DISTILL_SPECIALS:
        for (k, v) in DISTILL_SPECIALS[doc].items():
            origMetadata[k] = v

    metadata = {k: v for (k, v) in origMetadata.items()}

    for k in META_KEY_ORDER:
        source = metadata.get(k, "")
        if source.startswith("!"):
            CORRECTION_FORBIDDEN.setdefault(doc, set()).add(k)
            source = source[1:]
            metadata[k] = source

        source = SEP_RE.sub(" ", source)
        if k in DISTILL:
            args = (True,) if k == "author" else (False,) if k == "authorFull" else ()
            (v, source) = DISTILL[k](source, *args)
            if k in {"author", "authorFull"}:
                rep = ", ".join(n[0] for n in v)
                for (name, label) in v:
                    metaValues[k][name].append(doc)
                v = rep
            else:
                metaValues[k][v].append(doc)
            if k == "title":
                if "rest" in origMetadata:
                    source = origMetadata["rest"]
                if source:
                    metaValues["rest"][source].append(doc)
                    metaDiag[doc][k] = ("!!", source, source, "")
            metadata[k] = v

    if doc in FROM_PREVIOUS:
        for k in COLOFON_KEYS:
            metadata[k] = previousMeta[k]

    match = HEAD_RE.search(bodyText)
    head = HI_CLEAN_STRONG_RE.sub(
        r"""\1""", match.group(1).replace("<lb/>", " ").replace("\n", " ")
    )
    doc = info["doc"]
    info["heads"][doc] = head
    match = FIRST_PAGE_RE.search(bodyText)
    firstPage = match.group(1) if match else ""

    distilled = distillHead(doc, info, head)
    distilled["page"] = firstPage

    for k in META_KEY_ORDER:
        v = metadata.get(k, "")
        ov = origMetadata.get(k, "")

        if doc in FROM_PREVIOUS:
            v = previousMeta.get(k, "")
            metadata[k] = v
            metaDiag[doc][k] = ("ok", ov, v, "")
            continue

        dv = distilled.get(k, "")

        if doc in CORRECTION_FORBIDDEN and k in CORRECTION_FORBIDDEN[doc]:
            metadata[k] = v
            label = (
                "ok"
                if v == dv
                else "-+"
                if not v and dv
                else "+-"
                if v and not dv
                else "xx"
            )
            metaDiag[doc][k] = (label, ov, v, dv)
            continue

        metadata[k] = dv

        label = (
            "ok"
            if v == dv or k == "pid"
            else "ok"
            if k in ADD_META_KEYS
            else "ok"
            if not v and dv
            else "ok"
            if doc in CORRECTION_ALLOWED and k in CORRECTION_ALLOWED[doc]
            else "ok"
            if k in {"title", "author", "authorFull"}
            and roughlyEqual(v, dv, lax=k == "title")
            else "??"
            if v and not dv
            else "xx"
        )

        metaDiag[doc][k] = (label, ov, v, dv)

    previousMeta.clear()
    for (k, v) in metadata.items():
        previousMeta[k] = v

    newMeta = "\n".join(
        f"""<meta key="{k}" value="{v}"/>""" for (k, v) in metadata.items()
    )

    info["metas"] += 1
    return f"<header>\n{newMeta}\n</header>\n"


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
    previous = {}
    result = []

    def doPage(page, *args, **kwargs):
        if page is None:
            if processPage is not None:
                processPage(None, previous, result, info, *args, **kwargs)
            return

        match = PAGE_NUM_RE.search(page)
        pageNum = f"-{match.group(1):>04}" if match else ""
        info["page"] = f"{info['doc']}{pageNum}"
        info["pageNum"] = pageNum.lstrip("-")
        if stage == 0:
            page = X_RE.sub("", page)
            page = FACS_REF1_RE.sub(r'''tpl="1" vol="\1" facs="\2"''', page)
            page = FACS_REF2_RE.sub(r'''tpl="2" vol="\1" facs="\2"''', page)
        if processPage is None:
            page = trimPage(page, info, *args, **kwargs)
            page = LB_RE.sub(r"""<lb/>\n""", page)
            page = PB_RE.sub(r"""\n\n\g<0>\n\n""", page)
            page = NL_B_RE.sub(r"""\n<\1\2>""", page)
            page = NL_E_RE.sub(r"""\n</\1>\n""", page)
            if stage == 0:
                page = page.replace(" <hi", "\n<hi")
            page = WHITE_NL_RE.sub("\n", page.strip())
            page = SPACE_RE.sub(" ", page)
            result.append(page)
        else:
            processPage(page, previous, result, info, *args, **kwargs)

    for match in PB_RE.finditer(text):
        b = match.start()
        thisPage = text[prevMatch:b].strip()
        doPage(thisPage, *args, **kwargs)
        result.append("\n")
        prevMatch = b

    if prevMatch < len(text):
        thisPage = text[prevMatch:].strip()
        doPage(thisPage, *args, **kwargs)
    doPage(None, *args, kwargs)

    body = "".join(result)

    match = PB_RE.search(body)
    prePage = body[0 : match.start()].strip()
    if prePage:
        print(f"\nMaterial before first page\n\t=={prePage}==")

    body = WHITE_NLNL_RE.sub("\n\n", body.strip())
    return body
