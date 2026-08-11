"""Train the CEL-P5 simulation-surrogate models from the qualified CEL-P4 DOE.

This script is intentionally conservative:

* It refuses to train unless the frozen CEL-P4 gate has authorized P5 training.
* It reports two validation regimes:
  1. pair-aware velocity interpolation inside qualified material-pair ranges;
  2. leave-one-pair-out boundary audit for unseen-pair extrapolation.
* It saves a Python model artifact and a JSON tree-ensemble artifact that can be
  consumed by a zero-dependency WebXR client.

The resulting model is a simulation surrogate, not an externally validated
physical bonding model.
"""

from __future__ import annotations

import json
import math
import sys
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import RidgeCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.multioutput import MultiOutputRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


ROOT = Path(__file__).resolve().parents[1]
P4_RESULTS = ROOT / "extracted" / "production" / "CEL_P4" / "cel_p4_results.json"
P4_DATASET = ROOT / "database" / "cel_p4_simulation_surrogate_dataset.csv"
MATERIAL_REGISTRY = ROOT / "config" / "material_registry.csv"

MODEL_DIR = ROOT / "models"
REPORT_DIR = ROOT / "reports"
FIGURE_DIR = REPORT_DIR / "figures"
DATABASE_DIR = ROOT / "database"
WEBXR_DIR = ROOT / "webxr"

METRICS_JSON = REPORT_DIR / "cel_p5_surrogate_metrics.json"
TRAINING_REPORT = REPORT_DIR / "cel_p5_surrogate_training_report.md"
PREDICTIONS_CSV = DATABASE_DIR / "cel_p5_surrogate_predictions.csv"
FINAL_MODEL_PREDICTIONS_CSV = DATABASE_DIR / "cel_p5_final_model_predictions.csv"
MODEL_JOBLIB = MODEL_DIR / "cel_p5_extra_trees_surrogate.joblib"
MODEL_CARD_JSON = MODEL_DIR / "cel_p5_surrogate_model_card.json"
WEBXR_JSON = WEBXR_DIR / "cel_p5_surrogate_tree_ensemble.json"
WEBXR_RUNTIME = WEBXR_DIR / "cel_p5_tree_runtime.mjs"

INTERPOLATION_PARITY = FIGURE_DIR / "cel_p5_interpolation_parity.png"
LOPO_PARITY = FIGURE_DIR / "cel_p5_lopo_boundary_parity.png"
MODEL_COMPARISON = FIGURE_DIR / "cel_p5_model_comparison.png"
VELOCITY_RESPONSE = FIGURE_DIR / "cel_p5_velocity_response_curves.png"

PASS_DECISION = "PASS_CEL_P5_SIMULATION_SURROGATE_TRAINING_AUTHORIZED"


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
    "terminal_particle_volume_weighted_velocity_m_s": "Terminal velocity (m/s)",
    "particle_axial_flattening_percent": "Particle flattening (%)",
    "normalized_crater_depth": "Normalized crater depth",
    "particle_peeqvavg_p95": "Particle PEEQ p95",
    "substrate_peeq_p95": "Substrate PEEQ p95",
    "particle_temperature_max_k": "Particle Tmax (K)",
    "substrate_temperature_max_k": "Substrate Tmax (K)",
    "maximum_temperature_over_melt": "Max T/Tm",
    "peak_contact_pressure_pa": "Peak contact pressure (Pa)",
}

REPORT_TARGETS = [
    "terminal_particle_volume_weighted_velocity_m_s",
    "particle_axial_flattening_percent",
    "normalized_crater_depth",
    "particle_peeqvavg_p95",
    "substrate_peeq_p95",
    "particle_temperature_max_k",
    "maximum_temperature_over_melt",
    "peak_contact_pressure_pa",
]

MATERIAL_COLUMNS = [
    "density_kg_m3",
    "elastic_modulus_pa",
    "poissons_ratio",
    "specific_heat_j_kg_k",
    "conductivity_w_m_k",
    "melt_temp_k",
    "jc_a_pa",
    "jc_b_pa",
    "jc_n",
    "jc_c",
    "jc_m",
    "ref_temp_k",
]

BASE_FEATURES = [
    "pair",
    "particle_material",
    "substrate_material",
    "impact_velocity_m_s",
    "velocity_fraction",
    "qualified_velocity_min_m_s",
    "qualified_velocity_max_m_s",
    "Ek_norm",
    "H_ratio",
    "T_hom_p",
    "T_hom_s",
    "density_ratio",
    "modulus_ratio",
    "melt_ratio",
    "conductivity_ratio",
]

ROLE_MATERIAL_FEATURES = [
    f"{role}_{column}"
    for role in ("particle", "substrate")
    for column in [
        "density_kg_m3",
        "elastic_modulus_pa",
        "specific_heat_j_kg_k",
        "conductivity_w_m_k",
        "melt_temp_k",
        "jc_a_pa",
        "jc_b_pa",
        "jc_n",
        "jc_c",
        "jc_m",
    ]
]

FEATURES = BASE_FEATURES + ROLE_MATERIAL_FEATURES
CATEGORICAL_FEATURES = ["pair", "particle_material", "substrate_material"]
NUMERIC_FEATURES = [feature for feature in FEATURES if feature not in CATEGORICAL_FEATURES]


