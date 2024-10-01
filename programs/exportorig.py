from tf.core.files import initTree


class Portion:
    def __init__(self, F, up_para, nodes, vl, lt):
        texts = []
        pos = 0
        folioRefs = {}

        pos = 0

        para = None
        page = None

        for (tp, n) in nodes:
            tx = f"{F.trans.v(n)}{F.punc.v(n)}"

            if tp == "folio":
                folioRefs.setdefault(pos, "")
                folioRefs[pos] += tx
            elif tp == "orig":
                thisPara = up_para(n)

                if thisPara != para:
                    if para is not None:
                        texts[-1] += "\n"
                        pos += 1
                    texts.append("")
                    para = thisPara

                texts[-1] += tx
                pos += len(tx)

        self.texts = "".join(texts)
        self.pos = len(self.texts)
        self.annotations = dict(folio=folioRefs)
        date = f"{F.year.v(lt)}-{F.month.v(lt)}-{F.day.v(lt)}"
        self.meta = (F.n.v(vl), F.page.v(lt), F.author.v(lt), date, F.seq.v(lt))


class Text:
    def __init__(self):
        self.texts = []
        self.annotations = {}
        self.itemList = []
        self.pos = 0

    def add(self, P):
        texts = self.texts
        pos = self.pos
        pTexts = P.texts
        pPos = P.pos

        annotations = self.annotations
        pAnnotations = P.annotations

        itemList = self.itemList

        extra = "" if pos == 0 else "\n\n"

        texts.append(extra + pTexts)
        newStart = pos + len(extra)
        newPos = newStart + pPos
        self.pos = newPos

        pMeta = (newStart, newPos, *P.meta)

        for pFeat, pFeatData in pAnnotations.items():
            dest = annotations.setdefault(pFeat, {})
            for (p, v) in pFeatData.items():
                dest[pos + p] = v

        itemList.append(pMeta)

    def export(self, app):
        info = app.info
        indent = app.indent
        repoLocation = app.repoLocation
        destDir = f"{repoLocation}/originals"

        indent(reset=True)
        initTree(destDir, fresh=True, gentle=True)

        with open(f"{destDir}/text.txt", "w") as fh:
            fh.write("".join(self.texts))

        with open(f"{destDir}/portions.tsv", "w") as fh:
            fh.write("start\tend\tvolume\tstartpage\tauthor\tdate\tletter\n")

            for itemData in self.itemList:
                fh.write("\t".join(str(x) for x in itemData) + "\n")

        for (feat, featData) in self.annotations.items():
            with open(f"{destDir}/{feat}.tsv", "w") as fh:
                fh.write("pos\tvalue\n")

                for (pos, value) in featData.items():
                    fh.write(f"{pos}\t{value}\n")

        info(f"Originals plus annotations written to {destDir}")


class Export:
    def __init__(self, app):
        self.app = app

    def generate(self):
        app = self.app
        api = app.api
        F = api.F
        L = api.L
        info = app.info
        indent = app.indent

        def up_para(n):
            paras = L.u(n, otype="para")
            return paras[0] if len(paras) else 0

        Tx = Text()
        self.Tx = Tx

        indent(reset=True)

        for vl in F.otype.s("volume"):
            info(F.n.v(vl))

            for lt in L.d(vl, otype="letter"):
                words = L.d(lt, otype="word")
                nodes = []

                for wd in words:
                    tp = (
                        "folio"
                        if F.isfolio.v(wd)
                        else "orig"
                        if F.isorig.v(wd)
                        else None
                    )
                    if tp is not None:
                        nodes.append((tp, wd))

                P = Portion(F, up_para, nodes, vl, lt)
                Tx.add(P)

        info("done")

    def write(self):
        app = self.app
        Tx = self.Tx
        Tx.export(app)
