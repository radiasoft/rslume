"""Generate `zone_twin.bob`, a to-scale, clickable synoptic of the AWA
zone1->zone2 twin served by `twin/serve.py`.

Each element is drawn as a colored button at its real position
along the beamline; clicking it selects that element in the editor panel
beside the screen images. The panel holds one `embedded` widget per
element, all at the same spot, each showing a small, reusable, generic
editor `.bob` for that device *kind* (`solenoid_controls.bob`,
`cavity_controls.bob`, `corrector_controls.bob`, `quad_controls.bob`),
parameterized by macros carrying that element's own served PV names --
the same file serves every solenoid, cavity, etc., just loaded with
different macro values. A button writes its element's name to the local
PV `loc://selected_element`, and a rule on each embedded widget shows it
only while that PV holds its element's name. A screen shows `screen_view.bob`, an `image`
widget on its own `<name>_image` PV (a 2D histogram `Zone1Model`/
`Zone2Model` compute from `get_bunch_at_screens()`). A bare drift is
not drawn at all.

Positions and widths come straight from `zone_model`'s own loaded
`ZONE1_MODULE.ELEMENTS`/`ZONE2_MODULE.ELEMENTS` -- the exact
generated element tables `zone_model.py` itself builds from. Each element's
`elemedge` is each element's *absolute* position for zone1 (a Volume,
placed at arbitrary, even overlapping z) and each element's *start*
position for zone2 (a Lattice, sequential) -- `l` (when an element has
one; cavities/solenoids don't, their length instead comes from their
field-map file at build time) turns a start into a center for the
latter. The macro values (which PV each button's editor controls) come
straight from `build_model()`'s own per-kind naming convention
(`<name>_phid`, `<name>_k1`, `<name>_hkick`/`<name>_vkick`, ...) --
`solenoid_fieldmap`'s `<name>_scale_factor` is the one exception,
`Zone1Model`'s own rebuild-based variable, not one `build_model()`
itself exposes. So the display follows the code
on both counts. Run `python generate_zone_twin_display.py` to
regenerate; do not edit the `.bob` files by hand.
"""

from __future__ import annotations

import sys
from pathlib import Path
from xml.sax.saxutils import escape

from pykern.pkcollections import PKDict
from rslume.rftrack_units import UNITS

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "twin"))
from zone_model import (  # noqa: E402
    SCREEN_FOV_MM,
    screen_names,
    ZONE1_MODULE,
    ZONE2_MODULE,
)

ZONE1_ELEMENTS = ZONE1_MODULE.ELEMENTS
ZONE2_ELEMENTS = ZONE2_MODULE.ELEMENTS

DEFAULT_PREFIX = (
    "AWA:SIM:"  # the PV prefix serve.py uses; the display macro P replaces it
)

X0, AXIS_Y, WIDTH_PX = 30, 160, 1200

# screen_view.bob's own canvas size and the ScreenTabs navtabs' tab-button
# column width -- the navtabs widget's own width/height must be at least
# tab_width plus this canvas size, or the embedded display is clipped to
# whatever smaller area navtabs actually gives it (confirmed live: it
# does not scale the embedded display down to fit, it crops it).
_SCREEN_VIEW_WIDTH = 500
_SCREEN_VIEW_HEIGHT = 540
_SCREEN_TAB_WIDTH = 140

COLORS = PKDict(
    cavity=(220, 60, 60),
    solenoid=(60, 120, 220),
    corrector=(200, 60, 200),
    quadrupole=(255, 140, 0),
    screen=(0, 190, 120),
)

# The generated per-element `kind` string -> this display's drawing group
# (color/editor). Anything not listed (drift, bpm, rbend, ...) isn't
# drawn at all -- neither zone uses the ones left out, but the mapping
# only covers what it needs to, not every kind _build_element() knows.
_KIND_GROUP = {
    "cavity_analytic": "cavity",
    "cavity_fieldmap": "cavity",
    "cavity_fieldmap_2d": "cavity",
    "solenoid_analytic": "solenoid",
    "solenoid_fieldmap": "solenoid",
    "corrector": "corrector",
    "quadrupole_k1": "quadrupole",
    "quadrupole_gradient": "quadrupole",
    "screen": "screen",
}

