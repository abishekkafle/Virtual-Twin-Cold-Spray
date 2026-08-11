// Zero-dependency evaluator for webxr/cel_p5_surrogate_tree_ensemble.json.
//
// Intended use:
//   import bundle from './cel_p5_surrogate_tree_ensemble.json' assert { type: 'json' };
//   import { predictBundle } from './cel_p5_tree_runtime.mjs';
//   const result = predictBundle(bundle, {
//     particle_material: 'Cu',
//     substrate_material: 'Cu',
//     impact_velocity_m_s: 575
//   });
//
// This runtime is deliberately strict about domain checks. The CEL-P5 bundle is
// a qualified-pair Abaqus/CEL simulation surrogate; it is not an experimental
// bonding classifier and not an unseen-material extrapolator.

function asFiniteNumber(value, label) {
  const numberValue = Number(value);
  if (!Number.isFinite(numberValue)) {
    throw new Error(`Invalid finite numeric value for ${label}: ${value}`);
  }
  return numberValue;
}

function resolvePair(bundle, params) {
  let pair = params.pair || params.material_pair || null;
  let particle = params.particle_material || params.powder_material || null;
  let substrate = params.substrate_material || null;

  if (pair && pair.includes('__') && !pair.includes('->')) {
    const parts = pair.split('__');
    if (parts.length === 2) {
      particle = particle || parts[0];
      substrate = substrate || parts[1];
      pair = `${parts[0]}->${parts[1]}`;
    }
  }

  if (!pair && particle && substrate) {
    pair = `${particle}->${substrate}`;
  }

  const domain = pair ? bundle.scope?.pair_domains?.[pair] : null;
  if (domain) {
    particle = particle || domain.particle_material;
    substrate = substrate || domain.substrate_material;
  }

  return { pair, particle, substrate, domain };
}

export function buildRawFeatureMap(bundle, params) {
  const { pair, particle, substrate, domain } = resolvePair(bundle, params);
  if (!pair || !particle || !substrate) {
    throw new Error('Provide either pair or particle_material/substrate_material.');
  }

  const materials = bundle.materials || {};
  const particleProperties = materials[particle];
  const substrateProperties = materials[substrate];
  if (!particleProperties || !substrateProperties) {
    throw new Error(`Unknown material combination: ${particle}->${substrate}`);
  }

  const velocity = asFiniteNumber(
    params.impact_velocity_m_s ?? params.velocity_m_s,
    'impact_velocity_m_s'
  );
  const vMin = asFiniteNumber(
    domain?.velocity_min_m_s ?? params.qualified_velocity_min_m_s,
    'qualified_velocity_min_m_s'
  );
  const vMax = asFiniteNumber(
    domain?.velocity_max_m_s ?? params.qualified_velocity_max_m_s,
    'qualified_velocity_max_m_s'
  );

  const raw = {
    pair,
    particle_material: particle,
    substrate_material: substrate,
    impact_velocity_m_s: velocity,
    velocity_fraction: (velocity - vMin) / (vMax - vMin),
    qualified_velocity_min_m_s: vMin,
    qualified_velocity_max_m_s: vMax,
    Ek_norm: 0.5 * particleProperties.density_kg_m3 * velocity * velocity / particleProperties.jc_a_pa,
    H_ratio: particleProperties.jc_a_pa / substrateProperties.jc_a_pa,
    T_hom_p: particleProperties.ref_temp_k / particleProperties.melt_temp_k,
    T_hom_s: substrateProperties.ref_temp_k / substrateProperties.melt_temp_k,
    density_ratio: particleProperties.density_kg_m3 / substrateProperties.density_kg_m3,
    modulus_ratio: particleProperties.elastic_modulus_pa / substrateProperties.elastic_modulus_pa,
    melt_ratio: particleProperties.melt_temp_k / substrateProperties.melt_temp_k,
    conductivity_ratio: particleProperties.conductivity_w_m_k / substrateProperties.conductivity_w_m_k,
  };

  for (const [prefix, properties] of [
    ['particle', particleProperties],
    ['substrate', substrateProperties],
  ]) {
    for (const [name, value] of Object.entries(properties)) {
      raw[`${prefix}_${name}`] = Number(value);
    }
  }

  for (const feature of bundle.features.raw_feature_order) {
    if (!(feature in raw)) {
      throw new Error(`Feature ${feature} was not constructed by the runtime.`);
    }
  }

  return raw;
}

export function transformFeatures(bundle, raw) {
  const transformed = [];
  const categories = bundle.features.categorical_categories || {};

  for (const feature of bundle.features.categorical_features || []) {
    const value = String(raw[feature]);
    for (const category of categories[feature] || []) {
      transformed.push(value === String(category) ? 1 : 0);
    }
  }

  const means = bundle.features.numeric_mean || [];
  const scales = bundle.features.numeric_scale || [];
  const numericFeatures = bundle.features.numeric_features || [];
  for (let index = 0; index < numericFeatures.length; index += 1) {
    const feature = numericFeatures[index];
    const value = asFiniteNumber(raw[feature], feature);
    const scale = scales[index] === 0 ? 1 : scales[index];
    transformed.push((value - means[index]) / scale);
  }

  return transformed;
}

