#!/usr/bin/env python3
"""
gen_configs.py — build every IDE config file from the canonical schema.

WHY GENERATED AND NOT HAND-WRITTEN
----------------------------------
The entire job of a .cursorrules file is to stop an LLM inventing field names.
A hand-written one that contains invented field names does the opposite: the
model emits them with more confidence, the developer ships them, Forge returns
them in unresolved_tags, and the developer concludes Forge is broken.

That is not hypothetical. The first draft of these rules listed seven "standard
fields". Checked against schema/fields.json, five of them do not exist:

    spindle_temperature_c   -> real name is spindle_temperature
    coolant_temperature_c   -> real name is sensor_readings.coolant_temp
    coolant_pressure_bar    -> real name is sensor_readings.coolant_pressure
    bearing_vibration_mm_s  -> real name is sensor_readings.vibration_x
    feed_rate_mm_min        -> real name is feed_rate

It also stated two naming conventions that match zero fields in the corpus:
"vibration fields end in _mm_s" and "pressure fields end in _bar".

So every field name in the output is read out of the published schema at build
time, and each one is annotated with how many real vendor tags map to it. A
name that disappears upstream disappears here, instead of quietly living on in
a rules file that nobody re-checks.

Source: https://github.com/FoundryNet/canonical-schema  (MIT)

Run:  python3 gen_configs.py [path-to-canonical-schema]
"""

import json
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = os.path.expanduser(
    sys.argv[1] if len(sys.argv) > 1 else "~/Desktop/foundrynet-canonical-schema")

MCP = "https://mcp.foundrynet.io/mcp"
API = "https://forge.foundrynet.io"
REPO = "https://github.com/FoundryNet/canonical-schema"
SANDBOX = "ghcr.io/foundrynet/forge-sandbox"

# The 32 tools production exposes, read off forge-mcp's @mcp.tool decorators.
TOOLS = [
    ("normalize_telemetry", "raw vendor telemetry -> canonical fields. The one you want first."),
    ("get_coverage", "what Forge can normalize, per OEM. Call before guessing a field name."),
    ("identify_machine", "register or resolve a machine identity (mint_id)."),
    ("query_machine_history", "stored normalized readings for a machine."),
    ("predict", "forecast a canonical series."),
    ("predict_breach", "will a series cross a threshold, and when. STATELESS."),
    ("remaining_life", "remaining useful life against a failure threshold."),
    ("predict_batch", "score many machines at once."),
    ("fleet_health", "fleet rollup, risk distribution, maintenance queue."),
    ("detect_anomalies", "z-score anomaly scan, no forecast."),
    ("machine_intelligence", "combined assessment for one machine."),
    ("prediction_accuracy", "how past predictions scored."),
    ("health_index", "single health score for a machine."),
    ("diagnose_machine", "guided diagnosis from recent telemetry."),
    ("calculate_oee", "OEE for one machine over a period."),
    ("fleet_oee", "OEE across the fleet."),
    ("energy_consumption", "energy use for a machine over a period."),
    ("shift_report", "shift summary."),
    ("create_automation", "create a trigger on a canonical field."),
    ("activate_automation", "arm a trigger."),
    ("list_automations", "triggers on a machine."),
    ("disable_automation", "disarm a trigger."),
    ("delete_automation", "remove a trigger."),
    ("restore_automation", "undo a delete."),
    ("query_webhook_history", "what a trigger actually fired."),
    ("list_guardrails", "safety limits on a machine."),
    ("check_guardrail", "would this proposed write be blocked?"),
    ("correct_mapping", "tell Forge a mapping was wrong; it learns."),
    ("verify_record", "verify a stored record's integrity."),
    ("fire_sandbox", "test a trigger without real equipment."),
    ("get_agent_card", "this agent's identity card."),
    ("list_agents", "discover agents by capability."),
]

# Two canonical names for one quantity is a real wart in the corpus. Mirrors
# CANONICAL_ALIASES in forge_core/canonicals.py so a model that guesses the
# wrong spelling is corrected rather than left to fail.
ALIASES = {
    "spindle_temperature": ["spindle_temperature_c", "spindle_temp", "spindle_temp_c"],
    "spindle_speed_rpm": ["spindle.speed", "spindle_rotary_velocity", "rotary_velocity"],
    "spindle_load_pct": ["spindle.load", "spindle_load_percent"],
    "motor_temperature": ["motor_temperature_c", "motor_temp"],
    "vibration_rms": ["vibration_mm_s", "vibration_rms_mm_s", "vibration.rms"],
    "power_consumption_kw": ["motor_power_kw", "power_kw", "electrical_power_kw"],
}


