import sys
import re

from lib import WHITE_RE, TRIM_DIR, HI_CLEAN_STRONG_RE


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
    r"""
    ^(.*?)
    (
        \*\)[.•]
        | 1\)\.
        | &gt;\)\.
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
        r"""(<p\b[^>]*>[^>]+(?:<lb/>\s*)*)\s*(<folio>[^<]*</folio>)""",
        re.S,
    ),
)


HEAD_RE = re.compile(r"""<head\b[^>]*>(.*?)</head>""", re.S)

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
    ({HEAD_CORRECT})
    (<note)
    """,
    re.S | re.X,
)

HEAD_CORRECT_NUM_RE = re.compile(
    r"""
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
                &[a-z]+;
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
    return match.groups([1, 2]) if match else plain


# RETAIN
# (potlood
# (na fol
# (Copie
# (copie
# (secreet)
# (F-v
# (F.
# (folio 87


def checkFw(match):
    fw = match.group(1)
    fw = WHITE_RE.sub(" ", fw.strip())
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
    if IGNORE_RE.search(fw):
        return ""
    wrong = IS_TEXT_1_RE.search(fw) or (IS_TEXT_2_RE.search(fw) and len(fw) > 100)
    return f"<p>{orig}</p>" if wrong else ""


HEAD_TITLE_RE = re.compile(r"""<head rend="[^"]*?\bxlarge\b[^>]*>(.*?)</head>""", re.S)


def trimPage(text, info, *args, **kwargs):
    if "fwh" not in info:
        info["fwh"] = open(f"{TRIM_DIR}1/fwh-no.tsv", "w")
    fwh = info["fwh"]
    captionInfo = info["captionInfo"]
    captionNorm = info["captionNorm"]
    captionVariant = info["captionVariant"]
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

    folioUndecided = info["folioUndecided"]
    folioFalse = info["folioFalse"]
    folioTrue = info["folioTrue"]
    folioResult = info["folioResult"]

    newText = []
    lastPos = 0

    text = FOLIO_KA_RE.sub(r"""<folio>\2</folio>\n""", text)
    text = FOLIO_PAGE_RE.sub(r"""<folio>\2</folio>\n""", text)

    for tmatch in FOLIO_TRIGGER_RE.finditer(text):
        (btag, space, pre, fol, post, etag) = tmatch.groups(range(1, 7))
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

    for match in FOLIO_RESULT_RE.finditer(text):
        fol = match.group(1)
        if "<" in fol:
            print(f"\nFOLIO has subelements: `{fol}`")
        folioResult[fol].append(page)

    text = FOLIO_ISOLATE_RE.sub(r"""\2""", text)
    text = FOLIO_LB_RE.sub(r"""\1""", text)

    for trimRe in FOLIO_MOVE:
        text = trimRe.sub(r"""\2\1""", text)

    headInfo = info["headInfo"]

    text = HEAD_TITLE_RE.sub(r"""\n<bigTitle>\1</bigTitle>\n""", text)
    text = HEAD_CORRECT_NAME_RE.sub(r"""\n<subHead>\1</subHead>\n""", text)
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

    return text
