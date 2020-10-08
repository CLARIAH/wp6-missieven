import sys

from lib import REPO, VERSION_SRC, trim

from trimTei0 import trimPage as t0, processPage as p0
from trimTei1 import trimPage as t1, processPage as p1
from trimTei2 import trimPage as t2, processPage as p2
from trimTei3 import trimPage as t3, processPage as p3

trimPage = [t0, t1, t2, t3]
processPage = [p0, p1, p2, p3]


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
        print(HELP.format(stage='?'))
        return True

    if len(args) == 0:
        print("Specify a stage!")
        print(HELP.format(stage='?'))
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

    vol = None
    lid = None

    kwargs = {}
    pargs = []

    good = True

    for arg in args:
        if arg.isdigit() or '-' in arg:
            if '-' in arg:
                (b, e) = arg.split('-', 1)
                if b.isdigit() and e.isdigit():
                    values = set(range(int(b), int(e) + 1))
                else:
                    print(f"Unrecognized argument `{arg}`")
                    good = False
                    continue
            else:
                values = {int(arg)}
            if vol is None:
                vol = values
            elif lid is None:
                lid = values
        else:
            kv = arg.split("=", 1)
            if len(kv) == 1:
                pargs.append[arg]
            else:
                (k, v) = kv
                if k == "orig":
                    v = set(v.split(","))
                kwargs[k] = v

    if not good:
        return False

    if vol is not None:
        vol = {f"{i:>02}" for i in vol}
    if lid is not None:
        lid = {f"p{i:>04}" for i in lid}

    print(f"TEI trimmer stage {stage} for {REPO}")
    print(f"TEI source version = {VERSION_SRC}")

    return trim(stage, vol, lid, trimPage[stage], processPage[stage], *pargs, **kwargs)


sys.exit(0 if main() else 1)
