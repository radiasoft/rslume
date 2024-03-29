"""RadiaSoft additions to LUME genesis 2 interface

:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

import genesis.genesis2
import numpy
import os
import pmd_beamphysics.interfaces.genesis
import pmd_beamphysics.particles


class Genesis2(genesis.genesis2.Genesis2):

    # override lume-genesis final_particles()

    def final_particles(self):
        if "dpa" not in self.output["data"]:
            return None
        d = self.output["data"]["dpa"]
        d[:,1,:] -= numpy.min(d[:,1,:])
        v = pmd_beamphysics.particles.ParticleGroup(
            data=pmd_beamphysics.interfaces.genesis.genesis2_dpa_to_data(
                d, xlamds=self["xlamds"], current=self.output["data"]["current"],
                # compute required wavelengths to hold the whole beam
                zsep=numpy.max(d[:,1,:]) / (2 * numpy.pi),
            )
        )
        # center psi
        v.t -= numpy.mean(v.t)
        return v


    # -- RS addition

    def set_particle_input(self, particle_group, filename='inpart.dat'):
        filepath = os.path.join(self.workdir, filename)

        # pt ct x y ux uy

        # gamma
        # ct * 2pi / xlamds
        # x
        # y
        # ux (gamma * beta_x)
        # uy (gamma * beta_y)

        gamma = particle_group.gamma
        GBx = gamma*particle_group.beta_x
        GBy = gamma*particle_group.beta_y

        d = numpy.zeros((6, len(particle_group.x)))
        d[0] = gamma
        d[1] = particle_group.t * 2 * numpy.pi / self["xlamds"]
        d[1] -= numpy.mean(d[1])
        d[2] = particle_group.x
        d[3] = particle_group.y
        d[4] = GBx
        d[5] = GBy

        self["partfile"] = filename
        self["ippart"] = 0
        self["ipradi"] = 0
        factor = 4 * self["nbins"]
        self["npart"] = int(len(particle_group.x) / factor) * factor
        print(f'npart = {self["npart"]}')
        d = d[:, :self["npart"]]

        with open(filepath, "wb") as f:
            d.tofile(f)
