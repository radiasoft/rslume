"""RF-Track bunch <-> openPMD-beamphysics ParticleGroup conversions

Four bridge functions, one pair per RF-Track bunch type (`Bunch6d`,
`Bunch6dT`), each pair being exact inverses of each other. The two
pairs are not interchangeable: `Bunch6d` is a fixed-z-plane snapshot
(real `t`, `z` forced to 0), while `Bunch6dT` is a genuine time
snapshot (real `z`, with `t` the common snapshot time `%t` by default,
or each particle's creation time `t0` for an exact round trip) -- see
each function's own docstring.

:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

import beamphysics
import numpy
import scipy.constants

# mass [MeV/c^2], charge [e] -- deliberately just these three, the species
# every version of beamphysics (nee pmd_beamphysics) this wrapper has been
# tested against has recognized, even though newer releases know more
# (beamphysics.species.MASS_OF as of 0.16.1 also has H-/H2+/muon/
# antimuon). A ParticleGroup has no "other"/generic-ion species to fall
# back to regardless, so bunch6d_to_particlegroup() can only infer a
# species when the bunch's own mass/charge matches one of these.
_PARTICLEGROUP_SPECIES = {
    "electron": (
        scipy.constants.physical_constants["electron mass energy equivalent in MeV"][
            0
        ],
        -1,
    ),
    "positron": (
        scipy.constants.physical_constants["electron mass energy equivalent in MeV"][
            0
        ],
        1,
    ),
    "proton": (
        scipy.constants.physical_constants["proton mass energy equivalent in MeV"][0],
        1,
    ),
}


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


def _infer_particlegroup_species(mass_mev, charge_e):
    for name, (mass, charge) in _PARTICLEGROUP_SPECIES.items():
        if charge_e == charge and abs(mass_mev - mass) < 1e-6 * mass:
            return name
    raise ValueError(
        f"no ParticleGroup species matches mass={mass_mev} MeV/c^2,"
        f" charge={charge_e} e -- beamphysics only knows electron,"
        " positron, and proton"
    )
