"""LUME models for AWA zone1/zone2, chained with `lume.staged_model.StagedModel`.

Both zones' physics come from two generated scripts, "AWA Zone 1" and
"AWA Zone 2", kept in `sources/zone1_source.py`/`sources/zone2_source.py`
(see `_load_generated_module()` below).
Reusing their `build_beamline()`/`build_bunch()`/`autophase()` and
`rslume`'s `apply_space_charge()`/`build_model()` means this module doesn't
re-derive the lattice, bunch, autophase, and space-charge setup -- the
two generated scripts are the single source of truth, and this module is just glue: load
them, chain zone1's output into zone2's input, and expose each one's
own `build_model()` action variables (plus a few extras, below) as
`LUMEModel` variables.

`rslume.rftrack.build_model()`'s per-element action variables (gradient/
phid/k1/max_current/P_actual/hkick/vkick) cover everything with a live, no-rebuild RF-Track setter.
The one real gap: zone1's solenoids (`SolBF`/`SolM`/`SolL1`/`SolL2`/`SolL4`) are `solenoid_fieldmap` kind, whose field is rescaled
from a file at *construction* time -- `build_model()` deliberately
skips them (no live scale attribute exists on
`Static_Magnetic_FieldMap_1d`). `Zone1Model` adds a rebuild-based
`<name>_scale_factor` variable for each one instead: changing it edits
`ELEMENTS[i].scale_factor` in the loaded zone1 module and reruns
`build_beamline()`/`autophase()`/`apply_space_charge()`/`build_model()`
from scratch, the only way to make it take effect. This is exposed as
RF-Track's own `scale_factor` (`Static_Magnetic_FieldMap_1d`'s field
scales linearly with it), not a fabricated Amps value -- the archived
sim alone doesn't carry the coil's own current-to-field calibration
needed to convert it faithfully.

`lume.actions.ActionModel` (what `rslume.rftrack.LUMERFTrackModel` -- what
`build_model()` returns -- is built on) is already a `lume.model.
LUMEModel` subclass, and the existing `bunch6dt_to_particlegroup()`/
`particlegroup_to_bunch6d()` bridge functions in `rslume.rftrack_utils`
are exactly the zone1(`Bunch6dT`)-to-zone2(`Bunch6d`) handoff needed --
no changes needed there, and no lab/bunch-frame conversion or drift,
because zone1's tracked output is already the physical handoff state (no
intervening change of reference frame between the two zones).

Zone1's rebuild is slow: reading ~10 field-map files from disk,
autophase, and (most of all) a space-charge-tracked run of 10,000
macroparticles (the archived sim's own `BUNCH.np`) take real time --
budget something on the order of a minute per solenoid change, less
for anything build_model() already handles live (no rebuild at all).
Zone2's rebuild (only reached via its own `reset()`) has no field
maps, no autophase, and no space charge, and is fast.
"""

import pathlib

import numpy
import RF_Track as rft
from lume.model import LUMEModel
from lume.staged_model import FinalParticlesMixIn, InitialParticlesMixIn, StagedModel

from rslume.rftrack import build_model
from rslume.rftrack_utils import (
    apply_space_charge,
    bunch6d_to_particlegroup,
    bunch6dt_to_particlegroup,
    particlegroup_to_bunch6d,
)

from actions import (
    IMAGE_BINS,
    SolenoidScaleFactorVariable,
    diagnostic_variables,
    screen_image_variables,
    solenoid_scale_factor_variables,
)

_SOURCES_DIR = pathlib.Path(__file__).resolve().parent / "sources"

# Neither generated script pins a thread count it can be trusted with
# (each carries whatever SETTINGS.num_threads its own generating machine
# happened to have), so `build_chain()` sets one -- capped at
# rft.max_number_of_threads so it stays valid on a machine with fewer cores.
# 8 is within 8% of the fastest zone1 build at 1000, 2000 and 5000 particles
# (4-8 threads win; 12 or more is slower).
_DEFAULT_THREADS = 8

