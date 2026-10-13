#!/usr/bin/env python
"""Generated Python source for the AWA Zone 1 sim, used as the physics
source `Zone1Model` builds from. Its trailing auto-run `main()` call is
removed: `main()` itself is kept but never called (see zone_model.py's
loader).
"""

from pykern.pkcollections import PKDict
import RF_Track as rft
import numpy
from rslume.rftrack import LUMERFTrackModel
from rslume.rftrack_actions import (
    RFTrackWritableScalarVariable,
    RFTrackWritableVectorComponentVariable,
)
from rslume.rftrack_simulator import RFTrackSimulator
from rslume.rftrack_units import UNITS

ELEMENTS = [
    PKDict(
        name="Gun",
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
        kind="cavity_fieldmap",
        file="CAVITY-fieldMapFile.rf_gunG4.dat",
        rescale_mode="peak",
        target_field=80000000.0,
        frequency_hz=1300000000,
        phase_deg=0.0,
    ),
    PKDict(
        name="SolBF",
        elemedge=-0.5,
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
        kind="solenoid_fieldmap",
        file="SOLENOID-fieldMapFile.sol_bucking-focusing_pm550A.dat",
        rescale_mode="factor",
        scale_factor=0.0001,
    ),
    PKDict(
        name="SolM",
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
        kind="solenoid_fieldmap",
        file="SOLENOID-fieldMapFile.sol_matching_m440A.dat",
        rescale_mode="factor",
        scale_factor=0.0001,
    ),
    PKDict(
        name="DT1",
        elemedge=0.701802,
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
        l=0.0381,
        h_kick=0,
        v_kick=0,
    ),
    PKDict(
        name="L1",
        elemedge=0.576433,
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
        kind="cavity_fieldmap",
        file="CAVITY-fieldMapFile.linac.dat",
        rescale_mode="peak",
        target_field=22000000.0,
        frequency_hz=1300000000,
        phase_deg=0.0,
    ),
    PKDict(
        name="DT2",
        elemedge=1.63525,
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
        l=0.0381,
        h_kick=0,
        v_kick=0,
    ),
    PKDict(
        name="SolL1",
        elemedge=1.544,
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
        kind="solenoid_fieldmap",
        file="SOLENOID-fieldMapFile.sol_linacLB_500A.dat",
        rescale_mode="factor",
        scale_factor=2.0000000000000002e-07,
    ),
    PKDict(
        name="YAG1",
        elemedge=2.9,
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
        name="L2",
        elemedge=3.306433,
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
        kind="cavity_fieldmap",
        file="CAVITY-fieldMapFile.linac.dat",
        rescale_mode="peak",
        target_field=22000000.0,
        frequency_hz=1300000000,
        phase_deg=0.0,
    ),
    PKDict(
        name="DT3",
        elemedge=4.3053,
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
        l=0.0381,
        h_kick=0,
        v_kick=0,
    ),
    PKDict(
        name="SolL2",
        elemedge=4.12,
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
        kind="solenoid_fieldmap",
        file="SOLENOID-fieldMapFile.sol_linac_500A.dat",
        rescale_mode="factor",
        scale_factor=2e-07,
    ),
    PKDict(
        name="L3",
        elemedge=4.856433,
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
        kind="cavity_fieldmap",
        file="CAVITY-fieldMapFile.linac.dat",
        rescale_mode="peak",
        target_field=22000000.0,
        frequency_hz=1300000000,
        phase_deg=0.0,
    ),
    PKDict(
        name="YAG2",
        elemedge=6.292,
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
        name="SolL4",
        elemedge=5.881,
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
        kind="solenoid_fieldmap",
        file="SOLENOID-fieldMapFile.sol_linac_500A.dat",
        rescale_mode="factor",
        scale_factor=2e-07,
    ),
    PKDict(
        name="DT4",
        elemedge=5.84835,
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
        l=0.0381,
        h_kick=0,
        v_kick=0,
    ),
    PKDict(
        name="DT5",
        elemedge=7.0358,
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
        l=0.0381,
        h_kick=0,
        v_kick=0,
    ),
    PKDict(
        name="L4",
        elemedge=6.986433,
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
        kind="cavity_fieldmap",
        file="CAVITY-fieldMapFile.linac.dat",
        rescale_mode="peak",
        target_field=22000000.0,
        frequency_hz=1300000000,
        phase_deg=0.0,
    ),
    PKDict(
        name="L5",
        elemedge=8.326433,
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
        kind="cavity_fieldmap",
        file="CAVITY-fieldMapFile.linac.dat",
        rescale_mode="peak",
        target_field=22000000.0,
        frequency_hz=1300000000,
        phase_deg=0.0,
    ),
    PKDict(
        name="YAG3",
        elemedge=9.525,
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
        name="DT6",
        elemedge=9.7917,
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
        l=0.0381,
        h_kick=0,
        v_kick=0,
    ),
    PKDict(
        name="L6",
        elemedge=9.736433,
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
        kind="cavity_fieldmap",
        file="CAVITY-fieldMapFile.linac.dat",
        rescale_mode="peak",
        target_field=22000000.0,
        frequency_hz=1300000000,
        phase_deg=0.0,
    ),
    PKDict(
        name="DT7",
        elemedge=11.120374,
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
        name="YAG4",
        elemedge=11.372,
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
PHASE_SPACE_FIELDS = "%X %xp %Y %yp %Z %t0 %Px %Py %Pz %P %E %K"
# Volume.get_bunch_at_screens() always returns Bunch6d-typed bunches, even
# when the tracked bunch is a Bunch6dT (cathode distribution), so the token
# string for screen-captured bunches can differ from the one above.
PHASE_SPACE_FIELDS_SCREEN = "%X %xp %Y %yp %Z %dt %Px %Py %Pz %P %E %K"
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
    pc_mev=100,
    random_seed=5489,
    c_sig_t=3,
    c_sig_x=3,
    c_sig_y=3,
    cathode=True,
    dist_pz="fd_300",
    dist_x="r",
    dist_y="g",
    dist_z="plateau",
    e_photon=4.73,
    lt=0.006,
    noise_reduc=True,
    np=10000,
    phi_eff=3.5,
    q_total_nc=1,
    ref_clock=0,
    ref_ekin=0,
    ref_zpos=0,
    rt=0.0003,
    sig_x=1.67,
    species="electrons",
)
SETTINGS = PKDict(
    num_threads=12,
    space_charge=PKDict(
        dt_mm=3,
        grid=(
            8,
            8,
            16,
        ),
        mirror_m=0,
        smooth=0.5,
    ),
    tracking_range_m=(
        0,
        11.372,
    ),
    volume_dt_mm=0.5,
    volume_tt_dt_mm=10.0,
)

STAT_FIELDS = "%mean_Z %beta_x %beta_y %alpha_x %alpha_y %emitt_x %emitt_y %emitt_4d %beta_z %alpha_z %emitt_z %sigma_X %sigma_Y %sigma_Z %sigma_Pz %sigma_E %disp_x %disp_y %disp_px %disp_py %mean_X %mean_Y %mean_Px %mean_Py %mean_K %mean_E %mean_P %rmax %rmax90 %rmax99 %rmax99.9 %N"
STAT_SCALE = numpy.array(
    [
        0.001,
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


def apply_space_charge(volume):
    sc_settings = SETTINGS.space_charge
    volume.sc_dt_mm = sc_settings.dt_mm
    sc = rft.SpaceCharge_PIC_FreeSpace(*sc_settings.grid)
    sc.set_smooth(sc_settings.smooth)
    sc.set_mirror(sc_settings.mirror_m)
    # rft.cvar.SC_engine (a process-global) rather than
    # Volume.set_sc_engine(): the latter does not apply space-charge
    # forces the same way for a multi-element Volume.
    rft.cvar.SC_engine = sc


def autophase(volume):
    # Autophase against a single on-axis reference particle, then track
    # the real bunch through this SAME (now-phased) volume; do not
    # rebuild it. Volume.autophase() sets each RF element's internal t0
    # directly and .track() uses that state as-is -- get_phid() does not
    # reflect it (it always reads back the phid the element was
    # constructed with), so reading it back to "convert" t0 into an
    # equivalent phid for a rebuilt volume silently produces the unphased
    # result instead of the true autophased state.
    # A Cathode or From File reference particle starts at rest
    # (X,Px,Y,Py,Z,Pz all 0), not at the design momentum, since both are
    # snapshots of a bunch that begins from (near) rest, not an
    # already-accelerated analytic (Twiss) distribution.
    p0 = rft.Bunch6dT(
        numpy.array(
            [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, BUNCH.mass_mev, BUNCH.charge, 1.0, 0.0]]
        )
    )
    volume.unset_t0()
    volume.autophase(p0)


def build_beamline():
    # Volume (rather than Lattice) supports elements at explicit, possibly
    # overlapping absolute z positions -- e.g. a gun cavity's E field and
    # a bucking/focusing solenoid's B field genuinely occupy the same
    # physical space in a real photoinjector.
    v = rft.Volume()
    for spec in ELEMENTS:
        v.add(
            _build_element(spec),
            spec.dx,
            spec.dy,
            spec.elemedge + spec.dz,
            spec.rz,
            spec.rx,
            spec.ry,
        )
    v.set_s0(SETTINGS.tracking_range_m[0])
    v.set_s1(SETTINGS.tracking_range_m[1])
    v.odeint_algorithm = "rkf45"
    v.dt_mm = SETTINGS.volume_dt_mm
    v.tt_dt_mm = SETTINGS.volume_tt_dt_mm
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
    # Cathode emission: particles start essentially at rest and are
    # generated directly from the photocathode's laser/emission model,
    # rather than from an already-moving analytic (Twiss) distribution.
    g = rft.Bunch6dT_Generator()
    g.species = BUNCH.species
    g.cathode = BUNCH.cathode
    g.noise_reduc = BUNCH.noise_reduc
    g.q_total = BUNCH.q_total_nc
    g.ref_ekin = BUNCH.ref_ekin
    g.ref_zpos = BUNCH.ref_zpos
    g.ref_clock = BUNCH.ref_clock
    g.phi_eff = BUNCH.phi_eff
    g.e_photon = BUNCH.e_photon
    g.dist_x = BUNCH.dist_x
    g.dist_y = BUNCH.dist_y
    g.sig_x = BUNCH.sig_x
    g.dist_z = BUNCH.dist_z
    g.rt = BUNCH.rt
    g.lt = BUNCH.lt
    g.c_sig_x = BUNCH.c_sig_x
    g.c_sig_y = BUNCH.c_sig_y
    g.c_sig_t = BUNCH.c_sig_t
    g.dist_pz = BUNCH.dist_pz
    return rft.Bunch6dT(g, BUNCH.np)


def main():
    rft.rng_set_seed(BUNCH.random_seed)
    rft.cvar.number_of_threads = SETTINGS.num_threads

    bunch = build_bunch()
    save_particles("initial_particles.npy", bunch, PHASE_SPACE_FIELDS)

    volume = build_beamline()
    autophase(volume)
    apply_space_charge(volume)

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


