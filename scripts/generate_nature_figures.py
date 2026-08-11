"""Generate Nature-style manuscript figures for the cold-spray virtual twin.

The AEI figure set in ``paper/figures`` is intentionally explanatory and
informatics-heavy.  This script produces a separate Nature-facing set in
``paper/nature_figures``: compact display items, restrained colour, lower-case
panel labels, vector PDFs for line art, high-resolution PNG previews and TIFF
copies, plus source-data CSV files for plotted quantities.
"""

from __future__ import annotations

import json
import math
import textwrap
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle
from sklearn.metrics import mean_absolute_error, r2_score


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "paper" / "nature_figures"
SOURCE_DIR = OUT_DIR / "source_data"
INDEX_MD = OUT_DIR / "NATURE_FIGURE_INDEX.md"

P4_DATASET = ROOT / "database" / "cel_p4_simulation_surrogate_dataset.csv"
P5_PREDICTIONS = ROOT / "database" / "cel_p5_surrogate_predictions.csv"
P5_FINAL_PREDICTIONS = ROOT / "database" / "cel_p5_final_model_predictions.csv"
P5_METRICS = ROOT / "reports" / "cel_p5_surrogate_metrics.json"
P4_RESULTS = ROOT / "extracted" / "production" / "CEL_P4" / "cel_p4_results.json"
WEBXR_VERIFICATION = ROOT / "reports" / "cel_p5_webxr_runtime_verification.json"
KG_WEBXR_MANIFEST = ROOT / "webxr" / "cel_p5_kg_webxr_manifest.json"
MATERIAL_CROSSWALK = ROOT / "config" / "material_kg_crosswalk.csv"


def mm(value: float) -> float:
    """Convert millimetres to inches for matplotlib figure sizing."""
    return value / 25.4


NATURE_FULL_WIDTH = mm(180)
NATURE_SINGLE_WIDTH = mm(90)

# Okabe-Ito colourblind-safe palette, kept modest for print conversion.
PAIR_COLORS = {
    "Al6061->SS304": "#0072B2",
    "Cu->Cu": "#D55E00",
    "Inconel718->Ti6Al4V": "#CC79A7",
    "Ti6Al4V->Ti6Al4V": "#009E73",
}
GREY = "#555555"
LIGHT_GREY = "#E9E9E9"
DARK = "#111111"
ACCENT = "#0072B2"
WARNING = "#E69F00"
BLOCK = "#D55E00"
PASS = "#009E73"

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
    "terminal_particle_volume_weighted_velocity_m_s": "Terminal velocity (m s$^{-1}$)",
    "particle_axial_flattening_percent": "Particle flattening (%)",
    "normalized_crater_depth": "Crater depth / $D_p$",
    "particle_peeqvavg_p95": "Particle PEEQ, p95",
    "substrate_peeq_p95": "Substrate PEEQ, p95",
    "particle_temperature_max_k": "Particle $T_{max}$ (K)",
    "substrate_temperature_max_k": "Substrate $T_{max}$ (K)",
    "maximum_temperature_over_melt": "Maximum $T/T_m$",
    "peak_contact_pressure_pa": "Peak pressure (Pa)",
}

SHORT_TARGET_LABELS = {
    "terminal_particle_volume_weighted_velocity_m_s": "$v_{term}$",
    "particle_axial_flattening_percent": "Flattening",
    "normalized_crater_depth": "Crater depth",
    "particle_peeqvavg_p95": "Particle PEEQ",
    "substrate_peeq_p95": "Substrate PEEQ",
    "particle_temperature_max_k": "Particle $T_{max}$",
    "substrate_temperature_max_k": "Substrate $T_{max}$",
    "maximum_temperature_over_melt": "$T/T_m$",
    "peak_contact_pressure_pa": "Peak pressure",
}

RESPONSE_TARGETS = [
    "terminal_particle_volume_weighted_velocity_m_s",
    "particle_axial_flattening_percent",
    "normalized_crater_depth",
    "maximum_temperature_over_melt",
]


mpl.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 7.0,
        "axes.labelsize": 7.0,
        "axes.titlesize": 7.5,
        "xtick.labelsize": 6.5,
        "ytick.labelsize": 6.5,
        "legend.fontsize": 6.5,
        "figure.titlesize": 8.0,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.6,
        "xtick.major.width": 0.5,
        "ytick.major.width": 0.5,
        "xtick.major.size": 2.5,
        "ytick.major.size": 2.5,
        "grid.linewidth": 0.35,
        "grid.color": "#BDBDBD",
        "grid.alpha": 0.35,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "savefig.facecolor": "white",
        "figure.facecolor": "white",
    }
)