# Each screen's image field of view [mm, full width] -- NOT the mechanical
# screen size in ELEMENTS (set_aperture's values): at nominal settings the
# beam is only ~0.1-1.5 mm in sigma there (confirmed empirically), tens of times
# smaller than the mechanical screen, so an image histogrammed over the
# full mechanical size is almost entirely empty. These are ~10 sigma at
# nominal settings (some headroom for retuning before the beam image
# clips); a large enough retune can still outgrow them -- regenerate with
# new numbers (print each screen's sigma from a tracked chain)
# if that happens often for your settings.
SCREEN_FOV_MM = {
    "YAG1": 10.0,
    "YAG2": 6.0,
    "YAG3": 6.0,
    "YAG4": 6.0,
    "YAG5": 6.0,
    "YAG7": 10.0,
}


def _load_generated_module(name, lib_dir=None):
    """Exec `sources/<name>.py` (a generated parameters.py, its
    trailing auto-run `main()` call already stripped) into a fresh namespace, returning that
    namespace as a plain dict of its top-level names (`ELEMENTS`,
    `BUNCH`, `SETTINGS`, `build_beamline`, `build_bunch`,
    `autophase` if the sim used it, ...).

    `lib_dir`, if given, rewrites every element's own field-map `file`
    to an absolute path under it -- the generated script's own `file`
    values are bare basenames, meant to be resolved relative to
    whatever run directory the lib file would have been copied into,
    not anything this module can rely on as its current working
    directory.
    """
    path = _SOURCES_DIR / f"{name}.py"
    ns = {"__file__": str(path), "__name__": f"rslume_awa_zone_twin.{name}"}
    exec(compile(path.read_text(), str(path), "exec"), ns)
    if lib_dir is not None:
        for spec in ns["ELEMENTS"]:
            if "file" in spec:
                spec.file = str(lib_dir / spec.file)
    return ns


# Read-only views of each generated source (element tables, screen names,
# variable names) for consumers that only inspect it. `Zone1Model` execs its
# own copy, because it edits ELEMENTS/BUNCH in place on every rebuild.
ZONE1_MODULE = _load_generated_module("zone1_source", lib_dir=_SOURCES_DIR / "zone1_lib")
ZONE2_MODULE = _load_generated_module("zone2_source")


def _find_spec(elements, name):
    for e in elements:
        if e.name == name:
            return e
    raise KeyError(name)


