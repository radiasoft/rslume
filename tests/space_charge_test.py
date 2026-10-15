"""rslume.rftrack_utils.apply_space_charge(), reset_space_charge() and the
archive round trip

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

_SETTINGS = dict(kind="pic", dt_mm=5.0, grid=(16, 16, 16), mirror_m=0.0, smooth=0.5)


def test_loaded_archive_needs_apply_space_charge():
    import numpy
    import RF_Track as rft
    from pykern import pkunit
    from rslume.rftrack_simulator import RFTrackSimulator
    from rslume.rftrack_utils import apply_space_charge, reset_space_charge

    path = str(pkunit.empty_work_dir().join("sc.h5"))
    _build_simulator(rft).archive(path, space_charge=_SETTINGS)
    loaded = RFTrackSimulator()
    loaded.load_archive(path)
    without = _phase_space(loaded)
    # PIC tracking amplifies the reloaded bunch's float rounding (~1e-15)
    # to about 1% in the beam sigmas, so the loaded simulator is compared
    # with a fresh one tracking the same reloaded bunch.
    fresh = _build_simulator(rft)
    fresh.initial_bunch = loaded.initial_bunch
    try:
        loaded.apply_space_charge()
        actual = _phase_space(loaded)
        apply_space_charge(fresh.beamline, _SETTINGS)
        numpy.testing.assert_array_equal(actual, _phase_space(fresh))
    finally:
        reset_space_charge()
    pkunit.pkok(not numpy.array_equal(actual, without), "space charge had no effect")


def test_reset_space_charge():
    import numpy
    import RF_Track as rft
    from pykern import pkunit
    from rslume.rftrack_utils import apply_space_charge, reset_space_charge

    # Each step tracks a fresh simulator: apply_space_charge() also sets the
    # Volume's sc_dt_mm, which the reset leaves alone.
    without = _phase_space(_build_simulator(rft))
    try:
        s = _build_simulator(rft)
        apply_space_charge(s.beamline, _SETTINGS)
        pkunit.pkok(
            not numpy.array_equal(_phase_space(s), without),
            "space charge had no effect",
        )
    finally:
        reset_space_charge()
    numpy.testing.assert_array_equal(_phase_space(_build_simulator(rft)), without)
    apply_space_charge(_build_simulator(rft).beamline, _SETTINGS)
    # a simulator without space charge settings resets the engine
    s = _build_simulator(rft)
    s.apply_space_charge()
    numpy.testing.assert_array_equal(_phase_space(s), without)


def test_unknown_kind():
    import RF_Track as rft
    from pykern import pkunit
    from rslume.rftrack_utils import apply_space_charge

    with pkunit.pkexcept(ValueError):
        apply_space_charge(rft.Lattice(), dict(kind="nope"))


def _build_simulator(rft):
    import rftrack_util
    from rslume.rftrack_simulator import RFTrackSimulator

    v = rft.Volume()
    v.add(rft.Drift(0.5), 0, 0, 0, 0, 0, 0)
    v.set_s0(0)
    v.set_s1(0.5)
    return RFTrackSimulator(v, rftrack_util.twiss_bunch(rft, 2.0, 500, charge_nc=100.0))


def _phase_space(simulator):
    simulator.track()
    return simulator.tracked_bunch.get_phase_space("%X %Px %Y %Py %Z %Pz")
