"""List pipe shipments."""
import sys
from pathlib import Path
import numpy as np

from itkdb_gtk import ITkDBlogin, ITkDButils

def main(session):
    """List shipments from DESY to AVS containing PIPES."""
    payload = {
            "filterMap": {
                "sender": "DESYHH",
                "recipient": ["AVS"],
                "status": "delivered"
            }
        }

    # Loop over shipments
    shpmts = session.get("listShipmentsByInstitution", json=payload)
    for s in shpmts:
        items = session.get("listShipmentItems", json={"shipment": s["id"]})
        pipes = []
        for it in items:
            if it["component"]["componentType"]['code'] == "COOLING_LOOP_PETAL":
                pipes.append(it)


        if len(pipes) == 0:
            continue

        print("Shipment {}".format(s["name"]))
        print(":> {}".format(s["sentTs"]))
        for c in pipes:
            pid = c["component"]["alternativeIdentifier"]
            print("*-- {}".format(pid))

            the_pipe = ITkDButils.get_DB_component(session, c["component"]["serialNumber"])
            if the_pipe is None:
                print("    !! ERROR: Could not retrieve component {} !!".format(c["component"]["serialNumber"]))
                continue

            if the_pipe["parents"] is not None:
                for p in the_pipe["parents"]:
                    if p["componentType"]["code"] == "CORE_PETAL":
                        print(  "    -> Core Petal: {} [{}]".format(p["component"]["alternativeIdentifier"],the_pipe["currentLocation"]["code"]) )

        print("\n")

if __name__ == "__main__":
    # ITk_PB authentication
    dlg = ITkDBlogin.ITkDBlogin()
    client = dlg.get_client()

    try:
        main(client)

    except Exception as E:
        print(E)

    dlg.die()