# forge-dev-configs

Drop-in configuration that teaches your AI coding tools the **FoundryNet
Canonical Schema** — the field vocabulary that industrial equipment telemetry
normalizes into.

Without it, an LLM asked to model machine telemetry invents field names.
`coolant_temperature_c` is the obvious guess. It is also wrong: the real field
is `sensor_readings.coolant_temp`, and code built on the guess fails silently
against every real system.

MIT licensed. No dependency on Forge — the schema is
[open source](https://github.com/FoundryNet/canonical-schema) and these files
are useful whether or not you ever call the API.

---

## Install

Copy the file your tool reads into the root of your project.

| Tool | File | Where it goes |
|---|---|---|
| Cursor | `.cursorrules` | project root |
| Windsurf | `.windsurfrules` | project root |
| Claude Code / Claude Desktop | `claude-industrial.md` | paste into `CLAUDE.md`, or your project instructions |
| GitHub Copilot | `.github/copilot-instructions.md` | `.github/` in your repo |
| Codex, Jules, Amp, and other agents | `AGENTS.md` | project root |
| VS Code | `vscode-settings.json` | **merge** into `.vscode/settings.json` |

```bash
git clone https://github.com/FoundryNet/forge-dev-configs
cp forge-dev-configs/.cursorrules              your-project/
cp forge-dev-configs/AGENTS.md                 your-project/
mkdir -p your-project/.github && cp forge-dev-configs/.github/copilot-instructions.md your-project/.github/
```

`vscode-settings.json` is a **fragment**, not a settings file. Merge its keys
into your existing `.vscode/settings.json` — copying it wholesale replaces your
configuration.

---

## What the rules actually say

Three things, in order of how much trouble they save you.

**1. Do not invent field names.** The schema was extracted from a corpus of
16,908 real vendor tags, not designed on a whiteboard, so it is irregular in
ways no model will guess correctly. The rules ship an alias table for the
plausible-but-wrong names, so `spindle_temperature_c` gets corrected to
`spindle_temperature` instead of shipping.

**2. Do not infer units from names.** Only 58 of 366 fields declare a unit.
`sensor_readings.coolant_temp` carries no `_c` and may be Celsius or Fahrenheit
depending on which vendor tag fed it. Read the unit; never assume it from the
suffix.

**3. Look it up instead of guessing.** The rules point at three lookups —
the live API, the published `fields.json`, and a keyless local sandbox:

```bash
docker run -p 8000:8000 ghcr.io/foundrynet/forge-sandbox
curl localhost:8000/v1/canonical-fields
```

(`/v1/canonical-fields` is a sandbox endpoint. Production serves `/v1/coverage`;
the full dictionary lives in the schema repo.)

The instruction that matters most is not "memorize 366 fields" — it is "here
are the high-frequency ones, and here is how to look up the rest."

---

## These files are generated, deliberately

`gen_configs.py` builds every output from
[`schema/fields.json`](https://github.com/FoundryNet/canonical-schema). Nothing
here is typed by hand, and that is the point.

The first hand-written draft of these rules listed seven "standard fields".
Checked against the schema, **five did not exist**:

| Claimed in the draft | Actually |
|---|---|
| `spindle_temperature_c` | `spindle_temperature` |
| `coolant_temperature_c` | `sensor_readings.coolant_temp` |
| `coolant_pressure_bar` | `sensor_readings.coolant_pressure` |
| `bearing_vibration_mm_s` | `sensor_readings.vibration_x` |
| `feed_rate_mm_min` | `feed_rate` |

It also asserted two conventions that match **zero** fields in the corpus:
*"vibration fields end in `_mm_s`"* and *"pressure fields end in `_bar`"*.

A rules file whose job is to prevent hallucinated field names, containing
hallucinated field names, is worse than no rules file — the model states them
with more confidence. So the build verifies every canonical field name it
emits against the schema and **fails** if one does not resolve:

```
$ python3 gen_configs.py
✓ every canonical field named in the configs exists in schema v1.0.0
  366 fields, 16,908 mappings, 18 OEM families
```

Regenerate after a schema release:

```bash
git clone https://github.com/FoundryNet/canonical-schema ../canonical-schema
python3 gen_configs.py ../canonical-schema
```

---

## The schema in one table

Six verticals, 366 fields. Ordered by how many real vendor tags map onto each —
if you remember five field names, make it these.

| Field | Unit | Vendor tags mapped |
|---|---|---:|
| `spindle_speed_rpm` | rpm | 307 |
| `spindle_load_pct` | % | 255 |
| `axes.0.position_actual` | — | 232 |
| `sensor_readings.vibration_x` | — | 229 |
| `operating_hours` | h | 227 |
| `energy_kwh` | kWh | 226 |
| `axes.0.temperature_c` | degC | 222 |
| `alarm_code` | — | 218 |

Note the inconsistency in that list — `_pct` and `_rpm` and `_c` suffixes next
to bare `feed_rate` and dot-namespaced `sensor_readings.*`. That irregularity is
exactly why guessing does not work.

---

## Optional: connect the agent to live equipment

The schema is useful on its own. If you also want an agent that can read real
machines, Forge serves 32 tools over MCP:

```bash
claude mcp add --scope user --transport http forge https://mcp.foundrynet.io/mcp \
  --header 'Authorization: Bearer YOUR_FORGE_KEY'
```

Or work against the keyless local sandbox first — same schema, simulated data,
no account:

```bash
docker run -p 8000:8000 ghcr.io/foundrynet/forge-sandbox
claude mcp add --scope user --transport http forge-sandbox http://localhost:8000/mcp
```

---

## Contributing

The schema lives in
[FoundryNet/canonical-schema](https://github.com/FoundryNet/canonical-schema).
Vendor tag contributions are especially welcome for the `process` vertical,
which has canonical names declared but no mapped vendor tags yet.

If you find a field name in these configs that does not resolve, that is a bug
in the generator's verification step — please open an issue.

---

MIT · [foundrynet.io](https://foundrynet.io) · forge@foundrynet.io
