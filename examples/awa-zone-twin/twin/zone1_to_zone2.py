"""Run the zone1->zone2 chain once and print what each zone produced.

A quick sanity check of `build_chain()` without Phoebus or lume-pva in the loop. Zone1's own build
(field-map I/O, autophase, and a space-charge-tracked run) takes about a
minute at the default particle count; this is expected, not a hang.
"""

from zone_model import build_chain


def main():
    chain = build_chain()
    zone1, zone2 = chain.lume_model_instances

    print("zone1 (source, no injection needed):")
    z1 = zone1.get(["zone1_charge_pC", "zone1_energy_MeV", "zone1_energy_spread_pct"])
    print(f"  charge        = {z1['zone1_charge_pC']:.3f} pC")
    print(f"  energy        = {z1['zone1_energy_MeV']:.3f} MeV")
    print(f"  energy spread = {z1['zone1_energy_spread_pct']:.4f} %")

    # Drive the chain once, same as a StagedModel.set() would on any put --
    # this injects zone1's final_particles into zone2 and tracks it there.
    chain.set({})

    print("zone2 (after zone1's bunch is injected and tracked):")
    z2 = zone2.get(["zone2_charge_pC", "zone2_energy_MeV", "zone2_energy_spread_pct"])
    print(f"  charge        = {z2['zone2_charge_pC']:.3f} pC")
    print(f"  energy        = {z2['zone2_energy_MeV']:.3f} MeV")
    print(f"  energy spread = {z2['zone2_energy_spread_pct']:.4f} %")

    print(
        "\nzone2 has no RF cavities (just drifts/quads/correctors), so its "
        "energy and charge should match zone1's to the particle-tracking "
        "noise floor -- that agreement is the chain's own sanity check."
    )


if __name__ == "__main__":
    main()