def ensure_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_multi(fig: plt.Figure, stem: str) -> Dict[str, str]:
    """Save vector and raster copies of a figure."""
    paths = {
        "pdf": OUT_DIR / f"{stem}.pdf",
        "png": OUT_DIR / f"{stem}.png",
        "tiff": OUT_DIR / f"{stem}.tiff",
    }
    fig.savefig(paths["pdf"], bbox_inches="tight")
    fig.savefig(paths["png"], dpi=600, bbox_inches="tight")
    fig.savefig(paths["tiff"], dpi=300, bbox_inches="tight", pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)
    return {key: path.name for key, path in paths.items()}


def panel_label(ax: plt.Axes, label: str, x: float = -0.13, y: float = 1.07) -> None:
    ax.text(
        x,
        y,
        label,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontweight="bold",
        fontsize=8.0,
        color=DARK,
    )


def panel_label_axes(ax: plt.Axes, label: str, x: float, y: float) -> None:
    ax.text(x, y, label, ha="left", va="bottom", fontweight="bold", fontsize=8.0, color=DARK)


def clean_axis(ax: plt.Axes) -> None:
    ax.tick_params(direction="out")
    ax.grid(True, alpha=0.28)


def format_pair(pair: str) -> str:
    return pair.replace("->", "→")


def wrap_text(text: str, width: int = 20) -> str:
    wrapped_lines: List[str] = []
    for line in str(text).splitlines():
        if line.strip():
            wrapped_lines.append("\n".join(textwrap.wrap(line, width=width)))
        else:
            wrapped_lines.append("")
    return "\n".join(wrapped_lines)


def add_box(
    ax: plt.Axes,
    xy: tuple[float, float],
    wh: tuple[float, float],
    title: str,
    body: str,
    edge: str = ACCENT,
    face: str = "white",
) -> None:
    x, y = xy
    w, h = wh
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.012,rounding_size=0.010",
            linewidth=0.75,
            edgecolor=edge,
            facecolor=face,
        )
    )
    ax.add_patch(Rectangle((x, y), 0.007, h, facecolor=edge, edgecolor="none"))
    ax.text(x + 0.018, y + h - 0.028, title, ha="left", va="top", fontweight="bold", color=DARK, fontsize=6.8)
    ax.text(x + 0.018, y + h - 0.070, wrap_text(body, 22), ha="left", va="top", color=GREY, linespacing=1.15, fontsize=6.2)


def add_arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float], color: str = GREY) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=9,
            linewidth=0.75,
            color=color,
            shrinkA=2,
            shrinkB=2,
        )
    )


def selected_metric(metrics: Dict[str, Any], model: str = "ExtraTrees", regime: str = "pair_aware_velocity_interpolation") -> Dict[str, Any]:
    for record in metrics["results"]:
        if record["model"] == model and record["regime"] == regime:
            return record
    raise KeyError((model, regime))


def fig01_architecture(manifest: Dict[str, Any]) -> Dict[str, str]:
    fig, (ax_a, ax_b) = plt.subplots(
        2,
        1,
        figsize=(NATURE_FULL_WIDTH, mm(105)),
        gridspec_kw={"height_ratios": [1.15, 0.8], "hspace": 0.18},
    )
    for ax in (ax_a, ax_b):
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")

    counts = manifest["kg_layer"]["counts"]
    surrogate = manifest["cel_p5_surrogate_layer"]
    runtime = load_json(WEBXR_VERIFICATION)

    panel_label_axes(ax_a, "a", 0.0, 0.96)
    x0 = [0.035, 0.245, 0.455, 0.665, 0.825]
    widths = [0.155, 0.155, 0.155, 0.155, 0.145]
    titles = ["Knowledge graph", "Material crosswalk", "Gated CEL", "Surrogate", "WebXR HMI"]
    bodies = [
        f"{counts['literature_entities_merged']:,} literature entities\n{counts['literature_triples_nli_scored']:,} NLI-scored triples",
        "simulation identifiers\nlinked to KG names",
        f"{manifest['cel_p4_layer']['case_count']} accepted cases\n{manifest['cel_p4_layer']['constitutive_review_case_count']} review-flagged",
        f"{surrogate['selected_model']}\nR² = {surrogate['interpolation_mean_r2']:.4f}\nNRMSE = {surrogate['interpolation_mean_nrmse']:.4f}",
        f"{runtime['rows_replayed']} rows × {runtime['targets_replayed']} targets\nmax drift = {runtime['global_max_abs_error']}",
    ]
    edges = [ACCENT, "#666666", PASS, WARNING, "#6A51A3"]
    box_y = 0.50
    box_h = 0.34
    for x, w, title, body, edge in zip(x0, widths, titles, bodies, edges):
        add_box(ax_a, (x, box_y), (w, box_h), title, body, edge=edge)
    for i in range(4):
        add_arrow(ax_a, (x0[i] + widths[i], box_y + box_h / 2), (x0[i + 1], box_y + box_h / 2))
    ax_a.text(
        0.5,
        0.22,
        "The virtual twin is treated as an auditable decision-support chain, not as an autonomous process controller.",
        ha="center",
        va="center",
        color=GREY,
    )

    panel_label_axes(ax_b, "b", 0.0, 0.94)
    authorized = manifest["claim_boundary"]["authorized"]
    blocked = manifest["claim_boundary"]["not_authorized"]
    ax_b.text(0.06, 0.80, "Authorized outputs", fontweight="bold", color=DARK)
    ax_b.text(0.56, 0.80, "Blocked claims", fontweight="bold", color=DARK)
    for i, item in enumerate(authorized):
        yy = 0.62 - i * 0.19
        ax_b.plot([0.065], [yy], marker="o", color=PASS, markersize=3.8)
        ax_b.text(0.085, yy, wrap_text(item, 48), ha="left", va="center", color=DARK)
    for i, item in enumerate(blocked):
        yy = 0.62 - i * 0.15
        ax_b.plot([0.565], [yy], marker="x", color=BLOCK, markersize=4.2, mew=1.0)
        ax_b.text(0.585, yy, wrap_text(item, 42), ha="left", va="center", color=DARK)
    ax_b.plot([0.5, 0.5], [0.08, 0.83], color=LIGHT_GREY, linewidth=0.8)

    fig.subplots_adjust(left=0.02, right=0.98, top=0.96, bottom=0.05)
    return save_multi(fig, "nature_fig01_virtual_twin_architecture")