# The PV the element buttons write and the embedded editors' rules watch.
_SELECTED_PV = 'loc://selected_element("")'

_EDITOR_WIDTH = 370

# group -> (editor title, editor file, [(label, macro, unit, format), ...]).
# The macros each editor needs are built per-element by _element_macros()
# below, not a fixed dict here.
_EDITORS = {
    # The scale factor is ~1e-4, so it is shown and entered in
    # exponential notation.
    "solenoid": (
        "Solenoid",
        "solenoid_controls.bob",
        [("Field scale factor", "SCALE", "", "exponential")],
    ),
    # POWER is RF_Track's own P_actual, in W: the field amplitude
    # scales as sqrt(P_actual / P_map). (build_model() has no live
    # setter for an absolute V/m value.)
    "cavity": (
        "Cavity",
        "cavity_controls.bob",
        [
            ("Power", "POWER", UNITS.p_actual, "decimal"),
            ("Phase", "PHASE", UNITS.phid, "decimal"),
        ],
    ),
    "corrector": (
        "Corrector",
        "corrector_controls.bob",
        [
            ("Horizontal", "H", UNITS.hkick, "decimal"),
            ("Vertical", "V", UNITS.vkick, "decimal"),
        ],
    ),
    "quadrupole": (
        "Quadrupole",
        "quad_controls.bob",
        [("Strength k1", "K1", UNITS.k1, "decimal")],
    ),
}


def _element_macros(group, e):
    """`{macro: value}` for `e`'s own editor, in `build_model()`'s (or,
    for a solenoid, `Zone1Model`'s own rebuild-based) PV naming
    convention. `NAME` is the
    element's own name, shown in the editor's title.
    """
    name = e.name
    if group == "cavity":
        # Both of zone1's/zone2's cavities (there are none in zone2)
        # are fieldmap-sourced, so P_actual always applies; an
        # analytic cavity has no live amplitude setter at all (see
        # build_model()'s own docstring) and isn't handled here.
        return {"NAME": name, "PHASE": f"{name}_phid", "POWER": f"{name}_p_actual"}
    if group == "solenoid":
        return {"NAME": name, "SCALE": f"{name}_scale_factor"}
    if group == "corrector":
        return {"NAME": name, "H": f"{name}_hkick", "V": f"{name}_vkick"}
    if group == "quadrupole":
        return {"NAME": name, "K1": f"{name}_k1"}
    raise AssertionError(f"unsupported group={group!r}")


def _visible_rule(shown_for):
    """A `rules` block that shows its widget while `_SELECTED_PV` equals
    `shown_for` and hides it otherwise.
    """
    q = escape(f'"{shown_for}"', {'"': "&quot;"})
    return (
        f"    <rules>\n"
        f'      <rule name="Selected" prop_id="visible" out_exp="false">\n'
        f'        <exp bool_exp="pvStr0 == {q}">\n'
        f"          <value>true</value>\n"
        f"        </exp>\n"
        f'        <exp bool_exp="pvStr0 != {q}">\n'
        f"          <value>false</value>\n"
        f"        </exp>\n"
        f"        <pv_name>{escape(_SELECTED_PV)}</pv_name>\n"
        f"      </rule>\n"
        f"    </rules>\n"
    )


