// Qualified-pair CEL-P5 simulation-surrogate wrapper for the WebXR twin.
//
// This sits beside the legacy cold_spray_model.js without replacing it. The
// legacy model remains useful for historical comparison/demo-only screenshots;
// this wrapper exposes the new gated metal-on-metal Abaqus/CEL surrogate.

import { predictBundle } from './js/cel_p5_tree_runtime.mjs';

export const MODEL_VERSION = 'CEL-P5';

export const DEFAULTS = {
  particle_material: 'Cu',
  substrate_material: 'Cu',
  impact_velocity_m_s: 575.0,
};

export const SUPPORTED_PAIRS = [
  'Cu->Cu',
  'Al6061->SS304',
  'Ti6Al4V->Ti6Al4V',
  'Inconel718->Ti6Al4V',
];

let celP5Bundle = null;
let loadError = null;

export async function loadCelP5Bundle() {
  if (celP5Bundle) return celP5Bundle;
  if (loadError) throw loadError;
  try {
    const response = await fetch('./data/cel_p5_surrogate_tree_ensemble.json', { cache: 'no-cache' });
    if (!response.ok) throw new Error(`CEL-P5 bundle HTTP ${response.status}`);
    celP5Bundle = await response.json();
    if (celP5Bundle.schema_version !== '1.0.0' || celP5Bundle.ensemble?.type !== 'ExtraTreesRegressor') {
      throw new Error('Unexpected or incomplete CEL-P5 model bundle');
    }
    return celP5Bundle;
  } catch (error) {
    loadError = error;
    throw error;
  }
}

export function predict(params = {}) {
  if (!celP5Bundle) throw new Error('CEL-P5 surrogate unavailable until loadCelP5Bundle() resolves');
  const p = { ...DEFAULTS, ...params };
  const result = predictBundle(celP5Bundle, {
    pair: p.pair,
    particle_material: p.particle_material || p.powder_material,
    substrate_material: p.substrate_material,
    impact_velocity_m_s: Number(p.impact_velocity_m_s ?? p.velocity_m_s ?? p.v_gas),
  });

  if (!result.prediction) {
    return {
      blocked: true,
      model_version: MODEL_VERSION,
      applicability: result.applicability,
      prediction: null,
    };
  }

  const y = result.prediction;
  return {
    blocked: false,
    model_version: MODEL_VERSION,
    particle_material: p.particle_material || p.powder_material,
    substrate_material: p.substrate_material,
    impact_velocity_m_s: Number(p.impact_velocity_m_s ?? p.velocity_m_s ?? p.v_gas),
    terminal_velocity_m_s: y.terminal_particle_volume_weighted_velocity_m_s,
    particle_flattening_percent: y.particle_axial_flattening_percent,
    normalized_crater_depth: y.normalized_crater_depth,
    particle_peeq_p95: y.particle_peeqvavg_p95,
    substrate_peeq_p95: y.substrate_peeq_p95,
    particle_tmax_k: y.particle_temperature_max_k,
    substrate_tmax_k: y.substrate_temperature_max_k,
    maximum_temperature_over_melt: y.maximum_temperature_over_melt,
    peak_contact_pressure_pa: y.peak_contact_pressure_pa,
    prediction: y,
    target_labels: result.target_labels,
    applicability: result.applicability,
    operator_authority: false,
    simulation_surrogate_only: true,
  };
}

loadCelP5Bundle().catch(error => console.error('[CEL-P5 VirtualTwin] model load failed:', error));
