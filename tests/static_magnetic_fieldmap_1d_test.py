"""rslume.rftrack archive()/load_archive() coverage for
Static_Magnetic_FieldMap_1d (a field-map SOLENOID) specifically.

There's no direct Bz-array getter for this class (unlike RF_FieldMap_1d's
get_Ez()), so the serializer samples get_field() instead -- and
get_field(x, y, z, t)'s coordinate arguments are documented (RF-Track
reference manual, section 5.1.2) as millimeters, not meters like every
other length-valued getter/setter in this module (get_length(),
get_z0()/get_z1(), set_s0()/set_s1(), Volume.add()'s x/y/z, ...). Getting
this wrong silently samples only the field map's first ~1mm, which looks
like a small, nearly-flat, physically-plausible-looking value if you
aren't comparing against the real source file -- this test exists because
that's exactly what happened during development, caught only by comparing
the sampled peak against ground truth from a real field-map file.

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def _build_solenoid(rft, numpy, peak_t=0.3):
    # a bell-curve profile peaking mid-element, not at an edge -- a flat
    # or monotonic profile wouldn't catch a coordinate-unit bug the way a
    # real solenoid's shape does (the bug this test is named for produces
    # a profile that still looks superficially plausible: small and
    # slowly varying)
    bz = peak_t * numpy.exp(-((numpy.linspace(-1, 1, 101)) ** 2) * 4)
    sol = rft.Static_Magnetic_FieldMap_1d(bz, 0.01)
    sol.set_name("SOL1")
    return sol, bz


def test_peak_field_matches_construction_input():
    import numpy
    import RF_Track as rft
    from pykern import pkunit
    from rslume.rftrack_archive import _serialize_static_magnetic_fieldmap_1d

    sol, bz_in = _build_solenoid(rft, numpy, peak_t=0.3)
    d = _serialize_static_magnetic_fieldmap_1d(sol)

    pkunit.pkok(
        abs(numpy.abs(d["bz"]).max() - 0.3) < 1e-6,
        "expected peak sampled field near 0.3 T, got {}",
        numpy.abs(d["bz"]).max(),
    )
    peak_idx = int(numpy.argmax(numpy.abs(d["bz"])))
    pkunit.pkok(
        abs(peak_idx - len(bz_in) // 2) <= 1,
        "expected the peak near the middle of the element, got index {} of {}",
        peak_idx,
        len(bz_in),
    )


def test_archive_round_trip():
    import h5py
    import numpy
    import RF_Track as rft
    from pykern import pkunit
    from rslume.rftrack_simulator import RFTrackSimulator

    path = str(pkunit.empty_work_dir().join("solenoid.h5"))

    sol, _ = _build_solenoid(rft, numpy)
    v = rft.Volume()
    v.add(sol, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    v.set_s0(0.0)
    v.set_s1(sol.get_length())

    twiss = rft.Bunch6d_twiss()
    twiss.beta_x = 1.0
    twiss.beta_y = 1.0
    twiss.alpha_x = 0.0
    twiss.alpha_y = 0.0
    twiss.emitt_x = 1.0
    twiss.emitt_y = 1.0
    twiss.sigma_t = 1.0
    twiss.sigma_pt = 1.0
    RFTrackSimulator(
        v, rft.Bunch6d_QR(rft.electronmass, 0.05 * rft.nC, -1, 10.0, twiss, 50)
    ).archive(path)

    with h5py.File(path, "r") as f:
        pkunit.pkeq("Static_Magnetic_FieldMap_1d", f["elements"]["0"].attrs["class"])
        # a shared "field_maps" dataset, referenced by "@<md5>" --
        # see RFTrackSimulator.archive()'s own docstring
        bz_archived = f["field_maps"][f["elements"]["0"].attrs["bz"][1:]][()]

    reloaded = RFTrackSimulator()
    reloaded.load_archive(path)

    z_mm = numpy.linspace(sol.get_z0(), sol.get_z1(), int(sol.get_nz())) * 1000.0

    numpy.testing.assert_allclose(
        numpy.asarray(reloaded.beamline[0].get_field(0.0, 0.0, z_mm, 0.0)[1])[:, 2],
        numpy.asarray(sol.get_field(0.0, 0.0, z_mm, 0.0)[1])[:, 2],
        rtol=0,
        atol=1e-12,
        err_msg="reloaded solenoid's field doesn't match the original's",
    )
    pkunit.pkok(
        numpy.max(numpy.abs(bz_archived)) > 0.01,
        "archived field looks suspiciously small (the mm-vs-m coordinate bug"
        " this test is named for produces a tiny, near-constant profile): {}",
        bz_archived,
    )
