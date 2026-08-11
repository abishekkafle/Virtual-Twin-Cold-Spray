// Optional CEL-P5 adapter for the WebXR WarpSPEE3D scene.
//
// This module does not replace js/cs_model_adapter.js. It exposes a separate
// window.r4CELP5Model object so the qualified Abaqus/CEL surrogate can be
// tested, shown in screenshots, or wired into vr.html when desired.

import { loadCelP5Bundle, predict, DEFAULTS, SUPPORTED_PAIRS }
  from '../cold_spray_cel_p5_model.js';

const PRESSURE_TO_VELOCITY_SLOPE = 15;      // m/s per bar, provisional UI mapping
const PRESSURE_TO_VELOCITY_BASE_BAR = 30;
const VELOCITY_BOUNDS = [250, 1250];

const MATERIAL_PAIR_MAP = {
  pure_cu: {
    particle_material: 'Cu',
    substrate_material: 'Cu',
    label: 'Cu -> Cu',
  },
  al6061: {
    particle_material: 'Al6061',
    substrate_material: 'SS304',
    label: 'Al6061 -> SS304',
  },
  ti6al4v: {
    particle_material: 'Ti6Al4V',
    substrate_material: 'Ti6Al4V',
    label: 'Ti6Al4V -> Ti6Al4V',
  },
  inconel718: {
    particle_material: 'Inconel718',
    substrate_material: 'Ti6Al4V',
    label: 'Inconel718 -> Ti6Al4V',
  },
};

const state = {
  ready: false,
  error: null,
  materialId: 'pure_cu',
  materialName: 'OFHC Copper',
  last: null,
};

function clamp(value, lo, hi) {
  return Math.max(lo, Math.min(hi, value));
}

function pressureToImpactVelocity(pressureBar) {
  const velocity = DEFAULTS.impact_velocity_m_s +
    PRESSURE_TO_VELOCITY_SLOPE * (pressureBar - PRESSURE_TO_VELOCITY_BASE_BAR);
  return clamp(velocity, VELOCITY_BOUNDS[0], VELOCITY_BOUNDS[1]);
}

function getParamValue(id, fallback) {
  const internal = window.r4Internal;
  const defs = internal && Array.isArray(internal.paramsDef) ? internal.paramsDef : [];
  const param = defs.find(item => item.id === id);
  return param && typeof param.value === 'number' ? param.value : fallback;
}

function buildParams() {
  const pressureBar = getParamValue('pressure', 30);
  const pair = MATERIAL_PAIR_MAP[state.materialId] || null;
  if (!pair) {
    return {
      unsupported_material_id: state.materialId,
      impact_velocity_m_s: pressureToImpactVelocity(pressureBar),
    };
  }
  return {
    ...pair,
    impact_velocity_m_s: pressureToImpactVelocity(pressureBar),
    pressure_bar_ui: pressureBar,
  };
}

function recompute() {
  const params = buildParams();
  if (!state.ready) {
    state.last = {
      blocked: true,
      params,
      applicability: { status: state.error ? 'MODEL_ERROR' : 'MODEL_LOADING' },
    };
    return state.last;
  }
  if (params.unsupported_material_id) {
    state.last = {
      blocked: true,
      params,
      applicability: {
        status: 'UNSUPPORTED_WEBXR_MATERIAL_SELECTION',
        warning: `Material selector ${params.unsupported_material_id} is not mapped to a CEL-P5 qualified pair.`,
      },
    };
    return state.last;
  }
  try {
    state.last = { ...predict(params), params };
  } catch (error) {
    state.error = String(error);
    state.last = {
      blocked: true,
      params,
      applicability: { status: 'MODEL_ERROR', warning: state.error },
    };
  }
  return state.last;
}

const rows = new Map();

function textEntity(value, y, color = '#eef3f8', width = 0.54, wrap = 28) {
  const t = document.createElement('a-text');
  t.setAttribute('value', value);
  t.setAttribute('position', `0 ${y} 0.022`);
  t.setAttribute('align', 'center');
  t.setAttribute('color', color);
  t.setAttribute('width', width);
  t.setAttribute('wrap-count', wrap);
  return t;
}

