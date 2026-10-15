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


def test_volume_archive_round_trip():
    import h5py
    import numpy
    import RF_Track as rft
    from pykern import pkunit
    import rftrack_util
    from rslume.rftrack_simulator import RFTrackSimulator

    path = str(pkunit.empty_work_dir().join("volume.h5"))

    original = RFTrackSimulator(
        rftrack_util.volume_with_cavity(rft), rftrack_util.twiss_bunch(rft, 10.0, 200)
    )
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

    pkunit.pkeq(
        10.0, original.beamline[0].get_phid(), "archive() must not mutate beamline"
    )

    reloaded = RFTrackSimulator()
    reloaded.load_archive(path)

    pkunit.pkeq("Volume", type(reloaded.beamline).__name__)
    pkunit.pkeq(
        original.beamline[0].get_length(),
        reloaded.beamline[0].get_length(),
    )
    pkunit.pkeq(10.0, reloaded.beamline[0].get_phid())

    original.track()
    reloaded.track()
    # archive() stores the bunch's own macroparticles, so the reloaded copy
    # tracks to the same result, particle by particle, to float rounding
    f = "%x %xp %y %yp %t %P"
    numpy.testing.assert_allclose(
        reloaded.tracked_bunch.get_phase_space(f),
        original.tracked_bunch.get_phase_space(f),
        rtol=1e-12,
        atol=1e-12,
    )
