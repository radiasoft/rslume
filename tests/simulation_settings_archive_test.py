"""RFTrackSimulator.archive()/load_archive() can carry simulation-level
settings (autophase, space charge) that have no live equivalent at all
in RF-Track's own API to read back (confirmed empirically:
rft.cvar.SC_engine's getter is completely type-erased, and dir(rft.cvar)
itself returns [] -- there's no way to discover or identify any
process-global setting from Python). archive()/load_archive() never act
on these themselves; they're purely informational for the caller.

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
    return rft.Bunch6d_QR(rft.electronmass, 0.05 * rft.nC, -1, 10.0, twiss, 20)


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
        space_charge=dict(kind="pic", dt_mm=3.0, grid=(8, 8, 16), mirror_m=0.0, smooth=0.5),
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