function evaluateTree(tree, features) {
  let node = 0;
  while (tree.feature[node] >= 0) {
    node = features[tree.feature[node]] <= tree.threshold[node]
      ? tree.children_left[node]
      : tree.children_right[node];
  }
  return tree.value_scaled[node];
}

function inverseTransformTargets(bundle, scaledPrediction) {
  const means = bundle.targets.target_mean;
  const scales = bundle.targets.target_scale;
  const targetOrder = bundle.targets.target_order;
  const prediction = {};
  for (let index = 0; index < targetOrder.length; index += 1) {
    prediction[targetOrder[index]] = scaledPrediction[index] * scales[index] + means[index];
  }
  return prediction;
}

function domainApplicability(bundle, raw) {
  const domain = bundle.scope?.pair_domains?.[raw.pair] || null;
  const outOfRangeFeatures = [];
  const featureMin = bundle.features.training_min || {};
  const featureMax = bundle.features.training_max || {};

  for (const feature of bundle.features.numeric_features || []) {
    const value = Number(raw[feature]);
    if (!Number.isFinite(value)) continue;
    const min = featureMin[feature];
    const max = featureMax[feature];
    if (Number.isFinite(min) && value < min) {
      outOfRangeFeatures.push({ feature, value, min, max, side: 'below' });
    } else if (Number.isFinite(max) && value > max) {
      outOfRangeFeatures.push({ feature, value, min, max, side: 'above' });
    }
  }

  const withinVelocityRange = Boolean(
    domain &&
    raw.impact_velocity_m_s >= domain.velocity_min_m_s &&
    raw.impact_velocity_m_s <= domain.velocity_max_m_s
  );

  const reviewCases = domain?.constitutive_review_cases || [];
  const firstReviewVelocity = reviewCases.length
    ? Math.min(...reviewCases.map(item => Number(item.velocity_m_s)))
    : null;
  const nearConstitutiveReviewRegion = Number.isFinite(firstReviewVelocity)
    ? raw.impact_velocity_m_s >= firstReviewVelocity
    : false;

  let status = 'PREDICTION_AUTHORIZED_SIMULATION_SURROGATE';
  let predictionAuthorized = true;
  if (!domain) {
    status = 'UNSUPPORTED_PAIR';
    predictionAuthorized = false;
  } else if (!withinVelocityRange) {
    status = 'OUTSIDE_QUALIFIED_VELOCITY_RANGE';
    predictionAuthorized = false;
  }

  return {
    represented_pair: Boolean(domain),
    prediction_authorized: predictionAuthorized,
    status,
    qualified_pair_domain: domain,
    within_velocity_range: withinVelocityRange,
    out_of_range_features: outOfRangeFeatures,
    near_constitutive_review_region: nearConstitutiveReviewRegion,
    constitutive_review_cases: reviewCases,
    claim_boundary: bundle.scope?.authorized_use || 'simulation-surrogate interpolation only',
    not_authorized_for: bundle.scope?.not_authorized_for || [],
  };
}

export function predictBundle(bundle, params) {
  const resolved = resolvePair(bundle, params);
  if (!resolved.domain) {
    const pair = resolved.pair || 'UNRESOLVED_PAIR';
    return {
      prediction: null,
      target_labels: bundle.targets.labels,
      applicability: {
        represented_pair: false,
        prediction_authorized: false,
        status: 'UNSUPPORTED_PAIR',
        qualified_pair_domain: null,
        within_velocity_range: false,
        out_of_range_features: [],
        near_constitutive_review_region: false,
        constitutive_review_cases: [],
        attempted_pair: pair,
        claim_boundary: bundle.scope?.authorized_use || 'simulation-surrogate interpolation only',
        not_authorized_for: bundle.scope?.not_authorized_for || [],
      },
    };
  }

  const raw = buildRawFeatureMap(bundle, params);
  const applicability = domainApplicability(bundle, raw);
  if (!applicability.prediction_authorized) {
    return {
      prediction: null,
      target_labels: bundle.targets.labels,
      applicability,
    };
  }

  const features = transformFeatures(bundle, raw);
  const targetCount = bundle.targets.target_order.length;
  const accumulator = Array(targetCount).fill(0);
  const trees = bundle.ensemble.trees || [];
  for (const tree of trees) {
    const value = evaluateTree(tree, features);
    for (let index = 0; index < targetCount; index += 1) {
      accumulator[index] += value[index];
    }
  }
  const scaledPrediction = accumulator.map(value => value / trees.length);

  return {
    prediction: inverseTransformTargets(bundle, scaledPrediction),
    target_labels: bundle.targets.labels,
    applicability,
  };
}
