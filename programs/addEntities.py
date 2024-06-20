from itertools import chain
from tf.app import use
from tf.core.helpers import console
from tf.dataset import modify
from tf.browser.ner.helpers import toId
from tf.core.files import dirExists, dirRemove


class AddEntities:
    def __init__(self):
        A = use(
            "CLARIAH/wp6-missieven:clone",
            version="1.0",
            mod="CLARIAH/wp6-missieven/voc-missives/export/tf:clone",
            checkout="clone",
        )
        self.A = A

    def getStreaks(self):
        A = self.A
        F = A.api.F

        streaks = []

        curStreak = []
        curId = None

        def addEntity():
            streaks.append(tuple(curStreak))

        for w in F.otype.s("word"):
            eid = F.entityId.v(w)

            if eid is None:
                if curId is not None:
                    addEntity()
                    curId = None
                continue

            if eid == curId:
                curStreak.append(w)
                continue

            if curId is not None:
                addEntity()

            curId = eid
            curStreak = [w]

        if curId is not None:
            addEntity()

        console(f"{len(streaks)} entity occurrences")
        self.streaks = streaks

    def checkStreaks(self):
        A = self.A
        F = A.api.F
        streaks = self.streaks

        idv = F.entityId.v
        kindv = F.entityKind.v

        goodStreaks = []
        badStreaks = []

        for streak in streaks:
            if (
                len({idv(s) for s in streak}) == 1
                and len({kindv(s) for s in streak}) == 1
            ):
                goodStreaks.append(streak)
            else:
                badStreaks.append(streak)

        nGood = len(goodStreaks)
        nBad = len(badStreaks)
        console(f"{nGood:>5} good streaks")
        console(f"{nBad:>5} bad streaks")

        return nBad == 0

    def prepareData(self):
        A = self.A
        F = A.api.F
        T = A.api.T
        streaks = self.streaks

        kindv = F.entityKind.v

        slotLink = {}
        kindFeature = {}
        eidFeature = {}
        occEdge = {}
        entities = {}

        n = 0

        for streak in streaks:
            n += 1
            refS = streak[0]
            slotLink[n] = streak
            ekind = kindv(refS)
            kindFeature[n] = ekind
            eid = toId(T.text(streak))
            eidFeature[n] = eid
            entities.setdefault((eid, ekind), []).append(n)

        nStreaks = len(streaks)

        for ((eid, ekind), ms) in entities.items():
            n += 1
            occEdge[n] = set(ms)
            slotLink[n] = tuple(chain.from_iterable(slotLink[m] for m in ms))
            kindFeature[n] = ekind
            eidFeature[n] = eid

        console(f"{len(streaks):>5} entity nodes")
        console(f"{len(set(eidFeature.values())):>5} distinct eids")
        console(f"{len(entities):>5} distinct entities")

        nodeFeatures = dict(kind=kindFeature, eid=eidFeature)
        edgeFeatures = dict(eoccs=occEdge)

        featureMeta = dict(
            eid=dict(
                valueType="str",
                description="entity identifier base on string value of occurrence",
            ),
            kind=dict(
                valueType="str",
                description="entity kind",
            ),
            eoccs=dict(
                valueType="str",
                description="from entity nodes to their occurrence nodes",
            )
        )

        self.addTypes = dict(
            ent=dict(
                nodeFrom=1,
                nodeTo=nStreaks,
                nodeSlots=slotLink,
                nodeFeatures=nodeFeatures,
            ),
            entity=dict(
                nodeFrom=nStreaks + 1,
                nodeTo=nStreaks + len(entities),
                nodeSlots=slotLink,
                nodeFeatures=nodeFeatures,
                edgeFeatures=edgeFeatures,
            ),
        )
        self.featureMeta = featureMeta

        return True

    def modify(self):
        A = self.A
        TF = A.TF

        origTf = f"{A.repoLocation}/tf/{A.version}"
        newTf = f"{origTf}e"
        newVersion = f"{A.version}e"

        if dirExists(newTf):
            dirRemove(newTf)

        addTypes = self.addTypes
        featureMeta = self.featureMeta

        deleteFeatures = ["entityId", "entityKind"] + [
            f for f in TF.features if f.startswith("omap@")
        ]

        return modify(
            origTf,
            newTf,
            targetVersion=newVersion,
            deleteFeatures=deleteFeatures,
            addTypes=addTypes,
            featureMeta=featureMeta,
        )

    def tweakApp(self):
        A = self.A

        config = f"{A.repoLocation}/app/config.yaml"
        oldVersion = A.version
        newVersion = f"{oldVersion}ent"

        with open(config) as fh:
            text = fh.read()

        text = text.replace(f'version: "{oldVersion}"', f'version: "{newVersion}"')

        with open(config, mode="w") as fh:
            fh.write(text)

    def loadNew(self):
        A = use(
            "CLARIAH/wp6-missieven:clone",
            checkout="clone",
        )
        self.A = A

    def run(self):
        self.getStreaks()

        if not self.checkStreaks():
            return

        if not self.prepareData():
            return

        if not self.modify():
            return

        self.tweakApp()
        self.loadNew()