@dataclass
class EvaluationResult:
    name: str
    regime: str
    predictions: np.ndarray
    metrics_by_target: Dict[str, Dict[str, float]]
    mean_r2: float
    mean_nrmse: float


def ensure_directories() -> None:
    for directory in (MODEL_DIR, REPORT_DIR, FIGURE_DIR, DATABASE_DIR, WEBXR_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def load_p4_gate() -> Mapping[str, Any]:
    if not P4_RESULTS.exists():
        raise FileNotFoundError(f"Missing CEL-P4 aggregate results: {P4_RESULTS}")
    with P4_RESULTS.open("r", encoding="utf-8") as stream:
        summary = json.load(stream)
    decision = summary.get("decision")
    if decision != PASS_DECISION:
        raise RuntimeError(
            f"CEL-P4 decision is {decision!r}, not {PASS_DECISION!r}. "
            "Refusing to train a surrogate before the production DOE gate passes."
        )
    return summary


def to_bool(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    return series.astype(str).str.lower().isin(["true", "1", "yes", "y"])


def load_and_enrich_dataset() -> pd.DataFrame:
    df = pd.read_csv(P4_DATASET)
    materials = pd.read_csv(MATERIAL_REGISTRY).set_index("material_id")

    required_materials = set(df["particle_material"]).union(set(df["substrate_material"]))
    missing_materials = sorted(required_materials.difference(materials.index))
    if missing_materials:
        raise KeyError(f"Material registry is missing: {missing_materials}")

    df["ml_candidate"] = to_bool(df["ml_candidate"])
    df = df[df["ml_candidate"]].copy()
    if df.empty:
        raise RuntimeError("No ML-candidate CEL-P4 rows are available.")

    for role, source_column in (("particle", "particle_material"), ("substrate", "substrate_material")):
        for material_column in MATERIAL_COLUMNS:
            df[f"{role}_{material_column}"] = df[source_column].map(materials[material_column]).astype(float)

    velocity = df["impact_velocity_m_s"].astype(float)
    df["velocity_fraction"] = (
        (velocity - df["qualified_velocity_min_m_s"].astype(float))
        / (df["qualified_velocity_max_m_s"].astype(float) - df["qualified_velocity_min_m_s"].astype(float))
    )

    # Dimensionless physics features used in the manuscript/twin.
    df["Ek_norm"] = 0.5 * df["particle_density_kg_m3"] * velocity.pow(2) / df["particle_jc_a_pa"]
    df["H_ratio"] = df["particle_jc_a_pa"] / df["substrate_jc_a_pa"]
    df["T_hom_p"] = df["particle_ref_temp_k"] / df["particle_melt_temp_k"]
    df["T_hom_s"] = df["substrate_ref_temp_k"] / df["substrate_melt_temp_k"]
    df["density_ratio"] = df["particle_density_kg_m3"] / df["substrate_density_kg_m3"]
    df["modulus_ratio"] = df["particle_elastic_modulus_pa"] / df["substrate_elastic_modulus_pa"]
    df["melt_ratio"] = df["particle_melt_temp_k"] / df["substrate_melt_temp_k"]
    df["conductivity_ratio"] = df["particle_conductivity_w_m_k"] / df["substrate_conductivity_w_m_k"]

    for target in TARGETS:
        df[target] = pd.to_numeric(df[target], errors="raise")

    return df


def make_one_hot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:  # scikit-learn < 1.2
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def make_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("cat", make_one_hot_encoder(), CATEGORICAL_FEATURES),
            ("num", StandardScaler(), NUMERIC_FEATURES),
        ],
        remainder="drop",
    )


def make_models(random_state: int = 11) -> Dict[str, Pipeline]:
    target_scaler = StandardScaler()
    return {
        "RidgeCV": Pipeline(
            steps=[
                ("pre", make_preprocessor()),
                (
                    "model",
                    TransformedTargetRegressor(
                        regressor=RidgeCV(alphas=np.logspace(-4, 4, 21)),
                        transformer=deepcopy(target_scaler),
                    ),
                ),
            ]
        ),
        "RandomForest": Pipeline(
            steps=[
                ("pre", make_preprocessor()),
                (
                    "model",
                    TransformedTargetRegressor(
                        regressor=RandomForestRegressor(
                            n_estimators=600,
                            random_state=random_state,
                            min_samples_leaf=1,
                            bootstrap=True,
                            n_jobs=-1,
                        ),
                        transformer=deepcopy(target_scaler),
                    ),
                ),
            ]
        ),
        "ExtraTrees": Pipeline(
            steps=[
                ("pre", make_preprocessor()),
                (
                    "model",
                    TransformedTargetRegressor(
                        regressor=ExtraTreesRegressor(
                            n_estimators=800,
                            random_state=random_state,
                            min_samples_leaf=1,
                            bootstrap=False,
                            n_jobs=-1,
                        ),
                        transformer=deepcopy(target_scaler),
                    ),
                ),
            ]
        ),
        "GradientBoosting": Pipeline(
            steps=[
                ("pre", make_preprocessor()),
                (
                    "model",
                    TransformedTargetRegressor(
                        regressor=MultiOutputRegressor(
                            GradientBoostingRegressor(
                                random_state=random_state,
                                n_estimators=250,
                                max_depth=2,
                                learning_rate=0.03,
                                subsample=1.0,
                            )
                        ),
                        transformer=deepcopy(target_scaler),
                    ),
                ),
            ]
        ),
    }


