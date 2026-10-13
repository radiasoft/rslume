"""rslume.rftrack_simulator.RFTrackSimulator.archive()/load_archive() round-trip test
for a Bunch6dT initial bunch (e.g. a Cathode Emission distribution),
distinct from x_band_fodo_archive_test.py's Bunch6d coverage.

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

_RANDOM_SEED = 5489


def _build_bunch(rft):
    t = rft.Bunch6dT_twiss()
    t.beta_x = 0.01
    t.alpha_x = 0.0
    t.emitt_x = 1e-6
    t.beta_y = 0.01
    t.alpha_y = 0.0
    t.emitt_y = 1e-6
    t.beta_z = 0.01
    t.alpha_z = 0.0
    t.emitt_z = 1e-6
    t.sigma_z = 0.1
    t.sigma_pz = 1.0
    # the precise electron mass (not a truncated 0.511): archive() now
    # converts through a beamphysics ParticleGroup, which needs this to
    # match beamphysics' own electron mass constant closely enough for
    # species inference (rslume.rftrack_utils._infer_particlegroup_species).
    return rft.Bunch6dT(0.51099895069, 1e9, -1, 0.5, t, 10000)


def _build_volume(rft):
    d = rft.Drift(0.1)
    d.set_name("D0")
    v = rft.Volume()
    v.add(d, 0, 0, 0, 0, 0, 0)
    v.set_s0(0)
    v.set_s1(0.1)
    return v


def test_bunch6dt_archive_round_trip():
    import RF_Track as rft
    from pykern import pkunit
    from rslume.rftrack_simulator import RFTrackSimulator

    w = pkunit.empty_work_dir()
    path = str(w.join("archive.h5"))

    original = RFTrackSimulator(_build_volume(rft), _build_bunch(rft))
    original.archive(path)

    # the archive is plain, self-describing HDF5 -- not something that
    # requires importing this module to read back. It's also a real
    # standalone openPMD particle file (archive()'s own docstring).
    import h5py

    with h5py.File(path, "r") as f:
        pkunit.pkeq("rslume", f.attrs["software"])
        pkunit.pkeq("Bunch6dT", f.attrs["bunch_type"])
        pkunit.pkeq(b"openPMD", f.attrs["dataType"])
        pkunit.pkok("particles" in f, "expected a particles group")

    reloaded = RFTrackSimulator()
    reloaded.load_archive(path)
    pkunit.pkeq("Bunch6dT", type(reloaded.initial_bunch).__name__)

    # The exact same macroparticles come back (see archive()'s own
    # docstring) -- compare the real phase space, not just statistics.
    o = original.initial_bunch.get_phase_space("%X %Y %Z %Px %Py %Pz")
    r = reloaded.initial_bunch.get_phase_space("%X %Y %Z %Px %Py %Pz")
    pkunit.pkok(
        (abs(o - r) < 1e-6 * (abs(o) + 1e-9)).all(),
        "phase space differs too much: original={} reloaded={}",
        o,
        r,
    )
