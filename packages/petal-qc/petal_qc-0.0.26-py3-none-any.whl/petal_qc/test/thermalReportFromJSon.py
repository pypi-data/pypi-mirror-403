#!/usr/bin/env python3
"""List failing cores from JSon files."""
import sys
import argparse
import re
from pathlib import Path
import json

from itkdb_gtk import ITkDBlogin
from itkdb_gtk import ITkDButils

try:
    import petal_qc

except ImportError:
    cwd = Path(__file__).parent.parent
    sys.path.append(cwd.as_posix())

from petal_qc.utils.ArgParserUtils import RangeListAction
from petal_qc.utils.all_files import all_files


match_fnam = re.compile("20US.*Thermal.json", re.DOTALL)


def main(client, options):
    """main entry."""
    petal_cores = {}
    for fpath in options.files:
        fnam = str(fpath.name)
        M = match_fnam.match(fnam)
        if M is None:
            continue

#         ipos = fnam.find("PPC")
#         lpos = fnam[ipos:].find("-")
#         petal_id = fnam[ipos:ipos+lpos]
#         pid = int(petal_id[4:])
# 
#         if len(options.cores)>0 and pid not in options.cores:
#             continue

        with open(fpath, "r", encoding="utf-8") as fin:
            data = json.load(fin)

        if not data["passed"]:
            if data["component"] is None:
                print("Petal {} has bad Serial number".format(petal_id))
                continue

            core = ITkDButils.get_DB_component(client, data["component"])
            petal_id = core['alternativeIdentifier']
            
            petalId = "{}-{}".format(petal_id, data["component"])
            print (petalId)
            for D in data["defects"]:
                print("{}: {} {}".format(D["name"], D["description"], D["properties"]["msg"]))


    keys = sorted(petal_cores.keys())
    for petalId in keys:
        print(petalId)
        for side in ["FRONT","BACK"]:
            if len(petal_cores[petalId][side])>0:
                print("+-", side)
            for D in petal_cores[petalId][side]:
                print("  ", D)

        print("\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='*', help="Input files")
    parser.add_argument("--cores", dest="cores", action=RangeListAction, default=[],
                        help="Create list of cores to analyze. The list is made with  numbers or ranges (ch1:ch2 or ch1:ch2:step) ")
    opts = parser.parse_args()


    dlg = None
    try:
        # We use here the Gtk GUI
        dlg = ITkDBlogin.ITkDBlogin()
        client = dlg.get_client()

    except Exception:
        # Login with "standard" if the above fails.
        client = ITkDButils.create_client()


    #folder = Path("/tmp/petal-metrology/results")
    folder = Path("~/SACO-CSIC/ITk-Strips/Local Supports/thermal/IFIC-thermal/thermal-new-golden/results").expanduser()
    opts.files = []
    for fnam in all_files(folder, "*.json"):
        opts.files.append(fnam)

    main(client, opts)
    dlg.die()
    