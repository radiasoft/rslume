"""rslume.rftrack tests

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def _build_model():
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

    twiss = rft.Bunch6d_twiss()
    twiss.beta_x = 5.0
    twiss.beta_y = 5.0
    twiss.alpha_x = 0.0
    twiss.alpha_y = 0.0
    twiss.emitt_x = 1.0
    twiss.emitt_y = 1.0
    twiss.sigma_t = 1.0
    twiss.sigma_pt = 1.0
    return LUMERFTrackModel(
        simulator=RFTrackSimulator(
            beamline,
            rft.Bunch6d_QR(rft.electronmass, -1 * rft.nC, -1, 100.0, twiss, 100),
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
    from pykern import pkunit

    m = _build_model()
    m.set({"Q1_strength": 5.0})
    x1 = m.simulator.tracked_bunch.get_phase_space("%x").mean()
    m.set({"Q1_strength": 5000.0})
    x2 = m.simulator.tracked_bunch.get_phase_space("%x").mean()
    pkunit.pkok(x1 != x2, "expected tracked beam to change: x1={} x2={}", x1, x2)


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
    import RF_Track as rft
    from rslume.rftrack import LUMERFTrackModel
    from rslume.rftrack_actions import RFTrackWritableVectorComponentVariable
    from rslume.rftrack_simulator import RFTrackSimulator

    c = rft.Corrector(0.1)
    c.set_name("C1")
    beamline = rft.Lattice()
    beamline.append(c)

    twiss = rft.Bunch6d_twiss()
    twiss.beta_x = 5.0
    twiss.beta_y = 5.0
    twiss.alpha_x = 0.0
    twiss.alpha_y = 0.0
    twiss.emitt_x = 1.0
    twiss.emitt_y = 1.0
    twiss.sigma_t = 1.0
    twiss.sigma_pt = 1.0
    return LUMERFTrackModel(
        simulator=RFTrackSimulator(
            beamline,
            rft.Bunch6d_QR(rft.electronmass, -1 * rft.nC, -1, 100.0, twiss, 100),
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
