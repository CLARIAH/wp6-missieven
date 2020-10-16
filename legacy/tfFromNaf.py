import sys
import os
import re
import collections
from itertools import chain
from shutil import rmtree

import yaml

from tf.fabric import Fabric
from tf.convert.walker import CV

# CONFIG READING


def readYaml(fileName):
    if os.path.exists(fileName):
        with open(fileName) as y:
            y = yaml.load(y, Loader=yaml.FullLoader)
    else:
        y = {}
    return y


# LOCATIONS

LOCAL = os.path.expanduser("~/local")
BASE = os.path.expanduser("~/github")
ORG = "Dans-labs"
REPO = "clariah-gm"

REPO_DIR = f"{BASE}/{ORG}/{REPO}"
SOURCE_DIR = f"{LOCAL}/{REPO}"

DECL_PATH = f"{REPO_DIR}/yaml"
META_DECL_FILE = f"{DECL_PATH}/meta.yaml"

META_DECL = readYaml(META_DECL_FILE)

VERSION_SRC = META_DECL["versionSrc"]
VERSION_TF = META_DECL["versionTf"]

IN_DIR = f"{SOURCE_DIR}/{VERSION_SRC}/naf"
PLAIN_DIR = f"{SOURCE_DIR}/{VERSION_SRC}/plain"
WORD_DIR = f"{SOURCE_DIR}/{VERSION_SRC}/word"

TF_DIR = f"{REPO_DIR}/tf"
OUT_DIR = f"{TF_DIR}/{VERSION_TF}"


# TF CONFIGURATION

slotType = "word"

generic = {
    k: META_DECL[k]
    for k in """
    name
    title
    editor
    published
    period
    language
    institute
    project
    researcher
    converters
""".strip().split()
}

otext = {
    "fmt:text-orig-full": "{trans}{punc}",
    "sectionFeatures": "title,number,number",
    "sectionTypes": "letter,section,p",
}

intFeatures = set(
    """
        number
        vol
    """.strip().split()
)

featureMeta = {
    "title": {"description": "short title of letter, from fileDesc element"},
    "location": {"description": "location from letter was sent, from fileDesc element"},
    "vol": {"description": "volume number"},
    "data": {"description": "date when letter was sent, from fileDesc element"},
    "lid": {"description": "ID of letter, from fileDesc element"},
    "number": {"description": "number of a letter, page, paragraph"},
    "trans": {"description": "transcription of a word"},
    "punc": {
        "description": "whitespace and/or punctuation following a word"
        "up to the next word"
    },
}

# ERROR HANDLING


def showDiags(diags, kind, batch=20):
    if not diags:
        print("No diags")
    else:
        for (diag, srcs) in sorted(diags.items()):
            print(f"{kind} {diag}")
            for (src, data) in sorted(srcs.items()):
                print(f"\t{src} ({len(data)}x)")
                for (l, line, doc, sore) in sorted(data)[0:batch]:
                    soreRep = "" if sore is None else f'"{sore}" in '
                    print(f"\t\t{l} in {doc}: {soreRep}{line}")
                if len(data) > batch:
                    print("\t\t + more")


# SET UP CONVERSION


def getConverter():
    TF = Fabric(locations=OUT_DIR)
    return CV(TF)


def convert(generateTf):
    if generateTf:
        if os.path.exists(OUT_DIR):
            rmtree(OUT_DIR)
        os.makedirs(OUT_DIR, exist_ok=True)

    cv = getConverter()

    return cv.walk(
        director,
        slotType,
        otext=otext,
        generic=generic,
        intFeatures=intFeatures,
        featureMeta=featureMeta,
        generateTf=generateTf,
    )


# DIRECTOR


RAW_RE = re.compile(r"""<raw><!\[CDATA\[(.*?)\]\]></raw>""", re.S)
TUNITS_RE = re.compile(r"""<tunits>(.*?)</tunits>""", re.S)
TUNIT_RE = re.compile(
    r"""
    <tunit
        \s+
        id="([^"]*)"
        \s+
        type="([^"]*)"
        \s+
        xpath="([^"]*)"
        \s+
        offset="([^"]*)"
        \s+
        length="([^"]*)"
        \s*/>
    """,
    re.S | re.X,
)
ROMAN_RE = re.compile(r"""^(?:[IVXL]\s?)+""")

