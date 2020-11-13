import os
import re
import collections

from distill import META_KEY_TRANS_DEF
from lib import (
    CHANGE_DIR,
    REPORT_DIR,
    TRIM_DIR,
    PAGE_NUM_RE,
    LT,
    GT,
    AMP,
    rangesFromList,
    specFromRanges,
)

trimDocBefore = None
trimDocPrep = None
processPage = None
trimDocPost = None

STAGE = 0
REP = f"{REPORT_DIR}{STAGE}"
DST = f"{TRIM_DIR}{STAGE}"

ADD_PAGE = {}
ADD_PAGE_SET = collections.defaultdict(set)
ADD_DOC = {}
REPLACE_PAGE = {}


def corpusPre(givenVol):
    for (subPath, dest) in (
        ("doc", ADD_DOC),
        ("add", ADD_PAGE),
        ("replace", REPLACE_PAGE),
    ):
        thisChangeDir = f"{CHANGE_DIR}/{subPath}"
        with os.scandir(thisChangeDir) as dh:
            for entry in dh:
                if entry.is_dir():
                    vol = entry.name
                    if vol.isdigit() and (givenVol is None or vol in givenVol):
                        with os.scandir(f"{thisChangeDir}/{vol}") as dh:
                            for entry in dh:
                                if entry.is_file():
                                    fileName = entry.name
                                    if fileName.endswith(".xml"):
                                        name = fileName[0:-4]
                                        if subPath == "add":
                                            (base, p) = name.split("-", 1)
                                            pNum = int(p.lstrip("0"))
                                            ADD_PAGE_SET[vol].add(pNum)
                                            pNum = f"{pNum + 1:>04}"
                                            storeName = f"{base}-{pNum}"
                                        else:
                                            storeName = name
                                        doc = f"{vol}:{storeName}"
                                        with open(
                                            f"{thisChangeDir}/{vol}/{fileName}"
                                        ) as fh:
                                            text = fh.read()
                                        dest[doc] = text


def trimVolume(vol, letters, info, idMap, givenLid, mergeText):
    pageDiag = info["pageDiag"]
    for (doc, text) in ADD_DOC.items():
        (docVol, name) = doc.split(":")
        if docVol != vol:
            continue
        path = f"{DST}/{vol}/{name}.xml"
        with open(path, "w") as fh:
            fh.write(text)
        pages = PAGE_NUM_RE.findall(text)
        for p in pages:
            p = int(p)
            if p in pageDiag[vol]:
                print(f"PAGE ERROR in volume {vol}: duplicate page {p}")
            pageDiag[vol][p] = "ocr"


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
META_KEY_NO_TRANS = {"authorFull", "status"}
META_KEY_TRANS = {
    old: new for (new, old) in META_KEY_TRANS_DEF if new not in META_KEY_NO_TRANS
}
META_KEYS = {x[1] for x in META_KEY_TRANS_DEF}
META_KEY_IGNORE = set(
    """
        tocLevel
        volume
        witnessDayLevel1_to
        witnessMonthLevel1_to
        witnessYearLevel1_to
    """.strip().split()
)
META_VAL_RE = re.compile(
    r"""
        <interp>
            (.*?)
        </interp>
    """,
    re.S | re.X,
)


def trimDocPrep(info, metaText, bodyText, previousMeta):
    vol = info["vol"]
    pageDiag = info["pageDiag"]

    pages = PAGE_NUM_RE.findall(bodyText)
    for p in pages:
        p = int(p)
        if p in pageDiag[vol]:
            print(f"PAGE ERROR in volume {vol}: duplicate page {p}")
        info["pageDiag"][vol][p] = "tei"
    return (trimHeader(metaText, info), bodyText)


def trimPage(text, info, *args, **kwargs):
    text = text.replace(''' rend=""''', "")
    text = text.replace(''' rend=" "''', "")
    text = (
        text.replace("&quot;", '"')
        .replace("&apos;", "'")
        .replace("&lt;", LT)
        .replace("&gt;", GT)
        .replace("&amp;", AMP)
    )

    page = info["page"]

    return (
        REPLACE_PAGE[page]
        if page in REPLACE_PAGE
        else (ADD_PAGE[page] if page in ADD_PAGE else "") + text
    )


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


def transVal(value):
    values = META_VAL_RE.findall(value)
    return ",".join(v for v in values if v)


def corpusPost(info):
    metasUnknown = info["metasUnknown"]
    print(f"\t{len(metasUnknown):>3} docs with unrecognized metadata")
    with open(f"{REP}/metaUnrecognized.txt", "w") as fh:
        for (doc, meta) in sorted(metasUnknown):
            fh.write(f"{doc}\n")
            for (k, v) in meta.items():
                fh.write(f"\t{k:<10} = {v}\n")
            fh.write("\n")

    print("PAGES:")
    pageDiag = info["pageDiag"]
    with open(f"{REP}/pageDiag.txt", "w") as fh:
        for vol in sorted(pageDiag):
            fh.write(f"{vol}:\n")
            stats = dict(ok=[], xx=[], dd=[])
            pages = pageDiag[vol]
            minPage = min(pages)
            maxPage = max(pages)
            for p in range(minPage, maxPage + 1):
                if p not in pages:
                    label = "ocr" if p in ADD_PAGE_SET[vol] else "xx"
                    pageDiag[vol][p] = label
                    stats["ok" if label == "ocr" else label].append(p)
                else:
                    stats["ok"].append(p)
                fh.write(f"\tp{p:>04} {pageDiag[vol][p]}\n")

            first = True
            for label in ("ok", "xx", "dd"):
                data = stats[label]
                if data:
                    rep = specFromRanges(rangesFromList(data))
                    volRep = f"{vol}:" if first else "   "
                    first = False
                    print(f"{volRep} {label} {rep}")
