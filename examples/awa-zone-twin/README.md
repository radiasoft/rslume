# AWA zone1 -> zone2 twin demo

Chains AWA zone1 (the photoinjector/booster, an RF-Track `Volume`) into
zone2 (the quad/corrector transport line, an RF-Track `Lattice`): zone1's
tracked bunch becomes zone2's source beam. Both zones are served as EPICS
PVs and watched in Phoebus; changing a zone1 or zone2 parameter re-tracks
the chain and updates both zones' diagnostics.

Two things define its shape:

- No archive/selector step. RF-Track is fast enough to re-track both zones
  live on every change, so nothing needs pre-recording. "Fast
  enough" means zone2 (well under a second); zone1's own run -- field-map
  I/O, autophase, and space charge -- takes tens of seconds, still handled
  live (the put is acknowledged at once and the served values update when
  the track finishes), just not instant.
- Both zones are live-tunable, not just the downstream one.

## How the pieces fit

The physics is two Sirepo-generated scripts -- "AWA Zone 1" and
"AWA Zone 2" -- kept in `twin/sources/`.
Each defines `ELEMENTS`, `build_beamline()`, `build_bunch()`, `autophase()`,
`apply_space_charge()` and `build_model()`; the twin reuses them as they
are, so the lattice, bunch, autophase and space-charge setup come from
them (`twin/zone_model.py` execs them).

`twin/zone_model.py`'s `Zone1Model`/`Zone2Model` are `lume.model.LUMEModel`s
around each script's `build_model()` (an `rslume.rftrack.RfTrack`), which
already exposes every element with a live setter (gradient, k1, phid,
P_actual, hkick/vkick). Zone1's solenoids are the exception: their field is
rescaled when the element is built, so `Zone1Model` adds a
`<name>_scale_factor` variable for each that rebuilds the whole zone.
`build_chain()` returns `StagedModel([Zone1Model(), Zone2Model()])`; zone1's
tracked bunch becomes zone2's `initial_particles` on every `set()`, through
`rslume.rftrack_utils.bunch6dt_to_particlegroup()`
and `particlegroup_to_bunch6d()` (which drifts to a plane, so the bunch
length survives the handoff).

`twin/actions.py` holds the twin's own PVs as `lume.actions` variables, the
layer `virtual-accelerator`'s `cheetah/actions.py` plays over
`lume_cheetah`: each zone's `charge_pC`/`energy_MeV`/`energy_spread_pct`,
each screen's `<name>_image`, and zone1's `<name>_scale_factor`.

Space charge is zone1 only (zone2 is pure magnetic transport). Neither
script pins a thread count; `build_chain(threads=...)` sets one (default
14, capped at the machine's maximum). More threads is not always faster --
a zone1 build at 2000 particles measured 29 s at 4 threads and 47 s at 16 --
so try `serve.py --threads`.

`serving/serve.py` serves the chain's variables as PVs through `lume-pva`:
both zones' params read-write by default (`--read-only` to lock them),
each zone's three diagnostics read-only.

`phoebus/generate_zone_twin_display.py` generates a to-scale, clickable
synoptic (`zone_twin.bob`): each element is a colored
button at its real position along the beamline; clicking it opens a
small, reusable, generic editor (`cavity_controls.bob`,
`solenoid_controls.bob`, `corrector_controls.bob`, `quad_controls.bob`),
parameterized by macros carrying that element's own PV names, so one
editor file serves every device of that kind. There is no pre-built AWA
floor-plan to link against, so this one is built from the generated
scripts' own `ELEMENTS` tables (positions, lengths, and which PV each
element's kind controls).

A screen (YAG1-4, YAG5, YAG7) is drawn on the floor plan but not
clickable. Its image is
picked from the `ScreenTabs` column below the floor plan instead: a
`navtabs` widget (one tab per screen) that swaps a single embedded
`screen_view.bob` in place as you click a different tab. `screen_view.bob`
is an `image` widget on that screen's own `<name>_image` PV: a 64x64
histogram of the beam there (computed from `get_bunch_at_screens()` after
every track). The histogram's axis range is each screen's own
`_SCREEN_FOV_MM` entry in `twin/zone_model.py` -- sized to the beam at
nominal settings, not the screen's much larger mechanical size (e.g. YAG1
is mechanically 50.8 mm but its beam is under 1 mm sigma there) -- a large
enough retune can still outgrow it; regenerate with updated numbers if
that happens often for your settings.

## Install

Needs `rslume` (with RF-Track), plus `lume-pva` and a Phoebus 5.x build to
serve/view. No other lattice package is needed: the lattices are bundled
in `twin/sources/`.

## Run the twin

From this directory:

```bash
cd serving
python serve.py
```

Wait for `serving 65 variables` (zone1's first build -- field-map I/O,
autophase, and a space-charge-tracked run -- takes tens of seconds at the
default particle count) and leave the terminal open.

