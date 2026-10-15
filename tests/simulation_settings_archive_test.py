"""RFTrackSimulator.archive()/load_archive() can carry simulation-level
settings (autophase, space charge) that have no live equivalent at all
in RF-Track's own API to read back (confirmed empirically:
rft.cvar.SC_engine's getter is completely type-erased, and dir(rft.cvar)
itself returns [] -- there's no way to discover or identify any
process-global setting from Python). archive()/load_archive() never act
on these themselves; they're purely informational for the caller.

The tracking settings RF-Track can read back -- a Lattice's element offsets,
each element's aperture shape and step counts, and a Volume's integrator
settings -- are archived and restored.

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def _build_bunch(rft):
    import rftrack_util

    return rftrack_util.twiss_bunch(rft, 10.0, 20)


def _build_lattice(rft):
    d = rft.Drift(0.1)
    d.set_name("D0")
    v = rft.Lattice()
    v.append(d)
    return v


def test_pic_space_charge_and_autophase_round_trip():
    from pykern import pkunit
    from rslume.rftrack_simulator import RFTrackSimulator
    import RF_Track as rft

    path = str(pkunit.empty_work_dir().join("archive.h5"))

    RFTrackSimulator(_build_lattice(rft), _build_bunch(rft)).archive(
        path,
        autophase=True,
        space_charge=dict(
            kind="pic", dt_mm=3.0, grid=(8, 8, 16), mirror_m=0.0, smooth=0.5
        ),
    )

    reloaded = RFTrackSimulator()
    reloaded.load_archive(path)
    pkunit.pkeq(True, reloaded.autophase)
    pkunit.pkeq(
        dict(kind="pic", dt_mm=3.0, grid=(8, 8, 16), mirror_m=0.0, smooth=0.5),
        reloaded.space_charge,
    )


def test_p2p_space_charge_round_trip():
    from pykern import pkunit
    from rslume.rftrack_simulator import RFTrackSimulator
    import RF_Track as rft

    path = str(pkunit.empty_work_dir().join("archive.h5"))

    RFTrackSimulator(_build_lattice(rft), _build_bunch(rft)).archive(
        path, autophase=False, space_charge=dict(kind="p2p")
    )

    reloaded = RFTrackSimulator()
    reloaded.load_archive(path)
    pkunit.pkeq(False, reloaded.autophase)
    pkunit.pkeq(dict(kind="p2p"), reloaded.space_charge)


def test_unset_space_charge_defaults_to_none_autophase_is_inferred():
    from pykern import pkunit
    from rslume.rftrack_simulator import RFTrackSimulator
    import RF_Track as rft

    path = str(pkunit.empty_work_dir().join("archive.h5"))

    RFTrackSimulator(_build_lattice(rft), _build_bunch(rft)).archive(path)

    reloaded = RFTrackSimulator()
    reloaded.load_archive(path)
    # autophase=None means "infer it," not "don't record it" -- a
    # Drift-only lattice has no cavity to have ever been autophase()'d,
    # so it infers False, not None (there's no space_charge-like
    # equivalent to infer from, so that one really does stay None).
    pkunit.pkeq(False, reloaded.autophase)
    pkunit.pkeq(None, reloaded.space_charge)


def test_rearchive_keeps_loaded_space_charge():
    import h5py
    import RF_Track as rft
    from pykern import pkunit
    from rslume.rftrack_simulator import RFTrackSimulator

    w = pkunit.empty_work_dir()
    first = str(w.join("first.h5"))
    second = str(w.join("second.h5"))

    RFTrackSimulator(_build_lattice(rft), _build_bunch(rft)).archive(
        first, space_charge={"kind": "p2p"}
    )
    loaded = RFTrackSimulator()
    loaded.load_archive(first)
    loaded.archive(second)
    with h5py.File(second, "r") as f:
        pkunit.pkeq("p2p", f["space_charge"].attrs["kind"])


def test_lattice_offsets_steps_and_aperture_round_trip():
    import numpy
    import RF_Track as rft
    from pykern import pkunit
    from rslume.rftrack_simulator import RFTrackSimulator

    path = str(pkunit.empty_work_dir().join("lattice.h5"))
    lattice = rft.Lattice()
    for i in range(3):
        d = rft.Drift(0.1)
        d.set_name(f"D{i}")
        d.set_nsteps(7 + i)
        d.set_sc_nsteps(3 + i)
        d.set_tt_nsteps(20 + i)
        lattice.append(d)
    lattice[1].set_aperture(0.01, 0.02, "rectangular")
    # x, y, z, (always 1), roll, pitch, yaw
    offsets = numpy.array(
        [
            [0.001, 0.002, 0.0, 1.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
            [-0.003, 0.0, 0.004, 1.0, 0.01, 0.02, 0.0],
        ]
    )
    lattice.set_elements_offsets(offsets)
    original = RFTrackSimulator(lattice, _build_bunch(rft))
    original.archive(path)
    reloaded = RFTrackSimulator()
    reloaded.load_archive(path)
    numpy.testing.assert_array_equal(
        numpy.asarray(reloaded.beamline.get_elements_offsets()), offsets
    )
    for i in range(3):
        o, r = original.beamline[i], reloaded.beamline[i]
        for g in ("get_nsteps", "get_sc_nsteps", "get_tt_nsteps", "get_aperture_shape"):
            pkunit.pkeq(getattr(o, g)(), getattr(r, g)(), "element {} {}", i, g)
    # no tracking comparison: with sc_nsteps set, RF-Track applies its
    # default space-charge engine, which turns float rounding in the
    # round-tripped bunch into visible differences for so few particles


def test_volume_integrator_round_trip():
    import RF_Track as rft
    from pykern import pkunit
    from rslume.rftrack_simulator import RFTrackSimulator

    path = str(pkunit.empty_work_dir().join("volume.h5"))
    v = rft.Volume()
    v.add(rft.Drift(0.5), 0, 0, 0, 0, 0, 0)
    v.set_s0(0.0)
    v.set_s1(0.5)
    settings = dict(
        dt_mm=0.25,
        odeint_algorithm="rkf45",
        odeint_epsabs=1e-8,
        odeint_epsrel=1e-7,
        t_max_mm=1234.0,
        tt_dt_mm=5.0,
    )
    for k, x in settings.items():
        setattr(v, k, x)
    RFTrackSimulator(v, _build_bunch(rft)).archive(path)
    reloaded = RFTrackSimulator()
    reloaded.load_archive(path)
    pkunit.pkeq(settings, {k: getattr(reloaded.beamline, k) for k in settings})
