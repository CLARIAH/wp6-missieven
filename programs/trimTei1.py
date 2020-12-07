import sys
import re
from itertools import chain

from distill import META_KV_2_RE, HEAD_RE, HI_CLEAN_STRONG_RE, distillHead
from lib import (
    TRIM_DIR,
    REPORT_DIR,
    WHITE_RE,
    BODY_RE,
    CELL_RE,
    GT,
    LT,
    AMP,
    A2Z,
    applyCorrections,
    summarize,
)


corpusPre = None
trimVolume = None
processPage = None

STAGE = 1
SRC = f"{TRIM_DIR}{STAGE - 1}"
DST = f"{TRIM_DIR}{STAGE}"
REP = f"{REPORT_DIR}{STAGE}"

# SOURCE CORRECTIONS

MERGE_DOCS = {
    "06:p0406": ("06:p0407",),
}
SKIP_DOCS = {x for x in chain.from_iterable(MERGE_DOCS.values())}

CORRECTIONS_DEF = {
    "01:p0203": ((re.compile(r"""(<p\ rend="font-size:)\ 8\.5;""", re.S), r"\1 12;"),),
    "01:p0663": ((re.compile(r""">\(1\) Dirck""", re.S), r">1) Dirck"),),
    "02:p0480": (
        (re.compile(r"""<p\b[^>]*>p\.r cento<lb/>\s*</p>\s*""", re.S), r""),
        (
            re.compile(r"""<fw\b[^>]*>(noorden gezonden[^<]*)</fw>""", re.S),
            r"""<note resp="editor">\1</note>""",
        ),
    ),
    "03:p0676": (
        (re.compile(r"""<p\b[^>]*>(De catechismus.*?</p>)""", re.S), r"<p>\1"),
    ),
    "04:p0183": (
        (
            re.compile(
                r"""
                    (
                        (?:
                            <note[^>]*>1\)\ Vermoedelijk\ was\ men.*?</note>
                            \s*
                        )+
                    )
                    (
                        (?:
                            <p\b[^>]*>.*?</p>
                            \s*
                        )+
                    )
                    (
                        <pb\s*n="204"[^>]*>
                    )
                """,
                re.S | re.X,
            ),
            r"\2\1\3",
        ),
    ),
    "04:p0373": (
        (
            re.compile(r"""<fw\b[^>]*>(inkomsten en producten[^<]*)</fw>""", re.S),
            r"""<note resp="editor">\1</note>""",
        ),
        (
            re.compile(
                r"""
                    (
                        (?:
                            <p\b[^>]*>Ten\ comptoire\ Pegu.*?</p>
                            \s*
                        )
                        (?:
                            <p\b[^>]*>.*?</p>
                            \s*
                        )+?
                        (?:
                            <p\b[^>]*>Nagelwanze8\).*?</p>
                            \s*
                        )
                    )
                    (
                        (?:
                            <p\b[^>]*>.*?</p>
                            \s*
                        ){2}
                    )
                    (
                        <p\b[^>]*>
                            .*?
                    )
                    (
                            10\ 678\.10
                            .*?
                    )
                    (
                        <pb\s*n="393"[^>]*>
                    )
                """,
                re.S | re.X,
            ),
            r"\1\n<p>\4\n\2\3</p>\5",
        ),
    ),
    "04:p0496": ((re.compile(r"""I( en 9 maart 1683)""", re.S), r"""1\1"""),),
    "05:p0296": (
        (
            re.compile(r"""<fw\b[^>]*>(beschikbaar zijn; koopman[^<]*)</fw>""", re.S),
            r"""<note resp="editor">\1</note>""",
        ),
        (
            re.compile(r"""<fw\b[^>]*>(toren inspecteren[^<]*)</fw>""", re.S),
            r"""<note resp="editor">\1</note>""",
        ),
        (
            re.compile(r"""<fw\b[^>]*>(vangen voor[^<]*)</fw>""", re.S),
            r"""<note resp="editor">\1</note>""",
        ),
    ),
    "05:p0605": (
        (
            re.compile(r"""<p\b[^>]*>(wel eenige notebomen.*?)</p>""", re.S),
            r"""<note resp="editor">\1</note>""",
        ),
    ),
    "05:p0668": (
        (
            re.compile(r"""<fw[^>]*>Van Outlioom[^<]*?689(doen[^<]*)</fw>""", re.S),
            r"""<note resp="editor">\1</note>""",
        ),
    ),
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
    "06:p0011": (
        (
            re.compile(r"""<fw\b[^>]*>(Karaëng Bontolangkas[^<]*)</fw>""", re.S),
            r"""<note resp="editor">\1</note>""",
        ),
    ),
    "06:p0161": (
        (
            re.compile(r"""<fw\b[^>]*>(groten [^<]*)</fw>""", re.S),
            r"""<note resp="editor">\1</note>""",
        ),
        (
            re.compile(r"""<fw[^>]*>172 Van Out[^<]*?1701(niet[^<]*)</fw>""", re.S),
            r"""<note resp="editor">\1</note>""",
        ),
    ),
    "06:p0189": (
        (
            re.compile(r"""<fw[^>]*>194 Van Out[^<]*?1702(hierover[^<]*)</fw>""", re.S),
            r"""<note resp="editor">\1</note>""",
        ),
    ),
    "06:p0346": (
        (
            re.compile(r"""<fw[^>]*>(vertrek van De Vos[^<]*)</fw>""", re.S),
            r"""<note resp="editor">\1</note>""",
        ),
    ),
    "06:p0415": (
        (
            re.compile(r"""<fw[^>]*>(139 man aan[^<]*)</fw>""", re.S),
            r"""<note resp="editor">\1</note>""",
        ),
        (
            re.compile(r"""<fw[^>]*>(wordt vice-[^<]*)</fw>""", re.S),
            r"""<note resp="editor">\1</note>""",
        ),
    ),
    "06:p0477": (
        (
            re.compile(
                r"""<fw[^>]*>510 Van Hoorn[^<]*?1707(de Chinese[^<]*)</fw>""", re.S
            ),
            r"""<note resp="editor">\1</note>""",
        ),
    ),
    "06:p0836": (
        (
            re.compile(r"""<fw[^>]*>(70088 \*S\?[^<]*)</fw>""", re.S),
            r"""<note resp="editor">\1</note>""",
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
    "06:p0915": (
        (
            re.compile(r"""<fw[^>]*>(betekent in Bengalen[^<]*)</fw>""", re.S),
            r"""<note resp="editor">\1</note>""",
        ),
    ),
    "07:p0003": ((re.compile(r"""(<head\b[^>]*>)(CHRIS)""", re.S), r"""\1I. \2"""),),
    "07:p0517": (
        (
            re.compile(r"""<fw[^>]*>Zwaardecroon[^<]*?533(winnende[^<]*)</fw>""", re.S),
            r"""<note resp="editor">\1</note>""",
        ),
    ),
    "07:p0660": ((re.compile(r"""(<head\b[^>]*>XX)L""", re.S), r"""\1II"""),),
    "08:p0179": ((re.compile(r"""(begraven\)\. )’(<lb/>)""", re.S), r"\1\2"),),
    "09:p0112": (
        (
            re.compile(r"""<p\b[^>]*>SURAT<lb/>\n</p>""", re.S),
            """<subhead>SURAT<lb/>\n</subhead>""",
        ),
    ),
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
    "09:p0344": (
        (
            re.compile(r"""<fw[^>]*>(Klarabeek[^<]*)</fw>""", re.S),
            r"""<note resp="editor">\1</note>""",
        ),
        (
            re.compile(r"""<fw[^>]*>(retourschepen[^<]*)</fw>""", re.S),
            r"""<note resp="editor">\1</note>""",
        ),
        (
            re.compile(
                r"""<p[^>]*>(<hi\b[^>]*>Europeanen[^<]*</hi>.*?\)\.</hi><lb/>)""", re.S
            ),
            r"""<note resp="editor">\1</note>\n<p>""",
        ),
        (
            re.compile(r"""<fw[^>]*>(Franqois[^<]*)</fw>""", re.S),
            r"""<note resp="editor">\1</note>""",
        ),
        (
            re.compile(r"""<p[^>]*>(loeds.*?)</p>""", re.S),
            r"""<note resp="editor">\1</note>""",
        ),
        (
            re.compile(
                r"""
                    (<note[^>]*>\(\ Per\ Heinkenszand.*?)
                    (</note>)
                    \s*
                    <p\b[^>]*>(.*?)</p>
                    \s*
                    <p\b[^>]*>(.*?)</p>
                """,
                re.S | re.X,
            ),
            r"\1<lb/>\n\3<lb/>\n\4<lb/>\n\2",
        ),
        (
            re.compile(r"""<p\b[^>]*>SURAT<lb/>\n</p>""", re.S),
            """<subhead>SURAT<lb/>\n</subhead>""",
        ),
    ),
    "09:p0628": (
        (
            re.compile(
                r"""
                    (<note[^>]*>\(Kleden\ niet.*?)
                    (</note>)
                    \s*
                    <p\b[^>]*>(.*?)</p>
                    \s*
                    <p\b[^>]*>(.*?)</p>
                    \s*
                    <p\b[^>]*>(.*?)</p>
                """,
                re.S | re.X,
            ),
            r"\1<lb/>\n\3<lb/>\n\4<lb/>\n\5<lb/>\n\2",
        ),
        (
            re.compile(r"""<p\b[^>]*>SURAT<lb/>\n</p>""", re.S),
            """<subhead>SURAT<lb/>\n</subhead>""",
        ),
    ),
    "10:p0175": (
        (
            re.compile(r"""<p\b[^>]*>(<hi\b[^>]*>Atjeh,.*? f 80,\)</hi><lb/>)""", re.S),
            r"""<note resp="editor">\1</note>\n<p>""",
        ),
        (
            re.compile(r"""<fw[^>]*>(voor f77[^<]*)</fw>""", re.S),
            r"""<note resp="editor">\1</note>""",
        ),
    ),
    "10:p0413": (
        (
            re.compile(r"""<fw[^>]*>(\[ MacNeal\? \],[^<]*)</fw>""", re.S),
            r"""<note resp="editor">\1</note>""",
        ),
    ),
    "10:p0633": (
        (
            re.compile(
                r"""
                (
                    <pb\ n="743"[^>]*>\n
                    <fw[^>]*>.*?</fw>\n
                )
                </p>\n
                """,
                re.S | re.X,
            ),
            r"\1",
        ),
        (
            re.compile(
                r"""
                    <note[^>]*>(bij\ de\ Chinese.*?</note>\n)
                    (<table>.*?</table>\n)
                """,
                re.S | re.X,
            ),
            r"""</p>\n\2<note resp="editor">( \1""",
        ),
    ),
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
    "10:p0857": ((re.compile(r"""decem¬ber""", re.S), r"""december"""),),
    "11:p0226": (
        (re.compile(r"""\((niet getekend wegens ziekte)\]""", re.S), r"""(\1)"""),
    ),
    "11:p0350": (
        (
            re.compile(
                r"""
                    (<note[^>]*>\(De\ verkoop\ van\ kruidnagels.*?)
                    (</note>)
                    \s*
                    <p\b[^>]*>(.*?)</p>
                    \s*
                    <p\b[^>]*>(.*?)</p>
                """,
                re.S | re.X,
            ),
            r"\1<lb/>\n\3<lb/>\n\4<lb/>\n\2",
        ),
        (
            re.compile(r"""(<note[^>]*>\(Dat er 19 balen grove.*?</note>)""", re.S),
            r"</p>\1",
        ),
        (
            re.compile(
                r"""
                (
                    <pb\ n="435"[^>]*>\n
                    <fw[^>]*>.*?</fw>\n
                )
                </p>\n
                """,
                re.S | re.X,
            ),
            r"\1",
        ),
    ),
    "12:p0003": (
        (
            re.compile(r"""<fw[^>]*>(dien[^<]*)</fw>""", re.S),
            r"""<note resp="editor">\1</note>""",
        ),
    ),
    "13:p0122": (
        (
            re.compile(r"""<fw[^>]*>(Om achter[^<]*)</fw>""", re.S),
            r"""<note resp="editor">\1</note>""",
        ),
    ),
    "13:p0231": (
        (
            re.compile(r"""<fw[^>]*>(goederen ƒ[^<]*)</fw>""", re.S),
            r"""<note resp="editor">\1</note>""",
        ),
    ),
    "13:p0340": (
        (
            re.compile(r"""<fw[^>]*>(Verleende[^<]*)</fw>""", re.S),
            r"""<note resp="editor">\1</note>""",
        ),
    ),
    "13:p0362": (
        (
            re.compile(r"""<fw[^>]*>(opgedragen[^<]*)</fw>""", re.S),
            r"""<note resp="editor">\1</note>""",
        ),
        (
            re.compile(r"""<fw[^>]*>(tot 31 augustus[^<]*)</fw>""", re.S),
            r"""<note resp="editor">\1</note>""",
        ),
    ),
    "13:p0501": (
        (
            re.compile(
                r"""
                    (</note>\s*<note[^>]*>29<lb/>\s*)
                    (</note>)
                    \s*
                    <p\b[^>]*>(.*?)</p>
                    \s*
                    <p\b[^>]*>(.*?)</p>
                """,
                re.S | re.X,
            ),
            r"\1<lb/>\n\3<lb/>\n\4<lb/>\n\2",
        ),
    ),
}

CORRECTIONS = {
    page: tuple((spec[0], spec[1], 1 if len(spec) == 2 else spec[2]) for spec in specs)
    for (page, specs) in CORRECTIONS_DEF.items()
}

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


def trimVolume(vol, letters, info, idMap, givenLid, mergeText):
    thisSrcDir = f"{SRC}/{vol}"
    for name in letters:
        lid = name if idMap is None else idMap[name]
        if givenLid is not None and lid.rstrip(A2Z) not in givenLid:
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


def trimDocBefore(doc, name, thisSrcDir, mergeText):
    if doc in SKIP_DOCS:
        return None

    if doc in mergeText:
        text = mergeText[doc]
    else:
        with open(f"{thisSrcDir}/{name}.xml") as fh:
            text = fh.read()
    return applyCorrections(CORRECTIONS, doc, text)


def combineTexts(first, following):
    bodies = []

    for text in following:
        match = BODY_RE.search(text)
        bodies.append(match.group(1))

    return first.replace("</body", ("\n".join(bodies)) + "</body>")


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


def trimDocPrep(info, metaText, bodyText, previousMeta):
    doc = info["doc"]
    bigTitle = info["bigTitle"]
    header = f"""<header>\n{metaText}\n</header>"""
    match = HEADER_TITLE_RE.search(header)
    if match:
        title = match.group(1)
        if REST_RE.match(title):
            bigTitle[doc] = HI_CLEAN_STRONG_RE.sub(
                r"""\1""", title.replace("<lb/>", " ").replace("\n", " ")
            )
            return (header, None)

    if doc in CORRECTION_HEAD:
        (corrRe, corrText) = CORRECTION_HEAD[doc]
        (bodyText, n) = corrRe.subn(f"<head>{corrText}</head>\n", bodyText, count=1)
        if not n:
            print(f"\nWarning: head correction failed on `{doc}`")

    return (header, bodyText)


def trimDocPost(info, body):
    vol = info["vol"]
    doc = info["doc"]
    bigTitle = info["bigTitle"]

    body = PB_P_PERM_RE.sub(r"""\2\n\1""", body)
    match = BIG_TITLE_PART_RE.search(body)

    if match:

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

    return body


def corpusPost(info):
    docs = info["docs"]
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

    firstP = info["firstP"]
    if firstP:
        print(f"FIRST PARA REMOVALS on {len(firstP)} pages")
        with open(f"{REP}/firstp.txt", "w") as fh:
            for page in sorted(firstP):
                text = (
                    firstP[page]
                    .replace("<lb/>\n", " ")
                    .replace("\n", " ")
                    .replace("<lb/>", " ")
                    .strip()
                )
                fh.write(f"{page} {summarize(text, limit=30)[0]}\n")

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
                    msg = f"{fol:<20} {nContexts:>3} contexts, {nOccs:>4} occurrences"
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


HEADER_RE = re.compile(r"""^.*?</header>\s*""", re.S)

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


def splitDoc(doc, info):
    (vol, startPage) = doc.split(":")
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


def writeDoc(dst, vol, pageNum, metadata, text):
    header = "\n".join(
        f"""<meta key="{k}" value="{v}"/>""" for (k, v) in sorted(metadata.items())
    )
    header = f"<header>\n{header}\n</header>\n"
    body = f"<body>\n{text}\n</body>\n"

    with open(f"{dst}/{vol}/{pageNum:>04}.xml", "w") as fh:
        fh.write(f"<teiTrim>\n{header}{body}</teiTrim>")


def stripRendAtt(match):
    material = match.group(1).replace(";", " ")
    if material == "" or material == " ":
        return ""
    material = WHITE_RE.sub(" ", material)
    material = material.strip()
    return f''' rend="{material}"'''


CLEAR_FW_RE = re.compile(r"""<fw\b[^>]*>(.*?)</fw>""", re.S)

ALIGN_RE = re.compile(r"""text-align:\s*justify[^;"']*;?""", re.S)
ALIGN_H_RE = re.compile(r"""text-align:\s*([^;"']+)[^;'"]*;?""", re.S)
ALIGN_V_RE = re.compile(r"""vertical-align:\s*([^;"']+)[^;'"]*;?""", re.S)
DECORATION_RE = re.compile(r"""text-decoration:\s*([^;"']+)[^;'"]*;?""", re.S)
DEG_RE = re.compile(r"""(°)(</hi>)""", re.S)
F_RE = re.compile(r"""<hi\b[^>]*>f</hi>""", re.S)
FAMILY_RE = re.compile(r"""font-family:[^;"']*;?""", re.S)
FONT_STYLE_RE = re.compile(
    r"""font-(?:style|weight|variant):\s*([^;"' ]+)[^;"']*;?""", re.S
)
HALF_RE = re.compile(r"""1\s*/?\s*<hi rend="sub">\s*2([^<]*)</hi>""", re.S)
HEIGHT_RE = re.compile(r"""line-height:[^;"']*;?""", re.S)
HI_SPECIAL_RE = re.compile(
    r"""
        <hi\b[^>]*>
            (kol[. ]*)
        </hi>
        ([^<]*)
        <hi\b[^>]*>
            (fol[. ]*)
        </hi>
        ([^<]*)
    """,
    re.S | re.I | re.X,
)

"""
<hi rend="font-size:11; font-family:Liberation Serif">Kol.</hi> Arch. 2284, VOC 2392,
<hi rend="font-size:11; font-family:Liberation Serif">fol.</hi> 76-445.<lb/>
"""

HI_CLEAN_RE = re.compile(r"""<hi\b[^>]*>([^a-zA-Z0-9]*?)</hi>""", re.S)
HI_EMPH_RE = re.compile(
    r"""(<hi\b[^>]*?rend=['"])[^'"]*?(?:bold|italic)[^'"]*(['"])[^>]*>""", re.S
)
HI_SUBSUPER_RE = re.compile(
    r"""(<hi\b[^>]*?rend=['"])[^'"]*?(super|sub|small-caps)[^'"]*(['"])[^>]*>""", re.S
)
HI_UND_RE = re.compile(
    r"""<hi\b[^>]*?rend=['"][^'"]*?underline[^'"]*['"][^>]*>(.*?)</hi>""", re.S
)
SMALLCAPS_RE = re.compile(r"""font-variant:\s*small-caps;?""", re.S)
INDENT_RE = re.compile(r"""text-indent:\s*[^-][^;"']*;?""", re.S)
MARGIN_RE = re.compile(r"""margin-(?:[^:'"]*):[^;"']*;?""", re.S)
OUTDENT_RE = re.compile(r"""text-indent:\s*-[^;"']*;?""", re.S)
SIZE_RE = re.compile(r"""font-size:\s*(?:9\.5|10\.5|10)\s*[^;"']*;?""", re.S)
SIZE_XLARGE_RE = re.compile(
    r"""
        font-size:
        \s*
        (?:
            (?:[2-9][0-9])
            |
            (?:1[5-9])
        )
        \.?5?
        [^;"']*
        ;?
    """,
    re.S | re.X,
)
SIZE_LARGE_RE = re.compile(
    r"""
        font-size:
        \s*
        (?:
            (?:1[1-4])
        )
        \.?5?
        [^;"']*
        ;?
    """,
    re.S | re.X,
)
SIZE_SMALL_RE = re.compile(
    r"""
        font-size:
        \s*
        (?:
            9
            |
            (?:[6-8])
        )
        \.?5?
        [^;"']*
        ;?
    """,
    re.S | re.X,
)
SIZE_XSMALL_RE = re.compile(
    r"""
        font-size:
        \s*
        (?:
            [1-5]
        )
        \.?5?
        [^;"']*
        ;?
    """,
    re.S | re.X,
)
SPACING_RE = re.compile(r"""letter-spacing:[^;"']*;?""", re.S)
STRIP_RE = re.compile(r""" rend=['"]([^'"]*)['"]""", re.S)
IS_TEXT_1_RE = re.compile(
    r"""
        (?:[A-Z]{8,})
        |(?:\bt\b)
        |[(:„ƒ]
        |(?:\ [fl]b?\.\ )
        |(?:^N$)
        |(?:[Ff]ol\.?(?:io)?)
        |\.\ \.\ \.
        |(?:^s$)
        |aanreekening
        |bedragen
        |Bestaande
        |Bontolangkas
        |brief
        |canneel
        |corpo
        |Choromandel
        |Curator
        |deser
        |dienaren
        |hebben
        |Heeft
        |Eysch
        |incomsten
        |inlanders
        |Juweel
        |koopmanschappen
        |nagelen
        |onbequame
        |ongelden
        |ormandel
        |predicatiën
        |Proffijt
        |reekening
        |Rijssel
        |Rusland
        |verdre
        |vertrek
        |vgl\.
        |voordeel
        |Zwavel
    """,
    re.S | re.X,
)
IS_TEXT_2_RE = re.compile(r"""ae|ck|heyt|oo""", re.S)
IGNORE_RE = re.compile(
    r"""
            ^
            (?:
                index
                |
                (?:in[dio][a-z\ -]*x)
                |
                toelich
                |
                persoonsnamen
                |
                (?:
                    [0-9\ ]*
                    $
                )
            )
        """,
    re.S | re.I | re.X,
)

COMMA = r"""[.,’'`]"""
DIGIT_OCR = r"""=\]'coöjsgbiïl"""
DIGIT_PLUS = fr"""[0-9{DIGIT_OCR}]"""
DIGIT_OCR_X = fr"""[{DIGIT_OCR}]"""
NONWORD = fr"""[^a-z0-9{DIGIT_OCR}]"""


NUM_PAT = fr"""
    (?:^|(?<={NONWORD}))
    (?:
        (?:
            bi|lö|ö
        )
        |
        (?:
            [0-9]+
            (?:
                \s
                |
                {DIGIT_PLUS}
            )+
        )
        |
        (?:
            {DIGIT_OCR_X}
            \s*
            [0-9]+
            (?:
                \s
                |
                {DIGIT_PLUS}
            )*
        )
    )
    (?:$|(?={NONWORD}))
"""

SPACE_REPL = r" "

ROMAN_EXCLUDE = set(
    """
    3
    caen
    d
    de
    dec
    deciel
    dedel
    dee
    den
    diemen
    diemeu
    dutecum
    duteeum
    duteuum
    e
    haan
    heuvel
    indie
    jan
    juli
    juni
    lijn
    mei
    maan
    van
    vlaclc
    xy
    y
""".strip().split()
)


ROMANS = set()
GOOD_ROMAN = re.compile(r"^[ivxlcdm]+a?$", re.S)


def romanRepl(match):
    word = match.group(0).strip()

    if not word or word in ROMAN_EXCLUDE:
        return f"{word} "

    goodR = (
        word.replace("t", "i")
        .replace("h", "ii")
        .replace("y", "v")
        .replace("j", "i")
        .replace("3", "i")
        .replace("u", "ii")
        .replace("1", "i")
        .replace("ï", "i")
    )
    goodR = (
        goodR.replace("e", "i")
        if "e" in goodR and "x" in goodR
        else "viii"
        if goodR in {"viel", "vin"}
        else "ii"
        if goodR == "el"
        else goodR
    )

    if not GOOD_ROMAN.match(goodR):
        ROMANS.add(word)
    return SPACE_REPL


GOOD_STRIPE = (
    (
        "stmartin",
        re.compile(r"""d[oe] saint[* -]*mart\s*in""", re.S),
        r"de_saint_martin ",
    ),
    (
        "strange",
        re.compile(
            fr"""[^a-z0-9{DIGIT_OCR}.,’`:;"{{}}\[!@$%^*()_+=|\\~<>?/ \t\n-]""", re.S
        ),
        r"?",
    ),
    ("d.v.", re.compile(fr"""\b[dvy]{COMMA}\s*"""), SPACE_REPL),
    ("enz", re.compile(fr"""{NONWORD}.[un][vzar]\b{COMMA}*\s*""", re.S), SPACE_REPL),
    ("arabic", re.compile(rf"""{NUM_PAT}\s*""", re.S | re.X), SPACE_REPL),
    ("comma", re.compile(fr"""{COMMA}\s*""", re.S), SPACE_REPL),
    ("entity", re.compile(fr"""[{AMP}{GT}{LT}]\s*""", re.S), SPACE_REPL),
    ("en", re.compile(r"""\b[oe][ni]i?\b\s*""", re.S), SPACE_REPL),
    ("he", re.compile(r"""\bhe\b\s*"""), SPACE_REPL),
    (
        "roman",
        re.compile(r"""\b[iïjvyxlcdmnthuüe3][iïjvyxlcdmnthuüe13']*a?\b""", re.S),
        romanRepl,
    ),
    (
        "month",
        re.compile(
            r"""
        \b
        (?:
            anu|jan|an
            |f[eo]b|tebr
            |maa|ina
            |apr
            |mei
            |jun|jul|u[nl]i
            |aug
            |s[eo]p|ept|aept
            |o[cok]t|ktob
            |nov
            |d[ceo][eco]
        )
        [a-z]*\b
        \.?
    """,
            re.S | re.X | re.I,
        ),
        SPACE_REPL,
    ),
    ("cleanup", re.compile(r"""[^a-zöï_ ]+"""), r""),
)


NAME_SANITY = tuple(
    entry[0:-1].split("=")
    for entry in f"""
both=both .
b rouwer=brouwer .
camphuj's=camphuys .
cur pen tier=carpentier .
d emmer=demmer .
dedel=dedel .
d n=den .
do =de .
don =den .
è=e.
e)e=de .
gij seis=gijsels .
harte inck=hartsinck .
ho orn=hoorn .
luca-sz=lucasz .
maotsuj'ker=maetsuycker .
mae o suy ker=maetsuycker .
maets yker=maetsuycker .
o suy ker=maetsuycker .
yker,maetsu=maetsuycker .
j^tsuyker=maetsuycker .
oud.tsh.oorn=oudtshoorn .
o utho om=oudtshoorn .
st/eur=steur .
v an=van .
v au=van .
v2n=van .
vau=van .
vaii=van .
va leken ier=valckenier .
vanbnhoff=van imhoff .
vanlmhoff=van imhoff .
van lm ho ff=van imhoff .
yan=van .
a{AMP}n=van .
w'elsmg=welsing .
y'i=vii.
""".strip().split(
        "\n"
    )
)
TEST_TEXTS = ("De Wïth on Steur II",)
TEST_TEXTS = ()


def test():
    for fw in TEST_TEXTS:
        fw = fw.lower()
        print(f"TEST -1: {fw}")

        for (variant, intention) in NAME_SANITY:
            fw = fw.replace(variant, intention)
        print(f"TEST  0: {fw}")

        for (i, (label, trimRe, trimRepl)) in enumerate(GOOD_STRIPE):
            fw = trimRe.sub(trimRepl, fw)
            print(f"{label:<10}: {fw}")

        print()
        sys.exit()


if TEST_TEXTS:
    test()


STOPWORDS = set(
    """
    van
    de
    den
    der
""".strip().split()
)

NAME_REPLACEMENTS_DEF = """
abraham

adriaan

alphen
    aiphen
    alplien

barendsz
    jbarendsz

bent

blom

bogaerde
    bogaorde

bornezee
    bomezee
    bomezeo
    bomezoe
    bomezoo
    bornezeo
    bornezoe

bort
    borfc
    burt
    bert

both
    bofch

broeckum
    broeclcum
    broeekum

brouwer
    jrouwer

brouck
    broack
    brouek
    brouok

burch
    buxch
    bureh

caen
    coen
    oaen

caesar
    ceasar

camphuys
    mphuys
    campbuys
    camphuy
    camphuyb
    caraphuys
    cainphuys
    campings
    campkuys
    carnphuys
    catnphuys
    comphuys
    jamphuys
    oainphuys

caron

carpentier
    carpentiei
    carpentior
    carperntier

chastelein
    chasfcelein
    chastelem
    chasteloin
    chastolein
    cliastelein
    casielijn
    casteleijn
    castelijn
    casteljjn

cloon
    cioon

cops
    copa

croocq

crudop

cunaeus
    chinaeus
    cimaeus
    cnnaeus
    cunaeas
    cunaens
    cunaeu
    cunaous
    uunaeus
    canaeus
    cnnaous
    conaens
    cunaeua
    cunaons
    cunaoua
    cunoeus

de_saint_martin
    sainfcmartin
    saintfartin
    saintmarfcin
    saintmartin

dedel
    dedl
    dedxl

demmer
    dammer
    deimner
    deinmer
    deminer
    demmor
    demnier
    demraer
    demtner
    demzner
    denuner
    deramer
    dermner
    dernmer
    deromer
    dommer
    lemmer

diderik
    didcrik
    piderik

diemen
    diemeu
    dieraen
    diernen
    diomen

dirk

douglas
    dougla
    douglaa
    dougls
    dougias
    douglass

durven

dutecum
    dutecom
    duteeum
    duteuum

faes

gabry

gardenijs

geleynsz

generaal

gijsels
    gijseis

groens
    goens
    goen
    goena
    goenb
    goenf
    goons
    groens

gorcom

gouverneur

haas

haan

haeze

hartsinck
    harcsinck
    harfcsinck
    hartainck
    harteinck
    harteinok
    hartsinclc
    hartsinok
    iiarfczinck
    iiartsinck
    ilartsinck
    rartsinck
    hortsinck

hartzinck
    harbzinck
    harfczinck
    hartzinek
    hartzinok
    ilartzinck
    hartzinclc
    iiarfczinck
    iiartzinck
    ixarfczinck
    ixartzinck

hasselaar

heuvel

hoorn
    iioora
    iioorn

houtman

hulft
    huift

hurdt
    elurdt
    blurdt
    hardt
    hnrdt
    hurdfc
    iiurdt
    ilurdt
    rurdt

huysman

imhoff
    imhofj
    imhojf
    lmhoff

jacob

joan
    joon

johannes

indie

lijn

lucasz
    lucas
    lucaszz
    lueasz

maerten

maetsuycker
    etsuyker
    maefcsuyker
    maetsucyker
    maetsuyclcer
    maetsuyeker
    maetsuyker
    maetsuylcer
    maotsuycker
    maotsuj'ker
    aiaetsuyker
    alaetsuyker
    mactsuyker
    maefcsuykcr
    maetauyker
    maetauykor
    maetbuyker
    maeteuyker
    maeteuykor
    maeteuylcer
    maetsuykcr
    maetsuykor
    maetsuykw
    maetsuylwr
    maofcsuyker
    maotauyker
    maotsuyker
    moetsuyker
    moetsuykor
    mootsuyker
    mootsuykor
    tsuyker
    uaetsuyker
    axaetsuyker
    maetsuvker

mossel

nobel

nuyts

ottens

oudtshoorn
    oudfcshoorn
    oudtsfioorn
    oudtshoom
    oudtshuom
    oudtsrioorn
    oudxshoorn
    qudtshoorn
    udtshoom
    xudtshoom
    oadtshoorn
    oudtahoom
    oudtahoora
    oudtahoorn
    oudtakoora
    oudtalioorn
    oudtehoom
    oudtehoorn
    oudtshoora
    oudtskoom
    oudtskoorn
    oudtslioom
    oudtslioorn
    outhcom
    outhoom
    outhoora
    outhoorn
    oufchoom
    oufchoorn
    outkoorn
    outlioom
    outlioorn
    oxthoom
    othoom

overtwater
    vertwater
    ovemvater
    overtwaoer
    overtwator
    ovortwater
    xvertwater
    overfcwater

patras

paviljoen

philips

pit
    pits
    pifc
    pita

pijl
    pij

putmans

quaelbergh

raden

raemburch
    raembnrch
    raemburcb

ranst

reael
    jreael reaei

reniers
    beniers
    eniers
    herders
    iteniers
    jeteniers
    keniers
    kreniers
    rcniecrs
    rcniers
    renicrs
    reuiers
    romers
    rreniers
    remers
    xteniers
    ïteniers

reyersz
    ileyersz

reynst

riebeeck
    riebecck
    rieboeck
    riobeeck
    rioboeck
    riebeeclc
    riebeeek
    riebeeok
    riebeock
    rieboock

rijn

schaghen
    schaghon

schouten

schram

sonck
    snck

specx
    ispecx
    speex
    spzcx

speelman
    speelmanen
    spoelman

steur
    rfteur
    stem
    steux
    stour

sweers
    sweera
    sweors

swoll
    swoii
    swol
    swoli
    swoil

thedens

thijsz
    tbijsz
    tliijsz
    thxjsz

timmerman
    timmermans
    timmermna

tolling

twist

uffelen
    uffeleii

valckenier
    valckenior
    valckonier
    valckonior
    valclcenier

verburch
    verbureh
    verburen
    yerburch
    varburch
    verbarch
    verbnrch
    verbnroh
    verburck
    verburcli
    verburoh
    vorbnrch
    vorburch
    vterbnrch

versteghen
    verstegfien
    yersteghen

vlack
    vlaek
    vlaok
    yalck
    yiack
    ylack
    ylaek
    vlaclc

vos
    voa

vuyst

welsing
    weising
    welging
    welgingen
    welsingen

wilde

willem

with
    witii
    wxth
    wxtii

witsen
    witaen
    wtsen
    wxtsen

ysbrantsz

zwaardecroon
    zwaarecroon

""".strip().split(
    "\n\n"
)

NAME_VARIANTS = {}
NAMES = set()

for nameInfo in NAME_REPLACEMENTS_DEF:
    (intention, *variants) = nameInfo.strip().split()
    NAMES.add(intention)
    for variant in variants:
        NAME_VARIANTS[variant] = intention


FOLIO_PAGE_RE = re.compile(
    r"""
    <
        ([a-z]+)
        \b
        [^>]*
    >
    (
    [Pp]
    \.
    \s*
    [0-9]+
    [0-9,.\ -]*
    )
    [^<]*
    (?:<lb/>\s)*
    </
        \1
    >
    """,
    re.S | re.X,
)


def folioPageRepl(match):
    text = match.group(0)
    (tag, folioPage) = match.group(1, 2)
    return text if tag == "note" else f"<folio>{folioPage}</folio>\n"


FOLIO_KA_RE = re.compile(
    r"""
    <
        ([a-z]+)
        \b
        [^>]*
    >
    (
    [Kk](?:ol)?
    \.?
    [Aa](?:rch)?
    \.
    \s*
    [0-9]+
    [0-9,.\ -]*
    )
    [^<]*
    (?:<lb/>\s)*
    </
        \1
    >
    """,
    re.S | re.X,
)

FOLIO_TRIGGER_RE = re.compile(
    r"""
        (^|<[^/][^>]*>)
        (\s*)
        ([^<]*?)
        (
            (?:f|it)ol
            [^< ]*
        )
        ([^<]*)
        (<\/?[^>]*>)
    """,
    re.S | re.I | re.X,
)


FOLIO_TRUE_RE = re.compile(
    r"""
    ^
    (?:
        FoL
        |FoLSlSv\.
        |Fol
        |Fol.237r-v\.
        |Fol.4238r-4238v\.
        |Fol.473r\.
        |Fol.499r\.
        |Fol.897v\.
        |Foll
        |folieerd
        |folieerd,
        |folio’s,
        |folio’s\.
        |iTol\.
    )
    $
    """,
    re.S | re.X,
)
FOLIO_FALSE_RE = re.compile(
    r"""
    ^
    (?:
        Folafi,
        |Folios
        |Foltering:
        |fola
        |fola,
        |folgens
        |folie
        |folie,
        |folieerd\.
        |folij
        |folio's
        |folio's,
        |folio,
        |folios
        |folio’s
        |folla
        |folla,
        |folterde
        |foltering
        |itol
        |itolambij
        |itolauw,
        |itoli
        |itoli,
        |itoli:
        |itolootinseugenenschuyten
    )
    $
    """,
    re.S | re.X,
)

FOLIO_COND_RE = re.compile(
    r"""
    ^
    (?:
        Fol\.
        |Folio
        |fol
        |fol\.
        |folio
        |folio\.
        |folio's\.
    )
    $
    """,
    re.S | re.X,
)
BIS = r"""b[iIlflsbB8]*"""
FOLIO_PRE_TRUE_RE = re.compile(
    fr"""
    ^
    (?:
        (?:\s*{COMMA}*\s*)
        (?:
            (?:Ongetekende)
            |
            (?:[Cc]opie)
            |
            (?:Ko[ln]\.\s*[Aa]rc[hl]i?)
            |
            (?:K\.\s*[AO])
            |
            (?:VOC)
            |
            [0-9ö]+
            |
            (?:{BIS})
            |
            (?:\(potlood-?\))
        )
    )+
    (?:\s*{COMMA}*\s*)
    $
    """,
    re.S | re.X,
)
FOLIO_PRE_FALSE_RE = re.compile(
    r"""
    ^
    (?:
        (?:[0-9ö]+\s*\))
        |\(
        |31\ december
        |Dusdanig
        |Na
        |Reglement
        |Teyouan
        |Totale\ omvang
        |Tussen
        |Zie
        |\(?Voor
        |aan\ 3333
        |bawa
        |brieff
        |dato
        |die\ door\ de
        |door\ kan
        |ende
        |fl\.
        |gedeelte\ van
        |gelieven
        |geregistreert
        |geseyden
        |missive
        |sijnde
        |van\ het\ plakkaat
        |verstaen
        |werd\ om\ den
        |ƒ
        |„sachtsinnige
    )
    """,
    re.S | re.X,
)

FOLIO_TWEAK_RE = re.compile(
    fr"""
        ^
        (.*?)
        \.
        (
            (?:K\.\s*A\.\s*)?
            [0-9]+
            (?:{BIS})?
            ,
            .*
        )
    """,
    re.S | re.X,
)

FOLIO_POST_RETAIN_RE = re.compile(
    r"""
        \(potlood
        | \(na\ fol
        | \(Copie
        | \(copie
        | \(secreet\)
        | \(F-v
        | \(F\.
        | \(folio\ 87
    """,
    re.S | re.X,
)

FOLIO_POST_REMOVE_RE = re.compile(
    fr"""
    ^(.*?)
    (
        \*\)[.•]
        | 1\)\.
        | {GT}\)\.
        | »\)\.
        | '\)\.
        | \(.*
    )
    $
    """,
    re.S | re.X,
)

FOLIO_MERGE_RE = re.compile(
    r"""
    (<folio>[^<]*)(</folio>)\s*</hi>\s*<hi[^>]*>([^<]*)(</hi>)
    """,
    re.S | re.X,
)

FOLIO_RESULT_RE = re.compile(r"""<folio>(.*?)</folio>""", re.S)

FOLIO_SEP_RE = re.compile(
    r"""
    (
        [A-Za-z]
        \.?
    )
    (
        [0-9]+
    )
    """,
    re.S | re.X,
)


def folioSepRepl(match):
    text = match.group(1)
    result = FOLIO_SEP_RE.sub(r"\1 \2", text)
    return f"<folio>{result}</folio>"


FOLIO_ISOLATE_RE = re.compile(
    r"""
        <([a-zA-Z]+)\b[^>]*>
        \s*
        (<folio>[^<]*</folio>)
        \s*
        (?:<lb/>\s*)*
        </\1>
        \s*
        (?:<lb/>\s*)*
    """,
    re.S | re.X,
)

FOLIO_LB_RE = re.compile(
    r"""
        (<folio>[^<]*</folio>)
        \s*
        (?:<lb/>\s*)+
    """,
    re.S | re.X,
)

FOLIO_MOVE = (
    re.compile(
        r"""(<p\b[^>]*>)\s*(<folio>[^<]*</folio>)""",
        re.S,
    ),
    re.compile(
        r"""(<folio>[^<]*</folio>)\s*(</p>)""",
        re.S,
    ),
    re.compile(
        r"""(<folio>[^<]*</folio>)\s*(</head>)""",
        re.S,
    ),
    re.compile(
        r"""(<folio>[^<]*</folio>)\s*(</head>)""",
        re.S,
    ),
    re.compile(
        r"""(<p\b[^>]*>[^>]+(?:<lb/>\s*)*)\s*(<folio>[^<]*</folio>)""",
        re.S,
    ),
)


HEAD_CORRECT = r"""
        [IVXLC]+[IVXLCl\ ]*(?:\s*a)?\.?\s*
        [A-Z\ ,.]{10,}
        [^<]*
        (?:<lb/>[^<]*)*
"""

HEAD_CORRECT_RE = re.compile(
    fr"""
    (<p\b[^>]*>)
    (?:<hi[^>]*>\s*)?
    ({HEAD_CORRECT})
    (?:</hi>\s*)?
    (?:<lb/>\s*)?
    (</p>\s*)
    """,
    re.S | re.X,
)


def headCorrectRepl(match):
    text = match.group(2)
    return (
        f"{match.group(1)}{text}{match.group(3)}"
        if "FEBRUARI" in text
        else f"""\n<head>{text}</head>\n"""
    )


HEAD_CORRECT_N_RE = re.compile(
    fr"""
    (<p\b[^>]*>)
    (?:<hi[^>]*>\s*)?
    ({HEAD_CORRECT})
    (?:</hi>\s*)?
    (<note)
    """,
    re.S | re.X,
)


HEAD_CORRECT_NUM_RE = re.compile(
    fr"""
    <head\b[^>]*>
    (
        (?:
            [0-9.,„«/()^ABCDfHIJKMNOQUrVw°—-]
            |
            (?:
                <hi\b[^>]*>[^<]*</hi>
            )
            |
            (?:
                [{GT}{LT}{AMP}]
            )
            |
            (?:
                <lb/>
            )
            |
            (?:
                \s+
            )
        )*
    )
    (?:<lb/>\s*)?
    </head>\s*
    """,
    re.S | re.X,
)

HEAD_CLEAN_HI_RE = re.compile(
    r"""
    (
        <head\b[^>]*>
        \s*
    )
    <hi\b[^>]*>
        ([^<]*)
    </hi>
    (
        \s*
        (?:
            <lb/>\s*
        )*
        </head>
    )
    """,
    re.S | re.X,
)

ALPHA = r"""[A-ZËÖ]+"""

HEAD_CORRECT_NAME_RE = re.compile(
    fr"""
    <head\b[^>]*>
    \s*
    (
        (?:
            {ALPHA}\s*
        ){{1,3}}
    )
    (?:<lb/>\s*)?
    </head>\s*
    """,
    re.S | re.X,
)

HEAD_NOTE_RE = re.compile(
    r"""
    <head>
    (.*?)
    (
        \(.*\)
        \.?
    )
    \s*
    </head>\s*
    """,
    re.S | re.X,
)


def getFolioPost(post):
    plain = (post, "")
    if FOLIO_POST_RETAIN_RE.search(post):
        return plain
    match = FOLIO_POST_REMOVE_RE.match(post)
    return match.group(1, 2) if match else plain


def checkFw(match):
    fw = match.group(1)
    fw = WHITE_RE.sub(" ", fw.strip())
    if not fw or fw == "d":
        return ""
    orig = fw
    fw = fw.replace("ë", "e").replace("é", "e").replace("ó", "o")
    if IGNORE_RE.search(fw):
        return ""
    wrong = IS_TEXT_1_RE.search(fw) or (IS_TEXT_2_RE.search(fw) and len(fw) > 100)
    return f"<p>{orig}</p>" if wrong else ""


HEAD_TITLE_RE = re.compile(r"""<head rend="[^"]*?\bxlarge\b[^>]*>(.*?)</head>""", re.S)

P_REMOVE = re.compile(r"""<p\b[^>]*>""", re.S)
SUB_RE = re.compile(r"""<hi\b[^>]*?sub[^>]*>(.*?)</hi>""", re.S)
SUPER_RE = re.compile(r"""<hi\b[^>]*?super[^>]*>(.*?)</hi>""", re.S)
SUBHEAD_RE = re.compile(r"""<p\b[^>]*?smallcaps[^>]*>(.*?)</p>""", re.S)

FIRST_P_SMALL_RE = re.compile(
    r"""
        (<pb\b[^>]*>)
        \s*
        <p\b
            [^>]*?
            x?small
            [^>]*
        >
            (.*?)
        </p>
    """,
    re.S | re.X,
)


def firstPReplProto(info):
    def firstPRepl(match):
        pb = match.group(1)
        first = match.group(2)
        firstText = first.replace("<lb/>\n", "").replace("\n", "").replace("<lb/>", "")
        if len(firstText) > 2:
            return match.group(0)

        page = info["page"]
        firstP = info["firstP"]
        firstP[page] = first
        return pb

    return firstPRepl


def removePs(match):
    text = match.group(1)
    text = text.replace("</p>", "<lb/>")
    text = P_REMOVE.sub("", text)
    return f"""<cell>{text}</cell>"""


SUBSUPER_MOVE_RE = re.compile(
    r"""
    (
        <(super|sub)>
        [^<]*
    )
    (
        \s*
        [.,:;]
        \s*
    )
    (
        </\2>
    )
    """,
    re.S | re.X,
)


def trimPage(text, info, *args, **kwargs):
    if "fwh" not in info:
        info["fwh"] = open(f"{REP}/fwh-no.tsv", "w")
    fwh = info["fwh"]
    captionInfo = info["captionInfo"]
    captionNorm = info["captionNorm"]
    captionVariant = info["captionVariant"]
    firstPRepl = firstPReplProto(info)
    doc = info["doc"]
    page = info["page"]
    showOrig = f"{page[0:4]}{page[9:]}" in kwargs.get("orig", set())

    ROMANS.clear()

    for fw in CLEAR_FW_RE.findall(text):
        if showOrig:
            orig = fw.strip()

        fw = WHITE_RE.sub(" ", fw.strip())
        if not fw or fw == "d":
            continue
        fw = fw.replace("ë", "e").replace("é", "e").replace("ó", "o")
        if IGNORE_RE.search(fw):
            continue
        wrong = IS_TEXT_1_RE.search(fw) or (IS_TEXT_2_RE.search(fw) and len(fw) > 100)
        if wrong:
            fwh.write(f"{page}\t{fw}\n")
        else:
            fw = fw.lower()

            if showOrig:
                orig2 = fw
            for (variant, intention) in NAME_SANITY:
                fw = fw.replace(variant, intention)

            fw = WHITE_RE.sub(r" ", fw.strip())

            for (i, (label, trimRe, trimRepl)) in enumerate(GOOD_STRIPE):
                fw = trimRe.sub(trimRepl, fw)

            fw = fw.replace("ö", "o").replace("ï", "i")
            fw = WHITE_RE.sub(" ", fw.strip())
            names = sorted(wl for w in fw.split() if (wl := w.lower()) not in STOPWORDS)

            if showOrig and orig:
                captionInfo[f"ORIG1 {orig}"].append(page)
                captionInfo[f"ORIG2 {orig2}"].append(page)
                captionInfo[f"PROC {fw}"].append(page)
            for name in names:
                if not name:
                    continue
                if name in NAMES:
                    captionNorm[name].append(page)
                elif name in NAME_VARIANTS:
                    name = NAME_VARIANTS[name]
                    captionNorm[name].append(page)
                else:
                    captionVariant[name].append(page)

    text = CLEAR_FW_RE.sub(checkFw, text)
    for trimRe in (
        FAMILY_RE,
        SPACING_RE,
        HEIGHT_RE,
        MARGIN_RE,
        ALIGN_RE,
        SIZE_RE,
    ):
        text = trimRe.sub("", text)

    text = DEG_RE.sub(r"\2\1", text)

    for (trimRe, val) in ((F_RE, "ƒ"),):
        text = trimRe.sub(val, text)

    text = HI_SUBSUPER_RE.sub(r"\1\2\3>", text)
    text = HI_EMPH_RE.sub(r"\1emphasis\2>", text)
    text = HI_UND_RE.sub(r"<und>\1</und>", text)

    for (trimRe, val) in (
        (SIZE_XLARGE_RE, "xlarge"),
        (SIZE_LARGE_RE, "large"),
        (SIZE_SMALL_RE, "small"),
        (SIZE_XSMALL_RE, "xsmall"),
        (SMALLCAPS_RE, "smallcaps"),
        (OUTDENT_RE, "outdent"),
        (INDENT_RE, "indent"),
    ):
        text = trimRe.sub(val, text)

    text = SUB_RE.sub(r"<sub>\1</sub>", text)
    text = SUPER_RE.sub(r"<super>\1</super>", text)
    text = SUBSUPER_MOVE_RE.sub(r"\1\4\3", text)
    text = SUBHEAD_RE.sub(r"<subhead>\1</subhead>", text)
    text = FIRST_P_SMALL_RE.sub(firstPRepl, text)

    for trimRe in (FONT_STYLE_RE, ALIGN_V_RE, ALIGN_H_RE, DECORATION_RE):
        text = trimRe.sub(r"\1", text)

    text = STRIP_RE.sub(stripRendAtt, text)
    text = text.replace(''' rend=""''', "")
    text = text.replace(''' rend=" "''', "")

    text = HI_CLEAN_RE.sub(r"""\1""", text)
    text = HI_SPECIAL_RE.sub(r"""\1\2\3\4""", text)
    text = text.replace("<hi/>", "")

    text = HALF_RE.sub(r"½\1", text)

    folioUndecided = info["folioUndecided"]
    folioFalse = info["folioFalse"]
    folioTrue = info["folioTrue"]
    folioResult = info["folioResult"]

    newText = []
    lastPos = 0

    text = FOLIO_KA_RE.sub(r"""<folio>\2</folio>\n""", text)
    text = FOLIO_PAGE_RE.sub(folioPageRepl, text)

    for tmatch in FOLIO_TRIGGER_RE.finditer(text):
        (btag, space, pre, fol, post, etag) = tmatch.group(*range(1, 7))
        (b, e) = tmatch.span()
        newText.append(text[lastPos:b])
        lastPos = e

        before = ""

        if pre:
            if pre == "i" or pre == "r":
                pre = ""
            else:
                pre = pre.replace("J 169", "1169")
                ka = pre.find("Kol.")
                if ka > 0:
                    before = pre[0:ka]
                    pre = pre[ka:]
                else:
                    match = FOLIO_TWEAK_RE.match(pre)
                    if match:
                        before = match.group(1)
                        pre = match.group(2)
                    else:
                        if len(pre) > 4 and pre[-4:].isdigit():
                            before = pre
                            pre = ""
        if fol[-1].isalpha() and post and post[0].isalpha():
            newText.append(text[b:e])
            continue

        fol = fol.strip().replace("\n", " ").replace(" ,", ",")
        pre = pre.strip().replace("\n", " ").replace(" ,", ",")
        post = post.strip().replace("\n", " ").replace(" ,", ",")

        if FOLIO_FALSE_RE.match(fol):
            folioFalse[fol].append(page)
            newText.append(text[b:e])
            continue

        if FOLIO_TRUE_RE.match(fol):
            folioTrue[fol].append(page)
            (post, after) = getFolioPost(post)
            newText.append(
                f"{btag}{space}{before}<folio>{pre}{fol}{post}</folio>{after}{etag}"
            )
            continue

        if FOLIO_COND_RE.match(fol):
            if (pre == "" and post.endswith("brief")) or FOLIO_PRE_FALSE_RE.match(pre):
                folioFalse[fol].append(page)
                newText.append(text[b:e])
                continue

            if pre == "[" or pre == "" or FOLIO_PRE_TRUE_RE.match(pre):
                folioTrue[fol].append(page)
                (post, after) = getFolioPost(post)
                newText.append(
                    f"{btag}{space}{before}<folio>{pre}{fol}{post}</folio>{after}{etag}"
                )
                continue

        folioUndecided[fol][f"{pre}├{fol}┤{post}"].append(page)
        newText.append(text[b:e])

    newText.append(text[lastPos:])
    text = "".join(newText)

    text = FOLIO_MERGE_RE.sub(r"""\1 \3\2\4""", text)

    text = FOLIO_RESULT_RE.sub(folioSepRepl, text)

    for match in FOLIO_RESULT_RE.finditer(text):
        fol = match.group(1)
        if "<" in fol:
            print(f"\nFOLIO has subelements: `{fol}`")
        folioResult[fol].append(page)

    text = FOLIO_ISOLATE_RE.sub(r"""\2""", text)
    text = FOLIO_LB_RE.sub(r"""\1""", text)

    for trimRe in FOLIO_MOVE:
        text = trimRe.sub(r"""\2\n\1""", text)

    headInfo = info["headInfo"]

    text = HEAD_TITLE_RE.sub(r"""\n<bigTitle>\1</bigTitle>\n""", text)
    text = HEAD_CLEAN_HI_RE.sub(r"""\1\2\3""", text)
    text = HEAD_CORRECT_NAME_RE.sub(r"""\n<subhead>\1</subhead>\n""", text)
    text = HEAD_CORRECT_RE.sub(headCorrectRepl, text)
    text = HEAD_CORRECT_N_RE.sub(r"""\n<head>\2</head>\n\1\3""", text)
    text = HEAD_CORRECT_NUM_RE.sub(r"""\n<p>\1</p>\n""", text)
    text = HEAD_NOTE_RE.sub(
        r"""<head>\1</head>\n<note resp="editor">\2</note>\n""", text
    )
    for match in HEAD_RE.finditer(text):
        head = match.group(1)
        head = HI_CLEAN_STRONG_RE.sub(
            r"""\1""", head.replace("<lb/>", " ").replace("\n", " ")
        )
        headInfo[doc].append((page, head))

    for rom in ROMANS:
        info["captionRoman"][rom].append(page)

    text = CELL_RE.sub(removePs, text)

    return text
