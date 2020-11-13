import collections
import re

from distill import META_KEY_ORDER, EXTRA_META_KEYS, DERIVED_META_KEYS, checkMeta
from lib import REPORT_DIR, WHITE_RE, CELL_RE, GT, LT, AMP, docSummary

corpusPre = None
trimVolume = None
trimDocBefore = None
processPage = None
trimDocPost = None


STAGE = 2
REP = f"{REPORT_DIR}{STAGE}"

WHITE_B_RE = re.compile(r"""(>)\s+""", re.S)
WHITE_E_RE = re.compile(r"""\s+(<)""", re.S)

DEL_TBL_ELEM = re.compile(r"""</?(?:lb|p)/?>""", re.S)
ROW_RE = re.compile(r"""<row>(.*?)</row>""", re.S)
TABLE_RE = re.compile(r"""<table>(.*?)</table>""", re.S)

P_RE = re.compile(r"""(</?)p\b""", re.S)

CHECK_RE = re.compile(r"""<hi rend="(?:small-caps|sub|large)">(.*?)</hi>""", re.S)
DELETE_REND_RE = re.compile(
    r"""(<(?:note|head|para)\b[^>]*?) rend=['"][^'"]*['"]""", re.S
)
EMPH_RE = re.compile(r"""<hi rend="emphasis">(.*?)</hi>""", re.S)
SMALL_RE = re.compile(r"""<hi rend="small[^"]*">(.*?)</hi>""", re.S)
SMALLX_RE = re.compile(r"""<hi rend="xsmall[^"]*">(.*?)</hi>""", re.S)
LARGE_RE = re.compile(r"""<hi rend="large[^"]*">(.*?)</hi>""", re.S)
LARGEX_RE = re.compile(r"""<hi rend="xlarge[^"]*">(.*?)</hi>""", re.S)
SUPER_RE = re.compile(r"""<hi rend="super[^"]*">(.*?)</hi>""", re.S)
REF_RE = re.compile(r"""<hi>(.*?)</hi>""", re.S)
REMARK_NOTE_RE = re.compile(r"""<note\b[^>]*?\bresp="editor"[^>]*>(.*?)</note>""", re.S)
REMARK_EXTRA_RE = re.compile(r"""<note\b[^>]*>(\(.*?)</note>""", re.S)
REMARK_EMPH_RE = re.compile(
    r"""(<remark>)\s*<emph>(.*?)</emph>(.*?)(</remark>)""", re.S
)
REMARK_STRIP_RE = re.compile(r"""</?remark>""")
NOTE_STRIP_RE = re.compile(r"""</?note>""")


def trimDocPrep(info, metaText, bodyText, previousMeta):
    header = checkMeta(metaText, bodyText, info, previousMeta)
    return (header, bodyText)


def corpusPost(info):
    table = info["table"]
    tableDiag = info["tableDiag"]

    nPatho = 0

    with open(f"{REP}/tableDiag.txt", "w") as fh:
        for (n, tableInfo) in tableDiag.items():
            doc = tableInfo["doc"]
            rows = tableInfo["rows"]
            cells = tableInfo["cells"]
            pathos = tableInfo["pathos"]
            empties = tableInfo["empties"]
            pathoMeasure = int(round(100 * pathos / (cells - empties)))
            pathoRep = f"{pathoMeasure:>3}% ({pathos:>3} out of {cells - empties:>3})"
            if pathoMeasure > 10:
                nPatho += 1
                pathoRep += " PATHOLOGICAL"
            fh.write(
                f"{n:>3} {doc} {rows:>3} rows, {cells:>4} cells"
                f" P={pathoRep}\n"
            )

    print(f"TABLES: {table} x (of which {nPatho} pathological")

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


def formatTablePre(info):
    return lambda match: formatTable(match, info)


PATHO_CHAR = fr"""[*•■±§—‘£.()<>'!?,.:;\[\]{{}}+={AMP}%$#@^\\/_-]"""
PATHO_CHAR_RE = re.compile(PATHO_CHAR, re.S | re.X)

PATHO_RE = re.compile(
    fr"""
    ^
    (?:
        [a-zA-Z0-9]
        |
        {PATHO_CHAR}
    )
    $
    """,
    re.S | re.X,
)

