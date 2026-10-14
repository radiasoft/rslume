"""rslume.rftrack ParticleGroup <-> Bunch6dT conversion
(`bunch6dt_to_particlegroup()`/`particlegroup_to_bunch6dt()`).

Treats the bunch as a genuine time snapshot: Bunch6dT's own `Z` <->
ParticleGroup's `z`, and by default the bunch's common time `%t` ->
ParticleGroup's `t`; with `snapshot_time=False`, each particle's creation
time `t0` <-> `t` instead, so a Bunch6dT round-trips exactly.

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def _build_bunch6dt(rft, numpy):
    x = numpy.array([1.0, 2.0, -1.5])
    px = numpy.array([10.0, -20.0, 5.0])
    y = numpy.array([0.5, 1.5, -0.5])
    py = numpy.array([5.0, 6.0, -3.0])
    z = numpy.array([100.0, 200.0, -50.0])
    pz = numpy.array([5000.0, 5000.0, 4000.0])
    mass = numpy.full(3, rft.electronmass)
    q = numpy.full(3, -1.0)
    n = numpy.full(3, 1e9)
    t0 = numpy.array([3.0, 4.0, -1.0])
    return rft.Bunch6dT(numpy.column_stack([x, px, y, py, z, pz, mass, q, n, t0]))


def test_z_and_t():
    import numpy
    import RF_Track as rft
    import scipy.constants
    from pykern import pkunit
    from rslume.rftrack_utils import bunch6dt_to_particlegroup

    b = _build_bunch6dt(rft, numpy)
    pg = bunch6dt_to_particlegroup(b)

    pkunit.pkeq("electron", pg.species)
    z_expect = b.get_phase_space("%Z")[:, 0] / 1000.0
    numpy.testing.assert_allclose(pg.z, z_expect, rtol=0, atol=1e-9)
    # ParticleGroup t is seconds; RF-Track's %t/%t0 are mm/c
    t_mm_c = pg.t * scipy.constants.c * 1e3
    numpy.testing.assert_allclose(
        t_mm_c, b.get_phase_space("%t")[:, 0], err_msg="default t is not the common %t"
    )
    t0_mm_c = bunch6dt_to_particlegroup(b, snapshot_time=False).t * scipy.constants.c * 1e3
    numpy.testing.assert_allclose(
        t0_mm_c, b.get_phase_space("%t0")[:, 0], err_msg="snapshot_time=False t is not t0"
    )


def test_round_trip():
    import numpy
    import RF_Track as rft
    from rslume.rftrack_utils import bunch6dt_to_particlegroup, particlegroup_to_bunch6dt

    b = _build_bunch6dt(rft, numpy)
    fields = "%X %Y %Z %Px %Py %Pz %m %Q %N %t0"
    numpy.testing.assert_allclose(
        particlegroup_to_bunch6dt(
            bunch6dt_to_particlegroup(b, snapshot_time=False)
        ).get_phase_space(fields),
        b.get_phase_space(fields),
        rtol=0,
        atol=1e-5,
    )
