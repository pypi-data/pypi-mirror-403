"""migrate files to database

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-21 18:30:00

This migration:
1. Creates artifacts from preprocessing/ folder (scaler_x, pcas, column_transformer, all_features)
2. Creates artifacts from TARGET_X/ folder (models, features, thresholds, scaler_y)
3. Creates data from data/ folder (train, val, test + scaled)
4. Creates data from TARGET_X/ folder (scores_tracking, predictions, feature CSVs)
5. Populates best_model, best_model_score, feature_selection, feature_selection_rank
"""

from typing import Sequence, Union
from alembic import op
import os
import io
import json
import logging
import math


def _nan_to_none(value):
    """Convert NaN and inf values to None for MySQL compatibility."""
    if value is None:
        return None
    try:
        if math.isnan(value) or math.isinf(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def _sanitize_json(obj):
    """Recursively sanitize NaN values from nested structures for MySQL JSON columns."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return {k: _sanitize_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_json(v) for v in obj]
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
    return obj


logger = logging.getLogger("alembic.runtime.migration")

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6g7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# =============================================================================
# CatBoostWrapper for backward compatibility
# =============================================================================

class CatBoostWrapper:
    """Stub class for deserializing old pickled models that used CatBoostWrapper."""
    def __init__(self, model=None):
        self.model = model
        self._model = model

def _inject_catboost_wrapper():
    """Inject CatBoostWrapper into the expected module paths for unpickling."""
    import sys
    from types import ModuleType

    # Inject into lecrapaud.model
    if "lecrapaud.model" not in sys.modules:
        module = ModuleType("lecrapaud.model")
        sys.modules["lecrapaud.model"] = module
    else:
        module = sys.modules["lecrapaud.model"]
    module.CatBoostWrapper = CatBoostWrapper

    # Also inject into lecrapaud.models.best_model (some old pickles reference it there)
    if "lecrapaud.models.best_model" not in sys.modules:
        best_model_module = ModuleType("lecrapaud.models.best_model")
        sys.modules["lecrapaud.models.best_model"] = best_model_module
    else:
        best_model_module = sys.modules["lecrapaud.models.best_model"]
    best_model_module.CatBoostWrapper = CatBoostWrapper

def _unwrap_catboost(model):
    """Unwrap CatBoostWrapper if present."""
    if isinstance(model, CatBoostWrapper):
        return model.model if hasattr(model, 'model') else model._model
    return model


# =============================================================================
# Serialization functions
# =============================================================================

def _serialize_joblib(obj) -> bytes:
    """Serialize an object using joblib."""
    import joblib
    buffer = io.BytesIO()
    joblib.dump(obj, buffer)
    return buffer.getvalue()

def _serialize_dataframe(df) -> bytes:
    """Serialize a DataFrame to parquet bytes."""
    df_copy = df.copy()
    for col in df_copy.columns:
        if df_copy[col].dtype == "object":
            df_copy[col] = df_copy[col].astype(str)
    buffer = io.BytesIO()
    df_copy.to_parquet(buffer, compression="snappy", index=True)
    return buffer.getvalue()

def _serialize_keras(model) -> bytes:
    """Serialize a Keras model to bytes."""
    buffer = io.BytesIO()
    model.save(buffer)
    return buffer.getvalue()


# =============================================================================
# Database helper functions
# =============================================================================

def _save_artifact(session, ExperimentArtifact, experiment_id, artifact_type, artifact_name,
                   data, serialization_format, target_id=None, best_model_score_id=None):
    """Save an artifact to the database."""
    existing = session.query(ExperimentArtifact).filter(
        ExperimentArtifact.experiment_id == experiment_id,
        ExperimentArtifact.artifact_type == artifact_type,
        ExperimentArtifact.artifact_name == artifact_name,
        ExperimentArtifact.target_id == target_id,
    ).first()

    if existing:
        existing.data = data
        existing.serialization_format = serialization_format
        if best_model_score_id:
            existing.best_model_score_id = best_model_score_id
    else:
        artifact = ExperimentArtifact(
            experiment_id=experiment_id,
            target_id=target_id,
            best_model_score_id=best_model_score_id,
            artifact_type=artifact_type,
            artifact_name=artifact_name,
            data=data,
            serialization_format=serialization_format,
        )
        session.add(artifact)

def _save_dataframe_record(session, ExperimentData, experiment_id, data_type, data,
                           row_count, column_count, target_id=None, best_model_score_id=None):
    """Save a DataFrame record to the database."""
    if data_type == "prediction" and best_model_score_id:
        existing = session.query(ExperimentData).filter(
            ExperimentData.best_model_score_id == best_model_score_id,
            ExperimentData.data_type == "prediction",
        ).first()
    else:
        existing = session.query(ExperimentData).filter(
            ExperimentData.experiment_id == experiment_id,
            ExperimentData.data_type == data_type,
            ExperimentData.target_id == target_id,
        ).first()

    if existing:
        existing.data = data
        existing.row_count = row_count
        existing.column_count = column_count
    else:
        record = ExperimentData(
            experiment_id=experiment_id,
            target_id=target_id,
            best_model_score_id=best_model_score_id,
            data_type=data_type,
            data=data,
            row_count=row_count,
            column_count=column_count,
        )
        session.add(record)


def _get_or_create_model(session, ModelType, model_name: str, model_cache: dict = None):
    """Get or create a ModelType record.

    Args:
        model_cache: Optional dict to cache models and avoid repeated queries
    """
    # Check cache first
    if model_cache is not None and model_name in model_cache:
        return model_cache[model_name]

    model_type_map = {
        "xgb": "xgboost", "lgb": "lightgbm", "catboost": "catboost",
        "rf": "random_forest", "svm": "svm", "lr": "logistic_regression",
        "mlp": "mlp", "keras": "keras", "lstm": "keras", "gru": "keras",
        "tcn": "keras", "sgd": "sgd", "linear": "linear",
    }
    base_name = model_name.split(".")[0]
    model_type = model_type_map.get(base_name, base_name)

    existing = session.query(ModelType).filter(ModelType.name == model_name).first()
    if existing:
        if model_cache is not None:
            model_cache[model_name] = existing
        return existing

    model = ModelType(name=model_name, type=model_type)
    session.add(model)
    session.flush()
    if model_cache is not None:
        model_cache[model_name] = model
    return model


def _get_or_create_feature(session, Feature, feature_name: str, feature_type: str = None, feature_cache: dict = None):
    """Get or create a Feature record.

    Args:
        feature_type: "categorical" or "numerical" (optional)
        feature_cache: Optional dict to cache features
    """
    # Check cache first
    if feature_cache is not None and feature_name in feature_cache:
        feature = feature_cache[feature_name]
        # Update type if not set and we have a type to set
        if feature_type and not feature.type:
            feature.type = feature_type
        return feature

    existing = session.query(Feature).filter(Feature.name == feature_name).first()
    if existing:
        # Update type if not set and we have a type to set
        if feature_type and not existing.type:
            existing.type = feature_type
            # Don't flush here - let it batch
        if feature_cache is not None:
            feature_cache[feature_name] = existing
        return existing

    feature = Feature(name=feature_name, type=feature_type)
    session.add(feature)
    session.flush()  # Need ID for FKs
    if feature_cache is not None:
        feature_cache[feature_name] = feature
    return feature


# =============================================================================
# Metadata population functions
# =============================================================================

def _populate_best_model_scores(session, best_model, target_dir, target_type, ModelType, Model, pd, model_cache=None):
    """Create Model for each model folder in target_dir.

    Args:
        target_type: "regression" or "classification" - determines which metrics to populate
        model_cache: Optional dict to cache Model objects
    """
    if model_cache is None:
        model_cache = {}

    # Define metrics by target type
    REGRESSION_METRICS = [
        "rmse", "mae", "r2", "mape", "mam", "mad",
        "mae_mam_ratio", "mae_mad_ratio", "bias",
        "eval_data_std", "rmse_std_ratio", "training_time",
    ]
    CLASSIFICATION_METRICS = [
        "logloss", "accuracy", "precision", "recall", "f1",
        "roc_auc", "avg_precision", "training_time",
        "precision_at_threshold", "recall_at_threshold", "f1_at_threshold",
    ]

    # Select metrics based on target type
    score_fields = REGRESSION_METRICS if target_type == "regression" else CLASSIFICATION_METRICS

    # Load scores from CSV
    scores_data = {}
    scores_path = f"{target_dir}/scores_tracking.csv"
    if os.path.exists(scores_path):
        try:
            df = pd.read_csv(scores_path)
            model_col = next((c for c in ["MODEL_NAME", "Model", "model"] if c in df.columns), "model")
            for _, row in df.iterrows():
                model_name = row.get(model_col)
                if model_name:
                    scores_data[model_name] = {}
                    for field in score_fields:
                        # Try uppercase first, then lowercase
                        value = row.get(field.upper()) if field.upper() in row else row.get(field)
                        scores_data[model_name][field] = value

                    # Classification-specific: Calculate f1_at_threshold if missing
                    if target_type == "classification":
                        f1_val = scores_data[model_name].get("f1_at_threshold")
                        if f1_val is None or (isinstance(f1_val, float) and math.isnan(f1_val)):
                            prec = _nan_to_none(scores_data[model_name].get("precision_at_threshold"))
                            rec = _nan_to_none(scores_data[model_name].get("recall_at_threshold"))
                            if prec is not None and rec is not None and (prec + rec) > 0:
                                scores_data[model_name]["f1_at_threshold"] = 2 * (prec * rec) / (prec + rec)

                        # Parse THRESHOLDS column (dict-like string or scalar)
                        thresholds_raw = row.get("THRESHOLDS") if "THRESHOLDS" in row else row.get("thresholds")
                        if thresholds_raw is not None:
                            try:
                                import ast
                                if isinstance(thresholds_raw, str):
                                    thresholds_dict = ast.literal_eval(thresholds_raw)
                                    scores_data[model_name]["thresholds"] = _sanitize_json(thresholds_dict)
                                elif isinstance(thresholds_raw, (int, float)) and not (math.isnan(thresholds_raw) or math.isinf(thresholds_raw)):
                                    # Scalar threshold - build JSON from precision/recall/f1 at threshold
                                    scores_data[model_name]["thresholds"] = {
                                        "1": {
                                            "threshold": _nan_to_none(thresholds_raw),
                                            "precision": _nan_to_none(scores_data[model_name].get("precision_at_threshold")),
                                            "recall": _nan_to_none(scores_data[model_name].get("recall_at_threshold")),
                                            "f1": _nan_to_none(scores_data[model_name].get("f1_at_threshold")),
                                        }
                                    }
                            except:
                                pass
        except Exception as e:
            logger.warning(f"  Failed to load scores_tracking.csv: {e}")

    # Load best_params from target-level best_params.json
    all_best_params = {}
    best_params_path = f"{target_dir}/best_params.json"
    if os.path.exists(best_params_path):
        try:
            with open(best_params_path, "r") as f:
                all_best_params = json.load(f)
            if all_best_params:
                all_best_params = _sanitize_json(all_best_params)
        except Exception as e:
            logger.warning(f"  Failed to load best_params.json: {e}")

    # Discover models from folders (excluding feature_selection, tensorboard)
    skip_folders = {"feature_selection", "tensorboard", "preprocessing"}
    model_folders = set()
    if os.path.exists(target_dir):
        for item in os.listdir(target_dir):
            item_path = f"{target_dir}/{item}"
            if os.path.isdir(item_path) and item not in skip_folders:
                model_folders.add(item)

    if not model_folders:
        return {}

    # OPTIMIZATION: Bulk query all models at once
    model_folders_list = list(model_folders)
    existing_models = session.query(ModelType).filter(ModelType.name.in_(model_folders_list)).all()
    for m in existing_models:
        model_cache[m.name] = m

    # Create missing models in one batch
    missing_model_names = [name for name in model_folders_list if name not in model_cache]
    if missing_model_names:
        model_type_map = {
            "xgb": "xgboost", "lgb": "lightgbm", "catboost": "catboost",
            "rf": "random_forest", "svm": "svm", "lr": "logistic_regression",
            "mlp": "mlp", "keras": "keras", "lstm": "keras", "gru": "keras",
            "tcn": "keras", "sgd": "sgd", "linear": "linear",
        }
        new_models = []
        for model_name in missing_model_names:
            base_name = model_name.split(".")[0]
            model_type = model_type_map.get(base_name, base_name)
            new_models.append(ModelType(name=model_name, type=model_type))
        session.bulk_save_objects(new_models, return_defaults=True)
        session.flush()  # Single flush to get all IDs
        # Re-query to get the IDs
        for m in session.query(ModelType).filter(ModelType.name.in_(missing_model_names)).all():
            model_cache[m.name] = m

    # OPTIMIZATION: Bulk query existing scores
    model_ids = [model_cache[name].id for name in model_folders_list if name in model_cache]
    existing_scores = session.query(Model).filter(
        Model.best_model_id == best_model.id,
        Model.model_id.in_(model_ids),
    ).all()
    existing_score_map = {s.model_id: s for s in existing_scores}

    score_map = {}  # model_name -> Model
    new_scores = []  # Scores to bulk insert
    updated_any = False

    for model_name in model_folders_list:
        if model_name not in model_cache:
            continue
        model = model_cache[model_name]

        existing = existing_score_map.get(model.id)

        if existing:
            needs_update = False

            # Update best_params if missing
            if not existing.best_params:
                model_best_params = all_best_params.get(model_name)
                if model_best_params:
                    existing.best_params = _sanitize_json(model_best_params)
                    needs_update = True

            # Update score fields if missing (using target-type-specific fields)
            # Skip "bias" as it was introduced later and can legitimately be None
            skip_update_fields = {"bias"}
            score_row = scores_data.get(model_name, {})
            if score_row:
                for field in score_fields:
                    if field in skip_update_fields:
                        continue
                    if getattr(existing, field, None) is None:
                        value = _nan_to_none(score_row.get(field))
                        if value is not None:
                            setattr(existing, field, value)
                            needs_update = True

                # Update thresholds if missing (classification only)
                if target_type == "classification":
                    if not existing.thresholds and score_row.get("thresholds"):
                        existing.thresholds = score_row.get("thresholds")
                        needs_update = True

            if needs_update:
                updated_any = True

            score_map[model_name] = existing
            continue

        # Get best_params for this model from target-level best_params.json
        model_best_params = all_best_params.get(model_name)
        if model_best_params:
            model_best_params = _sanitize_json(model_best_params)

        score_row = scores_data.get(model_name, {})

        # Build kwargs based on target type
        score_kwargs = {
            "model_id": model.id,
            "best_model_id": best_model.id,
            "best_params": model_best_params,
            "training_time": _nan_to_none(score_row.get("training_time")),
        }

        if target_type == "regression":
            # Regression-specific metrics
            score_kwargs.update({
                "rmse": _nan_to_none(score_row.get("rmse")),
                "mae": _nan_to_none(score_row.get("mae")),
                "r2": _nan_to_none(score_row.get("r2")),
                "mape": _nan_to_none(score_row.get("mape")),
                "mam": _nan_to_none(score_row.get("mam")),
                "mad": _nan_to_none(score_row.get("mad")),
                "mae_mam_ratio": _nan_to_none(score_row.get("mae_mam_ratio")),
                "mae_mad_ratio": _nan_to_none(score_row.get("mae_mad_ratio")),
                "bias": _nan_to_none(score_row.get("bias")),
                "eval_data_std": _nan_to_none(score_row.get("eval_data_std")),
                "rmse_std_ratio": _nan_to_none(score_row.get("rmse_std_ratio")),
            })
        else:
            # Classification-specific metrics
            score_kwargs.update({
                "logloss": _nan_to_none(score_row.get("logloss")),
                "accuracy": _nan_to_none(score_row.get("accuracy")),
                "precision": _nan_to_none(score_row.get("precision")),
                "recall": _nan_to_none(score_row.get("recall")),
                "f1": _nan_to_none(score_row.get("f1")),
                "roc_auc": _nan_to_none(score_row.get("roc_auc")),
                "avg_precision": _nan_to_none(score_row.get("avg_precision")),
                "precision_at_threshold": _nan_to_none(score_row.get("precision_at_threshold")),
                "recall_at_threshold": _nan_to_none(score_row.get("recall_at_threshold")),
                "f1_at_threshold": _nan_to_none(score_row.get("f1_at_threshold")),
                "thresholds": score_row.get("thresholds"),
            })

        score = Model(**score_kwargs)
        session.add(score)
        new_scores.append((model_name, score))

    # OPTIMIZATION: Single flush for all updates and new scores
    if updated_any or new_scores:
        session.flush()

    # Map the new scores after flush (now they have IDs)
    for model_name, score in new_scores:
        score_map[model_name] = score

    if new_scores:
        logger.info(f"    Created {len(new_scores)} best_model_scores")

    return score_map


def _populate_feature_selection_ranks(session, feature_selection, target_dir, Feature, FeatureSelectionRank, FeatureSelectionMethod, FeatureType, pd, feature_map=None):
    """Create FeatureSelectionRank for each method CSV in feature_selection folder.

    Optimized with bulk operations to avoid N+1 query problem.
    Sets feature type based on method: Chi2 = categorical, others = numerical.

    Args:
        feature_map: Optional dict of {feature_name: Feature} to reuse from caller
    """
    feature_selection_dir = f"{target_dir}/feature_selection"
    if not os.path.exists(feature_selection_dir):
        return

    # Map partial filename (lowercase) to (db_method, feature_type)
    # Chi2 is for categorical features, all others are for numerical
    method_mappings = [
        ("chi2", FeatureSelectionMethod.CHI2.value, FeatureType.CATEGORICAL.value),
        ("person", FeatureSelectionMethod.PEARSONS_R.value, FeatureType.NUMERICAL.value),
        ("anova", FeatureSelectionMethod.ANOVA.value, FeatureType.NUMERICAL.value),
        ("spearman", FeatureSelectionMethod.SPEARMANS_R.value, FeatureType.NUMERICAL.value),
        ("kendall", FeatureSelectionMethod.KENDALLS_TAU.value, FeatureType.NUMERICAL.value),
        ("mi.csv", FeatureSelectionMethod.MUTUAL_INFORMATION.value, FeatureType.NUMERICAL.value),
        ("fi.csv", FeatureSelectionMethod.FI.value, FeatureType.NUMERICAL.value),
        ("rfe", FeatureSelectionMethod.RFE.value, FeatureType.NUMERICAL.value),
        ("sfs", FeatureSelectionMethod.SFS.value, FeatureType.NUMERICAL.value),
    ]

    # List all CSV files in the directory
    try:
        all_files = os.listdir(feature_selection_dir)
    except:
        return

    # Pre-collect all unique feature names from all CSVs
    all_feature_names = set()
    csv_data = []  # Store (csv_path, db_method, feature_type, df) for later processing

    for pattern, db_method, feature_type in method_mappings:
        csv_path = None
        for fn in all_files:
            if fn.lower().endswith('.csv') and pattern in fn.lower():
                csv_path = f"{feature_selection_dir}/{fn}"
                break

        if not csv_path:
            continue

        try:
            df = pd.read_csv(csv_path)
            df.columns = df.columns.str.lower()
            feature_names = df["features"].dropna().tolist()
            if feature_names:
                all_feature_names.update(feature_names)
                csv_data.append((csv_path, db_method, feature_type, df))
        except Exception as e:
            logger.warning(f"    Failed to read CSV for {db_method}: {e}")

    if not all_feature_names:
        return

    # Use provided feature_map or build one
    if feature_map is None:
        feature_map = {}

    # Only query/create features not already in the map
    missing_from_map = all_feature_names - set(feature_map.keys())
    if missing_from_map:
        # Bulk query existing features
        existing_features = session.query(Feature).filter(Feature.name.in_(missing_from_map)).all()
        for f in existing_features:
            feature_map[f.name] = f

        # Create missing features using _get_or_create_feature (handles type properly)
        still_missing = missing_from_map - set(feature_map.keys())
        for name in still_missing:
            feature_map[name] = _get_or_create_feature(session, Feature, name)

    # Bulk query all existing ranks for this feature_selection
    all_feature_ids = [f.id for f in feature_map.values() if f.name in all_feature_names]
    existing_ranks_query = session.query(
        FeatureSelectionRank.feature_id,
        FeatureSelectionRank.method
    ).filter(
        FeatureSelectionRank.feature_selection_id == feature_selection.id,
        FeatureSelectionRank.feature_id.in_(all_feature_ids),
    ).all()
    existing_rank_keys = {(r[0], r[1]) for r in existing_ranks_query}

    # Now process each CSV with the pre-built feature map
    all_new_ranks = []

    for csv_path, db_method, feature_type, df in csv_data:
        try:
            for _, row in df.iterrows():
                feature_name = row.get("features")
                if not feature_name or feature_name not in feature_map:
                    continue

                feature = feature_map[feature_name]

                # Update feature type if needed
                if feature_type and not feature.type:
                    feature.type = feature_type

                # Skip if already exists
                if (feature.id, db_method) in existing_rank_keys:
                    continue

                # Convert support to 0 or 1 (not null)
                support_val = row.get("support")
                if support_val is None or (isinstance(support_val, float) and math.isnan(support_val)):
                    support_val = 0
                else:
                    support_val = 1 if support_val else 0

                all_new_ranks.append(FeatureSelectionRank(
                    feature_id=feature.id,
                    feature_selection_id=feature_selection.id,
                    method=db_method,
                    score=_nan_to_none(row.get("score")),
                    pvalue=_nan_to_none(row.get("pvalue")),
                    rank=_nan_to_none(row.get("rank")),
                    support=support_val,
                    training_time=_nan_to_none(row.get("training_time")),
                ))
                # Track for duplicate check within this batch
                existing_rank_keys.add((feature.id, db_method))

        except Exception as e:
            logger.warning(f"    Failed to populate ranks for {db_method}: {e}")

    # Single bulk insert for all ranks
    if all_new_ranks:
        session.bulk_save_objects(all_new_ranks)
        session.flush()
        logger.info(f"    Created {len(all_new_ranks)} feature_selection_ranks (all methods)")


def _find_best_model_name(target_dir):
    """Find the best model name from .best or .keras files at root of target_dir."""
    if not os.path.exists(target_dir):
        return None

    for item in os.listdir(target_dir):
        item_path = f"{target_dir}/{item}"
        if os.path.isfile(item_path):
            # Check for .best or .keras files at root level
            if item.endswith(".best") or item.endswith(".keras"):
                # Extract model name (e.g., "xgb.best" -> "xgb", "lstm.keras" -> "lstm")
                model_name = item.rsplit(".", 1)[0]
                return model_name
    return None


def _get_best_score_from_tracking(target_dir, model_name, target_type, pd):
    """Get the score row for a specific model from scores_tracking.csv.

    Args:
        target_type: "regression" or "classification" - determines which metrics to return
    """
    scores_path = f"{target_dir}/scores_tracking.csv"
    if not os.path.exists(scores_path):
        return None

    # Define metrics by target type
    REGRESSION_METRICS = [
        "rmse", "mae", "r2", "mape", "mam", "mad",
        "mae_mam_ratio", "mae_mad_ratio", "bias",
        "eval_data_std", "rmse_std_ratio", "training_time",
    ]
    CLASSIFICATION_METRICS = [
        "logloss", "accuracy", "precision", "recall", "f1",
        "roc_auc", "avg_precision", "training_time",
        "precision_at_threshold", "recall_at_threshold", "f1_at_threshold",
    ]
    score_fields = REGRESSION_METRICS if target_type == "regression" else CLASSIFICATION_METRICS

    try:
        df = pd.read_csv(scores_path)
        # Try different column name variations
        model_col = None
        for col in ["MODEL_NAME", "Model", "model"]:
            if col in df.columns:
                model_col = col
                break
        if not model_col:
            logger.warning(f"  No model column found in scores_tracking.csv")
            return None

        # Find the row for this model
        model_rows = df[df[model_col] == model_name]
        if len(model_rows) > 0:
            row = model_rows.iloc[0]
            result = {"model_name": model_name}
            for field in score_fields:
                # Try uppercase first, then lowercase
                value = row.get(field.upper()) if field.upper() in row else row.get(field)
                result[field] = _nan_to_none(value)
            return result
    except Exception as e:
        logger.warning(f"  Failed to get best score from tracking: {e}")

    return None


def _get_or_create_best_model(session, experiment, target, target_dir, target_type, ModelType, BestModel, Model, joblib, pd, model_cache=None):
    """Get or create BestModel for a target.

    Args:
        target_type: "regression" or "classification" - determines which metrics to populate
        model_cache: Optional dict to cache Model objects across calls
    """
    if model_cache is None:
        model_cache = {}

    existing = session.query(BestModel).filter(
        BestModel.experiment_id == experiment.id,
        BestModel.target_id == target.id,
    ).first()

    if existing:
        # Still populate scores for any new models
        score_map = _populate_best_model_scores(
            session, existing, target_dir, target_type, ModelType, Model, pd, model_cache
        )

        # Fill in missing fields if needed
        needs_update = False

        # If best_model_id is not set, try to find from .best/.keras files
        if not existing.best_model_id:
            best_model_name = _find_best_model_name(target_dir)
            if best_model_name:
                model = _get_or_create_model(session, ModelType, best_model_name, model_cache)
                existing.best_model_id = model.id
                needs_update = True

        # Get the best model name for further updates
        best_model = None
        best_model_name = None
        if existing.best_model_id:
            # Check cache first
            for name, m in model_cache.items():
                if m.id == existing.best_model_id:
                    best_model = m
                    best_model_name = name
                    break
            if not best_model:
                best_model = session.query(ModelType).filter(ModelType.id == existing.best_model_id).first()
                if best_model:
                    best_model_name = best_model.name
                    model_cache[best_model_name] = best_model

        # Update best_best_model_score_id if not set
        if not existing.best_best_model_score_id and best_model_name and best_model_name in score_map:
            existing.best_best_model_score_id = score_map[best_model_name].id
            needs_update = True

        # Update best_score if not set
        if not existing.best_score and best_model_name:
            best_score = _get_best_score_from_tracking(target_dir, best_model_name, target_type, pd)
            if best_score:
                existing.best_score = _sanitize_json(best_score)
                needs_update = True

        # Update best_model_params if not set
        if not existing.best_model_params and best_model_name:
            best_params_path = f"{target_dir}/best_params.json"
            if os.path.exists(best_params_path):
                try:
                    with open(best_params_path, "r") as f:
                        all_best_params = json.load(f)
                    best_model_params = all_best_params.get(best_model_name)
                    if best_model_params:
                        existing.best_model_params = _sanitize_json(best_model_params)
                        needs_update = True
                except:
                    pass

        if needs_update:
            session.flush()

        return existing, score_map

    # Load all best_params from target-level best_params.json
    all_best_params = {}
    best_params_path = f"{target_dir}/best_params.json"
    if os.path.exists(best_params_path):
        try:
            with open(best_params_path, "r") as f:
                all_best_params = json.load(f)
            if all_best_params:
                all_best_params = _sanitize_json(all_best_params)
        except:
            pass

    # Load thresholds (classification only)
    best_thresholds = None
    if target_type == "classification":
        thresholds_path = f"{target_dir}/thresholds.pkl"
        if os.path.exists(thresholds_path):
            try:
                best_thresholds = joblib.load(thresholds_path)
                if best_thresholds:
                    best_thresholds = _sanitize_json(best_thresholds)
            except:
                pass

    # Find best model from .best or .keras files at root of target_dir
    best_model_name = _find_best_model_name(target_dir)
    best_model_id = None
    best_model_params = None
    best_score = None

    if best_model_name:
        model = _get_or_create_model(session, ModelType, best_model_name, model_cache)
        best_model_id = model.id
        # Get best_params for the best model specifically
        best_model_params = all_best_params.get(best_model_name)
        if best_model_params:
            best_model_params = _sanitize_json(best_model_params)
        # Get best_score from scores_tracking
        best_score = _get_best_score_from_tracking(target_dir, best_model_name, target_type, pd)
        if best_score:
            best_score = _sanitize_json(best_score)
        logger.info(f"    Found best model: {best_model_name}")

    best_model = BestModel(
        experiment_id=experiment.id,
        target_id=target.id,
        best_model_params=best_model_params,
        best_thresholds=best_thresholds,
        best_model_id=best_model_id,
        best_score=best_score,
    )
    session.add(best_model)
    session.flush()  # Need ID for score_map
    logger.info(f"    Created best_model for {target.name}")

    # Populate scores
    score_map = _populate_best_model_scores(
        session, best_model, target_dir, target_type, ModelType, Model, pd, model_cache
    )

    # Set best_best_model_score_id after scores are created (no extra flush needed, will be committed later)
    if best_model_name and best_model_name in score_map:
        best_model.best_best_model_score_id = score_map[best_model_name].id
        logger.info(f"    Set best_best_model_score_id to {best_model.best_best_model_score_id}")

    return best_model, score_map


def _get_or_create_feature_selection(session, experiment, target, target_dir, Feature, FeatureSelection, FeatureSelectionRank, FeatureSelectionMethod, FeatureType, feature_selection_association, joblib, pd, feature_cache=None):
    """Get or create FeatureSelection for a target.

    Args:
        feature_cache: Optional dict to cache Feature objects across calls
    """
    if feature_cache is None:
        feature_cache = {}

    existing = session.query(FeatureSelection).filter(
        FeatureSelection.experiment_id == experiment.id,
        FeatureSelection.target_id == target.id,
    ).first()

    if existing:
        # Still populate ranks for any new methods
        _populate_feature_selection_ranks(session, existing, target_dir, Feature, FeatureSelectionRank, FeatureSelectionMethod, FeatureType, pd, feature_map=feature_cache)
        return existing

    # Load features from features.pkl
    features_path = f"{target_dir}/features.pkl"
    if not os.path.exists(features_path):
        features_path = f"{target_dir}/feature_selection/features.pkl"

    if not os.path.exists(features_path):
        return None

    try:
        feature_names = joblib.load(features_path)
        if not isinstance(feature_names, list):
            return None

        feature_selection = FeatureSelection(
            experiment_id=experiment.id,
            target_id=target.id,
            best_features_path=features_path,
        )
        session.add(feature_selection)
        session.flush()  # Need ID for associations

        # OPTIMIZATION: Bulk query existing features first (only those not in cache)
        unique_names = list(set(feature_names))
        names_to_query = [n for n in unique_names if n not in feature_cache]

        if names_to_query:
            existing_features = session.query(Feature).filter(Feature.name.in_(names_to_query)).all()
            for f in existing_features:
                feature_cache[f.name] = f

        # Bulk create missing features
        missing_names = [n for n in unique_names if n not in feature_cache]
        if missing_names:
            new_features = [Feature(name=name) for name in missing_names]
            session.bulk_save_objects(new_features, return_defaults=True)
            session.flush()  # Single flush for all new features
            # Re-query to get the objects with IDs
            for f in session.query(Feature).filter(Feature.name.in_(missing_names)).all():
                feature_cache[f.name] = f

        # OPTIMIZATION: Bulk insert associations (single operation)
        association_values = [
            {"feature_selection_id": feature_selection.id, "feature_id": feature_cache[name].id}
            for name in feature_names if name in feature_cache
        ]
        if association_values:
            session.execute(
                feature_selection_association.insert().prefix_with("IGNORE"),
                association_values
            )
            # No flush needed here - will be flushed later or at commit

        logger.info(f"    Created feature_selection for {target.name} with {len(feature_names)} features")

        # Populate ranks (pass feature_cache to avoid re-querying features)
        _populate_feature_selection_ranks(session, feature_selection, target_dir, Feature, FeatureSelectionRank, FeatureSelectionMethod, FeatureType, pd, feature_map=feature_cache)

        return feature_selection
    except Exception as e:
        logger.warning(f"    Failed to create feature_selection for {target.name}: {e}")
        return None


# =============================================================================
# Main migration function
# =============================================================================

def upgrade() -> None:
    """Migrate all file-based data to database."""
    try:
        import joblib
        import pandas as pd
    except ImportError as e:
        logger.warning(f"Could not import required modules: {e}")
        return

    from sqlalchemy.orm import Session
    bind = op.get_bind()
    session = Session(bind=bind)

    try:
        from lecrapaud.models import (
            Experiment, ExperimentArtifact, ExperimentData,
            Feature, FeatureType, FeatureSelection, FeatureSelectionRank, FeatureSelectionMethod,
            ModelType, BestModel, Model,
        )
        from lecrapaud.models.feature_selection import lecrapaud_feature_selection_association

        _inject_catboost_wrapper()

        # Find all experiments with a path
        experiments = session.query(Experiment).filter(Experiment.path.isnot(None)).all()

        if not experiments:
            logger.info("No experiments with file paths found")
            return

        logger.info(f"Found {len(experiments)} experiment(s) to migrate")

        for experiment in experiments:
            experiment_path = str(experiment.path) if experiment.path else None
            if not experiment_path or not os.path.exists(experiment_path):
                continue

            logger.info(f"Migrating experiment {experiment.id}: {experiment.name}")

            # Shared caches for this experiment to reduce DB queries
            model_cache = {}
            feature_cache = {}

            try:
                # =============================================================
                # 1. ARTIFACTS FROM preprocessing/ FOLDER
                # =============================================================
                preprocessing_dir = f"{experiment_path}/preprocessing"
                if os.path.exists(preprocessing_dir):
                    artifact_files = [
                        ("scaler_x.pkl", "scaler", "scaler_x"),
                        ("column_transformer.pkl", "transformer", "column_transformer"),
                        ("pcas.pkl", "pca", "pcas"),
                        ("pcas_cross_sectional.pkl", "pca", "pcas_cross_sectional"),
                        ("pcas_temporal.pkl", "pca", "pcas_temporal"),
                        ("all_features.pkl", "features", "all_features"),
                        ("all_features_before_encoding.pkl", "features", "all_features_before_encoding"),
                        ("all_features_before_selection.pkl", "features", "all_features_before_selection"),
                    ]

                    for file_name, artifact_type, artifact_name in artifact_files:
                        file_path = f"{preprocessing_dir}/{file_name}"
                        if os.path.exists(file_path):
                            try:
                                obj = joblib.load(file_path)
                                data = _serialize_joblib(obj)
                                _save_artifact(
                                    session, ExperimentArtifact,
                                    experiment_id=experiment.id,
                                    artifact_type=artifact_type,
                                    artifact_name=artifact_name,
                                    data=data,
                                    serialization_format="joblib",
                                )
                                logger.info(f"  Migrated {artifact_name}")
                            except Exception as e:
                                logger.warning(f"  Failed to migrate {artifact_name}: {e}")

                # =============================================================
                # 2. DATA FROM data/ FOLDER
                # =============================================================
                data_dir = f"{experiment_path}/data"
                if os.path.exists(data_dir):
                    data_files = ["train", "val", "test", "train_scaled", "val_scaled", "test_scaled"]

                    for data_type in data_files:
                        # Try .pkl first, then .parquet
                        for ext in [".pkl", ".parquet"]:
                            file_path = f"{data_dir}/{data_type}{ext}"
                            if os.path.exists(file_path):
                                try:
                                    if ext == ".pkl":
                                        df = joblib.load(file_path)
                                    else:
                                        df = pd.read_parquet(file_path)

                                    if isinstance(df, pd.DataFrame):
                                        data = _serialize_dataframe(df)
                                        _save_dataframe_record(
                                            session, ExperimentData,
                                            experiment_id=experiment.id,
                                            data_type=data_type,
                                            data=data,
                                            row_count=len(df),
                                            column_count=len(df.columns),
                                        )
                                        logger.info(f"  Migrated data/{data_type}")
                                except Exception as e:
                                    logger.warning(f"  Failed to migrate data/{data_type}: {e}")
                                break

                    # Handle full.pkl -> extract pca_visualization (lighter)
                    for ext in [".pkl", ".parquet"]:
                        full_path = f"{data_dir}/full{ext}"
                        if os.path.exists(full_path):
                            try:
                                if ext == ".pkl":
                                    full_df = joblib.load(full_path)
                                else:
                                    full_df = pd.read_parquet(full_path)

                                if isinstance(full_df, pd.DataFrame):
                                    # Extract PCA columns + targets for visualization
                                    pca_cols = [col for col in full_df.columns if "_pca_" in col or col.startswith("CS_PC_") or col.startswith("TMP_PC_")]
                                    target_cols = [col for col in full_df.columns if col.startswith("TARGET_")]
                                    if pca_cols:
                                        pca_viz_cols = pca_cols + target_cols
                                        pca_viz_df = full_df[pca_viz_cols]
                                        data = _serialize_dataframe(pca_viz_df)
                                        _save_dataframe_record(
                                            session, ExperimentData,
                                            experiment_id=experiment.id,
                                            data_type="pca_visualization",
                                            data=data,
                                            row_count=len(pca_viz_df),
                                            column_count=len(pca_viz_df.columns),
                                        )
                                        logger.info(f"  Migrated data/pca_visualization (from full)")
                                    else:
                                        logger.info(f"  Skipped full (no PCA columns found)")
                            except Exception as e:
                                logger.warning(f"  Failed to migrate full -> pca_visualization: {e}")
                            break

                # =============================================================
                # 3. PROCESS EACH TARGET
                # =============================================================
                for target in experiment.targets:
                    target_dir = f"{experiment_path}/{target.name}"
                    if not os.path.exists(target_dir):
                        continue

                    # Determine target type (default to regression if not set)
                    target_type = getattr(target, "type", None) or "regression"
                    logger.info(f"  Processing {target.name} ({target_type})...")

                    # Get/create best_model and scores
                    best_model, score_map = _get_or_create_best_model(
                        session, experiment, target, target_dir, target_type,
                        ModelType, BestModel, Model, joblib, pd, model_cache
                    )

                    # Get/create feature_selection and ranks
                    _get_or_create_feature_selection(
                        session, experiment, target, target_dir,
                        Feature, FeatureSelection, FeatureSelectionRank, FeatureSelectionMethod, FeatureType,
                        lecrapaud_feature_selection_association, joblib, pd, feature_cache
                    )

                    # ---------------------------------------------------------
                    # 3a. TARGET-LEVEL ARTIFACTS (scaler_y, thresholds, features)
                    # ---------------------------------------------------------
                    target_artifacts = [
                        ("scaler_y.pkl", "scaler", "scaler_y"),
                        ("thresholds.pkl", "threshold", "thresholds"),
                        ("features.pkl", "features", "features"),
                    ]

                    for file_name, artifact_type, artifact_name in target_artifacts:
                        file_path = f"{target_dir}/{file_name}"
                        if os.path.exists(file_path):
                            try:
                                obj = joblib.load(file_path)
                                data = _serialize_joblib(obj)
                                _save_artifact(
                                    session, ExperimentArtifact,
                                    experiment_id=experiment.id,
                                    artifact_type=artifact_type,
                                    artifact_name=artifact_name,
                                    data=data,
                                    serialization_format="joblib",
                                    target_id=target.id,
                                )
                                logger.info(f"    Migrated {artifact_name}")
                            except Exception as e:
                                logger.warning(f"    Failed to migrate {artifact_name}: {e}")

                    # ---------------------------------------------------------
                    # 3b. TARGET-LEVEL DATA (scores_tracking)
                    # ---------------------------------------------------------
                    scores_path = f"{target_dir}/scores_tracking.csv"
                    if os.path.exists(scores_path):
                        try:
                            df = pd.read_csv(scores_path)
                            data = _serialize_dataframe(df)
                            _save_dataframe_record(
                                session, ExperimentData,
                                experiment_id=experiment.id,
                                data_type="scores_tracking",
                                data=data,
                                row_count=len(df),
                                column_count=len(df.columns),
                                target_id=target.id,
                            )
                            logger.info(f"    Migrated scores_tracking")
                        except Exception as e:
                            logger.warning(f"    Failed to migrate scores_tracking: {e}")

                    # ---------------------------------------------------------
                    # 3c. FEATURE SELECTION CSVs
                    # ---------------------------------------------------------
                    fs_dir = f"{target_dir}/feature_selection"
                    if os.path.exists(fs_dir):
                        for csv_file in os.listdir(fs_dir):
                            if csv_file.endswith(".csv"):
                                csv_path = f"{fs_dir}/{csv_file}"
                                try:
                                    df = pd.read_csv(csv_path)
                                    data = _serialize_dataframe(df)
                                    data_type = f"feature_scores_{csv_file.replace('.csv', '').replace(' ', '_').replace(chr(39), '')}"
                                    _save_dataframe_record(
                                        session, ExperimentData,
                                        experiment_id=experiment.id,
                                        data_type=data_type,
                                        data=data,
                                        row_count=len(df),
                                        column_count=len(df.columns),
                                        target_id=target.id,
                                    )
                                    logger.info(f"    Migrated {data_type}")
                                except Exception as e:
                                    logger.warning(f"    Failed to migrate {csv_file}: {e}")

                    # ---------------------------------------------------------
                    # 3d. MODEL FOLDERS (models + predictions)
                    # ---------------------------------------------------------
                    skip_folders = {"feature_selection", "tensorboard", "preprocessing"}
                    for model_folder in os.listdir(target_dir):
                        model_folder_path = f"{target_dir}/{model_folder}"
                        if not os.path.isdir(model_folder_path) or model_folder in skip_folders:
                            continue

                        model_name = model_folder
                        score = score_map.get(model_name)
                        score_id = score.id if score else None

                        if not score_id:
                            logger.warning(f"    No score found for model {model_name}, skipping artifacts")
                            continue

                        # Find and save model files
                        for file_name in os.listdir(model_folder_path):
                            file_path = f"{model_folder_path}/{file_name}"
                            if os.path.isdir(file_path):
                                continue

                            # Model files
                            if file_name.endswith(".best") or file_name.endswith(".pkl"):
                                if "hyperopt" in file_name or "trials" in file_name:
                                    continue  # Skip hyperopt trials
                                try:
                                    model = joblib.load(file_path)
                                    model = _unwrap_catboost(model)
                                    data = _serialize_joblib(model)
                                    _save_artifact(
                                        session, ExperimentArtifact,
                                        experiment_id=experiment.id,
                                        artifact_type="model",
                                        artifact_name=f"{file_name}",
                                        data=data,
                                        serialization_format="joblib",
                                        target_id=target.id,
                                        best_model_score_id=score_id,
                                    )
                                    logger.info(f"    Migrated model {file_name}")
                                except Exception as e:
                                    logger.warning(f"    Failed to migrate model {file_name}: {e}")

                            # Keras models
                            elif file_name.endswith(".keras") or file_name.endswith(".h5"):
                                try:
                                    from keras.models import load_model
                                    model = load_model(file_path)
                                    data = _serialize_keras(model)
                                    _save_artifact(
                                        session, ExperimentArtifact,
                                        experiment_id=experiment.id,
                                        artifact_type="model",
                                        artifact_name=f"{file_name}",
                                        data=data,
                                        serialization_format="keras",
                                        target_id=target.id,
                                        best_model_score_id=score_id,
                                    )
                                    logger.info(f"    Migrated model {file_name}")
                                except Exception as e:
                                    logger.warning(f"    Failed to migrate model {file_name}: {e}")

                            # Prediction CSVs
                            elif file_name == "prediction.csv":
                                try:
                                    df = pd.read_csv(file_path)
                                    data = _serialize_dataframe(df)
                                    _save_dataframe_record(
                                        session, ExperimentData,
                                        experiment_id=experiment.id,
                                        data_type="prediction",
                                        data=data,
                                        row_count=len(df),
                                        column_count=len(df.columns),
                                        target_id=target.id,
                                        best_model_score_id=score_id,
                                    )
                                    logger.info(f"    Migrated prediction for {model_name}")
                                except Exception as e:
                                    logger.warning(f"    Failed to migrate prediction for {model_name}: {e}")

                # Commit after each experiment
                session.commit()
                logger.info(f"  Committed experiment {experiment.id}")

            except Exception as e:
                logger.error(f"Failed to migrate experiment {experiment.id}: {e}")
                session.rollback()

        logger.info("Migration complete")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def downgrade() -> None:
    """Downgrade is a no-op."""
    pass
