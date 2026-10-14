"""rslume.rftrack_utils field-map readers and result writers

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def test_load_field_map():
    import numpy
    from pykern import pkunit
    from pykern.pkcollections import PKDict
    from rslume.rftrack_utils import load_field_map

    f = str(pkunit.empty_work_dir().join("map.txt"))
    numpy.savetxt(f, numpy.column_stack([[0.0, 0.5, 1.0], [1.0, -4.0, 2.0]]))
    field, step, length = load_field_map(
        PKDict(file=f, rescale_mode="factor", scale_factor=2.0)
    )
    numpy.testing.assert_allclose(field, [2.0, -8.0, 4.0])
    pkunit.pkeq(0.5, step)
    pkunit.pkeq(1.0, length)
    field, _, _ = load_field_map(PKDict(file=f, rescale_mode="target", target_field=1.0))
    numpy.testing.assert_allclose(field, [0.25, -1.0, 0.5])


def test_load_field_map_2d():
    import numpy
    from pykern import pkunit
    from pykern.pkcollections import PKDict
    from rslume.rftrack_utils import load_field_map_2d

    f = str(pkunit.empty_work_dir().join("map2d.txt"))
    # Z [cm], R [cm], Ez, Er, |E|, H -- Z varies fastest
    rows = [[z, r, 10.0 * z + r, 100.0 * z + r, 0.0, 0.0] for r in (0.0, 1.0) for z in (0.0, 1.0, 2.0)]
    numpy.savetxt(f, numpy.array(rows))
    er, ez, hr, hz = load_field_map_2d(PKDict(file=f))
    pkunit.pkeq((3, 2), ez.shape)
    pkunit.pkeq(0.01, hz)
    pkunit.pkeq(0.01, hr)
    numpy.testing.assert_allclose(ez[2, 1], 21.0e6)
    numpy.testing.assert_allclose(er[1, 0], 100.0e6)


def test_save_particles():
    import numpy
    import RF_Track as rft
    from pykern import pkunit
    from rslume.rftrack_utils import save_particles

    with pkunit.save_chdir_work():
        save_particles(
            "p.npy",
            rft.Bunch6d(
                numpy.array(
                    [[1.0, 2.0, 3.0, 4.0, 0.0, 5.0, rft.electronmass, -1.0, 1.0, 1]]
                )
            ),
        )
        a = numpy.load("p.npy")
        pkunit.pkeq((1, 12), a.shape)
        numpy.testing.assert_allclose(a[0, 0], 0.001)
        numpy.testing.assert_allclose(a[0, 2], 0.003)
        numpy.testing.assert_allclose(a[0, 9], 5.0e6, rtol=1e-6)


def test_save_particles_bunch6dt():
    import numpy
    import RF_Track as rft
    from pykern import pkunit
    from rslume.rftrack_utils import save_particles

    with pkunit.save_chdir_work():
        save_particles(
            "p.npy",
            rft.Bunch6dT(
                numpy.array(
                    [[1.0, 2.0, 3.0, 4.0, 0.0, 5.0, rft.electronmass, -1.0, 1.0, 0.0]]
                )
            ),
        )
        a = numpy.load("p.npy")
        pkunit.pkeq((1, 12), a.shape)
        numpy.testing.assert_allclose(a[0, 0], 0.001)
        numpy.testing.assert_allclose(a[0, 2], 0.003)


def test_save_stats_lattice_and_volume():
    import numpy
    import RF_Track as rft
    from pykern import pkunit
    from rslume.rftrack_utils import save_stats

    def _bunch():
        t = rft.Bunch6d_twiss()
        t.beta_x = t.beta_y = t.emitt_x = t.emitt_y = 1.0
        t.alpha_x = t.alpha_y = 0.0
        t.sigma_t = t.sigma_pt = 1.0
        rft.rng_set_seed(5489)
        return rft.Bunch6d_QR(rft.electronmass, 0.05 * rft.nC, -1, 100.0, t, 100)

    with pkunit.save_chdir_work():
        lattice = rft.Lattice()
        lattice.append(rft.Drift(1.0))
        lattice.track(_bunch())
        save_stats(lattice)
        a = numpy.load("stats.npy")
        # transport table, then on-axis Ez and Bz; s is in meters
        pkunit.pkeq(34, a.shape[1])
        numpy.testing.assert_allclose(a[-1, 0], 1.0)

        volume = rft.Volume()
        volume.add(rft.Drift(1.0), 0, 0, 0, 0, 0, 0)
        volume.set_s0(0)
        volume.set_s1(1.0)
        volume.tt_dt_mm = 10.0
        volume.track(_bunch())
        save_stats(volume)
        b = numpy.load("stats.npy")
        pkunit.pkeq(34, b.shape[1])
        numpy.testing.assert_allclose(b[-1, 0], 1.0, atol=0.011)
