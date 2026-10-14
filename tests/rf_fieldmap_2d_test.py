"""rslume.rftrack archive()/load_archive() coverage for RF_FieldMap_2d
(a 2D field-map CAVITY, as used by the CERN Linac4 CCDTL section) --
specifically.

There's no direct 2D array getter for this class (unlike RF_FieldMap_1d's
get_Ez()), so the serializer samples get_field_complex(x, y, z, t) point
by point over the full (nz, nr) grid instead (cylindrical symmetry: Er is
just the Cartesian Ex component at (x=r, y=0)). Two things make this
easy to get subtly wrong, caught only by comparing a reconstructed
element's get_field() against the original's, not just checking shapes:

1. get_field_complex()'s result already has the element's own phid
   rotation baked in -- extracting with phid left as-is and then also
   calling set_phid() on the reconstruction double-applies the rotation.
2. get_field_complex() only accepts a scalar z (unlike get_field()'s
   vectorized z), so the extraction loop is genuinely point-by-point.

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def _build_cavity(rft, numpy):
    z = numpy.linspace(0, numpy.pi, 11)
    r = numpy.linspace(0, 1, 6)
    cav = rft.RF_FieldMap_2d(
        (1e5 * numpy.cos(z)[:, None] * r[None, :]).astype(complex),
        (1e6 * numpy.sin(z)[:, None] * (1 - 0.3 * r[None, :])).astype(complex),
        0, 0, 0.005, 0.02, -1, 3e9, 1.0, 1.0, 1.0,
    )
    cav.set_name("C1")
    cav.set_phid(15.0)
    return cav


def test_serialize_does_not_double_apply_phid():
    import numpy
    import RF_Track as rft
    from pykern import pkunit
    from rslume.rftrack_archive import _serialize_rf_fieldmap_2d

    cav = _build_cavity(rft, numpy)
    orig_phid = cav.get_phid()
    d = _serialize_rf_fieldmap_2d(cav)

    # extracting must not mutate the element's own phid
    pkunit.pkeq(orig_phid, cav.get_phid())

    rebuilt = rft.RF_FieldMap_2d(
        d["er"], d["ez"], 0, 0, d["hr"], d["hz"], -1, d["frequency"],
        d["direction"], d["p_map"], d["p_actual"],
    )
    rebuilt.set_phid(d["phid"])

    z_mm = numpy.linspace(0, cav.get_length(), 15) * 1000.0
    for x_mm in (0.0, 1.0, 3.0):
        numpy.testing.assert_allclose(
            rebuilt.get_field(x_mm, 0.0, z_mm, 0.0)[0],
            cav.get_field(x_mm, 0.0, z_mm, 0.0)[0],
            rtol=0,
            atol=1e-6,
            err_msg=f"x_mm={x_mm}: field differs",
        )


def test_archive_round_trip():
    import h5py
    import numpy
    import RF_Track as rft
    from pykern import pkunit
    from rslume.rftrack_simulator import RFTrackSimulator

    path = str(pkunit.empty_work_dir().join("cavity2d.h5"))

    cav = _build_cavity(rft, numpy)
    beamline = rft.Lattice()
    beamline.append(cav)
    beamline.append(rft.Drift(0.1))

    twiss = rft.Bunch6d_twiss()
    twiss.beta_x = 1.0
    twiss.beta_y = 1.0
    twiss.alpha_x = 0.0
    twiss.alpha_y = 0.0
    twiss.emitt_x = 1.0
    twiss.emitt_y = 1.0
    twiss.sigma_t = 1.0
    twiss.sigma_pt = 1.0
    rft.rng_set_seed(5489)
    RFTrackSimulator(
        beamline,
        rft.Bunch6d_QR(rft.electronmass, 0.05 * rft.nC, -1, 100.0, twiss, 30),
    ).archive(path)

    with h5py.File(path, "r") as f:
        pkunit.pkeq("RF_FieldMap_2d", f["elements"]["0"].attrs["class"])
        # a shared "field_maps" dataset, referenced by "@<md5>" --
        # see RFTrackSimulator.archive()'s own docstring
        pkunit.pkeq(
            (11, 6), f["field_maps"][f["elements"]["0"].attrs["ez"][1:]].shape
        )

    reloaded = RFTrackSimulator()
    rft.rng_set_seed(5489)
    reloaded.load_archive(path)

    z_mm = numpy.linspace(0, cav.get_length(), 15) * 1000.0
    numpy.testing.assert_allclose(
        reloaded.beamline[0].get_field(1.0, 0.0, z_mm, 0.0)[0],
        beamline[0].get_field(1.0, 0.0, z_mm, 0.0)[0],
        rtol=0,
        atol=1e-6,
        err_msg="reloaded cavity field differs",
    )
