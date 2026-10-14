"""rslume.rftrack_simulator.RFTrackSimulator.archive()/load_archive() round-trip test
for a Volume-mode beamline with an RF_FieldMap_1d cavity and a Screen --
the element classes and absolute (not sequential) positioning a Volume
beamline of field-map cavities/solenoids, correctors, and screens needs.
Static_Magnetic_FieldMap_1d (field-map SOLENOID) is covered too (see
static_magnetic_fieldmap_1d_test.py); so is Corrector (see
corrector_test.py).

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def _build_volume(rft):
    import numpy

    nz = 21
    hz = 0.01
    # a smooth half-sine bump, not a single spike -- RF_Track's Volume.track()
    # autophases the cavity, which fails ("no on-crest accelerating phase")
    # against an unrealistic field profile
    cavity = rft.RF_FieldMap_1d(
        (1e6 * numpy.sin(numpy.linspace(0, numpy.pi, nz))).astype(complex),
        hz,
        (nz - 1) * hz,
        1.3e9,
        1.0,
        1.0,
        1.0,
    )
    cavity.set_name("C1")
    cavity.set_phid(10.0)

    screen = rft.Screen()
    screen.set_name("SCR1")

    v = rft.Volume()
    v.add(cavity, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    v.add(screen, 0.0, 0.0, cavity.get_length() + 0.1, 0.0, 0.0, 0.0)
    v.set_s0(0.0)
    v.set_s1(cavity.get_length() + 0.2)
    return v


def _build_bunch(rft):
    twiss = rft.Bunch6d_twiss()
    twiss.beta_x = 1.0
    twiss.beta_y = 1.0
    twiss.alpha_x = 0.0
    twiss.alpha_y = 0.0
    twiss.emitt_x = 1.0
    twiss.emitt_y = 1.0
    twiss.sigma_t = 1.0
    twiss.sigma_pt = 1.0
    return rft.Bunch6d_QR(rft.electronmass, 0.05 * rft.nC, -1, 10.0, twiss, 200)


def test_volume_archive_round_trip():
    import h5py
    import RF_Track as rft
    from pykern import pkunit
    from rslume.rftrack_simulator import RFTrackSimulator

    path = str(pkunit.empty_work_dir().join("volume.h5"))

    rft.rng_set_seed(5489)
    original = RFTrackSimulator(_build_volume(rft), _build_bunch(rft))
    # archive before track(): Volume.track() autophases the cavity in
    # place (mutates its phid to find an on-crest phase), so archiving
    # afterwards would capture that autophased value instead of the 10.0
    # set above, and the reloaded copy would then autophase a second time
    # starting from an already-autophased state -- archiving the
    # pre-track() state means both copies autophase once, from the same
    # starting point.
    original.archive(path)

    with h5py.File(path, "r") as f:
        pkunit.pkeq("Volume", f.attrs["beamline_class"])
        pkunit.pkeq("RF_FieldMap_1d", f["elements"]["0"].attrs["class"])
        pkunit.pkeq("Screen", f["elements"]["1"].attrs["class"])
        # the field map array went in as a real dataset under the
        # shared "field_maps" group, referenced by the element's own
        # "ez" attr ("@<md5>") rather than duplicated inline -- see
        # rslume.rftrack_archive.archive()'s own docstring (_dedupe_field_maps)
        pkunit.pkeq(21, len(f["field_maps"][f["elements"]["0"].attrs["ez"][1:]]))

    pkunit.pkeq(10.0, original.beamline[0].get_phid(), "archive() must not mutate beamline")

    reloaded = RFTrackSimulator()
    rft.rng_set_seed(5489)
    reloaded.load_archive(path)

    pkunit.pkeq("Volume", type(reloaded.beamline).__name__)
    pkunit.pkeq(
        original.beamline[0].get_length(),
        reloaded.beamline[0].get_length(),
    )
    pkunit.pkeq(10.0, reloaded.beamline[0].get_phid())

    rft.rng_set_seed(5489)
    original.track()
    rft.rng_set_seed(5489)
    reloaded.track()

    for field in ("x", "y", "K"):
        o = original.tracked_bunch.get_phase_space(f"%{field}")
        r = reloaded.tracked_bunch.get_phase_space(f"%{field}")
        pkunit.pkok(
            abs(o.std() - r.std()) < 0.1 * max(abs(o.std()), 1e-9),
            "{} std differs too much: original={} reloaded={}",
            field,
            o.std(),
            r.std(),
        )
