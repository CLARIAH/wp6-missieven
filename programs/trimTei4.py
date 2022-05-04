import re

corpusPre = None
trimVolume = None
trimDocBefore = None
trimDocPrep = None
processPage = None
trimDocPost = None
corpusPost = None

STAGE = 4

"""
Main function of this stage: move the footnote bodies to the place of the
footnote references.
"""


FNOTE_BODIES_RE = re.compile(r"""<fnote\b.*</fnote>""", re.S)
FNOTE_RE = re.compile(r"""<fnote ref="([^"]+)">(.*?)</fnote>""", re.S)

FNOTE_MARKS_RE = re.compile(r"""<fref ref="([^"]+)"/>""", re.S)

FOLIO_RE = re.compile(r"""</?folio>""")

SUPER_Q_RE = re.compile(r"""<super>(\s*[^ </][^/]*)/(\s*[^ <][^<]*)</super>""", re.S)

PB_RE = re.compile(r'''\b(?:facs|tpl)="[^"]*"''', re.S)


fNotes = {}


def getBodies(match):
    bodiesStr = match.group(0)
    for (mark, body) in FNOTE_RE.findall(bodiesStr):
        # remove folio refs inside a footnote
        fNotes[mark] = f"""<note mark="{mark}">{FOLIO_RE.sub("", body)}</note>"""
    return ""


def hoistBody(match):
    (fref, mark) = match.group(0, 1)
    return fNotes.get(mark, fref)


def trimPage(text, info, *args, **kwargs):
    if "<fnote ref=" not in text:
        return text

    fNotes.clear()
    text = FNOTE_BODIES_RE.sub(getBodies, text)
    text = FNOTE_MARKS_RE.sub(hoistBody, text)
    text = SUPER_Q_RE.sub(r"""<q><num>\1</num>/<den>\2</den></q>""", text)
    text = PB_RE.sub("", text)
    return text