class _Display:
    def __init__(self, width: int, height: int) -> None:
        self.width, self.height = width, height
        self._widgets: list[str] = []
        self._names: set[str] = set()

    def _unique(self, name: str) -> str:
        base, index = name, 2
        while name in self._names:
            name, index = f"{base}{index}", index + 1
        self._names.add(name)
        return name

    def label(self, name, text, x, y, w, h=22, bold=False, size=None, rotated=False):
        font = ""
        if bold or size:
            font = (
                f'\n    <font><font family="Liberation Sans" style="{"BOLD" if bold else "REGULAR"}" '
                f'size="{size or 12.0}"/></font>'
            )
        rot = "\n    <rotation_step>1</rotation_step>" if rotated else ""
        self._widgets.append(
            f'  <widget type="label" version="2.0.0">\n'
            f"    <name>{self._unique(name)}</name>\n"
            f"    <text>{escape(text)}</text>\n"
            f"    <x>{x}</x><y>{y}</y><width>{w}</width><height>{h}</height>{font}{rot}\n"
            f"  </widget>"
        )

    def value(self, name, pv, x, y, w, h=22, precision=3):
        self._widgets.append(
            f'  <widget type="textupdate" version="2.0.0">\n'
            f"    <name>{self._unique(name)}</name>\n"
            f"    <pv_name>pva://$(P={DEFAULT_PREFIX}){pv}</pv_name>\n"
            f"    <x>{x}</x><y>{y}</y><width>{w}</width><height>{h}</height>\n"
            f"    <precision>{precision}</precision>\n"
            f"    <precision_from_pv>false</precision_from_pv>\n"
            f"    <show_units>false</show_units>\n"
            f"  </widget>"
        )

    def placeholder(self, name, text, x, y, w, h=22):
        """A label shown only while nothing is selected."""
        self._widgets.append(
            f'  <widget type="label" version="2.0.0">\n'
            f"    <name>{self._unique(name)}</name>\n"
            f"    <text>{escape(text)}</text>\n"
            f"    <x>{x}</x><y>{y}</y><width>{w}</width><height>{h}</height>\n"
            f"{_visible_rule('')}"
            f"  </widget>"
        )

    def led(self, name, pv, x, y, w=20, h=20):
        self._widgets.append(
            f'  <widget type="led" version="2.0.0">\n'
            f"    <name>{self._unique(name)}</name>\n"
            f"    <pv_name>pva://$(P={DEFAULT_PREFIX}){pv}</pv_name>\n"
            f"    <x>{x}</x><y>{y}</y><width>{w}</width><height>{h}</height>\n"
            f'    <off_color><color red="0" green="170" blue="0"/></off_color>\n'
            f'    <on_color><color red="255" green="150" blue="0"/></on_color>\n'
            f"  </widget>"
        )

    def rect(self, name, x, y, w, h, rgb):
        r, g, b = rgb
        self._widgets.append(
            f'  <widget type="rectangle" version="2.0.0">\n'
            f"    <name>{self._unique(name)}</name>\n"
            f"    <x>{x}</x><y>{y}</y><width>{w}</width><height>{h}</height>\n"
            f'    <background_color><color red="{r}" green="{g}" blue="{b}"/></background_color>\n'
            f"    <line_width>1</line_width>\n"
            f"  </widget>"
        )

    def embedded(self, name, x, y, w, h, file, macros, shown_for):
        """An `embedded` display of `file` with `macros`, visible only
        while `_SELECTED_PV` holds `shown_for`.
        """
        macro_xml = "".join(f"<{k}>{escape(v)}</{k}>" for k, v in macros.items())
        self._widgets.append(
            f'  <widget type="embedded" version="2.0.0">\n'
            f"    <name>{self._unique(name)}</name>\n"
            f"    <file>{escape(file)}</file>\n"
            f"    <macros>{macro_xml}</macros>\n"
            f"    <x>{x}</x><y>{y}</y><width>{w}</width><height>{h}</height>\n"
            f"    <visible>false</visible>\n"
            f"{_visible_rule(shown_for)}"
            f"  </widget>"
        )

    def select_button(self, name, x, y, w, h, rgb, element, tooltip):
        """A button that writes `element` to `_SELECTED_PV`."""
        r, g, b = rgb
        self._widgets.append(
            f'  <widget type="action_button" version="3.0.0">\n'
            f"    <name>{self._unique(name)}</name>\n"
            f"    <actions>\n"
            f'      <action type="write_pv">\n'
            f"        <pv_name>{escape(_SELECTED_PV)}</pv_name>\n"
            f"        <value>{escape(element)}</value>\n"
            f"        <description>{escape(tooltip)}</description>\n"
            f"      </action>\n"
            f"    </actions>\n"
            f"    <text></text>\n"
            f"    <x>{x}</x><y>{y}</y><width>{w}</width><height>{h}</height>\n"
            f'    <background_color><color red="{r}" green="{g}" blue="{b}"/></background_color>\n'
            f"    <tooltip>{escape(tooltip)}</tooltip>\n"
            f"  </widget>"
        )

    def navtabs(self, name, tabs, x, y, w, h, tab_width=140, tab_height=30):
        """A `navtabs` widget (one embedded display at a time, selected
        from a column of tab buttons -- `direction` defaults to
        `VERTICAL`, which is what makes that column, not a horizontal
        strip): `tabs` is `[(tab_name, file, macros_dict), ...]`.
        """
        tab_xml = "".join(
            f"\n      <tab>\n"
            f"        <name>{escape(tab_name)}</name>\n"
            f"        <file>{escape(file)}</file>\n"
            f"        <macros>"
            + "".join(f"<{k}>{escape(v)}</{k}>" for k, v in macros.items())
            + "</macros>\n"
            f"        <group_name></group_name>\n"
            f"      </tab>"
            for tab_name, file, macros in tabs
        )
        self._widgets.append(
            f'  <widget type="navtabs" version="2.0.0">\n'
            f"    <name>{self._unique(name)}</name>\n"
            f"    <tabs>{tab_xml}\n    </tabs>\n"
            f"    <x>{x}</x><y>{y}</y><width>{w}</width><height>{h}</height>\n"
            f"    <tab_width>{tab_width}</tab_width>\n"
            f"    <tab_height>{tab_height}</tab_height>\n"
            f"  </widget>"
        )

    def xml(self) -> str:
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<display version="2.0.0">\n'
            "  <name>AWA zone1-&gt;zone2 twin</name>\n"
            f"  <width>{self.width}</width>\n  <height>{self.height}</height>\n"
            + "\n".join(self._widgets)
            + "\n</display>\n"
        )


