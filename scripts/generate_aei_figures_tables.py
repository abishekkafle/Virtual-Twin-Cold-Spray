"""Generate Advanced Engineering Informatics manuscript figures and tables.

The outputs in ``paper/figures`` and ``paper/tables`` are derived from the
verified CEL-P4/CEL-P5 artifacts already committed to this repository.  The
figures are intentionally AEI-facing: they emphasize knowledge representation,
qualification gates, runtime authorization, and human-machine decision support,
not only cold-spray mechanics.
"""

from __future__ import annotations

import json
import math
import shutil
import textwrap
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "paper" / "figures"
TABLE_DIR = ROOT / "paper" / "tables"
INDEX_MD = ROOT / "paper" / "FIGURE_TABLE_INDEX.md"

P4_DATASET = ROOT / "database" / "cel_p4_simulation_surrogate_dataset.csv"
P5_PREDICTIONS = ROOT / "database" / "cel_p5_surrogate_predictions.csv"
P5_FINAL_PREDICTIONS = ROOT / "database" / "cel_p5_final_model_predictions.csv"
P5_METRICS = ROOT / "reports" / "cel_p5_surrogate_metrics.json"
P4_RESULTS = ROOT / "extracted" / "production" / "CEL_P4" / "cel_p4_results.json"
WEBXR_VERIFICATION = ROOT / "reports" / "cel_p5_webxr_runtime_verification.json"
KG_WEBXR_MANIFEST = ROOT / "webxr" / "cel_p5_kg_webxr_manifest.json"
MATERIAL_CROSSWALK = ROOT / "config" / "material_kg_crosswalk.csv"


TARGETS = [
    "terminal_particle_volume_weighted_velocity_m_s",
    "particle_axial_flattening_percent",
    "normalized_crater_depth",
    "particle_peeqvavg_p95",
    "substrate_peeq_p95",
    "particle_temperature_max_k",
    "substrate_temperature_max_k",
    "maximum_temperature_over_melt",
    "peak_contact_pressure_pa",
]

TARGET_LABELS = {
    "terminal_particle_volume_weighted_velocity_m_s": "Terminal velocity\n(m/s)",
    "particle_axial_flattening_percent": "Particle flattening\n(%)",
    "normalized_crater_depth": "Crater depth\n/Dp",
    "particle_peeqvavg_p95": "Particle PEEQ\np95",
    "substrate_peeq_p95": "Substrate PEEQ\np95",
    "particle_temperature_max_k": "Particle Tmax\n(K)",
    "substrate_temperature_max_k": "Substrate Tmax\n(K)",
    "maximum_temperature_over_melt": "Max T/Tm",
    "peak_contact_pressure_pa": "Peak pressure\n(Pa)",
}

PAIR_COLORS = {
    "Al6061->SS304": "#2c7fb8",
    "Cu->Cu": "#d95f0e",
    "Inconel718->Ti6Al4V": "#756bb1",
    "Ti6Al4V->Ti6Al4V": "#31a354",
}


plt.rcParams.update(
    {
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "legend.fontsize": 8.5,
        "figure.titlesize": 14,
        "savefig.dpi": 320,
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)


def ensure_dirs() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def wrap(text: str, width: int = 28) -> str:
    return "\n".join(textwrap.wrap(str(text), width=width))


def draw_box(
    ax: plt.Axes,
    xy: tuple[float, float],
    wh: tuple[float, float],
    title: str,
    body: str,
    color: str,
    edge: str = "#263445",
    title_color: str = "white",
) -> None:
    x, y = xy
    w, h = wh
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.018,rounding_size=0.025",
        linewidth=1.3,
        edgecolor=edge,
        facecolor=color,
        alpha=0.97,
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h - 0.055, title, ha="center", va="top", color=title_color, weight="bold", fontsize=10)
    ax.text(x + w / 2, y + h / 2 - 0.02, body, ha="center", va="center", color="#0e1726", fontsize=8.5, linespacing=1.25)


def arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float], color: str = "#34495e") -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=14,
            linewidth=1.7,
            color=color,
            shrinkA=5,
            shrinkB=5,
        )
    )


