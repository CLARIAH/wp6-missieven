import re

from lib import WHITE_RE


def stripRendAtt(match):
    material = match.group(1).replace(";", " ")
    if material == "" or material == " ":
        return ""
    material = WHITE_RE.sub(" ", material)
    material = material.strip()
    return f''' rend="{material}"'''


CLEAR_FW_RE = re.compile(r"""<fw\b[^>]*>(.*?)</fw>""", re.S)


def checkFw(match):
    text = match.group(1)
    if len(text) > 100:
        return f"<p>{text}</p>"
    else:
        return ""


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
INDENT_RE = re.compile(r"""text-indent:\s*[^-][^;"']*;?""", re.S)
MARGIN_RE = re.compile(r"""margin-(?:[^:'"]*):[^;"']*;?""", re.S)
OUTDENT_RE = re.compile(r"""text-indent:\s*-[^;"']*;?""", re.S)
SIZE_RE = re.compile(r"""font-size:\s*(?:9\.5|10\.5|10)\s*[^;"']*;?""", re.S)
SIZE_BIG_RE = re.compile(r"""font-size:\s*(?:20|(?:1[1-9]))\.?5?[^;"']*;?""", re.S)
SIZE_SMALL_RE = re.compile(r"""font-size:\s*(?:9|(?:[6-8]))\.?5?[^;"']*;?""", re.S)
SIZE_XSMALL_RE = re.compile(r"""font-size:\s*(?:[1-5])\.?5?[^;"']*;?""", re.S)
SPACING_RE = re.compile(r"""letter-spacing:[^;"']*;?""", re.S)
STRIP_RE = re.compile(r""" rend=['"]([^'"]*)['"]""", re.S)
P_LB_RE = re.compile(r"""<lb/>\s*(</p>)""", re.S)


def trimPage(text, *args):
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
        (SIZE_BIG_RE, "large"),
        (SIZE_SMALL_RE, "small"),
        (SIZE_XSMALL_RE, "xsmall"),
        (OUTDENT_RE, "outdent"),
        (INDENT_RE, "indent"),
    ):
        text = trimRe.sub(val, text)

    for trimRe in (FONT_STYLE_RE, ALIGN_V_RE, ALIGN_H_RE, DECORATION_RE):
        text = trimRe.sub(r"\1", text)

    text = STRIP_RE.sub(stripRendAtt, text)
    text = text.replace(''' rend=""''', "")
    text = text.replace(''' rend=" "''', "")

    text = HI_CLEAN_RE.sub(r"""\1""", text)
    text = text.replace("<hi/>", "")

    text = HALF_RE.sub(r"½\1", text)

    return text
