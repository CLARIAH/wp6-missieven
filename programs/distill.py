import re
from itertools import chain
from lib import GT, LT, AMP


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
    "01:p0003a": {"page"},
    "01:p0003b": {"page"},
    "01:p0003c": {"page"},
    "01:p0016a": {"page"},
    "01:p0016b": {"page"},
    "01:p0020b": {"page"},
    "01:p0020c": {"page"},
    "01:p0027a": {"page"},
    "01:p0027b": {"page"},
    "01:p0097a": {"page"},
    "01:p0097b": {"page"},
    "01:p0097c": {"page"},
    "01:p0097d": {"page"},
    "01:p0097e": {"page"},
    "01:p0097f": {"page"},
    "01:p0097g": {"page"},
    "01:p0098a": {"page"},
    "01:p0098b": {"page"},
    "01:p0098c": {"page"},
    "01:p0118a": {"page"},
    "01:p0118b": {"page"},
    "01:p0118c": {"page"},
    "01:p0118d": {"page"},
    "01:p0118e": {"page"},
    "01:p0118f": {"page"},
    "01:p0244a": {"page"},
    "01:p0244b": {"page"},
    "01:p0244c": {"page"},
    "01:p0244d": {"page"},
    "01:p0244e": {"page"},
    "01:p0244f": {"page"},
    "01:p0244g": {"page"},
    "01:p0244h": {"page"},
    "01:p0008": {"place"},
    "01:p0087": {"place"},
}
FROM_PREVIOUS = {"01:p0056"}

META_KV_2_RE = re.compile(r"""<meta key="([^"]*)" value="([^"]*)"/>""", re.S)
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

META_KEY_ORDER = tuple(x[0] for x in META_KEY_TRANS_DEF)
COLOFON_KEYS = META_KEY_ORDER[5:]

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

HEAD_RE = re.compile(r"""<head\b[^>]*>(.*?)</head>""", re.S)
FIRST_PAGE_RE = re.compile(r"""<pb\b[^>]*?\bn="([^"]*)"[^>]*>""", re.S)


def ucfirst(x, lower=True):
    return (x[0].upper() + (x[1:].lower() if lower else x[1:])) if x else x


def longestFirst(x):
    return -len(x)


NUM_SANITIZE_RE = re.compile(r"""[0-9][0-9 ]*[0-9]""", re.S)


def numSanitize(match):
    return f" {match.group(0).replace(' ', '')} "


HI_CLEAN_STRONG_RE = re.compile(r"""<hi\b[^>]*>([^<]*)</hi>""", re.S)

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

Ile

Jakatra

Kasteel

Makéan

Maleyo

Mauritius

Mayo

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

Tafelbaai

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
    liggende
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

antzen      s

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

blocq       s1

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

dircksz     f

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

duynen      s

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

lam         s

laurens     f

leene       s

lefebvre    s

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

martensz    s2

martinus    f

mattheus    f
    mat-theus

maurits     f

meester     s

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
                (?:
                    (?:
                        [0-9]
                        |
                        \bI
                    )
                    [0-9I]?
                )
                |
                (?:
                    (?:
                        (?:
                            [0-9]
                            |
                            \bI
                        )
                    )
                    \ [0-9I]
                )
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


SEP_RE = re.compile(r"""[ \n.,;]+""", re.S)


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

NOTEMARK_RE = re.compile(
    fr"""
    (?:
        \s*
        <super>
        (?:
            (?:
                &[^;]*;
            )
            |
            [iJlx0-9*'"!{GT}{LT}{AMP}]
        )
        \)?
        </super>
    )
    |
    (?:
        \s*
        (?:
            [iJlx0-9*'"!{GT}{LT}{AMP}]
        )
        \)
    )
    """,
    re.S | re.X,
)

BRACKET_RE = re.compile(r"""\s*\([^)]*\)\s*""", re.S)


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


def checkMeta(metaText, bodyText, info, previousMeta):
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
            label = "ok"
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


def roughlyEqual(v, d, lax=False):
    # print("RE v", v)
    # print("RE d", d)
    vWords = set(SEP_RE.sub(" ", v.lower()).split())
    dWords = set(SEP_RE.sub(" ", d.lower()).split())

    if lax:
        vWords = vWords - PLACES_LOWER - AUTHORS_LOWER
        dWords = dWords - PLACES_LOWER - AUTHORS_LOWER

    return vWords == dWords
