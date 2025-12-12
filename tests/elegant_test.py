"""rslume.elegant tests

:copyright: Copyright (c) 2025 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def test_archive():
    from pykern import pkio, pkunit, pkdebug
    import numpy
    import rslume.elegant

    for d in pkio.sorted_glob(pkunit.data_dir().join("*")):
        w = pkunit.work_dir().join(d.basename)
        pkio.mkdir_parent(w)
        E = rslume.elegant.Elegant(
            d.join("elegant.ele"),
            workdir=w,
            use_temp_dir=False,
        )
        E.cmd("bunched_beam").use_twiss_command_values = 1
        E.el("QD").k1 = 0.65
        E.run()
        cols = ("s", "betax", "betaxBeam", "betayBeam", "betay")
        n = "stats.csv"
        numpy.savetxt(
            w.join(n),
            numpy.array([E.output.stats[c] for c in cols]).T,
            delimiter=",",
            header=",".join(cols),
            comments="",
        )
        P = E.output["particles"]["final_particles"]
        P.write(str(w.join("final_particles.h5")))
        pkunit.pkeq(999.999915, round(P["mean_energy"] * 1e-6, 6))
        pkunit.pkeq("eV", str(P.units("mean_energy")))
        E.output["particles"]["W1"].write(str(w.join("W1.h5")))
        for f in (n, "elegant.ele", "elegant.lte"):
            pkunit.file_eq(d.join(f"{n}.out"), actual_path=w.join(n))
        a = str(w.join("archive.h5"))
        E.archive(a)

        E2 = rslume.Elegant()
        E2.load_archive(a)
        pkunit.pkeq(E.output.stats.betax[-1], E2.output.stats.betax[-1])
        pkunit.pkeq(E.output.particles.W1, E2.output.particles.W1)
