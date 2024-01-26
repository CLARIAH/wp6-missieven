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

        for i, streak in enumerate(streaks):
            n = i + 1
            refS = streak[0]
            slotLink[n] = streak
            kindFeature[n] = kindv(refS)
            eid = toId(T.text(streak))
            eidFeature[n] = eid

        console(f"{len(streaks):>5} entity nodes")
        console(f"{len(set(eidFeature.values())):>5} distinct eids")

        features = dict(kind=kindFeature, eid=eidFeature)

        featureMeta = dict(
            eid=dict(
                valueType="str",
                description="entity identifier base on string value of occurrence",
            ),
            kind=dict(
                valueType="str",
                description="entity kind",
            ),
        )

        self.addTypes = dict(
            ent=dict(
                nodeFrom=1,
                nodeTo=len(streaks),
                nodeSlots=slotLink,
                nodeFeatures=features,
            ),
        )
        self.featureMeta = featureMeta

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

        modify(
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
        newVersion = f"{oldVersion}e"

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

        self.prepareData()
        self.modify()
        self.tweakApp()
        self.loadNew()