def fig02_qualification(df: pd.DataFrame, p4: Dict[str, Any]) -> Dict[str, str]:
    fig = plt.figure(figsize=(NATURE_FULL_WIDTH, mm(132)))
    gs = GridSpec(2, 2, figure=fig, height_ratios=[0.9, 1.0], width_ratios=[1.05, 1.0], hspace=0.36, wspace=0.30)
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, :])

    pairs = list(df.groupby("pair", sort=False).groups.keys())
    pair_to_y = {pair: i for i, pair in enumerate(pairs)}
    for pair in pairs:
        sub = df[df["pair"] == pair].sort_values("impact_velocity_m_s")
        review = sub["constitutive_review_flags"].fillna("").astype(str).str.len() > 0
        ax_a.scatter(
            sub.loc[~review, "impact_velocity_m_s"],
            [pair_to_y[pair]] * (~review).sum(),
            s=18,
            color=PAIR_COLORS[pair],
            edgecolor="white",
            linewidth=0.25,
            zorder=3,
        )
        if review.any():
            ax_a.scatter(
                sub.loc[review, "impact_velocity_m_s"],
                [pair_to_y[pair]] * review.sum(),
                s=30,
                marker="^",
                color=WARNING,
                edgecolor=DARK,
                linewidth=0.35,
                zorder=4,
            )
        ax_a.hlines(pair_to_y[pair], sub["impact_velocity_m_s"].min(), sub["impact_velocity_m_s"].max(), color=LIGHT_GREY, linewidth=1.0, zorder=1)
    ax_a.set_yticks(range(len(pairs)))
    ax_a.set_yticklabels([format_pair(pair) for pair in pairs])
    ax_a.set_xlabel("Impact velocity (m s$^{-1}$)")
    ax_a.set_title("Qualified simulation domain")
    ax_a.set_ylim(-0.6, len(pairs) - 0.4)
    ax_a.invert_yaxis()
    ax_a.grid(axis="x", alpha=0.25)
    panel_label(ax_a, "a", x=-0.22)

    gates = pd.DataFrame(
        [
            ("ALLAE/ALLIE", df["final_allae_over_allie"].max(), 0.05),
            ("|ΔETOTAL|/KE$_0$", df["etotal_drift_over_initial_ke"].max(), 0.02),
            ("Volume change", df["particle_material_volume_relative_change_abs"].max(), 0.01),
            ("Boundary return", df["endpoint_over_first_boundary_return"].max(), 0.8),
            ("Maximum $T/T_m$", df["maximum_temperature_over_melt"].max(), 1.0),
        ],
        columns=["gate", "observed", "threshold"],
    )
    gates["observed_over_threshold"] = gates["observed"] / gates["threshold"]
    y = np.arange(len(gates))
    ax_b.barh(y, gates["observed_over_threshold"], color=PASS, height=0.58)
    ax_b.axvline(1.0, color=BLOCK, linestyle="--", linewidth=0.8)
    for yi, (_, row) in zip(y, gates.iterrows()):
        label = f"{row['observed']:.5f}" if row["gate"] == "Maximum $T/T_m$" else f"{row['observed']:.4g}"
        ax_b.text(row["observed_over_threshold"] + 0.03, yi, label, va="center")
    ax_b.set_yticks(y)
    ax_b.set_yticklabels(gates["gate"])
    ax_b.set_xlim(0, 1.12)
    ax_b.invert_yaxis()
    ax_b.set_xlabel("Observed / threshold")
    ax_b.set_title("Worst-case numerical gate values")
    ax_b.grid(axis="x", alpha=0.25)
    panel_label(ax_b, "b", x=-0.19)

    for pair in pairs:
        sub = df[df["pair"] == pair].sort_values("impact_velocity_m_s")
        review = sub["constitutive_review_flags"].fillna("").astype(str).str.len() > 0
        ax_c.plot(
            sub["impact_velocity_m_s"],
            sub["maximum_temperature_over_melt"],
            color=PAIR_COLORS[pair],
            linewidth=0.9,
            marker="o",
            markersize=3.0,
            label=format_pair(pair),
        )
        if review.any():
            ax_c.scatter(
                sub.loc[review, "impact_velocity_m_s"],
                sub.loc[review, "maximum_temperature_over_melt"],
                marker="^",
                s=34,
                color=WARNING,
                edgecolor=DARK,
                linewidth=0.35,
                zorder=4,
            )
    ax_c.axhline(1.0, color=BLOCK, linestyle="--", linewidth=0.8)
    ax_c.axhline(0.95, color=WARNING, linestyle=":", linewidth=0.8)
    ax_c.set_xlabel("Impact velocity (m s$^{-1}$)")
    ax_c.set_ylabel("Maximum $T/T_m$")
    ax_c.set_title("Constitutive caution retained as metadata")
    ax_c.legend(frameon=False, ncol=4, loc="upper left", bbox_to_anchor=(0.0, -0.28), columnspacing=1.1, handlelength=1.8)
    ax_c.set_ylim(0.30, 1.04)
    clean_axis(ax_c)
    panel_label(ax_c, "c", x=-0.04)

    source = df[
        [
            "production_case_id",
            "pair",
            "impact_velocity_m_s",
            "constitutive_review_flags",
            "final_allae_over_allie",
            "etotal_drift_over_initial_ke",
            "particle_material_volume_relative_change_abs",
            "endpoint_over_first_boundary_return",
            "maximum_temperature_over_melt",
        ]
    ].copy()
    source.to_csv(SOURCE_DIR / "nature_fig02_source_data.csv", index=False)
    gates.to_csv(SOURCE_DIR / "nature_fig02_gate_summary.csv", index=False)

    fig.subplots_adjust(left=0.11, right=0.98, top=0.93, bottom=0.18)
    return save_multi(fig, "nature_fig02_simulation_qualification")


