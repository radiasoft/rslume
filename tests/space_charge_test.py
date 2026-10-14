"""rslume.rftrack_utils.apply_space_charge() and the archive round trip

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

_SETTINGS = dict(kind="pic", dt_mm=5.0, grid=(16, 16, 16), mirror_m=0.0, smooth=0.5)


def _build_simulator(rft):
    from rslume.rftrack_simulator import RFTrackSimulator

    v = rft.Volume()
    v.add(rft.Drift(0.5), 0, 0, 0, 0, 0, 0)
    v.set_s0(0)
    v.set_s1(0.5)
    t = rft.Bunch6d_twiss()
    t.beta_x = t.beta_y = t.emitt_x = t.emitt_y = 1.0
    t.alpha_x = t.alpha_y = 0.0
    t.sigma_t = t.sigma_pt = 1.0
    rft.rng_set_seed(5489)
    return RFTrackSimulator(
        v, rft.Bunch6d_QR(rft.electronmass, 100.0 * rft.nC, -1, 2.0, t, 500)
    )


def _sigma_x(simulator):
    simulator.track()
    return simulator.tracked_bunch.get_phase_space("%x").std()


def test_loaded_archive_needs_apply_space_charge():
    import numpy
    import RF_Track as rft
    from pykern import pkunit
    from rslume.rftrack_simulator import RFTrackSimulator
    from rslume.rftrack_utils import apply_space_charge

    path = str(pkunit.empty_work_dir().join("sc.h5"))
    # the SC_engine is process-global and can't be unset, so the
    # no-space-charge runs come first
    without = _sigma_x(_build_simulator(rft))
    original = _build_simulator(rft)
    apply_space_charge(original.beamline, _SETTINGS)
    with_sc = _sigma_x(original)
    pkunit.pkok(with_sc > 10 * without, "expected space charge: {} vs {}", with_sc, without)
    original.archive(path, space_charge=_SETTINGS)

    loaded = RFTrackSimulator()
    loaded.load_archive(path)
    loaded.apply_space_charge()
    numpy.testing.assert_allclose(_sigma_x(loaded), with_sc, rtol=1e-2)


def test_unknown_kind():
    import RF_Track as rft
    from pykern import pkunit
    from rslume.rftrack_utils import apply_space_charge

    with pkunit.pkexcept(ValueError):
        apply_space_charge(rft.Lattice(), dict(kind="nope"))
