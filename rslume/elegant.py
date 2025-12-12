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
import rslume.wrapper


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

    def fix_deprecated_n_kicks(self):
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

    # --- lume-base implementation ---

    def archive(self, h5=None):

        def _particle_data(group):
            b = self.cmd("sdds_beam", required=False) or self.cmd(
                "bunched_beam", required=False
            )
            if b:
                p = None
                if b._type == "sdds_beam":
                    _particle_group_from_sdds(b.input, group, "initial_particles")
                elif b.bunch:
                    _particle_group_from_sdds(
                        "bunched_beam.bunch.sdds", group, "initial_particles"
                    )
            g = group.create_group("particles")
            _particle_group_from_sdds("run_setup.output.sdds", g, "final_particles")
            for el in self._input.models.elements:
                if el.type == "WATCH" and el.filename:
                    _particle_group_from_sdds(
                        f"{el.name}.filename-001.sdds", g, el.name
                    )

        def _particle_group_from_sdds(filename, parent, name):
            n = pykern.pkio.py_path(self.path).join(filename)
            if n.exists():
                ParticleGroup(
                    data=pmd_beamphysics.interfaces.elegant.elegant_to_data(str(n))
                ).write(parent, name)

        def _stat_data(group):
            for c in self.output.stats:
                ds = group.create_dataset(c, data=self.output.stats[c])
                ds.attrs["unitSymbol"] = self.output.stats_unit[c]

        assert isinstance(h5, str)
        with h5py.File(h5, "w") as f:
            g = f.create_group("elegant")
            _stat_data(g.create_group("stats"))
            _particle_data(g)
        return h5

    def load_archive(self, h5):
        # TODO(pjm): init outputs
        self.output = PKDict(
            stats=PKDict(),
            stats_unit=PKDict(),
            particles=PKDict(),
        )
        with h5py.File(h5, "r") as f:
            for c in f["/elegant/stats"]:
                self.output.stats[c] = f[f"/elegant/stats/{c}"][:]
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
                self.output.particles[name] = ParticleGroup(
                    data=pmd_beamphysics.interfaces.elegant.elegant_to_data(str(p)),
                )

        self.output = PKDict(
            particles=PKDict(),
            stats=PKDict(),
            stats_unit=PKDict(),
        )
        _particles("final_particles", "run_setup.output.sdds")
        for el in self._input.models.elements:
            if el.type == "WATCH" and el.filename:
                _particles(el.name, el.filename.replace("%03ld", "001"))
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
                    self.output.stats_unit[c] = v.column_def[1]
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
