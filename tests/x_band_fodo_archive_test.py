"""rslume.rftrack_simulator.RFTrackSimulator.archive()/load_archive() round-trip test,
against the same "X-band Linac FODO Cell" lattice used by x_band_fodo_test.py.

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def test_archive_round_trip():
    import numpy
    import RF_Track as rft
    from pykern import pkunit
    import rftrack_util
    from rslume.rftrack_simulator import RFTrackSimulator

    path = str(pkunit.empty_work_dir().join("archive.h5"))

    original = RFTrackSimulator(
        rftrack_util.x_band_fodo_lattice(rft),
        rftrack_util.twiss_bunch(rft, 100.0, 100, emitt=5.0),
    )
    original.track()
    original.archive(path)

    # the archive is plain, self-describing HDF5 -- not something that
    # requires importing this module to read back (that's the whole point:
    # it's the interchange contract with anything that reads it)
    import h5py

    with h5py.File(path, "r") as f:
        # also a real standalone openPMD particle file (archive()'s own
        # docstring) -- "dataType" is openPMD's own root attr, not ours.
        pkunit.pkeq(b"openPMD", f.attrs["dataType"])
        pkunit.pkeq("rslume", f.attrs["software"])
        pkunit.pkeq("Bunch6d", f.attrs["bunch_type"])
        pkunit.pkeq("Drift", f["elements"]["0"].attrs["class"])
        pkunit.pkeq("D0", f["elements"]["0"].attrs["name"])
        pkunit.pkeq("Pillbox_Cavity", f["elements"]["1"].attrs["class"])
        pkunit.pkok("particles" in f, "expected a particles group")

    # load_archive() fills in an otherwise-empty simulator, same calling
    # convention as rslume.elegant.Elegant()/load_archive() (and
    # lume.base.Base's in general)
    reloaded = RFTrackSimulator()
    reloaded.load_archive(path)
    reloaded.track()

    pkunit.pkeq(
        original.beamline.size(), reloaded.beamline.size(), "element count differs"
    )
    for i in range(original.beamline.size()):
        pkunit.pkeq(
            original.beamline[i].get_name(),
            reloaded.beamline[i].get_name(),
            "element {} name differs",
            i,
        )

    # archive() stores the bunch's own macroparticles, so the reloaded copy
    # tracks to the same result, particle by particle, to float rounding
    f = "%x %xp %y %yp %t %P"
    numpy.testing.assert_allclose(
        reloaded.tracked_bunch.get_phase_space(f),
        original.tracked_bunch.get_phase_space(f),
        rtol=1e-12,
        atol=1e-12,
    )
