"""LUME interface for elegant

:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from pmd_beamphysics import ParticleGroup
from pykern import pkio, pksubprocess
from pykern.pkdebug import pkdlog
from sirepo.template import elegant_common
import lume.base
import os
import pmd_beamphysics.interfaces.elegant
import sirepo.lib


class Elegant(lume.base.CommandWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(
            command="elegant",
            command_mpi="Pelegant",
            *args,
            **kwargs,
        )
        if not self.input_file:
            raise AssertionError("Missing input_file argument")
        self.load_input(self.input_file)
        self.configure()

    # --- lume-base implementation ---

    def archive(self, h5=None):
        raise NotImplementedError("archive() not yet implemented.")

    def configure(self):
        self.setup_workdir(self._workdir)

    def input_parser(self, path):
        return sirepo.lib.Importer("elegant").parse_file(path)

    def load_archive(self, h5, configure=True):
        raise NotImplementedError("load_archive() not yet implemented.")

    def load_output(self):
        self.output = {}
        c = self.cmd("run_setup")
        if c.output:
            self.output["particles"] = ParticleGroup(
                data=pmd_beamphysics.interfaces.elegant.elegant_to_data(
                    os.path.join(self.path, c.output),
                ),
            )
        #TODO(pjm): load other sdds output files
        #TODO(pjm): load warnings and errors from log

    def plot(self):
        raise NotImplementedError("plot() not yet implemented.")

    def run(self):
        runscript = self.get_run_script(write_to_path=False)
        self.vprint(f"Running '{runscript}' in {self.path}")
        self.write_input()
        with pkio.save_chdir(self.path):
            pksubprocess.check_call_with_signals(
                runscript,
                msg=pkdlog,
                output="elegant.log",
                env=elegant_common.subprocess_env(),
            )
        self.load_output()

    def write_input(self):
        self._input.write_files(self.path)

    # --- elegant-specific interface ---

    def cmd(self, command_name, count=0):
        return self._find_by_field("commands", "_type", command_name, count)

    def el(self, element_name):
        return self._find_by_field("elements","name",  element_name)

    def final_particles(self):
        if "particles" in self.output:
            return self.output["particles"]
        return None

    def _find_by_field(self, container, field, name, count=0):
        c = 0
        for v in self._input.models[container]:
            if v[field] == name:
                if c == count:
                    return v
                c += 1
        raise AssertionError(f"unknown name: {name}")
