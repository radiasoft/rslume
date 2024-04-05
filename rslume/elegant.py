"""LUME interface for elegant

:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

import rslume.wrapper
from pmd_beamphysics import ParticleGroup
from pykern import pkio, pksubprocess
from pykern.pkcollections import PKDict
from sirepo.template import elegant_common
import os
import pmd_beamphysics.interfaces.elegant


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

    # --- lume-base implementation ---

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

    # -- RS addition

    def set_particle_input(self, particle_group, filename='in.sdds'):
        filepath = os.path.join(self.workdir, filename)
        pmd_beamphysics.interfaces.elegant.write_elegant(
            particle_group,
            filepath,
            verbose=True,
        )
        if self.cmd('bunched_beam', required=False):
            for idx, v in enumerate(self._input.models.commands):
                if v._type == 'bunched_beam':
                    i = v._id
                    self._input.models.commands[idx] = PKDict(
                        _id=i,
                        _type='sdds_beam',
                        input=filename,
                    )
                    break
        beam = self.cmd('sdds_beam')
        beam.input = filename
        beam.center_arrival_time = '1'
        # don't automatically center_transversely as so beam offsets can be tested between simulations
        # beam.center_transversely = '1'
        beam.reverse_t_sign = '1'
        self.cmd('run_setup').expand_for = filename
