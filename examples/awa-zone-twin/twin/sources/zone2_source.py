#!/usr/bin/env python
"""Generated Python source for the AWA Zone 2 sim, used as the physics
source `Zone2Model` builds from. Its trailing auto-run `main()` call is
removed: `main()` itself is kept but never called (see zone_model.py's
loader). Its own BUNCH/distribution_file are unused by the twin -- zone1's tracked
output is injected as zone2's initial_particles instead.
"""

from pykern.pkcollections import PKDict
import RF_Track as rft
import numpy
import beamphysics
import rslume.rftrack
import rslume.rftrack_utils

ELEMENTS = [
    PKDict(
        name="D_YAG4_DT8",
        elemedge=0,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="drift",
        l=0.555448,
    ),
    PKDict(
        name="DT8",
        elemedge=0.555448,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="corrector",
        l=0.085852,
        h_kick=0,
        v_kick=0,
    ),
    PKDict(
        name="D_DT8_DQ1",
        elemedge=0.6413000000000001,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="drift",
        l=0.147574,
    ),
    PKDict(
        name="DQ1",
        elemedge=0.7888740000000001,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="quadrupole_k1",
        l=0.1016,
        k1=0,
    ),
    PKDict(
        name="D_DQ1_DQ2",
        elemedge=0.8904740000000001,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="drift",
        l=0.143,
    ),
    PKDict(
        name="DQ2",
        elemedge=1.033474,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="quadrupole_k1",
        l=0.1016,
        k1=0,
    ),
    PKDict(
        name="D_DQ2_DQ3",
        elemedge=1.135074,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="drift",
        l=0.2824,
    ),
    PKDict(
        name="DQ3",
        elemedge=1.417474,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="quadrupole_k1",
        l=0.1016,
        k1=0,
    ),
    PKDict(
        name="D_DQ3_DT9",
        elemedge=1.5190739999999998,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="drift",
        l=0.134974,
    ),
    PKDict(
        name="DT9",
        elemedge=1.6540479999999997,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="corrector",
        l=0.085852,
        h_kick=0,
        v_kick=0,
    ),
    PKDict(
        name="D_DT9_DT10",
        elemedge=1.7398999999999998,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="drift",
        l=0.142748,
    ),
    PKDict(
        name="DT10",
        elemedge=1.8826479999999999,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="corrector",
        l=0.085852,
        h_kick=0,
        v_kick=0,
    ),
    PKDict(
        name="D_DT10_DQ4",
        elemedge=1.9685,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="drift",
        l=0.123773,
    ),
    PKDict(
        name="DQ4",
        elemedge=2.092273,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="quadrupole_k1",
        l=0.168402,
        k1=3,
    ),
    PKDict(
        name="D_DQ4_DQ5",
        elemedge=2.260675,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="drift",
        l=0.094998,
    ),
    PKDict(
        name="DQ5",
        elemedge=2.355673,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="quadrupole_k1",
        l=0.168402,
        k1=0,
    ),
    PKDict(
        name="D_DQ5_DQ6",
        elemedge=2.524075,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="drift",
        l=0.085598,
    ),
    PKDict(
        name="DQ6",
        elemedge=2.609673,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="quadrupole_k1",
        l=0.168402,
        k1=0,
    ),
    PKDict(
        name="D_DQ6_DQ7",
        elemedge=2.778075,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="drift",
        l=0.104698,
    ),
    PKDict(
        name="DQ7",
        elemedge=2.882773,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="quadrupole_k1",
        l=0.168402,
        k1=-4,
    ),
    PKDict(
        name="D_DQ7_DT12",
        elemedge=3.0511749999999997,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="drift",
        l=1.638073,
    ),
    PKDict(
        name="DT12",
        elemedge=4.689247999999999,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="corrector",
        l=0.085852,
        h_kick=0,
        v_kick=0,
    ),
    PKDict(
        name="D_DT12_YAG5",
        elemedge=4.775099999999999,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="drift",
        l=0.293674,
    ),
    PKDict(
        name="YAG5",
        elemedge=5.0687739999999994,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="screen",
    ),
    PKDict(
        name="D_YAG5_DQ8",
        elemedge=5.0687739999999994,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="drift",
        l=0.1841,
    ),
    PKDict(
        name="DQ8",
        elemedge=5.252873999999999,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="quadrupole_k1",
        l=0.0762,
        k1=7,
    ),
    PKDict(
        name="D_DQ8_DQ9",
        elemedge=5.329073999999999,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="drift",
        l=0.2731,
    ),
    PKDict(
        name="DQ9",
        elemedge=5.602174,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="quadrupole_k1",
        l=0.0762,
        k1=3,
    ),
    PKDict(
        name="D_DQ9_ET2",
        elemedge=5.678374,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="drift",
        l=0.071374,
    ),
    PKDict(
        name="ET2",
        elemedge=5.749747999999999,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="corrector",
        l=0.085852,
        h_kick=0,
        v_kick=0,
    ),
    PKDict(
        name="D_ET2_DQ10",
        elemedge=5.8355999999999995,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="drift",
        l=0.074674,
    ),
    PKDict(
        name="DQ10",
        elemedge=5.910273999999999,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="quadrupole_k1",
        l=0.0762,
        k1=-8,
    ),
    PKDict(
        name="D_DQ10_YAG7",
        elemedge=5.986473999999999,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="drift",
        l=0.3904,
    ),
    PKDict(
        name="YAG7",
        elemedge=6.376873999999999,
        set_aperture=True,
        aperture_x=0.015,
        aperture_y=0.015,
        aperture_type="circular",
        dx=0,
        dy=0,
        dz=0,
        rx=0,
        ry=0,
        rz=0,
        kind="screen",
    ),
]
BUNCH = PKDict(
    charge=-1.0,
    mass_mev=0.51099895069,
    pc_mev=60,
    random_seed=5489,
    distribution_file="beam-distributionFile.awa_zone1_output.h5",
    from_file_z_offset=0.0,
)
SETTINGS = PKDict(
    num_threads=12,
    space_charge=PKDict(),
)


