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

    corr = rft.Corrector(0.1, 2.0, 3.0)
    for p_ref_mev in (1.0, 137.0, 5000.0):
        corr2 = rft.Corrector(0.1, 2.0, 3.0)
        # _serialize_corrector always queries get_kick(1.0) internally;
        # this just confirms that choice wasn't load-bearing by checking
        # the same recovery formula at other reference momenta too
        kick = corr2.get_kick(p_ref_mev)
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

    d = _serialize_corrector(corr)
    pkunit.pkok(abs(d["kx"] - 2.0) < 1e-9, "kx={}", d["kx"])
    pkunit.pkok(abs(d["ky"] - 3.0) < 1e-9, "ky={}", d["ky"])
    pkunit.pkeq(0.1, d["length"])


def test_archive_round_trip():
    import RF_Track as rft
    from pykern import pkunit
    from rslume.rftrack_simulator import RFTrackSimulator

    w = pkunit.empty_work_dir()
    path = str(w.join("corrector.h5"))

    beamline = rft.Lattice()
    corr = rft.Corrector(0.1, 2.0, 3.0)
    corr.set_name("DC1")
    beamline.append(corr)
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
    bunch = rft.Bunch6d_QR(rft.electronmass, 0.05 * rft.nC, -1, 100.0, twiss, 50)

    original = RFTrackSimulator(beamline, bunch)
    original.archive(path)

    reloaded = RFTrackSimulator()
    rft.rng_set_seed(5489)
    reloaded.load_archive(path)

    k1 = original.beamline[0].get_kick(1.0)
    k2 = reloaded.beamline[0].get_kick(1.0)
    pkunit.pkok(
        abs(k1[0] - k2[0]) < 1e-6 and abs(k1[1] - k2[1]) < 1e-6,
        "kick differs: original={} reloaded={}",
        k1,
        k2,
    )

    original.track()
    reloaded.track()
    # the reloaded bunch is a new, statistically-equivalent realization
    # (see RFTrackSimulator.archive()'s docstring), not an exact copy, so
    # compare within a loose tolerance rather than exact equality
    o = original.tracked_bunch.get_phase_space("%x").mean()
    r = reloaded.tracked_bunch.get_phase_space("%x").mean()
    pkunit.pkok(
        abs(o - r) < 0.1 * max(abs(o), 1e-9),
        "mean x differs too much: original={} reloaded={}",
        o,
        r,
    )
