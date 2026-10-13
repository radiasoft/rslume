"""Tests for `archiver/pvlist.py` -- that it stays in sync with what
`serving/serve.py` actually serves. The live round trip against a real
EPICS Archiver Appliance (`archivePV`, then `getDataAtTime`) was verified
by hand against a running quickstart appliance; there is no such
appliance in a normal test environment to exercise it automatically.

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

import sys

import pykern.pkio

_ROOT = pykern.pkio.py_path(__file__).dirpath().dirpath()


def test_pvlist_matches_served_scalar_variables():
    sys.path.insert(0, str(_ROOT.join("twin")))
    sys.path.insert(0, str(_ROOT.join("archiver")))
    from pykern import pkunit
    from pvlist import DEFAULT_PREFIX, awa_pv_names
    from zone_model import build_chain

    # only the served names matter here, not the physics
    chain = build_chain(n_particles=100, threads=1)
    # pvlist.py deliberately excludes the screen _image variables -- the
    # archiver is for scalar history, not images (the HTU twin's own
    # archiver setup, if it has one, would face the same split).
    served_scalars = {
        DEFAULT_PREFIX + name
        for name in chain.supported_variables
        if not name.endswith("_image")
    }
    listed = set(awa_pv_names())
    pkunit.pkeq(listed, served_scalars)