def fig03_response_manifolds(df: pd.DataFrame) -> Dict[str, str]:
    fig, axes = plt.subplots(2, 2, figsize=(NATURE_FULL_WIDTH, mm(130)), sharex=False)
    axes = axes.ravel()
    panels = ["a", "b", "c", "d"]
    for ax, target, label in zip(axes, RESPONSE_TARGETS, panels):
        for pair, sub in df.groupby("pair", sort=False):
            sub = sub.sort_values("impact_velocity_m_s")
            y = sub[target]
            ax.plot(
                sub["impact_velocity_m_s"],
                y,
                marker="o",
                markersize=2.8,
                linewidth=0.9,
                color=PAIR_COLORS[pair],
                label=format_pair(pair),
            )
        ax.set_xlabel("Impact velocity (m s$^{-1}$)")
        ax.set_ylabel(TARGET_LABELS[target])
        clean_axis(ax)
        panel_label(ax, label)
    axes[0].axhline(0, color=GREY, linewidth=0.6, linestyle=":")
    axes[3].axhline(1.0, color=BLOCK, linewidth=0.8, linestyle="--")
    axes[3].axhline(0.95, color=WARNING, linewidth=0.8, linestyle=":")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, loc="lower center", ncol=4, bbox_to_anchor=(0.5, 0.01), columnspacing=1.1)
    df[["production_case_id", "pair", "impact_velocity_m_s", *RESPONSE_TARGETS]].to_csv(
        SOURCE_DIR / "nature_fig03_source_data.csv",
        index=False,
    )
    fig.subplots_adjust(left=0.12, right=0.98, top=0.97, bottom=0.14, hspace=0.38, wspace=0.34)
    return save_multi(fig, "nature_fig03_cel_response_manifolds")


