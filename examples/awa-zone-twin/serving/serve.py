"""Serve the AWA zone1->zone2 twin (`twin/zone_model.py`) as EPICS PVs
through `lume-pva`.

`python serve.py [--prefix AWA:SIM:]` builds the chain (`build_chain()`)
and serves every variable of both zones: zone1's and zone2's writable
params (solenoid scale factors, cavity power/phase, quadrupole strengths,
corrector kicks) read-write by default, and each zone's read-only
diagnostics (`zone{1,2}_charge_pC`, `zone{1,2}_energy_MeV`,
`zone{1,2}_energy_spread_pct`). `lume-pva` adds `<prefix>STATUS`,
`<prefix>RESET` and `<prefix>SNAPSHOT` on top of the model's own variables.

Unlike `docs/htu-twin/serving/serve.py`, there is no archive step and no
`--include-inputs` flag: both zones are meant to be driven interactively
here, not served as a fixed,
previously-recorded source the way the HTU twin's LPA archive is. Pass
`--read-only` to serve every param read-only instead (e.g. to look at the
twin without being able to change it).

A put is acknowledged at once by default, before the model has finished
tracking: Phoebus waits one second for a put reply on its UI thread, and a
zone1 change (field-map I/O, autophase, and a space-charge-tracked run)
takes tens of seconds at the default particle count -- far longer than
that. `--wait-for-puts` acknowledges only after the model has finished
(`PutMode.Complete`), for a scan client that sets and waits; do not use
it from Phoebus.

Needs `lume-pva` (already installed in this environment; not a declared
dependency of `rslume` itself, same as the reference). Run it from this
directory or by path; it imports `zone_model.py` from `../twin`.

`--restore-at ISOTIME` seeds the twin's writable params from an EPICS
Archiver Appliance's recorded values at that time (ISO 8601, e.g.
`"2026-10-10T02:35:00.000-07:00"`) instead of each variable's
default, via `archiver/restore.py`'s `restore_at()` -- the same
`getDataAtTime` BPL call `archiver/configure_archiver.py`'s own PVs were
registered for. A name the archiver has no value for at that time (never
archived, or archived after that time) keeps its default instead of
failing the whole restore.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--prefix", default="AWA:SIM:", help="PV name prefix")
    parser.add_argument(
        "--read-only",
        action="store_true",
        help="serve every zone1/zone2 param read-only instead of read-write",
    )
    parser.add_argument(
        "--protocol",
        nargs="+",
        choices=["ca", "pva"],
        help="protocols to serve (default both)",
    )
    parser.add_argument(
        "--n-particles",
        type=int,
        default=2000,
        help="macroparticles zone1 tracks (a fresh cathode bunch every set())",
    )
    parser.add_argument(
        "--wait-for-puts",
        action="store_true",
        help="acknowledge a put only after the model has finished (PutMode.Complete); "
        "do not use this from Phoebus, which waits only one second on its UI thread "
        "for a put reply, far shorter than zone1's retrack",
    )
    parser.add_argument(
        "--restore-at",
        metavar="ISOTIME",
        help='seed writable params from the archiver\'s recorded values at this time '
        '(ISO 8601, e.g. "2026-10-10T02:35:00.000-07:00") instead of the zones\' own '
        "defaults",
    )
    parser.add_argument(
        "--archiver-retrieval-url",
        default=None,
        help="retrieval URL for --restore-at (default: archiver/restore.py's own "
        "default, the local quickstart appliance)",
    )
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument(
        "--threads",
        type=int,
        default=None,
        help="RF-Track thread count (default: min(14, RF_Track.max_number_of_threads))",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=args.log_level)
    runner = _import_runner()

    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root / "twin"))
    from zone_model import build_chain

    chain = build_chain(n_particles=args.n_particles, threads=args.threads)

    if args.restore_at:
        sys.path.insert(0, str(repo_root / "archiver"))
        from pvlist import awa_pv_names
        from restore import DEFAULT_RETRIEVAL_URL, restore_at

        archived = restore_at(
            awa_pv_names(args.prefix),
            args.restore_at,
            args.archiver_retrieval_url or DEFAULT_RETRIEVAL_URL,
        )
        writable = {
            name
            for name, variable in chain.supported_variables.items()
            if not variable.read_only
        }
        restored = {
            name[len(args.prefix) :]: value
            for name, value in archived.items()
            if name[len(args.prefix) :] in writable
        }
        logging.getLogger(__name__).info(
            "restoring %d/%d writable params from %s", len(restored), len(writable), args.restore_at
        )
        chain.set(restored)

    config = runner.Runner.generate_config(
        chain,
        prefix=args.prefix,
        put_mode=runner.PutMode.Complete if args.wait_for_puts else runner.PutMode.Immediate,
    )
    if args.read_only:
        config["variables"] = {
            name: {**entry, "mode": type(entry["mode"]).RO}
            for name, entry in config["variables"].items()
        }
    if args.protocol:
        config["protocol"] = list(args.protocol)

    logging.getLogger(__name__).info("serving %d variables", len(config["variables"]))
    runner.Runner(model=chain, config=config).run()


def _import_runner():
    """The `lume_pva.runner` module (it holds `Runner` and `PutMode`)."""
    try:
        import lume_pva.runner as runner
    except ImportError as error:
        raise ImportError(
            "serve.py needs the lume-pva package, which is not installed."
        ) from error
    return runner


if __name__ == "__main__":
    main()