def build_beamline():
    # Lattice appends elements sequentially with no absolute-position
    # concept at all -- gaps were already filled with synthetic Drifts
    # and overlaps rejected when ELEMENTS was generated, so every element
    # here simply begins where the previous one ended. There is no
    # Volume-style tracking range to set (a Lattice is inherently bounded
    # by its own appended elements), and no continuous-ODE step size to
    # tune (dt_mm/odeint_algorithm/tt_dt_mm are Volume-only) -- each
    # element instead has its own default step count.
    v = rft.Lattice()
    elements = [_build_element(spec) for spec in ELEMENTS]
    for e in elements:
        # set_tt_nsteps() controls how finely get_transport_table()
        # samples within this element (the Lattice-only equivalent of
        # Volume's tt_dt_mm) -- without it, the transport table (and so
        # the Beam Variables/Lattice Overlay plots) only reports one
        # point per element.
        e.set_tt_nsteps(20)
        v.append(e)
    # Element.set_offsets(), called on an already-appended element,
    # silently has no effect (verified empirically) --
    # Lattice.set_elements_offsets() is the reliable, bulk equivalent of
    # Volume.add()'s per-element x/y/z/roll/pitch/yaw args (its extra 4th
    # column, always 1.0 here, is unrelated to any misalignment field).
    v.set_elements_offsets(
        numpy.array([[s.dx, s.dy, s.dz, 1.0, s.rz, s.rx, s.ry] for s in ELEMENTS])
    )
    # nonzero: RF_Track prints tracking progress (e.g. "t = ... mm/c")
    # straight to stdout as track() advances, which is run.log's own
    # content with no further plumbing needed
    v.verbosity = 1
    return v


def build_bunch():
    pg = beamphysics.ParticleGroup(h5=BUNCH.distribution_file)
    # Already-accelerated bunch (e.g. re-injecting a previous sim's own
    # tracked output downstream, matching how zone_2.ipynb loads zone_1's
    # own saved output via
    # preproc.load_bunch_from_openpmd(bunch_type="Bunch6d")): Pz dominates
    # here, so the small-angle approximation Bunch6d's x'/y' rely on is
    # valid -- and Bunch6d is the only bunch type Lattice.track() accepts
    # at all, so Sequential (Lattice) positioning requires this branch.
    # RF_Track's native units are mm, mrad, MeV/c, mm/c; ParticleGroup's
    # are already SI (m, eV/c, s, C).
    x = pg.x * 1e3
    y = pg.y * 1e3
    px = pg.px / 1e6
    py = pg.py / 1e6
    pz = pg.pz / 1e6
    t = pg.t * rft.clight * 1e3
    population = pg.charge * rft.C
    xp = numpy.divide(px, pz, out=numpy.zeros_like(px), where=(pz != 0)) * 1e3
    yp = numpy.divide(py, pz, out=numpy.zeros_like(py), where=(pz != 0)) * 1e3
    p = numpy.sqrt(px**2 + py**2 + pz**2)
    return rft.Bunch6d(
        BUNCH.mass_mev,
        population,
        BUNCH.charge,
        numpy.column_stack([x, xp, y, yp, t, p]),
    )


