"""Action-variable implementations for the AWA zone twin's own extra PVs
-- the ones the generated `build_model()` (via `rslume.rftrack`) can't
cover: zone1's solenoid scale factor (baked in at construction, no live
setter), and each zone's charge/energy/energy-spread diagnostics and
screen images (derived from the tracked bunch, not a single element
attribute at all).

`rslume.rftrack_actions`'s own action classes
(`RFTrackWritableScalarVariable` etc.) are the generic layer; these are
the AWA-twin-specific one.

Each variable's `_get`/`_set` here takes the
*owning* `Zone1Model`/`Zone2Model` instance as its "simulator" argument,
not an RF-Track simulator directly -- the rebuild/screen-image/
diagnostic-bunch logic these need lives on the zone model itself, not
on `model.simulator`. See `zone_model.py`'s own module docstring for
why zone1's solenoids need a rebuild at all.
"""

import RF_Track as rft
from lume.actions import ReadOnlyActionMixin, WritableActionMixin
from lume.variables import NDVariable, ScalarVariable

# Resolution of a screen's served image (AWA's zones have no modeled
# camera, so this is just a reasonable display resolution).
IMAGE_BINS = 64


class ChargePcVariable(ScalarVariable, ReadOnlyActionMixin):
    """A zone's total tracked charge, in pC (NaN before there's a bunch
    to measure -- see the owning model's own `diagnostic_bunch()`).
    """

    def _get(self, model):
        bunch = model.diagnostic_bunch()
        if bunch is None:
            return float("nan")
        return abs(bunch.get_total_charge()) / rft.nC * 1000.0


class EnergyMeVVariable(ScalarVariable, ReadOnlyActionMixin):
    """A zone's mean kinetic energy, in MeV (NaN before there's a bunch
    to measure).
    """

    def _get(self, model):
        bunch = model.diagnostic_bunch()
        if bunch is None:
            return float("nan")
        return bunch.get_info().mean_E


class EnergySpreadPctVariable(ScalarVariable, ReadOnlyActionMixin):
    """A zone's energy spread, as a percent of its mean energy (NaN
    before there's a bunch to measure, or if the mean energy is exactly
    0).
    """

    def _get(self, model):
        bunch = model.diagnostic_bunch()
        if bunch is None:
            return float("nan")
        info = bunch.get_info()
        return 100.0 * info.sigma_E / info.mean_E if info.mean_E else float("nan")


class ScreenImageVariable(NDVariable, ReadOnlyActionMixin):
    """A screen's own 2D histogram image. Just serves whatever the
    owning model's own `_update_screen_images()` already computed --
    unlike Cheetah's `Screen.reading`, RF-Track has no built-in
    screen-image accessor, so computing the histogram itself is the
    zone model's job, not this variable's.
    """

    screen_name: str

    def _get(self, model):
        return model.screen_images[f"{self.screen_name}_image"]


class SolenoidScaleFactorVariable(ScalarVariable, WritableActionMixin):
    """Zone1-only: one solenoid's field-map scale factor. Baked in at
    construction time (`Static_Magnetic_FieldMap_1d` has no live scale
    attribute), so `_set()` only records the new value on the owning
    model -- it does *not* rebuild by itself. `Zone1Model._set()` is
    the one that decides when to actually rebuild (once per `.set()`
    call, no matter how many solenoids changed in it, not once per
    solenoid -- a rebuild re-tracks 10,000 macroparticles through space
    charge, so coalescing matters).
    """

    solenoid_name: str

    def _get(self, model):
        return model.solenoid_scale_factor[self.solenoid_name]

    def _set(self, model, value):
        model.solenoid_scale_factor[self.solenoid_name] = float(value)


def diagnostic_variables(prefix):
    """`{"<prefix>charge_pC", "<prefix>energy_MeV", "<prefix>energy_spread_pct"}`."""
    return {
        f"{prefix}charge_pC": ChargePcVariable(
            name=f"{prefix}charge_pC", read_only=True, unit="pC"
        ),
        f"{prefix}energy_MeV": EnergyMeVVariable(
            name=f"{prefix}energy_MeV", read_only=True, unit="MeV"
        ),
        f"{prefix}energy_spread_pct": EnergySpreadPctVariable(
            name=f"{prefix}energy_spread_pct", read_only=True, unit="%"
        ),
    }


def screen_image_variables(screen_names):
    return {
        f"{name}_image": ScreenImageVariable(
            name=f"{name}_image",
            screen_name=name,
            shape=(IMAGE_BINS, IMAGE_BINS),
            unit="counts",
            read_only=True,
        )
        for name in screen_names
    }


def solenoid_scale_factor_variables(solenoid_scale_factor):
    """One `SolenoidScaleFactorVariable` per `{name: current_value}` in
    `solenoid_scale_factor` (`Zone1Model.solenoid_scale_factor`).
    """
    return {
        f"{name}_scale_factor": SolenoidScaleFactorVariable(
            name=f"{name}_scale_factor",
            solenoid_name=name,
            default_value=value,
            unit=None,
        )
        for name, value in solenoid_scale_factor.items()
    }