def load():
    with open(os.path.join(SCHEMA, "schema", "fields.json")) as f:
        return json.load(f)


def top_fields(fields, vertical, n):
    rows = [x for x in fields if x["vertical"] == vertical]
    rows.sort(key=lambda x: (-(x.get("mapping_count") or 0), x["field"]))
    return rows[:n]


def fmt(rows, width=34):
    out = []
    for x in rows:
        unit = x.get("unit") or "—"
        out.append(f"  {x['field']:<{width}} {unit:<6} {x.get('mapping_count') or 0:>4} mappings")
    return "\n".join(out)


def suffix_stats(fields):
    names = [x["field"] for x in fields]
    c = Counter()
    for n in names:
        m = re.search(r"_([a-z0-9_]+)$", n)
        if m:
            c[m.group(1)] += 1
    return c, names


def build_field_reference(d):
    fields = d["fields"]
    parts = []
    for v, n in (("cnc", 18), ("robotics", 12), ("universal", 20),
                 ("vehicle", 10), ("additive", 6), ("amr", 6)):
        rows = top_fields(fields, v, n)
        if not rows:
            continue
        parts.append(f"{v.upper()} ({len([x for x in fields if x['vertical']==v])} fields total)\n"
                     + fmt(rows))
    return "\n\n".join(parts)


def alias_block():
    out = []
    for primary, wrong in ALIASES.items():
        out.append(f"  {', '.join(wrong)}\n    -> {primary}")
    return "\n".join(out)


# ---------------------------------------------------------------------------

RULES_BODY = """\
# FoundryNet Canonical Schema — field naming for industrial telemetry
#
# Generated from {repo} v{version} ({count} fields, {maps} vendor mappings).
# Do not hand-edit: run gen_configs.py to regenerate.

When working with industrial equipment telemetry — CNC machines, robots, PLCs,
vehicles, 3D printers, building automation — use the FoundryNet Canonical
Schema for field names. It is the target vocabulary that vendor-specific tags
normalize into.

## The single most important rule

DO NOT INVENT FIELD NAMES. The schema is irregular because it was extracted
from a real corpus of {maps} vendor tags, not designed on a whiteboard. Names
you would expect to exist frequently do not:

{aliasblock}

If you need a field that is not listed below, look it up rather than guessing:

  curl {api}/v1/coverage        # production: what is supported, per OEM
  {repo}/blob/main/schema/fields.json   # every field, with type + unit

Or run the sandbox locally and query it with no API key at all. Note that
/v1/canonical-fields is a SANDBOX endpoint — production serves /v1/coverage
and the full dictionary lives in the schema repo:

  docker run -p 8000:8000 {sandbox}
  curl localhost:8000/v1/canonical-fields

## Naming conventions that actually hold

These suffixes are real and consistent enough to rely on:

{suffixes}

## Conventions that do NOT hold — do not assume them

- Unit suffixes are NOT universal. Only {units} of {count} fields declare a
  unit at all. `sensor_readings.coolant_temp` has no `_c`; `feed_rate` has no
  `_mm_min`. Never append a unit suffix to make a name "consistent".
- Never infer the unit from the name. Read the `unit` property, or convert
  explicitly. A field named `..._temp` may be Celsius or Fahrenheit depending
  on the source tag; Forge reports the conversion it applied.
- Percentages are mostly `_pct`, but `axes.0.load_percent` uses `_percent`.
- Some fields are dot-namespaced (`sensor_readings.*`, `axes.*`, `robot.*`,
  `ros.*`) and some are flat. There is no rule; use the exact published name.
- `axes.0.*` and `axes.x_*` are BOTH real and mean different things in
  different packs. Do not normalize one into the other.

## High-frequency fields

Ordered by how many real vendor tags map to each. If you only remember a
handful, remember the top of this list.

{fieldref}

## Normalizing raw vendor telemetry

Do not hand-write a mapping table. Send the raw payload to Forge and use what
comes back:

  POST {api}/v1/normalize
  Authorization: Bearer YOUR_FORGE_KEY
  {{"oem": "haas", "data": {{"S SPEED (RPM)": 8500, "SP_LOAD_PCT (%)": 84.7}}}}

  -> {{"normalized": {{"spindle_speed_rpm": 8500, "spindle_load_pct": 84.7}},
       "coverage_pct": 100.0}}

Check `unresolved_tags` in the response. Anything listed there did not map, and
inventing a name for it locally defeats the purpose.

Or connect an agent directly over MCP: {mcp}

## Predictions are stateless

`predict_breach`, `remaining_life`, and `fleet_health` never read stored
telemetry. You must pass `time_series` (16+ points, oldest to newest) on every
call. Sending {{machine_id, field, threshold}} and expecting a lookup is a 422.
"""


