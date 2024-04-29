"""LUME interface for Sirepo lattice apps

:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

# TODO(pjm): work-around until https://github.com/radiasoft/sirepo/issues/6632 is addressed
import os

os.environ["SIREPO_FEATURE_CONFIG_SIM_TYPES"] = "elegant:opal"

from pykern import pkio, pksubprocess
from pykern.pkdebug import pkdlog
import lume.base
import sirepo.lib


class SirepoWrapper(lume.base.CommandWrapper):

    def __init__(self, *args, **kwargs):
        self.sim_type = kwargs["sim_type"]
        self.run_env = kwargs["run_env"]
        self.update_filenames = kwargs.get("update_filenames", False)
        if "update_filenames" in kwargs:
            self.update_filenames = kwargs["update_filenames"]
            del kwargs["update_filenames"]
        del kwargs["sim_type"]
        del kwargs["run_env"]
        super().__init__(*args, **kwargs)
        if not self.input_file:
            raise AssertionError("Missing input_file argument")
        self.load_input(self.input_file)
        self.configure()

    def archive(self, h5=None):
        raise NotImplementedError("archive() not yet implemented.")

    def configure(self):
        self.setup_workdir(self._workdir)

    def input_parser(self, path):
        return sirepo.lib.Importer(
            self.sim_type,
            update_filenames=self.update_filenames,
        ).parse_file(path)

    def load_archive(self, h5, configure=True):
        raise NotImplementedError("load_archive() not yet implemented.")

    def run(self):
        runscript = self.get_run_script(write_to_path=False)
        self.vprint(f"Running '{runscript}' in {self.path}")
        self.write_input()
        with pkio.save_chdir(self.path):
            pksubprocess.check_call_with_signals(
                runscript,
                msg=pkdlog,
                output=f"{self.sim_type}.log",
                env=self.run_env,
            )
        self.load_output()

    def plot(self):
        raise NotImplementedError("plot() not yet implemented.")

    def write_input(self):
        self.write_initial_particles()
        self._input.write_files(self.path)

    # Sirepo lattice and command accessors

    def cmd(self, command_name, count=0, required=True):
        return self._find_by_field(
            "commands", "_type", command_name, count=count, required=required
        )

    def el(self, element_name, required=True):
        return self._find_by_field("elements", "name", element_name, require=required)

    def final_particles(self):
        if "particles" in self.output:
            return self.output["particles"]
        return None

    def _find_by_field(self, container, field, name, count=0, required=True):
        c = 0
        for v in self._input.models[container]:
            if v[field] == name:
                if c == count:
                    return v
                c += 1
        if required:
            raise AssertionError(f"unknown name: {name}")
        return None
