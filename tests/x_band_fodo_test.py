"""rslume.rftrack test against a realistic lattice: an X-band linac FODO
cell, built directly from RF_Track's native API
(one FODO period: D0, C1, C2, QF, C3, C4, QD; analytic
Pillbox cavities, no field maps, autophase off, space charge off, so this has
no external data-file dependency).

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

_FIELDS = "%x %xp %y %yp %t %P"

_MODEL = None


def test_quad_gradients_set():
    import numpy
    from pykern import pkunit

    m = _model()
    fodo = m.simulator.tracked_bunch.get_phase_space(_FIELDS)
    m.set({"QF_gradient": 0.0, "QD_gradient": 0.0})
    actual = m.simulator.tracked_bunch.get_phase_space(_FIELDS)
    numpy.testing.assert_array_equal(
        actual,
        _changed(
            lambda s: (
                s.find_element("QF").set_gradient(0.0),
                s.find_element("QD").set_gradient(0.0),
            )
        ),
    )
    pkunit.pkok(not numpy.array_equal(fodo, actual), "quadrupoles had no effect")


def test_cavity_phase_set():
    import numpy
    from pykern import pkunit

    m = _model()
    default = m.simulator.tracked_bunch.get_phase_space(_FIELDS)
    m.set({"C1_phid": 90.0})
    actual = m.simulator.tracked_bunch.get_phase_space(_FIELDS)
    numpy.testing.assert_array_equal(
        actual, _changed(lambda s: s.find_element("C1").set_phid(90.0))
    )
    pkunit.pkok(not numpy.array_equal(default, actual), "C1's phase had no effect")


def test_reset_restores_fodo_focusing():
    from pykern import pkunit

    m = _model()
    m.set({"QF_gradient": 5.0, "QD_gradient": -5.0})
    sigma_x_fodo = m.simulator.tracked_bunch.get_phase_space("%x").std()

    m.set({"QF_gradient": 0.0, "QD_gradient": 0.0})
    m.reset()

    pkunit.pkeq(5.0, m.get("QF_gradient"))
    pkunit.pkeq(-5.0, m.get("QD_gradient"))
    pkunit.pkeq(sigma_x_fodo, m.simulator.tracked_bunch.get_phase_space("%x").std())


def _build_model():
    from rslume.rftrack import LUMERFTrackModel
    from rslume.rftrack_actions import RFTrackWritableScalarVariable

    return LUMERFTrackModel(
        simulator=_simulator(),
        action_variables=[
            RFTrackWritableScalarVariable(
                name="QF_gradient",
                element_name="QF",
                attribute="gradient",
                default_value=5.0,
            ),
            RFTrackWritableScalarVariable(
                name="QD_gradient",
                element_name="QD",
                attribute="gradient",
                default_value=-5.0,
            ),
            RFTrackWritableScalarVariable(
                name="C1_phid",
                element_name="C1",
                attribute="phid",
                default_value=0.0,
            ),
        ],
    )


def _changed(change):
    """A fresh simulator's tracked phase space after `change(simulator)`,
    made the way the model makes it: track once with the defaults (which
    autophases the cavities), change the elements directly, track again."""
    s = _simulator()
    s.track()
    change(s)
    s.track()
    return s.tracked_bunch.get_phase_space(_FIELDS)


def _model():
    """One model shared by every test here, reset to its defaults first.
    Building the first Pillbox_Cavity in a process takes seconds, and
    RF-Track redoes that work whenever no cavity is left alive, so a model
    per test would pay it every time."""
    global _MODEL
    if _MODEL is None:
        _MODEL = _build_model()
    _MODEL.reset()
    return _MODEL


def _simulator():
    import RF_Track as rft
    import rftrack_util
    from rslume.rftrack_simulator import RFTrackSimulator

    return RFTrackSimulator(
        rftrack_util.x_band_fodo_lattice(rft),
        rftrack_util.twiss_bunch(rft, 100.0, 100, emitt=5.0),
    )
