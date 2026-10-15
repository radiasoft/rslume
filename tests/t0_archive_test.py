"""RFTrackSimulator.archive()/load_archive() faithfully preserves an RF
element's autophase() correction (t0), not just the phid it was built
with -- get_phid() never reflects it (confirmed empirically: it always
reads back the phid the element was constructed with), so this is the
only way an archived element's actual effective phase survives the
round trip. Distinct from volume_archive_test.py, which deliberately
archives *before* track()/autophase() specifically to avoid this case.

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def test_t0_archive_round_trip():
    import numpy
    import RF_Track as rft
    import rftrack_util
    from pykern import pkunit
    from rslume.rftrack_simulator import RFTrackSimulator

    path = str(pkunit.empty_work_dir().join("archive.h5"))
    volume = rftrack_util.volume_with_cavity(rft)
    cavity = volume[0]
    p0 = rft.Bunch6d(
        rft.electronmass, 0.0, -1, numpy.array([0.0, 0.0, 0.0, 0.0, 0.0, 10.0])
    )
    volume.unset_t0()
    volume.autophase(p0)
    pkunit.pkok(cavity.t0_is_set(), "expected autophase() to set t0")
    original_t0 = cavity.get_t0()
    # get_phid() never reflects autophase() -- still the construction
    # value, not the real effective phase
    pkunit.pkeq(10.0, cavity.get_phid())

    original = RFTrackSimulator(volume, rftrack_util.twiss_bunch(rft, 10.0, 200))
    original.archive(path)
    original.track()

    reloaded = RFTrackSimulator()
    reloaded.load_archive(path)
    pkunit.pkok(reloaded.beamline[0].t0_is_set(), "expected t0 to survive the archive")
    pkunit.pkeq(original_t0, reloaded.beamline[0].get_t0())
    # archive() was never told autophase=True explicitly -- it's
    # inferred from the cavity's own nonzero archived t0.
    pkunit.pkeq(True, reloaded.autophase)
    reloaded.track()

    # no autophase() was called on the reloaded copy at all -- t0 alone
    # reproduces the same physics, particle by particle, to float rounding
    f = "%x %xp %y %yp %t %P"
    numpy.testing.assert_allclose(
        reloaded.tracked_bunch.get_phase_space(f),
        original.tracked_bunch.get_phase_space(f),
        rtol=1e-12,
        atol=1e-12,
    )