def velocity_level_splits(df: pd.DataFrame, fold_count: int = 5) -> List[Tuple[np.ndarray, np.ndarray, str]]:
    """Pair-aware interpolation: hold out velocity levels, retaining all pairs in train."""
    splits = []
    indices = np.arange(len(df))
    level_index = df["velocity_level_index"].astype(int).to_numpy()
    for fold in range(fold_count):
        test = np.flatnonzero((level_index % fold_count) == fold)
        train = np.setdiff1d(indices, test)
        splits.append((train, test, f"velocity_mod_{fold}"))
    return splits


def leave_one_pair_out_splits(df: pd.DataFrame) -> List[Tuple[np.ndarray, np.ndarray, str]]:
    splits = []
    indices = np.arange(len(df))
    pairs = df["pair"].astype(str).to_numpy()
    for pair in sorted(df["pair"].unique()):
        test = np.flatnonzero(pairs == pair)
        train = np.setdiff1d(indices, test)
        splits.append((train, test, f"heldout_{pair}"))
    return splits


def safe_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    try:
        score = r2_score(y_true, y_pred)
    except ValueError:
        return float("nan")
    return float(score)


def compute_metrics(y_true: pd.DataFrame, y_pred: np.ndarray) -> Tuple[Dict[str, Dict[str, float]], float, float]:
    metrics: Dict[str, Dict[str, float]] = {}
    r2_values: List[float] = []
    nrmse_values: List[float] = []
    for column_index, target in enumerate(TARGETS):
        actual = y_true[target].to_numpy(dtype=float)
        predicted = y_pred[:, column_index].astype(float)
        rmse = math.sqrt(mean_squared_error(actual, predicted))
        mae = mean_absolute_error(actual, predicted)
        value_range = float(np.nanmax(actual) - np.nanmin(actual))
        nrmse = float(rmse / value_range) if value_range > 0 else float("nan")
        r2 = safe_r2(actual, predicted)
        metrics[target] = {
            "r2": r2,
            "mae": float(mae),
            "rmse": float(rmse),
            "nrmse": nrmse,
            "actual_min": float(np.nanmin(actual)),
            "actual_max": float(np.nanmax(actual)),
        }
        if np.isfinite(r2):
            r2_values.append(r2)
        if np.isfinite(nrmse):
            nrmse_values.append(nrmse)
    return metrics, float(np.mean(r2_values)), float(np.mean(nrmse_values))


def evaluate(
    name: str,
    model: Pipeline,
    regime: str,
    splits: Sequence[Tuple[np.ndarray, np.ndarray, str]],
    x: pd.DataFrame,
    y: pd.DataFrame,
) -> Tuple[EvaluationResult, pd.DataFrame]:
    predictions = np.full(y.shape, np.nan, dtype=float)
    fold_names = np.empty(len(y), dtype=object)

    for train_index, test_index, fold_name in splits:
        fitted = clone(model)
        fitted.fit(x.iloc[train_index], y.iloc[train_index])
        predictions[test_index, :] = fitted.predict(x.iloc[test_index])
        fold_names[test_index] = fold_name

    if np.isnan(predictions).any():
        raise RuntimeError(f"Evaluation produced NaN predictions for {name}/{regime}.")

    metrics, mean_r2, mean_nrmse = compute_metrics(y, predictions)
    result = EvaluationResult(
        name=name,
        regime=regime,
        predictions=predictions,
        metrics_by_target=metrics,
        mean_r2=mean_r2,
        mean_nrmse=mean_nrmse,
    )

    rows: List[Dict[str, Any]] = []
    for row_index in range(len(y)):
        for target_index, target in enumerate(TARGETS):
            actual = float(y.iloc[row_index, target_index])
            predicted = float(predictions[row_index, target_index])
            rows.append(
                {
                    "model": name,
                    "regime": regime,
                    "fold": fold_names[row_index],
                    "production_case_id": x.index[row_index],
                    "target": target,
                    "target_label": TARGET_LABELS[target],
                    "actual": actual,
                    "predicted": predicted,
                    "residual": predicted - actual,
                    "absolute_error": abs(predicted - actual),
                }
            )
    return result, pd.DataFrame(rows)


def prediction_wide_frame(
    df: pd.DataFrame,
    result: EvaluationResult,
    regime: str,
    model_name: str,
) -> pd.DataFrame:
    columns = [
        "production_case_id",
        "pair",
        "particle_material",
        "substrate_material",
        "impact_velocity_m_s",
        "velocity_level_index",
        "constitutive_review_flags",
        "case_gate_decision",
        "solve_reuse",
    ]
    out = df[columns].copy()
    out.insert(0, "model", model_name)
    out.insert(1, "regime", regime)
    for target_index, target in enumerate(TARGETS):
        out[f"{target}__actual"] = df[target].astype(float).to_numpy()
        out[f"{target}__predicted"] = result.predictions[:, target_index]
        out[f"{target}__residual"] = result.predictions[:, target_index] - df[target].astype(float).to_numpy()
    return out


