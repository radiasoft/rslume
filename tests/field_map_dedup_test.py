"""RFTrackSimulator.archive()/load_archive() field-map deduplication:
several elements built from the same field-map array (e.g. a linac's
identical accelerating cavities, all from one uploaded file) should be
archived with one shared copy, not a byte-for-byte duplicate per element.

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def _build_volume(rft, numpy):
    ez = numpy.zeros(21)
    ez[10] = 1e7
    cavities = []
    for name in ("L1", "L2", "L3"):
        c = rft.RF_FieldMap_1d(ez, 0.01, 0.2, 1.3e9, 1)
        c.set_name(name)
        c.set_phid(10.0)
        cavities.append(c)
    v = rft.Volume()
    for i, c in enumerate(cavities):
        v.add(c, 0, 0, i * 0.3, 0, 0, 0)
    v.set_s0(0)
    v.set_s1(0.8)
    return v


def test_field_map_dedup():
    import h5py
    import numpy
    import RF_Track as rft
    from pykern import pkunit
    import rftrack_util
    from rslume.rftrack_simulator import RFTrackSimulator

    path = str(pkunit.empty_work_dir().join("archive.h5"))

    original = RFTrackSimulator(
        _build_volume(rft, numpy), rftrack_util.twiss_bunch(rft, 100.0, 50)
    )
    original.archive(path)

    with h5py.File(path, "r") as f:
        # one shared dataset, not three byte-for-byte duplicates
        pkunit.pkeq(1, len(f["field_maps"]))
        refs = {
            f["elements"][str(i)].attrs["name"]: f["elements"][str(i)].attrs["ez"]
            for i in range(3)
        }
        pkunit.pkeq(3, len(refs))
        pkunit.pkeq(
            1,
            len({v for v in refs.values()}),
            "all three should reference the same array",
        )

    reloaded = RFTrackSimulator()
    reloaded.load_archive(path)
    pkunit.pkeq(3, reloaded.beamline.size())
    for i in range(3):
        pkunit.pkeq(original.beamline[i].get_phid(), reloaded.beamline[i].get_phid())
        pkunit.pkeq(
            list(original.beamline[i].get_field(0.0, 0.0, 100.0, 0.0)[0]),
            list(reloaded.beamline[i].get_field(0.0, 0.0, 100.0, 0.0)[0]),
        )