# Visual-only width for a kind with no `l` of its own (cavities/
# solenoids: their real length comes from a field-map file at build
# time, not anything in ELEMENTS) -- a schematic approximation, not a
# metrology-grade drawing.
_DISPLAY_WIDTH_M = {"cavity": 0.3, "solenoid": 0.15, "screen": 0.05}


def _zone1_layout():
    """`[(s_center, width_m, group, element_dict), ...]` for
    `ZONE1_ELEMENTS`, plus zone1's own nominal length (its own
    `SETTINGS.tracking_range_m[1]`, not guessed from the last element's
    position -- a Volume's elements aren't necessarily stored in z
    order). `elemedge` is each element's *absolute* z position already
    (Volume/absolute mode), not a start position to accumulate.
    """
    layout = []
    for e in ZONE1_ELEMENTS:
        group = _KIND_GROUP.get(e.kind)
        if group is None:
            continue
        width = e.get("l") or _DISPLAY_WIDTH_M.get(group, 0.1)
        layout.append((e.elemedge, width, group, e))
    return layout, float(ZONE1_MODULE.SETTINGS.tracking_range_m[1])


def _zone2_layout(start_s):
    """`[(s_center, width_m, group, element_dict), ...]` for
    `ZONE2_ELEMENTS`, offset by `start_s` (zone1's own end) to make one
    continuous axis for the whole twin. `elemedge` is each element's
    *start* position (Lattice/sequential mode) -- `l` (present for
    every zone2 kind drawn: corrector, quadrupole; a screen has none,
    treated as a zero-width marker at its own elemedge) turns that into
    a center. A drift is skipped (never drawn).
    """
    layout = []
    end = start_s
    for e in ZONE2_ELEMENTS:
        end = max(end, start_s + float(e.elemedge) + float(e.get("l", 0.0)))
        group = _KIND_GROUP.get(e.kind)
        if group is None:
            continue
        width = e.get("l") or _DISPLAY_WIDTH_M.get(group, 0.1)
        layout.append((start_s + float(e.elemedge) + width / 2.0, width, group, e))
    return layout, end


