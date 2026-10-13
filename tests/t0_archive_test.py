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

from volume_archive_test import _build_bunch, _build_volume


def test_t0_archive_round_trip():
    import RF_Track as rft
    from pykern import pkunit
    from rslume.rftrack_simulator import RFTrackSimulator

    w = pkunit.empty_work_dir()
    path = str(w.join("archive.h5"))

    import numpy

    volume = _build_volume(rft)
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

    rft.rng_set_seed(5489)
    original = RFTrackSimulator(volume, _build_bunch(rft))
    original.archive(path)
    original.track()

    # load_archive() reads the archived particles directly -- no new
    # random draw, so no need to reseed before it (unlike original's
    # own _build_bunch() call above).
    reloaded = RFTrackSimulator()
    reloaded.load_archive(path)
    pkunit.pkok(reloaded.beamline[0].t0_is_set(), "expected t0 to survive the archive")
    pkunit.pkeq(original_t0, reloaded.beamline[0].get_t0())
    # archive() was never told autophase=True explicitly -- it's
    # inferred from the cavity's own nonzero archived t0.
    pkunit.pkeq(True, reloaded.autophase)
    reloaded.track()

    # no autophase() was called on the reloaded copy at all -- t0 alone
    # reproduces the same physics. Not bit-exact: the bunch itself went
    # through an openPMD unit round-trip (mm<->m, MeV/c<->eV/c) with its
    # own float64 rounding, same ~1e-7 relative noise already tolerated
    # elsewhere (x_band_fodo_archive_test.py).
    for field in ("x", "y", "K"):
        o = original.tracked_bunch.get_phase_space(f"%{field}")
        r = reloaded.tracked_bunch.get_phase_space(f"%{field}")
        pkunit.pkok(
            (abs(o - r) < 1e-4 * (abs(o) + 1e-9)).all(),
            "{} differs too much: original={} reloaded={}",
            field,
            o,
            r,
        )
