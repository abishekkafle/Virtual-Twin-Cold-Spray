# CEL-P5 WebXR runtime verification

**Decision:** PASS_WEBXR_RUNTIME_EQUIVALENCE.

- Rows replayed: 44.
- Targets replayed: 9.
- Compared values: 396.
- Global max absolute error: 0.
- Global max relative error: 0.
- Unsupported-pair gate: UNSUPPORTED_PAIR, prediction null = true.
- Out-of-range gate: OUTSIDE_QUALIFIED_VELOCITY_RANGE, prediction null = true.

| Target | Max abs error | Max relative error |
|---|---:|---:|
| terminal_particle_volume_weighted_velocity_m_s | 0 | 0 |
| particle_axial_flattening_percent | 0 | 0 |
| normalized_crater_depth | 0 | 0 |
| particle_peeqvavg_p95 | 0 | 0 |
| substrate_peeq_p95 | 0 | 0 |
| particle_temperature_max_k | 0 | 0 |
| substrate_temperature_max_k | 0 | 0 |
| maximum_temperature_over_melt | 0 | 0 |
| peak_contact_pressure_pa | 0 | 0 |

The JavaScript runtime exactly replays the Python-fitted ExtraTrees bundle to numerical precision and preserves deployment domain gates.
