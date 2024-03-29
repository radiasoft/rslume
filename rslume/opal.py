"""LUME interface for OPAL

:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

from pmd_beamphysics import ParticleGroup
from pykern.pkcollections import PKDict
import h5py
import numpy
import os
import pmd_beamphysics.interfaces.opal
import rslume.wrapper

class OPAL(rslume.wrapper.SirepoWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(
            sim_type="opal",
            command="opal",
            #TODO(pjm): proper mpi exec command w/cores
            command_mpi="mpiexec -n 4 opal",
            run_env=None,
            *args,
            **kwargs,
        )

    # --- lume-base implementation ---

    def load_output(self):
        self.output = {}
        with h5py.File(os.path.join(self.path, "opal.h5"), "r") as f:
            self.output["particles"] = ParticleGroup(
                #TODO(pjm): get last Step
                data=pmd_beamphysics.interfaces.opal.opal_to_data(f["/Step#0"]),
            )

    # -- RS addition

    def set_particle_input(self, particle_group, filename='in.dat'):
        filepath = os.path.join(self.workdir, filename)
        pmd_beamphysics.interfaces.opal.write_opal(
            particle_group,
            filepath,
            dist_type="emitted",
            verbose=True,
        )
        d = self.cmd("distribution")
        d.type = "FROMFILE"
        d.fname = filename
        d.emitted = "1"
        b = self.cmd("beam")
        b.npart = particle_group.n_particle
        b.gamma = 0
        b.energy = 0
        b.pc = numpy.mean(particle_group.p) * 1e-9
