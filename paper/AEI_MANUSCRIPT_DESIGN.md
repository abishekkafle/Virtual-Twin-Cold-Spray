# Advanced Engineering Informatics manuscript design

## Target journal

Advanced Engineering Informatics, Elsevier.

The manuscript must be written as an engineering-informatics contribution, not as a narrowly thermal-spray or computational-mechanics paper. The cold-spray work is the artifact-centered manufacturing case study used to demonstrate a generalizable knowledge-intensive virtual-twin architecture.

## Recommended article type

Original research article.

## Recommended title

**A knowledge-grounded simulation-surrogate virtual twin for metal-on-metal cold spray additive manufacturing**

Alternative, more explicit title:

**Integrating literature knowledge graphs, gated finite-element simulation, and browser-executable surrogates for a WebXR cold-spray virtual twin**

## Central thesis

Knowledge-intensive manufacturing decisions require more than a fast predictor. They require traceable evidence, numerically qualified data, bounded applicability, and human-readable interaction. This paper presents a virtual-twin architecture that connects:

1. a literature/operator knowledge graph for provenance and process context;
2. a gated Abaqus/Explicit CEL simulation campaign for high-fidelity synthetic data;
3. a simulation-surrogate model with explicit deployment-domain gates;
4. a WebXR human-machine interface for in-context decision support.

The manuscript should claim a **qualified simulation-surrogate virtual twin**, not an experimentally validated physical bonding model.

## Positioning for Advanced Engineering Informatics

### Why this fits AEI

The paper supports knowledge-intensive engineering tasks by combining explicit knowledge representation, engineering simulation provenance, machine-learning inference, and immersive decision support. The contribution is not simply "ML predicts cold spray"; it is a reusable informatics pattern for coupling knowledge graphs, gated computational workflows, surrogate models, and human-facing virtual twins.

### What to avoid

- Do not frame the paper primarily as a Johnson-Cook/CEL mechanics study.
- Do not frame the ML model as a universal material predictor.
- Do not claim experimental validation, critical velocity, or bond/no-bond classification.
- Do not bury the KG as background; AEI needs explicit knowledge representation and use.

## Proposed contribution statements

1. A four-layer virtual-twin architecture for knowledge-intensive cold-spray process support, integrating KG provenance, gated CEL simulation, surrogate inference, and WebXR interaction.
2. A gate-based simulation-data qualification protocol that separates numerically accepted simulation-surrogate data from failed, unqualified, or constitutively flagged cases.
3. A 44-case metal-on-metal CEL dataset across four qualified material-pair domains and eleven velocity levels per pair.
4. A browser-executable ExtraTrees simulation surrogate with exact JavaScript/Python runtime equivalence and domain-gated predictions.
5. A transparent claim-boundary model distinguishing interpolation within qualified simulation domains from unsupported unseen-pair or physical-validation claims.

## Research questions

RQ1. How can literature/operator knowledge graphs be coupled with simulation-surrogate models to support knowledge-intensive manufacturing decisions?

RQ2. Can explicit numerical-qualification gates produce a defensible simulation dataset for virtual-twin surrogate training?

RQ3. How accurately can a browser-executable tree-ensemble surrogate interpolate qualified Abaqus/CEL cold-spray responses within solved material-pair domains?

RQ4. How can WebXR interfaces expose prediction results, provenance, and applicability warnings without implying autonomous process authority?

## Recommended abstract logic

1. Problem: engineering virtual twins often separate knowledge provenance, expensive simulations, surrogate prediction, and operator interaction.
2. Gap: this separation is risky in materials/process design because users may treat unqualified simulation or ML outputs as physical truth.
3. Method: present a KG + gated CEL + ML surrogate + WebXR architecture for metal-on-metal cold spray.
4. Dataset: 44 numerically accepted Abaqus/Explicit CEL cases over four qualified pairs.
5. Model result: ExtraTrees interpolation mean R² = 0.9694, mean NRMSE = 0.0363; JavaScript runtime exactly replays Python model over 396 target comparisons.
6. Boundary: leave-one-pair-out mean R² = 0.0381, so unseen-pair prediction is explicitly blocked.
7. Contribution: an auditable, bounded, knowledge-grounded virtual twin for engineering decision support.

## Draft highlights

- A KG-grounded virtual twin architecture links evidence, simulation, ML, and WebXR.
- Numerical gates qualify 44 metal-on-metal Abaqus/CEL cases for surrogate training.
- ExtraTrees interpolates qualified-pair responses with mean R² = 0.9694.
- Browser inference exactly reproduces Python predictions over 396 comparisons.
- Domain gates block unseen-pair and out-of-range virtual-twin predictions.

## Keywords

Engineering informatics; virtual twin; knowledge graph; cold spray additive manufacturing; simulation surrogate; WebXR; finite element analysis; human-machine interface

## Recommended manuscript structure

### 1. Introduction

Purpose: motivate a knowledge-grounded virtual-twin architecture for manufacturing process support.

Key points:

