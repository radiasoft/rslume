"""Tests for `twin/zone_model.py`: `Zone1Model.reset()`, independence of
separate `Zone1Model`s, and the zone1 -> zone2 handoff (charge, energy and
bunch length all survive it).

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

import sys

import pykern.pkio

_TWIN_DIR = pykern.pkio.py_path(__file__).dirpath().dirpath().join("twin")
_N_PARTICLES = 300
# Tests run single-threaded so they never take every core on a big machine.
_THREADS = 1
_SOLENOID = "SolBF_scale_factor"


def test_reset_restores_solenoid_scale_factor():
    sys.path.insert(0, str(_TWIN_DIR))
    import RF_Track as rft
    from pykern import pkunit
    from zone_model import Zone1Model

    rft.cvar.number_of_threads = _THREADS
    z = Zone1Model(n_particles=_N_PARTICLES)
    nominal = z.get([_SOLENOID])[_SOLENOID]
    z.set({_SOLENOID: nominal * 2})
    pkunit.pkeq(nominal * 2, z.get([_SOLENOID])[_SOLENOID])
    z.reset()
    pkunit.pkeq(nominal, z.get([_SOLENOID])[_SOLENOID])


def test_zone1_models_do_not_share_state():
    sys.path.insert(0, str(_TWIN_DIR))
    import RF_Track as rft
    from pykern import pkunit
    from zone_model import Zone1Model

    rft.cvar.number_of_threads = _THREADS
    a = Zone1Model(n_particles=_N_PARTICLES)
    nominal = a.get([_SOLENOID])[_SOLENOID]
    a.set({_SOLENOID: nominal * 2})
    pkunit.pkeq(
        nominal, Zone1Model(n_particles=_N_PARTICLES).get([_SOLENOID])[_SOLENOID]
    )


def test_handoff_keeps_charge_energy_and_bunch_length():
    sys.path.insert(0, str(_TWIN_DIR))
    import actions
    from pykern import pkunit
    from zone_model import build_chain

    chain = build_chain(n_particles=_N_PARTICLES, threads=_THREADS)
    zone1, zone2 = chain.lume_model_instances
    chain.set({})
    for n1, n2 in zip(
        actions.diagnostic_variables("zone1_"), actions.diagnostic_variables("zone2_")
    ):
        a = zone1.get([n1])[n1]
        b = zone2.get([n2])[n2]
        pkunit.pkok(
            abs(a - b) < 1e-3 * abs(a),
            "{} changed in handoff: zone1={} zone2={}",
            n2,
            a,
            b,
        )
    sigma_z = zone1.model.simulator.tracked_bunch.get_phase_space("%Z")[:, 0].std()
    sigma_t = zone2.model.simulator.initial_bunch.get_phase_space("%t")[:, 0].std()
    # zone1 is relativistic, so sigma_t [mm/c] ~ sigma_z [mm] / beta ~ sigma_z
    pkunit.pkok(
        abs(sigma_t - sigma_z) < 0.02 * sigma_z,
        "bunch length lost in handoff: sigma_t={} sigma_z={}",
        sigma_t,
        sigma_z,
    )
