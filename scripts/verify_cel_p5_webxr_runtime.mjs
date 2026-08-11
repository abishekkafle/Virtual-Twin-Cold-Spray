import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { predictBundle } from '../webxr/cel_p5_tree_runtime.mjs';

const __filename = fileURLToPath(import.meta.url);
const ROOT = path.resolve(path.dirname(__filename), '..');
const BUNDLE_PATH = path.join(ROOT, 'webxr', 'cel_p5_surrogate_tree_ensemble.json');
const PYTHON_REFERENCE_PATH = path.join(ROOT, 'database', 'cel_p5_final_model_predictions.csv');
const REPORT_JSON = path.join(ROOT, 'reports', 'cel_p5_webxr_runtime_verification.json');
const REPORT_MD = path.join(ROOT, 'reports', 'cel_p5_webxr_runtime_verification.md');

function parseCsv(text) {
  const lines = text.trim().split(/\r?\n/);
  const headers = lines.shift().split(',');
  return lines.map(line => {
    const values = line.split(',');
    const row = {};
    headers.forEach((header, index) => {
      row[header] = values[index] ?? '';
    });
    return row;
  });
}

function formatScientific(value) {
  if (!Number.isFinite(value)) return 'nan';
  if (value === 0) return '0';
  return value.toExponential(6);
}

const bundle = JSON.parse(fs.readFileSync(BUNDLE_PATH, 'utf8'));
const rows = parseCsv(fs.readFileSync(PYTHON_REFERENCE_PATH, 'utf8'));
const targets = bundle.targets.target_order;

const perTarget = {};
for (const target of targets) {
  perTarget[target] = {
    max_abs_error: 0,
    max_relative_error: 0,
    mean_abs_error_sum: 0,
  };
}

let globalMaxAbs = 0;
let globalMaxRelative = 0;
let comparedValues = 0;

for (const row of rows) {
  const result = predictBundle(bundle, {
    particle_material: row.particle_material,
    substrate_material: row.substrate_material,
    impact_velocity_m_s: Number(row.impact_velocity_m_s),
  });
  if (!result.applicability.prediction_authorized) {
    throw new Error(`Authorized training row was rejected: ${row.production_case_id}`);
  }
  for (const target of targets) {
    const jsValue = Number(result.prediction[target]);
    const pyValue = Number(row[`${target}__predicted`]);
    const absError = Math.abs(jsValue - pyValue);
    const denom = Math.max(1, Math.abs(pyValue));
    const relError = absError / denom;
    perTarget[target].max_abs_error = Math.max(perTarget[target].max_abs_error, absError);
    perTarget[target].max_relative_error = Math.max(perTarget[target].max_relative_error, relError);
    perTarget[target].mean_abs_error_sum += absError;
    globalMaxAbs = Math.max(globalMaxAbs, absError);
    globalMaxRelative = Math.max(globalMaxRelative, relError);
    comparedValues += 1;
  }
}

for (const target of targets) {
  perTarget[target].mean_abs_error = perTarget[target].mean_abs_error_sum / rows.length;
  delete perTarget[target].mean_abs_error_sum;
}

const unsupported = predictBundle(bundle, {
  particle_material: 'Cu',
  substrate_material: 'Al6061',
  impact_velocity_m_s: 575,
});
const outOfRange = predictBundle(bundle, {
  particle_material: 'Cu',
  substrate_material: 'Cu',
  impact_velocity_m_s: 1200,
});

const pass = globalMaxRelative < 1e-10 &&
  unsupported.prediction === null &&
  unsupported.applicability.status === 'UNSUPPORTED_PAIR' &&
  outOfRange.prediction === null &&
  outOfRange.applicability.status === 'OUTSIDE_QUALIFIED_VELOCITY_RANGE';

const report = {
  schema_version: '1.0.0',
  decision: pass ? 'PASS_WEBXR_RUNTIME_EQUIVALENCE' : 'FAIL_WEBXR_RUNTIME_EQUIVALENCE',
  bundle: path.relative(ROOT, BUNDLE_PATH),
  runtime: 'webxr/cel_p5_tree_runtime.mjs',
  python_reference: path.relative(ROOT, PYTHON_REFERENCE_PATH),
  rows_replayed: rows.length,
  targets_replayed: targets.length,
  compared_values: comparedValues,
  global_max_abs_error: globalMaxAbs,
  global_max_relative_error: globalMaxRelative,
  per_target: perTarget,
  domain_gate_checks: {
    unsupported_pair_status: unsupported.applicability.status,
    unsupported_pair_prediction_is_null: unsupported.prediction === null,
    out_of_range_status: outOfRange.applicability.status,
    out_of_range_prediction_is_null: outOfRange.prediction === null,
  },
};

fs.writeFileSync(REPORT_JSON, JSON.stringify(report, null, 2), 'utf8');

const targetRows = targets.map(target => (
  `| ${target} | ${formatScientific(perTarget[target].max_abs_error)} | ${formatScientific(perTarget[target].max_relative_error)} |`
));

fs.writeFileSync(
  REPORT_MD,
  [
    '# CEL-P5 WebXR runtime verification',
    '',
    `**Decision:** ${report.decision}.`,
    '',
    `- Rows replayed: ${rows.length}.`,
    `- Targets replayed: ${targets.length}.`,
    `- Compared values: ${comparedValues}.`,
    `- Global max absolute error: ${formatScientific(globalMaxAbs)}.`,
    `- Global max relative error: ${formatScientific(globalMaxRelative)}.`,
    `- Unsupported-pair gate: ${unsupported.applicability.status}, prediction null = ${unsupported.prediction === null}.`,
    `- Out-of-range gate: ${outOfRange.applicability.status}, prediction null = ${outOfRange.prediction === null}.`,
    '',
    '| Target | Max abs error | Max relative error |',
    '|---|---:|---:|',
    ...targetRows,
    '',
    'The JavaScript runtime exactly replays the Python-fitted ExtraTrees bundle to numerical precision and preserves deployment domain gates.',
    '',
  ].join('\n'),
  'utf8',
);

console.log(report.decision);
console.log(`rows=${rows.length} targets=${targets.length} global_max_relative_error=${globalMaxRelative}`);
process.exit(pass ? 0 : 2);