def metric_records(metrics: Dict[str, Any]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for record in metrics["results"]:
        for target, vals in record["metrics_by_target"].items():
            rows.append(
                {
                    "model": record["model"],
                    "regime": record["regime"],
                    "target": target,
                    "r2": vals["r2"],
                    "mae": vals["mae"],
                    "rmse": vals["rmse"],
                    "nrmse": vals["nrmse"],
                    "mean_r2": record["mean_r2"],
                    "mean_nrmse": record["mean_nrmse"],
                }
            )
    return pd.DataFrame(rows)


def parity_panel(ax: plt.Axes, pred: pd.DataFrame, target: str, label: str) -> None:
    for pair, sub in pred.groupby("pair", sort=False):
        ax.scatter(
            sub[f"{target}__actual"],
            sub[f"{target}__predicted"],
            s=10,
            color=PAIR_COLORS[pair],
            edgecolor="white",
            linewidth=0.2,
            alpha=0.95,
        )
    actual = pred[f"{target}__actual"].astype(float)
    predicted = pred[f"{target}__predicted"].astype(float)
    lo = min(actual.min(), predicted.min())
    hi = max(actual.max(), predicted.max())
    pad = 0.06 * (hi - lo if hi > lo else 1.0)
    ax.plot([lo - pad, hi + pad], [lo - pad, hi + pad], color=GREY, linewidth=0.7)
    ax.set_xlim(lo - pad, hi + pad)
    ax.set_ylim(lo - pad, hi + pad)
    ax.set_xlabel("CEL")
    ax.set_ylabel("Surrogate")
    ax.set_title(TARGET_LABELS[target])
    ax.text(
        0.03,
        0.95,
        f"R² = {r2_score(actual, predicted):.3f}\nMAE = {mean_absolute_error(actual, predicted):.3g}",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=6.4,
        color=DARK,
    )
    clean_axis(ax)
    panel_label(ax, label)


def fig04_surrogate_validation(pred: pd.DataFrame, metrics: Dict[str, Any]) -> Dict[str, str]:
    pred_et = pred[
        (pred["model"] == "ExtraTrees") & (pred["regime"] == "pair_aware_velocity_interpolation")
    ].copy()
    selected = selected_metric(metrics)
    metric_df = metric_records(metrics)

    fig = plt.figure(figsize=(NATURE_FULL_WIDTH, mm(150)))
    gs = GridSpec(2, 3, figure=fig, width_ratios=[0.95, 1.0, 1.0], hspace=0.42, wspace=0.36)
    ax_a = fig.add_subplot(gs[:, 0])
    parity_axes = [
        fig.add_subplot(gs[0, 1]),
        fig.add_subplot(gs[0, 2]),
        fig.add_subplot(gs[1, 1]),
        fig.add_subplot(gs[1, 2]),
    ]

    target_order = TARGETS
    r2_vals = [selected["metrics_by_target"][target]["r2"] for target in target_order]
    y = np.arange(len(target_order))
    colors = [ACCENT if target != "peak_contact_pressure_pa" else GREY for target in target_order]
    ax_a.barh(y, r2_vals, color=colors, height=0.62)
    ax_a.axvline(selected["mean_r2"], color=WARNING, linestyle="--", linewidth=0.8)
    ax_a.set_yticks(y)
    ax_a.set_yticklabels([SHORT_TARGET_LABELS[target] for target in target_order])
    ax_a.set_xlim(0.72, 1.01)
    ax_a.invert_yaxis()
    ax_a.set_xlabel("Interpolation R²")
    ax_a.set_title(f"ExtraTrees mean R² = {selected['mean_r2']:.4f}")
    for yi, value in zip(y, r2_vals):
        ax_a.text(value + 0.004, yi, f"{value:.3f}", va="center", fontsize=6.2)
    clean_axis(ax_a)
    panel_label(ax_a, "a", x=-0.24)

    for ax, target, label in zip(parity_axes, RESPONSE_TARGETS, ["b", "c", "d", "e"]):
        parity_panel(ax, pred_et, target, label)

    handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=PAIR_COLORS[pair], markeredgecolor="white", markersize=4, label=format_pair(pair))
        for pair in pred_et.groupby("pair", sort=False).groups.keys()
    ]
    fig.legend(handles=handles, frameon=False, ncol=4, loc="lower center", bbox_to_anchor=(0.5, 0.01), columnspacing=1.1)

    pred_et.to_csv(SOURCE_DIR / "nature_fig04_parity_source_data.csv", index=False)
    metric_df.to_csv(SOURCE_DIR / "nature_fig04_metric_source_data.csv", index=False)
    fig.subplots_adjust(left=0.12, right=0.98, top=0.96, bottom=0.13)
    return save_multi(fig, "nature_fig04_surrogate_validation")


