"""Register the AWA zone1->zone2 twin's PVs with an EPICS Archiver
Appliance, so it starts recording every setting change once `serving/
serve.py` is running.

Calls the appliance's mgmt BPL `archivePV` action (confirmed against the
actual installed `mgmt.war`'s `BPLServlet`/`ArchivePVAction` classes --
`GET <mgmt_url>/archivePV?pv=NAME`), once per PV: confirmed live against
the running quickstart appliance that this action reads only the first
`pv` parameter of a request, so a single call with several repeated
`pv=` values (the form some other BPL actions and the Archiver
Appliance's own docs show for bulk operations) silently archives only
the first of them.

A newly-added PV reports `"Initial sampling"` from `getPVStatus` for up
to a minute before settling to `"Being archived"` -- expected, not a
failure; `archive_pvs()` does not wait for that.

Run it once, any time after a quickstart appliance is up and before (or
after) `serving/serve.py` starts -- order does not matter, the archiver
polls for the PVs' Channel Access servers independently. Needs
`serve.py` to be serving the `ca` protocol (the default) for the
archiver's engine to actually connect; a PVA-only server has nothing for
it to archive.
"""

from __future__ import annotations

import argparse
import urllib.parse
import urllib.request

from pvlist import DEFAULT_PREFIX, awa_pv_names

DEFAULT_MGMT_URL = "http://localhost:8008/mgmt/bpl"


def archive_pvs(pv_names: list[str], mgmt_url: str = DEFAULT_MGMT_URL) -> None:
    """Register every name in `pv_names` for archiving, one `archivePV`
    call each.

    Raises:
        urllib.error.HTTPError: a PV's request failed.
    """
    for name in pv_names:
        query = urllib.parse.urlencode({"pv": name})
        url = f"{mgmt_url}/archivePV?{query}"
        with urllib.request.urlopen(url, timeout=30) as response:
            body = response.read().decode()
        print(f"archivePV {name}: {body.strip()}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--mgmt-url", default=DEFAULT_MGMT_URL)
    parser.add_argument("--prefix", default=DEFAULT_PREFIX)
    args = parser.parse_args(argv)

    names = awa_pv_names(args.prefix)
    print(f"registering {len(names)} PVs with {args.mgmt_url} ...")
    archive_pvs(names, args.mgmt_url)
    print("done -- check http://localhost:8008/mgmt/ui/index.html to confirm")


if __name__ == "__main__":
    main()
