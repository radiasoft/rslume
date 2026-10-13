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
from rslume.rftrack import LUMERFTrackModel
from rslume.rftrack_actions import (
    RFTrackWritableScalarVariable,
    RFTrackWritableVectorComponentVariable,
)
from rslume.rftrack_simulator import RFTrackSimulator
from rslume.rftrack_units import UNITS

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
PHASE_SPACE_FIELDS = "%x %xp %y %yp %Z %t %Px %Py %Pz %P %E %K"
# Volume.get_bunch_at_screens() always returns Bunch6d-typed bunches, even
# when the tracked bunch is a Bunch6dT (cathode distribution), so the token
# string for screen-captured bunches can differ from the one above.
PHASE_SPACE_FIELDS_SCREEN = "%x %xp %y %yp %Z %t %Px %Py %Pz %P %E %K"
# RF_Track's native phase-space units are mm, mrad, and MeV/c; rescale to
# base SI units (m, rad, eV/c, eV, s) to match impact-t's convention.
PHASE_SPACE_SCALE = numpy.array(
    [
        0.001,
        0.001,
        0.001,
        0.001,
        0.001,
        3.3356409519815207e-12,
        1000000.0,
        1000000.0,
        1000000.0,
        1000000.0,
        1000000.0,
        1000000.0,
    ]
)

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