def fig05_deployment_gating(metrics: Dict[str, Any], runtime: Dict[str, Any], df: pd.DataFrame) -> Dict[str, str]:
    fig = plt.figure(figsize=(NATURE_FULL_WIDTH, mm(118)))
    gs = GridSpec(2, 2, figure=fig, height_ratios=[1.0, 0.85], width_ratios=[1.15, 0.85], hspace=0.45, wspace=0.32)
    ax_a = fig.add_subplot(gs[:, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 1])

    records = metrics["results"]
    models = []
    interp: Dict[str, float] = {}
    lopo: Dict[str, float] = {}
    nrmse_lopo: Dict[str, float] = {}
    for record in records:
        model = record["model"]
        if model not in models:
            models.append(model)
        if record["regime"] == "pair_aware_velocity_interpolation":
            interp[model] = record["mean_r2"]
        elif record["regime"] == "leave_one_pair_out_boundary_audit":
            lopo[model] = record["mean_r2"]
            nrmse_lopo[model] = record["mean_nrmse"]

    y = np.arange(len(models))
    ax_a.set_xlim(-0.16, 1.04)
    for yi, model in zip(y, models):
        lo = max(lopo[model], -0.14)
        ax_a.plot([lo, interp[model]], [yi, yi], color=LIGHT_GREY, linewidth=1.1, zorder=1)
        ax_a.scatter(interp[model], yi, color=ACCENT, s=20, zorder=3)
        ax_a.scatter(lo, yi, color=BLOCK, s=20, zorder=3)
        ax_a.text(interp[model] + 0.018, yi, f"{interp[model]:.2f}", va="center")
        if lopo[model] < -0.14:
            ax_a.annotate(
                f"{lopo[model]:.1f}",
                xy=(-0.14, yi),
                xytext=(-0.03, yi - 0.18),
                arrowprops={"arrowstyle": "-|>", "lw": 0.7, "color": BLOCK},
                color=BLOCK,
                fontsize=6.5,
            )
        else:
            ax_a.text(lo - 0.018 if lo < 0 else lo + 0.018, yi, f"{lopo[model]:.2f}", va="center", ha="right" if lo < 0 else "left")
    ax_a.axvspan(-0.05, 0.05, color="#F3F3F3", zorder=0)
    ax_a.axvline(0, color=GREY, linewidth=0.65)
    ax_a.set_yticks(y)
    ax_a.set_yticklabels(models)
    ax_a.invert_yaxis()
    ax_a.set_xlabel("Mean R² across nine targets")
    ax_a.set_title("Interpolation and unseen-pair audit")
    clean_axis(ax_a)
    panel_label(ax_a, "a", x=-0.18)
    ax_a.legend(
        handles=[
            Line2D([0], [0], marker="o", color="none", markerfacecolor=ACCENT, markersize=4, label="Qualified-pair interpolation"),
            Line2D([0], [0], marker="o", color="none", markerfacecolor=BLOCK, markersize=4, label="Leave-one-pair-out audit"),
        ],
        frameon=False,
        loc="upper right",
    )

    policies = [
        ("Qualified pair\nin range", "Display"),
        ("Unsupported pair", "Block"),
        ("Out of range", "Block"),
        ("Physical bond\nor control", "Block"),
    ]
    ax_b.axis("off")
    ax_b.set_xlim(0, 1)
    ax_b.set_ylim(0, 1)
    panel_label_axes(ax_b, "b", 0.0, 0.96)
    for i, (condition, decision) in enumerate(policies):
        y0 = 0.79 - i * 0.20
        status_color = PASS if decision == "Display" else BLOCK
        ax_b.text(0.06, y0, condition, ha="left", va="center", color=DARK)
        ax_b.plot([0.58], [y0], marker="o", color=status_color, markersize=4)
        ax_b.text(0.63, y0, decision, ha="left", va="center", color=status_color, fontweight="bold")
    ax_b.text(0.06, 0.93, "Runtime policy", fontweight="bold")

    ax_c.axis("off")
    ax_c.set_xlim(0, 1)
    ax_c.set_ylim(0, 1)
    panel_label_axes(ax_c, "c", 0.0, 0.96)
    ax_c.text(0.06, 0.82, "JavaScript/Python replay", fontweight="bold")
    replay_lines = [
        f"{runtime['rows_replayed']} cases",
        f"{runtime['targets_replayed']} targets",
        f"{runtime['compared_values']} values",
        f"maximum drift = {runtime['global_max_abs_error']}",
    ]
    for i, line in enumerate(replay_lines):
        yy = 0.62 - i * 0.15
        ax_c.plot([0.08], [yy], marker="o", color=PASS, markersize=3.2)
        ax_c.text(0.13, yy, line, va="center")

    pd.DataFrame(
        [
            {"model": model, "interpolation_mean_r2": interp[model], "lopo_mean_r2": lopo[model], "lopo_mean_nrmse": nrmse_lopo[model]}
            for model in models
        ]
    ).to_csv(SOURCE_DIR / "nature_fig05_validation_regimes.csv", index=False)
    pd.DataFrame(policies, columns=["input_condition", "runtime_decision"]).to_csv(
        SOURCE_DIR / "nature_fig05_runtime_policy.csv",
        index=False,
    )

    fig.subplots_adjust(left=0.11, right=0.98, top=0.94, bottom=0.11)
    return save_multi(fig, "nature_fig05_deployment_gating")


