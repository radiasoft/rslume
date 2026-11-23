"""rslume.rftrack moved to lume-rftrack

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def test_import_says_where_it_moved():
    from pykern import pkunit

    with pkunit.pkexcept("moved to lume-rftrack"):
        import rslume.rftrack  # noqa: F401


def test_old_names_say_where_they_moved():
    from pykern import pkunit

    import rslume

    for n in ("RFTrackSimulator", "build_model", "LUMERFTrackModel"):
        with pkunit.pkexcept("moved to lume-rftrack"):
            getattr(rslume, n)
    pkunit.pkok("RFTrackSimulator" not in rslume.__all__, "__all__={}", rslume.__all__)