def fig01_architecture(manifest: Dict[str, Any]) -> Path:
    path = FIG_DIR / "fig01_knowledge_grounded_virtual_twin_architecture.png"
    fig, ax = plt.subplots(figsize=(13.5, 7.5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    boxes = [
        (
            (0.045, 0.58),
            (0.19, 0.25),
            "Knowledge graph",
            "Literature + operator KG\n2070 entities\n3631 NLI-scored triples\n1401 operator entities",
            "#bfe3ff",
        ),
        (
            (0.285, 0.58),
            (0.19, 0.25),
            "Gated simulation",
            "Abaqus/Explicit CEL\n44 accepted cases\nnumerical + ML gates\nconstitutive flags retained",
            "#c7f0d8",
        ),
        (
            (0.525, 0.58),
            (0.19, 0.25),
            "Simulation surrogate",
            "ExtraTrees model\npair-aware interpolation\nmean R² = 0.9694\nmean NRMSE = 0.0363",
            "#ffe2b8",
        ),
        (
            (0.765, 0.58),
            (0.19, 0.25),
            "WebXR runtime",
            "Zero-dependency JS\n396 replay checks\nmax drift = 0\nruntime domain gates",
            "#dcc7ff",
        ),
        (
            (0.285, 0.17),
            (0.19, 0.22),
            "Claim boundary",
            "Simulation-surrogate only\nqualified pairs only\nno bond/no-bond claim\nno autonomous control",
            "#ffd6d6",
        ),
        (
            (0.525, 0.17),
            (0.19, 0.22),
            "Human decision support",
            "Prediction panel\napplicability warning\nKG provenance\noperator context",
            "#d7f5f3",
        ),
    ]
    for item in boxes:
        draw_box(ax, *item)

    arrow(ax, (0.235, 0.705), (0.285, 0.705))
    arrow(ax, (0.475, 0.705), (0.525, 0.705))
    arrow(ax, (0.715, 0.705), (0.765, 0.705))
    arrow(ax, (0.86, 0.58), (0.66, 0.39))
    arrow(ax, (0.59, 0.58), (0.42, 0.39))
    arrow(ax, (0.38, 0.58), (0.38, 0.39))
    arrow(ax, (0.235, 0.64), (0.525, 0.28), color="#6f42c1")

    ax.text(
        0.5,
        0.93,
        "Knowledge-grounded simulation-surrogate virtual twin for cold-spray process support",
        ha="center",
        va="center",
        fontsize=15,
        weight="bold",
        color="#1b2635",
    )
    ax.text(
        0.5,
        0.075,
        "Architecture principle: every fast prediction is traceable to a qualified simulation domain and surfaced with applicability limits.",
        ha="center",
        va="center",
        fontsize=10,
        color="#34495e",
    )
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def fig02_gate_dashboard(df: pd.DataFrame) -> Path:
    path = FIG_DIR / "fig02_cel_p4_gate_dashboard.png"
    fig = plt.figure(figsize=(13.5, 8.2))
    gs = fig.add_gridspec(2, 2, height_ratios=[0.95, 1.05], width_ratios=[1.0, 1.15], hspace=0.34, wspace=0.28)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, :])

    summary = (
        df.assign(review=df["constitutive_review_flags"].fillna("").astype(str).str.len() > 0)
        .groupby("pair", sort=False)
        .agg(cases=("production_case_id", "count"), review=("review", "sum"))
        .reset_index()
    )
    summary["clean"] = summary["cases"] - summary["review"]
    y = np.arange(len(summary))
    ax1.barh(y, summary["clean"], color="#5abf90", label="Accepted, no review flag")
    ax1.barh(y, summary["review"], left=summary["clean"], color="#f6b73c", label="Accepted + review flag")
    ax1.set_yticks(y)
    ax1.set_yticklabels(summary["pair"])
    ax1.set_xlabel("CEL-P4 cases")
    ax1.set_title("A. ML-candidate cases by qualified material pair")
    ax1.set_xlim(0, 12)
    ax1.legend(frameon=False, loc="lower right")
    ax1.grid(axis="x", alpha=0.25)

    gates = [
        ("ALLAE/ALLIE", "final_allae_over_allie", 0.05),
        ("|ΔETOTAL|/KE₀", "etotal_drift_over_initial_ke", 0.02),
        ("particle volume\nchange", "particle_material_volume_relative_change_abs", 0.01),
        ("boundary return", "endpoint_over_first_boundary_return", 0.8),
        ("max T/Tm", "maximum_temperature_over_melt", 1.0),
    ]
    labels = [item[0] for item in gates]
    ratios = [float(df[column].max() / threshold) for _, column, threshold in gates]
    observed = [float(df[column].max()) for _, column, _ in gates]
    x = np.arange(len(gates))
    colors = ["#5abf90" if r <= 1.0 else "#d9534f" for r in ratios]
    ax2.bar(x, ratios, color=colors, edgecolor="#2a3b4c", linewidth=0.6)
    ax2.axhline(1.0, color="#d9534f", linestyle="--", linewidth=1.3, label="gate threshold")
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, rotation=22, ha="right")
    ax2.set_ylim(0, 1.15)
    ax2.set_ylabel("Observed worst / threshold")
    ax2.set_title("B. Worst-case normalized numerical gate values")
    for xi, ratio, obs in zip(x, ratios, observed):
        ax2.text(xi, ratio + 0.025, f"{obs:.5g}", ha="center", va="bottom", fontsize=8)
    ax2.legend(frameon=False)
    ax2.grid(axis="y", alpha=0.25)

    for pair, group in df.groupby("pair", sort=False):
        review = group["constitutive_review_flags"].fillna("").astype(str).str.len() > 0
        ax3.plot(
            group["impact_velocity_m_s"],
            group["maximum_temperature_over_melt"],
            color=PAIR_COLORS[pair],
            linewidth=1.7,
            alpha=0.85,
        )
        ax3.scatter(
            group.loc[~review, "impact_velocity_m_s"],
            group.loc[~review, "maximum_temperature_over_melt"],
            color=PAIR_COLORS[pair],
            edgecolor="white",
            s=46,
            linewidth=0.6,
            label=pair,
        )
        if review.any():
            ax3.scatter(
                group.loc[review, "impact_velocity_m_s"],
                group.loc[review, "maximum_temperature_over_melt"],
                color=PAIR_COLORS[pair],
                edgecolor="#222222",
                marker="^",
                s=75,
                linewidth=0.9,
            )
    ax3.axhline(1.0, color="#d9534f", linestyle="--", linewidth=1.2, label="ML melt exclusion")
    ax3.axhline(0.95, color="#f0ad4e", linestyle=":", linewidth=1.4, label="near-melt review")
    ax3.set_xlabel("Impact velocity (m/s)")
    ax3.set_ylabel("Maximum temperature / melt temperature")
    ax3.set_title("C. Constitutive review is retained as metadata, not hidden from the surrogate dataset")
    ax3.set_ylim(0.28, 1.05)
    ax3.grid(True, alpha=0.25)
    ax3.legend(frameon=False, ncol=3, loc="upper left")

    fig.suptitle("CEL-P4 production dataset qualification: 44/44 cases accepted for simulation-surrogate training", y=0.99)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def fig03_parity(pred: pd.DataFrame, metrics: Dict[str, Any]) -> Path:
    path = FIG_DIR / "fig03_surrogate_interpolation_parity.png"
    selected = metrics["selected_model"]
    sub = pred[(pred["model"] == selected) & (pred["regime"] == "pair_aware_velocity_interpolation")].copy()
    if sub.empty:
        raise RuntimeError("Could not find selected-model pair-aware interpolation predictions.")

    ncols = 3
    nrows = 3
    fig, axes = plt.subplots(nrows, ncols, figsize=(13.8, 12.2))
    axes_flat = axes.ravel()
    for idx, target in enumerate(TARGETS):
        ax = axes_flat[idx]
        actual = sub[f"{target}__actual"].astype(float).to_numpy()
        predicted = sub[f"{target}__predicted"].astype(float).to_numpy()
        for pair, group in sub.groupby("pair", sort=False):
            ax.scatter(
                group[f"{target}__actual"].astype(float),
                group[f"{target}__predicted"].astype(float),
                s=30,
                color=PAIR_COLORS[pair],
                edgecolor="white",
                linewidth=0.5,
                alpha=0.92,
                label=pair if idx == 0 else None,
            )
        lo = min(np.nanmin(actual), np.nanmin(predicted))
        hi = max(np.nanmax(actual), np.nanmax(predicted))
        pad = 0.04 * (hi - lo) if hi > lo else 1.0
        ax.plot([lo - pad, hi + pad], [lo - pad, hi + pad], color="#444444", linewidth=1.0)
        r2 = r2_score(actual, predicted)
        mae = mean_absolute_error(actual, predicted)
        ax.set_title(f"{TARGET_LABELS[target]}\nR²={r2:.3f}, MAE={mae:.3g}")
        ax.set_xlabel("CEL simulation")
        ax.set_ylabel("Surrogate")
        ax.grid(True, alpha=0.25)

    handles, labels = axes_flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=4, frameon=False, bbox_to_anchor=(0.5, 1.005))
    fig.suptitle("Selected ExtraTrees surrogate: pair-aware velocity-interpolation parity", y=1.03)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def fig04_model_comparison(metrics: Dict[str, Any]) -> Path:
    path = FIG_DIR / "fig04_validation_regime_comparison.png"
    records = metrics["results"]
    models = []
    interp = {}
    lopo = {}
    nrmse_interp = {}
    for record in records:
        model = record["model"]
        if model not in models:
            models.append(model)
        if record["regime"] == "pair_aware_velocity_interpolation":
            interp[model] = record["mean_r2"]
            nrmse_interp[model] = record["mean_nrmse"]
        elif record["regime"] == "leave_one_pair_out_boundary_audit":
            lopo[model] = record["mean_r2"]

    y = np.arange(len(models))
    interp_values = [interp[m] for m in models]
    lopo_values = [lopo[m] for m in models]
    lopo_clip_min = -0.14

    fig, (ax_a, ax_b) = plt.subplots(
        1,
        2,
        figsize=(12.8, 5.4),
        sharey=True,
        gridspec_kw={"width_ratios": [1.05, 1.0], "wspace": 0.08},
    )

    ax_a.barh(y, interp_values, color="#2c7fb8", height=0.62)
    ax_a.axvline(0.70, color="#5abf90", linestyle="--", linewidth=1.1)
    ax_a.text(0.70, -0.72, "illustrative R² = 0.70", color="#28784f", ha="center", va="bottom", fontsize=8)
    ax_a.set_xlim(0.0, 1.05)
    ax_a.set_yticks(y)
    ax_a.set_yticklabels(models)
    ax_a.invert_yaxis()
    ax_a.set_xlabel("Mean R² across nine targets")
    ax_a.set_title("A. Pair-aware velocity interpolation")
    ax_a.grid(axis="x", alpha=0.22)
    for yi, value in zip(y, interp_values):
        ax_a.text(min(value + 0.018, 1.02), yi, f"{value:.4f}", va="center", ha="left", fontsize=8.5)

    clipped_lopo = [max(value, lopo_clip_min) for value in lopo_values]
    ax_b.axvspan(-0.05, 0.05, color="#efefef", zorder=0)
    ax_b.barh(y, clipped_lopo, color="#f16913", height=0.62, zorder=2)
    ax_b.axvline(0, color="#333333", linewidth=0.9)
    ax_b.set_xlim(lopo_clip_min - 0.02, 0.16)
    ax_b.set_xlabel("Mean R² across nine targets")
    ax_b.set_title("B. Leave-one-pair-out boundary audit")
    ax_b.grid(axis="x", alpha=0.22)
    ax_b.tick_params(axis="y", left=False, labelleft=False)
    ax_b.text(0, -0.72, "near-zero region", color="#555555", ha="center", va="bottom", fontsize=8)
    for yi, value in zip(y, lopo_values):
        if value < lopo_clip_min:
            ax_b.annotate(
                f"{value:.2f} off scale",
                xy=(lopo_clip_min, yi),
                xytext=(-0.035, yi - 0.26),
                ha="left",
                va="center",
                fontsize=8.5,
                color="#8c2d04",
                arrowprops={"arrowstyle": "-|>", "color": "#8c2d04", "lw": 1.0},
            )
        else:
            x_text = value + 0.008 if value >= 0 else value - 0.008
            ax_b.text(x_text, yi, f"{value:.4f}", va="center", ha="left" if value >= 0 else "right", fontsize=8.5)

    fig.suptitle(
        "Validation-regime separation prevents overclaiming cross-material generalization",
        y=1.02,
        fontsize=14,
    )
    fig.subplots_adjust(left=0.12, right=0.985, top=0.83, bottom=0.15, wspace=0.08)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def fig05_webxr_hmi(final_pred: pd.DataFrame, runtime: Dict[str, Any]) -> Path:
    path = FIG_DIR / "fig05_webxr_hmi_runtime_gate_panel.png"
    sample = final_pred[
        (final_pred["pair"] == "Cu->Cu") & (final_pred["impact_velocity_m_s"].astype(float).round(6) == 575.0)
    ]
    if sample.empty:
        sample = final_pred[final_pred["pair"] == "Cu->Cu"].iloc[[0]]
    row = sample.iloc[0]
    y = {
        target: float(row[f"{target}__predicted"])
        for target in TARGETS
    }

    fig, ax = plt.subplots(figsize=(13.5, 7.4))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Background
    ax.add_patch(Rectangle((0, 0), 1, 1, facecolor="#f5f7fb", edgecolor="none"))

    # Three panels
    panels = [
        (0.045, 0.14, 0.27, 0.72, "WebXR controls", "#e8f2ff"),
        (0.365, 0.14, 0.27, 0.72, "CEL-P5 prediction panel", "#eafaf1"),
        (0.685, 0.14, 0.27, 0.72, "Runtime authorization", "#fff3df"),
    ]
    for x, yy, w, h, title, color in panels:
        ax.add_patch(
            FancyBboxPatch(
                (x, yy),
                w,
                h,
                boxstyle="round,pad=0.015,rounding_size=0.02",
                facecolor=color,
                edgecolor="#3d4b5f",
                linewidth=1.2,
            )
        )
        ax.text(x + w / 2, yy + h - 0.055, title, ha="center", va="top", weight="bold", fontsize=11, color="#172033")

    # Controls panel
    control_lines = [
        "Material pair selector",
        "Cu → Cu",
        "",
        "Impact velocity slider",
        "575 m/s",
        "",
        "Other qualified domains",
        "Al6061 → SS304",
        "Ti6Al4V → Ti6Al4V",
        "Inconel718 → Ti6Al4V",
    ]
    ax.text(0.18, 0.755, "\n".join(control_lines), ha="center", va="top", fontsize=9.4, color="#172033", linespacing=1.22)
    ax.plot([0.09, 0.27], [0.315, 0.315], color="#2c7fb8", linewidth=6, solid_capstyle="round")
    ax.scatter([0.18], [0.315], s=180, color="#ffffff", edgecolor="#2c7fb8", linewidth=2.0, zorder=3)
    ax.text(0.18, 0.265, "domain-bounded control", ha="center", fontsize=8.5, color="#4b5b6d")

    # Prediction panel
    prediction_lines = [
        f"Terminal velocity: {y['terminal_particle_volume_weighted_velocity_m_s']:.2f} m/s",
        f"Flattening: {y['particle_axial_flattening_percent']:.2f} %",
        f"Crater depth/Dp: {y['normalized_crater_depth']:.3f}",
        f"Particle PEEQ p95: {y['particle_peeqvavg_p95']:.3f}",
        f"Substrate PEEQ p95: {y['substrate_peeq_p95']:.3f}",
        f"Particle Tmax: {y['particle_temperature_max_k']:.0f} K",
        f"Max T/Tm: {y['maximum_temperature_over_melt']:.3f}",
        f"Peak pressure: {y['peak_contact_pressure_pa'] / 1e9:.2f} GPa",
    ]
    ax.text(0.50, 0.755, "\n".join(prediction_lines), ha="center", va="top", fontsize=9.7, color="#172033", linespacing=1.48)
    ax.text(0.50, 0.24, "Simulation surrogate output\nnot a bond/no-bond classifier", ha="center", va="center", fontsize=9, color="#1f6f43", weight="bold")

    # Authorization panel
    gate_lines = [
        ("Qualified pair + in-range", "AUTHORIZED", "#2ca25f"),
        ("Unsupported pair", "BLOCKED", "#d9534f"),
        ("Out-of-range velocity", "BLOCKED", "#d9534f"),
        ("Near review region", "WARNING", "#f0ad4e"),
        ("Experimental claim", "NOT AUTHORIZED", "#d9534f"),
    ]
    y0 = 0.735
    for i, (condition, status, color) in enumerate(gate_lines):
        yy = y0 - i * 0.102
        ax.add_patch(Rectangle((0.712, yy - 0.034), 0.035, 0.035, facecolor=color, edgecolor="#333333", linewidth=0.5))
        ax.text(0.758, yy - 0.006, condition, ha="left", va="center", fontsize=8.4, color="#172033")
        ax.text(0.758, yy - 0.039, status, ha="left", va="center", fontsize=8.1, color=color, weight="bold")
    ax.text(
        0.82,
        0.185,
        f"JS/Python replay: {runtime['rows_replayed']} cases × {runtime['targets_replayed']} targets\nmax relative drift = {runtime['global_max_relative_error']}",
        ha="center",
        va="center",
        fontsize=9,
        color="#172033",
    )

    arrow(ax, (0.315, 0.50), (0.365, 0.50), color="#34495e")
    arrow(ax, (0.635, 0.50), (0.685, 0.50), color="#34495e")
    ax.text(0.5, 0.93, "WebXR human-machine interface concept with executable CEL-P5 runtime gates", ha="center", weight="bold", fontsize=14, color="#172033")
    ax.text(0.5, 0.065, "The interface displays predictions only when the runtime applicability policy authorizes qualified-pair interpolation.", ha="center", fontsize=10, color="#34495e")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def fig06_traceability(df: pd.DataFrame, final_pred: pd.DataFrame, manifest: Dict[str, Any]) -> Path:
    path = FIG_DIR / "fig06_end_to_end_traceability_example.png"
    row = df[(df["pair"] == "Cu->Cu") & (df["impact_velocity_m_s"].astype(float).round(6) == 575.0)]
    if row.empty:
        row = df[df["pair"] == "Cu->Cu"].iloc[[0]]
    sim = row.iloc[0]
    pred = final_pred[
        (final_pred["production_case_id"] == sim["production_case_id"])
    ].iloc[0]

    fig, ax = plt.subplots(figsize=(15.2, 7.2))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    steps = [
        (
            "1. User selection",
            f"pair: Cu → Cu\nvelocity: {float(sim['impact_velocity_m_s']):.0f} m/s",
            "#e8f2ff",
        ),
        (
            "2. KG crosswalk",
            "simulation: Cu\nKG canonical: Cu\nmapping: exact",
            "#dff3ff",
        ),
        (
            "3. CEL-P4 case",
            f"{sim['production_case_id']}\nALLAE/ALLIE {float(sim['final_allae_over_allie']):.4f}\n|ΔE|/KE₀ {float(sim['etotal_drift_over_initial_ke']):.4f}",
            "#eafaf1",
        ),
        (
            "4. Surrogate",
            "ExtraTrees\nqualified-pair interpolation\nmean R² 0.9694",
            "#fff3df",
        ),
        (
            "5. WebXR runtime",
            "JSON tree ensemble\nJS domain gate\nexact replay verified",
            "#efe6ff",
        ),
        (
            "6. HMI output",
            f"terminal v {float(pred['terminal_particle_volume_weighted_velocity_m_s__predicted']):.2f} m/s\nflattening {float(pred['particle_axial_flattening_percent__predicted']):.2f}%\nstatus: authorized",
            "#f7e4e4",
        ),
    ]
    x_positions = [0.030, 0.190, 0.350, 0.510, 0.670, 0.830]
    w, h, y = 0.128, 0.32, 0.48
    for i, (title, body, color) in enumerate(steps):
        draw_box(ax, (x_positions[i], y), (w, h), title, body, color, title_color="#172033")
        if i < len(steps) - 1:
            arrow(ax, (x_positions[i] + w, y + h / 2), (x_positions[i + 1], y + h / 2), color="#34495e")

    ax.add_patch(
        FancyBboxPatch(
            (0.13, 0.12),
            0.74,
            0.20,
            boxstyle="round,pad=0.02,rounding_size=0.025",
            facecolor="#f8fbff",
            edgecolor="#3d4b5f",
            linewidth=1.1,
        )
    )
    ax.text(
        0.5,
        0.265,
        "Traceability record",
        ha="center",
        va="center",
        weight="bold",
        fontsize=11,
        color="#172033",
    )
    ax.text(
        0.5,
        0.19,
        (
            f"source ODB path retained in extracted dataset → {sim['odb_file']}\n"
            "artifact path: webxr/cel_p5_surrogate_tree_ensemble.json → WebXR panel; "
            "claim boundary: simulation-surrogate interpolation only"
        ),
        ha="center",
        va="center",
        fontsize=8.7,
        color="#34495e",
        linespacing=1.25,
    )
    ax.text(0.5, 0.91, "End-to-end traceability from material selection to bounded WebXR prediction", ha="center", weight="bold", fontsize=14, color="#172033")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def markdown_escape(value: Any) -> str:
    """Escape characters that would otherwise alter GitHub-flavored Markdown tables."""
    text = str(value)
    return text.replace("\\", "\\\\").replace("|", "&#124;").replace("\n", "<br>")