function ensurePanel() {
  let panel = document.getElementById('r4CELP5ModelPanel');
  const scene = document.querySelector('a-scene');
  if (!panel && scene) {
    panel = document.createElement('a-entity');
    panel.setAttribute('id', 'r4CELP5ModelPanel');
    panel.setAttribute('position', '-1.33 2.105 1.00');
    panel.setAttribute('visible', 'false');
    scene.appendChild(panel);
  }
  if (!panel || panel.children.length) return panel;

  const bezel = document.createElement('a-box');
  bezel.setAttribute('width', 0.82);
  bezel.setAttribute('height', 0.72);
  bezel.setAttribute('depth', 0.03);
  bezel.setAttribute('material', 'color:#152033;metalness:0.5;roughness:0.5');
  panel.appendChild(bezel);

  const display = document.createElement('a-plane');
  display.setAttribute('width', 0.76);
  display.setAttribute('height', 0.66);
  display.setAttribute('position', '0 0 0.018');
  display.setAttribute('material', 'color:#030912;emissive:#091d2b;emissiveIntensity:0.35;side:double');
  panel.appendChild(display);

  panel.appendChild(textEntity('CEL-P5 QUALIFIED-PAIR SURROGATE', 0.260, '#7fe9ff', 0.58, 29));

  const layout = [
    ['pair', 0.185],
    ['inputs', 0.120],
    ['velocity', 0.055],
    ['flattening', -0.010],
    ['strain', -0.075],
    ['temperature', -0.140],
    ['pressure', -0.205],
    ['status', -0.285],
  ];
  for (const [id, y] of layout) {
    const el = textEntity('', y);
    rows.set(id, el);
    panel.appendChild(el);
  }
  return panel;
}

function setRow(id, value, color = '#eef3f8') {
  const el = rows.get(id);
  if (!el) return;
  el.setAttribute('value', value);
  el.setAttribute('color', color);
}

function refreshPanel() {
  ensurePanel();
  const r = state.last || recompute();
  const params = r.params || {};
  const status = r.applicability?.status || 'UNKNOWN';

  if (r.blocked) {
    setRow('pair', state.materialName || state.materialId, '#ffffff');
    setRow('inputs', status, '#f6b73c');
    setRow('velocity', r.applicability?.warning || 'Prediction blocked by CEL-P5 domain gate.', '#ffb8b8');
    setRow('flattening', '', '#bcd7e8');
    setRow('strain', '', '#bcd7e8');
    setRow('temperature', '', '#bcd7e8');
    setRow('pressure', '', '#bcd7e8');
    setRow('status', 'SIMULATION SURROGATE | HUMAN REVIEW ONLY', '#ff6b6b');
    return;
  }

  const review = r.applicability?.near_constitutive_review_region;
  setRow('pair', `${params.label || `${params.particle_material} -> ${params.substrate_material}`}`, '#ffffff');
  setRow('inputs', `v_imp ${Math.round(r.impact_velocity_m_s)} m/s | pressure knob ${params.pressure_bar_ui?.toFixed?.(1) ?? 'n/a'} bar`, '#bcd7e8');
  setRow('velocity', `terminal velocity ${r.terminal_velocity_m_s.toFixed(2)} m/s`, '#bcd7e8');
  setRow('flattening', `flattening ${r.particle_flattening_percent.toFixed(2)} % | crater/D ${r.normalized_crater_depth.toFixed(3)}`, '#bcd7e8');
  setRow('strain', `PEEQ p95 p/s ${r.particle_peeq_p95.toFixed(3)} / ${r.substrate_peeq_p95.toFixed(3)}`, '#bcd7e8');
  setRow('temperature', `Tmax p/s ${Math.round(r.particle_tmax_k)} / ${Math.round(r.substrate_tmax_k)} K | max T/Tm ${r.maximum_temperature_over_melt.toFixed(3)}`, review ? '#f6b73c' : '#bcd7e8');
  setRow('pressure', `peak contact pressure ${(r.peak_contact_pressure_pa / 1e9).toFixed(2)} GPa`, '#bcd7e8');
  setRow('status', review ? 'AUTHORIZED + CONSTITUTIVE REVIEW FLAG' : 'AUTHORIZED SIMULATION SURROGATE', review ? '#f6b73c' : '#5ee08a');
}

window.r4CELP5Model = {
  state,
  supportedPairs: SUPPORTED_PAIRS,
  predict() {
    const result = recompute();
    refreshPanel();
    return result;
  },
  lastPrediction() {
    return state.last;
  },
  showPanel() {
    const panel = ensurePanel();
    if (panel) panel.setAttribute('visible', true);
    recompute();
    refreshPanel();
  },
  hidePanel() {
    const panel = document.getElementById('r4CELP5ModelPanel');
    if (panel) panel.setAttribute('visible', false);
  },
};

document.addEventListener('spee3d-config-applied', event => {
  const material = event.detail && event.detail.material;
  if (material && material.id) {
    state.materialId = material.id;
    state.materialName = material.name || material.short || material.id;
  }
  recompute();
  refreshPanel();
});

document.addEventListener('r4-params-changed', () => {
  recompute();
  refreshPanel();
});

function init() {
  const scene = document.querySelector('a-scene');
  if (scene) {
    if (scene.hasLoaded) ensurePanel();
    else scene.addEventListener('loaded', ensurePanel);
  }
  loadCelP5Bundle()
    .then(() => {
      state.ready = true;
      recompute();
      refreshPanel();
    })
    .catch(error => {
      state.error = String(error);
      recompute();
      refreshPanel();
    });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
