"""LUME interface for RF-Track

RF-Track is an in-process Python simulation library with no text-based
lattice file format, so this builds on ``lume.actions.ActionModel``
directly: the caller builds a real ``RF_Track.Lattice``/``RF_Track.Volume``
and initial bunch themselves via RF-Track's native API, then wraps them in
:class:`rslume.rftrack_simulator.RFTrackSimulator` and a list of
:class:`rslume.rftrack_actions.RFTrackWritableScalarVariable`/
:class:`rslume.rftrack_actions.RFTrackReadOnlyScalarVariable` instances
naming the element attributes to expose.

Element attribute access uses RF-Track's own paired ``get_X()``/``set_X()``
methods (e.g. ``get_gradient()``/``set_gradient()``), not plain mutable
attributes.

:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from lume.actions import ActionModel

from rslume.rftrack_actions import (
    RFTrackWritableScalarVariable,
    RFTrackWritableVectorComponentVariable,
)
from rslume.rftrack_simulator import RFTrackSimulator
from rslume.rftrack_units import UNITS


class LUMERFTrackModel(ActionModel[RFTrackSimulator]):
    """LUME model for RF-Track.

    Every `set()` re-tracks the whole beamline eagerly (RF-Track tracking
    is fast enough for this to be appropriate, unlike more expensive
    PIC-style codes).
    """

    def reset(self):
        # Not using ActionModel's inherited reset(): it decides what to
        # reset via `isinstance(av, WritableActionMixin)`, but
        # rftrack_actions.RFTrackReadOnlyActionMixin also inherits from
        # RFTrackWritableActionMixin (to reuse its _get), so a read-only
        # variable would incorrectly be included and hit ReadOnlyError.
        self._set(
            {
                av.name: av.default_value
                for av in self._action_variable_by_name.values()
                if not av.read_only and av.default_value is not None
            }
        )

    def _set(self, values):
        super()._set(values)
        self.simulator.track()


def build_model(elements, volume, bunch):
    """`volume`/`bunch` wrapped as a `LUMERFTrackModel`, with one writable
    action variable per adjustable `elements` entry -- only attributes a
    real control system could plausibly set (e.g. a solenoid's current),
    never a field-map file name. Each variable's default_value is read
    directly off the element already in `volume` (RF_Track's own live
    get_X(), not a separate `elements` field), since that element is the
    single source of truth for its own attributes regardless of which
    `elements` fields happened to build it.

    Args:
        elements (list): the `PKDict` specs `volume` was built from, each
            with `name` and `kind`
        volume: the `RF_Track.Volume` or `RF_Track.Lattice` to track
        bunch: the initial `RF_Track` bunch

    Returns:
        LUMERFTrackModel: wrapping `volume` and `bunch`

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
      full rebuild of the beamline, not a per-element mutation like
      every other row here -- deliberately out of scope for now.
    - drift/screen/bpm: never control-room knobs.
    """
    simulator = RFTrackSimulator(volume, bunch)
    variables = []
    for spec in elements:
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