SPACE_RE = re.compile(r"""  +""")

LINE_LENGTH = 100


def normalize(content, standoff):
    normalized = content.replace("\n", " ")
    lenNormalized = len(normalized)

    # we change the source text, so we have to update all standoff annotations
    # we maintain a mapping from old positions to new positions
    # we change the mapping after each change in the source

    # note that a position can refer to just after the last character

    posMapping = {i: i for i in range(lenNormalized + 1)}

    # detect the collapsible white spaces
    # adapt the mapping to the fact that we collapse each white strectch to
    # exactly one space

    # we keep track of the amount of deleted material when we pass through the text
    # we keep track of the original position just after the last stretch
    shrunk = 0
    lastPos = 0

    for match in SPACE_RE.finditer(normalized):
        (b, e) = match.span()
        shift = e - b

        # apply the shrunk from after the last stretch to just before this stretch:
        for i in range(lastPos, b):
            posMapping[i] -= shrunk

        # all positions within the stretch translate to its first position
        for i in range(b, e + 1):
            posMapping[i] = b - shrunk

        # update shrunk and lastPos

        shrunk += shift
        lastPos = e + 1

    # apply the shrunk to everything after the last stretch

    for i in range(lastPos, lenNormalized + 1):
        posMapping[i] -= shrunk

    # now we can collapse the white space

    normalized = SPACE_RE.sub(" ", normalized)
    lenNormalized = len(normalized)

    # we adapt all standoff annotations, using the posMapping

    normStandoff = {}
    for (tp, annotations) in standoff.items():
        normStandoff[tp] = tuple(
            (posMapping[annot[0]], posMapping[annot[1]]) for annot in annotations
        )

    # we produce tab separated lines for the standoff annotations

    normStandoffLines = []
    for (tp, annotations) in sorted(normStandoff.items()):
        for (start, end) in annotations:
            normStandoffLines.append(f"{tp}\t{start}\t{end}")

    # we chop the normalized text in lines of fixed length (except for the last line)

    nWholeLines = int(lenNormalized // LINE_LENGTH)
    nLines = nWholeLines + (1 if lenNormalized % LINE_LENGTH else 0)

    lines = []
    for i in range(nLines):
        start = i * LINE_LENGTH
        lines.append(normalized[start : min((lenNormalized, start + LINE_LENGTH))])

    # deliver the chopped, normalized text and the modified annotations in tsv

    return ("\n".join(lines), "\n".join(normStandoffLines))


def wordify(text, standoff):
    lenText = len(text)
    # determine start and end points of annotations
    # note that we do not take the starts of zero-length annotations,
    # but we will take the ends of them
    starts = {
        annot[0]
        for annot in chain.from_iterable(standoff.values())
        if annot[0] != annot[1]
    }
    # note that the end points at the first character after the annotation
    # note that zero-length annotations starting at 0 have end 0, so
    # we get -1 in the ends!
    ends = {
        e - 1
        for annot in chain.from_iterable(standoff.values())
        if (e := annot[1]) == lenText or text[e] != " "
    } - {-1}
    boundaries = starts | ends

    # we construct a mapping of character positions to word positions (posMap)
    # we collect the words by splitting at spaces and annotation boundaries
    # we maintain the current word number
    # and the starting char pos of the first word that has not yet been appended

    posMap = {}
    words = []
    curPos = 0
    nextI = 0

    for (n, c) in enumerate(text):
        if n == 0:
            # we discard an initial space
            if c == " ":
                nextI = 1
                continue

        # a word boundary may be a space
        elif n < lenText - 1 and c == " ":

            # we add the word before this space, including the space itself
            words.append(text[nextI : n + 1])
            curPos += 1

            # we map all char positions in this word to its word number
            # and update the fresh word position
            for i in range(nextI, n):
                posMap[i] = curPos
            nextI = n + 1

            # we map the space itself to the new word position
            # but marked by a negative value for case distinction later on
            posMap[n] = -curPos

        # or a standoff boundary
        elif n in boundaries:

            # if it is a start and an end, it is a word on its own
            if n in starts and n in ends:
                if nextI < n:
                    words.append(text[nextI:n])
                    curPos += 1
                    for i in range(nextI, n):
                        posMap[i] = curPos
                    nextI = n

                words.append(text[n : n + 1])
                curPos += 1
                posMap[n] = curPos
                nextI = n + 1

            # if it is a start only, then the boundary is before this position
            elif n in starts:
                if nextI < n:
                    words.append(text[nextI:n])
                    curPos += 1
                    for i in range(nextI, n):
                        posMap[i] = curPos
                    nextI = n

            # if it is an end only, then the boundary is after this position
            elif n in ends:
                if nextI < n + 1:
                    words.append(text[nextI : n + 1])
                    curPos += 1
                    for i in range(nextI, n + 1):
                        posMap[i] = curPos
                    nextI = n + 1

        # we may have reached the end of the text
        if n == lenText - 1:
            # we discard a final space
            stopI = lenText - 1 if c == " " else lenText
            if nextI < stopI:
                words.append(text[nextI:stopI])
                curPos += 1
                for i in range(nextI, stopI):
                    posMap[i] = curPos

    # with this mapping we can translate the char addressing of standoff annotations
    # to word addressing.

    # For character positions inside words it is easy:
    # they translate to the word number.

    # Character positions at spaces are special:
    # start offsets of annotations that target a space mean: the next word.
    # end offsets of annotations that target a space mean: the previous word.
    # Zero-width annotations follow their end position: they are attached to the
    # previous word.

    # We discard zero width annotations at the start: we assume they are page breaks,
    # we warn if we see others.

    report = collections.Counter()

    wordStandoff = []

    for (tp, annotations) in standoff.items():
        for (start, end) in annotations:
            pEnd = end - 1

            if start == 0 and end == 0 and tp != "pb":
                report[tp] += 1

            # zero length annotations attach to the previous word
            if start == end:
                if start == 0:
                    continue

                wordEnd = posMap[pEnd]
                if wordEnd < 0:
                    wordEnd = -wordEnd - 1
                wordStart = wordEnd

            else:
                wordStart = abs(posMap[start])
                wordEnd = posMap[pEnd]
            if wordEnd < 0:
                wordEnd = -wordEnd - 1

            # we store the word end negatively, for sorting purposes
            wordStandoff.append((wordStart, -wordEnd, tp))

    wordStandoffTsv = tuple(f"{tp}\t{b}\t{-e}" for (b, e, tp) in sorted(wordStandoff))

    return (words, wordStandoffTsv, report)


def getVolumes(srcDir):
    volumes = []
    with os.scandir(srcDir) as dh:
        for entry in dh:
            if entry.is_dir():
                vol = entry.name
                if not vol.isdigit():
                    continue
                volumes.append(int(vol))
    return sorted(volumes)


def getLetters(srcDir):
    letters = []

    with os.scandir(srcDir) as dh:
        for entry in dh:
            if entry.is_file():
                name = entry.name
                if name.endswith(".txt"):
                    lid = name[0:-4]
                    letters.append(lid)
    return tuple(sorted(letters))


def shortenIds():
    # reduce the big, opaque file names to shorter file names
    # check whether there are collisions

    volumes = getVolumes(IN_DIR)
    idMap = {}
    letters = {}

    collisions = 0

    for vol in volumes:
        thisInDir = f"{IN_DIR}/{vol}"

        thisIdMap = {}
        theseLetters = []

        with os.scandir(thisInDir) as vdh:
            for entry in vdh:
                if entry.is_file():
                    name = entry.name
                    if name.endswith(".naf"):
                        lid = name.split('_')[1]
                        if lid in thisIdMap:
                            collisions += 1
                        else:
                            thisIdMap[lid] = name
                        theseLetters.append(lid)
        letters[vol] = tuple(sorted(theseLetters))
        idMap[vol] = thisIdMap

    if collisions:
        print(f"MAPPING to short letter ids: {collisions} collisions")
        return False
    else:
        print("No collisions while constructing short letter ids")
    return (volumes, letters, idMap)


def makePlain(volumes, letters, idMap):
    # transform the NAF in noise free plain text files:
    #
    # the raw text in a block of 100-char wide lines,
    # so that offsets can be read off easily in a text editor
    # normalized white space
    #
    # Standoff annotations adapted to the normalization,
    # stored in tab-separated lines: element start end
    #
    # Collect statistics on elements

    # clean up previous content and make fresh directory

    if os.path.exists(PLAIN_DIR):
        rmtree(PLAIN_DIR)
    os.makedirs(PLAIN_DIR, exist_ok=True)

    nLetters = 0
    elements = collections.Counter()
    elementSize = collections.Counter()

    print("Make plain ...")

    for vol in volumes:
        lids = letters[vol]
        thisInDir = f"{IN_DIR}/{vol}"
        thisPlainDir = f"{PLAIN_DIR}/{vol}"
        os.makedirs(thisPlainDir)

        thisNLetters = len(lids)
        print(f"\tVolume {vol:>2} with {thisNLetters:>3} letters")

        for lid in lids:
            name = idMap[vol][lid]
            inPath = f"{thisInDir}/{name}"
            plainBase = f"{thisPlainDir}/{lid}"
            with open(inPath) as fh:
                content = fh.read()
            match = RAW_RE.search(content)
            if not match:
                content = ""
            else:
                orig = match.group(1)
            if orig == "":
                print(f"\tNo text in letter {lid} = {name}")
                continue
            nLetters += 1
            match = TUNITS_RE.search(content)
            if match:
                tunitsStr = match.group(1)
                tunits = TUNIT_RE.findall(tunitsStr)
            else:
                tunits = []

            standoff = {}
            for (lidPath, tp, xp, offset, length) in tunits:
                offset = int(offset)
                length = int(length)
                standoff.setdefault(tp, []).append((offset, offset + length))
                elements[tp] += 1
                elementSize[tp] += length

            for (tp, annotations) in standoff.items():
                standoff[tp] = tuple(annotations)

            (formatted, standoffTsv) = normalize(orig, standoff)

            with open(f"{plainBase}.txt", "w") as fh:
                fh.write(formatted)
            with open(f"{plainBase}.tsv", "w") as fh:
                fh.write(standoffTsv)

    print(f"Total {nLetters:>3} letters")
    for (tp, nTp) in sorted(elements.items()):
        tpSize = elementSize[tp]
        print(f"{nTp:>6} x {tp:<6} = {tpSize:>8} characters")

    return True


def makeWord():
    # transform the plain version in worded versions.
    # We split words at spaces and at start/end points of annotations
    # We represent the text in a file with just one word per line
    # We translate character positions to word positions.

    # clean up previous content and make fresh directory

    if os.path.exists(WORD_DIR):
        rmtree(WORD_DIR)
    os.makedirs(WORD_DIR, exist_ok=True)

    volumes = getVolumes(PLAIN_DIR)

    good = True

    print("Make worded ...")

    for vol in volumes:
        thisPlainDir = f"{PLAIN_DIR}/{vol}"
        thisWordDir = f"{WORD_DIR}/{vol}"
        os.makedirs(thisWordDir)

        lids = getLetters(thisPlainDir)
        thisNLetters = len(lids)
        print(f"\tVolume {vol:>2} with {thisNLetters:>3} letters")

        for lid in lids:
            if lid != 'p0033':
                continue
            plainBase = f"{thisPlainDir}/{lid}"
            wordBase = f"{thisWordDir}/{lid}"

            with open(f"{plainBase}.txt") as fh:
                text = "".join(line.rstrip("\n") for line in fh)

            standoff = {}
            with open(f"{plainBase}.tsv") as fh:
                for line in fh:
                    (tp, start, end) = line.rstrip("\n").split("\t")
                    start = int(start)
                    end = int(end)
                    standoff.setdefault(tp, []).append((start, end))
            for (tp, annotations) in standoff.items():
                standoff[tp] = tuple(annotations)

            (words, standoffTsv, report) = wordify(text, standoff)

            if report:
                print("\tUnexpected zero-length annotations:")
                for (tp, amount) in sorted(report.items()):
                    print(f"\t\t{amount:>3} x {tp}")
                good = False

            with open(f"{wordBase}.txt", "w") as fh:
                for word in words:
                    fh.write(f"{word}\n")

            with open(f"{wordBase}.tsv", "w") as fh:
                fh.write("\n".join(standoffTsv))
        break
    return good


def director(cv):

    # before we split into words, we insert nonbreaking spaces
    # at every location where a standoff element starts or terminates.
    # We get rid of these spaces when we perform the split.

    warnings = collections.defaultdict(lambda: collections.defaultdict(set))
    errors = collections.defaultdict(lambda: collections.defaultdict(set))

    for vol in VOLUMES:
        print(f"Volume {vol:>2}")

        curVol = cv.node("volume")
        cv.feature(curVol, vol=vol)

        volDir = f"{PLAIN_DIR}/{vol}"
        lids = []
        with os.scandir(volDir) as vdh:
            for entry in vdh:
                if entry.is_file():
                    name = entry.name
                    if name.endswith(".txt"):
                        lid = name[0:-4]
                        lids.append(lid)

        lids = sorted(lids)
        thisNLetters = len(lids)
        print(f"\t{thisNLetters:>3} letters")

        for lid in lids:
            textPath = f"{volDir}/{lid}.txt"
            standoffPath = f"{volDir}/{lid}.tsv"
            with open(textPath) as fh:
                text = "".join(line.rstrip("\n") for line in lines)
            standoff = {}
            with open(standoffPath) as fh:
                for line in fh:
                    (tp, start, end, length) = line.rstrip("\n").split("\t")
                    start = int(start)
                    length = int(length)
                    standoff.setdefault(tp, []).append(start, end)
            for (tp, annotations) in standoff.items():
                standoff[tp] = tuple(annotations)

            curLetter = cv.node("letter")
            cv.feature(curLetter, lid=lid, lidx=shortLid)
            slot = cv.slot()
            # before we split into words, we insert nonbreaking spaces
            # at every location where a standoff element starts or terminates.
            # We get rid of these spaces when we perform the split.
            words = content.split()
            cv.feature(slot, trans=words[0], punc=" ")
            cv.terminate(curLetter)

        cv.terminate(curVol)

    # delete meta data of unused features
    for feat in featureMeta:
        if not cv.occurs(feat):
            print(f"WARNING: feature {feat} does not occur")
            cv.meta(feat)

    if warnings:
        showDiags(warnings, "WARNING")
    if errors:
        showDiags(errors, "ERROR")


# TF LOADING (to test the generated TF)


def loadTf():
    TF = Fabric(locations=[OUT_DIR])
    allFeatures = TF.explore(silent=True, show=True)
    loadableFeatures = allFeatures["nodes"] + allFeatures["edges"]
    api = TF.load(loadableFeatures, silent=False)
    if api:
        print(f"max node = {api.F.otype.maxNode}")
        print("Frequency of readings")
        print(api.F.reading.freqList()[0:20])
        print("Frequency of grapheme")
        print(api.F.grapheme.freqList()[0:20])


# MAIN


def main():
    args = () if len(sys.argv) == 1 else tuple(sys.argv[1:])

    doPlain = "plain" in args
    doWord = "word" in args
    doWalk = "walk" in args
    doLoad = "load" in args

    print(f"NAF to TF converter for {REPO}")
    print(f"NAF source version = {VERSION_SRC}")
    print(f"TF  target version = {VERSION_TF}")

    if doPlain:
        result = shortenIds()
        if not result:
            return False
        if not makePlain(*result):
            return False

    if doWord:
        if not makeWord():
            return False

    if doWalk:
        if not convert(doLoad):
            return False

    if doLoad:
        loadTf()

    return True


sys.exit(0 if main() else 1)
