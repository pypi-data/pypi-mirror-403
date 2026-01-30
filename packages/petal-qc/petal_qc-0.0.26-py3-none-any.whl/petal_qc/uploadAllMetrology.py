#!/usr/bin/env python3
"""Get right stage for this test."""

import sys
import re
import json
from pathlib import Path
from argparse import ArgumentParser

cwd = Path(__file__).parent.parent
sys.path.insert(0, cwd.as_posix())

from itkdb_gtk import ITkDBlogin, ITkDButils
from petal_qc.utils.all_files import all_files


r_petal_id = re.compile("PPC.([0-9]*)")
def check_valid_petal(core, core_list=None):
    """Check if we have a valid core."""
    if core_list is None:
        core_list = []

    altid = core['alternativeIdentifier']
    if "PPC" not in altid:
        return False

    R = r_petal_id.search(altid)
    if R is None:
        return False

    pid = int(R.group(1))

    if len(core_list)>0 and pid not in core_list:
        return False

    return True


data_folder = Path.home() / Path("SACO-CSIC/ITk-Strips/Local.Supports/metrology/Results-Jan26")

def main():
    """Main entry."""
    # command line argumetns
    parser = ArgumentParser()
    parser.add_argument("--data_folder", default=None, help="Folder with all Json files.")
    parser.add_argument("--institute", default=None, help="The petal QC site. Default is user's institution.")
    options = parser.parse_args()

    # Check data folder.
    if options.data_folder is None:
        print("I need a data folder")
        parser.print_help()
        return


    # DB login
    dlg = ITkDBlogin.ITkDBlogin()
    client = dlg.get_client()
    if client is None:
        print("Could not connect to DB with provided credentials.")
        dlg.die()
        sys.exit()

    # Institute
    if options.institute is None:
        options.institute = ITkDButils.get_db_user_institutions(client)[0]


    for core in ITkDButils.find_petal_cores(client):
        if not check_valid_petal(core):
            continue

        qc_site = ITkDButils.find_petal_core_qc_site(client, core["serialNumber"])
        if qc_site != options.institute:
            continue

        coreStage = core["currentStage"]['code']
        altid = core['alternativeIdentifier']
        currentLocation = core["currentLocation"]["code"]

        print("+ {} - {}".format(altid, coreStage))
        for fpath in all_files(data_folder, "{}-*.json".format(altid)):
            print("\t{}".format(fpath.name))
            with open(fpath, "r", encoding="UTF-8") as fp:
                data = json.load(fp)

                if coreStage != "AT_QC_SITE":
                    data["isRetroactive"] = True
                    data["stage"] = "AT_QC_SITE"

            if "isRetroactive" not in data and currentLocation != options.institute:
                    data["isRetroactive"] = True
                    data["stage"] = "AT_QC_SITE"

            try:
                rc = ITkDButils.upload_test(client, data, check_runNumber=True)

            except Exception as e:
                rc = str(e)

            if rc:
                print("\n*** Could not upload test {} for {}".format(data["testType"], altid))
                print(rc)
                print()
                with open("{}-failed.json".format(fpath.stem), "w", encoding="utf-8") as fp:
                    json.dump(data, fp)
                    fp.close()

    dlg.die()

if __name__ == "__main__":
    main()