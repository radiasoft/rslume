"""The AWA zone1->zone2 twin's PV names, for anything that needs the full
list without starting the twin itself (`configure_archiver.py`,
`restore.py`'s callers): the EPICS Archiver Appliance's PV-add BPL call
needs the list to register them, and a restore-at-time call needs it to
know what to ask the archiver for.

Built from `twin/zone_model.py`'s own `cheap_variable_names()` (reads
`build_model()`'s own served names for each zone without paying for a
full rebuild -- see that function's own docstring) plus zone1's own
solenoid `*_scale_factor` names (`Zone1Model`'s own rebuild-based
variables, not `build_model()`'s) and each zone's three diagnostic
names, so this always matches what `serving/serve.py` actually serves
(scalars only -- the screens' own `*_image` waveforms are deliberately
excluded, see `awa_pv_names()`'s own docstring) -- confirmed by
`test_pvlist_matches_served_scalar_variables` in `tests/archiver_test.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "twin"))
from zone_model import (  # noqa: E402
    Zone1Model,
    cheap_variable_names,
    _zone1_module,
    _zone2_module,
)

DEFAULT_PREFIX = "AWA:SIM:"

_DIAGNOSTIC_SUFFIXES = ("charge_pC", "energy_MeV", "energy_spread_pct")


def awa_pv_names(prefix: str = DEFAULT_PREFIX) -> list[str]:
    """Every scalar PV `serving/serve.py` serves for the twin, `prefix`
    prepended: zone1's and zone2's writable params (including zone1's
    own rebuild-based solenoid `*_scale_factor` names), then each
    zone's three diagnostics. Deliberately excludes the screens' own
    `*_image` variables -- the archiver is for scalar history, not
    images (the HTU twin's own archiver setup, if it has one, would
    face the same split).
    """
    names = (
        cheap_variable_names(_zone1_module)
        + [f"{name}_scale_factor" for name in Zone1Model.SOLENOID_NAMES]
        + cheap_variable_names(_zone2_module)
    )
    for zone in ("zone1_", "zone2_"):
        names += [f"{zone}{suffix}" for suffix in _DIAGNOSTIC_SUFFIXES]
    return [f"{prefix}{name}" for name in names]


if __name__ == "__main__":
    for name in awa_pv_names():
        print(name)