class Zone1Model(FinalParticlesMixIn, LUMEModel):
    """AWA zone 1 as a `LUMEModel`: the chain's
    upstream, self-sourced stage (it generates its own cathode bunch --
    there is no stage ahead of it to inject one).
    """

    # Volume.get_bunch_at_screens() order follows these elements' own
    # physical order in ELEMENTS, confirmed against the generated
    # script's own ELEMENTS table.
    SOLENOID_NAMES = ("SolBF", "SolM", "SolL1", "SolL2", "SolL4")

    def __init__(self, n_particles=None):
        """`n_particles`, if given, overrides the archived sim's own
        `BUNCH.np` (10,000) for every (re)build -- lower it for a
        faster interactive response at the cost of statistics; `None`
        keeps the archived value as-is.
        """
        super().__init__()
        self._module = _load_generated_module(
            "zone1_source", lib_dir=_SOURCES_DIR / "zone1_lib"
        )
        rft.rng_set_seed(self._module["BUNCH"].random_seed)
        self._n_particles = n_particles
        self._screens = screen_names(self._module["ELEMENTS"])
        self._default_scale_factor = {
            name: float(_find_spec(self._module["ELEMENTS"], name).scale_factor)
            for name in self.SOLENOID_NAMES
        }
        self.solenoid_scale_factor = dict(self._default_scale_factor)
        self.model = None
        self.screen_images = {}
        self._rebuild()
        self._variables = dict(self.model.supported_variables)
        self._variables.update(solenoid_scale_factor_variables(self._default_scale_factor))
        self._variables.update(diagnostic_variables("zone1_"))
        self._variables.update(screen_image_variables(self._screens))

    def diagnostic_bunch(self):
        """The bunch `actions.py`'s diagnostic variables measure --
        zone1 has no "not ready yet" state of its own (it generates its
        own cathode bunch, so `tracked_bunch` is `None` only before the
        very first `track()`, same as `final_particles`).
        """
        return self.model.simulator.tracked_bunch

    @property
    def final_particles(self):
        """`tracked_bunch` as a `ParticleGroup`: `Bunch6dT`'s fixed-time
        snapshot, with every particle at the bunch's common time so
        zone2 can drift it to a plane and keep the bunch length."""
        bunch = self.model.simulator.tracked_bunch
        if bunch is None:
            return None
        return bunch6dt_to_particlegroup(bunch)

    def reset(self):
        self.solenoid_scale_factor = dict(self._default_scale_factor)
        self._rebuild()

    @property
    def supported_variables(self):
        return dict(self._variables)

    def _get(self, names):
        values = {}
        for name in names:
            if name in self.model.supported_variables:
                values[name] = self.model.get([name])[name]
            else:
                values[name] = self._variables[name]._get(self)
        return values

    def _rebuild(self):
        for name, value in self.solenoid_scale_factor.items():
            _find_spec(self._module["ELEMENTS"], name).scale_factor = value
        if self._n_particles is not None:
            self._module["BUNCH"].np = self._n_particles
        bunch = self._module["build_bunch"]()
        volume = self._module["build_beamline"]()
        self._module["autophase"](volume)
        apply_space_charge(volume, self._module["SETTINGS"].space_charge)
        self.model = build_model(self._module["ELEMENTS"], volume, bunch)
        self.model.reset()
        self._update_screen_images()

    def _set(self, values):
        model_values = {}
        rebuild = False
        for name, value in values.items():
            if name in self.model.supported_variables:
                model_values[name] = value
                continue
            var = self._variables[name]
            var._set(self, value)
            if isinstance(var, SolenoidScaleFactorVariable):
                rebuild = True
        if rebuild:
            # A solenoid's field is baked in at construction -- the
            # only way to apply a new scale_factor is a full rebuild,
            # which also re-autophases and re-tracks, so any other
            # changed variable is applied to the NEW model afterward
            # rather than to the one about to be discarded.
            self._rebuild()
            if model_values:
                self.model.set(model_values)
        elif model_values:
            self.model.set(model_values)
            self._update_screen_images()

    def _update_screen_images(self):
        self.screen_images = {
            f"{name}_image": _screen_image(bunch, SCREEN_FOV_MM[name])
            for name, bunch in zip(
                self._screens, self.model.simulator.beamline.get_bunch_at_screens()
            )
        }


