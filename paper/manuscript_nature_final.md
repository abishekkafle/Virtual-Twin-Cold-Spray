# A knowledge-grounded virtual twin for bounded cold-spray process simulation

Abishek Kafle1,*

1 Department of Mechanical Engineering, University of Houston, Houston, TX, USA. *Correspondence: Abishek Kafle.

## Summary

Engineering virtual twins increasingly connect knowledge bases, high-fidelity simulations, machine-learning inference and immersive interfaces, but these layers are often validated separately. We present a knowledge-grounded simulation-surrogate virtual twin for metal-on-metal cold-spray additive manufacturing. The verified dataset contains 44 accepted impact simulations over four material-pair domains. The selected ExtraTrees surrogate achieved pair-aware velocity-interpolation mean R2 = 0.9694 and mean NRMSE = 0.0363 across nine response quantities, while leave-one-material-pair-out auditing gave mean R2 = 0.0381. The browser runtime exactly replayed the Python model over 396 comparisons and blocks unsupported material pairs and out-of-range velocities.

## Manuscript source note

The editable DOCX is the authoritative final manuscript package. This Markdown file is a compact source companion generated from the same script.

## Key quantitative claims

- 44/44 CEL-P4 cases numerically accepted and ML-candidate.
- ExtraTrees pair-aware interpolation mean R2 = 0.9694; mean NRMSE = 0.0363.
- Leave-one-pair-out mean R2 = 0.0381; unseen-pair prediction is blocked.
- WebXR runtime replay: 44 cases x 9 targets = 396 comparisons; max drift = 0.

## Figures

- **Figure 1. Knowledge-grounded virtual-twin architecture.** a, Architecture connecting KG provenance, material crosswalk, qualified CEL simulation, surrogate inference and WebXR decision support. b, Explicit claim boundary separating authorized simulation-surrogate outputs from unsupported physical, unseen-pair and autonomous-control claims. File: `paper/nature_figures/nature_fig01_virtual_twin_architecture.png`
- **Figure 2. Numerical qualification of the CEL simulation campaign.** a, Qualified material-pair and velocity domains for the 44-case CEL-P4 dataset. b, Worst-case numerical gate values normalized by their thresholds. c, Maximum homologous temperature with near-melt review flags retained as metadata. File: `paper/nature_figures/nature_fig02_simulation_qualification.png`
- **Figure 3. CEL response manifolds over qualified metal-on-metal domains.** a-d, Simulation response trends for terminal velocity, particle flattening, normalized crater depth and maximum homologous temperature across the four qualified material-pair domains. File: `paper/nature_figures/nature_fig03_cel_response_manifolds.png`
- **Figure 4. Simulation-surrogate interpolation accuracy.** a, Target-level interpolation R2 values for the selected ExtraTrees surrogate. b-e, Pair-aware velocity-interpolation parity for representative response quantities. The peak-pressure target is retained as a diagnostic because it is visibly less accurate than the deformation, velocity and temperature outputs. File: `paper/nature_figures/nature_fig04_surrogate_validation.png`
- **Figure 5. Deployment-domain gating and browser runtime equivalence.** a, Comparison of pair-aware interpolation and leave-one-pair-out boundary auditing across candidate model families. b, Runtime authorization policy. c, JavaScript/Python replay verification over 44 cases and nine targets. File: `paper/nature_figures/nature_fig05_deployment_gating.png`
- **Figure 6. WebXR traceability from material selection to displayed prediction.** a, Traceability path from a Cu->Cu, 575 m s-1 query through KG crosswalk, CEL provenance, surrogate inference and HMI output. b, WebXR panel mock-up displaying bounded simulation-surrogate predictions and authorization state. File: `paper/nature_figures/nature_fig06_webxr_traceability.png`

## References

1. Papyrin, A., Kosarev, V., Klinkov, S., Alkhimov, A. & Fomin, V. Cold Spray Technology. Elsevier (2007).
2. Assadi, H., Gärtner, F., Stoltenhoff, T. & Kreye, H. Bonding mechanism in cold gas spraying. Acta Materialia 51, 4379-4394 (2003). https://doi.org/10.1016/S1359-6454(03)00274-X.
3. Schmidt, T., Gärtner, F., Assadi, H. & Kreye, H. Development of a generalized parameter window for cold spray deposition. Acta Materialia 54, 729-742 (2006). https://doi.org/10.1016/j.actamat.2005.10.005.
4. Assadi, H., Kreye, H., Gärtner, F. & Klassen, T. Cold spraying - A materials perspective. Acta Materialia 116, 382-407 (2016). https://doi.org/10.1016/j.actamat.2016.06.034.
5. Johnson, G. R. & Cook, W. H. A constitutive model and data for metals subjected to large strains, high strain rates and high temperatures. Proc. 7th International Symposium on Ballistics, 541-547 (1983).
6. Kritzinger, W., Karner, M., Traar, G., Henjes, J. & Sihn, W. Digital Twin in manufacturing: A categorical literature review and classification. IFAC-PapersOnLine 51, 1016-1022 (2018). https://doi.org/10.1016/j.ifacol.2018.08.474.
7. Fuller, A., Fan, Z., Day, C. & Barlow, C. Digital Twin: Enabling technologies, challenges and open research. IEEE Access 8, 108952-108971 (2020). https://doi.org/10.1109/ACCESS.2020.2998358.
8. Hogan, A. et al. Knowledge graphs. ACM Computing Surveys 54, 71:1-71:37 (2021). https://doi.org/10.1145/3447772.
9. Geurts, P., Ernst, D. & Wehenkel, L. Extremely randomized trees. Machine Learning 63, 3-42 (2006). https://doi.org/10.1007/s10994-006-6226-1.
10. Pedregosa, F. et al. Scikit-learn: Machine learning in Python. Journal of Machine Learning Research 12, 2825-2830 (2011).
11. He, P., Gao, J. & Chen, W. DeBERTaV3: Improving DeBERTa using ELECTRA-style pre-training with gradient-disentangled embedding sharing. ICLR (2023). arXiv:2111.09543.
12. World Wide Web Consortium. WebXR Device API. Candidate Recommendation Draft. https://www.w3.org/TR/webxr/.
13. Dassault Systèmes. Abaqus Analysis User's Guide. Dassault Systèmes Simulia Corp. (accessed 2026).
