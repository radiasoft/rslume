"""HDF5 archive format for rslume.rftrack

`RFTrackSimulator.archive()`/`load_archive()` (`rslume.rftrack_simulator`)
delegate to :func:`archive`/:func:`load_archive` here, and
:func:`read_archive` reads an archive without RF-Track (e.g. for another
program to import it). This module holds the actual beamline + bunch <->
HDF5 serialization, covering only the
element classes that have a `_serialize_<class>()` function -- not a
bespoke format of its own, just RF-Track's own native class/attribute
names, written as plain, self-describing HDF5 any tool can read.

:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

import beamphysics
import h5py
import numpy
import pykern.pkinspect
from beamphysics.units import pmd_unit, write_unit_h5
from pykern.pkcollections import PKDict
from rslume.rftrack_units import UNITS
from rslume.rftrack_utils import (
    bunch6d_to_particlegroup,
    bunch6dt_to_particlegroup,
    particlegroup_to_bunch6d,
    particlegroup_to_bunch6dt,
)

_CAVITY_CLASSES = frozenset(("Pillbox_Cavity", "RF_FieldMap_1d", "RF_FieldMap_2d"))

# Volume tracking settings archive() records and load_archive() restores
_VOLUME_INTEGRATOR_ATTRS = (
    "dt_mm",
    "odeint_algorithm",
    "odeint_epsabs",
    "odeint_epsrel",
    "t_max_mm",
    "tt_dt_mm",
)


def archive(simulator, path, autophase=None, space_charge=None):
    """Write `simulator.beamline` and `simulator.initial_bunch` to `path`
    as HDF5 (called as `RFTrackSimulator.archive()`).

    `path` is also a valid standalone openPMD particle file (readable
    with `beamphysics.ParticleGroup(h5=path)`). The bunch comes back as
    the same macroparticles, not a new realization; the random seed is
    not recorded. Each element's aperture and step counts, a Lattice's
    element offsets and a Volume's integrator settings are recorded too,
    and an autophased RF element keeps its phase correction, so a
    reloaded beamline tracks identically without calling `autophase()`
    again. Space charge is recorded as settings only: after loading, call
    `RFTrackSimulator.apply_space_charge()` to use it.

    Args:
        simulator (RFTrackSimulator): the `Lattice` or `Volume` and the
            `Bunch6d` or `Bunch6dT` to write
        path (str): file to write
        autophase (bool): whether autophase was used; `None` infers it
            from the cavities' `t0` [None]
        space_charge (dict): `{"kind": "p2p"}` or `{"kind": "pic",
            "dt_mm": float, "grid": (nx, ny, nz), "mirror_m": float,
            "smooth": float}`; `None` uses `simulator.space_charge`
            [None]. RF-Track cannot report its active space-charge
            engine, so this cannot be inferred. To archive a loaded
            simulator without space charge, set
            `simulator.space_charge = None` first.

    Raises:
        NotImplementedError: an element class with no serializer, or a
            Volume element with a non-identity rotation

    The file is plain HDF5, readable without this module:

    - root attrs: `software`, `bunch_type`, `beamline_class`,
      `autophase`, and for a Volume `s0`/`s1` and its integrator settings
      (`dt_mm`, `tt_dt_mm`, `odeint_algorithm`, `odeint_epsabs`,
      `odeint_epsrel`, `t_max_mm`)
    - `elements_offsets`: for a Lattice, one row per element, as
      `Lattice.set_elements_offsets()` takes them
    - `elements/<i>`: one group per element, using RF-Track's own
      class and attribute names
    - `field_maps`: each unique array-valued field once, keyed by md5
      and referenced from an element as `"@<md5>"`
    - `space_charge`: the settings above, if any
    - `units`: the unit of each element field
    - `particles`: the bunch, as openPMD
    """
    kind = type(simulator.beamline).__name__
    elements, field_maps = _dedupe_field_maps(
        [
            _element_to_attrs(simulator.beamline[i], kind)
            for i in range(simulator.beamline.size())
        ]
    )
    particle_group, bunch_type = _bunch_to_particlegroup(simulator.initial_bunch)
    if autophase is None:
        autophase = _infer_autophase(elements)
    if space_charge is None:
        space_charge = simulator.space_charge
    if space_charge is not None:
        space_charge = PKDict(space_charge)
    with h5py.File(path, "w") as f:
        # no dataType attr of our own: ParticleGroup.write() sets (and
        # would overwrite) openPMD's
        f.attrs["software"] = "rslume"
        f.attrs["bunch_type"] = bunch_type
        f.attrs["beamline_class"] = kind
        f.attrs["autophase"] = int(autophase)
        if space_charge is not None:
            sc = f.create_group("space_charge")
            sc.attrs["kind"] = space_charge.kind
            if space_charge.kind == "pic":
                sc.attrs["dt_mm"] = float(space_charge.dt_mm)
                sc.attrs["grid"] = numpy.asarray(space_charge.grid, dtype=int)
                sc.attrs["mirror_m"] = float(space_charge.mirror_m)
                sc.attrs["smooth"] = float(space_charge.smooth)
        if kind == "Volume":
            # get_s0()/get_s1() return a Frame (like an element's
            # get_offsets()), not a plain float -- its origin's z
            # component (in mm, same as get_offsets(), hence /1000) is
            # the tracking-range value set_s0()/set_s1() itself takes
            # (in meters).
            f.attrs["s0"] = (
                float(
                    numpy.asarray(simulator.beamline.get_s0().get_origin()).flatten()[2]
                )
                / 1000.0
            )
            f.attrs["s1"] = (
                float(
                    numpy.asarray(simulator.beamline.get_s1().get_origin()).flatten()[2]
                )
                / 1000.0
            )
            for k in _VOLUME_INTEGRATOR_ATTRS:
                f.attrs[k] = getattr(simulator.beamline, k)
        else:
            # one row per element, as Lattice.set_elements_offsets() takes it
            f.create_dataset(
                "elements_offsets",
                data=numpy.asarray(simulator.beamline.get_elements_offsets()),
            )
        _write_indexed_group(f, "elements", elements)
        if field_maps:
            fm = f.create_group("field_maps")
            for h, arr in field_maps.items():
                fm.create_dataset(h, data=arr)
        units_elements = f.create_group("units").create_group("elements")
        for i, element in enumerate(elements):
            _write_field_units_h5(units_elements.create_group(str(i)), element.keys())
        particle_group.write(f)


def load_archive(simulator, path):
    """Replace `simulator.beamline` and `simulator.initial_bunch` with the
    contents of `path` (as written by `archive()`; called as
    `RFTrackSimulator.load_archive()`), rebuilding a new `rft.Lattice`
    or `rft.Volume` and the exact same macroparticles `archive()`
    wrote. Clears `simulator.tracked_bunch`.

    Also sets `simulator.autophase`/`simulator.space_charge` from
    whatever `archive()` was given (`None` for either if it wasn't
    passed at archive time) -- purely informational, same as
    `simulator.beamline`/`simulator.initial_bunch`; this never acts on
    them itself (e.g. it doesn't call `autophase()` or build an
    `SC_engine`; call `simulator.apply_space_charge()` for that).
    """
    import RF_Track as rft

    a = read_archive(path)
    simulator.autophase = a.autophase
    simulator.space_charge = a.space_charge
    if a.beamline_class == "Lattice":
        beamline = rft.Lattice()
        for e in a.elements:
            beamline.append(_element_from_attrs(rft, e))
        beamline.set_elements_offsets(a.elements_offsets)
    elif a.beamline_class == "Volume":
        beamline = rft.Volume()
        for e in a.elements:
            beamline.add(
                _element_from_attrs(rft, e),
                float(e.x),
                float(e.y),
                float(e.z),
                0.0,
                0.0,
                0.0,
            )
        beamline.set_s0(a.s0)
        beamline.set_s1(a.s1)
        for k, v in a.integrator.items():
            setattr(beamline, k, v)
    else:
        raise NotImplementedError(
            f"don't know how to restore a beamline_class={a.beamline_class!r}"
        )
    simulator.beamline = beamline
    simulator.initial_bunch = _particlegroup_to_bunch(a.particle_group, a.bunch_type)
    simulator.tracked_bunch = None


def read_archive(path):
    """Read everything `archive()` wrote to `path`, without RF-Track.

    Returns:
        PKDict:
            autophase (bool): `None` if not recorded
            beamline_class (str): "Lattice" or "Volume"
            bunch_type (str): "Bunch6d" or "Bunch6dT"
            elements (list): one `PKDict` per element, keyed by RF-Track's
                class (`class`) and attribute names (see the
                `_serialize_*` functions), with field maps resolved to arrays
            elements_offsets (numpy.ndarray): a Lattice's element offsets,
                as `Lattice.set_elements_offsets()` takes them, else `None`
            integrator (PKDict): a Volume's `dt_mm`, `tt_dt_mm`,
                `odeint_algorithm`, `odeint_epsabs`, `odeint_epsrel` and
                `t_max_mm`, else `None`
            particle_group (beamphysics.ParticleGroup): the initial bunch
            s0 (float): a Volume's tracking start [m], else `None`
            s1 (float): a Volume's tracking end [m], else `None`
            space_charge (PKDict): see `archive()`, or `None`
    """
    with h5py.File(path, "r") as f:
        elements = _read_indexed_group(f, "elements")
        if "field_maps" in f:
            elements = _resolve_field_map_refs(elements, f["field_maps"])
        space_charge = None
        if "space_charge" in f:
            space_charge = PKDict(f["space_charge"].attrs)
            if "grid" in space_charge:
                space_charge.grid = tuple(int(n) for n in space_charge.grid)
        volume = str(f.attrs["beamline_class"]) == "Volume"
        return PKDict(
            autophase=bool(f.attrs["autophase"]) if "autophase" in f.attrs else None,
            beamline_class=str(f.attrs["beamline_class"]),
            bunch_type=str(f.attrs["bunch_type"]),
            elements=elements,
            elements_offsets=None if volume else f["elements_offsets"][()],
            integrator=(
                PKDict({k: _attr_value(f.attrs[k]) for k in _VOLUME_INTEGRATOR_ATTRS})
                if volume
                else None
            ),
            particle_group=beamphysics.ParticleGroup(h5=f),
            s0=float(f.attrs["s0"]) if "s0" in f.attrs else None,
            s1=float(f.attrs["s1"]) if "s1" in f.attrs else None,
            space_charge=space_charge,
        )


def _aperture_is_set(e):
    """Whether `set_aperture()` was ever called on `e`.

    RF-Track has no getter for that, so this compares with the class's
    own default: (-0.001, -0.001) for every archivable class except
    `Pillbox_Cavity`, whose default depends on its geometry, so it is
    compared with a freshly built cavity of the same geometry.
    """
    import RF_Track as rft

    a = (e.get_aperture_x(), e.get_aperture_y())
    if isinstance(e, rft.Pillbox_Cavity):
        r = rft.Pillbox_Cavity(
            numpy.zeros(1),
            e.get_frequency(),
            e.get_cell_length(),
            round(e.get_length() / e.get_cell_length()),
        )
        return a != (r.get_aperture_x(), r.get_aperture_y())
    return a != (-0.001, -0.001)


def _attr_value(v):
    """An HDF5 attr as a plain Python value: h5py returns numpy scalars."""
    if isinstance(v, bytes):
        return v.decode()
    return v.item() if isinstance(v, numpy.generic) else v


def _bunch_to_particlegroup(bunch):
    """Convert `bunch` (a Bunch6d or Bunch6dT) to a `ParticleGroup`,
    returning `(particle_group, bunch_type)`. `bunch_type` records
    which conversion was used -- `particlegroup_to_bunch6d()`/
    `particlegroup_to_bunch6dt()` are not interchangeable (opposite
    z/t conventions), and nothing about the
    resulting `ParticleGroup` itself says which one made it.
    """
    import RF_Track as rft

    if isinstance(bunch, rft.Bunch6dT):
        return bunch6dt_to_particlegroup(bunch, snapshot_time=False), "Bunch6dT"
    return bunch6d_to_particlegroup(bunch), "Bunch6d"


def _dedupe_field_maps(elements):
    """Replace any numpy-array-valued field in `elements` (e.g.
    RF_FieldMap_1d's "ez", Static_Magnetic_FieldMap_1d's "bz") with a
    short reference ("@<md5>") to one shared copy, keyed by the array's
    own content hash -- several elements built from the same uploaded
    field-map file (e.g. a linac's identical accelerating cavities) are
    otherwise archived with a byte-for-byte duplicate of the same array
    once per element.

    Returns:
        (list, dict): the deduped element dicts (shallow copies -- the
            originals are untouched), and `{md5: array}` for every
            unique array found, to write once under a shared top-level
            group (see `archive()`). A reference is plain text (goes in
            as a normal attr, same as any other string field), so this
            needs no changes to `_write_attrs_h5`/`_read_attrs_h5`.
    """
    import hashlib

    field_maps = {}
    deduped = []
    for e in elements:
        d = PKDict(e)
        for k, v in e.items():
            if isinstance(v, numpy.ndarray):
                h = hashlib.md5(v.tobytes()).hexdigest()
                field_maps[h] = v
                d[k] = f"@{h}"
        deduped.append(d)
    return deduped, field_maps


def _deserialize_bpm(rft, d):
    return rft.Bpm(float(d.length), float(d.resolution), float(d.resolution_t))


def _deserialize_corrector(rft, d):
    return rft.Corrector(float(d.length), float(d.kx), float(d.ky))


def _deserialize_drift(rft, d):
    return rft.Drift(float(d.length))


def _deserialize_pillbox_cavity(rft, d):
    e = rft.Pillbox_Cavity(
        numpy.array(d.coefficients, dtype=float),
        float(d.frequency),
        float(d.cell_length),
        float(d.n_cells),
    )
    e.set_phid(float(d.phid))
    return e


def _deserialize_quadrupole(rft, d):
    e = rft.Quadrupole(float(d.length), float("nan"), 0.0)
    e.set_gradient(float(d.gradient))
    return e


def _deserialize_rf_fieldmap_1d(rft, d):
    e = rft.RF_FieldMap_1d(
        numpy.asarray(d.ez),
        float(d.hz),
        float(d.length),
        float(d.frequency),
        float(d.direction),
        float(d.p_map),
        float(d.p_actual),
    )
    e.set_phid(float(d.phid))
    return e


def _deserialize_rf_fieldmap_2d(rft, d):
    e = rft.RF_FieldMap_2d(
        numpy.asarray(d.er),
        numpy.asarray(d.ez),
        0,
        0,
        float(d.hr),
        float(d.hz),
        -1,
        float(d.frequency),
        float(d.direction),
        float(d.p_map),
        float(d.p_actual),
    )
    e.set_phid(float(d.phid))
    return e


def _deserialize_screen(rft, d):
    e = rft.Screen()
    e.set_width(float(d.width))
    e.set_height(float(d.height))
    return e


def _deserialize_static_magnetic_fieldmap_1d(rft, d):
    return rft.Static_Magnetic_FieldMap_1d(numpy.asarray(d.bz), float(d.hz))


def _element_from_attrs(rft, d):
    cls = d["class"]
    f = getattr(pykern.pkinspect.this_module(), f"_deserialize_{cls.lower()}", None)
    if f is None:
        raise NotImplementedError(f"don't know how to restore a {cls!r} element yet")
    e = f(rft, d)
    e.set_name(str(d.name))
    if d.aperture_set:
        e.set_aperture(float(d.aperture_x), float(d.aperture_y), str(d.aperture_shape))
    e.set_nsteps(int(d.nsteps))
    e.set_sc_nsteps(int(d.sc_nsteps))
    e.set_tt_nsteps(int(d.tt_nsteps))
    if "t0" in d:
        e.set_t0(float(d.t0))
    return e


def _element_to_attrs(e, beamline_class="Lattice"):
    cls = type(e).__name__
    f = getattr(pykern.pkinspect.this_module(), f"_serialize_{cls.lower()}", None)
    if f is None:
        raise NotImplementedError(f"don't know how to archive a {cls!r} element yet")
    d = f(e)
    d["class"] = cls
    d.name = e.get_name()
    d.aperture_x = e.get_aperture_x()
    d.aperture_y = e.get_aperture_y()
    d.aperture_set = _aperture_is_set(e)
    d.aperture_shape = e.get_aperture_shape()
    d.nsteps = e.get_nsteps()
    d.sc_nsteps = e.get_sc_nsteps()
    d.tt_nsteps = e.get_tt_nsteps()
    if beamline_class == "Volume":
        d.update(_position_to_attrs(e))
    # Only Pillbox_Cavity/RF_FieldMap_1d/RF_FieldMap_2d/Screen have
    # t0_is_set()/get_t0() at all (confirmed empirically -- Drift,
    # Quadrupole, Corrector, Solenoid, Static_Magnetic_FieldMap_1d,
    # Bpm don't). get_phid() alone never reflects autophase(): it
    # "always reads back the phid the element was constructed with"
    # (confirmed empirically: get_phid() stays unchanged across
    # autophase()) -- t0 is the actual correction autophase() applies
    # and .track() uses as-is. Archiving it directly (confirmed
    # empirically: a fresh beamline with set_t0() from these captured
    # values, autophase() never called again, reproduces the
    # autophased beamline's own tracked mean kinetic energy exactly)
    # means load_archive() reproduces the real physics regardless of
    # whether the caller re-runs autophase() or even knows it was ever
    # used, rather than depending on that recomputation happening to
    # be reproducible.
    if hasattr(e, "t0_is_set") and e.t0_is_set():
        d.t0 = e.get_t0()
    return d


def _infer_autophase(elements):
    """Infer whether `autophase()` was used, from the already-serialized
    `elements` themselves, for `archive()`'s own `autophase=None` case.

    A cavity `autophase()`'d before archiving has a real, nonzero `t0`
    (see `_element_to_attrs()`'s own comment -- `get_phid()` never
    reflects it, `t0` does); one that was never autophased either has
    no `"t0"` key at all (`t0_is_set()` was `False`) or, if the caller
    deliberately pinned it to suppress a `Bunch6dT` beamline's own
    unwanted rescue autophase on `.track()`, exactly `0.0`. Either way,
    "any cavity with a nonzero `t0`" is the signal.
    """
    return any(
        d.get("class") in _CAVITY_CLASSES and d.get("t0", 0.0) != 0.0 for d in elements
    )


def _particlegroup_to_bunch(particle_group, bunch_type):
    """The exact inverse of `_bunch_to_particlegroup()`."""
    if bunch_type == "Bunch6dT":
        return particlegroup_to_bunch6dt(particle_group)
    return particlegroup_to_bunch6d(particle_group)


def _position_to_attrs(e):
    """Return `{x, y, z}` for a Volume-mode element's absolute placement.

    Raises:
        NotImplementedError: the element has a non-identity rotation --
            decoding RF-Track's (origin, nx, ny, nz) Frame back into the
            roll/pitch/yaw angles Volume.add() takes isn't implemented yet
            (every element archived so far happens to have no rotation,
            so this hasn't been needed, and guessing at the angle
            convention risks silently wrong physics).
    """
    fr = e.get_offsets()
    origin = numpy.asarray(fr.get_origin()).flatten()
    nx = numpy.asarray(fr.get_nx()).flatten()
    ny = numpy.asarray(fr.get_ny()).flatten()
    nz = numpy.asarray(fr.get_nz()).flatten()
    if not (
        numpy.allclose(nx, [1, 0, 0])
        and numpy.allclose(ny, [0, 1, 0])
        and numpy.allclose(nz, [0, 0, 1])
    ):
        raise NotImplementedError(
            "archiving a Volume element with a non-identity rotation isn't supported yet"
        )
    # Frame.get_origin() is in mm, confirmed empirically (e.g. a screen
    # added at z=0.3 m reads back as origin z=300) -- but Volume.add()'s
    # own x/y/z args are in meters, same as every other RF-Track setter in
    # this module, so this must convert back.
    return PKDict(x=origin[0] / 1000.0, y=origin[1] / 1000.0, z=origin[2] / 1000.0)


def _read_attrs_h5(group):
    d = PKDict(group.attrs)
    for k in group:
        d[k] = group[k][()]
    return d


def _read_indexed_group(parent, name):
    g = parent[name]
    return [_read_attrs_h5(g[str(i)]) for i in range(len(g))]


def _resolve_field_map_refs(elements, field_maps_group):
    """The exact inverse of `_dedupe_field_maps()`: replace every "@<md5>"
    reference in `elements` with the real array read from
    `field_maps_group[md5]`.
    """
    resolved = []
    for e in elements:
        d = PKDict(e)
        for k, v in e.items():
            if isinstance(v, str) and v.startswith("@"):
                d[k] = field_maps_group[v[1:]][()]
        resolved.append(d)
    return resolved


def _serialize_bpm(e):
    return PKDict(
        length=e.get_length(),
        resolution=e.get_resolution(),
        resolution_t=e.get_resolution_t(),
    )


def _serialize_corrector(e):
    kx, ky = e.get_strength()
    return PKDict(length=e.get_length(), kx=float(kx), ky=float(ky))


def _serialize_drift(e):
    return PKDict(length=e.get_length())


def _serialize_pillbox_cavity(e):
    return PKDict(
        frequency=e.get_frequency(),
        cell_length=e.get_cell_length(),
        n_cells=round(e.get_length() / e.get_cell_length()),
        coefficients=e.get_coefficients().tolist(),
        phid=e.get_phid(),
    )


def _serialize_quadrupole(e):
    return PKDict(length=e.get_length(), gradient=e.get_gradient())


def _serialize_rf_fieldmap_1d(e):
    # get_Ez() is the exact array the field map file was loaded into --
    # confirmed empirically this round-trips a reconstructed element's
    # get_field() output exactly (max diff 0.0) against the original.
    return PKDict(
        ez=e.get_Ez(),
        hz=e.get_hz(),
        length=e.get_length(),
        frequency=e.get_frequency(),
        direction=e.get_direction(),
        phid=e.get_phid(),
        p_map=e.get_P_map(),
        p_actual=e.get_P_actual(),
    )


def _serialize_rf_fieldmap_2d(e):
    # Unlike RF_FieldMap_1d's get_Ez(), there's no direct 2D array getter,
    # so this samples get_field_complex(x, y, z, t) point by point over
    # the full (nz, nr) grid -- cylindrical symmetry means Er is just the
    # Cartesian Ex component at (x=r, y=0) (confirmed empirically: sampling
    # at (x=0, y=r) instead shows the identical value in Ey, not Ex).
    #
    # Critically, get_field_complex()'s result already has the element's
    # own phid rotation baked in -- confirmed empirically: a copy built
    # with phid=0 and never touched matches the original's reading
    # exactly, while one built from this same grid with phid set AGAIN
    # double-applies the rotation. So phid is reset to 0 for the
    # extraction, then restored on the original afterward, and the
    # genuine phid is carried separately (same split as every other
    # cavity type here) rather than baked into the grid.
    hr = e.get_hr()
    hz = e.get_hz()
    nr = int(e.get_nr())
    nz = int(e.get_nz())
    phid = e.get_phid()
    e.set_phid(0.0)
    try:
        er = numpy.zeros((nz, nr), dtype=complex)
        ez = numpy.zeros((nz, nr), dtype=complex)
        for zi in range(nz):
            z_mm = zi * hz * 1000.0
            for ri in range(nr):
                r_mm = ri * hr * 1000.0
                field = e.get_field_complex(r_mm, 0.0, z_mm, 0.0)[0]
                er[zi, ri] = field[0]
                ez[zi, ri] = field[2]
    finally:
        e.set_phid(phid)
    return PKDict(
        er=er,
        ez=ez,
        hr=hr,
        hz=hz,
        frequency=e.get_frequency(),
        direction=e.get_direction(),
        phid=phid,
        p_map=e.get_P_map(),
        p_actual=e.get_P_actual(),
    )


def _serialize_screen(e):
    return PKDict(width=e.get_width(), height=e.get_height())


def _serialize_static_magnetic_fieldmap_1d(e):
    # There's no direct Bz-array getter for this class (unlike
    # RF_FieldMap_1d's get_Ez()), so this samples get_field() along the
    # element's own z range instead. get_field(x, y, z, t)'s coordinate
    # arguments are documented (RF-Track reference manual, section 5.1.2)
    # as millimeters, not meters like get_length()/get_z0()/get_z1() --
    # confirmed empirically: sampling with z in mm reproduces a real
    # solenoid field map's documented peak field exactly, matching its
    # source field-map file; the returned B itself is already in Tesla,
    # no further scaling needed.
    hz = e.get_hz()
    nz = int(e.get_nz())
    z_mm = numpy.linspace(e.get_z0(), e.get_z1(), nz) * 1000.0
    _, b = e.get_field(0.0, 0.0, z_mm, 0.0)
    return PKDict(bz=numpy.asarray(b)[:, 2], hz=hz)


def _write_attrs_h5(group, data):
    """Write a flat dict of scalars/small arrays as attrs on `group`,
    except a numpy array (e.g. a field map), which goes in as its own
    dataset instead -- an attr isn't meant to hold something that size.

    Mirrors lume-impact's `write_attrs_h5()`/`write_fieldmap_h5()`, the
    simplest pattern in the LUME ecosystem for this.
    """
    for k, v in data.items():
        if isinstance(v, numpy.ndarray):
            group.create_dataset(k, data=v)
        else:
            group.attrs[k] = v


def _write_field_units_h5(group, keys):
    """Write one child group per key in `keys` that `rslume.rftrack_units.UNITS`
    knows a unit symbol for, each holding openPMD-style `unitSI`/
    `unitDimension`/`unitSymbol` attrs (`beamphysics.units.write_unit_h5()`,
    given a `pmd_unit` built from that symbol on the spot -- `UNITS` itself
    holds plain strings, not `pmd_unit` objects, so it can also be reused
    directly as `unit=` for a live action variable).

    Lives under a top-level `units` group parallel to `elements`/`bunch`,
    not nested inside them -- nesting a child group under an
    elements/bunch item would break `_read_attrs_h5`'s `group[k][()]`,
    which assumes every child is a dataset. Purely additive documentation;
    `load_archive()` never reads this back, since the Python code already
    knows the units by construction.
    """
    for k in keys:
        symbol = UNITS.get(k)
        if symbol is not None:
            write_unit_h5(group.create_group(k), pmd_unit(symbol))


def _write_indexed_group(parent, name, items):
    """Write `items` (each a flat dict) as `parent/name/0`, `.../1`, ..."""
    g = parent.create_group(name)
    for i, item in enumerate(items):
        _write_attrs_h5(g.create_group(str(i)), item)
