import importlib

__all__ = [
    "Elegant",
    "Genesis2",
    "OPAL",
    "RfTrack",
    "RfTrackReadOnlyScalarVariable",
    "RfTrackWritableScalarVariable",
]

# Each wrapper is imported lazily (PEP 562) so that one wrapper's broken or
# missing dependency (e.g. lume-genesis/openpmd-beamphysics version drift)
# only fails when that specific wrapper is used, not for every import of
# rslume or of an unrelated wrapper.
_LAZY = {
    "Elegant": ("rslume.elegant", "Elegant"),
    "Genesis2": ("rslume.genesis2", "Genesis2"),
    "OPAL": ("rslume.opal", "OPAL"),
    "RfTrack": ("rslume.rftrack", "RfTrack"),
    "RfTrackReadOnlyScalarVariable": ("rslume.rftrack", "RfTrackReadOnlyScalarVariable"),
    "RfTrackWritableScalarVariable": ("rslume.rftrack", "RfTrackWritableScalarVariable"),
}


def __getattr__(name):
    if name not in _LAZY:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr_name = _LAZY[name]
    value = getattr(importlib.import_module(module_name), attr_name)
    globals()[name] = value
    return value
