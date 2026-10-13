"""rslume.rftrack_simulator.RfTrackSimulator.archive()/load_archive() round-trip test,
against the same "X-band Linac FODO Cell" lattice used by x_band_fodo_test.py.

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

_RANDOM_SEED = 5489


def _relative_diff(a, b):
    return abs(a - b) / abs(a)


def test_archive_round_trip():
    import RF_Track as rft
    from pykern import pkunit
    from rslume.rftrack_simulator import RfTrackSimulator
    from x_band_fodo_test import _build_bunch, _build_lattice

    w = pkunit.empty_work_dir()
    path = str(w.join("archive.h5"))

    rft.rng_set_seed(_RANDOM_SEED)
    original = RfTrackSimulator(_build_lattice(rft), _build_bunch(rft))
    original.track()
    original.archive(path)

    # the archive is plain, self-describing HDF5 -- not something that
    # requires importing this module to read back (that's the whole point:
    # it's the interchange contract with e.g. Sirepo's rftrack import)
    import h5py

    with h5py.File(path, "r") as f:
        # also a real standalone openPMD particle file (archive()'s own
        # docstring) -- "dataType" is openPMD's own root attr, not ours.
        pkunit.pkeq(b"openPMD", f.attrs["dataType"])
        pkunit.pkeq("rslume", f.attrs["software"])
        pkunit.pkeq("Bunch6d", f.attrs["bunch_type"])
        pkunit.pkeq("Drift", f["elements"]["0"].attrs["class"])
        pkunit.pkeq("D0", f["elements"]["0"].attrs["name"])
        pkunit.pkeq("Pillbox_Cavity", f["elements"]["1"].attrs["class"])
        pkunit.pkok("particles" in f, "expected a particles group")

    # load_archive() fills in an otherwise-empty simulator, same calling
    # convention as rslume.elegant.Elegant()/load_archive() (and
    # lume.base.Base's in general)
    reloaded = RfTrackSimulator()
    reloaded.load_archive(path)
    reloaded.track()

    pkunit.pkeq(
        original.beamline.size(), reloaded.beamline.size(), "element count differs"
    )
    for i in range(original.beamline.size()):
        pkunit.pkeq(
            original.beamline[i].get_name(),
            reloaded.beamline[i].get_name(),
            "element {} name differs",
            i,
        )

    # The exact same macroparticles come back (see archive()'s own
    # docstring), so tracking them through the same reloaded beamline
    # reproduces the original tracked result almost exactly -- a loose
    # tolerance only for the float round trip through openPMD's own SI
    # units, not a statistical refit.
    for field in ("x", "y", "K"):
        o = original.tracked_bunch.get_phase_space(f"%{field}")
        r = reloaded.tracked_bunch.get_phase_space(f"%{field}")
        pkunit.pkok(
            _relative_diff(o.mean(), r.mean()) < 1e-4
            if abs(o.mean()) > 1e-9
            else abs(r.mean()) < 1e-9,
            "{} mean differs too much: original={} reloaded={}",
            field,
            o.mean(),
            r.mean(),
        )
        pkunit.pkok(
            _relative_diff(o.std(), r.std()) < 1e-4,
            "{} std differs too much: original={} reloaded={}",
            field,
            o.std(),
            r.std(),
        )
