# Forge — industrial equipment telemetry

<!-- Generated from https://github.com/FoundryNet/canonical-schema v1.0.0. Run gen_configs.py to regenerate. -->

You have access to the Forge MCP server for industrial equipment data. Forge
normalizes telemetry from 18 OEM families across 14 protocols into one
canonical schema of 366 fields, built from 16,908 curated vendor mappings.

**Endpoint:** `https://mcp.foundrynet.io/mcp`
**Schema:** https://github.com/FoundryNet/canonical-schema (MIT)
**No-key sandbox:** `docker run -p 8000:8000 ghcr.io/foundrynet/forge-sandbox`

## How to use it

**Start with `get_coverage`.** Before writing any field name, ask Forge what it
supports for that OEM. This is cheaper than guessing wrong and faster than
reading the schema.

**Never invent a canonical field name.** The schema is irregular — extracted
from a real corpus, not designed. Fields you would expect often do not exist:

  spindle_temperature_c, spindle_temp, spindle_temp_c
    -> spindle_temperature
  spindle.speed, spindle_rotary_velocity, rotary_velocity
    -> spindle_speed_rpm
  spindle.load, spindle_load_percent
    -> spindle_load_pct
  motor_temperature_c, motor_temp
    -> motor_temperature
  vibration_mm_s, vibration_rms_mm_s, vibration.rms
    -> vibration_rms
  motor_power_kw, power_kw, electrical_power_kw
    -> power_consumption_kw

**Never infer a unit from a field name.** Only 58 of 366 fields declare
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

- `normalize_telemetry` — raw vendor telemetry -> canonical fields. The one you want first.
- `get_coverage` — what Forge can normalize, per OEM. Call before guessing a field name.
- `identify_machine` — register or resolve a machine identity (mint_id).
- `query_machine_history` — stored normalized readings for a machine.
- `predict` — forecast a canonical series.
- `predict_breach` — will a series cross a threshold, and when. STATELESS.
- `remaining_life` — remaining useful life against a failure threshold.
- `predict_batch` — score many machines at once.
- `fleet_health` — fleet rollup, risk distribution, maintenance queue.
- `detect_anomalies` — z-score anomaly scan, no forecast.
- `machine_intelligence` — combined assessment for one machine.
- `prediction_accuracy` — how past predictions scored.
- `health_index` — single health score for a machine.
- `diagnose_machine` — guided diagnosis from recent telemetry.
- `calculate_oee` — OEE for one machine over a period.
- `fleet_oee` — OEE across the fleet.
- `energy_consumption` — energy use for a machine over a period.
- `shift_report` — shift summary.
- `create_automation` — create a trigger on a canonical field.
- `activate_automation` — arm a trigger.
- `list_automations` — triggers on a machine.
- `disable_automation` — disarm a trigger.
- `delete_automation` — remove a trigger.
- `restore_automation` — undo a delete.
- `query_webhook_history` — what a trigger actually fired.
- `list_guardrails` — safety limits on a machine.
- `check_guardrail` — would this proposed write be blocked?
- `correct_mapping` — tell Forge a mapping was wrong; it learns.
- `verify_record` — verify a stored record's integrity.
- `fire_sandbox` — test a trigger without real equipment.
- `get_agent_card` — this agent's identity card.
- `list_agents` — discover agents by capability.

## Worked example

A SINUMERIK posts German tag names. You do not need to know what they mean:

    normalize_telemetry(oem="siemens", data={
      "SPINDEL_AUSLASTUNG (%)": 63.0,
      "STUECKZAHL (pcs)": 842,
      "Betriebsstunden": 14203.5
    })

    -> {"spindle_load_pct": 63.0,
         "part_count": 842,
         "operating_hours": 14203.5}

Then forecast against a canonical field:

    predict_breach(time_series=[...48 readings...],
                   threshold=95.0,
                   canonical_field="spindle_load_pct")
