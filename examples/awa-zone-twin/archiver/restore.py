"""Get the AWA twin's PV values at a past time from an EPICS Archiver
Appliance, for seeding `serving/serve.py --restore-at` at startup.

Modeled directly on `lcls_live.archiver.lcls_archiver_restore()` (same
`retrieval/data/getDataAtTime` BPL call, confirmed against the actual
installed `retrieval.war`'s `DataRetrievalServlet`/`GetDataAtTime`
classes), but with the retrieval URL as a parameter instead of hardcoded
to SLAC's production archiver -- this one points at the local quickstart
appliance by default.
"""

from __future__ import annotations

import requests

DEFAULT_RETRIEVAL_URL = "http://localhost:8008/retrieval"


def restore_at(
    pv_names: list[str], isotime: str, retrieval_url: str = DEFAULT_RETRIEVAL_URL, verbose: bool = True
) -> dict[str, float]:
    """`{pv_name: value}` for every name in `pv_names` the archiver has a
    value for at `isotime` (ISO 8601, e.g. `"2026-10-10T02:30:00.000-07:00"`);
    a name with no archived value at that time is left out (and, if
    `verbose`, reported).

    Raises:
        RuntimeError: the archiver request itself failed.
    """
    url = f"{retrieval_url}/data/getDataAtTime?at={isotime}&includeProxies=true"
    if verbose:
        print("Requesting:", url)
    response = requests.post(url, headers={"Content-Type": "application/json"}, json=pv_names)
    if not response.ok:
        raise RuntimeError(f"Archiver request failed: {response.status_code} - {response.reason}")
    data = response.json()
    values = {}
    for name in pv_names:
        if name not in data:
            if verbose:
                print("Warning: no archived value for", name)
        else:
            values[name] = data[name]["val"]
    return values


def main(argv: list[str] | None = None) -> None:
    import argparse

    from pvlist import DEFAULT_PREFIX, awa_pv_names

    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("isotime", help='e.g. "2026-10-10T02:30:00.000-07:00"')
    parser.add_argument("--retrieval-url", default=DEFAULT_RETRIEVAL_URL)
    parser.add_argument("--prefix", default=DEFAULT_PREFIX)
    args = parser.parse_args(argv)

    values = restore_at(awa_pv_names(args.prefix), args.isotime, args.retrieval_url)
    for name, value in values.items():
        print(f"{name} = {value}")


if __name__ == "__main__":
    main()
