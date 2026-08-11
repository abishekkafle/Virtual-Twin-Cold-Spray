"""Create a compact ChatGPT-verification package for the CEL-P5 virtual twin."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
ABAQUS_ROOT = ROOT.parents[1]
KG_ROOT = ABAQUS_ROOT / "cold_spray_kg - Copy"
WEBXR_ROOT = ABAQUS_ROOT / "kg_driven_cold_spray"

PACKAGE_STEM = "chatgpt_upload_cel_p5_virtual_twin"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_file(src: Path, dst: Path) -> Dict[str, object]:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return {
        "source": str(src),
        "package_path": str(dst),
        "size_bytes": dst.stat().st_size,
        "sha256": sha256(dst),
    }


def main() -> int:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_root = ROOT / f"{PACKAGE_STEM}_{stamp}"
    package_root.mkdir(parents=True, exist_ok=False)

    files: List[Tuple[Path, Path]] = [
        (ROOT / "reports" / "cel_p4_protocol.md", Path("reports/cel_p4_protocol.md")),
        (ROOT / "reports" / "cel_p4_datacheck_report.md", Path("reports/cel_p4_datacheck_report.md")),
        (ROOT / "reports" / "cel_p4_gate_report.md", Path("reports/cel_p4_gate_report.md")),
        (ROOT / "reports" / "cel_p4_parallel_solve_ledger.json", Path("reports/cel_p4_parallel_solve_ledger.json")),
        (ROOT / "reports" / "cel_p4_extract_parallel_ledger.json", Path("reports/cel_p4_extract_parallel_ledger.json")),
        (ROOT / "reports" / "cel_p5_surrogate_training_report.md", Path("reports/cel_p5_surrogate_training_report.md")),
        (ROOT / "reports" / "cel_p5_surrogate_metrics.json", Path("reports/cel_p5_surrogate_metrics.json")),
        (ROOT / "reports" / "cel_p5_webxr_runtime_verification.md", Path("reports/cel_p5_webxr_runtime_verification.md")),
        (ROOT / "reports" / "cel_p5_webxr_runtime_verification.json", Path("reports/cel_p5_webxr_runtime_verification.json")),
        (ROOT / "reports" / "cel_p5_kg_webxr_integration_plan.md", Path("reports/cel_p5_kg_webxr_integration_plan.md")),
        (ROOT / "config" / "cel_p4_acceptance_gates.json", Path("config/cel_p4_acceptance_gates.json")),
        (ROOT / "config" / "cel_p3_final_disposition.json", Path("config/cel_p3_final_disposition.json")),
        (ROOT / "config" / "material_registry.csv", Path("config/material_registry.csv")),
        (ROOT / "config" / "material_kg_crosswalk.csv", Path("config/material_kg_crosswalk.csv")),
        (ROOT / "manifests" / "cel_p4_production_cases.json", Path("manifests/cel_p4_production_cases.json")),
        (ROOT / "extracted" / "production" / "CEL_P4" / "cel_p4_results.json", Path("extracted/production/CEL_P4/cel_p4_results.json")),
        (ROOT / "database" / "cel_p4_simulation_surrogate_dataset.csv", Path("database/cel_p4_simulation_surrogate_dataset.csv")),
        (ROOT / "database" / "cel_p5_surrogate_predictions.csv", Path("database/cel_p5_surrogate_predictions.csv")),
        (ROOT / "database" / "cel_p5_final_model_predictions.csv", Path("database/cel_p5_final_model_predictions.csv")),
        (ROOT / "models" / "cel_p5_surrogate_model_card.json", Path("models/cel_p5_surrogate_model_card.json")),
        (ROOT / "models" / "cel_p5_extra_trees_surrogate.joblib", Path("models/cel_p5_extra_trees_surrogate.joblib")),
        (ROOT / "webxr" / "cel_p5_surrogate_tree_ensemble.json", Path("webxr/cel_p5_surrogate_tree_ensemble.json")),
        (ROOT / "webxr" / "cel_p5_tree_runtime.mjs", Path("webxr/cel_p5_tree_runtime.mjs")),
        (ROOT / "webxr" / "cel_p5_kg_webxr_manifest.json", Path("webxr/cel_p5_kg_webxr_manifest.json")),
        (ROOT / "scripts" / "train_cel_p5_surrogate.py", Path("scripts/train_cel_p5_surrogate.py")),
        (ROOT / "scripts" / "verify_cel_p5_webxr_runtime.mjs", Path("scripts/verify_cel_p5_webxr_runtime.mjs")),
        (ROOT / "scripts" / "build_cel_p5_kg_webxr_manifest.py", Path("scripts/build_cel_p5_kg_webxr_manifest.py")),
        (ROOT / "scripts" / "build_chatgpt_upload_package.py", Path("scripts/build_chatgpt_upload_package.py")),
        (KG_ROOT / "ENGINE_OVERVIEW.md", Path("kg/ENGINE_OVERVIEW.md")),
        (KG_ROOT / "extraction_protocol_findings.md", Path("kg/extraction_protocol_findings.md")),
        (WEBXR_ROOT / "cold_spray_cel_p5_model.js", Path("webxr_app/cold_spray_cel_p5_model.js")),
        (WEBXR_ROOT / "js" / "cel_p5_model_adapter.js", Path("webxr_app/js/cel_p5_model_adapter.js")),
        (WEBXR_ROOT / "js" / "cel_p5_tree_runtime.mjs", Path("webxr_app/js/cel_p5_tree_runtime.mjs")),
    ]

    for figure in [
        "cel_p5_interpolation_parity.png",
        "cel_p5_lopo_boundary_parity.png",
        "cel_p5_model_comparison.png",
        "cel_p5_velocity_response_curves.png",
    ]:
        files.append((ROOT / "reports" / "figures" / figure, Path("reports/figures") / figure))

    copied = []
    missing = []
    for src, relative_dst in files:
        if not src.exists():
            missing.append(str(src))
            continue
        copied.append(copy_file(src, package_root / relative_dst))

    readme = package_root / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# CEL-P5 metal-on-metal cold-spray virtual twin verification package",
                "",
                "This package is intentionally compact: it includes extracted/aggregated data, gates, reports, figures, the trained model card, the WebXR tree bundle/runtime, and KG provenance documents. It excludes Abaqus ODB files because they are too large for ordinary upload; the gate reports and extracted CSV/JSON files are the verification interface.",
                "",
                "## Key claims supported by this package",
                "",
                "- CEL-P4 production DOE passed: 44/44 cases numerically accepted and ML-candidate.",
                "- CEL-P5 ExtraTrees simulation surrogate trained for four qualified material-pair domains.",
                "- Pair-aware velocity interpolation mean R2 = 0.9694; mean NRMSE = 0.0363.",
                "- Leave-one-pair-out mean R2 = 0.0381, so unseen-pair generalization is not claimed.",
                "- WebXR runtime exactly replays the Python fitted model over 44 cases × 9 targets.",
                "- KG is used as provenance/HMI context, not as a source of new simulation labels.",
                "",
                "## Start here",
                "",
                "1. `reports/cel_p5_surrogate_training_report.md`",
                "2. `reports/cel_p5_webxr_runtime_verification.md`",
                "3. `reports/cel_p5_kg_webxr_integration_plan.md`",
                "4. `webxr/cel_p5_kg_webxr_manifest.json`",
                "",
                "## Claim boundary",
                "",
                "This package supports a qualified-pair Abaqus/CEL simulation-surrogate virtual twin. It does not support experimental validation, physical bond/no-bond thresholds, unseen-pair prediction, or autonomous control claims.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    copied.append(
        {
            "source": "generated",
            "package_path": str(readme),
            "size_bytes": readme.stat().st_size,
            "sha256": sha256(readme),
        }
    )

    manifest = {
        "schema_version": "1.0.0",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "package_root": str(package_root),
        "file_count": len(copied),
        "missing_sources": missing,
        "files": copied,
    }
    manifest_path = package_root / "PACKAGE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    zip_path = ROOT / f"{package_root.name}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in package_root.rglob("*"):
            archive.write(path, path.relative_to(package_root.parent))

    print(f"Package folder: {package_root}")
    print(f"Package zip: {zip_path}")
    print(f"Copied files: {len(copied)}")
    if missing:
        print("Missing files:")
        for item in missing:
            print(f"  {item}")
    return 0 if not missing else 2


if __name__ == "__main__":
    raise SystemExit(main())
