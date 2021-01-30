import sys

from lib import REPO, VERSION_SRC, parseArgs, trim

from trimTei0 import (
    corpusPre as a0,
    trimVolume as v0,
    trimDocBefore as b0,
    trimDocPrep as d0,
    trimPage as t0,
    processPage as p0,
    trimDocPost as e0,
    corpusPost as c0,
)
from trimTei1 import (
    corpusPre as a1,
    trimVolume as v1,
    trimDocBefore as b1,
    trimDocPrep as d1,
    trimPage as t1,
    processPage as p1,
    trimDocPost as e1,
    corpusPost as c1,
)
from trimTei2 import (
    corpusPre as a2,
    trimVolume as v2,
    trimDocBefore as b2,
    trimDocPrep as d2,
    trimPage as t2,
    processPage as p2,
    trimDocPost as e2,
    corpusPost as c2,
)
from trimTei3 import (
    corpusPre as a3,
    trimVolume as v3,
    trimDocBefore as b3,
    trimDocPrep as d3,
    trimPage as t3,
    processPage as p3,
    trimDocPost as e3,
    corpusPost as c3,
)

from trimTei4 import (
    corpusPre as a4,
    trimVolume as v4,
    trimDocBefore as b4,
    trimDocPrep as d4,
    trimPage as t4,
    processPage as p4,
    trimDocPost as e4,
    corpusPost as c4,
)

corpusPre = [a0, a1, a2, a3, a4]
trimVolume = [v0, v1, v2, v3, v4]
trimDocBefore = [b0, b1, b2, b3, b4]
trimDocPrep = [d0, d1, d2, d3, d4]
trimPage = [t0, t1, t2, t3, t4]
processPage = [p0, p1, p2, p3, p4]
trimDocPost = [e0, e1, e2, e3, e4]
corpusPost = [c0, c1, c2, c3, c4]


HELP = f"""
Convert TEI source to simplified pseudo TEI,
stage {{stage}} (must be 0 .. {len(trimPage) - 1}).

python3 trimTei.py {{stage}} [volume] [page] [--help]

--help: print this text amd exit

volume: only process this volume; default: all volumes
page  : only process letter that starts at this page; default: all letters
"""


def main():
    args = [] if len(sys.argv) == 1 else list(sys.argv[1:])

    if "--help" in args:
        print(HELP.format(stage="?"))
        return True

    if len(args) == 0:
        print("Specify a stage!")
        print(HELP.format(stage="?"))
        return False

    stage = args.pop(0)

    if stage.isdigit():
        stage = int(stage)
    else:
        print(f"{stage} is not a number!")
        print(HELP.format(stage=stage))
        return False

    if stage >= len(trimPage):
        print(HELP.format(stage=stage))
        return False

    (good, vol, lid, kwargs, pargs) = parseArgs(args)

    if not good:
        return False

    print(f"TEI trimmer stage {stage} for {REPO}")
    print(f"TEI source version = {VERSION_SRC}")

    return trim(
        stage,
        vol,
        lid,
        corpusPre[stage],
        trimVolume[stage],
        trimDocBefore[stage],
        trimDocPrep[stage],
        trimPage[stage],
        processPage[stage],
        trimDocPost[stage],
        corpusPost[stage],
        *pargs,
        **kwargs,
    )


sys.exit(0 if main() else 1)
