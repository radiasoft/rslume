"""HDF5 archive format for rslume.rftrack

`RfTrackSimulator.archive()`/`load_archive()` (`rslume.rftrack_simulator`)
delegate to :func:`archive`/:func:`load_archive` here: this module holds the
actual beamline + bunch <-> HDF5 serialization, covering only the
element classes :data:`_ELEMENT_SERIALIZERS` knows about -- not a
bespoke format of its own, just RF-Track's own native class/attribute
names, written as plain, self-describing HDF5 any tool can read. See
:func:`archive`'s own docstring for the full format and what is/isn't a
faithful round-trip.

:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

import beamphysics
import h5py
import numpy
import scipy.constants
from beamphysics.units import pmd_unit, write_unit_h5
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdc, pkdlog, pkdp
from rslume.rftrack_units import UNITS
from rslume.rftrack_utils import (
    bunch6d_to_particlegroup,
    bunch6dt_to_particlegroup,
    particlegroup_to_bunch6d,
    particlegroup_to_bunch6dt,
)

# c in mm/ns == m/us, i.e. scipy.constants.c scaled down by 1e6 -- the same
# scale factor RF-Track's own Corrector.get_kick() uses internally to
# convert an integrated strength in T.mm to a kick angle in mrad for a
# given reference momentum in MeV/c (confirmed empirically against the
# reference manual's documented Kx/Ky units).
_C_MM_PER_NS = scipy.constants.c / 1e6

_CAVITY_CLASSES = frozenset(("Pillbox_Cavity", "RF_FieldMap_1d", "RF_FieldMap_2d"))


def archive(simulator, path, autophase=None, space_charge=None):
    """Write `simulator.beamline` and `simulator.initial_bunch` to `path`
    as HDF5 (called as `RfTrackSimulator.archive()`).

    `autophase` (bool) and `space_charge` (a dict, see below, or
    `None` for no space charge) record simulation-level settings
    that have no live equivalent in `rft.cvar` to read back at
    all: confirmed empirically that `rft.cvar.SC_engine`'s getter
    is completely type-erased (always the base `SpaceCharge` type,
    even checked at the raw SWIG object level; calling a
    concrete-subclass-only method on it fails), and `dir(rft.cvar)`
    itself returns `[]`, so there's no way to enumerate or identify
    *any* process-global setting from Python, space charge or
    otherwise.

    `space_charge` has no such signal to infer from (nothing about
    an element records whether space charge was active during its
    own tracking), so it defaults to `simulator.space_charge` -- `None`
    (not recorded) for a simulator built directly, or whatever
    `load_archive()` restored, so re-archiving a loaded simulator keeps
    it -- unless the caller passes it explicitly. `None` always means
    "use the simulator's", so to archive a loaded simulator *without*
    space charge, set `simulator.space_charge = None` first. `space_charge`'s shape mirrors the generated script's
    own `SETTINGS.space_charge`: `{"kind": "p2p"}`, or
    `{"kind": "pic", "dt_mm": float, "grid": (nx, ny, nz),
    "mirror_m": float, "smooth": float}`.

    `autophase`, unlike `space_charge`, *is* inferrable: a cavity
    element's own archived `t0` already tells us whether it was
    autophase()'d (see `_infer_autophase()`), so `autophase=None`
    here means "infer it from the elements," not "don't record
    it" -- the root attr is always written. Pass `True`/`False`
    explicitly only to override that inference.

    `load_archive()` sets `simulator.autophase`/`simulator.space_charge`
    from whatever was archived (`simulator.space_charge` is `None` if
    this wasn't passed at archive time) -- it never acts on them itself
    (e.g. it doesn't call `autophase()` again or build an
    `SC_engine`); they're informational for the caller, same as
    `simulator.beamline`/`simulator.initial_bunch`.

    `initial_bunch` is written as a real openPMD particle file (via
    `beamphysics.ParticleGroup.write()`), not a statistical summary
    -- `path` is simultaneously a valid standalone openPMD file
    (readable by any openPMD-aware tool, e.g.
    `beamphysics.ParticleGroup(h5=path)`) and this archive, sharing
    one HDF5 file. `load_archive()` gets back the exact same
    macroparticles (modulo float round-trip), not a new
    statistically-equivalent realization -- unlike the random seed
    (never recorded: RF-Track's own API has no getter for it,
    `rng_set_seed()` is write-only), there is nothing approximate
    about this part of the round trip.

    `initial_bunch` may be either a Bunch6d or a Bunch6dT -- the
    archived `bunch_type` attr records which, and `load_archive()`
    rebuilds the matching one (`particlegroup_to_bunch6d()`/
    `particlegroup_to_bunch6dt()` -- see `_bunch_to_particlegroup()`).

    An RF element that was autophase()'d before archiving (Volume.
    autophase() sets its `t0` directly; `get_phid()` never reflects
    that correction -- it always reads back the phid the element
    was constructed with) is archived faithfully: `t0` is captured
    per-element, for any class that has it (Pillbox_Cavity,
    RF_FieldMap_1d, RF_FieldMap_2d, Screen -- confirmed empirically,
    no other class does), and `load_archive()` restores it with
    `set_t0()`. Confirmed empirically to reproduce the autophased
    beamline's own tracked result exactly, without ever calling
    autophase() again -- `load_archive()` doesn't need to know
    autophase() was used in the first place.

    Raises `NotImplementedError` if `beamline` contains an element
    class `_ELEMENT_SERIALIZERS` doesn't know about yet, or a Volume
    element with a non-identity rotation (see `_serialize_position`).

    The format (root attrs `software="rslume"`, `bunch_type`
    ("Bunch6d" or "Bunch6dT"), `beamline_class` ("Lattice" or
    "Volume"), plus `s0`/`s1` for a Volume; a group `elements` of
    indexed, flat-attrs-or-dataset element groups; a group
    `field_maps`, present only if any element has an array-valued
    field, holding one dataset per *unique* array (keyed by its own
    md5), referenced from an element's attrs as `"@<md5>"` instead
    of embedding a byte-for-byte duplicate per element (see
    `_dedupe_field_maps`); a group `units` documenting each element
    field's RF-Track-native unit, openPMD-style; the bunch itself as
    a standard openPMD `particles` group, written by
    `ParticleGroup.write()`) is the actual interchange contract with
    anything that reads this file -- so it's plain, self-describing
    HDF5, not something that requires importing this module to read
    back. Root attrs deliberately
    exclude a `dataType` of our own: `ParticleGroup.write()` already
    sets one (`"openPMD"`, via openPMD's own `pmd_init()`) and
    silently overwrites anything already there under that exact key
    (confirmed empirically) -- `software`/`bunch_type`/
    `beamline_class` don't collide with any of openPMD's own root
    attrs (`basePath`/`dataType`/`openPMD`/`openPMDextension`/
    `particlesPath`).
    """
    kind = type(simulator.beamline).__name__
    elements, field_maps = _dedupe_field_maps(
        [_serialize_element(simulator.beamline[i], kind) for i in range(simulator.beamline.size())]
    )
    particle_group, bunch_type = _bunch_to_particlegroup(simulator.initial_bunch)
    if autophase is None:
        autophase = _infer_autophase(elements)
    if space_charge is None:
        space_charge = simulator.space_charge
    with h5py.File(path, "w") as f:
        f.attrs["software"] = "rslume"
        f.attrs["bunch_type"] = bunch_type
        f.attrs["beamline_class"] = kind
        f.attrs["autophase"] = int(autophase)
        if space_charge is not None:
            sc = f.create_group("space_charge")
            sc.attrs["kind"] = space_charge["kind"]
            if space_charge["kind"] == "pic":
                sc.attrs["dt_mm"] = float(space_charge["dt_mm"])
                sc.attrs["grid"] = numpy.asarray(space_charge["grid"], dtype=int)
                sc.attrs["mirror_m"] = float(space_charge["mirror_m"])
                sc.attrs["smooth"] = float(space_charge["smooth"])
        if kind == "Volume":
            # get_s0()/get_s1() return a Frame (like an element's
            # get_offsets()), not a plain float -- its origin's z
            # component (in mm, same as get_offsets(), hence /1000) is
            # the tracking-range value set_s0()/set_s1() itself takes
            # (in meters).
            f.attrs["s0"] = float(
                numpy.asarray(simulator.beamline.get_s0().get_origin()).flatten()[2]
            ) / 1000.0
            f.attrs["s1"] = float(
                numpy.asarray(simulator.beamline.get_s1().get_origin()).flatten()[2]
            ) / 1000.0
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
    `RfTrackSimulator.load_archive()`), rebuilding a new `rft.Lattice`
    or `rft.Volume` and the exact same macroparticles `archive()`
    wrote (see its own docstring). Clears `simulator.tracked_bunch`.

    Also sets `simulator.autophase`/`simulator.space_charge` from
    whatever `archive()` was given (`None` for either if it wasn't
    passed at archive time) -- purely informational, same as
    `simulator.beamline`/`simulator.initial_bunch`; this never acts on
    them itself (e.g. it doesn't call `autophase()` or build an
    `SC_engine`).
    """
    import RF_Track as rft

    with h5py.File(path, "r") as f:
        kind = str(f.attrs["beamline_class"])
        bunch_type = str(f.attrs["bunch_type"])
        elements = _read_indexed_group(f, "elements")
        if "field_maps" in f:
            elements = _resolve_field_map_refs(elements, f["field_maps"])
        s0 = f.attrs.get("s0")
        s1 = f.attrs.get("s1")
        simulator.autophase = bool(f.attrs["autophase"]) if "autophase" in f.attrs else None
        if "space_charge" in f:
            sc = f["space_charge"]
            simulator.space_charge = PKDict(sc.attrs)
            if "grid" in simulator.space_charge:
                simulator.space_charge["grid"] = tuple(
                    int(n) for n in simulator.space_charge["grid"]
                )
        else:
            simulator.space_charge = None
        particle_group = beamphysics.ParticleGroup(h5=f)
    if kind == "Lattice":
        beamline = rft.Lattice()
        for e in elements:
            beamline.append(_deserialize_element(rft, e))
    elif kind == "Volume":
        beamline = rft.Volume()
        for e in elements:
            beamline.add(
                _deserialize_element(rft, e),
                float(e.x),
                float(e.y),
                float(e.z),
                0.0,
                0.0,
                0.0,
            )
        beamline.set_s0(float(s0))
        beamline.set_s1(float(s1))
    else:
        raise NotImplementedError(f"don't know how to restore a beamline_class={kind!r}")
    simulator.beamline = beamline
    simulator.initial_bunch = _particlegroup_to_bunch(particle_group, bunch_type)
    simulator.tracked_bunch = None


def _bunch_to_particlegroup(bunch):
    """Convert `bunch` (a Bunch6d or Bunch6dT) to a `ParticleGroup`,
    returning `(particle_group, bunch_type)`. `bunch_type` records
    which conversion was used -- `particlegroup_to_bunch6d()`/
    `particlegroup_to_bunch6dt()` are not interchangeable (opposite
    z/t conventions, see their own docstrings), and nothing about the
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
    return rft.Bpm(
        float(d.length), float(d.resolution), float(d.resolution_t)
    )


def _deserialize_corrector(rft, d):
    return rft.Corrector(float(d.length), float(d.kx), float(d.ky))


def _deserialize_drift(rft, d):
    return rft.Drift(float(d.length))


def _deserialize_element(rft, d):
    cls = d["class"]
    if cls not in _ELEMENT_DESERIALIZERS:
        raise NotImplementedError(f"don't know how to restore a {cls!r} element yet")
    e = _ELEMENT_DESERIALIZERS[cls](rft, d)
    e.set_name(str(d.name))
    e.set_aperture(float(d.aperture_x), float(d.aperture_y), "circular")
    if "t0" in d:
        e.set_t0(float(d.t0))
    return e


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


def _infer_autophase(elements):
    """Infer whether `autophase()` was used, from the already-serialized
    `elements` themselves, for `archive()`'s own `autophase=None` case.

    A cavity `autophase()`'d before archiving has a real, nonzero `t0`
    (see `_serialize_element()`'s own comment -- `get_phid()` never
    reflects it, `t0` does); one that was never autophased either has
    no `"t0"` key at all (`t0_is_set()` was `False`) or, if the caller
    deliberately pinned it to suppress a `Bunch6dT` beamline's own
    unwanted rescue autophase on `.track()`, exactly `0.0`. Either way,
    "any cavity with a nonzero `t0`" is the signal.
    """
    return any(
        d.get("class") in _CAVITY_CLASSES and d.get("t0", 0.0) != 0.0
        for d in elements
    )


def _particlegroup_to_bunch(particle_group, bunch_type):
    """The exact inverse of `_bunch_to_particlegroup()`."""
    if bunch_type == "Bunch6dT":
        return particlegroup_to_bunch6dt(particle_group)
    return particlegroup_to_bunch6d(particle_group)


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
    # there's no direct Kx/Ky getter -- get_kick(p_ref_mev) returns the
    # EQUIVALENT kick angle in mrad for a particle with that reference
    # momentum, so this picks an arbitrary nonzero p_ref and inverts the
    # relation (any p_ref gives the same recovered Kx/Ky).
    p_ref_mev = 1.0
    kick = e.get_kick(p_ref_mev)
    return PKDict(
        length=e.get_length(),
        kx=kick[0] * p_ref_mev / _C_MM_PER_NS,
        ky=kick[1] * p_ref_mev / _C_MM_PER_NS,
    )


def _serialize_drift(e):
    return PKDict(length=e.get_length())


def _serialize_element(e, beamline_class="Lattice"):
    cls = type(e).__name__
    if cls not in _ELEMENT_SERIALIZERS:
        raise NotImplementedError(f"don't know how to archive a {cls!r} element yet")
    d = _ELEMENT_SERIALIZERS[cls](e)
    d["class"] = cls
    d.name = e.get_name()
    d.aperture_x = e.get_aperture_x()
    d.aperture_y = e.get_aperture_y()
    if beamline_class == "Volume":
        d.update(_serialize_position(e))
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


def _serialize_pillbox_cavity(e):
    return PKDict(
        frequency=e.get_frequency(),
        cell_length=e.get_cell_length(),
        n_cells=round(e.get_length() / e.get_cell_length()),
        coefficients=e.get_coefficients().tolist(),
        phid=e.get_phid(),
    )


def _serialize_position(e):
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


# Dispatch tables built from the `_serialize_*`/`_deserialize_*` functions
# above -- placed here, after them, rather than up with the other globals,
# since they need those functions to already exist.
_ELEMENT_SERIALIZERS = {
    "Bpm": _serialize_bpm,
    "Corrector": _serialize_corrector,
    "Drift": _serialize_drift,
    "Quadrupole": _serialize_quadrupole,
    "Pillbox_Cavity": _serialize_pillbox_cavity,
    "RF_FieldMap_1d": _serialize_rf_fieldmap_1d,
    "RF_FieldMap_2d": _serialize_rf_fieldmap_2d,
    "Screen": _serialize_screen,
    "Static_Magnetic_FieldMap_1d": _serialize_static_magnetic_fieldmap_1d,
}
_ELEMENT_DESERIALIZERS = {
    "Bpm": _deserialize_bpm,
    "Corrector": _deserialize_corrector,
    "Drift": _deserialize_drift,
    "Quadrupole": _deserialize_quadrupole,
    "Pillbox_Cavity": _deserialize_pillbox_cavity,
    "RF_FieldMap_1d": _deserialize_rf_fieldmap_1d,
    "RF_FieldMap_2d": _deserialize_rf_fieldmap_2d,
    "Screen": _deserialize_screen,
    "Static_Magnetic_FieldMap_1d": _deserialize_static_magnetic_fieldmap_1d,
}
