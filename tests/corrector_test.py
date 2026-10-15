"""rslume.rftrack archive()/load_archive() coverage for Corrector.

Corrector(L, Kx, Ky)'s Kx/Ky are documented (RF-Track reference manual,
section 5.2.5) as an integrated strength in T.mm, not a kick angle -- and
there's no direct Kx/Ky getter, only get_kick(p_ref_mev), which returns
the EQUIVALENT kick angle in mrad for a particle with that reference
momentum. Recovering Kx/Ky means inverting that relation for an arbitrary
reference momentum (confirmed empirically: any choice of p_ref recovers
the same Kx/Ky, to floating-point precision).

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def test_serialize_recovers_kx_ky_independent_of_reference_momentum():
    import RF_Track as rft
    from pykern import pkunit
    from rslume.rftrack_archive import _serialize_corrector

    for p_ref_mev in (1.0, 137.0, 5000.0):
        # _serialize_corrector always queries get_kick(1.0) internally;
        # this just confirms that choice wasn't load-bearing by checking
        # the same recovery formula at other reference momenta too
        kick = rft.Corrector(0.1, 2.0, 3.0).get_kick(p_ref_mev)
        import scipy.constants

        c_mm_per_ns = scipy.constants.c / 1e6
        kx = kick[0] * p_ref_mev / c_mm_per_ns
        ky = kick[1] * p_ref_mev / c_mm_per_ns
        pkunit.pkok(
            abs(kx - 2.0) < 1e-9 and abs(ky - 3.0) < 1e-9,
            "p_ref={}: recovered ({}, {}) != (2.0, 3.0)",
            p_ref_mev,
            kx,
            ky,
        )

    d = _serialize_corrector(rft.Corrector(0.1, 2.0, 3.0))
    pkunit.pkok(abs(d["kx"] - 2.0) < 1e-9, "kx={}", d["kx"])
    pkunit.pkok(abs(d["ky"] - 3.0) < 1e-9, "ky={}", d["ky"])
    pkunit.pkeq(0.1, d["length"])


def test_archive_round_trip():
    import rftrack_util
    import numpy
    import RF_Track as rft
    from pykern import pkunit
    from rslume.rftrack_simulator import RFTrackSimulator

    path = str(pkunit.empty_work_dir().join("corrector.h5"))

    beamline = rft.Lattice()
    corr = rft.Corrector(0.1, 2.0, 3.0)
    corr.set_name("DC1")
    beamline.append(corr)
    beamline.append(rft.Drift(0.1))

    original = RFTrackSimulator(
        beamline,
        rftrack_util.twiss_bunch(rft, 100.0, 50),
    )
    original.archive(path)

    reloaded = RFTrackSimulator()
    reloaded.load_archive(path)
    numpy.testing.assert_allclose(
        reloaded.beamline[0].get_kick(1.0),
        original.beamline[0].get_kick(1.0),
        rtol=1e-12,
    )

    original.track()
    reloaded.track()
    # archive() stores the bunch's own macroparticles, so the reloaded copy
    # tracks to the same result, particle by particle
    f = "%x %xp %y %yp %t %P"
    numpy.testing.assert_allclose(
        reloaded.tracked_bunch.get_phase_space(f),
        original.tracked_bunch.get_phase_space(f),
        rtol=1e-12,
        atol=1e-12,
    )