class Zone2Model(InitialParticlesMixIn, LUMEModel):
    """AWA zone 2 as a `LUMEModel`: the chain's
    downstream, particle-accepting stage. Every one of its elements
    (quadrupoles, correctors) has a live `build_model()` setter, so
    unlike zone1 this never needs to rebuild the beamline at all.

    Its own generated `BUNCH`/`build_bunch()` (a `fromFile`
    distribution, a saved snapshot of zone1's earlier
    output) is unused here -- zone1's *live* tracked output is injected
    as `initial_particles` instead. Until the first injection, a
    single-macroparticle placeholder (this zone's own design momentum,
    zero everything else) stands in as `simulator.initial_bunch` so
    `build_model()`'s own `reset()`/`set()` (which always re-tracks)
    never has to handle a `None` bunch; `_has_injected` is what
    actually gates whether `initial_particles`/the diagnostics report
    real values or "nothing yet".
    """

    def __init__(self):
        super().__init__()
        self._screens = screen_names(ZONE2_MODULE["ELEMENTS"])
        self._has_injected = False
        self.model = build_model(
            ZONE2_MODULE["ELEMENTS"],
            ZONE2_MODULE["build_beamline"](),
            _placeholder_bunch(ZONE2_MODULE["BUNCH"]),
        )
        self.model.reset()
        self.screen_images = {
            f"{name}_image": numpy.zeros((IMAGE_BINS, IMAGE_BINS)) for name in self._screens
        }
        self._variables = dict(self.model.supported_variables)
        self._variables.update(diagnostic_variables("zone2_"))
        self._variables.update(screen_image_variables(self._screens))

    def diagnostic_bunch(self):
        """The bunch `actions.py`'s diagnostic variables measure --
        `None` until zone1 has actually injected one (unlike zone1,
        whose own `tracked_bunch` is a real signal on its own; zone2's
        `tracked_bunch` is never `None` once built, even before a real
        injection, because of its placeholder bunch).
        """
        return self.model.simulator.tracked_bunch if self._has_injected else None

    @property
    def initial_particles(self):
        """The bunch last injected from zone1, as a `ParticleGroup`
        (`Bunch6d`'s own fixed-z-plane snapshot); `None` before one has
        been injected."""
        if not self._has_injected:
            return None
        return bunch6d_to_particlegroup(self.model.simulator.initial_bunch)

    @initial_particles.setter
    def initial_particles(self, particles):
        self.model.simulator.initial_bunch = particlegroup_to_bunch6d(particles)
        self.model.simulator.track()
        self._has_injected = True
        self._update_screen_images()

    def reset(self):
        self.model = build_model(
            ZONE2_MODULE["ELEMENTS"],
            ZONE2_MODULE["build_beamline"](),
            _placeholder_bunch(ZONE2_MODULE["BUNCH"]),
        )
        self.model.reset()
        self._has_injected = False
        self.screen_images = {
            f"{name}_image": numpy.zeros((IMAGE_BINS, IMAGE_BINS)) for name in self._screens
        }

    @property
    def supported_variables(self):
        return dict(self._variables)

    def _get(self, names):
        values = {}
        for name in names:
            if name in self.model.supported_variables:
                values[name] = self.model.get([name])[name]
            else:
                values[name] = self._variables[name]._get(self)
        return values

    def _set(self, values):
        # Always safe: simulator.initial_bunch is the real injected
        # bunch once there is one, or the placeholder until then --
        # never None -- so LUMERFTrackModel._set()'s own re-track never crashes.
        self.model.set(values)
        if self._has_injected:
            self._update_screen_images()

    def _update_screen_images(self):
        self.screen_images = {
            f"{name}_image": _screen_image(bunch, SCREEN_FOV_MM[name])
            for name, bunch in zip(
                self._screens, self.model.simulator.beamline.get_bunch_at_screens()
            )
        }


def build_chain(n_particles=None, threads=None):
    """`StagedModel([Zone1Model(n_particles), Zone2Model()])`: zone1's
    tracked bunch becomes zone2's input on every `set()`.

    `threads` is RF-Track's thread count for every track (default
    `_DEFAULT_THREADS`, capped at `rft.max_number_of_threads`).
    """
    rft.cvar.number_of_threads = min(
        _DEFAULT_THREADS if threads is None else threads, rft.max_number_of_threads
    )
    return StagedModel([Zone1Model(n_particles), Zone2Model()])


def screen_names(elements):
    return [e.name for e in elements if e.kind == "screen"]


def _placeholder_bunch(bunch_settings):
    """A single macroparticle at `bunch_settings`' own design momentum
    (zero everything else) -- just enough for `build_model()`'s
    `reset()`/`set()` (which always re-tracks) to have something valid
    to track before zone1 has actually injected a real bunch.
    """
    return rft.Bunch6d(
        bunch_settings.mass_mev,
        0.0,
        bunch_settings.charge,
        numpy.array([0.0, 0.0, 0.0, 0.0, 0.0, bunch_settings.pc_mev]),
    )


def _screen_image(bunch, size_mm, bins=IMAGE_BINS):
    """2D histogram of `bunch`'s transverse position in
    `[-size_mm/2, size_mm/2]` on each axis, `bins` x `bins`, as a
    `counts` array. `Bunch6dT` (zone1's screens) needs the uppercase
    `%X %Y` field codes; `Bunch6d` (zone2's) needs lowercase `%x %y` --
    confirmed empirically, so this picks the right one from the bunch's
    own class rather than asking the caller to know.
    """
    codes = "%X %Y" if type(bunch).__name__ == "Bunch6dT" else "%x %y"
    xy = bunch.get_phase_space(codes)
    half = size_mm / 2.0
    image, _, _ = numpy.histogram2d(
        xy[:, 0], xy[:, 1], bins=bins, range=[[-half, half], [-half, half]]
    )
    return image.astype(numpy.float64)

