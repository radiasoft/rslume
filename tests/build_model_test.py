"""rslume.rftrack.build_model: one variable per adjustable parameter of each
element kind, with its default read from the element

:copyright: Copyright (c) 2026 RadiaSoft LLC.  All Rights Reserved.
:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""


def test_unknown_kind():
    import RF_Track as rft
    import rslume.rftrack
    from pykern import pkunit
    from pykern.pkcollections import PKDict

    elements, lattice, bunch = _beamline(rft, [("drift", "D1", rft.Drift(0.1))])
    with pkunit.pkexcept("unsupported element kind='quad'"):
        rslume.rftrack.build_model([PKDict(kind="quad", name="D1")], lattice, bunch)


def test_variables():
    import numpy
    import RF_Track as rft
    import rslume.rftrack
    from pykern import pkunit

    qg = rft.Quadrupole(0.1, float("nan"), 0.0)
    qg.set_gradient(3.0)
    qk = rft.Quadrupole(0.1, float("nan"), 0.0)
    qk.set_strength(2.0)
    cor = rft.Corrector(0.1)
    cor.set_strength(1.5, -0.5)
    # an analytic cavity as Sirepo builds it: G cos(n pi z / l), two cells
    z = numpy.linspace(0.0, 0.1, 81)
    an = rft.RF_FieldMap_1d(
        (1e6 * numpy.cos(2 * numpy.pi * z / 0.1)).astype(complex),
        z[1] - z[0],
        0.1,
        3e9,
        +1,
    )
    an.set_phid(12.0)
    fm = rft.RF_FieldMap_1d(
        (1e6 * numpy.sin(numpy.linspace(0, numpy.pi, 21))).astype(complex),
        0.01,
        0.2,
        1.3e9,
        1.0,
        1.0,
        1.0,
    )
    fm.set_phid(7.0)
    sol = rft.Solenoid(0.1, 0.5, 0.05)
    elements, lattice, bunch = _beamline(
        rft,
        [
            ("drift", "D1", rft.Drift(0.1)),
            ("quadrupole_gradient", "QG", qg),
            ("quadrupole_k1", "QK", qk),
            ("corrector", "COR", cor),
            ("cavity_analytic", "AN", an),
            ("cavity_fieldmap", "FM", fm),
            ("solenoid_analytic", "SOL", sol),
            ("rbend", "B1", rft.SBend(0.2, 0.01, 100.0)),
            ("screen", "SCR", rft.Screen()),
        ],
    )
    pkunit.pkeq(
        [
            ("QG_gradient", "gradient", 3.0, "T/m"),
            ("QK_k1", "strength", 2.0, "1/m^2"),
            ("COR_hkick", "strength", 1.5, "T*mm"),
            ("COR_vkick", "strength", -0.5, "T*mm"),
            ("AN_phid", "phid", 12.0, "deg"),
            ("AN_p_actual", "P_actual", 1.0, "W"),
            ("FM_phid", "phid", 7.0, "deg"),
            ("FM_p_actual", "P_actual", 1.0, "W"),
            ("SOL_max_current", "max_current", round(sol.get_max_current(), 12), "A"),
            ("B1_angle", "angle", 0.01, "rad"),
        ],
        [
            # RF-Track returns the corrector's vkick as -0.4999999999999999
            (n, v.attribute, round(v.default_value, 12), v.unit)
            for n, v in rslume.rftrack.build_model(
                elements, lattice, bunch
            ).supported_variables.items()
        ],
    )


def _beamline(rft, kind_name_element):
    """`[PKDict(kind, name)]`, a Lattice of the elements, and a
    one-particle bunch."""
    import numpy
    from pykern.pkcollections import PKDict

    elements = []
    lattice = rft.Lattice()
    for kind, name, e in kind_name_element:
        e.set_name(name)
        lattice.append(e)
        elements.append(PKDict(kind=kind, name=name))
    return (
        elements,
        lattice,
        rft.Bunch6d(
            numpy.array(
                [[0.0, 0.0, 0.0, 0.0, 0.0, 100.0, rft.electronmass, -1.0, 1.0, 1]]
            )
        ),
    )
