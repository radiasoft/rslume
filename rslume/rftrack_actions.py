"""RF-Track element-attribute action variables for `rslume.rftrack.RfTrack`

Each class exposes one RF-Track element attribute (via its paired
``get_X()``/``set_X()`` methods) as a `lume.variables.Variable`/
`lume.actions.Action`, for use as an `RfTrack` action variable --
generic, simulator-level plumbing with no unit conversion or PV-naming
convention of its own (a facility-specific control-system layer, if
one is ever needed, belongs on top of these).

Class order here follows the inheritance chain (each base class
defined before what builds on it), not strict alphabetical order --
`_RfTrackElementAccessMixin` has to come first despite being private,
since every other class in this module depends on it.

:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from lume.actions import ReadOnlyActionMixin, WritableActionMixin
from lume.exceptions import ReadOnlyError
from lume.variables import ScalarVariable


class _RfTrackElementAccessMixin:
    """Shared element-attribute resolution for RF-Track action variables."""

    element_name: str
    attribute: str

    def _get_direct_attribute(self, simulator):
        e = simulator.find_element(self.element_name)
        return getattr(e, f"get_{self.attribute}")()

    def _set_direct_attribute(self, simulator, value):
        e = simulator.find_element(self.element_name)
        getattr(e, f"set_{self.attribute}")(value)


class RfTrackWritableActionMixin(_RfTrackElementAccessMixin, WritableActionMixin):
    """Writable action mixin for an RF-Track element attribute."""

    def _get(self, simulator):
        return self._get_direct_attribute(simulator)

    def _set(self, simulator, value):
        self._set_direct_attribute(simulator, value)


class RfTrackReadOnlyActionMixin(RfTrackWritableActionMixin, ReadOnlyActionMixin):
    """Read-only action mixin for an RF-Track element attribute."""

    read_only = True

    def _set(self, simulator, value):
        raise ReadOnlyError("RfTrackReadOnlyActionMixin does not support setting values.")


class RfTrackWritableScalarVariable(ScalarVariable, RfTrackWritableActionMixin):
    """Writable scalar variable for an RF-Track element attribute."""


class RfTrackWritableVectorComponentVariable(ScalarVariable, RfTrackWritableActionMixin):
    """Writable scalar variable for one component of a vector-valued
    RF-Track element attribute (e.g. ``Corrector.strength`` ->
    ``[hkick, vkick]``).

    The underlying ``get_X()``/``set_X(...)`` pair takes/returns the whole
    vector at once, so a set here first reads the other component(s) back
    to avoid clobbering them.
    """

    index: int

    def _get(self, simulator):
        return self._get_direct_attribute(simulator)[self.index]

    def _set(self, simulator, value):
        e = simulator.find_element(self.element_name)
        current = list(getattr(e, f"get_{self.attribute}")())
        current[self.index] = value
        getattr(e, f"set_{self.attribute}")(*current)


class RfTrackReadOnlyScalarVariable(ScalarVariable, RfTrackReadOnlyActionMixin):
    """Read-only scalar variable for an RF-Track element attribute."""
