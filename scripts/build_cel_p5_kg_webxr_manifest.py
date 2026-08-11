"""Build the CEL-P5 KG/WebXR integration manifest and paper-facing plan."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping


ROOT = Path(__file__).resolve().parents[1]
ABAQUS_ROOT = ROOT.parents[1]
KG_ROOT = ABAQUS_ROOT / "cold_spray_kg - Copy"
WEBXR_ROOT = ABAQUS_ROOT / "kg_driven_cold_spray"

P4_RESULTS = ROOT / "extracted" / "production" / "CEL_P4" / "cel_p4_results.json"
P5_METRICS = ROOT / "reports" / "cel_p5_surrogate_metrics.json"
P5_RUNTIME_VERIFICATION = ROOT / "reports" / "cel_p5_webxr_runtime_verification.json"
P5_MODEL_CARD = ROOT / "models" / "cel_p5_surrogate_model_card.json"
P5_BUNDLE = ROOT / "webxr" / "cel_p5_surrogate_tree_ensemble.json"
LEGACY_WEBXR_BUNDLE = WEBXR_ROOT / "data" / "webxr_twin_data.json"
MATERIAL_CROSSWALK = ROOT / "config" / "material_kg_crosswalk.csv"

MANIFEST = ROOT / "webxr" / "cel_p5_kg_webxr_manifest.json"
PLAN = ROOT / "reports" / "cel_p5_kg_webxr_integration_plan.md"


def load_json(path: Path) -> Mapping[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def count_jsonl(path: Path) -> int | None:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8", errors="replace") as stream:
        return sum(1 for line in stream if line.strip())


def rel(path: Path, base: Path = ROOT) -> str:
    try:
        return str(path.relative_to(base)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def read_crosswalk(materials: Iterable[str]) -> List[Dict[str, str]]:
    wanted = set(materials)
    rows = []
    with MATERIAL_CROSSWALK.open("r", encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["simulation_material_id"] in wanted:
                rows.append(row)
    return rows


def markdown_table(rows: List[List[Any]], headers: List[str]) -> str:
    out = ["| " + " | ".join(headers) + " |"]
    out.append("|" + "|".join("---" for _ in headers) + "|")
    for row in rows:
        out.append("| " + " | ".join(str(item) for item in row) + " |")
    return "\n".join(out)


def fmt(value: Any, digits: int = 4) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(number) >= 1e5 or (abs(number) < 1e-3 and number != 0):
        return f"{number:.{digits}e}"
    return f"{number:.{digits}f}"


def main() -> int:
    p4 = load_json(P4_RESULTS)
    p5_metrics = load_json(P5_METRICS)
    runtime = load_json(P5_RUNTIME_VERIFICATION)
    model_card = load_json(P5_MODEL_CARD)
    p5_bundle = load_json(P5_BUNDLE)

    legacy = load_json(LEGACY_WEBXR_BUNDLE) if LEGACY_WEBXR_BUNDLE.exists() else {}

    pair_domains = p5_bundle["scope"]["pair_domains"]
    materials = sorted(p5_bundle["materials"].keys())
    crosswalk = read_crosswalk(materials)

    kg_counts = {
        "literature_entities_merged": count_jsonl(KG_ROOT / "data" / "ontology" / "entities.merged.jsonl"),
        "literature_triples_audited_file": count_jsonl(KG_ROOT / "data" / "ontology" / "triples.audited.jsonl"),
        "literature_triples_nli_scored": count_jsonl(KG_ROOT / "data" / "ontology" / "triples.nli_scored.jsonl"),
        "operator_entities": count_jsonl(KG_ROOT / "data" / "ontology" / "operator_entities.jsonl"),
        "operator_triples": count_jsonl(KG_ROOT / "data" / "ontology" / "operator_triples.jsonl"),
        "bridge_triples": count_jsonl(KG_ROOT / "data" / "ontology" / "bridge_triples.jsonl"),
    }

    selected = p5_metrics["selected_model"]
    selected_interp = next(
        item
        for item in p5_metrics["results"]
        if item["model"] == selected and item["regime"] == "pair_aware_velocity_interpolation"
    )
    selected_lopo = next(
        item
        for item in p5_metrics["results"]
        if item["model"] == selected and item["regime"] == "leave_one_pair_out_boundary_audit"
    )

    manifest = {
        "schema_version": "1.0.0",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "system_title": "Metal-on-metal cold-spray agentic virtual twin, KG + CEL + ML + WebXR",
        "kg_layer": {
            "root": rel(KG_ROOT, ABAQUS_ROOT),
            "engine_overview": rel(KG_ROOT / "ENGINE_OVERVIEW.md", ABAQUS_ROOT),
            "extraction_protocol_findings": rel(KG_ROOT / "extraction_protocol_findings.md", ABAQUS_ROOT),
            "counts": kg_counts,
            "role_in_twin": "evidence/provenance layer for material identity, literature context, operator knowledge, and in-headset citations",
        },
        "legacy_webxr_layer": {
            "root": rel(WEBXR_ROOT, ABAQUS_ROOT),
            "bundle": rel(LEGACY_WEBXR_BUNDLE, ABAQUS_ROOT),
            "version": legacy.get("version"),
            "scope_status": legacy.get("scope_status"),
            "training_cases": legacy.get("training_cases"),
            "supported_pairs_count": len(legacy.get("supported_pairs", [])),
            "demonstration_pairs_count": len(legacy.get("demonstration_pairs", [])),
            "role_after_cel_p5": "retain scene, KG panels, and HMI patterns; supersede demonstration-only surrogate with the CEL-P5 qualified-pair bundle",
        },
        "cel_p4_layer": {
            "decision": p4.get("decision"),
            "case_count": p4.get("case_count"),
            "numerically_passing_case_count": p4.get("numerically_passing_case_count"),
            "ml_candidate_count": p4.get("ml_candidate_count"),
            "constitutive_review_case_count": p4.get("constitutive_review_case_count"),
            "dataset": rel(ROOT / p4.get("dataset_csv", ""), ROOT),
            "gate_report": "reports/cel_p4_gate_report.md",
        },
        "cel_p5_surrogate_layer": {
            "selected_model": selected,
            "interpolation_mean_r2": selected_interp["mean_r2"],
            "interpolation_mean_nrmse": selected_interp["mean_nrmse"],
            "leave_one_pair_out_mean_r2": selected_lopo["mean_r2"],
            "leave_one_pair_out_mean_nrmse": selected_lopo["mean_nrmse"],
            "model_card": rel(P5_MODEL_CARD),
            "metrics": rel(P5_METRICS),
            "webxr_bundle": rel(P5_BUNDLE),
            "webxr_runtime": "webxr/cel_p5_tree_runtime.mjs",
            "runtime_verification": rel(P5_RUNTIME_VERIFICATION),
            "runtime_verification_decision": runtime.get("decision"),
            "supported_pair_domains": pair_domains,
        },
        "material_kg_crosswalk": crosswalk,
        "hmi_tiers": [
            {
                "tier": 1,
                "name": "KG evidence tier",
                "content": "material identity, literature provenance, NLI/evidence support, operator knowledge, DOI/manual-source citations",
            },
            {
                "tier": 2,
                "name": "CEL simulation-surrogate tier",
                "content": "qualified material-pair selector, velocity slider, predicted deformation/temperature/PEEQ/contact outputs, numerical-gate provenance",
            },
            {
                "tier": 3,
                "name": "OEM/operator HMI tier",
                "content": "WarpSPEE3D cell context, safe operating envelope, SOP/fault/hazard panels, and explicit non-autonomous decision support",
            },
        ],
        "claim_boundary": {
            "authorized": [
                "qualified-pair interpolation of Abaqus/Explicit CEL response quantities",
                "browser-executable surrogate inference with exact Python-runtime replay",
                "KG-backed provenance and operator-context visualization",
            ],
            "not_authorized": [
                "experimental physical validation claims",
                "bond/no-bond threshold claims",
                "unseen material-pair prediction",
                "autonomous process control",
            ],
        },
        "recommended_next_actions": [
            "copy cel_p5_surrogate_tree_ensemble.json into kg_driven_cold_spray/data/",
            "copy cel_p5_tree_runtime.mjs into kg_driven_cold_spray/js/",
            "add a small adapter that maps the existing WebXR controls to particle_material, substrate_material, and impact_velocity_m_s",
            "display the runtime applicability status before displaying predictions",
            "surface KG citation panels through the existing kg_client/materials_kg path",
            "capture WebXR screenshots after adapter integration for the manuscript figure set",
        ],
    }

    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    pair_rows = [
        [
            pair,
            domain["particle_material"],
            domain["substrate_material"],
            fmt(domain["velocity_min_m_s"], 1),
            fmt(domain["velocity_max_m_s"], 1),
            domain["constitutive_review_case_count"],
        ]
        for pair, domain in pair_domains.items()
    ]
    crosswalk_rows = [
        [
            row["simulation_material_id"],
            row["kg_canonical_name"],
            row["mapping_type"],
            row["material_scope"],
        ]
        for row in crosswalk
    ]
    hmi_rows = [
        [item["tier"], item["name"], item["content"]]
        for item in manifest["hmi_tiers"]
    ]

    lines = [
        "# CEL-P5 KG/WebXR virtual-twin integration plan",
        "",
        "**Status:** ready for WebXR adapter implementation and manuscript drafting.",
        "",
        "## What is now ready",
        "",
        f"- CEL-P4 simulation gate: `{p4.get('decision')}` with {p4.get('ml_candidate_count')} ML-candidate cases.",
        f"- CEL-P5 selected surrogate: `{selected}` with pair-aware interpolation mean R2 = {selected_interp['mean_r2']:.4f} and mean NRMSE = {selected_interp['mean_nrmse']:.4f}.",
        f"- WebXR runtime verification: `{runtime.get('decision')}` over {runtime.get('rows_replayed')} cases × {runtime.get('targets_replayed')} targets.",
        f"- Leave-one-pair-out audit mean R2 = {selected_lopo['mean_r2']:.4f}; this remains a boundary warning against unseen-pair claims.",
        "",
        "## Knowledge-graph layer",
        "",
        f"- KG root: `{rel(KG_ROOT, ABAQUS_ROOT)}`.",
        f"- Engine overview: `{rel(KG_ROOT / 'ENGINE_OVERVIEW.md', ABAQUS_ROOT)}`.",
        f"- Extraction-protocol findings: `{rel(KG_ROOT / 'extraction_protocol_findings.md', ABAQUS_ROOT)}`.",
        f"- Literature entities merged: {kg_counts['literature_entities_merged']}.",
        f"- Audited-triples file lines: {kg_counts['literature_triples_audited_file']}.",
        f"- NLI-scored literature triples: {kg_counts['literature_triples_nli_scored']}.",
        f"- Operator entities/triples/bridges: {kg_counts['operator_entities']} / {kg_counts['operator_triples']} / {kg_counts['bridge_triples']}.",
        "",
        "The paper should describe the KG as the provenance/evidence layer, not as a source of new simulation labels. We are expanding the simulation campaign, not expanding the KG.",
        "",
        "## Supported CEL-P5 deployment domains",
        "",
        markdown_table(
            pair_rows,
            ["Pair", "Particle", "Substrate", "v min (m/s)", "v max (m/s)", "Review cases"],
        ),
        "",
        "## Material KG crosswalk",
        "",
        markdown_table(
            crosswalk_rows,
            ["Simulation material", "KG canonical", "Mapping", "Scope"],
        ),
        "",
        "## WebXR integration path",
        "",
        "The existing `kg_driven_cold_spray` WebXR bundle is marked demonstration-only (`scope_status = DEMONSTRATION_ONLY_PHYSICS_UNQUALIFIED`, zero supported pairs). The CEL-P5 result should supersede only the surrogate-prediction layer while retaining the scene, KG browser, and HMI patterns.",
        "",
        "Recommended file placement:",
        "",
        "- Copy `webxr/cel_p5_surrogate_tree_ensemble.json` → `kg_driven_cold_spray/data/cel_p5_surrogate_tree_ensemble.json`.",
        "- Copy `webxr/cel_p5_tree_runtime.mjs` → `kg_driven_cold_spray/js/cel_p5_tree_runtime.mjs`.",
        "- Add a small adapter that reads the UI material selectors and impact-velocity slider, calls `predictBundle(bundle, params)`, then writes predictions and applicability warnings to the VR panel.",
        "- Keep existing KG panels wired through `kg_client.js`, `materials_kg.js`, and `research_kg_panel.js`.",
        "",
        "## Three-tier HMI architecture",
        "",
        markdown_table(hmi_rows, ["Tier", "Name", "Content"]),
        "",
        "## Claim boundary for the manuscript",
        "",
        "Allowed claims:",
        "",
        "- a qualified-pair Abaqus/CEL simulation-surrogate virtual twin;",
        "- exact browser replay of the trained Python tree ensemble;",
        "- KG-backed provenance and operator-context panels;",
        "- decision-support HMI, not autonomous control.",
        "",
        "Not allowed yet:",
        "",
        "- external experimental validation;",
        "- physical bonding/no-bonding threshold claims;",
        "- prediction for unseen material pairs;",
        "- universal cross-material model claims.",
        "",
        "## Next concrete step",
        "",
        "Implement the WebXR adapter in `kg_driven_cold_spray`, capture screenshots, then draft the manuscript around the four-pillar architecture: KG provenance, gated CEL simulation, simulation surrogate, and immersive WebXR twin.",
        "",
        f"Machine-readable manifest: `{rel(MANIFEST)}`.",
        "",
    ]
    PLAN.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {rel(MANIFEST)}")
    print(f"Wrote {rel(PLAN)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
