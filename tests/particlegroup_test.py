"""rslume.rftrack ParticleGroup <-> Bunch6d conversion
(`bunch6d_to_particlegroup()`/`particlegroup_to_bunch6d()`).

Both directions treat the bunch as a fixed-z-plane snapshot: Bunch6d's own
`t` <-> ParticleGroup's `t`, with `z` fixed at 0 (ParticleGroup has no
"other" species, so a bunch whose mass/charge don't match beamphysics'
electron/positron/proton raises instead of guessing).

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


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
    rft.rng_set_seed(5489)
    return rft.Bunch6d_QR(rft.electronmass, 0.05 * rft.nC, -1, 100.0, twiss, 50)


def test_bunch6d_to_particlegroup():
    import RF_Track as rft
    from pykern import pkunit
    from rslume.rftrack_utils import bunch6d_to_particlegroup

    pg = bunch6d_to_particlegroup(_build_bunch(rft))

    pkunit.pkeq("electron", pg.species)
    pkunit.pkeq(50, len(pg.x))
    pkunit.pkok(
        abs(pg.charge - 0.05e-9) < 1e-15,
        "expected total charge near 0.05 nC, got {} C",
        pg.charge,
    )
    pkunit.pkok(
        abs(pg.energy.mean() - 100.0e6) / 100.0e6 < 0.01,
        "expected mean energy near 100 MeV, got {} eV",
        pg.energy.mean(),
    )


def test_round_trip():
    import numpy
    import RF_Track as rft
    from rslume.rftrack_utils import bunch6d_to_particlegroup, particlegroup_to_bunch6d

    bunch = _build_bunch(rft)
    fields = "%x %xp %y %yp %t %P %m %Q %N"
    numpy.testing.assert_allclose(
        particlegroup_to_bunch6d(bunch6d_to_particlegroup(bunch)).get_phase_space(fields),
        bunch.get_phase_space(fields),
        rtol=0,
        atol=1e-6,
    )


def test_unknown_species_raises():
    import numpy
    import RF_Track as rft
    from pykern import pkunit
    from rslume.rftrack_utils import bunch6d_to_particlegroup

    # a proton-mass particle with charge +2 (e.g. an alpha-like ion) isn't
    # electron/positron/proton -- beamphysics has no "other" species
    with pkunit.pkexcept(ValueError):
        bunch6d_to_particlegroup(
            rft.Bunch6d(
                numpy.array([[0.0, 0.0, 0.0, 0.0, 0.0, 100.0, 938.272, 2.0, 1e9, 1]])
            )
        )


def test_large_angle_momentum_matches_rf_track():
    import numpy
    import RF_Track as rft
    from pykern import pkunit
    from rslume.rftrack_utils import bunch6d_to_particlegroup, particlegroup_to_bunch6d

    # 300/200 mrad: px = P*xp (small-angle) would be off by ~6%
    bunch = rft.Bunch6d(
        numpy.array(
            [
                [0.0, 300.0, 0.0, 200.0, 0.0, 2.0, rft.electronmass, -1.0, 1.0, 1],
                [0.0, 0.0, 0.0, 0.0, 0.0, 2.0, rft.electronmass, -1.0, 1.0, 2],
            ]
        )
    )
    pg = bunch6d_to_particlegroup(bunch)
    expect = bunch.get_phase_space("%Px %Py %Pz")
    actual = numpy.column_stack([pg.px, pg.py, pg.pz]) / 1e6
    pkunit.pkok(
        numpy.abs(actual - expect).max() < 1e-9,
        "momentum differs from RF-Track: {} vs {}",
        actual,
        expect,
    )
    pkunit.pkok(
        numpy.abs(
            particlegroup_to_bunch6d(pg).get_phase_space("%xp %yp")
            - bunch.get_phase_space("%xp %yp")
        ).max()
        < 1e-6,
        "angles do not round-trip",
    )


def test_bunch6dt_snapshot_keeps_bunch_length_into_bunch6d():
    import numpy
    import RF_Track as rft
    from pykern import pkunit
    from rslume.rftrack_utils import (
        bunch6dt_to_particlegroup,
        particlegroup_to_bunch6d,
    )

    # A tracked Bunch6dT has every Z at one common time (%t) but t0 = 0
    # (or an emission time): the longitudinal spread must land in the
    # Bunch6d's per-particle arrival time, not be lost.
    n = 200
    z = numpy.linspace(-1.0, 1.0, n)
    p_mev = 50.0
    b = rft.Bunch6dT(
        numpy.column_stack(
            [
                numpy.zeros(n),
                numpy.zeros(n),
                numpy.zeros(n),
                numpy.zeros(n),
                z,
                numpy.full(n, p_mev),
                numpy.full(n, rft.electronmass),
                numpy.full(n, -1.0),
                numpy.ones(n),
                numpy.zeros(n),
            ]
        )
    )
    v = rft.Volume()
    v.add(rft.Drift(1.0), 0, 0, 0, 0, 0, 0)
    v.set_s0(0)
    v.set_s1(1.0)
    tracked = v.track(b)

    out = particlegroup_to_bunch6d(
        bunch6dt_to_particlegroup(tracked)
    )
    beta = p_mev / numpy.hypot(p_mev, rft.electronmass)
    expect_sigma_t = tracked.get_phase_space("%Z")[:, 0].std() / beta
    actual_sigma_t = out.get_phase_space("%t")[:, 0].std()
    pkunit.pkok(
        abs(actual_sigma_t - expect_sigma_t) < 1e-3 * expect_sigma_t,
        "sigma_t [mm/c] {} != sigma_z/beta {}",
        actual_sigma_t,
        expect_sigma_t,
    )
