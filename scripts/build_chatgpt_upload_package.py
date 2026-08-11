"""Build a compact writing-and-verification package for ChatGPT upload.

The package is intended for a second-pass manuscript writer/editor.  It includes
the manuscript draft, all curated manuscript figures/tables and their source
data, the qualified simulation-surrogate datasets, numerical gate reports, KG
provenance notes, and WebXR runtime assets.  It intentionally excludes raw
Abaqus ODB files.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


ROOT = Path(__file__).resolve().parents[1]
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


def add_file(files: List[Tuple[Path, Path]], relpath: str) -> None:
    path = Path(relpath)
    files.append((ROOT / path, path))


def add_tree(
    files: List[Tuple[Path, Path]],
    relroot: str,
    patterns: Iterable[str],
) -> None:
    root = ROOT / relroot
    if not root.exists():
        files.append((root, Path(relroot)))
        return
    for pattern in patterns:
        for src in sorted(root.rglob(pattern)):
            if src.is_file():
                files.append((src, src.relative_to(ROOT)))


def readme_text() -> str:
    return """# ChatGPT upload package: CEL-P5 metal-on-metal cold-spray virtual twin

This folder is a compact, upload-ready handoff for manuscript writing and verification. It contains the current manuscript draft, all manuscript figures and tables, source data behind figures, qualified simulation-surrogate datasets, KG provenance notes, and WebXR deployment/runtime assets.

## Recommended upload order

If ChatGPT accepts the whole ZIP, upload `chatgpt_upload_cel_p5_virtual_twin_*.zip`.

If you need to upload in batches, use this order:

1. `CHATGPT_TASK_PROMPT.md`
2. `paper/manuscript_nature_final.md`
3. `paper/tables/`
4. `paper/nature_figures/` and `paper/nature_figures/source_data/`
5. `reports/`
6. `database/`, `config/`, `manifests/`, `kg/`, `webxr/`, and `webxr_app/`

## Scientific claim boundary

This package supports a knowledge-grounded, agentic virtual-twin manuscript based on bounded Abaqus/CEL simulation-surrogate results for qualified metal-on-metal material-pair domains. It supports claims about:

- reproducible simulation-data qualification gates;
- interpolation inside qualified material-pair/velocity domains;
- model packaging into a WebXR-compatible JavaScript tree runtime;
- KG-assisted provenance and HMI context;
- deployment authorization boundaries that prevent unsupported pair extrapolation.

It does not support claims about:

- experimental validation;
- universal cold-spray bonding thresholds;
- unseen-material-pair prediction;
- autonomous process control;
- production certification.

## Most important files

- `CHATGPT_TASK_PROMPT.md` — instructions for the writing model.
- `paper/manuscript_nature_final.md` — current text draft to revise.
- `paper/manuscript_nature_final.docx` — formatted Word version.
- `paper/AEI_MANUSCRIPT_DESIGN.md` — Advanced Engineering Informatics framing.
- `paper/FIGURE_TABLE_INDEX.md` — figure/table inventory.
- `paper/nature_figures/NATURE_FIGURE_INDEX.md` — Nature-style figure inventory.
- `reports/cel_p4_gate_report.md` — simulation qualification gates.
- `reports/cel_p5_surrogate_training_report.md` — surrogate training and validation.
- `reports/cel_p5_webxr_runtime_verification.md` — WebXR runtime replay verification.
- `reports/cel_p5_kg_webxr_integration_plan.md` — KG/WebXR integration logic.
- `database/cel_p4_simulation_surrogate_dataset.csv` — simulation-derived ML dataset.
- `webxr/cel_p5_kg_webxr_manifest.json` — runtime manifest linking KG, model and gate policy.

## What was intentionally excluded

Raw Abaqus ODB files and heavy intermediate simulation work directories are excluded. The uploaded package uses extracted CSV/JSON/Markdown reports as the verification interface.
"""


def prompt_text() -> str:
    return """# Task for ChatGPT: finish the virtual-twin manuscript

Act as a senior cold-spray additive manufacturing researcher, Abaqus/CEL computational mechanician, machine-learning surrogate-model reviewer, WebXR virtual-twin systems researcher, and scientific editor.

## Goal

Revise `paper/manuscript_nature_final.md` into a polished submission-ready manuscript. The preferred target is Advanced Engineering Informatics; a Nature-style high-impact framing is also acceptable if the claims remain bounded.

## Required scientific stance

Be ambitious in the engineering-informatics framing, but do not overclaim. This is a simulation-surrogate and WebXR virtual-twin paper, not an experimentally validated cold-spray process-map paper.

Use these claim boundaries:

- The CEL-P4 dataset is a numerically qualified simulation dataset.
- The surrogate is valid for interpolation inside the qualified material-pair and velocity domains.
- Leave-one-pair-out performance shows that unseen-pair generalization is not established.
- The WebXR runtime is verified as a faithful replay/export of the Python tree ensemble, not as an experimentally validated controller.
- The knowledge graph provides provenance, design rationale, and HMI context, not new numerical labels.

Avoid these claims unless explicitly marked as future work:

- experimentally validated deposition efficiency;
- universal critical velocity prediction;
- autonomous closed-loop process control;
- transfer to arbitrary metals or unseen dissimilar pairs;
- certification-grade digital twin.

## Files to read first

1. `paper/manuscript_nature_final.md`
2. `paper/AEI_MANUSCRIPT_DESIGN.md`
3. `paper/FIGURE_TABLE_INDEX.md`
4. `paper/nature_figures/NATURE_FIGURE_INDEX.md`
5. `reports/cel_p4_gate_report.md`
6. `reports/cel_p5_surrogate_training_report.md`
7. `reports/cel_p5_webxr_runtime_verification.md`
8. `reports/cel_p5_kg_webxr_integration_plan.md`

