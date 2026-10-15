"""rslume.rftrack tests

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def _build_model():
    import rftrack_util
    import RF_Track as rft
    from rslume.rftrack import LUMERFTrackModel
    from rslume.rftrack_actions import (
        RFTrackReadOnlyScalarVariable,
        RFTrackWritableScalarVariable,
    )
    from rslume.rftrack_simulator import RFTrackSimulator

    q = rft.Quadrupole(0.1, 5.0)
    q.set_name("Q1")
    d = rft.Drift(0.2)
    d.set_name("D1")
    beamline = rft.Lattice()
    beamline.append(q)
    beamline.append(d)

    return LUMERFTrackModel(
        simulator=RFTrackSimulator(
            beamline,
            rftrack_util.twiss_bunch(rft, 100.0, 100, charge_nc=-1, beta=5.0),
        ),
        action_variables=[
            RFTrackWritableScalarVariable(
                name="Q1_strength",
                element_name="Q1",
                attribute="strength",
                default_value=5.0,
            ),
            RFTrackReadOnlyScalarVariable(
                name="Q1_strength_ro",
                element_name="Q1",
                attribute="strength",
                read_only=True,
            ),
        ],
    )


def test_set_and_get():
    from pykern import pkunit

    m = _build_model()
    pkunit.pkeq(5.0, m.get("Q1_strength"))
    m.set({"Q1_strength": 500.0})
    pkunit.pkeq(500.0, m.get("Q1_strength"))
    pkunit.pkeq(500.0, m.get("Q1_strength_ro"))


def test_set_retracks():
    """set() changes the element and re-tracks: the result is the same as
    changing a fresh copy of the beamline directly and tracking it."""
    import numpy
    from pykern import pkunit

    f = "%x %xp %y %yp %t %P"
    m = _build_model()
    m.set({"Q1_strength": 5.0})
    default = m.simulator.tracked_bunch.get_phase_space(f)
    m.set({"Q1_strength": 5000.0})
    actual = m.simulator.tracked_bunch.get_phase_space(f)
    s = _build_model().simulator
    s.find_element("Q1").set_strength(5000.0)
    s.track()
    numpy.testing.assert_array_equal(actual, s.tracked_bunch.get_phase_space(f))
    pkunit.pkok(not numpy.array_equal(default, actual), "Q1's strength had no effect")


def test_read_only_raises():
    from lume.exceptions import ReadOnlyError
    from pykern import pkunit

    with pkunit.pkexcept(ReadOnlyError):
        _build_model().set({"Q1_strength_ro": 1.0})


def test_reset():
    from pykern import pkunit

    m = _build_model()
    m.set({"Q1_strength": 500.0})
    m.reset()
    pkunit.pkeq(5.0, m.get("Q1_strength"))
    pkunit.pkeq(5.0, m.simulator.find_element("Q1").get_strength())


def _build_corrector_model():
    import rftrack_util
    import RF_Track as rft
    from rslume.rftrack import LUMERFTrackModel
    from rslume.rftrack_actions import RFTrackWritableVectorComponentVariable
    from rslume.rftrack_simulator import RFTrackSimulator

    c = rft.Corrector(0.1)
    c.set_name("C1")
    beamline = rft.Lattice()
    beamline.append(c)

    return LUMERFTrackModel(
        simulator=RFTrackSimulator(
            beamline,
            rftrack_util.twiss_bunch(rft, 100.0, 100, charge_nc=-1, beta=5.0),
        ),
        action_variables=[
            RFTrackWritableVectorComponentVariable(
                name="C1_hkick",
                element_name="C1",
                attribute="strength",
                index=0,
                default_value=0.0,
            ),
            RFTrackWritableVectorComponentVariable(
                name="C1_vkick",
                element_name="C1",
                attribute="strength",
                index=1,
                default_value=0.0,
            ),
        ],
    )


def _pkeq_approx(expect, actual):
    # RF-Track's internal unit conversions round-trip a kick through
    # floating point, e.g. 1.0 -> 0.9999999999999998 -- not a bug, just
    # not exact equality.
    import math

    from pykern import pkunit

    pkunit.pkok(
        math.isclose(expect, actual, rel_tol=1e-9, abs_tol=1e-9),
        "expect={} != actual={}",
        expect,
        actual,
    )


def test_vector_component_preserves_other_index():
    m = _build_corrector_model()
    m.set({"C1_hkick": 1.0})
    _pkeq_approx(1.0, m.get("C1_hkick"))
    _pkeq_approx(0.0, m.get("C1_vkick"))
    strength = list(m.simulator.find_element("C1").get_strength())
    _pkeq_approx(1.0, strength[0])
    _pkeq_approx(0.0, strength[1])

    m.set({"C1_vkick": 2.0})
    _pkeq_approx(1.0, m.get("C1_hkick"))
    _pkeq_approx(2.0, m.get("C1_vkick"))
    strength = list(m.simulator.find_element("C1").get_strength())
    _pkeq_approx(1.0, strength[0])
    _pkeq_approx(2.0, strength[1])


def test_vector_component_set_and_get():
    from pykern import pkunit

    m = _build_corrector_model()
    pkunit.pkeq(0.0, m.get("C1_hkick"))
    pkunit.pkeq(0.0, m.get("C1_vkick"))
    m.set({"C1_hkick": 3.0, "C1_vkick": 4.0})
    _pkeq_approx(3.0, m.get("C1_hkick"))
    _pkeq_approx(4.0, m.get("C1_vkick"))