STAT_FIELDS = "%S %beta_x %beta_y %alpha_x %alpha_y %emitt_x %emitt_y %emitt_4d %beta_z %alpha_z %emitt_z %sigma_x %sigma_y %sigma_t %sigma_pt %sigma_E %disp_x %disp_y %disp_px %disp_py %mean_x %mean_y %mean_Px %mean_Py %mean_K %mean_E %mean_P %rmax %rmax90 %rmax99 %rmax99.9 %N"
STAT_SCALE = numpy.array(
    [
        1,
        1,
        1,
        1,
        1,
        1e-06,
        1e-06,
        1e-06,
        1,
        1,
        1e-06,
        0.001,
        0.001,
        0.001,
        1000000.0,
        1000000.0,
        1,
        1,
        1,
        1,
        0.001,
        0.001,
        1000000.0,
        1000000.0,
        1000000.0,
        1000000.0,
        1000000.0,
        0.001,
        0.001,
        0.001,
        0.001,
        1,
        1,
        1,
    ]
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


def build_model(volume, bunch):
    """`volume`/`bunch` wrapped as a `rslume.rftrack.LUMERFTrackModel`, with one
    writable action variable per adjustable ELEMENTS entry -- only
    attributes a real control system could plausibly set (e.g. a
    solenoid's current), never a field-map file name. Each variable's
    default_value is read directly off the element `_build_element()`
    just constructed (RF_Track's own live get_X(), not a separate
    ELEMENTS field), since that element is the single source of truth
    for its own attributes regardless of which ELEMENTS fields happened
    to build it.

    Per-kind mapping, each confirmed directly against RF_Track's own
    live API (not assumed):
    - quadrupole_gradient: gradient, plain.
    - quadrupole_k1: strength (= K1 directly; plain and
      reference-momentum-independent, unlike get_K1(P_Q)).
    - solenoid_analytic: max_current, plain.
    - rbend: angle, plain.
    - cavity_analytic/cavity_fieldmap/cavity_fieldmap_2d: phid (phase)
      -- Pillbox_Cavity's field amplitude is baked in at construction,
      no live setter exists, so cavity_analytic gets no second variable.
    - cavity_fieldmap/cavity_fieldmap_2d also get P_actual (RF
      power/amplitude scale) -- plain on RF_FieldMap_1d/RF_FieldMap_2d,
      unlike Pillbox_Cavity.
    - corrector: strength is a 2-vector ([hkick, vkick]), so this uses
      RFTrackWritableVectorComponentVariable (one per axis) instead of
      the plain scalar variable every other kind uses.
    - solenoid_fieldmap: skipped -- Static_Magnetic_FieldMap_1d has no
      live scale attribute at all, and replace_with() (which could
      otherwise swap in a freshly-rescaled instance) silently no-ops for
      Volume-placed elements. The only way to make it live-settable is a
      full build_beamline() rebuild, not a per-element mutation like
      every other row here -- deliberately out of scope for now.
    - drift/screen/bpm: never control-room knobs.
    """
    simulator = RFTrackSimulator(volume, bunch)
    variables = []
    for spec in ELEMENTS:
        e = simulator.find_element(spec.name)
        if spec.kind == "quadrupole_gradient":
            variables.append(
                RFTrackWritableScalarVariable(
                    name=f"{spec.name}_gradient",
                    element_name=spec.name,
                    attribute="gradient",
                    default_value=e.get_gradient(),
                    unit=UNITS["gradient"],
                )
            )
        elif spec.kind == "quadrupole_k1":
            variables.append(
                RFTrackWritableScalarVariable(
                    name=f"{spec.name}_k1",
                    element_name=spec.name,
                    attribute="strength",
                    default_value=e.get_strength(),
                    unit=UNITS["k1"],
                )
            )
        elif spec.kind == "solenoid_analytic":
            variables.append(
                RFTrackWritableScalarVariable(
                    name=f"{spec.name}_max_current",
                    element_name=spec.name,
                    attribute="max_current",
                    default_value=e.get_max_current(),
                    unit=UNITS["max_current"],
                )
            )
        elif spec.kind == "rbend":
            variables.append(
                RFTrackWritableScalarVariable(
                    name=f"{spec.name}_angle",
                    element_name=spec.name,
                    attribute="angle",
                    default_value=e.get_angle(),
                    unit=UNITS["angle"],
                )
            )
        elif spec.kind == "corrector":
            hkick, vkick = e.get_strength()
            variables.append(
                RFTrackWritableVectorComponentVariable(
                    name=f"{spec.name}_hkick",
                    element_name=spec.name,
                    attribute="strength",
                    index=0,
                    default_value=float(hkick),
                    unit=UNITS["hkick"],
                )
            )
            variables.append(
                RFTrackWritableVectorComponentVariable(
                    name=f"{spec.name}_vkick",
                    element_name=spec.name,
                    attribute="strength",
                    index=1,
                    default_value=float(vkick),
                    unit=UNITS["vkick"],
                )
            )
        elif spec.kind in ("cavity_analytic", "cavity_fieldmap", "cavity_fieldmap_2d"):
            variables.append(
                RFTrackWritableScalarVariable(
                    name=f"{spec.name}_phid",
                    element_name=spec.name,
                    attribute="phid",
                    default_value=e.get_phid(),
                    unit=UNITS["phid"],
                )
            )
            if spec.kind in ("cavity_fieldmap", "cavity_fieldmap_2d"):
                variables.append(
                    RFTrackWritableScalarVariable(
                        name=f"{spec.name}_p_actual",
                        element_name=spec.name,
                        attribute="P_actual",
                        default_value=e.get_P_actual(),
                        unit=UNITS["p_actual"],
                    )
                )
    return LUMERFTrackModel(simulator=simulator, action_variables=variables)


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
    save_particles("initial_particles.npy", bunch, PHASE_SPACE_FIELDS)

    volume = build_beamline()

    model = build_model(volume, bunch)
    model.reset()
    model.simulator.archive("archive-lume.h5")
    save_particles(
        "final_particles.npy", model.simulator.tracked_bunch, PHASE_SPACE_FIELDS
    )
    save_stats(model.simulator.beamline)
    save_screens(model.simulator.beamline)
    save_bpms(model.simulator.beamline)


def save_particles(filename, bunch, fields):
    numpy.save(filename, bunch.get_phase_space(fields) * PHASE_SPACE_SCALE)


def save_bpms(volume):
    # get_bpms()/get_nbpms() only exist on Lattice, not Volume -- BPM
    # readings aren't supported in Volume mode at all, so this is a
    # no-op there, same as it would be for a lattice with no BPMs
    if not hasattr(volume, "get_bpms") or volume.get_nbpms() == 0:
        return
    rows = []
    for bpm in volume.get_bpms():
        x, y, _ = bpm.get_reading()  # mm, mm, mm (z unused)
        rows.append([bpm.get_S(), x, y, bpm.get_total_charge()])
    numpy.save("bpms.npy", numpy.array(rows))


def save_screens(volume):
    for i, bunch in enumerate(volume.get_bunch_at_screens()):
        save_particles(f"screen-{i}.npy", bunch, PHASE_SPACE_FIELDS_SCREEN)


def save_stats(volume):
    t = numpy.array(volume.get_transport_table(STAT_FIELDS))
    # %sigma_pt (Lattice) is a RELATIVE momentum spread in permille
    # (matching this app's own beam.sigma_pt field), unlike %sigma_Pz
    # (Volume, an absolute momentum spread in MeV/c); dividing by 1000
    # and multiplying by %mean_P approximates that same absolute
    # quantity, verified empirically against Volume's own %sigma_Pz for
    # an equivalent beamline.
    t[:, 14] = t[:, 14] / 1000.0 * t[:, 26]
    # On-axis Ez/Bz: a direct field query (independent of the tracked
    # beam) at x=y=0 and t=0, sampled at the same s positions as the
    # transport table, so it can be selected as another y-axis column
    # alongside the beam statistics.
    volume.set_t0(0)
    e, b = volume.get_field(0.0, 0.0, t[:, 0], 0.0)
    volume.unset_t0()
    t = numpy.hstack([t, numpy.array(e)[:, 2:3], numpy.array(b)[:, 2:3]])
    numpy.save("stats.npy", t * STAT_SCALE)


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
        field, step, _ = _load_field_map(spec)
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
        field, step, length = _load_field_map(spec)
        e = rft.RF_FieldMap_1d(field, step, length, spec.frequency_hz, +1)
        e.set_phid(spec.phase_deg)
    elif spec.kind == "cavity_fieldmap_2d":
        Er, Ez, hr, hz = _load_field_map_2d(spec)
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


def _load_field_map(spec):
    t = numpy.loadtxt(spec.file)
    s = t[:, 0]
    step = (s.max() - s.min()) / (len(s) - 1)
    length = s.max() - s.min()
    field = t[:, 1]
    if spec.rescale_mode == "factor":
        field = field * spec.scale_factor
    else:
        field = field / numpy.max(numpy.abs(field)) * spec.target_field
    return field, step, length


def _load_field_map_2d(spec):
    # SUPERFISH-style: two `#`-commented header lines (numpy.loadtxt()
    # skips these on its own), then rows of Z [cm], R [cm], Ez [MV/m],
    # Er [MV/m], |E| [MV/m], H [A/m] -- not rescaled, unlike a 1D map
    t = numpy.loadtxt(spec.file)
    z = numpy.sort(numpy.unique(t[:, 0]))
    r = numpy.sort(numpy.unique(t[:, 1]))
    nz, nr = len(z), len(r)
    hz = (z[-1] - z[0]) / (nz - 1) / 100
    hr = (r[-1] - r[0]) / (nr - 1) / 100
    Ez = t[:, 2].reshape((nz, nr), order="F") * 1e6
    Er = t[:, 3].reshape((nz, nr), order="F") * 1e6
    return Er, Ez, hr, hz


