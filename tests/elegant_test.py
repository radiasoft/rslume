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
        cols = ("s", "pCentral0", "betax", "betaxBeam", "betay", "betayBeam")
        n = "stats.csv"
        numpy.savetxt(
            w.join(n),
            numpy.array([E.output.stats[c] for c in cols]).T,
            delimiter=",",
            header=",".join([f"{c} [{E.output.stats_unit[c]}]" for c in cols]),
            comments="",
            fmt="%.6e",
        )
        P = E.output["particles"]["final_particles"]
        P.write(str(w.join("final_particles.h5")))
        pkunit.pkeq("999.999915", f"{P['mean_energy'] * 1e-6:.6f}")
        pkunit.pkeq("eV", str(P.units("mean_energy")))
        E.output["particles"]["W1"].write(str(w.join("W1.h5")))
        for f in (n, "elegant.ele", "elegant.lte"):
            pkunit.file_eq(d.join(f"{f}.out"), actual_path=w.join(f))
        a = str(w.join("archive.h5"))
        E.archive(a)

        E2 = rslume.Elegant()
        E2.load_archive(a)
        pkunit.pkeq(E.output.stats.betax[-1], E2.output.stats.betax[-1])
        pkunit.pkeq(E.output.particles.W1, E2.output.particles.W1)
        pkunit.pkeq(
            E._input.models.bunch.p_central_mev, E2._input.models.bunch.p_central_mev
        )


def test_labels():
    from pykern import pkio, pkunit, pkdebug
    from rslume.elegant import ElegantLabel

    for case in (
        ("$gb$r$bx$n", r"\beta _x"),
        ("$ga$r$bc2$n", r"\alpha _{c2}"),
        ("1/(2$gp$r)", r"1/(2\pi )"),
        ("m$be$nc", r"m_ec"),
        ("$gc$r$by2$n", r"\eta _{y2}"),
        ("$gc$r$bx3$n$a'$n", r"\eta _{x3}^\prime "),
        ("$ga$r$bx,beam$n", r"\alpha _{x,beam}"),
        ("y'$bmax$n", r"y\prime _{max}"),
        ("$gc$r$by3$n$a'$n", r"\eta _{y3}^\prime "),
        ("max$sb$e$gD$rt$sb$e", r"max| \Delta t| "),
    ):
        pkunit.pkeq(case[1], ElegantLabel.to_katex(case[0]))
