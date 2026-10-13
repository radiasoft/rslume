"""The one canonical RF-Track field/attribute -> unit table

Covers both `rslume.rftrack_archive`'s serialized element fields and the
live action-variable attributes (gradient/k1/max_current/angle/hkick/
vkick/phid/p_actual) exposed as RfTrack action variables, so
the archive and the served variables can't disagree about a unit.
Follows `lume-impact`'s pattern (`impact/parsers.py`'s
`HEADER_UNITS`/`ELE_UNITS`): plain unit strings, used directly as a
variable's `unit=` and converted to a `pmd_unit` only where one is
needed (writing the archive, `rftrack_archive._write_field_units_h5`).

Every value is a unit symbol `beamphysics.units.pmd_unit(symbol)`
resolves on its own (no explicit `unitSI`/`unitDimension`), including
RF-Track's non-SI "deg" and "mm/c".

`hkick`/`vkick` (the live corrector variable names) and `kx`/`ky` (the
archive's field names for the same quantity, `Corrector.get_strength()`'s
`[Kx, Ky]`) are separate entries because they are different names, not
because the unit is stated twice.
"""

UNITS = {
    "angle": "rad",
    "aperture_x": "m",
    "aperture_y": "m",
    "bz": "T",
    "cell_length": "m",
    "coefficients": "V/m",
    "direction": "1",
    "er": "V/m",
    "ez": "V/m",
    "frequency": "Hz",
    "gradient": "T/m",
    "height": "mm",
    "hkick": "T*mm",
    "hr": "m",
    "hz": "m",
    "k1": "1/m^2",
    "kx": "T*mm",
    "ky": "T*mm",
    "length": "m",
    "max_current": "A",
    "n_cells": "1",
    "p_actual": "W",
    "p_map": "W",
    "phid": "deg",
    "resolution": "mm",
    # not in the reference manual (get_resolution_t()/the constructor's
    # third argument predate this copy of the manual) -- inferred by
    # analogy with every other RF-Track time-like quantity (t0,
    # set_time_window(), sigma_t) all documented as "mm/c".
    "resolution_t": "mm/c",
    "t0": "mm/c",
    "vkick": "T*mm",
    "width": "mm",
    "x": "m",
    "y": "m",
    "z": "m",
}