def plot_parity(
    df: pd.DataFrame,
    result: EvaluationResult,
    title: str,
    path: Path,
    targets: Sequence[str] = TARGETS,
) -> None:
    pair_colors = {
        pair: color
        for pair, color in zip(
            sorted(df["pair"].unique()),
            ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf"],
        )
    }
    ncols = 3
    nrows = int(math.ceil(len(targets) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(13.5, 4.0 * nrows), dpi=220)
    axes_flat = np.ravel(axes)
    for axis_index, target in enumerate(targets):
        ax = axes_flat[axis_index]
        target_index = TARGETS.index(target)
        actual = df[target].astype(float).to_numpy()
        predicted = result.predictions[:, target_index]
        for pair, group in df.groupby("pair", sort=True):
            idx = group.index.to_numpy()
            ax.scatter(
                actual[idx],
                predicted[idx],
                s=28,
                color=pair_colors[pair],
                edgecolor="white",
                linewidth=0.5,
                alpha=0.9,
                label=pair if axis_index == 0 else None,
            )
        lower = min(float(np.nanmin(actual)), float(np.nanmin(predicted)))
        upper = max(float(np.nanmax(actual)), float(np.nanmax(predicted)))
        pad = 0.04 * (upper - lower) if upper > lower else 1.0
        ax.plot([lower - pad, upper + pad], [lower - pad, upper + pad], color="#444444", linewidth=1.0)
        metric = result.metrics_by_target[target]
        ax.set_title(f"{TARGET_LABELS[target]}\n$R^2$={metric['r2']:.3f}, MAE={metric['mae']:.3g}")
        ax.set_xlabel("Simulation")
        ax.set_ylabel("Surrogate")
        ax.grid(True, alpha=0.25)
    for axis_index in range(len(targets), len(axes_flat)):
        axes_flat[axis_index].axis("off")
    handles, labels = axes_flat[0].get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc="upper center", ncol=4, frameon=False, bbox_to_anchor=(0.5, 1.0))
    fig.suptitle(title, y=1.03, fontsize=14)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def plot_model_comparison(results: Sequence[EvaluationResult], path: Path) -> None:
    interp = [result for result in results if result.regime == "pair_aware_velocity_interpolation"]
    lopo = [result for result in results if result.regime == "leave_one_pair_out_boundary_audit"]
    names = [result.name for result in interp]
    interp_scores = [result.mean_r2 for result in interp]
    lopo_map = {result.name: result.mean_r2 for result in lopo}
    lopo_scores = [lopo_map.get(name, np.nan) for name in names]

    x = np.arange(len(names))
    width = 0.36
    fig, ax = plt.subplots(figsize=(9.0, 4.8), dpi=220)
    ax.bar(x - width / 2, interp_scores, width, label="Pair-aware velocity interpolation", color="#2477b3")
    ax.bar(x + width / 2, lopo_scores, width, label="Leave-one-pair-out boundary audit", color="#c75b12")
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=20, ha="right")
    ax.set_ylabel("Mean $R^2$ across targets")
    ax.set_title("Surrogate validation regimes separate interpolation from cross-pair extrapolation")
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def dense_pair_rows(df: pd.DataFrame, points_per_pair: int = 121) -> pd.DataFrame:
    rows: List[pd.Series] = []
    for pair, group in df.sort_values(["pair", "velocity_level_index"]).groupby("pair", sort=True):
        base = group.iloc[0].copy()
        base["pair"] = pair
        v_min = float(base["qualified_velocity_min_m_s"])
        v_max = float(base["qualified_velocity_max_m_s"])
        for velocity in np.linspace(v_min, v_max, points_per_pair):
            row = base.copy()
            row["impact_velocity_m_s"] = velocity
            row["velocity_fraction"] = (velocity - v_min) / (v_max - v_min)
            row["Ek_norm"] = 0.5 * row["particle_density_kg_m3"] * velocity**2 / row["particle_jc_a_pa"]
            rows.append(row)
    return pd.DataFrame(rows).reset_index(drop=True)