SANE_RE = re.compile(
    r"""
    ^
        g[li]-
        |
        [0-9]+\)
        |
        (?:
            (?:
                [0-9]+
                |
                [A-Z]?[a-z]+
            )
            (?:
                \s+
                (?:
                    [0-9]+
                    |
                    [A-Z]?[a-z]+
                )
            )*
        )
    $""",
    re.S | re.X,
)

QUOTE_RE = re.compile(r"""^[_.’'"«»,„/<>()]+$""")


def hasPathoContent(cell):
    cell = (
        cell.replace(f"{GT}{GT}", "»")
        .replace(f"{LT}{LT}", "«")
        .replace("''", '"')
        .replace(",,", "„")
        .strip()
        .rstrip(".")
    )
    if not cell or cell == "-" or cell == "—":
        return False

    parts = cell.split()

    parts = [p for p in parts if not QUOTE_RE.match(p)]

    if not parts:
        return False

    if len(parts) > 2 or max(len(p) for p in parts) > 3 or SANE_RE.match(cell):
        return False

    for p in parts:
        if len(p) > 1 and p.startswith("0"):
            return True
        if p.isdigit():
            return False
        if PATHO_CHAR_RE.search(p):
            return True

        if PATHO_RE.match(p):
            return True

    return False


def formatTable(match, info):
    tableDiag = info["tableDiag"]
    doc = info["doc"]
    info["table"] += 1
    n = info["table"]
    remarkInfo = info["remarks"]

    table = match.group(1)
    table = DEL_TBL_ELEM.sub(r" ", table)
    for trimRe in (WHITE_B_RE, WHITE_E_RE):
        table = trimRe.sub(r"""\1""", table)
    table = WHITE_RE.sub(r" ", table)

    result = []
    result.append(f"""\n<table n="{n}">""")
    rows = ROW_RE.findall(table)

    nCells = 0
    pathos = 0
    empties = 0
    for (r, row) in enumerate(rows):
        result.append(f"""<row n="{n}" row="{r + 1}">""")
        cells = CELL_RE.findall(row)
        nCells += len(cells)

        for (c, cell) in enumerate(cells):
            cell = NOTE_STRIP_RE.sub("", cell)
            if not cell:
                empties += 1
            elif hasPathoContent(cell):
                # print(f"PATHO=`{cell}`")
                pathos += 1
            result.append(
                f"""<cell n="{n}" row="{r + 1}" col="{c + 1}">{cell}</cell>"""
            )
        result.append("</row>")

    result.append("</table>\n")
    table = "\n".join(result)
    (table, nRemarks) = REMARK_STRIP_RE.subn(r"", table)
    nRemarks //= 2
    if nRemarks > nCells // 2:
        table = f"<remark>\n{table}</remark>"
        remarkInfo["n"] -= nRemarks

    diag = dict(doc=doc, rows=len(rows), cells=nCells, pathos=pathos, empties=empties)
    tableDiag[n] = diag

    return table


def trimPage(text, info, *args, **kwargs):
    remarkInfo = info["remarks"]
    text = P_RE.sub(r"""\1para""", text)
    text = DELETE_REND_RE.sub(r"\1", text)
    text = EMPH_RE.sub(r"<emph>\1</emph>", text)
    text = CHECK_RE.sub(r"<special>\1</special>", text)
    text = SUPER_RE.sub(r"<super>\1</super>" "", text)
    text = SMALL_RE.sub(r"\1", text)
    text = SMALLX_RE.sub(r"<special>\1</special>", text)
    text = LARGE_RE.sub(r"\1", text)
    text = LARGEX_RE.sub(r"<special>\1</special>", text)
    (text, nR) = REMARK_NOTE_RE.subn(r"""\n<remark>\1</remark>\n""", text)
    (text, nRx) = REMARK_EXTRA_RE.subn(r"""\n<remark>\1</remark>\n""", text)
    remarkInfo["n"] += nR
    remarkInfo["nx"] += nRx
    text = REMARK_EMPH_RE.sub(r"""\1\2\3\4""", text)
    text = REF_RE.sub(r"""<ref>\1</ref>""", text)
    text = TABLE_RE.sub(formatTablePre(info), text)
    return text