- Cold spray additive manufacturing is a knowledge-intensive engineering task involving materials, process windows, mechanics, operator constraints, and evidence provenance.
- High-fidelity simulation is expensive and slow; surrogate models are fast but risky when detached from validity boundaries.
- Existing digital/virtual twins often under-specify provenance, numerical qualification, and deployment authorization.
- This work proposes a gated, knowledge-grounded virtual twin where every prediction is tied to a qualified simulation domain and KG/HMI context.

End with clear contributions and research questions.

### 2. Related work and informatics gap

Purpose: make AEI reviewers see the gap as informatics, not only cold spray.

Subsections:

2.1 Engineering knowledge graphs and provenance-aware decision support  
2.2 Simulation workflows and surrogate modeling for manufacturing twins  
2.3 Immersive/WebXR interfaces for engineering decision support  
2.4 Gap: disconnected KG, simulation qualification, surrogate inference, and operator HMI

Important framing:

- The novelty is the coupling and governance of the layers, not merely the presence of each layer.

### 3. Knowledge-grounded virtual-twin architecture

Purpose: introduce the system architecture before the cold-spray numerical details.

Subsections:

3.1 Four-layer architecture  
3.2 Knowledge graph and provenance layer  
3.3 Simulation-data qualification layer  
3.4 Surrogate inference and deployment-gating layer  
3.5 WebXR HMI and human-review layer

Use Figure 1 here: system architecture diagram.

Recommended Figure 1:

`KG evidence -> simulation campaign -> gated dataset -> surrogate model -> WebXR runtime -> operator panel`

Show feedback loops:

- KG informs material identity and evidence panels.
- Simulation provides labels.
- Surrogate provides fast interpolation.
- Runtime gates block unsupported conditions.
- HMI displays prediction + provenance + warning.

### 4. Case-study implementation: metal-on-metal cold spray

Purpose: describe enough physics and data generation to make the case study credible.

Subsections:

4.1 Material-pair scope and KG crosswalk  
4.2 Abaqus/Explicit CEL model and numerical controls  
4.3 CEL-P4 production design of experiments  
4.4 Numerical acceptance and constitutive-review gates

Recommended Table 1:

Qualified material-pair domains:

| Pair | Velocity range | Cases | Status | Review flags |
|---|---:|---:|---|---:|
| Cu→Cu | 300–850 m/s | 11 | Qualified | 0 |
| Al6061→SS304 | 500–725 m/s | 11 | Qualified | 0 |
| Ti6Al4V→Ti6Al4V | 500–1150 m/s | 11 | Qualified | 1 |
| Inconel718→Ti6Al4V | 500–1150 m/s | 11 | Qualified | 6 |

Recommended Table 2:

Acceptance gates:

- solver completion;
- contact detected;
- final ALLAE/ALLIE ≤ 0.05;
- abs(ΔETOTAL)/KE0 ≤ 0.02;
- particle-material volume change ≤ 0.01;
- endpoint boundary-return ratio ≤ 0.8;
- no mass scaling;
- maximum T/Tm < 1.0 for ML candidacy.

Recommended Figure 2:

P4 gate dashboard: all 44 cases pass numerical gates; show review-flag cases separately.

### 5. Simulation-surrogate model and validation

Purpose: present ML as a bounded simulation surrogate.

Subsections:

5.1 Feature engineering  
5.2 Target response quantities  
5.3 Model families and selected estimator  
5.4 Pair-aware velocity interpolation validation  
5.5 Leave-one-pair-out boundary audit

Core features:

- impact velocity;
- material-pair categorical features;
- material registry properties;
- `Ek_norm = 0.5 rho_p v^2 / A_p`;
- `H_ratio = A_p / A_s`;
- `T_hom_p = T_ref,p / T_m,p`;
- `T_hom_s = T_ref,s / T_m,s`.

Core result:

Selected model: ExtraTrees.

Pair-aware interpolation:

- mean R² = 0.9694;
- mean NRMSE = 0.0363.

Leave-one-pair-out boundary audit:

- mean R² = 0.0381;
- mean NRMSE = 0.2772.

Interpretation:

- Strong interpolation inside qualified pair domains.
- Weak unseen-pair extrapolation.
- Therefore WebXR runtime should authorize only qualified-pair interpolation.

Recommended Table 3:

Model comparison:

| Model | Interpolation mean R² | Interpolation mean NRMSE | LOPO mean R² | LOPO mean NRMSE |
|---|---:|---:|---:|---:|
| RidgeCV | 0.9579 | 0.0522 | -17.0432 | 1.1298 |
| RandomForest | 0.9439 | 0.0621 | 0.0073 | 0.2859 |
| ExtraTrees | 0.9694 | 0.0363 | 0.0381 | 0.2772 |
| GradientBoosting | 0.9349 | 0.0651 | 0.0893 | 0.2725 |

Recommended Figure 3:

Selected-model parity plots for pair-aware interpolation.

Recommended Figure 4:

Model-comparison bar chart contrasting interpolation and leave-one-pair-out audit.

### 6. WebXR virtual-twin deployment and runtime verification

Purpose: make the software/twin contribution explicit.

Subsections:

6.1 Browser-executable tree-ensemble package  
6.2 Exact Python-to-JavaScript runtime replay  
6.3 Domain-gated prediction policy  
6.4 Three-tier HMI: KG evidence, simulation surrogate, OEM/operator context

