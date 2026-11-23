import importlib

# Each wrapper is imported lazily (PEP 562) so that one wrapper's broken or
# missing dependency (e.g. lume-genesis/openpmd-beamphysics version drift)
# only fails when that specific wrapper is used, not for every import of
# rslume or of an unrelated wrapper.
_LAZY = {
    "Elegant": ("rslume.elegant", "Elegant"),
    "Genesis2": ("rslume.genesis2", "Genesis2"),
    "OPAL": ("rslume.opal", "OPAL"),
}

# Names rslume's RF-Track wrapper exported before it moved to lume-rftrack:
# importing rslume.rftrack raises an ImportError saying where it went
_MOVED_TO_LUME_RFTRACK = frozenset(
    (
        "LUMERFTrackModel",
        "RFTrackReadOnlyScalarVariable",
        "RFTrackSimulator",
        "RFTrackWritableScalarVariable",
        "RFTrackWritableVectorComponentVariable",
        "build_model",
    )
)

__all__ = sorted(_LAZY)


def __dir__():
    return sorted(set(globals()) | set(_LAZY))


def __getattr__(name):
    if name in _MOVED_TO_LUME_RFTRACK:
        importlib.import_module("rslume.rftrack")
    if name not in _LAZY:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr_name = _LAZY[name]
    value = getattr(importlib.import_module(module_name), attr_name)
    globals()[name] = value
    return value
