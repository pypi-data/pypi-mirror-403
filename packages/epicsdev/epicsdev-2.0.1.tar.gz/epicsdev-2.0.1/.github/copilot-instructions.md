# Copilot instructions for epicsdev

## Big picture
- Core EPICS PVAccess helpers are in [epicsdev/epicsdev.py](epicsdev/epicsdev.py). It keeps global server state in `C_` (prefix, PV map, verbosity, server state) and exposes `SPV()`, `publish()`, `pvv()`, `serverState()`.
- Server startup flow: `init_epicsdev(prefix, pvDefs, verbose=0, serverStateChanged=None, listDir=None)` builds PVs, then `Server(providers=[PVs])` runs a polling loop that checks `serverState()`; see [epicsdev/epicsdev.py](epicsdev/epicsdev.py) and [epicsdev/multiadc.py](epicsdev/multiadc.py).
- `create_PVs()` adds mandatory PVs (`host`, `version`, `status`, `server`, `verbose`, `polling`, `cycle`) before app-specific PVs; see [epicsdev/epicsdev.py](epicsdev/epicsdev.py).
- GUI pages for pypeto live in [config/epicsdev_pp.py](config/epicsdev_pp.py), [config/multiadc_pp.py](config/multiadc_pp.py), and [config/epicsSimscope_pp.py](config/epicsSimscope_pp.py); they assume the PV names/prefixes defined by the servers.

## Project-specific patterns & conventions
- PV definitions are `[name, description, SPV, extra]` and passed to `create_PVs()`; examples: `myPVDefs()` in [epicsdev/epicsdev.py](epicsdev/epicsdev.py) and [epicsdev/multiadc.py](epicsdev/multiadc.py).
- `SPV(initial, meta, vtype)` uses compact `meta`: `W` (writable), `R` (readable), `A` (alarm), `D` (discrete enum). `D` creates an `NTEnum` with `{choices,index}`.
- Writable PVs set `control.limitLow/High` to `0` as a PVA writability workaround (see `_create_PVs()` in [epicsdev/epicsdev.py](epicsdev/epicsdev.py)).
- `extra` dict keys commonly used: `setter`, `units`, `limitLow`, `limitHigh`, `format`, `valueAlarm`. `setter` receives `(value, spv)`.
- Use `publish()`/`pvv()` instead of direct `SharedPV` access; logging goes through `printi/printw/printe`, which also posts to `status`.
- In multi-channel templates, don’t pre-create `SPV` objects; use tuples and convert per-channel (see `ChannelTemplates` in [epicsdev/multiadc.py](epicsdev/multiadc.py)).

## External deps & integration points
- Requires `p4p` (see [pyproject.toml](pyproject.toml)). Optional runtime tools: `pypeto`, `pvplot` for GUI/plotting (see [README.md](README.md)).

## Common workflows (from README)
- Install and run demo server:
  - `python -m epicsdev.epicsdev`
- Control/plot demo (requires `pypeto`, `pvplot`):
  - `python -m pypeto -c config -f epicsdev`
- Run multi-channel waveform generator:
  - `python -m epicsdev.multiadc -c100 -n1000`
- Launch multiadc GUI:
  - `python -m pypeto -c config -f multiadc`