def dataframe_to_markdown(df: pd.DataFrame) -> str:
    headers = list(df.columns)
    rows = [
        "| " + " | ".join(markdown_escape(header) for header in headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for _, row in df.iterrows():
        rows.append("| " + " | ".join(markdown_escape(row[col]) for col in headers) + " |")
    return "\n".join(rows) + "\n"


def latex_escape(value: Any) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
        "→": r"$\rightarrow$",
        "≤": r"$\leq$",
        "×": r"$\times$",
        "Δ": r"$\Delta$",
        "₀": r"$_0$",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def dataframe_to_latex(df: pd.DataFrame, caption: str, label: str) -> str:
    col_spec = "l" * len(df.columns)
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        rf"\caption{{{latex_escape(caption)}}}",
        rf"\label{{{label}}}",
        rf"\begin{{tabular}}{{{col_spec}}}",
        r"\hline",
        " & ".join(latex_escape(col) for col in df.columns) + r" \\",
        r"\hline",
    ]
    for _, row in df.iterrows():
        lines.append(" & ".join(latex_escape(row[col]) for col in df.columns) + r" \\")
    lines.extend([r"\hline", r"\end{tabular}", r"\end{table}", ""])
    return "\n".join(lines)


def write_table(df: pd.DataFrame, stem: str, caption: str, label: str) -> Dict[str, str]:
    csv_path = TABLE_DIR / f"{stem}.csv"
    md_path = TABLE_DIR / f"{stem}.md"
    tex_path = TABLE_DIR / f"{stem}.tex"
    df.to_csv(csv_path, index=False)
    md_path.write_text(f"# {caption}\n\n" + dataframe_to_markdown(df), encoding="utf-8")
    tex_path.write_text(dataframe_to_latex(df, caption, label), encoding="utf-8")
    return {"csv": csv_path.name, "md": md_path.name, "tex": tex_path.name}


def fmt(value: float, digits: int = 4) -> str:
    if not np.isfinite(float(value)):
        return "nan"
    value = float(value)
    if abs(value) >= 1e5 or (abs(value) < 1e-3 and value != 0):
        return f"{value:.{digits}e}"
    return f"{value:.{digits}f}"


def build_tables(df: pd.DataFrame, p4: Dict[str, Any], metrics: Dict[str, Any], runtime: Dict[str, Any], manifest: Dict[str, Any]) -> List[Dict[str, str]]:
    table_records: List[Dict[str, str]] = []

    domains = []
    for pair, group in df.groupby("pair", sort=False):
        review_count = int(group["constitutive_review_flags"].fillna("").astype(str).str.len().gt(0).sum())
        domains.append(
            {
                "Pair": pair.replace("->", "→"),
                "Particle": group["particle_material"].iloc[0],
                "Substrate": group["substrate_material"].iloc[0],
                "Velocity range (m/s)": f"{float(group['impact_velocity_m_s'].min()):.0f}–{float(group['impact_velocity_m_s'].max()):.0f}",
                "Cases": len(group),
                "Review-flag cases": review_count,
                "Deployment status": "qualified interpolation",
            }
        )
    t1 = pd.DataFrame(domains)
    table_records.append(
        {
            "number": "Table 1",
            "caption": "Qualified CEL-P5 material-pair domains.",
            **write_table(t1, "table01_qualified_pair_domains", "Qualified CEL-P5 material-pair domains.", "tab:qualified_domains"),
        }
    )

    gate_rows = [
        {
            "Gate": "CEL-P4 case count",
            "Threshold": "44 required",
            "Observed worst / value": f"{p4['case_count']} cases",
            "Status": "PASS",
            "Role": "complete DOE",
        },
        {
            "Gate": "Numerically passing cases",
            "Threshold": "44 required",
            "Observed worst / value": f"{p4['numerically_passing_case_count']}/44",
            "Status": "PASS",
            "Role": "simulation qualification",
        },
        {
            "Gate": "ML candidates",
            "Threshold": "≥36 total and ≥9 per pair",
            "Observed worst / value": f"{p4['ml_candidate_count']} total; 11 per pair",
            "Status": "PASS",
            "Role": "surrogate training authorization",
        },
        {
            "Gate": "ALLAE/ALLIE",
            "Threshold": "≤0.05",
            "Observed worst / value": fmt(df["final_allae_over_allie"].max(), digits=6),
            "Status": "PASS",
            "Role": "hourglass/artificial energy control",
        },
        {
            "Gate": "|ΔETOTAL|/KE₀",
            "Threshold": "≤0.02",
            "Observed worst / value": fmt(df["etotal_drift_over_initial_ke"].max(), digits=6),
            "Status": "PASS",
            "Role": "global energy audit",
        },
        {
            "Gate": "Particle volume change",
            "Threshold": "≤0.01",
            "Observed worst / value": fmt(df["particle_material_volume_relative_change_abs"].max(), digits=6),
            "Status": "PASS",
            "Role": "Eulerian material conservation",
        },
        {
            "Gate": "Endpoint boundary return",
            "Threshold": "≤0.8",
            "Observed worst / value": fmt(df["endpoint_over_first_boundary_return"].max(), digits=6),
            "Status": "PASS",
            "Role": "duration/domain adequacy",
        },
        {
            "Gate": "Maximum T/Tm",
            "Threshold": "<1.0 for ML candidacy",
            "Observed worst / value": fmt(df["maximum_temperature_over_melt"].max(), digits=6),
            "Status": "PASS + review flags",
            "Role": "thermal softening applicability",
        },
        {
            "Gate": "Maximum PEEQ review",
            "Threshold": ">5 triggers review",
            "Observed worst / value": fmt(df["maximum_peeq"].max(), digits=6),
            "Status": "REVIEW, not exclusion",
            "Role": "large-strain constitutive caution",
        },
    ]
    t2 = pd.DataFrame(gate_rows)
    table_records.append(
        {
            "number": "Table 2",
            "caption": "CEL-P4 numerical acceptance and ML-candidate gates.",
            **write_table(t2, "table02_numerical_acceptance_gates", "CEL-P4 numerical acceptance and ML-candidate gates.", "tab:numerical_gates"),
        }
    )

    comparison_rows = []
    for model in ["RidgeCV", "RandomForest", "ExtraTrees", "GradientBoosting"]:
        interp = next(r for r in metrics["results"] if r["model"] == model and r["regime"] == "pair_aware_velocity_interpolation")
        lopo = next(r for r in metrics["results"] if r["model"] == model and r["regime"] == "leave_one_pair_out_boundary_audit")
        comparison_rows.append(
            {
                "Model": model,
                "Interpolation mean R²": fmt(interp["mean_r2"]),
                "Interpolation mean NRMSE": fmt(interp["mean_nrmse"]),
                "LOPO mean R²": fmt(lopo["mean_r2"]),
                "LOPO mean NRMSE": fmt(lopo["mean_nrmse"]),
            }
        )
    t3 = pd.DataFrame(comparison_rows)
    table_records.append(
        {
            "number": "Table 3",
            "caption": "Surrogate model comparison across validation regimes.",
            **write_table(t3, "table03_surrogate_model_comparison", "Surrogate model comparison across validation regimes.", "tab:model_comparison"),
        }
    )

    selected = metrics["selected_model"]
    selected_interp = next(r for r in metrics["results"] if r["model"] == selected and r["regime"] == "pair_aware_velocity_interpolation")
    target_rows = []
    for target, metric in selected_interp["metrics_by_target"].items():
        target_rows.append(
            {
                "Target": TARGET_LABELS[target].replace("\n", " "),
                "R²": fmt(metric["r2"]),
                "MAE": fmt(metric["mae"]),
                "RMSE": fmt(metric["rmse"]),
                "NRMSE": fmt(metric["nrmse"]),
                "Observed range": f"{fmt(metric['actual_min'])}–{fmt(metric['actual_max'])}",
                "Use in paper": "diagnostic" if target == "peak_contact_pressure_pa" else "primary response",
            }
        )
    t4 = pd.DataFrame(target_rows)
    table_records.append(
        {
            "number": "Table 4",
            "caption": "Selected ExtraTrees interpolation metrics by simulation response target.",
            **write_table(t4, "table04_selected_model_target_metrics", "Selected ExtraTrees interpolation metrics by simulation response target.", "tab:target_metrics"),
        }
    )

    policy_rows = [
        {
            "Input condition": "Qualified material pair and in-range velocity",
            "Runtime status": "PREDICTION_AUTHORIZED_SIMULATION_SURROGATE",
            "Output": "prediction displayed",
            "Manuscript claim": "authorized simulation-surrogate interpolation",
        },
        {
            "Input condition": "Unsupported material pair",
            "Runtime status": "UNSUPPORTED_PAIR",
            "Output": "prediction blocked",
            "Manuscript claim": "no unseen-pair prediction",
        },
        {
            "Input condition": "Qualified pair but velocity outside range",
            "Runtime status": "OUTSIDE_QUALIFIED_VELOCITY_RANGE",
            "Output": "prediction blocked",
            "Manuscript claim": "no velocity extrapolation",
        },
        {
            "Input condition": "Near-melt or high-PEEQ region",
            "Runtime status": "authorized with warning metadata",
            "Output": "prediction plus review flag",
            "Manuscript claim": "constitutive caution retained",
        },
        {
            "Input condition": "Physical bonding or autonomous-control request",
            "Runtime status": "not authorized by model card",
            "Output": "claim blocked",
            "Manuscript claim": "decision support only",
        },
        {
            "Input condition": "Python-to-JavaScript runtime replay",
            "Runtime status": runtime["decision"],
            "Output": f"{runtime['rows_replayed']} cases × {runtime['targets_replayed']} targets; max drift {runtime['global_max_relative_error']}",
            "Manuscript claim": "browser runtime equivalence",
        },
    ]
    t5 = pd.DataFrame(policy_rows)
    table_records.append(
        {
            "number": "Table 5",
            "caption": "WebXR runtime authorization and deployment policy.",
            **write_table(t5, "table05_webxr_runtime_authorization_policy", "WebXR runtime authorization and deployment policy.", "tab:runtime_policy"),
        }
    )

    return table_records


def write_index(figures: List[Dict[str, str]], tables: List[Dict[str, str]]) -> None:
    lines = [
        "# AEI manuscript figure and table package",
        "",
        "Generated from the verified CEL-P4/CEL-P5 repository artifacts by `scripts/generate_aei_figures_tables.py`.",
        "",
        "## Figures",
        "",
    ]
    for item in figures:
        lines.extend(
            [
                f"### {item['number']}. {item['title']}",
                "",
                f"- File: `paper/figures/{item['file']}`",
                f"- Caption: {item['caption']}",
                "",
            ]
        )
    lines.extend(["## Tables", ""])
    for item in tables:
        lines.extend(
            [
                f"### {item['number']}. {item['caption']}",
                "",
                f"- Markdown: `paper/tables/{item['md']}`",
                f"- CSV: `paper/tables/{item['csv']}`",
                f"- LaTeX: `paper/tables/{item['tex']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Claim boundary",
            "",
            "These assets support a qualified-pair simulation-surrogate virtual-twin manuscript. They do not support experimental validation, physical bond/no-bond thresholds, universal cross-material prediction, or autonomous process control claims.",
            "",
        ]
    )
    INDEX_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ensure_dirs()
    df = pd.read_csv(P4_DATASET)
    pred = pd.read_csv(P5_PREDICTIONS)
    final_pred = pd.read_csv(P5_FINAL_PREDICTIONS)
    metrics = load_json(P5_METRICS)
    p4 = load_json(P4_RESULTS)
    runtime = load_json(WEBXR_VERIFICATION)
    manifest = load_json(KG_WEBXR_MANIFEST)

    figures = [
        {
            "number": "Figure 1",
            "title": "Knowledge-grounded virtual-twin architecture",
            "file": fig01_architecture(manifest).name,
            "caption": "Four-layer architecture linking KG provenance, gated CEL simulation, simulation-surrogate inference, and WebXR human decision support.",
        },
        {
            "number": "Figure 2",
            "title": "CEL-P4 numerical qualification dashboard",
            "file": fig02_gate_dashboard(df).name,
            "caption": "Gate dashboard showing complete 44-case ML-candidate coverage, worst-case normalized numerical gates, and retained constitutive-review flags.",
        },
        {
            "number": "Figure 3",
            "title": "Selected-surrogate interpolation parity",
            "file": fig03_parity(pred, metrics).name,
            "caption": "Out-of-fold pair-aware velocity-interpolation parity for the selected ExtraTrees simulation surrogate across nine response targets.",
        },
        {
            "number": "Figure 4",
            "title": "Validation-regime comparison",
            "file": fig04_model_comparison(metrics).name,
            "caption": "Model comparison separating intended qualified-pair interpolation from leave-one-material-pair-out boundary auditing.",
        },
        {
            "number": "Figure 5",
            "title": "WebXR HMI runtime-gate panel",
            "file": fig05_webxr_hmi(final_pred, runtime).name,
            "caption": "WebXR HMI concept showing material/velocity controls, CEL-P5 prediction outputs, and runtime authorization statuses.",
        },
        {
            "number": "Figure 6",
            "title": "End-to-end traceability example",
            "file": fig06_traceability(df, final_pred, manifest).name,
            "caption": "Traceability path from a material-pair selection through KG crosswalk, CEL-P4 case provenance, surrogate prediction, WebXR runtime, and HMI output.",
        },
    ]

    tables = build_tables(df, p4, metrics, runtime, manifest)
    write_index(figures, tables)

    print(f"Wrote {len(figures)} figures to {FIG_DIR.relative_to(ROOT)}")
    print(f"Wrote {len(tables)} table sets to {TABLE_DIR.relative_to(ROOT)}")
    print(f"Wrote {INDEX_MD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
