import sys
import re

from lib import WHITE_RE, TRIM_DIR


processPage = None


def stripRendAtt(match):
    material = match.group(1).replace(";", " ")
    if material == "" or material == " ":
        return ""
    material = WHITE_RE.sub(" ", material)
    material = material.strip()
    return f''' rend="{material}"'''


CLEAR_FW_RE = re.compile(r"""<fw\b[^>]*>(.*?)</fw>""", re.S)

FWH = None


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
                Index
                |
                (?:IN[DIO][A-Z\ -]*X)
                |
                TOELICH|Toelich
                |
                persoonsnamen
                |
                (?:
                    [0-9\ ]*
                    $
                )
            )
        """,
    re.S | re.X,
)

COMMA = r"""[.,’'`]"""
DIGIT_OCR = r"""=\]'coöjsgbil"""
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


GOOD_STRIPE = (
    (
        re.compile(
            fr"""[^a-z0-9{DIGIT_OCR}.,’`:;"{{}}\[!@$%^&*()_+=|\\~<>?/ \t\n-]""", re.S
        ),
        r"x",
    ),
    (re.compile(fr"""{NONWORD}.[un][zar]\b{COMMA}*\s*""", re.S), SPACE_REPL),
    (re.compile(rf"""{NUM_PAT}\s*""", re.S | re.X), SPACE_REPL),
    (re.compile(fr"""{COMMA}\s*""", re.S), SPACE_REPL),
    (re.compile(r"""&[a-z]+;\s*""", re.S), SPACE_REPL),
    (re.compile(r"""\b[oe][ni]i?\b\s*""", re.S), SPACE_REPL),
    (re.compile(r"""\bhe\b\s*"""), SPACE_REPL),
    (
        re.compile(r"""\b[iïjvyxlcdmnthuüe3][iïjvyxlcdmnthuüae13]*\b\s*""", re.S),
        SPACE_REPL,
    ),
    (
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
    (re.compile(r"""[^a-zöï ]+"""), r""),
)


NAME_SANITY = tuple(
    entry[0:-1].split("=")
    for entry in """
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
gij seis=gijsels .
harte inck=hartsinck .
ho orn=hoorn .
luca-sz=lucasz .
maotsuj'ker=maetsuycker .
mae o suy ker=maetsuycker .
maets yker=maetsuycker .
o suy ker=maetsuycker .
yker,maetsu=maetsuycker .
oud.tsh.oorn=oudtshoorn .
o utho om=oudtshoorn .
st/eur=steur .
v an=van .
v au=van .
vau=van .
yan=van .
a&n=van .
w'elsmg=welsing .
""".strip().split(
        "\n"
    )
)

TEST_TEXTS = ("ö81",)
TEST_TEXTS = ()


def test():
    for fw in TEST_TEXTS:
        fw = fw.lower()
        print(f"TEST -1: {fw}")

        for (variant, intention) in NAME_SANITY:
            fw = fw.replace(variant, intention)
        print(f"TEST  0: {fw}")

        for (i, (trimRe, trimRepl)) in enumerate(GOOD_STRIPE):
            fw = trimRe.sub(trimRepl, fw)
            print(f"TEST  {i + 1}: {fw}")

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

SHOW_ORIG = set(
    """
02:p0443
""".strip().split()
)

NAME_REPLACEMENTS_DEF = """
alphen
    aiphen
    alplien

barendsz
    jbarendsz

bent

blom

bogaerde
    bogaorde

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

caron

carpentier
    carpentiei
    carpentior
    carperntier

croocq

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

diemen
    diemeu
    dieraen
    diernen
    diomen

dutecum
    dutecom
    duteeum
    duteuum

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

heuvel

hoorn
    iioora

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

joan
    joon

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

overtwater
    vertwater
    ovemvater
    overtwaoer
    overtwator
    ovortwater
    xvertwater
    overfcwater

paviljoen

philips

pit
    pits

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

reyersz
    ileyersz

reynst

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

thijsz
    tbijsz
    tliijsz
    thxjsz

twist

uffelen
    uffeleii

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

welsing
    weising
    welging
    welgingen
    welsingen

willem

with
    witii
    wxth
    wxtii

witsen
    witaen
    wxtsen

ysbrantsz

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


def trimPage(text, info, *args, **kwargs):
    if "fwh" not in info:
        info["fwh"] = open(f"{TRIM_DIR}1/fwh-no.tsv", "w")
    fwh = info["fwh"]
    captionInfo = info["captionInfo"]
    captionNorm = info["captionNorm"]
    captionVariant = info["captionVariant"]
    page = info["page"]
    showOrig = f"{page[0:4]}{page[9:]}" in kwargs.get("orig", set())

    for fw in CLEAR_FW_RE.findall(text):
        if showOrig:
            orig = fw.strip()

        fw = WHITE_RE.sub(" ", fw.strip())
        fw = (
            fw.replace("&amp;", "&")
            .replace("&quot;", '"')
            .replace("&apos;", "'")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("é", "e")
            .replace("ó", "o")
        )
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

            for (i, (trimRe, trimRepl)) in enumerate(GOOD_STRIPE):
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

    # text = CLEAR_FW_RE.sub(checkFw, text)

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