def main():
    rft.rng_set_seed(BUNCH.random_seed)
    rft.cvar.number_of_threads = SETTINGS.num_threads

    bunch = build_bunch()
    rslume.rftrack_utils.save_particles("initial_particles.npy", bunch)

    volume = build_beamline()

    model = rslume.rftrack.build_model(ELEMENTS, volume, bunch)
    model.reset()
    model.simulator.archive("archive-lume.h5")
    rslume.rftrack_utils.save_particles(
        "final_particles.npy", model.simulator.tracked_bunch
    )
    rslume.rftrack_utils.save_stats(model.simulator.beamline)
    rslume.rftrack_utils.save_screens(model.simulator.beamline, bunch)
    rslume.rftrack_utils.save_bpms(model.simulator.beamline)


def _build_element(spec):
    if spec.kind == "drift":
        e = rft.Drift(spec.l)
    elif spec.kind == "quadrupole_k1":
        e = rft.Quadrupole(spec.l, spec.k1)
    elif spec.kind == "quadrupole_gradient":
        e = rft.Quadrupole(spec.l, float("nan"), 0.0)
        e.set_gradient(spec.gradient)
    elif spec.kind == "rbend":
        e = rft.RBend(spec.l, spec.angle, BUNCH.pc_mev / BUNCH.charge)
    elif spec.kind == "solenoid_analytic":
        e = rft.Solenoid(spec.l, spec.b_field, spec.radius)
    elif spec.kind == "solenoid_fieldmap":
        field, step, _ = rslume.rftrack_utils.load_field_map(spec)
        e = rft.Static_Magnetic_FieldMap_1d(field, step)
    elif spec.kind == "corrector":
        e = rft.Corrector(spec.l, spec.h_kick, spec.v_kick)
    elif spec.kind == "cavity_analytic":
        l_cell = rft.clight / (2.0 * spec.frequency_hz)
        n_cells = max(1, round(spec.l / l_cell))
        a = numpy.zeros(1)
        a[-1] = spec.gradient_v_per_m
        e = rft.Pillbox_Cavity(a, spec.frequency_hz, l_cell, n_cells)
        e.set_phid(spec.phase_deg)
    elif spec.kind == "cavity_fieldmap":
        field, step, length = rslume.rftrack_utils.load_field_map(spec)
        e = rft.RF_FieldMap_1d(field, step, length, spec.frequency_hz, +1)
        e.set_phid(spec.phase_deg)
    elif spec.kind == "cavity_fieldmap_2d":
        Er, Ez, hr, hz = rslume.rftrack_utils.load_field_map_2d(spec)
        e = rft.RF_FieldMap_2d(Er, Ez, 0, 0, hr, hz, -1, spec.frequency_hz, +1)
        e.set_phid(spec.phase_deg)
    elif spec.kind == "screen":
        e = rft.Screen()
    elif spec.kind == "bpm":
        e = rft.Bpm(spec.l)
    else:
        raise AssertionError(f"unsupported element kind={spec.kind}")
    # Explicitly pin t0 to 0.0 on every cavity/screen: confirmed
    # empirically that Volume.track() internally re-autophases every RF
    # element (and every Screen) from scratch if ANY of them has
    # t0_is_set() False, regardless of phid, silently overriding an
    # explicitly-set phase with Autophase off.
    #
    # Only emitted when the autophase() function below WON'T run:
    # confirmed empirically that Volume.unset_t0() -- the first thing
    # that function does -- does NOT clear an element's t0 once set()
    # was ever called on it directly, even to 0.0. Pinning t0 here
    # unconditionally would silently defeat the real autophase() search
    # that follows, leaving every cavity stuck at 0.0 instead of a
    # freshly-derived value (confirmed: the whole beamline ends up
    # unphased, same failure mode as never phasing at all, just
    # disguised since t0_is_set() now reads True).
    if spec.kind in (
        "cavity_analytic",
        "cavity_fieldmap",
        "cavity_fieldmap_2d",
        "screen",
    ):
        e.set_t0(0.0)
    e.set_name(spec.name)
    if spec.set_aperture:
        e.set_aperture(spec.aperture_x, spec.aperture_y, spec.aperture_type)
    return e


