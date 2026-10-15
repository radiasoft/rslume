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
from pykern.pkcollections import PKDict

from rslume.rftrack_actions import (
    RFTrackWritableScalarVariable,
    RFTrackWritableVectorComponentVariable,
)
from rslume.rftrack_simulator import RFTrackSimulator
from rslume.rftrack_units import UNITS
import rslume.rftrack_utils

# Element kind -> the parameters `build_model()` makes a variable for, each
# named by `variable_name()` and with its unit in `UNITS`. Each was
# confirmed against RF-Track's live API. Every cavity kind is an
# RF_FieldMap_1d or RF_FieldMap_2d, whose P_actual scales its amplitude.
# Kinds left out have none:
# - solenoid_fieldmap: none. Static_Magnetic_FieldMap_1d has no live scale
#   attribute, and replace_with() silently does nothing for an element
#   placed in a Volume, so only a full rebuild of the beamline can change it.
# - drift, screen, bpm: not control-room knobs.
KIND_PARAMETERS = PKDict(
    cavity_analytic=("phid", "p_actual"),
    cavity_fieldmap=("phid", "p_actual"),
    cavity_fieldmap_2d=("phid", "p_actual"),
    corrector=("hkick", "vkick"),
    quadrupole_gradient=("gradient",),
    quadrupole_k1=("k1",),
    rbend=("angle",),
    solenoid_analytic=("max_current",),
)

# Parameter -> (RF-Track attribute, index into a vector attribute or None).
# k1 is `strength`, which is K1 directly, independent of the reference
# momentum, unlike get_K1(P_Q). A corrector's `strength` is [hkick, vkick].
_PARAMETER_ATTRIBUTE = PKDict(
    angle=("angle", None),
    gradient=("gradient", None),
    hkick=("strength", 0),
    k1=("strength", None),
    max_current=("max_current", None),
    p_actual=("P_actual", None),
    phid=("phid", None),
    vkick=("strength", 1),
)


class LUMERFTrackModel(ActionModel[RFTrackSimulator]):
    """LUME model for RF-Track.

    Every `set()` re-tracks the whole beamline eagerly (RF-Track tracking
    is fast enough for this to be appropriate, unlike more expensive
    PIC-style codes).
    """

    def _set(self, values):
        super()._set(values)
        self.simulator.track()


def build_model(elements, volume, bunch):
    """`volume`/`bunch` wrapped as a `LUMERFTrackModel`, with one writable
    action variable per `KIND_PARAMETERS` entry of each `elements` spec --
    only attributes a real control system could plausibly set (e.g. a
    solenoid's current), never a field-map file name. Each variable's
    default_value is read directly off the element already in `volume`
    (RF_Track's own live get_X(), not a separate `elements` field), since
    that element is the single source of truth for its own attributes
    regardless of which `elements` fields happened to build it.

    Args:
        elements (list): the `PKDict` specs `volume` was built from, each
            with `name` and a `kind` in `rslume.rftrack_utils.ELEMENT_KINDS`
        volume: the `RF_Track.Volume` or `RF_Track.Lattice` to track
        bunch: the initial `RF_Track` bunch

    Returns:
        LUMERFTrackModel: wrapping `volume` and `bunch`
    """
    simulator = RFTrackSimulator(volume, bunch)
    variables = []
    for spec in elements:
        if spec.kind not in rslume.rftrack_utils.ELEMENT_KINDS:
            raise AssertionError(f"unsupported element kind={spec.kind!r}")
        e = simulator.find_element(spec.name)
        for p in KIND_PARAMETERS.get(spec.kind, ()):
            variables.append(_variable(e, spec.name, p))
    return LUMERFTrackModel(simulator=simulator, action_variables=variables)


def variable_name(element_name, parameter):
    """The name of the variable for `element_name`'s `parameter`, e.g.
    "Q1_k1"."""
    return f"{element_name}_{parameter}"


def _variable(element, element_name, parameter):
    attribute, index = _PARAMETER_ATTRIBUTE[parameter]
    v = getattr(element, f"get_{attribute}")()
    common = PKDict(
        name=variable_name(element_name, parameter),
        element_name=element_name,
        attribute=attribute,
        unit=UNITS[parameter],
    )
    if index is None:
        return RFTrackWritableScalarVariable(default_value=v, **common)
    return RFTrackWritableVectorComponentVariable(
        default_value=float(v[index]), index=index, **common
    )
