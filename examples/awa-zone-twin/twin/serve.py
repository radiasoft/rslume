"""Serve the AWA zone1->zone2 twin (`twin/zone_model.py`) as EPICS PVs
through `lume-pva`.

`python serve.py [--prefix AWA:SIM:]` builds the chain (`build_chain()`)
and serves every variable of both zones: zone1's and zone2's writable
params (solenoid scale factors, cavity power/phase, quadrupole strengths,
corrector kicks) read-write, and each zone's read-only
diagnostics (`zone{1,2}_charge_pC`, `zone{1,2}_energy_MeV`,
`zone{1,2}_energy_spread_pct`). `lume-pva` adds `<prefix>STATUS`,
`<prefix>RESET` and `<prefix>SNAPSHOT` on top of the model's own variables.

Both zones are meant to be driven interactively, not served as a fixed,
previously-recorded source.

A put is acknowledged at once, before the model has finished tracking:
Phoebus waits one second for a put reply on its UI thread, and a zone1
change (field-map I/O, autophase, and a space-charge-tracked run) takes
tens of seconds at the default particle count -- far longer than that.

Needs `lume-pva` (already installed in this environment; not a declared
dependency of `rslume` itself). Run it from this
directory or by path; it imports the `zone_model.py` next to it.
"""

from __future__ import annotations

from pykern.pkdebug import pkdlog
import argparse
import zone_model

try:
    import lume_pva.runner
except ModuleNotFoundError as e:
    if e.name != "lume_pva":
        raise
    raise ModuleNotFoundError(
        "serve.py needs the lume-pva package, which is not installed.",
        name="lume_pva",
    ) from e


def main(argv: list[str] | None = None) -> None:
    def _parse_args(argv):
        parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
        parser.add_argument("--prefix", default="AWA:SIM:", help="PV name prefix")
        parser.add_argument(
            "--n-particles",
            type=int,
            default=2000,
            help="macroparticles zone1 tracks (a fresh cathode bunch every set())",
        )
        parser.add_argument(
            "--threads",
            type=int,
            default=None,
            help="RF-Track thread count (default: min("
            + f"{zone_model.DEFAULT_THREADS}, RF_Track.max_number_of_threads))",
        )
        return parser.parse_args(argv)

    args = _parse_args(argv)
    chain = zone_model.build_chain(n_particles=args.n_particles, threads=args.threads)
    config = lume_pva.runner.Runner.generate_config(
        chain,
        prefix=args.prefix,
        put_mode=lume_pva.runner.PutMode.Immediate,
    )
    pkdlog("serving {} variables", len(config["variables"]))
    lume_pva.runner.Runner(model=chain, config=config).run()


if __name__ == "__main__":
    main()