def fig06_webxr_traceability(df: pd.DataFrame, final_pred: pd.DataFrame, manifest: Dict[str, Any]) -> Dict[str, str]:
    sample = final_pred[
        (final_pred["pair"] == "Cu->Cu") & (final_pred["impact_velocity_m_s"].astype(float).round(6) == 575.0)
    ]
    if sample.empty:
        sample = final_pred[final_pred["pair"] == "Cu->Cu"].iloc[[0]]
    row = sample.iloc[0]
    case_id = row["production_case_id"]
    source = df[df["production_case_id"] == case_id].iloc[0]
    crosswalk = pd.read_csv(MATERIAL_CROSSWALK)
    cu_map = crosswalk[crosswalk["simulation_material_id"] == "Cu"].iloc[0]

    fig, (ax_a, ax_b) = plt.subplots(
        1,
        2,
        figsize=(NATURE_FULL_WIDTH, mm(112)),
        gridspec_kw={"width_ratios": [1.14, 0.86], "wspace": 0.24},
    )
    for ax in (ax_a, ax_b):
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")

    panel_label_axes(ax_a, "a", 0.0, 0.96)
    nodes = [
        ("Input", "Cu→Cu, 575 m s$^{-1}$", ACCENT),
        ("KG crosswalk", f"{cu_map['simulation_material_id']} mapped to {cu_map['kg_canonical_name']}", "#666666"),
        ("CEL provenance", f"{case_id}\nALLAE/ALLIE = {source['final_allae_over_allie']:.4f}", PASS),
        ("Surrogate", "ExtraTrees, in-domain", WARNING),
        ("HMI output", "Prediction + authorization", "#6A51A3"),
    ]
    chain_x = 0.05
    chain_w = 0.38
    chain_h = 0.115
    for i, (title, body, edge) in enumerate(nodes):
        yy = 0.82 - i * 0.145
        add_box(ax_a, (chain_x, yy), (chain_w, chain_h), title, body, edge=edge)
        if i < len(nodes) - 1:
            add_arrow(ax_a, (chain_x + chain_w / 2, yy), (chain_x + chain_w / 2, yy - 0.035))

    trace = [
        ("Case status", source["case_gate_decision"]),
        ("Review flag", "none" if pd.isna(source["constitutive_review_flags"]) else str(source["constitutive_review_flags"])),
        ("Velocity domain", f"{source['qualified_velocity_min_m_s']:.0f}–{source['qualified_velocity_max_m_s']:.0f} m s$^{{-1}}$"),
        ("Temperature gate", f"max $T/T_m$ = {source['maximum_temperature_over_melt']:.4f}"),
    ]
    ax_a.text(0.53, 0.82, "Traceability record", fontweight="bold")
    for i, (key, value) in enumerate(trace):
        yy = 0.70 - i * 0.13
        ax_a.text(0.53, yy, key, color=GREY, ha="left", va="center")
        ax_a.text(0.53, yy - 0.055, value, color=DARK, ha="left", va="center", fontsize=6.6)
        ax_a.plot([0.53, 0.94], [yy - 0.088, yy - 0.088], color=LIGHT_GREY, linewidth=0.45)

    panel_label_axes(ax_b, "b", 0.0, 0.96)
    ax_b.add_patch(Rectangle((0.08, 0.07), 0.84, 0.82, facecolor="white", edgecolor="#A0A0A0", linewidth=0.8))
    ax_b.text(0.12, 0.82, "WebXR panel", fontweight="bold")
    ax_b.text(0.12, 0.74, "Material pair", color=GREY)
    ax_b.text(0.12, 0.68, "Cu→Cu", color=DARK)
    ax_b.text(0.12, 0.59, "Impact velocity", color=GREY)
    ax_b.plot([0.12, 0.78], [0.54, 0.54], color=LIGHT_GREY, linewidth=2.2)
    ax_b.plot([0.47], [0.54], marker="o", color=ACCENT, markersize=5)
    ax_b.text(0.80, 0.54, "575", va="center", color=DARK)
    output_lines = [
        ("$v_{term}$", f"{row['terminal_particle_volume_weighted_velocity_m_s__predicted']:.2f} m s$^{{-1}}$"),
        ("Flattening", f"{row['particle_axial_flattening_percent__predicted']:.2f}%"),
        ("Crater / $D_p$", f"{row['normalized_crater_depth__predicted']:.3f}"),
        ("Max $T/T_m$", f"{row['maximum_temperature_over_melt__predicted']:.3f}"),
    ]
    ax_b.text(0.12, 0.43, "Simulation-surrogate outputs", fontweight="bold")
    for i, (key, value) in enumerate(output_lines):
        yy = 0.35 - i * 0.075
        ax_b.text(0.13, yy, key, color=GREY, ha="left", va="center")
        ax_b.text(0.57, yy, value, color=DARK, ha="left", va="center")
    ax_b.plot([0.13], [0.095], marker="o", color=PASS, markersize=4)
    ax_b.text(0.18, 0.095, "authorized simulation surrogate", va="center", color=PASS, fontweight="bold", fontsize=6.8)

    pd.DataFrame(
        [
            {
                "sample_case": case_id,
                "pair": row["pair"],
                "impact_velocity_m_s": row["impact_velocity_m_s"],
                "terminal_velocity_predicted_m_s": row["terminal_particle_volume_weighted_velocity_m_s__predicted"],
                "flattening_predicted_percent": row["particle_axial_flattening_percent__predicted"],
                "crater_depth_over_dp_predicted": row["normalized_crater_depth__predicted"],
                "maximum_temperature_over_melt_predicted": row["maximum_temperature_over_melt__predicted"],
                "material_mapping": cu_map["mapping_type"],
                "kg_canonical_name": cu_map["kg_canonical_name"],
            }
        ]
    ).to_csv(SOURCE_DIR / "nature_fig06_traceability_source_data.csv", index=False)

    fig.subplots_adjust(left=0.03, right=0.98, top=0.95, bottom=0.08)
    return save_multi(fig, "nature_fig06_webxr_traceability")


