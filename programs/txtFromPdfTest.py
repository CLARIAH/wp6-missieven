import fitz
import pprint as pp

from lib import PDF_DIR, TEST_DIR

pdfPage = 35


def pprint(x, fh=None):
    pp.pprint(x, stream=fh, indent=2)


class PText:
    def __init__(self, folder, pg):
        self.pg = pg
        self.doc = fitz.open(f"{folder}/{pg:>03}.pdf")

    def close(self):
        self.doc.close()

    def showText(self):
        doc = self.doc
        for page in doc:
            textPage = page.get_textpage()
            data = textPage.extractText()
            print(f"PAGE\n\n{data}")

    def testRawDict(self):
        doc = self.doc
        pg = self.pg
        with open(f"{TEST_DIR}/{pg:>03}-rawdict.txt", "w") as fh:
            for page in doc:
                textPage = page.get_textpage()
                data = textPage.extractRAWDICT()
                pprint(data, fh=fh)

    def testHtml(self):
        doc = self.doc
        pg = self.pg
        with open(f"{TEST_DIR}/{pg:>03}-html.txt", "w") as fh:
            for page in doc:
                textPage = page.get_textpage()
                data = textPage.extractHTML()
                fh.write(f"{data}\n")

    def testDict(self):
        doc = self.doc
        pg = self.pg
        with open(f"{TEST_DIR}/{pg:>03}-dict.txt", "w") as fh:
            for page in doc:
                textPage = page.get_textpage()
                data = textPage.extractDICT()
                pprint(data, fh=fh)


P = PText(PDF_DIR, pdfPage)
P.showText()
P.testRawDict()
P.testHtml()
P.testDict()
P.close()