def plot_velocity_response(df: pd.DataFrame, final_model: Pipeline, path: Path) -> None:
    dense = dense_pair_rows(df)
    dense_predictions = final_model.predict(dense[FEATURES])
    for target_index, target in enumerate(TARGETS):
        dense[f"{target}__predicted"] = dense_predictions[:, target_index]

    chosen_targets = [
        "terminal_particle_volume_weighted_velocity_m_s",
        "particle_axial_flattening_percent",
        "particle_temperature_max_k",
        "peak_contact_pressure_pa",
    ]
    pair_colors = {
        pair: color
        for pair, color in zip(
            sorted(df["pair"].unique()),
            ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf"],
        )
    }

    fig, axes = plt.subplots(2, 2, figsize=(13.0, 8.5), dpi=220)
    for ax, target in zip(np.ravel(axes), chosen_targets):
        for pair, group in dense.groupby("pair", sort=True):
            ax.plot(
                group["impact_velocity_m_s"],
                group[f"{target}__predicted"],
                color=pair_colors[pair],
                linewidth=2.0,
                label=pair,
            )
            observed = df[df["pair"] == pair]
            ax.scatter(
                observed["impact_velocity_m_s"],
                observed[target],
                color=pair_colors[pair],
                edgecolor="white",
                linewidth=0.5,
                s=26,
                alpha=0.9,
            )
        ax.set_title(TARGET_LABELS[target])
        ax.set_xlabel("Impact velocity (m/s)")
        ax.grid(True, alpha=0.25)
    axes[0, 0].set_ylabel("Response")
    axes[1, 0].set_ylabel("Response")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=4, frameon=False, bbox_to_anchor=(0.5, 1.02))
    fig.suptitle("Qualified-pair surrogate response curves with CEL-P4 simulation anchors", y=1.06, fontsize=14)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def jsonable(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [jsonable(item) for item in value]
    return value


def export_extra_trees_for_webxr(
    final_model: Pipeline,
    df: pd.DataFrame,
    metrics: Mapping[str, Any],
    path: Path,
) -> None:
    preprocessor: ColumnTransformer = final_model.named_steps["pre"]
    target_regressor: TransformedTargetRegressor = final_model.named_steps["model"]
    regressor = target_regressor.regressor_
    if not isinstance(regressor, ExtraTreesRegressor):
        raise TypeError("The WebXR tree export expects a fitted ExtraTreesRegressor.")

    cat_encoder: OneHotEncoder = preprocessor.named_transformers_["cat"]
    numeric_scaler: StandardScaler = preprocessor.named_transformers_["num"]
    try:
        transformed_feature_names = preprocessor.get_feature_names_out().tolist()
    except AttributeError:
        transformed_feature_names = []
        for feature, categories in zip(CATEGORICAL_FEATURES, cat_encoder.categories_):
            transformed_feature_names.extend([f"cat__{feature}_{category}" for category in categories])
        transformed_feature_names.extend([f"num__{feature}" for feature in NUMERIC_FEATURES])

    trees = []
    for estimator in regressor.estimators_:
        tree = estimator.tree_
        raw_values = tree.value.squeeze(axis=2) if tree.value.ndim == 3 and tree.value.shape[2] == 1 else tree.value.squeeze()
        if raw_values.ndim == 1:
            raw_values = raw_values[:, np.newaxis]
        trees.append(
            {
                "children_left": tree.children_left.astype(int).tolist(),
                "children_right": tree.children_right.astype(int).tolist(),
                "feature": tree.feature.astype(int).tolist(),
                "threshold": tree.threshold.astype(float).tolist(),
                "value_scaled": raw_values.astype(float).tolist(),
            }
        )

    material_properties = {}
    for material_column in sorted(set(df["particle_material"]).union(set(df["substrate_material"]))):
        row = df[df["particle_material"].eq(material_column) | df["substrate_material"].eq(material_column)].iloc[0]
        prefix = "particle" if row["particle_material"] == material_column else "substrate"
        material_properties[material_column] = {
            column: float(row[f"{prefix}_{column}"])
            for column in MATERIAL_COLUMNS
        }

    pair_domains = {}
    for pair, group in df.groupby("pair", sort=True):
        flagged = group[group["constitutive_review_flags"].fillna("").astype(str).str.len() > 0]
        pair_domains[pair] = {
            "particle_material": str(group["particle_material"].iloc[0]),
            "substrate_material": str(group["substrate_material"].iloc[0]),
            "velocity_min_m_s": float(group["qualified_velocity_min_m_s"].iloc[0]),
            "velocity_max_m_s": float(group["qualified_velocity_max_m_s"].iloc[0]),
            "training_velocity_levels_m_s": [float(v) for v in group["impact_velocity_m_s"].tolist()],
            "constitutive_review_case_count": int(
                group["constitutive_review_flags"].fillna("").astype(str).str.len().gt(0).sum()
            ),
            "constitutive_review_cases": [
                {
                    "case": str(row["production_case_id"]),
                    "velocity_m_s": float(row["impact_velocity_m_s"]),
                    "flags": str(row["constitutive_review_flags"]),
                    "maximum_temperature_over_melt": float(row["maximum_temperature_over_melt"]),
                    "maximum_peeq": float(row["maximum_peeq"]),
                }
                for _, row in flagged.iterrows()
            ],
        }

    payload = {
        "schema_version": "1.0.0",
        "artifact": "CEL-P5 zero-dependency WebXR ExtraTrees simulation-surrogate",
        "created_by": "scripts/train_cel_p5_surrogate.py",
        "training_source": str(P4_DATASET.relative_to(ROOT)),
        "simulation_gate_source": str(P4_RESULTS.relative_to(ROOT)),
        "scope": {
            "authorized_use": "interpolation within listed qualified material pairs and velocity ranges",
            "not_authorized_for": [
                "external physical bonding claims",
                "unseen material-pair prediction",
                "unqualified velocity extrapolation",
                "autonomous process control without human review",
            ],
            "candidate_case_count": int(len(df)),
            "pair_domains": pair_domains,
        },
        "materials": material_properties,
        "features": {
            "raw_feature_order": FEATURES,
            "categorical_features": CATEGORICAL_FEATURES,
            "categorical_categories": {
                feature: [str(value) for value in categories]
                for feature, categories in zip(CATEGORICAL_FEATURES, cat_encoder.categories_)
            },
            "numeric_features": NUMERIC_FEATURES,
            "numeric_mean": numeric_scaler.mean_.astype(float).tolist(),
            "numeric_scale": numeric_scaler.scale_.astype(float).tolist(),
            "transformed_feature_order": transformed_feature_names,
            "engineered_feature_equations": {
                "Ek_norm": "0.5 * particle_density_kg_m3 * impact_velocity_m_s^2 / particle_jc_a_pa",
                "H_ratio": "particle_jc_a_pa / substrate_jc_a_pa",
                "T_hom_p": "particle_ref_temp_k / particle_melt_temp_k",
                "T_hom_s": "substrate_ref_temp_k / substrate_melt_temp_k",
            },
            "training_min": {feature: float(df[feature].min()) for feature in NUMERIC_FEATURES},
            "training_max": {feature: float(df[feature].max()) for feature in NUMERIC_FEATURES},
        },
        "targets": {
            "target_order": TARGETS,
            "labels": TARGET_LABELS,
            "target_mean": target_regressor.transformer_.mean_.astype(float).tolist(),
            "target_scale": target_regressor.transformer_.scale_.astype(float).tolist(),
            "inverse_transform": "prediction = prediction_scaled * target_scale + target_mean",
        },
        "validation_summary": metrics,
        "ensemble": {
            "type": "ExtraTreesRegressor",
            "n_estimators": int(len(regressor.estimators_)),
            "aggregation": "mean",
            "trees": trees,
        },
    }

    with path.open("w", encoding="utf-8") as stream:
        json.dump(jsonable(payload), stream, indent=2)


def markdown_table(rows: Sequence[Sequence[Any]], headers: Sequence[str]) -> str:
    out = ["| " + " | ".join(headers) + " |"]
    out.append("|" + "|".join(["---" for _ in headers]) + "|")
    for row in rows:
        out.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(out)


def fmt(value: float, digits: int = 4) -> str:
    if not np.isfinite(value):
        return "nan"
    if abs(value) >= 1e5 or (abs(value) < 1e-3 and value != 0):
        return f"{value:.{digits}e}"
    return f"{value:.{digits}f}"


def write_report(
    p4_summary: Mapping[str, Any],
    df: pd.DataFrame,
    results: Sequence[EvaluationResult],
    best_result: EvaluationResult,
) -> None:
    result_lookup = {(result.name, result.regime): result for result in results}
    interpolation = [result for result in results if result.regime == "pair_aware_velocity_interpolation"]
    lopo = [result for result in results if result.regime == "leave_one_pair_out_boundary_audit"]

    model_rows = []
    for result in interpolation:
        lopo_result = result_lookup.get((result.name, "leave_one_pair_out_boundary_audit"))
        model_rows.append(
            [
                result.name,
                fmt(result.mean_r2),
                fmt(result.mean_nrmse),
                fmt(lopo_result.mean_r2 if lopo_result else float("nan")),
                fmt(lopo_result.mean_nrmse if lopo_result else float("nan")),
            ]
        )

    target_rows = []
    for target in TARGETS:
        metric = best_result.metrics_by_target[target]
        target_rows.append(
            [
                TARGET_LABELS[target],
                fmt(metric["r2"]),
                fmt(metric["mae"]),
                fmt(metric["rmse"]),
                fmt(metric["nrmse"]),
                f"{fmt(metric['actual_min'])}--{fmt(metric['actual_max'])}",
            ]
        )

    pair_rows = []
    for pair, group in df.groupby("pair", sort=True):
        pair_rows.append(
            [
                pair,
                len(group),
                fmt(float(group["impact_velocity_m_s"].min()), 1),
                fmt(float(group["impact_velocity_m_s"].max()), 1),
                int(group["constitutive_review_flags"].fillna("").astype(str).str.len().gt(0).sum()),
            ]
        )

    review_rows = []
    flagged = df[df["constitutive_review_flags"].fillna("").astype(str).str.len() > 0]
    for _, row in flagged.iterrows():
        review_rows.append(
            [
                row["production_case_id"],
                row["pair"],
                fmt(float(row["impact_velocity_m_s"]), 1),
                row["constitutive_review_flags"],
                fmt(float(row["maximum_temperature_over_melt"])),
                fmt(float(row["maximum_peeq"])),
            ]
        )

    lines = [
        "# CEL-P5 simulation-surrogate training report",
        "",
        f"**Decision:** CEL-P5 simulation surrogate trained from the authorized CEL-P4 DOE.",
        "",
        "## Source gate",
        "",
        f"- CEL-P4 decision: `{p4_summary.get('decision')}`.",
        f"- ML candidates used: {len(df)}.",
        f"- Numerically passing CEL-P4 cases: {p4_summary.get('numerically_passing_case_count')}/{p4_summary.get('case_count')}.",
        f"- Constitutive review cases retained with flags: {int(df['constitutive_review_flags'].fillna('').astype(str).str.len().gt(0).sum())}.",
        f"- Source dataset: `{P4_DATASET.relative_to(ROOT)}`.",
        "",
        "## Qualified pair domains",
        "",
        markdown_table(
            pair_rows,
            ["Pair", "Cases", "v min (m/s)", "v max (m/s)", "Review-flag cases"],
        ),
        "",
        "## Feature formulation",
        "",
        "The final surrogate uses categorical material-pair labels, material registry properties, and dimensionless physics features:",
        "",
        "- `Ek_norm = 0.5 rho_p v^2 / A_p`.",
        "- `H_ratio = A_p / A_s`.",
        "- `T_hom_p = T_ref,p / T_m,p`.",
        "- `T_hom_s = T_ref,s / T_m,s`.",
        "",
        "Here `A_p` and `A_s` are the Johnson--Cook quasi-static yield parameters for the particle and substrate materials.",
        "",
        "## Validation design",
        "",
        "Two validation regimes are reported to keep the claims honest:",
        "",
        "1. **Pair-aware velocity interpolation:** five folds formed from `velocity_level_index mod 5`. Each test fold contains held-out velocity levels for all four qualified pairs, while the training folds retain examples from every pair.",
        "2. **Leave-one-pair-out boundary audit:** each material pair is fully withheld once. This is a stress test for cross-material extrapolation, not the intended deployment regime.",
        "",
        "## Model comparison",
        "",
        markdown_table(
            model_rows,
            [
                "Model",
                "Interpolation mean R2",
                "Interpolation mean NRMSE",
                "LOPO mean R2",
                "LOPO mean NRMSE",
            ],
        ),
        "",
        f"Selected WebXR-exportable model: **{best_result.name}**, with interpolation mean R2 = {best_result.mean_r2:.4f}.",
        "",
        "## Selected-model interpolation metrics by target",
        "",
        markdown_table(
            target_rows,
            ["Target", "R2", "MAE", "RMSE", "NRMSE", "Observed range"],
        ),
        "",
        "## Constitutive review flags retained in the surrogate domain",
        "",
    ]
    if review_rows:
        lines.extend(
            [
                markdown_table(
                    review_rows,
                    ["Case", "Pair", "v (m/s)", "Flags", "Max T/Tm", "Max PEEQ"],
                ),
                "",
            ]
        )
    else:
        lines.extend(["No constitutive review flags were present.", ""])

    lines.extend(
        [
            "## Artifacts",
            "",
            f"- Python model: `{MODEL_JOBLIB.relative_to(ROOT)}`.",
            f"- WebXR tree ensemble JSON: `{WEBXR_JSON.relative_to(ROOT)}`.",
            f"- WebXR runtime module: `{WEBXR_RUNTIME.relative_to(ROOT)}`.",
            f"- Out-of-fold predictions: `{PREDICTIONS_CSV.relative_to(ROOT)}`.",
            f"- Final fitted-model predictions: `{FINAL_MODEL_PREDICTIONS_CSV.relative_to(ROOT)}`.",
            f"- Metrics JSON: `{METRICS_JSON.relative_to(ROOT)}`.",
            f"- Interpolation parity figure: `{INTERPOLATION_PARITY.relative_to(ROOT)}`.",
            f"- Boundary-audit parity figure: `{LOPO_PARITY.relative_to(ROOT)}`.",
            f"- Model-comparison figure: `{MODEL_COMPARISON.relative_to(ROOT)}`.",
            f"- Velocity-response figure: `{VELOCITY_RESPONSE.relative_to(ROOT)}`.",
            "",
            "## Publication claim boundary",
            "",
            "This P5 artifact supports a **qualified-pair simulation-surrogate virtual twin** claim: rapid interpolation of Abaqus/Explicit CEL response quantities inside the four solved metal-on-metal material-pair domains. It does **not** support universal cross-material prediction, physical bonding threshold claims, or experimental validation claims without additional evidence.",
            "",
        ]
    )

    TRAINING_REPORT.write_text("\n".join(lines), encoding="utf-8")


def write_model_card(
    p4_summary: Mapping[str, Any],
    df: pd.DataFrame,
    best_result: EvaluationResult,
    final_model_name: str,
) -> None:
    pair_domains = {}
    for pair, group in df.groupby("pair", sort=True):
        pair_domains[pair] = {
            "particle_material": str(group["particle_material"].iloc[0]),
            "substrate_material": str(group["substrate_material"].iloc[0]),
            "velocity_min_m_s": float(group["qualified_velocity_min_m_s"].iloc[0]),
            "velocity_max_m_s": float(group["qualified_velocity_max_m_s"].iloc[0]),
            "case_count": int(len(group)),
        }

    model_card = {
        "schema_version": "1.0.0",
        "stage": "CEL_P5_SIMULATION_SURROGATE",
        "model_name": final_model_name,
        "source_gate_decision": p4_summary.get("decision"),
        "training_rows": int(len(df)),
        "features": FEATURES,
        "targets": TARGETS,
        "pair_domains": pair_domains,
        "primary_validation_regime": best_result.regime,
        "primary_validation_mean_r2": best_result.mean_r2,
        "primary_validation_mean_nrmse": best_result.mean_nrmse,
        "target_metrics": best_result.metrics_by_target,
        "authorized_use": "simulation-surrogate interpolation inside listed material-pair and velocity domains",
        "limitations": [
            "not externally experimentally validated",
            "not validated for unseen material pairs",
            "not a bonding/no-bonding classifier",
            "review-flag cases remain subject to Johnson--Cook high-temperature/large-strain caution",
        ],
    }
    MODEL_CARD_JSON.write_text(json.dumps(jsonable(model_card), indent=2), encoding="utf-8")


def main() -> int:
    ensure_directories()
    p4_summary = load_p4_gate()
    df = load_and_enrich_dataset().reset_index(drop=True)
    df.index = df["production_case_id"].astype(str)

    x = df[FEATURES]
    y = df[TARGETS]

    interpolation_splits = velocity_level_splits(df)
    lopo_splits = leave_one_pair_out_splits(df)
    models = make_models()

    results: List[EvaluationResult] = []
    prediction_frames: List[pd.DataFrame] = []
    for model_name, model in models.items():
        interpolation_result, _ = evaluate(
            model_name,
            model,
            "pair_aware_velocity_interpolation",
            interpolation_splits,
            x,
            y,
        )
        lopo_result, _ = evaluate(
            model_name,
            model,
            "leave_one_pair_out_boundary_audit",
            lopo_splits,
            x,
            y,
        )
        results.extend([interpolation_result, lopo_result])
        prediction_frames.append(prediction_wide_frame(df, interpolation_result, interpolation_result.regime, model_name))
        prediction_frames.append(prediction_wide_frame(df, lopo_result, lopo_result.regime, model_name))

    interpolation_results = [result for result in results if result.regime == "pair_aware_velocity_interpolation"]
    best_result = max(interpolation_results, key=lambda result: result.mean_r2)
    final_model_name = best_result.name
    final_model = clone(models[final_model_name])
    final_model.fit(x, y)

    if final_model_name != "ExtraTrees":
        print(
            f"WARNING: best interpolation model was {final_model_name}, but WebXR export currently "
            "expects ExtraTrees. Refitting ExtraTrees for the deployable artifact.",
            file=sys.stderr,
        )
        final_model_name = "ExtraTrees"
        final_model = clone(models[final_model_name])
        final_model.fit(x, y)
        best_result = next(
            result
            for result in interpolation_results
            if result.name == final_model_name
        )

    final_predictions = final_model.predict(x)
    final_prediction_rows = df[
        [
            "production_case_id",
            "pair",
            "particle_material",
            "substrate_material",
            "impact_velocity_m_s",
            "velocity_level_index",
            "constitutive_review_flags",
            "case_gate_decision",
            "solve_reuse",
        ]
    ].copy()
    for target_index, target in enumerate(TARGETS):
        final_prediction_rows[f"{target}__actual"] = y[target].astype(float).to_numpy()
        final_prediction_rows[f"{target}__predicted"] = final_predictions[:, target_index]
        final_prediction_rows[f"{target}__residual"] = final_predictions[:, target_index] - y[target].astype(float).to_numpy()
    final_prediction_rows.to_csv(FINAL_MODEL_PREDICTIONS_CSV, index=False)

    predictions = pd.concat(prediction_frames, ignore_index=True)
    predictions.to_csv(PREDICTIONS_CSV, index=False)

    joblib.dump(final_model, MODEL_JOBLIB)

    metrics_payload = {
        "schema_version": "1.0.0",
        "source_dataset": str(P4_DATASET.relative_to(ROOT)),
        "source_gate_decision": p4_summary.get("decision"),
        "selected_model": final_model_name,
        "results": [
            {
                "model": result.name,
                "regime": result.regime,
                "mean_r2": result.mean_r2,
                "mean_nrmse": result.mean_nrmse,
                "metrics_by_target": result.metrics_by_target,
            }
            for result in results
        ],
    }
    METRICS_JSON.write_text(json.dumps(jsonable(metrics_payload), indent=2), encoding="utf-8")

    write_model_card(p4_summary, df, best_result, final_model_name)
    export_extra_trees_for_webxr(final_model, df, metrics_payload, WEBXR_JSON)

    plot_parity(
        df.reset_index(drop=True),
        best_result,
        "CEL-P5 selected surrogate: pair-aware velocity interpolation",
        INTERPOLATION_PARITY,
        targets=TARGETS,
    )
    lopo_best = next(
        result
        for result in results
        if result.name == final_model_name and result.regime == "leave_one_pair_out_boundary_audit"
    )
    plot_parity(
        df.reset_index(drop=True),
        lopo_best,
        "CEL-P5 boundary audit: leave-one-material-pair-out",
        LOPO_PARITY,
        targets=TARGETS,
    )
    plot_model_comparison(results, MODEL_COMPARISON)
    plot_velocity_response(df.reset_index(drop=True), final_model, VELOCITY_RESPONSE)

    write_report(p4_summary, df.reset_index(drop=True), results, best_result)

    print(f"Selected model: {final_model_name}")
    print(f"Interpolation mean R2: {best_result.mean_r2:.4f}")
    print(f"Interpolation mean NRMSE: {best_result.mean_nrmse:.4f}")
    print(f"Model: {MODEL_JOBLIB.relative_to(ROOT)}")
    print(f"WebXR JSON: {WEBXR_JSON.relative_to(ROOT)}")
    print(f"Report: {TRAINING_REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