def write_index(figures: Sequence[Dict[str, str]]) -> None:
    lines = [
        "# Nature-style figure package",
        "",
        "Generated by `scripts/generate_nature_figures.py` from the verified CEL-P4/CEL-P5 repository artifacts.",
        "",
        "## Style target",
        "",
        "- Double-column figures are sized near 180 mm width.",
        "- Vector PDFs are the primary line-art files; PNG previews are 600 dpi and TIFF copies are 300 dpi.",
        "- Panels use lower-case labels and reduced in-panel prose; detailed interpretation belongs in figure legends.",
        "- Source-data CSV files are written under `paper/nature_figures/source_data/`.",
        "",
        "## Figures",
        "",
    ]
    for fig in figures:
        lines.extend(
            [
                f"### {fig['number']}. {fig['title']}",
                "",
                f"- PDF: `paper/nature_figures/{fig['pdf']}`",
                f"- PNG: `paper/nature_figures/{fig['png']}`",
                f"- TIFF: `paper/nature_figures/{fig['tiff']}`",
                f"- Legend draft: {fig['legend']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Claim boundary",
            "",
            "These figures support a qualified simulation-surrogate virtual twin. They do not establish experimental physical validation, bond/no-bond thresholds, unseen-pair prediction, or autonomous process control.",
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

    figures: List[Dict[str, str]] = []
    specs = [
        (
            "Figure 1",
            "Knowledge-grounded virtual-twin architecture",
            fig01_architecture(manifest),
            "Architecture connecting KG provenance, material crosswalk, qualified CEL simulation, surrogate inference and WebXR decision support, with authorized and blocked claims stated explicitly.",
        ),
        (
            "Figure 2",
            "Numerical qualification of the CEL simulation campaign",
            fig02_qualification(df, p4),
            "Qualified material-pair and velocity domain, worst-case numerical gates, and retained constitutive-review metadata for the 44-case CEL-P4 dataset.",
        ),
        (
            "Figure 3",
            "CEL response manifolds over qualified metal-on-metal domains",
            fig03_response_manifolds(df),
            "Simulation response trends for terminal velocity, particle flattening, normalized crater depth and maximum homologous temperature across the four qualified material-pair domains.",
        ),
        (
            "Figure 4",
            "Simulation-surrogate interpolation accuracy",
            fig04_surrogate_validation(pred, metrics),
            "ExtraTrees interpolation metrics and parity plots for representative primary response quantities within qualified material-pair domains.",
        ),
        (
            "Figure 5",
            "Deployment-domain gating and browser runtime equivalence",
            fig05_deployment_gating(metrics, runtime, df),
            "Separation between pair-aware interpolation and leave-one-pair-out boundary auditing, plus runtime policies that display only authorized qualified-pair in-range predictions.",
        ),
        (
            "Figure 6",
            "WebXR traceability from material selection to displayed prediction",
            fig06_webxr_traceability(df, final_pred, manifest),
            "Example traceability path and WebXR panel for a Cu→Cu 575 m s⁻¹ query, linking KG material mapping, CEL case provenance, surrogate output and authorization status.",
        ),
    ]
    for number, title, files, legend in specs:
        figures.append({"number": number, "title": title, "legend": legend, **files})

    write_index(figures)
    print(f"Wrote {len(figures)} Nature-style figures to {OUT_DIR.relative_to(ROOT)}")
    print(f"Wrote source data to {SOURCE_DIR.relative_to(ROOT)}")
    print(f"Wrote {INDEX_MD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
