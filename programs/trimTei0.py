import os
import re
import collections

from distill import META_KEY_TRANS_DEF
from lib import CHANGE_DIR, REPORT_DIR, TRIM_DIR, PAGE_NUM_RE

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
    for (doc, text) in ADD_DOC.items():
        (vol, name) = doc.split(":")
        path = f"{DST}/{vol}/{name}.xml"
        with open(path, "w") as fh:
            fh.write(text)
        pages = PAGE_NUM_RE.findall(text)
        info["pages"][vol][doc].extend(int(p) for p in pages)


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
    doc = info["doc"]

    pages = PAGE_NUM_RE.findall(bodyText)
    info["pages"][vol][doc].extend(int(p) for p in pages)
    return (trimHeader(metaText, info), bodyText)


def trimPage(text, info, *args, **kwargs):
    text = text.replace(''' rend=""''', "")
    text = text.replace(''' rend=" "''', "")
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

    pages = info["pages"]
    log = []
    for vol in sorted(pages):
        pageIndex = collections.defaultdict(set)
        docs = pages[vol]
        for doc in sorted(docs):
            for p in docs[doc]:
                pageIndex[p].add(doc)
        minPage = min(pageIndex)
        maxPage = max(pageIndex)
        missing = tuple(
            p
            for p in range(minPage, maxPage + 1)
            if not (p in pageIndex or p in ADD_PAGE_SET[vol])
        )
        duplicates = {p: ds for (p, ds) in pageIndex.items() if len(ds) > 1}
        if missing or duplicates:
            log.append(
                f"\t{vol}: {len(missing):>2} missing; {len(duplicates):>2} duplicates"
            )
            if missing:
                psRep = ", ".join(str(p) for p in missing)
                log.append(f"\t\tmissing: {psRep}")
            if duplicates:
                log.append("\t\tduplicates:")
                for p in sorted(duplicates):
                    dRep = ", ".join(duplicates[p])
                    log.append(f"\t\t\t{p:<8} occurs in {dRep}")

    logStr = "\n".join(log)
    if log:
        print("PAGES:")
        print(logStr)
    with open(f"{REP}/pages.txt", "w") as fh:
        fh.write(f"{logStr}\n")
