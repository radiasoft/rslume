"""Tests for `phoebus/generate_zone_twin_display.py`: the checked-in
`zone_twin.bob` is current, and it shows exactly the variables the chain
serves.

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

import sys

import pykern.pkio

_EXAMPLE_DIR = pykern.pkio.py_path(__file__).dirpath().dirpath()
_DISPLAY = _EXAMPLE_DIR.join("phoebus", "zone_twin.bob")


def test_display_is_current():
    _add_paths()
    import generate_zone_twin_display
    from pykern import pkunit

    pkunit.pkeq(_DISPLAY.read(), generate_zone_twin_display.build())


def test_display_variables_are_served():
    _add_paths()
    from pykern import pkunit
    from zone_model import build_chain

    served = {}
    for z in build_chain(n_particles=10, threads=1).lume_model_instances:
        served.update(z.supported_variables)
    pkunit.pkeq(
        (
            sorted(n for n, v in served.items() if not v.read_only),
            sorted(n for n, v in served.items() if v.read_only),
        ),
        _display_variables(),
    )


def test_kinds_are_element_kinds():
    _add_paths()
    import generate_zone_twin_display
    import rslume.rftrack_utils
    from pykern import pkunit

    pkunit.pkeq(
        set(),
        set(generate_zone_twin_display._KIND_GROUP)
        - rslume.rftrack_utils.ELEMENT_KINDS,
    )


def _add_paths():
    for d in ("phoebus", "twin"):
        p = str(_EXAMPLE_DIR.join(d))
        if p not in sys.path:
            sys.path.insert(0, p)


def _display_variables():
    """(writable, read-only) variable names `zone_twin.bob` shows, sorted:
    the editors' PVs, and the readbacks' and screen images' PVs."""
    import re
    import xml.etree.ElementTree

    writable = set()
    read_only = set()
    for w in xml.etree.ElementTree.parse(str(_DISPLAY)).iter("widget"):
        if w.get("type") == "embedded":
            writable.update(m.text for m in w.find("macros") if m.tag != "NAME")
        elif w.get("type") == "navtabs":
            read_only.update(
                t.find("macros/CAM").text + "_image" for t in w.iter("tab")
            )
        elif (p := w.find("pv_name")) is not None and (
            m := re.fullmatch(r"pva://\$\(P=[^)]*\)(\w+)", p.text)
        ):
            read_only.add(m.group(1))
    # lume-pva serves STATUS itself
    read_only.remove("STATUS")
    return sorted(writable), sorted(read_only)
