"""rslume.rftrack_units.UNITS: every symbol parses to a real unit, and every
numeric field an archive writes has one.

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def test_every_symbol_is_a_real_unit():
    from beamphysics.units import pmd_unit
    from pykern import pkunit
    from rslume.rftrack_units import UNITS

    for k, v in UNITS.items():
        pkunit.pkok(isinstance(v, str) and v, "UNITS[{!r}] is not a unit symbol", k)
        pkunit.pkok(pmd_unit(v).unitSI != 0, "UNITS[{!r}]={!r} has unitSI 0", k, v)


def test_every_archived_numeric_field_has_a_unit():
    import h5py
    import numpy
    import RF_Track as rft
    from pykern import pkunit
    from rslume.rftrack_simulator import RFTrackSimulator

    ez = (1e6 * numpy.sin(numpy.linspace(0, numpy.pi, 21))).astype(complex)
    elements = [
        rft.Drift(0.1),
        rft.Quadrupole(0.1, float("nan"), 0.0),
        rft.Corrector(0.1, 1.0, 2.0),
        rft.Screen(),
        rft.Bpm(0.1, 0.0, 0.0),
        rft.Pillbox_Cavity(numpy.array([1e6]), 3e9, 0.05, 2),
        rft.RF_FieldMap_1d(ez, 0.01, 0.2, 1.3e9, 1.0, 1.0, 1.0),
    ]
    elements[1].set_gradient(1.0)
    lattice = rft.Lattice()
    for i, e in enumerate(elements):
        e.set_name(f"E{i}")
        lattice.append(e)
    twiss = rft.Bunch6d_twiss()
    twiss.beta_x = twiss.beta_y = twiss.emitt_x = twiss.emitt_y = 1.0
    twiss.alpha_x = twiss.alpha_y = 0.0
    twiss.sigma_t = twiss.sigma_pt = 1.0
    bunch = rft.Bunch6d_QR(rft.electronmass, 0.05 * rft.nC, -1, 10.0, twiss, 10)

    path = str(pkunit.empty_work_dir().join("a.h5"))
    RFTrackSimulator(lattice, bunch).archive(path)
    with h5py.File(path, "r") as f:
        for i in f["elements"]:
            e = f["elements"][i]
            # numbers, arrays (e.g. Pillbox coefficients) and "@<md5>"
            # references to a deduplicated field map (e.g. RF_FieldMap_1d ez)
            fields = {
                k
                for k, v in e.attrs.items()
                if isinstance(v, (int, float, numpy.number, numpy.ndarray))
                or (isinstance(v, str) and v.startswith("@"))
            } | set(e)
            have = set(f["units"]["elements"][i])
            pkunit.pkok(
                fields <= have,
                "element {} has fields without a unit: {}",
                i,
                sorted(fields - have),
            )
