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
            fr"""[^a-z0-9{DIGIT_OCR}.,’`:;"{{}}\[!@$%^&*()_+=|\\~<>?/ \t\n-]""", re.S
        ),
        r"?",
    ),
    ("d.v.", re.compile(fr"""\b[dvy]{COMMA}\s*"""), SPACE_REPL),
    ("enz", re.compile(fr"""{NONWORD}.[un][vzar]\b{COMMA}*\s*""", re.S), SPACE_REPL),
    ("arabic", re.compile(rf"""{NUM_PAT}\s*""", re.S | re.X), SPACE_REPL),
    ("comma", re.compile(fr"""{COMMA}\s*""", re.S), SPACE_REPL),
    ("entity", re.compile(r"""&[a-z]+;\s*""", re.S), SPACE_REPL),
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
a&n=van .
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

SHOW_ORIG = set(
    """
02:p0443
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


def checkFw(match):
    fw = match.group(1).strip()
    fw = WHITE_RE.sub(" ", fw)
    if not fw or fw == "d":
        return ""
    orig = fw
    fw = (
        fw.replace("&amp;", "&")
        .replace("&quot;", '"')
        .replace("&apos;", "'")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("ë", "e")
        .replace("é", "e")
        .replace("ó", "o")
    )
    return (
        ""
        if IGNORE_RE.search(fw)
        or (
            not IS_TEXT_1_RE.search(fw)
            and (len(fw) <= 100 or not IS_TEXT_2_RE.search(fw))
        )
        else f"<p>{orig}</p>"
    )


FOLIO_RE = re.compile(
    r"""
        (^|<[^/][^>]*>)
        \s*
        ([^<]*)
        (
            fol
            \.?
            (?:io)?
            [^< ]*
        )
        ([^<]*)
        (<\/?[^>]*>)
    """, re.S | re.I | re.X)


def trimPage(text, info, *args, **kwargs):
    if "fwh" not in info:
        info["fwh"] = open(f"{TRIM_DIR}1/fwh-no.tsv", "w")
    fwh = info["fwh"]
    captionInfo = info["captionInfo"]
    captionNorm = info["captionNorm"]
    captionVariant = info["captionVariant"]
    page = info["page"]
    showOrig = f"{page[0:4]}{page[9:]}" in kwargs.get("orig", set())

    ROMANS.clear()

    for fw in CLEAR_FW_RE.findall(text):
        if showOrig:
            orig = fw.strip()

        fw = WHITE_RE.sub(" ", fw.strip())
        if not fw or fw == "d":
            continue
        fw = (
            fw.replace("&amp;", "&")
            .replace("&quot;", '"')
            .replace("&apos;", "'")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("ë", "e")
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

    folio = info['folio']
    for (btag, pre, fol, post, etag) in FOLIO_RE.findall(text):
        folio[fol].append(page)

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

    for rom in ROMANS:
        info["captionRoman"][rom].append(page)

    return text