def render_rules(d, suffixes):
    return RULES_BODY.format(
        repo=REPO, version=d["version"], count=d["field_count"],
        maps=f"{d['mapping_count']:,}",
        units=len([x for x in d["fields"] if x.get("unit")]),
        aliasblock=alias_block(), suffixes=suffixes,
        fieldref=build_field_reference(d),
        api=API, mcp=MCP, sandbox=SANDBOX,
    )


CLAUDE_MD = """\
# Forge — industrial equipment telemetry

<!-- Generated from {repo} v{version}. Run gen_configs.py to regenerate. -->

You have access to the Forge MCP server for industrial equipment data. Forge
normalizes telemetry from {oems} OEM families across 14 protocols into one
canonical schema of {count} fields, built from {maps} curated vendor mappings.

**Endpoint:** `{mcp}`
**Schema:** {repo} (MIT)
**No-key sandbox:** `docker run -p 8000:8000 {sandbox}`

## How to use it

**Start with `get_coverage`.** Before writing any field name, ask Forge what it
supports for that OEM. This is cheaper than guessing wrong and faster than
reading the schema.

**Never invent a canonical field name.** The schema is irregular — extracted
from a real corpus, not designed. Fields you would expect often do not exist:

{aliasblock}

**Never infer a unit from a field name.** Only {units} of {count} fields declare
a unit. `sensor_readings.coolant_temp` has no `_c` suffix and may be Celsius or
Fahrenheit depending on the source tag. Read the unit; do not assume it.

**Check `unresolved_tags` on every normalize response.** Tags listed there did
not map. Do not paper over them with a locally invented name — either look up
the right one, or report the gap.

**Predictions are stateless.** `predict_breach`, `remaining_life`, and
`fleet_health` never read stored history. Pass `time_series` (16+ points,
oldest to newest) on every call.

**A 403 is usually correct.** Guardrail writes are restricted to humans by
design. If you hit one, route to a human rather than working around it. A 402
is billing, not permissions — the two are not interchangeable.

## Tools

{tools}

## Worked example

A SINUMERIK posts German tag names. You do not need to know what they mean:

    normalize_telemetry(oem="siemens", data={{
      "SPINDEL_AUSLASTUNG (%)": 63.0,
      "STUECKZAHL (pcs)": 842,
      "Betriebsstunden": 14203.5
    }})

    -> {{"spindle_load_pct": 63.0,
         "part_count": 842,
         "operating_hours": 14203.5}}

Then forecast against a canonical field:

    predict_breach(time_series=[...48 readings...],
                   threshold=95.0,
                   canonical_field="spindle_load_pct")
"""


def render_claude(d):
    tools = "\n".join(f"- `{n}` — {desc}" for n, desc in TOOLS)
    return CLAUDE_MD.format(
        repo=REPO, version=d["version"], count=d["field_count"],
        maps=f"{d['mapping_count']:,}", oems=len(d["oem_families"]),
        units=len([x for x in d["fields"] if x.get("unit")]),
        aliasblock=alias_block(), tools=tools, mcp=MCP, sandbox=SANDBOX,
    )


