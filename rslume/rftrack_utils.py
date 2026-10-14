"""RF-Track bunch <-> openPMD-beamphysics ParticleGroup conversions, plus
the field-map readers, result writers (`load_field_map*()`,
`save_*()`) and space-charge setup shared by RF-Track scripts

Four bridge functions, one pair per RF-Track bunch type (`Bunch6d`,
`Bunch6dT`), each pair being exact inverses of each other. The two
pairs are not interchangeable: `Bunch6d` is a fixed-z-plane snapshot
(real `t`, `z` forced to 0), while `Bunch6dT` is a genuine time
snapshot (real `z`, with `t` the common snapshot time `%t` by default,
or each particle's creation time `t0` for an exact round trip).

:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

import beamphysics
import numpy
import scipy.constants
from pykern.pkcollections import PKDict

# RF-Track's native phase-space units are mm, mrad, and MeV/c; saved
# particle files are rescaled to base SI units (m, rad, eV/c, eV, s) to
# match impact-t's convention. Columns: x, xp, y, yp, z, t, Px, Py, Pz, P,
# E, K (see `_BUNCH6D_FIELDS`).
PHASE_SPACE_SCALE = numpy.array(
    [
        1e-3,  # x: mm -> m
        1e-3,  # xp: mrad -> rad
        1e-3,  # y: mm -> m
        1e-3,  # yp: mrad -> rad
        1e-3,  # z: mm -> m
        1e-3 / scipy.constants.c,  # t: mm/c -> s
        1e6,  # Px: MeV/c -> eV/c
        1e6,  # Py: MeV/c -> eV/c
        1e6,  # Pz: MeV/c -> eV/c
        1e6,  # P: MeV/c -> eV/c
        1e6,  # E: MeV -> eV
        1e6,  # K: MeV -> eV
    ]
)

# %Z (uppercase) is the one token that behaves identically across Bunch6d
# and Bunch6dT, tracked or freshly generated, initial or screen-captured:
# lowercase %z is defined only for Bunch6d and is always exactly 0 there.
# %t is the absolute per-particle time; for a bunch built by one of
# RF-Track's own generators (e.g. Bunch6d_QR) it equals %dt, but %dt for a
# raw-matrix-constructed Bunch6d is relative to whichever particle happens
# to be first in the array, so %t is the safe one.
_BUNCH6D_FIELDS = "%x %xp %y %yp %Z %t %Px %Py %Pz %P %E %K"
# Bunch6dT uses different token names for the same quantities: uppercase
# %X/%Y for position (lowercase %x/%y are not defined), and %t0 rather than
# %t for the per-particle time.
_BUNCH6DT_FIELDS = "%X %xp %Y %yp %Z %t0 %Px %Py %Pz %P %E %K"
# Volume.get_bunch_at_screens() always returns Bunch6d-typed bunches, even
# when the tracked bunch was a Bunch6dT, so %t0 is not defined there; only
# %dt works.
_BUNCH6DT_SCREEN_FIELDS = "%X %xp %Y %yp %Z %dt %Px %Py %Pz %P %E %K"

# Volume.get_transport_table() column selector, and the matching scale
# (RF-Track's native units rescaled to base SI: m, rad, eV, eV/c) of the
# columns saved to `stats.npy` -- the transport table's, then the on-axis Ez
# and Bz `save_stats()` appends (already base SI, V/m and T). RF_Track's
# native units: beta/disp_x/disp_y in m already; emitt_* in mm.mrad;
# mean_Z, sigma_X/Y/Z, mean_X/Y, rmax* in mm; sigma_Pz in MeV/c;
# mean_Px/Py/mean_K/mean_E/mean_P/sigma_E in MeV or MeV/c; alpha_*, disp_p*,
# and N are dimensionless.
_STAT_FIELDS_VOLUME = (
    "%mean_Z %beta_x %beta_y %alpha_x %alpha_y %emitt_x %emitt_y %emitt_4d"
    " %beta_z %alpha_z %emitt_z %sigma_X %sigma_Y %sigma_Z %sigma_Pz %sigma_E"
    " %disp_x %disp_y %disp_px %disp_py %mean_X %mean_Y %mean_Px %mean_Py"
    " %mean_K %mean_E %mean_P %rmax %rmax90 %rmax99 %rmax99.9 %N"
)
# Lattice.get_transport_table() lacks %mean_Z/%sigma_X/%sigma_Y/%mean_X/
# %mean_Y (Volume-only tokens; "unknown identifier" otherwise) -- %S and
# the lowercase %mean_x/%mean_y/%sigma_x/%sigma_y are its equivalents.
# %sigma_Z (a length) has no Lattice equivalent at all; %sigma_t (a
# light-time, i.e. already a length in the same mm units once scaled) is
# the closest analog. %sigma_Pz (an absolute momentum spread) likewise has
# no equivalent -- %sigma_pt is a RELATIVE spread (dp/p), so `save_stats()`
# multiplies it by %mean_P to approximate the same absolute quantity.
_STAT_FIELDS_LATTICE = (
    "%S %beta_x %beta_y %alpha_x %alpha_y %emitt_x %emitt_y %emitt_4d"
    " %beta_z %alpha_z %emitt_z %sigma_x %sigma_y %sigma_t %sigma_pt %sigma_E"
    " %disp_x %disp_y %disp_px %disp_py %mean_x %mean_y %mean_Px %mean_Py"
    " %mean_K %mean_E %mean_P %rmax %rmax90 %rmax99 %rmax99.9 %N"
)
_STAT_SCALE_VOLUME = numpy.array(
    [
        1e-3,  # s (mean_Z): mm -> m
        1,  # beta_x: m
        1,  # beta_y: m
        1,  # alpha_x
        1,  # alpha_y
        1e-6,  # emitt_x: mm.mrad -> m.rad
        1e-6,  # emitt_y: mm.mrad -> m.rad
        1e-6,  # emitt_4d: mm.mrad -> m.rad (sqrt(emitt_x * emitt_y)-like scale)
        1,  # beta_z: m
        1,  # alpha_z
        1e-6,  # emitt_z: mm.mrad -> m.rad
        1e-3,  # sigma_x (sigma_X): mm -> m
        1e-3,  # sigma_y (sigma_Y): mm -> m
        1e-3,  # sigma_z (sigma_Z): mm -> m
        1e6,  # sigma_Pz: MeV/c -> eV/c
        1e6,  # sigma_E: MeV -> eV
        1,  # disp_x: m
        1,  # disp_y: m
        1,  # disp_px: rad
        1,  # disp_py: rad
        1e-3,  # mean_x (mean_X): mm -> m
        1e-3,  # mean_y (mean_Y): mm -> m
        1e6,  # mean_Px: MeV/c -> eV/c
        1e6,  # mean_Py: MeV/c -> eV/c
        1e6,  # mean_K: MeV -> eV
        1e6,  # mean_E: MeV -> eV
        1e6,  # mean_P: MeV/c -> eV/c
        1e-3,  # rmax: mm -> m
        1e-3,  # rmax90: mm -> m
        1e-3,  # rmax99: mm -> m
        1e-3,  # rmax99.9: mm -> m
        1,  # N
        1,  # Ez: V/m
        1,  # Bz: T
    ]
)
# %S (Lattice's position token) is already in meters -- verified empirically
# against Volume's %mean_Z (raw millimeters) for the same physical length --
# unlike every other position/size quantity (%mean_x, %sigma_x, %sigma_t,
# rmax*, ...), which stays in the same raw millimeters in both Lattice and
# Volume. So only the first ("s") entry differs from _STAT_SCALE_VOLUME.
_STAT_SCALE_LATTICE = numpy.concatenate([[1], _STAT_SCALE_VOLUME[1:]])

# mass [MeV/c^2], charge [e] -- deliberately just these three, the species
# every version of beamphysics (nee pmd_beamphysics) this wrapper has been
# tested against has recognized, even though newer releases know more
# (beamphysics.species.MASS_OF as of 0.16.1 also has H-/H2+/muon/
# antimuon). A ParticleGroup has no "other"/generic-ion species to fall
# back to regardless, so bunch6d_to_particlegroup() can only infer a
# species when the bunch's own mass/charge matches one of these.
_PARTICLEGROUP_SPECIES = {
    "electron": (
        scipy.constants.physical_constants["electron mass energy equivalent in MeV"][0],
        -1,
    ),
    "positron": (
        scipy.constants.physical_constants["electron mass energy equivalent in MeV"][0],
        1,
    ),
    "proton": (
        scipy.constants.physical_constants["proton mass energy equivalent in MeV"][0],
        1,
    ),
}


def apply_space_charge(beamline, settings):
    """Make RF-Track apply space charge, per `settings`, to `beamline`.

    Sets `rft.cvar.SC_engine`, a process-global: it affects every later
    track in this process, not only `beamline`'s. RF-Track has no way to
    report which engine is set, nor to unset one.

    Args:
        beamline (RF_Track.Lattice or RF_Track.Volume): what will be
            tracked
        settings (dict): `{"kind": "p2p"}`, or `{"kind": "pic", "dt_mm":
            float, "grid": (nx, ny, nz), "mirror_m": float, "smooth":
            float}` (what `RFTrackSimulator.space_charge` holds)

    Raises:
        ValueError: unknown `settings.kind`
    """
    import RF_Track as rft

    s = PKDict(settings)
    k = s.kind
    if k == "p2p":
        rft.cvar.SC_engine = rft.SpaceCharge_P2P()
    elif k == "pic":
        if isinstance(beamline, rft.Volume):
            beamline.sc_dt_mm = s.dt_mm
        sc = rft.SpaceCharge_PIC_FreeSpace(*[int(n) for n in s.grid])
        sc.set_smooth(float(s.smooth))
        sc.set_mirror(float(s.mirror_m))
        # rft.cvar.SC_engine rather than Volume.set_sc_engine(): the
        # latter does not apply space-charge forces the same way for a
        # multi-element Volume.
        rft.cvar.SC_engine = sc
    else:
        raise ValueError(f"unknown space charge kind={k!r}")


def bunch6d_to_particlegroup(bunch, species=None):
    """Convert an RF-Track bunch (anything with `get_phase_space()`, e.g.
    a `Bunch6d`) into an openPMD-beamphysics `ParticleGroup`.

    Treats `bunch` as a fixed-z-plane snapshot: its own `t` becomes the
    ParticleGroup's `t`, and every particle's `z` is set to 0 (the
    standard convention for this kind of snapshot -- same interpretation
    `particlegroup_to_bunch6d()` makes in reverse).

    Args:
        bunch: an RF-Track bunch object.
        species (str): overrides automatic inference from the bunch's
            own mass/charge (see `_infer_particlegroup_species`).

    Raises:
        ValueError: `species` isn't given and the bunch's mass/charge
            doesn't match beamphysics' only known species (electron,
            positron, proton).
    """
    m = bunch.get_phase_space("%x %y %t %Px %Py %Pz %m %Q %N %id")
    x_mm, y_mm, t_mm_c, px_mev, py_mev, pz_mev, mass_mev, q_e, n, pid = m.T
    if species is None:
        species = _infer_particlegroup_species(float(mass_mev[0]), float(q_e[0]))
    c = scipy.constants.c
    e_coulombs = scipy.constants.e
    return beamphysics.ParticleGroup(
        data=dict(
            x=x_mm / 1000.0,
            y=y_mm / 1000.0,
            z=numpy.zeros_like(x_mm),
            px=px_mev * 1e6,
            py=py_mev * 1e6,
            pz=pz_mev * 1e6,
            t=t_mm_c / (c * 1000.0),
            weight=n * numpy.abs(q_e) * e_coulombs,
            species=species,
            status=numpy.ones_like(x_mm, dtype=int),
            id=pid.astype(int),
        )
    )


def bunch6dt_to_particlegroup(bunch, species=None, snapshot_time=True):
    """Convert an RF-Track `Bunch6dT` (e.g. a Volume's tracked output)
    into a `ParticleGroup`, treating it as a genuine time snapshot: the
    bunch's own `Z` becomes the ParticleGroup's `z`, and the bunch's
    common time `%t` (the instant every `Z` is evaluated at) becomes
    every particle's `t` -- the opposite convention from
    `bunch6d_to_particlegroup()`'s fixed-z-plane snapshot.
    `particlegroup_to_bunch6d()` relies on this to drift the group to a
    plane, which is how a zone handoff keeps the bunch length.

    `snapshot_time=False` instead puts each particle's own creation
    (emission) time `t0` in `t` -- not the instant its `Z` is at, and
    `-inf` ("not set") for a bunch built from Twiss parameters. Only an
    exact `Bunch6dT` round trip wants that (`particlegroup_to_bunch6dt()`
    restores `t0` from `t`; `rslume.rftrack_archive` uses it so `-inf`
    survives).

    Args:
        bunch: an RF-Track `Bunch6dT`.
        species (str): overrides automatic inference from the bunch's
            own mass/charge.
        snapshot_time (bool): `t` is the bunch's common time `%t`
            (default); `False` uses each particle's creation time `t0`.

    Raises:
        ValueError: `species` isn't given and the bunch's mass/charge
            doesn't match beamphysics' only known species.
    """
    m = bunch.get_phase_space(
        "%X %Y %Z %Px %Py %Pz " + ("%t" if snapshot_time else "%t0") + " %m %Q %N %id"
    )
    x_mm, y_mm, z_mm, px_mev, py_mev, pz_mev, t_mm_c, mass_mev, q_e, n, pid = m.T
    if species is None:
        species = _infer_particlegroup_species(float(mass_mev[0]), float(q_e[0]))
    c = scipy.constants.c
    e_coulombs = scipy.constants.e
    return beamphysics.ParticleGroup(
        data=dict(
            x=x_mm / 1000.0,
            y=y_mm / 1000.0,
            z=z_mm / 1000.0,
            px=px_mev * 1e6,
            py=py_mev * 1e6,
            pz=pz_mev * 1e6,
            t=t_mm_c / (c * 1000.0),
            weight=n * numpy.abs(q_e) * e_coulombs,
            species=species,
            status=numpy.ones_like(x_mm, dtype=int),
            id=pid.astype(int),
        )
    )


def load_field_map(spec):
    """Read a two-column (s, field) text file into `(field, step, length)`,
    scaled per `spec` (a `PKDict` with `file` and `rescale_mode`, plus
    `scale_factor` for "factor" or `target_field` otherwise).
    """
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


def load_field_map_2d(spec):
    """Read a SUPERFISH-style 2D field map from `spec.file` into
    `(Er, Ez, hr, hz)`: two `#`-commented header lines (`numpy.loadtxt()`
    skips these on its own), then rows of Z [cm], R [cm], Ez [MV/m],
    Er [MV/m], |E| [MV/m], H [A/m]. Not rescaled, unlike a 1D map.
    """
    t = numpy.loadtxt(spec.file)
    z = numpy.sort(numpy.unique(t[:, 0]))
    r = numpy.sort(numpy.unique(t[:, 1]))
    nz, nr = len(z), len(r)
    hz = (z[-1] - z[0]) / (nz - 1) / 100
    hr = (r[-1] - r[0]) / (nr - 1) / 100
    Ez = t[:, 2].reshape((nz, nr), order="F") * 1e6
    Er = t[:, 3].reshape((nz, nr), order="F") * 1e6
    return Er, Ez, hr, hz


def particlegroup_to_bunch6d(pg):
    """Convert an openPMD-beamphysics `ParticleGroup` into an RF-Track
    `Bunch6d`, the exact inverse of `bunch6d_to_particlegroup()`.

    A `Bunch6d` is a fixed-z-plane snapshot, so a `ParticleGroup` with a
    longitudinal spread (a time snapshot, e.g. from
    `bunch6dt_to_particlegroup()`) is first
    drifted (on a copy) to its mean `z`: each particle's `t` then
    becomes its arrival time at that plane, which is how the bunch
    length survives the handoff. For a `ParticleGroup` that already has
    a single `z` (anything from `bunch6d_to_particlegroup()`) this is a
    no-op.
    """
    import RF_Track as rft

    pg = pg.copy()
    pg.drift_to_z()
    c = scipy.constants.c
    e_coulombs = scipy.constants.e
    charge_e = pg.species_charge / e_coulombs
    n = pg.weight / abs(pg.species_charge)
    mass_mev = pg.mass / 1e6
    pz = pg.pz
    matrix = numpy.column_stack(
        [
            pg.x * 1000.0,
            pg.px / pz * 1000.0,
            pg.y * 1000.0,
            pg.py / pz * 1000.0,
            pg.t * c * 1000.0,
            numpy.sqrt(pg.px**2 + pg.py**2 + pg.pz**2) / 1e6,
            numpy.full(len(pg.x), mass_mev),
            numpy.full(len(pg.x), charge_e),
            n,
            pg.id,
        ]
    )
    return rft.Bunch6d(matrix)


def particlegroup_to_bunch6dt(pg):
    """Convert a `ParticleGroup` into an RF-Track `Bunch6dT`, the exact
    inverse of `bunch6dt_to_particlegroup(..., snapshot_time=False)`:
    `pg.z` becomes `Z`, `pg.t` becomes the creation time `t0`.
    """
    import RF_Track as rft

    c = scipy.constants.c
    e_coulombs = scipy.constants.e
    charge_e = pg.species_charge / e_coulombs
    n = pg.weight / abs(pg.species_charge)
    mass_mev = pg.mass / 1e6
    matrix = numpy.column_stack(
        [
            pg.x * 1000.0,
            pg.px / 1e6,
            pg.y * 1000.0,
            pg.py / 1e6,
            pg.z * 1000.0,
            pg.pz / 1e6,
            numpy.full(len(pg.x), mass_mev),
            numpy.full(len(pg.x), charge_e),
            n,
            pg.t * c * 1000.0,
        ]
    )
    return rft.Bunch6dT(matrix)


def save_bpms(volume):
    """Write `bpms.npy` (rows of S, x, y, total charge) from `volume`'s BPMs.

    get_bpms()/get_nbpms() only exist on Lattice, not Volume -- BPM
    readings aren't supported in Volume mode at all, so this is a no-op
    there, same as it would be for a lattice with no BPMs.
    """
    if not hasattr(volume, "get_bpms") or volume.get_nbpms() == 0:
        return
    rows = []
    for bpm in volume.get_bpms():
        x, y, _ = bpm.get_reading()  # mm, mm, mm (z unused)
        rows.append([bpm.get_S(), x, y, bpm.get_total_charge()])
    numpy.save("bpms.npy", numpy.array(rows))


def save_particles(filename, bunch):
    """Write `bunch`'s phase space, in SI units (`PHASE_SPACE_SCALE`), to
    `filename`: columns x, xp, y, yp, z, t, Px, Py, Pz, P, E, K, with
    the RF-Track token string chosen by the bunch's type (`Bunch6d` or
    `Bunch6dT`).
    """
    import RF_Track as rft

    numpy.save(
        filename,
        bunch.get_phase_space(
            _BUNCH6DT_FIELDS if isinstance(bunch, rft.Bunch6dT) else _BUNCH6D_FIELDS
        )
        * PHASE_SPACE_SCALE,
    )


def save_screens(volume, initial_bunch):
    """Write each of `volume`'s screen bunches to `screen-<i>.npy`.

    `initial_bunch` is the bunch that was tracked: screen bunches are
    always `Bunch6d`, but a `Bunch6dT` one needs different tokens.
    """
    import RF_Track as rft

    f = (
        _BUNCH6DT_SCREEN_FIELDS
        if isinstance(initial_bunch, rft.Bunch6dT)
        else _BUNCH6D_FIELDS
    )
    for i, bunch in enumerate(volume.get_bunch_at_screens()):
        numpy.save(f"screen-{i}.npy", bunch.get_phase_space(f) * PHASE_SPACE_SCALE)


def save_stats(volume):
    """Write `stats.npy`: `volume`'s transport table, in SI units, plus the
    on-axis Ez and Bz at the same positions.

    `volume` is an `RF_Track.Volume` or `RF_Track.Lattice`; the transport
    table's tokens differ between the two, so this chooses by type.
    """
    import RF_Track as rft

    is_lattice = isinstance(volume, rft.Lattice)
    fields = _STAT_FIELDS_LATTICE if is_lattice else _STAT_FIELDS_VOLUME
    t = numpy.array(volume.get_transport_table(fields))
    if is_lattice:
        # %sigma_pt (Lattice) is a RELATIVE momentum spread in permille
        # (matching this app's own beam.sigma_pt field), unlike %sigma_Pz
        # (Volume, an absolute momentum spread in MeV/c); dividing by 1000
        # and multiplying by %mean_P approximates that same absolute
        # quantity, verified empirically against Volume's own %sigma_Pz for
        # an equivalent beamline.
        names = fields.split()
        i = names.index("%sigma_pt")
        t[:, i] = t[:, i] / 1000.0 * t[:, names.index("%mean_P")]
    # On-axis Ez/Bz: a direct field query (independent of the tracked
    # beam) at x=y=0 and t=0, sampled at the same s positions as the
    # transport table, so it can be selected as another y-axis column
    # alongside the beam statistics.
    volume.set_t0(0)
    e, b = volume.get_field(0.0, 0.0, t[:, 0], 0.0)
    volume.unset_t0()
    numpy.save(
        "stats.npy",
        numpy.hstack([t, numpy.array(e)[:, 2:3], numpy.array(b)[:, 2:3]])
        * (_STAT_SCALE_LATTICE if is_lattice else _STAT_SCALE_VOLUME),
    )


def _infer_particlegroup_species(mass_mev, charge_e):
    for name, (mass, charge) in _PARTICLEGROUP_SPECIES.items():
        if charge_e == charge and abs(mass_mev - mass) < 1e-6 * mass:
            return name
    raise ValueError(
        f"no ParticleGroup species matches mass={mass_mev} MeV/c^2,"
        f" charge={charge_e} e -- beamphysics only knows electron,"
        " positron, and proton"
    )
