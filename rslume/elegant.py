"""LUME interface for elegant

:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from pmd_beamphysics import ParticleGroup
from pykern.pkcollections import PKDict
from pykern.pkdebug import pkdc, pkdexc, pkdlog, pkdp
from sirepo.template import elegant_common
from sirepo.template import sdds_util
import h5py
import os
import pmd_beamphysics.interfaces.elegant
import pykern.pkio
import pykern.pkjson
import re
import rslume.wrapper
import string


class Elegant(rslume.wrapper.SirepoWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(
            sim_type="elegant",
            command="elegant",
            command_mpi="Pelegant",
            run_env=elegant_common.subprocess_env(),
            *args,
            **kwargs,
        )

    def fix_deprecated_elements(self):
        for e in self._input.models.elements:
            if "n_kicks" in e and "n_slices" in e and e.n_kicks != 4:
                e.n_slices = e.n_kicks
                e.n_kicks = 4

    def run_twiss_only(self):
        original_commands = self._input.models.commands
        new_commands = []
        for c in original_commands:
            if c._type in ("run_setup", "run_control", "twiss_output"):
                new_commands.append(c.copy())
        self._input.models.commands = new_commands
        self.cmd("run_setup").magnets = ""
        self.run()
        self._input.models.commands = original_commands

    def slice(self, start_name, end_name=None):
        def el_id(name):
            if name is None:
                return None
            r = self.el(name)
            assert r
            return r._id

        # assuming 1 beamline for now, would need to flatten beamline otherwise
        assert len(self._input.models.beamlines)
        start_el = el_id(start_name)
        assert start_el
        end_el = el_id(end_name)
        r = []
        in_start = False
        for b in self._input.models.beamlines[0]["items"]:
            if not in_start:
                if b == start_el:
                    in_start = True
                elif self.el_for_id(b).type == "CHARGE":
                    # TODO(pjm): certain elements should not get trimmed
                    pass
                elif b != start_el:
                    continue
            r.append(b)
            if b == end_el:
                break
        self._input.models.beamlines[0]["items"] = r

    def set_watches(self, names):
        """Clears existing watches and enables the named ones. Converts MARK to WATCH if necessary."""
        for el in self._input.models.elements:
            if el.name in names:
                if el.type == "MARK":
                    el.type = "WATCH"
                el.filename = "1"
            elif el.type == "WATCH":
                el.type = "MARK"

    # --- lume-base implementation ---

    def archive(self, h5=None):

        def _particle_data(group):
            g = group.create_group("particles")
            for n in self.output.particles:
                self.output.particles[n].write(g, n)

        def _stat_data(group):
            for c in self.output.stats:
                ds = group.create_dataset(c, data=self.output.stats[c])
                ds.attrs["unitSymbol"] = self.output.stats_unit[c]
                ds.attrs["label"] = self.output.stats_label[c]

        assert isinstance(h5, str)
        with h5py.File(h5, "w") as f:
            g = f.create_group("elegant")
            _stat_data(g.create_group("stats"))
            _particle_data(g)
            g.attrs["lattice"] = pykern.pkjson.dump_pretty(self._input.models)
        return h5

    def load_archive(self, h5):
        self._init_output()
        self._input = self.create_input()
        with h5py.File(h5, "r") as f:
            self._input.models = pykern.pkjson.load_any(f["/elegant"].attrs["lattice"])
            for c in f["/elegant/stats"]:
                self.output.stats[c] = f[f"/elegant/stats/{c}"][:]
                self.output.stats_unit[c] = f[f"/elegant/stats/{c}"].attrs["unitSymbol"]
                self.output.stats_label[c] = f[f"/elegant/stats/{c}"].attrs["label"]
            if "initial_particles" in f:
                self.initial_particles = ParticleGroup(h5=f["initial_particles"])
            for p in f["/elegant/particles"]:
                self.output.particles[p] = ParticleGroup(
                    h5=f[f"/elegant/particles/{p}"]
                )

    def load_output(self):
        def _particles(name, filename):
            p = pykern.pkio.py_path(self.path).join(filename)
            if p.exists():
                P = ParticleGroup(
                    data=pmd_beamphysics.interfaces.elegant.elegant_to_data(
                        # TODO(pjm): use charge at position
                        str(p),
                        charge=(
                            self.output.stats.Charge[-1]
                            if "Charge" in self.output.stats
                            else 1
                        ),
                    ),
                )
                self.output.particles[name] = P

        self._init_output()
        for n in (
            "run_setup.centroid.sdds",
            "run_setup.sigma.sdds",
            "twiss_output.filename.sdds",
        ):
            f = pykern.pkio.py_path(self.path).join(n)
            if f.exists():
                s = sdds_util.extract_sdds_column(str(f), "s", 0)
                for c in s.column_names:
                    v = sdds_util.extract_sdds_column(str(f), c, 0)
                    self.output.stats[c] = v["values"]
                    self.output.stats_unit[c] = ElegantLabel.to_katex(v.column_def[1])
                    self.output.stats_label[c] = ElegantLabel.to_katex(
                        v.column_def[0] or c
                    )

        if b := self.cmd("sdds_beam", required=False):
            _particles("initial_particles", b.input)
        elif b := self.cmd("bunched_beam", required=False):
            _particles("initial_particles", "bunched_beam.bunch.sdds")
        _particles("final_particles", "run_setup.output.sdds")
        for el in self._input.models.elements:
            if el.type == "WATCH" and el.filename:
                # TODO(pjm): use sirepo.lib to get the filename
                _particles(el.name, f"{el.name}.filename-001.sdds")
        # TODO(pjm): load warnings and errors from log

    def write_initial_particles(self, filename="in.sdds"):
        particle_group = self.initial_particles
        if not particle_group:
            return
        filepath = os.path.join(self.workdir, filename)
        pmd_beamphysics.interfaces.elegant.write_elegant(
            particle_group,
            filepath,
            verbose=True,
        )
        if self.cmd("bunched_beam", required=False):
            for idx, v in enumerate(self._input.models.commands):
                if v._type == "bunched_beam":
                    i = v._id
                    self._input.models.commands[idx] = PKDict(
                        _id=i,
                        _type="sdds_beam",
                        input=filename,
                    )
                    break
        beam = self.cmd("sdds_beam")
        beam.input = filename
        beam.center_arrival_time = "1"
        # don't automatically center_transversely as so beam offsets can be tested between simulations
        # beam.center_transversely = '1'
        # beam.reverse_t_sign = "1"
        self.cmd("run_setup").expand_for = filename

    def _init_output(self):
        self.output = PKDict(
            particles=PKDict(),
            stats=PKDict(),
            stats_unit=PKDict(),
            stats_label=PKDict(),
        )


class ElegantLabel:

    # greek, end-greek, special, end-special
    _FONTS = set(("g", "r", "s", "e"))
    _CHARACTERS = PKDict(
        g=PKDict(
            a=r"\alpha",
            b=r"\beta",
            c=r"\eta",
            d=r"\delta",
            e=r"\epsilon",
            f=r"\varphi",
            g=r"\gamma",
            h=r"\chi",
            i=r"\iota",
            j=r"\iota",
            k=r"\kappa",
            l=r"\lambda",
            m=r"\mu",
            n=r"\nu",
            o=r"\omicron",
            p=r"\pi",
            q=r"\vartheta",
            r=r"\rho",
            s=r"\sigma",
            t=r"\tau",
            u=r"\upsilon",
            v=r"\chi",
            w=r"\omega",
            x=r"\xi",
            y=r"\psi",
            z=r"\zeta",
            F=r"\Phi",
            Q=r"\Theta",
        ),
        # add additional as needed
        s=PKDict(
            b="|",
        ),
    )

    for c in string.ascii_uppercase:
        if c not in _CHARACTERS.g:
            v = _CHARACTERS.g[c.lower()]
            _CHARACTERS.g[c] = v[0] + v[1].upper() + v[2:]

    _TAGS = PKDict(
        a="^{",
        b="_{",
        n="}",
    )

    @classmethod
    def to_katex(cls, value):
        """Map elegant greek codes to KaTeX equivalent"""
        res = ""
        font = "r"
        is_tag = False

        for c in value:
            if c == "$":
                if is_tag:
                    raise AssertionError("Already within elegant $ tag")
                is_tag = True
            elif is_tag:
                if c in cls._TAGS:
                    res += cls._TAGS[c]
                elif c in cls._FONTS:
                    font = c
                    if c in ("r", "e"):
                        res += " "
                else:
                    raise AssertionError(f"Unexpected special character: {c}")
                is_tag = False
            elif font in cls._CHARACTERS:
                res += cls._CHARACTERS[font][c]
            else:
                res += c

        # simplify single character values
        res = re.sub(r"\{(.)\}", r"\1", res)
        res = re.sub(r"'", r"\\prime ", res)
        return res