def render_vscode(d):
    """A settings.json FRAGMENT. Emitted with a header comment because pasting a
    whole settings file over someone's config is how you lose their setup."""
    top = [x["field"] for x in sorted(
        d["fields"], key=lambda x: -(x.get("mapping_count") or 0))[:40]]
    cfg = {
        "//": [
            "FoundryNet canonical schema — VS Code settings FRAGMENT.",
            "MERGE these keys into your existing settings.json. Do not replace the file.",
            f"Generated from {REPO} v{d['version']}.",
        ],
        "github.copilot.chat.codeGeneration.instructions": [
            {"file": ".github/copilot-instructions.md"},
        ],
        "cSpell.words": sorted({
            "foundrynet", "forge", "mtconnect", "profinet", "bacnet", "sparkplug",
            "focas", "sinumerik", "canonicalize", "opcua", "modbus", "rpm",
            "kwh", "mint", "prusa", "fanuc", "haas", "okuma", "mazak",
        }),
        "files.associations": {
            ".cursorrules": "markdown",
            ".windsurfrules": "markdown",
            "*.forge.json": "json",
        },
        "json.schemas": [
            {
                "fileMatch": ["*.forge.json", "canonical-*.json"],
                "url": f"{REPO}/raw/main/schema/fields.json",
            }
        ],
        "editor.quickSuggestions": {"strings": True},
        "forge.canonicalFields": top,
        "forge.mcpEndpoint": MCP,
        "forge.sandboxImage": SANDBOX,
    }
    return json.dumps(cfg, indent=2)


def main():
    if not os.path.isdir(SCHEMA):
        sys.exit(f"canonical-schema not found at {SCHEMA}")
    d = load()
    fields = d["fields"]

    c, _ = suffix_stats(fields)
    keep = [("pct", "percentage, 0-100"), ("rpm", "revolutions per minute"),
            ("hours", "hours"), ("seconds", "seconds"), ("kwh", "kilowatt-hours"),
            ("kw", "kilowatts"), ("kg", "kilograms"), ("c", "degrees Celsius")]
    suffixes = "\n".join(
        f"  _{s:<9} {desc:<24} ({c.get(s, 0)} fields)" for s, desc in keep
    )

    outputs = {
        ".cursorrules": render_rules(d, suffixes),
        ".windsurfrules": render_rules(d, suffixes),
        "claude-industrial.md": render_claude(d),
        "vscode-settings.json": render_vscode(d),
        os.path.join(".github", "copilot-instructions.md"): render_claude(d),
        "AGENTS.md": render_claude(d),
    }

    for rel, content in outputs.items():
        path = os.path.join(HERE, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(rel) else None
        with open(path, "w", encoding="utf-8") as f:
            f.write(content if content.endswith("\n") else content + "\n")
        print(f"  {rel:<42} {len(content):>6} bytes")

    # Verification: every field name mentioned in any generated file must exist
    # in the schema. This is the check that would have caught the hand-written
    # draft, so it runs on every build rather than living in a test nobody runs.
    names = {x["field"] for x in fields}
    alias_ok = {a for v in ALIASES.values() for a in v} | set(ALIASES)
    # Tool names are snake_case too and would otherwise trip the field check.
    tool_names = {n for n, _ in TOOLS}
    # Prose refers to families with a wildcard ("axes.0.*"); accept a token that
    # is a strict prefix of a real field so the wildcard form does not read as
    # an invented name.
    prefixes = {n.rsplit(".", 1)[0] for n in names if "." in n}
    suspects = set()
    pattern = re.compile(r"\b([a-z][a-z0-9]*(?:[._][a-z0-9]+){1,4})\b")
    for rel, content in outputs.items():
        if rel.endswith(".json"):
            continue
        for tok in pattern.findall(content):
            if tok in names or tok in alias_ok or tok in tool_names or tok in prefixes:
                continue
            # Only flag things that LOOK like canonical fields: snake_case with
            # a known domain word, not prose or URLs.
            if any(tok.startswith(p) for p in
                   ("spindle_", "coolant_", "bearing_", "feed_", "axes.",
                    "sensor_readings.", "robot.", "ros.", "motor_", "part_",
                    "operating_", "energy_", "alarm_", "tool_", "power_")):
                suspects.add(tok)
    print()
    if suspects:
        print("!! field names not in schema and not a known alias:")
        for s in sorted(suspects):
            print("   ", s)
        sys.exit(1)
    print(f"✓ every canonical field named in the configs exists in schema v{d['version']}")
    print(f"  {d['field_count']} fields, {d['mapping_count']:,} mappings, "
          f"{len(d['oem_families'])} OEM families")


if __name__ == "__main__":
    main()
