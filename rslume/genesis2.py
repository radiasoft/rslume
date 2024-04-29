"""RadiaSoft additions to LUME genesis 2 interface

:license: http://www.apache.org/licenses/LICENSE-2.0.html
"""

import genesis.genesis2
import numpy
import os
import pmd_beamphysics.interfaces.genesis
import pmd_beamphysics.particles
import pmd_beamphysics.units


class Genesis2(genesis.genesis2.Genesis2):

    # override lume-genesis write_input() and final_particles()

    def write_input(self):
        self.write_initial_particles()
        super().write_input()

    def final_particles(self):
        # compute required wavelengths to hold the whole beam and center at 0
        if "dpa" not in self.output["data"]:
            return None
        d = self.output["data"]["dpa"]
        d[:, 1, :] -= numpy.min(d[:, 1, :])
        v = pmd_beamphysics.particles.ParticleGroup(
            data=pmd_beamphysics.interfaces.genesis.genesis2_dpa_to_data(
                d,
                xlamds=self["xlamds"],
                current=self.output["data"]["current"],
                zsep=numpy.max(d[:, 1, :]) / (2 * numpy.pi),
            )
        )
        # center psi
        v.t -= numpy.mean(v.t)
        return v

    def write_initial_particles(self, filename="inpart.dat"):
        particle_group = self.initial_particles
        if not particle_group:
            return
        filepath = os.path.join(self.workdir, filename)

        # gamma
        # ct * 2pi / xlamds
        # x
        # y
        # ux (gamma * beta_x)
        # uy (gamma * beta_y)

        d = numpy.zeros((6, len(particle_group.x)))
        d[0] = particle_group.gamma
        d[1] = (
            particle_group.t
            * pmd_beamphysics.units.c_light
            * 2
            * numpy.pi
            / self["xlamds"]
        )
        d[1] -= numpy.mean(d[1])
        d[2] = particle_group.x
        d[3] = particle_group.y
        d[4] = particle_group.gamma * particle_group.beta_x
        d[5] = particle_group.gamma * particle_group.beta_y

        self["partfile"] = filename
        self["gamma0"] = numpy.mean(particle_group.gamma)
        self["delgam"] = self["gamma0"] * 1e-3
        self["ippart"] = 0
        self["ipradi"] = 0
        factor = 4 * self["nbins"]
        self["npart"] = int(len(particle_group.x) / factor) * factor
        d = d[:, : self["npart"]]

        with open(filepath, "wb") as f:
            d.tofile(f)