### Check the PVs (optional)

From another terminal, with the EPICS command-line tools:

```bash
pvget AWA:SIM:STATUS AWA:SIM:SolBF_scale_factor AWA:SIM:zone2_energy_MeV
```

Expect `Idle`, `0.0001` and about `63` (MeV). `AWA:SIM:STATUS` is `Idle` or
`Simulating`, and is `Simulating` while the twin re-tracks.

### Run the chain once, without a server

```bash
cd twin
python zone1_to_zone2.py
```

Prints zone1's and zone2's charge/energy; they should agree closely
(zone2 has no RF cavities, so energy and charge are conserved through it
-- a built-in sanity check of the chain, not just a status report).

### Open the display in Phoebus

Regenerate the display if `twin/zone_model.py`'s variables ever change:

```bash
cd phoebus
python generate_zone_twin_display.py
```

Then, with the server running, from the Phoebus product directory:

```bash
java -jar target/product-<version>.jar \
    -settings <repository>/rslume/examples/awa-zone-twin/phoebus/settings.ini \
    -resource <repository>/rslume/examples/awa-zone-twin/phoebus/zone_twin.bob
```

`settings.ini` disables Phoebus' `ResponsivenessMonitor` watchdog
(`ui_monitor_period=0`), which otherwise dumps every thread's stack trace
whenever the JavaFX UI thread doesn't respond within 500 ms -- expected,
not an error, but this environment's lack of GLX acceleration for the
remote display trips it often during startup. Leave the flag off if you'd
rather see those dumps (e.g. to diagnose an actual freeze).

- **Twin:** LED and text at the top right: `Idle` (green) or `Simulating`
  (amber) while the twin re-tracks.
- **Click any colored element** (cavity, solenoid, corrector, quadrupole)
  to open its controls in a popup window: a spinner, a slider and a
  readback for each of its parameters. Changing a zone1 element's
  parameter retracks both zones (several seconds); changing a zone2
  element's retracks only zone2 (well under a second).
- The two "Zone N exit" readback blocks below the legend show each
  zone's charge/energy/energy spread after its own last track.
- **"Screen images":** click a tab in the column below the readbacks to
  see that screen's beam image. Screens on the floor plan above are not
  themselves clickable.

To stop, press Ctrl-C in the server terminal and close Phoebus.

## Record changes with the EPICS Archiver Appliance

The twin assumes a quickstart Archiver Appliance (v2.5.0) with
mgmt/engine/etl/retrieval BPL all under `http://localhost:8008`. Start it, then register
the twin's PVs so it starts recording every change:

```bash
# from the Archiver Appliance directory, if not already running
./dist/quickstart-8008.sh -s -d run dist/apache-tomcat-11.0.26.tar.gz

# from this directory, with serve.py already running (see above)
cd archiver
python configure_archiver.py
```

`archiver/pvlist.py` is the PV list both this and `restore.py` use --
the scalar names of `twin/zone_model.py`'s variables, so it always matches
what `serve.py` actually serves (59 names; `tests/archiver_test.py` checks it). A newly-registered PV shows
`"Initial sampling"` from the appliance's status UI
(`http://localhost:8008/mgmt/ui/index.html`) for up to a minute before
settling to `"Being archived"` -- expected, not a failure.

`configure_archiver.py` calls the mgmt BPL `archivePV` action once per
PV -- confirmed live against the running appliance that it only reads
the *first* `pv` parameter of a request, so bulk-registering with
several repeated `pv=` values (a form some other BPL actions do accept)
silently drops all but the first.

### Restore the twin from a past time

```bash
cd serving
python serve.py --restore-at "2026-10-10T02:35:00.000-07:00"
```

Seeds every writable param from the archiver's recorded value at that
time (`archiver/restore.py`'s `restore_at()`, the same `getDataAtTime`
BPL call `lcls_live.archiver.lcls_archiver_restore()` uses, pointed at
the local appliance instead of SLAC's) instead of each variable's
default. A param the archiver has no value for at that time
(never archived, or archived after that time) keeps its default; the
startup log reports how many of the writable params were actually
restored (`restoring N/53 writable params from ...`).

## Limits

- Zone1's space-charge-tracked run is slow: tens of seconds at the default
  2000 particles, scaling with particle count. Every
  zone1 PV put pays this cost; a `--wait-for-puts` scan client needs a
  timeout well past it.
- Zone1's setpoints are all construction-time parameters (solenoid
  currents and cavity fields are baked into field-map arrays when the
  element is built), so a zone1 change always rebuilds and re-tracks the
  whole zone -- there is no cheaper, partial update.
- Misalignments (`*misal` in both zones' defaults) are not exposed as PVs;
  neither is zone1's/zone2's own bunch-generation/tracking configuration
  (particle count, integrator step size, ...), which `serve.py`'s
  `--n-particles` is the only exposed knob for.