Key result:

The JavaScript WebXR runtime exactly replayed Python fitted-model predictions for 44 cases × 9 targets = 396 comparisons, with zero numerical drift.

Recommended Table 4:

Runtime deployment gates:

| Condition | Runtime status |
|---|---|
| Qualified pair + in-range velocity | Prediction authorized as simulation surrogate |
| Unsupported pair | Prediction blocked |
| Out-of-range velocity | Prediction blocked |
| Near constitutive-review region | Prediction shown with warning |
| Experimental/physical validation requested | Not authorized |

Recommended Figure 5:

WebXR HMI screenshot/panel once captured:

- selected material pair;
- velocity slider;
- predicted terminal velocity, flattening, PEEQ, temperature;
- applicability status;
- KG provenance panel.

### 7. Discussion

Purpose: interpret the architecture, not overclaim mechanics.

Subsections:

7.1 What the architecture adds beyond standalone ML  
7.2 Why negative leave-one-pair-out evidence is useful  
7.3 Knowledge/provenance benefits for engineering decision support  
7.4 Generalizability to other artifact-centered engineering processes  
7.5 Limitations and next validation steps

Key discussion points:

- The gate system is a contribution because it prevents model deployment drift.
- The KG is useful because it exposes provenance, material identity, and operator context inside the twin.
- The WebXR runtime is not merely visualization; it is an executable, domain-gated inference layer.
- Experimental validation remains future work.

### 8. Conclusions

Conclude with four concise claims:

1. A KG-grounded simulation-surrogate virtual twin architecture was implemented.
2. A 44-case qualified CEL dataset was generated for four metal-on-metal cold-spray domains.
3. The selected surrogate strongly interpolates within qualified domains but does not generalize to unseen pairs.
4. The WebXR runtime exactly reproduces Python predictions and enforces applicability gates.

## Recommended figure set

Figure 1. Knowledge-grounded virtual-twin architecture.  
Figure 2. CEL-P4 numerical qualification and candidate-gate dashboard.  
Figure 3. ExtraTrees pair-aware interpolation parity plots.  
Figure 4. Interpolation versus leave-one-pair-out validation comparison.  
Figure 5. WebXR HMI showing prediction, applicability, and KG provenance.  
Figure 6. End-to-end traceability example: material pair → KG crosswalk → CEL case → surrogate prediction → WebXR panel.

## Recommended table set

Table 1. Qualified material-pair domains and velocity ranges.  
Table 2. Numerical acceptance and ML-candidate gates.  
Table 3. Surrogate model comparison.  
Table 4. Selected-model interpolation metrics by target.  
Table 5. WebXR runtime and deployment authorization policy.

## Claim language to use

Use:

- "simulation surrogate";
- "qualified-pair interpolation";
- "domain-gated virtual twin";
- "knowledge-grounded decision support";
- "provenance-aware HMI";
- "runtime-equivalent browser deployment".

Avoid:

- "validated physical model";
- "predicts bonding";
- "universal cross-material surrogate";
- "experimentally confirmed";
- "autonomous process optimization".

## Suggested abstract draft

Engineering virtual twins for advanced manufacturing increasingly combine knowledge bases, high-fidelity simulations, surrogate models, and immersive human-machine interfaces, yet these layers are often developed and validated separately. This separation can obscure the provenance and applicability limits of model outputs in knowledge-intensive process-planning tasks. This paper presents a knowledge-grounded simulation-surrogate virtual-twin architecture for metal-on-metal cold spray additive manufacturing. The framework integrates a literature/operator knowledge graph, a gated Abaqus/Explicit coupled Eulerian-Lagrangian simulation campaign, a browser-executable machine-learning surrogate, and a WebXR decision-support interface. A 44-case production simulation dataset was generated across four qualified material-pair domains, with all cases satisfying numerical acceptance gates and ML-candidate criteria. An ExtraTrees surrogate trained on the qualified dataset achieved a pair-aware velocity-interpolation mean R² of 0.9694 and mean normalized RMSE of 0.0363 across nine simulation response quantities. A leave-one-material-pair-out audit produced a mean R² of 0.0381, demonstrating that the surrogate should not be used for unseen-pair prediction. The WebXR JavaScript runtime exactly reproduced the Python fitted model over 396 case-target comparisons and enforced deployment gates for unsupported pairs, out-of-range velocities, and constitutive-review regions. The result is an auditable virtual twin that supports bounded simulation-based decision making with explicit provenance and human-review constraints, rather than an unconstrained physical bonding predictor.

## Immediate next work before full submission

1. Capture the updated WebXR CEL-P5 panel screenshot.
2. Generate Figure 1 architecture diagram and Figure 6 traceability example.
3. Reconcile KG counts in the manuscript text:
   - locally verified merged literature entities: 2070;
   - audited-triples file lines: 6440;
   - NLI-scored literature triples: 3631.
4. Decide whether to submit the dataset repository as the formal data-availability link.
5. Draft the full manuscript in Elsevier single-column style, then convert to Word or LaTeX.
