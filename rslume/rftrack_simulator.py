"""RFTrackSimulator: wraps a native RF-Track beamline + bunch

The "simulator" `rslume.rftrack.LUMERFTrackModel`
(a `lume.actions.ActionModel`) wraps and every `rslume.rftrack_actions`
action variable operates on. `archive()`/`load_archive()` delegate to
`rslume.rftrack_archive`, which holds the actual HDF5 serialization.

:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


class RFTrackSimulator:
    """Wraps a native RF-Track beamline and initial bunch.

    Args:
        beamline (RF_Track.Lattice or RF_Track.Volume): the beamline to track through.
            May be left as None for an "empty" simulator meant to be filled in by
            `load_archive()`.
        initial_bunch: an RF_Track bunch object (e.g. Bunch6d, Bunch6d_QR) to track.
            May be left as None, same as `beamline`.
    """

    def __init__(self, beamline=None, initial_bunch=None):
        self.beamline = beamline
        self.initial_bunch = initial_bunch
        self.tracked_bunch = None
        self.autophase = None
        self.space_charge = None

    def apply_space_charge(self):
        """Apply `space_charge` (e.g. as restored by `load_archive()`) to
        `beamline`, via `rslume.rftrack_utils.apply_space_charge()`; does
        nothing if it is `None`. Sets the process-global `rft.cvar.SC_engine`.
        """
        from rslume import rftrack_utils

        if self.space_charge is not None:
            rftrack_utils.apply_space_charge(self.beamline, self.space_charge)

    def archive(self, path, autophase=None, space_charge=None):
        """Write `beamline` and `initial_bunch` to `path` as HDF5."""
        from rslume import rftrack_archive

        rftrack_archive.archive(
            self, path, autophase=autophase, space_charge=space_charge
        )

    def find_element(self, name):
        """Return the beamline element named `name`.

        Raises:
            KeyError: no element with that name exists.
        """
        e = self.beamline.get_elements_by_name(name)
        if e == []:
            raise KeyError(f"no element named {name!r}")
        return e

    def load_archive(self, path):
        """Replace `beamline` and `initial_bunch` with the contents of
        `path` (as written by `archive()`).
        """
        from rslume import rftrack_archive

        rftrack_archive.load_archive(self, path)

    def track(self):
        """Track `initial_bunch` through `beamline`, storing the result.

        `beamline.track()` does not mutate `initial_bunch` or the beamline's
        elements, so this is safe to call repeatedly after changing element
        attributes via the writable action variables.
        """
        self.tracked_bunch = self.beamline.track(self.initial_bunch)
