"""RF-Track support moved to lume-rftrack

The RF-Track LUME wrapper (formerly `rslume.rftrack` and the
`rslume.rftrack_*` modules) and the AWA zone twin example are now
maintained in https://github.com/lume-science/lume-rftrack as the
`lume_rftrack` package. Importing this module raises `ImportError`
pointing there.

:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

raise ImportError(
    "rslume.rftrack has moved to lume-rftrack"
    + " (https://github.com/lume-science/lume-rftrack): use the lume_rftrack"
    + " package, e.g. lume_rftrack.model.build_model() and LUMERFTrackModel,"
    + " lume_rftrack.simulator.RFTrackSimulator and lume_rftrack.actions",
    name=__name__,
)