def _draw_element(d, px_per_m, s_center, width_m, group, e):
    x = X0 + int(s_center * px_per_m) - max(int(width_m * px_per_m), 10) // 2
    w = max(int(width_m * px_per_m), 10)
    name = e.name
    if group == "screen":
        # not clickable: a screen's image is selected from the ScreenTabs
        # navtabs strip below, not from the floor plan.
        d.rect(f"rect_{name}", x, AXIS_Y - 30, 4, 60, COLORS.screen)
        d.label(f"lbl_{name}", name, x - 6, AXIS_Y - 95, 16, 56, rotated=True)
        return
    macros = _element_macros(group, e)
    tooltip = f"{name}: " + ", ".join(
        f"{m}={v}" for m, v in macros.items() if m != "NAME"
    )
    d.select_button(f"btn_{name}", x, AXIS_Y - 35, w, 70, COLORS[group], name, tooltip)
    d.label(f"lbl_{name}", name, x - 6, AXIS_Y - 100, 16, 56, rotated=True)


def build() -> str:
    """The display's XML."""
    zone1_elements, zone1_length = _zone1_layout()
    zone2_elements, total_length = _zone2_layout(zone1_length)
    px_per_m = WIDTH_PX / total_length

    d = _Display(X0 + WIDTH_PX + 40, AXIS_Y + 200)

    d.label(
        "Title",
        "AWA zone1 -> zone2 twin (click an element to edit it)",
        X0,
        10,
        700,
        28,
        bold=True,
        size=16.0,
    )
    d.label("StatusLabel", "Twin:", X0 + WIDTH_PX - 220, 12, 50, bold=True)
    d.led("StatusLed", "STATUS", X0 + WIDTH_PX - 170, 12)
    d.value("StatusText", "STATUS", X0 + WIDTH_PX - 140, 10, 130)

    # beam axis
    d.rect("axis", X0, AXIS_Y - 1, WIDTH_PX, 2, (0, 0, 0))

    for s_center, width_m, group, e in zone1_elements:
        _draw_element(d, px_per_m, s_center, width_m, group, e)
    for s_center, width_m, group, e in zone2_elements:
        _draw_element(d, px_per_m, s_center, width_m, group, e)

    # zone1/zone2 boundary marker
    boundary_x = X0 + int(zone1_length * px_per_m)
    d.rect("boundary", boundary_x, AXIS_Y - 60, 1, 120, (120, 120, 120))
    d.label(
        "BoundaryLabel", "zone1 | zone2", boundary_x - 50, AXIS_Y + 65, 100, 18, size=9
    )

    # legend
    ly = AXIS_Y + 110
    for i, (group, text) in enumerate(
        [
            ("cavity", "RF cavity (click)"),
            ("solenoid", "solenoid (click)"),
            ("corrector", "corrector (click)"),
            ("quadrupole", "quadrupole (click)"),
            ("screen", "screen (see tabs below)"),
        ]
    ):
        lx = X0 + i * 230
        d.rect(f"legend_{group}", lx, ly, 20, 20, COLORS[group])
        d.label(f"legend_text_{group}", text, lx + 28, ly - 2, 195, 24, size=14)

    # per-zone diagnostics (readbacks only -- not editable, so no button/popup)
    y = ly + 36
    for prefix, label_text, x in (
        ("zone1_", "Zone 1 exit", X0),
        ("zone2_", "Zone 2 exit", X0 + WIDTH_PX // 2),
    ):
        d.label(f"{prefix}DiagHeader", label_text, x, y, 300, 20, bold=True)
        for i, (field, text) in enumerate(
            (
                ("charge_pC", "Charge [pC]"),
                ("energy_MeV", "Energy [MeV]"),
                ("energy_spread_pct", "Energy spread [% rms]"),
            )
        ):
            d.label(f"{prefix}DiagL{i}", text, x, y + 26 + i * 24, 150)
            d.value(
                f"{prefix}DiagV{i}", f"{prefix}{field}", x + 155, y + 26 + i * 24, 110
            )
    y += 26 + 3 * 24 + 14

    # ScreenTabs: a column of tab buttons (navtabs' own VERTICAL default)
    # selects which screen's image is embedded here, replacing the
    # embedded display in place rather than opening a new window.
    d.label("ScreenTabsHeader", "Screen images", X0, y, 300, 22, bold=True)
    y += 28
    screens = screen_names(ZONE1_ELEMENTS) + screen_names(ZONE2_ELEMENTS)
    tabs = [
        (
            name,
            "screen_view.bob",
            {
                "CAM": name,
                "XMIN": f"{-SCREEN_FOV_MM[name] / 2:.3f}",
                "XMAX": f"{SCREEN_FOV_MM[name] / 2:.3f}",
                "YMIN": f"{-SCREEN_FOV_MM[name] / 2:.3f}",
                "YMAX": f"{SCREEN_FOV_MM[name] / 2:.3f}",
            },
        )
        for name in screens
    ]
    d.navtabs(
        "ScreenTabs",
        tabs,
        X0,
        y,
        _SCREEN_TAB_WIDTH + _SCREEN_VIEW_WIDTH,
        _SCREEN_VIEW_HEIGHT,
        tab_width=_SCREEN_TAB_WIDTH,
    )

    # The element editor, beside the screen images: every drawn element's
    # editor sits at this one spot, and only the selected one is visible.
    ex = X0 + _SCREEN_TAB_WIDTH + _SCREEN_VIEW_WIDTH + 30
    d.label("EditorHeader", "Element editor", ex, y - 28, 300, 22, bold=True)
    d.placeholder(
        "EditorHint", "Click an element above to edit it.", ex, y, _EDITOR_WIDTH
    )
    for _, _, group, e in zone1_elements + zone2_elements:
        if group == "screen":
            continue
        _, file, fields = _EDITORS[group]
        d.embedded(
            f"editor_{e.name}",
            ex,
            y,
            _EDITOR_WIDTH,
            _editor_height(fields),
            file,
            _element_macros(group, e),
            e.name,
        )

    d.height = y + _SCREEN_VIEW_HEIGHT + 20
    return d.xml()


def _write_editor_templates(out_dir: Path) -> None:
    """The four reusable, generic per-device-kind editor `.bob` files that
    `build()` embeds, plus the screen viewer. Each editor is parameterized
    by macros carrying the PV to control -- not a device name formatted
    into a fixed pattern -- so the same file serves every device of that
    kind.
    """
    templates = {
        file: _editor(title, fields) for title, file, fields in _EDITORS.values()
    }
    templates["screen_view.bob"] = _screen_view()
    for filename, xml in templates.items():
        (out_dir / filename).write_text(xml)


def _editor_height(fields) -> int:
    """The height of `_editor(title, fields)`."""
    return 50 + 66 * len(fields) + 10


def _editor(title: str, fields) -> str:
    """A small editor `.bob` with, for each `(label, macro, unit, format)`
    in `fields`, a label, a text entry (it writes the PV once, on Enter,
    so one edit starts one simulation), its unit, and a readback, all on
    `pva://$(P=AWA:SIM:)$(<macro>)`. `format` is `"decimal"` or
    `"exponential"`. `$(NAME)` (set by the embedding widget) is the
    element's name and appears in the title.
    """
    format_index = {"decimal": 1, "exponential": 2}
    y = 50
    widgets = []
    for label, macro, unit, fmt in fields:
        pv = f"pva://$(P={DEFAULT_PREFIX})$({macro})"
        widgets.append(
            f"""  <widget type="label" version="2.0.0">
    <name>Label_{macro}</name>
    <text>{escape(label)}</text>
    <x>20</x><y>{y}</y><width>130</width><height>25</height>
  </widget>
  <widget type="textentry" version="3.0.0">
    <name>Entry_{macro}</name>
    <pv_name>{pv}</pv_name>
    <x>155</x><y>{y}</y><width>120</width><height>25</height>
    <format>{format_index[fmt]}</format>
    <precision>4</precision>
    <precision_from_pv>false</precision_from_pv>
    <show_units>false</show_units>
  </widget>
  <widget type="label" version="2.0.0">
    <name>Unit_{macro}</name>
    <text>{escape(unit)}</text>
    <x>280</x><y>{y}</y><width>70</width><height>25</height>
  </widget>"""
        )
        y += 30
        widgets.append(
            f"""  <widget type="label" version="2.0.0">
    <name>RBLabel_{macro}</name>
    <text>readback:</text>
    <x>20</x><y>{y}</y><width>130</width><height>20</height>
  </widget>
  <widget type="textupdate" version="2.0.0">
    <name>RB_{macro}</name>
    <pv_name>{pv}</pv_name>
    <x>155</x><y>{y}</y><width>120</width><height>20</height>
    <format>{format_index[fmt]}</format>
    <precision>4</precision>
    <precision_from_pv>false</precision_from_pv>
    <show_units>false</show_units>
  </widget>"""
        )
        y += 36
    body = "\n".join(widgets)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<display version="2.0.0">
  <name>{escape(title)} $(NAME)</name>
  <width>{_EDITOR_WIDTH}</width>
  <height>{y + 10}</height>
  <widget type="label" version="2.0.0">
    <name>Title</name>
    <text>{escape(title)}: $(NAME)</text>
    <x>20</x><y>10</y><width>330</width><height>28</height>
    <font><font family="Liberation Sans" style="BOLD" size="16.0"/></font>
  </widget>
{body}
</display>
"""


def _screen_view() -> str:
    """A viewer `.bob` with one `image` widget on
    `pva://$(P=AWA:SIM:)$(CAM)_image`, `$(XMIN)/$(XMAX)/$(YMIN)/$(YMAX)`
    [mm] axis ranges, with `P` as a macro (default `AWA:SIM:`).
    """
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<display version="2.0.0">
  <name>$(CAM)</name>
  <width>{_SCREEN_VIEW_WIDTH}</width>
  <height>{_SCREEN_VIEW_HEIGHT}</height>
  <widget type="label" version="2.0.0">
    <name>Title</name>
    <text>$(CAM)</text>
    <x>10</x><y>5</y><width>400</width><height>24</height>
    <font><font family="Liberation Sans" style="BOLD" size="14.0"/></font>
  </widget>
  <widget type="image" version="2.0.0">
    <name>Image</name>
    <pv_name>pva://$(P={DEFAULT_PREFIX})$(CAM)_image</pv_name>
    <x>10</x><y>35</y><width>{_SCREEN_VIEW_WIDTH - 20}</width><height>{_SCREEN_VIEW_HEIGHT - 60}</height>
    <autoscale>true</autoscale>
    <x_axis>
      <visible>true</visible>
      <minimum>$(XMIN)</minimum>
      <maximum>$(XMAX)</maximum>
      <title>x [mm]</title>
    </x_axis>
    <y_axis>
      <visible>true</visible>
      <minimum>$(YMIN)</minimum>
      <maximum>$(YMAX)</maximum>
      <title>y [mm]</title>
    </y_axis>
  </widget>
</display>
"""


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    out_dir = Path(argv[0]) if argv else Path(__file__).parent
    out = out_dir / "zone_twin.bob"
    out.write_text(build())
    _write_editor_templates(out_dir)
    print(f"wrote {out} and its 5 editor/viewer templates in {out_dir}")


if __name__ == "__main__":
    main()
