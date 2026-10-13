"""rslume.rftrack test against a realistic lattice: an X-band linac FODO
cell, built directly from RF_Track's native API
(one FODO period: D0, C1, C2, QF, C3, C4, QD; analytic
Pillbox cavities, no field maps, autophase off, space charge off, so this has
no external data-file dependency).

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def _build_cavity(rft, name):
    import numpy

    # analytic cavities C1-C4, all identical: 11.9942 GHz, 80 MV/m,
    # length 0.15 m
    frequency_hz = 11994200000.0
    gradient_v_per_m = 80e6
    length = 0.15
    l_cell = rft.clight / (2.0 * frequency_hz)
    n_cells = max(1, round(length / l_cell))
    a = numpy.zeros(1)
    a[-1] = gradient_v_per_m
    e = rft.Pillbox_Cavity(a, frequency_hz, l_cell, n_cells)
    e.set_phid(0.0)  # the example's own default: autophase is off
    e.set_name(name)
    return e


def _build_lattice(rft):
    d0 = rft.Drift(0.05)
    d0.set_name("D0")

    qf = rft.Quadrupole(0.1, float("nan"), 0.0)
    qf.set_gradient(5.0)
    qf.set_name("QF")

    qd = rft.Quadrupole(0.1, float("nan"), 0.0)
    qd.set_gradient(-5.0)
    qd.set_name("QD")

    beamline = rft.Lattice()
    for e in (
        d0,
        _build_cavity(rft, "C1"),
        _build_cavity(rft, "C2"),
        qf,
        _build_cavity(rft, "C3"),
        _build_cavity(rft, "C4"),
        qd,
    ):
        beamline.append(e)
    return beamline


def _build_bunch(rft):
    # electron, pc=100 MeV/c, Twiss
    # distribution, beta_x=beta_y=1, emit_x=emit_y=5 mm.mrad normalized
    twiss = rft.Bunch6d_twiss()
    twiss.beta_x = 1.0
    twiss.beta_y = 1.0
    twiss.alpha_x = 0.0
    twiss.alpha_y = 0.0
    twiss.emitt_x = 5.0
    twiss.emitt_y = 5.0
    twiss.sigma_t = 1.0
    twiss.sigma_pt = 1.0
    return rft.Bunch6d_QR(0.51099895, 0.05 * rft.nC, -1, 100.0, twiss, 100)


def _build_model():
    import RF_Track as rft
    from rslume.rftrack import RfTrack
    from rslume.rftrack_actions import RfTrackWritableScalarVariable
    from rslume.rftrack_simulator import RfTrackSimulator

    simulator = RfTrackSimulator(_build_lattice(rft), _build_bunch(rft))
    variables = [
        RfTrackWritableScalarVariable(
            name="QF_gradient",
            element_name="QF",
            attribute="gradient",
            default_value=5.0,
        ),
        RfTrackWritableScalarVariable(
            name="QD_gradient",
            element_name="QD",
            attribute="gradient",
            default_value=-5.0,
        ),
        RfTrackWritableScalarVariable(
            name="C1_phid",
            element_name="C1",
            attribute="phid",
            default_value=0.0,
        ),
    ]
    return RfTrack(simulator=simulator, action_variables=variables)


_MODEL = None


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


def test_quad_gradient_changes_beam_size():
    from pykern import pkunit

    m = _model()
    m.set({"QF_gradient": 5.0, "QD_gradient": -5.0})
    sigma_x_fodo = m.simulator.tracked_bunch.get_phase_space("%x").std()

    # turn off focusing entirely -- just confirm the quads actually affect
    # the beam, not which direction (this single period isn't necessarily
    # matched to the example's initial beta_x=1, so "focusing -> smaller
    # beam" isn't a safe assumption over only one cell)
    m.set({"QF_gradient": 0.0, "QD_gradient": 0.0})
    sigma_x_no_focusing = m.simulator.tracked_bunch.get_phase_space("%x").std()

    pkunit.pkok(
        sigma_x_no_focusing != sigma_x_fodo,
        "expected quad gradient to affect beam size: fodo={} no_focusing={}",
        sigma_x_fodo,
        sigma_x_no_focusing,
    )


def test_cavity_phase_changes_energy_gain():
    from pykern import pkunit

    m = _model()
    initial_k = m.simulator.initial_bunch.get_phase_space("%K").mean()

    m.set({"C1_phid": 0.0})
    gain_on_crest_ish = (
        m.simulator.tracked_bunch.get_phase_space("%K").mean() - initial_k
    )

    m.set({"C1_phid": 90.0})
    gain_quadrature = (
        m.simulator.tracked_bunch.get_phase_space("%K").mean() - initial_k
    )

    pkunit.pkok(
        gain_on_crest_ish != gain_quadrature,
        "expected energy gain to depend on C1's phase: on_crest_ish={}"
        " quadrature={}",
        gain_on_crest_ish,
        gain_quadrature,
    )


def test_reset_restores_fodo_focusing():
    from pykern import pkunit

    m = _model()
    m.set({"QF_gradient": 5.0, "QD_gradient": -5.0})
    sigma_x_fodo = m.simulator.tracked_bunch.get_phase_space("%x").std()

    m.set({"QF_gradient": 0.0, "QD_gradient": 0.0})
    m.reset()

    pkunit.pkeq(5.0, m.get("QF_gradient"))
    pkunit.pkeq(-5.0, m.get("QD_gradient"))
    pkunit.pkeq(
        sigma_x_fodo, m.simulator.tracked_bunch.get_phase_space("%x").std()
    )
