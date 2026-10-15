"""rslume.rftrack_archive: whether each element's aperture was set
survives the archive round trip

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def test_aperture_round_trip():
    import h5py
    import numpy
    import RF_Track as rft
    from pykern import pkunit
    from rslume.rftrack_simulator import RFTrackSimulator

    path = str(pkunit.empty_work_dir().join("aperture.h5"))
    lattice = rft.Lattice()
    unset = rft.Drift(0.1)
    unset.set_name("unset")
    lattice.append(unset)
    aperture_set = rft.Drift(0.1)
    aperture_set.set_name("set")
    aperture_set.set_aperture(0.01, 0.02, "circular")
    lattice.append(aperture_set)
    # a Pillbox_Cavity's default aperture is not RF-Track's usual -0.001
    cavity = rft.Pillbox_Cavity(numpy.zeros(1), 3e9, 0.05, 2)
    cavity.set_name("cavity")
    lattice.append(cavity)
    RFTrackSimulator(
        lattice,
        rft.Bunch6d(
            numpy.array(
                [[0.0, 0.0, 0.0, 0.0, 0.0, 100.0, rft.electronmass, -1.0, 1.0, 1]]
            )
        ),
    ).archive(path)
    with h5py.File(path, "r") as f:
        pkunit.pkeq(
            [False, True, False],
            [bool(f["elements"][str(i)].attrs["aperture_set"]) for i in range(3)],
        )
    reloaded = RFTrackSimulator()
    reloaded.load_archive(path)
    for i in range(3):
        pkunit.pkeq(
            (lattice[i].get_aperture_x(), lattice[i].get_aperture_y()),
            (
                reloaded.beamline[i].get_aperture_x(),
                reloaded.beamline[i].get_aperture_y(),
            ),
        )