## Evidence files

- Simulation and ML datasets: `database/*.csv`
- Material metadata: `config/*.csv`, `config/*.json`
- Production case manifest: `manifests/cel_p4_production_cases.json`
- Extracted simulation results: `extracted/production/CEL_P4/cel_p4_results.json`
- Model card and runtime model: `models/*.json`, `webxr/*.json`, `webxr/*.mjs`
- KG provenance: `kg/ENGINE_OVERVIEW.md`, `kg/extraction_protocol_findings.md`

## Output requested from ChatGPT

Produce a complete revised manuscript with:

- title;
- abstract;
- keywords;
- introduction;
- related work / background;
- methods;
- results;
- virtual-twin/WebXR system section;
- discussion;
- limitations;
- conclusion;
- data and code availability;
- references;
- final figure captions;
- final table captions.

Also produce:

- a reviewer-risk checklist;
- a list of claims that need softening;
- a final submission-readiness checklist.
"""


def main() -> int:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_root = ROOT / f"{PACKAGE_STEM}_{stamp}"
    package_root.mkdir(parents=True, exist_ok=False)

    files: List[Tuple[Path, Path]] = []

    # Repository-level orientation.
    files.extend(
        [
            (ROOT / "README.md", Path("repository_README.md")),
            (ROOT / "DATASET_SCOPE.md", Path("DATASET_SCOPE.md")),
            (ROOT / "CITATION.cff", Path("CITATION.cff")),
            (ROOT / "PACKAGE_MANIFEST.json", Path("source_repository_PACKAGE_MANIFEST.json")),
            (ROOT / "REPOSITORY_MANIFEST.json", Path("REPOSITORY_MANIFEST.json")),
        ]
    )

    # Manuscript draft and paper design artifacts.
    for relpath in [
        "paper/manuscript_nature_final.md",
        "paper/manuscript_nature_final.docx",
        "paper/AEI_MANUSCRIPT_DESIGN.md",
        "paper/FIGURE_TABLE_INDEX.md",
        "paper/nature_figures/NATURE_FIGURE_INDEX.md",
    ]:
        add_file(files, relpath)

    # Manuscript figures, tables, and figure source data.
    add_tree(files, "paper/figures", ["*.png"])
    add_tree(files, "paper/nature_figures", ["*.png", "*.pdf", "*.tiff", "*.md", "*.csv"])
    add_tree(files, "paper/tables", ["*.csv", "*.md", "*.tex"])
    add_tree(files, "reports/figures", ["*.png"])

    # Simulation, ML, KG and WebXR evidence.
    add_tree(files, "database", ["*.csv"])
    add_tree(files, "config", ["*.csv", "*.json"])
    add_tree(files, "manifests", ["*.json"])
    add_tree(files, "extracted/production/CEL_P4", ["*.json"])
    add_tree(files, "reports", ["*.md", "*.json"])
    add_tree(files, "kg", ["*.md", "*.json", "*.jsonl"])
    add_tree(files, "models", ["*.json", "*.joblib"])
    add_tree(files, "webxr", ["*.json", "*.mjs", "*.js"])
    add_tree(files, "webxr_app", ["*.json", "*.mjs", "*.js", "*.html", "*.css"])

    # Reproducibility scripts needed by a reviewer/writing model.
    for relpath in [
        "scripts/generate_nature_manuscript.py",
        "scripts/generate_nature_figures.py",
        "scripts/generate_aei_figures_tables.py",
        "scripts/train_cel_p5_surrogate.py",
        "scripts/verify_cel_p5_webxr_runtime.mjs",
        "scripts/build_cel_p5_kg_webxr_manifest.py",
        "scripts/build_chatgpt_upload_package.py",
    ]:
        add_file(files, relpath)

    # De-duplicate while preserving order.
    seen: set[Tuple[str, str]] = set()
    deduped: List[Tuple[Path, Path]] = []
    for src, relative_dst in files:
        key = (str(src.resolve()) if src.exists() else str(src), str(relative_dst))
        if key not in seen:
            seen.add(key)
            deduped.append((src, relative_dst))

    copied: List[Dict[str, object]] = []
    missing: List[str] = []
    for src, relative_dst in deduped:
        if not src.exists() or not src.is_file():
            missing.append(str(src))
            continue
        copied.append(copy_file(src, package_root / relative_dst))

    readme_path = package_root / "README.md"
    readme_path.write_text(readme_text(), encoding="utf-8", newline="\n")
    copied.append(
        {
            "source": "generated",
            "package_path": str(readme_path),
            "size_bytes": readme_path.stat().st_size,
            "sha256": sha256(readme_path),
        }
    )

    prompt_path = package_root / "CHATGPT_TASK_PROMPT.md"
    prompt_path.write_text(prompt_text(), encoding="utf-8", newline="\n")
    copied.append(
        {
            "source": "generated",
            "package_path": str(prompt_path),
            "size_bytes": prompt_path.stat().st_size,
            "sha256": sha256(prompt_path),
        }
    )

    manifest = {
        "schema_version": "1.1.0",
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
        for path in sorted(package_root.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(package_root.parent))

    print(f"Package folder: {package_root}")
    print(f"Package zip: {zip_path}")
    print(f"Copied/generated files: {len(copied)}")
    print(f"Zip size bytes: {zip_path.stat().st_size}")
    if missing:
        print("Missing files:")
        for item in missing:
            print(f"  {item}")
    return 0 if not missing else 2


if __name__ == "__main__":
    raise SystemExit(main())
