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

from rslume.rftrack_simulator import RFTrackSimulator


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
