import re

from lib import WHITE_RE

processPage = None

WHITE_B_RE = re.compile(r"""(>)\s+""", re.S)
WHITE_E_RE = re.compile(r"""\s+(<)""", re.S)

CELL_RE = re.compile(r"""<cell>(.*?)</cell>""", re.S)
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
SUPER_RE = re.compile(r"""<hi rend="super[^"]*">(.*?)</hi>""", re.S)
REF_RE = re.compile(r"""<hi>(.*?)</hi>""", re.S)
REMARK_NOTE_RE = re.compile(r"""<note\b[^>]*?\bresp="editor"[^>]*>(.*?)</note>""", re.S)
REMARK_EMPH_RE = re.compile(
    r"""(<remark>)\s*<emph>(.*?)</emph>(.*?)(</remark>)""", re.S
)


def formatTablePre(info):
    return lambda match: formatTable(match, info)


def formatTable(match, info):
    info["table"] += 1
    n = info["table"]

    table = match.group(1)
    table = DEL_TBL_ELEM.sub(r" ", table)
    for trimRe in (WHITE_B_RE, WHITE_E_RE):
        table = trimRe.sub(r"""\1""", table)
    table = WHITE_RE.sub(r" ", table)

    result = []
    result.append(f"""\n<table n="{n}">""")
    rows = ROW_RE.findall(table)

    for (r, row) in enumerate(rows):
        result.append(f"""<row n="{n}" row="{r + 1}">""")
        cells = CELL_RE.findall(row)

        for (c, cell) in enumerate(cells):
            result.append(
                f"""<cell n="{n}" row="{r + 1}" col="{c + 1}">{cell}</cell>"""
            )
        result.append("</row>")

    result.append("</table>\n")

    return "\n".join(result)


def trimPage(text, info, *args, **kwargs):
    text = TABLE_RE.sub(formatTablePre(info), text)
    text = P_RE.sub(r"""\1para""", text)
    text = DELETE_REND_RE.sub(r"\1", text)
    text = EMPH_RE.sub(r"<emph>\1</emph>", text)
    text = CHECK_RE.sub(r"<special>\1</special>", text)
    text = SUPER_RE.sub(r"<super>\1</super>" "", text)
    text = SMALL_RE.sub(r"\1", text)
    text = SMALLX_RE.sub(r"<special>\1</special>", text)
    text = REMARK_NOTE_RE.sub(r"""\n<remark>\1</remark>\n""", text)
    text = REMARK_EMPH_RE.sub(r"""\1\2\3\4""", text)
    text = REF_RE.sub(r"""[\1]""", text)
    return text
