"""LeCrapaud API module.

This module provides the main interface for the LeCrapaud machine learning pipeline.
It allows for end-to-end ML workflows including data preprocessing, feature engineering,
model training, and prediction.

Basic Usage:
    # Set database URI (optional, uses env var DB_URI by default)
    LeCrapaud.set_uri("postgresql://user:pass@host/db")

    # Create a new experiment and train
    experiment = LeCrapaud(target_numbers=[1], target_clf=[1])
    experiment.fit(data)

    # Make predictions
    predictions, scores_reg, scores_clf = experiment.predict(new_data)

    # Load existing experiment
    experiment = LeCrapaud.get(id=123)
    predictions = experiment.predict(new_data)

    # Alternative: pass data directly (creates experiment immediately)
    experiment = LeCrapaud(data=data, target_numbers=[1], target_clf=[1])
    experiment.fit(data)

    # Class methods for experiment management
    best_exp = LeCrapaud.get_best_experiment_by_name('my_experiment')
    all_exps = LeCrapaud.list_experiments('my_experiment')
"""

import pandas as pd
import ast
import os
import time
import logging
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
import lime
import lime.lime_tabular
import shap
from typing import Literal
from lecrapaud.db.session import init_db
from lecrapaud.services import ArtifactService
from lecrapaud.feature_selection import FeatureSelector
from lecrapaud.model_preprocessing import ModelPreprocessor
from lecrapaud.model import LeCrapaudModel, plot_threshold
from lecrapaud.model_selection import (
    ModelSelector,
    evaluate,
    plot_evaluation_for_classification,
    plot_evaluation_for_regression,
)
from lecrapaud.feature_engineering import FeatureEngineer
from lecrapaud.feature_preprocessing import FeaturePreprocessor
from lecrapaud.experiment import create_experiment
from lecrapaud.models import Experiment
from lecrapaud.search_space import normalize_models_idx, all_models
from lecrapaud.utils import logger
from lecrapaud.directories import tmp_dir


class LeCrapaud:
    """
    Unified LeCrapaud class for machine learning experiments.

    This class provides both the ML pipeline functionality and experiment management.
    It can be initialized with configuration parameters, and optionally with data
    or an existing experiment ID.

    Usage:
        # Create new experiment (experiment created on fit)
        experiment = LeCrapaud(target_numbers=[1, 2], ...)
        experiment.fit(data)

        # Load existing experiment
        experiment = LeCrapaud.get(id=123)

        # Alternative: pass data directly (creates experiment immediately)
        experiment = LeCrapaud(data=df, target_numbers=[1, 2], ...)

        # Make predictions
        predictions = experiment.predict(new_data)

    Args:
        data (pd.DataFrame, optional): Input data for a new experiment (if provided,
            creates experiment immediately; otherwise created on fit())
        **kwargs: Configuration parameters (target_numbers, target_clf, etc.)
    """

    _uri = None  # Class-level database URI

    def __init__(self, id: int = None, data: pd.DataFrame = None, **kwargs):
        """
        Initialize LeCrapaud with configuration parameters.

        Args:
            data (pd.DataFrame, optional): If provided, creates experiment immediately.
                Otherwise, experiment is created when fit() is called.
            id (int, optional): Experiment ID to load an existing experiment.
            **kwargs: Configuration parameters
        """
        # Initialize database connection
        init_db(uri=self._uri)

        self.experiment = None
        self._data = data  # Store data for later use in fit() if needed

        # Merge defaults with provided kwargs
        effective_kwargs = {**self.DEFAULT_PARAMS, **kwargs}

        # Normalize models_idx if present
        if "models_idx" in effective_kwargs:
            effective_kwargs["models_idx"] = normalize_models_idx(
                effective_kwargs["models_idx"]
            )

        # Set all parameters as instance attributes
        for key, value in effective_kwargs.items():
            setattr(self, key, value)

        # Load existing experiment by ID (backward compatibility)
        if id is not None:
            experiment = Experiment.get(id)
            if experiment is None:
                raise ValueError(f"Experiment with id={id} not found")
            self._load_experiment(experiment)
        # Create experiment immediately if data is provided (backward compatibility)
        elif data is not None:
            self._create_experiment(data)

    def _create_experiment(self, data: pd.DataFrame):
        """Create experiment and set up directories."""
        effective_kwargs = {k: getattr(self, k, v) for k, v in self.DEFAULT_PARAMS.items()}
        # Extract required positional/named args from kwargs
        experiment_name = effective_kwargs.pop("experiment_name")
        date_column = effective_kwargs.pop("date_column", None)
        group_column = effective_kwargs.pop("group_column", None)
        self.experiment = create_experiment(
            data=data,
            experiment_name=experiment_name,
            date_column=date_column,
            group_column=group_column,
            **effective_kwargs
        )

    def _load_experiment(self, experiment: Experiment):
        """Load an existing experiment and set up instance."""
        self.experiment = experiment

        # Context from DB takes precedence over current attributes
        for key, value in experiment.context.items():
            setattr(self, key, value)

    @classmethod
    def set_uri(cls, uri: str):
        """
        Set the database URI for all LeCrapaud instances.

        Args:
            uri (str): Database connection URI (e.g., "postgresql://user:pass@host/db")
        """
        cls._uri = uri
        init_db(uri=uri)

    @classmethod
    def get(cls, id: int, **kwargs):
        """
        Load an existing experiment by ID.

        Args:
            id (int): Experiment ID to load
            **kwargs: Additional configuration overrides

        Returns:
            LeCrapaud: Instance with loaded experiment
        """
        instance = cls(**kwargs)
        experiment = Experiment.get(id)
        if experiment is None:
            raise ValueError(f"Experiment with id={id} not found")
        instance._load_experiment(experiment)
        return instance

    # Default values for all experiment parameters
    DEFAULT_PARAMS = {
        # Experiment
        "experiment_name": "experiment",
        # Feature Engineering
        "columns_drop": [],
        "columns_boolean": [],
        "columns_date": [],
        "columns_te_groupby": [],
        "columns_te_target": [],
        "fourier_order": 1,
        # Preprocessing
        "time_series": False,
        "val_size": 0.2,
        "test_size": 0.2,
        "columns_pca": [],
        "pca_temporal": [],
        "pca_cross_sectional": [],
        "columns_onehot": [],
        "columns_binary": [],
        "columns_ordinal": [],
        "columns_frequency": [],
        # Feature Selection
        "percentile": 20,
        "corr_threshold": 80,
        "max_features": None,  # None = auto-computed based on n_samples (√n or n/10)
        "max_p_value": 0.05,  # Universal p-value threshold for statistical tests
        "max_p_value_categorical": 0.05,  # Kept for backward compatibility
        "min_correlation": 0.1,  # Minimum correlation magnitude for Spearman/Kendall
        "cumulative_importance": 0.80,  # Cumulative threshold for MI and FI (80%)
        "auto_select_feature_count": True,
        # Model Selection
        "target_numbers": [],
        "target_clf": [],
        "models_idx": [],
        "max_timesteps": 120,
        "perform_hyperopt": True,
        "number_of_trials": 20,
        "perform_crossval": False,
        "plot": True,
        "preserve_model": True,
        "target_clf_thresholds": {},
        "use_class_weights": True,
        "optimization_metric": {},  # Per-target: {1: "ROC_AUC", 2: "RMSE"}, empty = auto
        # Data structure
        "date_column": None,
        "group_column": None,
    }

    @classmethod
    def get_default_params(cls):
        """Get the default parameters for experiments."""
        return cls.DEFAULT_PARAMS.copy()

    def get_effective_context(self):
        """Get the effective context (merged defaults + experiment context)."""
        return {k: getattr(self, k, v) for k, v in self.DEFAULT_PARAMS.items()}

    @classmethod
    def get_last_experiment_by_name(cls, name: str, **kwargs):
        """Retrieve the last experiment by name."""
        exp = Experiment.get_last_by_name(name)
        if exp is None:
            return None
        return cls.get(id=exp.id, **kwargs)

    @classmethod
    def get_best_experiment_by_name(cls, name: str, **kwargs):
        """Retrieve the best experiment by score."""
        best_exp = Experiment.get_best_by_score(name=name)
        if not best_exp:
            return None
        return cls.get(id=best_exp.id, **kwargs)

    @classmethod
    def list_experiments(cls, name: str = None, limit: int = 1000):
        """List all experiments in the database."""
        return [
            cls.get(id=exp.id) for exp in Experiment.get_all_by_name(name=name, limit=limit)
        ]

    @classmethod
    def compare_experiment_scores(cls, name: str) -> pd.DataFrame:
        """Compare scores of experiments with matching names.

        Returns:
            pd.DataFrame with columns: experiment, target, target_type, rmse, logloss, accuracy, f1, roc_auc
        """
        experiments = cls.list_experiments(name=name)

        if not experiments:
            return pd.DataFrame()

        rows = []
        for exp in experiments:
            # Get target_clf from experiment context to determine target types
            target_clf = exp.experiment.context.get("target_clf", [])

            for model_sel in exp.experiment.best_models:
                if model_sel.score:
                    # Extract target number from target name (e.g., "TARGET_1" -> 1)
                    target_name = model_sel.target.name
                    try:
                        target_number = int(target_name.split("_")[1])
                        target_type = "classification" if target_number in target_clf else "regression"
                    except (IndexError, ValueError):
                        target_type = "unknown"

                    row = {
                        "experiment": exp.experiment.name,
                        "target": target_name,
                        "target_type": target_type,
                        "best_model": model_sel.model.model_type.name if model_sel.model else None,
                        "rmse": model_sel.score.get("rmse"),
                        "mae": model_sel.score.get("mae"),
                        "r2": model_sel.score.get("r2"),
                        "logloss": model_sel.score.get("logloss"),
                        "accuracy": model_sel.score.get("accuracy"),
                        "precision": model_sel.score.get("precision"),
                        "recall": model_sel.score.get("recall"),
                        "f1": model_sel.score.get("f1"),
                        "roc_auc": model_sel.score.get("roc_auc"),
                        "avg_precision": model_sel.score.get("avg_precision"),
                    }
                    rows.append(row)
                else:
                    logger.warning(
                        f"No best score found for experiment {exp.experiment.name} and target {model_sel.target.name}"
                    )

        return pd.DataFrame(rows)

    # Main ML Pipeline Methods
    # ========================

    def fit(self, data: pd.DataFrame = None, best_params=None):
        """
        Fit the complete ML pipeline on the provided data.

        Args:
            data (pd.DataFrame, optional): Input training data. If not provided,
                uses data passed to __init__. Required if no data was passed to __init__.
            best_params (dict, optional): Pre-defined best parameters

        Returns:
            self: Returns self for chaining
        """
        # Use provided data or fall back to data from __init__
        if data is None:
            data = self._data
        if data is None:
            raise ValueError(
                "No data provided. Pass data to fit() or to LeCrapaud(data=...)"
            )

        # Create experiment if not already created
        if self.experiment is None:
            self._create_experiment(data)

        try:
            logger.info("\n" + "=" * 60 + f"\n  STARTING TRAINING: {self.experiment.name}\n" + "=" * 60)

            # Step 1: Feature Engineering
            logger.info("\n[Step 1/5] Feature Engineering...")
            feature_eng = FeatureEngineer(experiment=self.experiment)
            feature_eng.fit(data)
            data_eng = feature_eng.get_data()
            logger.debug("Feature engineering done.")

            # Step 2: Feature Preprocessing (split data)
            logger.info("\n[Step 2/5] Feature Preprocessing...")
            from lecrapaud.feature_preprocessing import split_data

            train, val, test = split_data(data_eng, experiment=self.experiment)

            # Apply feature preprocessing transformations
            feature_preprocessor = FeaturePreprocessor(experiment=self.experiment)
            feature_preprocessor.fit(train)
            train = feature_preprocessor.get_data()
            if val is not None:
                val = feature_preprocessor.transform(val)
            if test is not None:
                test = feature_preprocessor.transform(test)
            logger.debug("Feature preprocessing done.")

            # Step 3: Feature Selection (for each target)
            logger.info("\n[Step 3/5] Feature Selection...")
            for target_number in self.target_numbers:
                feature_selector = FeatureSelector(
                    experiment=self.experiment, target_number=target_number
                )
                feature_selector.fit(train)

            # Refresh experiment to get updated features
            self.experiment = Experiment.get(self.experiment.id)
            all_features = self.experiment.get_all_features(
                date_column=self.date_column, group_column=self.group_column
            )
            # Save all features to database
            ArtifactService.save_artifact(
                experiment_id=self.experiment.id,
                artifact_type="features",
                artifact_name="all_features",
                obj=all_features,
                serialization_format="json",
            )
            logger.debug("Feature selection done.")

            # Step 4: Model Preprocessing (scaling)
            logger.info("\n[Step 4/5] Model Preprocessing...")
            model_preprocessor = ModelPreprocessor(experiment=self.experiment)

            # Fit and transform training data, then transform val/test
            model_preprocessor.fit(train)
            train_scaled = model_preprocessor.get_data()
            val_scaled = model_preprocessor.transform(val) if val is not None else None
            test_scaled = model_preprocessor.transform(test) if test is not None else None

            # Create data dict for model selection (keep both raw and scaled splits)
            std_data = {
                "train": train,
                "val": val,
                "test": test,
                "train_scaled": train_scaled,
                "val_scaled": val_scaled,
                "test_scaled": test_scaled,
            }
            # Save data to database via ArtifactService
            for key, items in std_data.items():
                if items is not None:
                    ArtifactService.save_dataframe(
                        experiment_id=self.experiment.id,
                        data_type=key,
                        df=items,
                    )

            # Handle time series reshaping if needed
            reshaped_data = None
            # Check if any model requires recurrent processing
            need_reshaping = (
                any(all_models[i].get("recurrent") for i in self.models_idx)
                and self.time_series
            )

            if need_reshaping:
                # Sanity check: make sure we have enough data for max_timesteps
                if (
                    self.group_column
                    and train_scaled.groupby(self.group_column).size().min()
                    < self.max_timesteps
                ) or train_scaled.shape[0] < self.max_timesteps:
                    raise ValueError(
                        f"Not enough data for group_column {self.group_column} to reshape data for recurrent models"
                    )

                from lecrapaud.model_preprocessing import reshape_time_series

                features = self.experiment.get_all_features(
                    date_column=self.date_column, group_column=self.group_column
                )
                reshaped_data = reshape_time_series(
                    self.experiment,
                    features,
                    train_scaled,
                    val_scaled,
                    test_scaled,
                    timesteps=self.max_timesteps,
                )
            logger.debug("Model preprocessing done.")

            # Step 5: Model Selection (for each target)
            logger.info("\n[Step 5/5] Model Selection...")
            self.models_ = {}
            for target_number in self.target_numbers:
                model_selector = ModelSelector(
                    experiment=self.experiment, target_number=target_number
                )
                model_selector.fit(
                    std_data, reshaped_data=reshaped_data, best_params=best_params
                )
                self.models_[target_number] = model_selector.get_best_model()
            logger.debug("Model selection done.")

            # Refresh experiment to get updated model selections and scores
            self.experiment = Experiment.get(self.experiment.id)

            # Update cached scores after all models are trained
            logger.debug("Updating cached scores...")
            self.experiment.update_cached_scores()
            self.experiment.save()
            logger.debug("Cached scores updated.")

            return self

        except Exception as e:
            # Delete failed experiment and its related data
            logger.error(f"Training failed: {e}. Deleting experiment {self.experiment.id}...")
            try:
                self.experiment.destroy()
                self.experiment = None
                logger.info("Failed experiment deleted.")
            except Exception as delete_error:
                logger.error(f"Failed to delete experiment: {delete_error}")
            raise

    def predict(self, new_data, verbose: int = 0):
        """
        Make predictions on new data using the trained pipeline.

        Args:
            new_data (pd.DataFrame): Input data for prediction
            verbose (int): Verbosity level (0=warnings only, 1=all logs)

        Returns:
            tuple: (predictions_df, scores_regression, scores_classification)
        """
        # for scores if TARGET is in columns
        scores_reg = []
        scores_clf = []
        prediction_times = {}

        if verbose == 0:
            logger.setLevel(logging.WARNING)

        logger.info("\n" + "=" * 60 + f"\n  STARTING PREDICTION: {self.experiment.name}\n" + "=" * 60)
        logger.info(f"  Input data: {new_data.shape[0]} rows, {new_data.shape[1]} columns")

        # Apply the same preprocessing pipeline as training
        # Step 1: Feature Engineering
        logger.debug("Applying feature engineering...")
        feature_eng = FeatureEngineer(experiment=self.experiment)
        data = feature_eng.transform(new_data)

        # Step 2: Feature Preprocessing (no splitting for prediction)
        logger.debug("Applying feature preprocessing...")
        feature_preprocessor = FeaturePreprocessor(experiment=self.experiment)
        # Load existing transformations and apply
        data = feature_preprocessor.transform(data)

        # Step 3: Model Preprocessing (scaling)
        logger.debug("Applying model preprocessing...")
        model_preprocessor = ModelPreprocessor(experiment=self.experiment)
        # Apply existing scaling
        scaled_data = model_preprocessor.transform(data)

        # Step 4: Time series reshaping if needed
        reshaped_data = None
        # Check if any model requires recurrent processing
        need_reshaping = (
            any(all_models[i].get("recurrent") for i in self.models_idx)
            and self.time_series
        )

        if need_reshaping:
            # Sanity check: make sure we have enough data for max_timesteps
            if (
                self.group_column
                and scaled_data.groupby(self.group_column).size().min()
                < self.max_timesteps
            ) or scaled_data.shape[0] < self.max_timesteps:
                raise ValueError(
                    f"Not enough data for group_column {self.group_column} to reshape data for recurrent models"
                )

            from lecrapaud.model_preprocessing import reshape_time_series

            all_features = self.experiment.get_all_features(
                date_column=self.date_column, group_column=self.group_column
            )
            # For prediction, we reshape the entire dataset
            reshaped_data = reshape_time_series(
                self.experiment, all_features, scaled_data, timesteps=self.max_timesteps
            )
            reshaped_data = reshaped_data[
                "x_train_reshaped"
            ]  # Only need X data for prediction

        # Step 5: Predict for each target
        logger.info(f"\n  Generating predictions for {len(self.target_numbers)} target(s)...")
        for target_number in self.target_numbers:
            # Load the trained model from database
            model = self.load_model(target_number)
            logger.info(f"    TARGET_{target_number} ({model.target_type}) using {model.model_name}...")

            # Get features for this target
            all_features = self.experiment.get_all_features(
                date_column=self.date_column, group_column=self.group_column
            )
            features = self.experiment.get_features(target_number)

            # Prepare prediction data
            if model.recurrent:
                features_idx = [
                    i for i, e in enumerate(all_features) if e in set(features)
                ]
                x_pred = reshaped_data[:, :, features_idx]
            else:
                source_data = scaled_data if model.need_scaling else data
                # Use model's expected feature order if available
                model_features = None
                if hasattr(model._model, "feature_names_in_"):
                    # sklearn models
                    model_features = list(model._model.feature_names_in_)
                elif hasattr(model._model, "feature_name"):
                    # LightGBM - use feature_name() method
                    model_features = model._model.feature_name()
                elif hasattr(model._model, "feature_names_"):
                    # CatBoost
                    model_features = model._model.feature_names_
                elif hasattr(model._model, "feature_names"):
                    # XGBoost Booster
                    model_features = model._model.feature_names

                x_pred = source_data[model_features] if model_features else source_data[features]

            # Make prediction
            start = time.time()
            y_pred = model.predict(x_pred)
            end = time.time()
            prediction_times[target_number] = end - start
            logger.debug(f"Prediction for TARGET_{target_number} took {end - start:.2f}s")

            # Fix index for recurrent models
            if model.recurrent:
                y_pred.index = new_data.index

            # Unscale prediction if needed
            if (
                model.need_scaling
                and model.target_type == "regression"
                and model.scaler_y is not None
            ):
                y_pred = pd.Series(
                    model.scaler_y.inverse_transform(
                        y_pred.values.reshape(-1, 1)
                    ).flatten(),
                    index=new_data.index,
                )
                y_pred.name = "PRED"

            # Evaluate if target is present in new_data
            target_col = next(
                (
                    col
                    for col in new_data.columns
                    if col.upper() == f"TARGET_{target_number}"
                ),
                None,
            )
            if target_col is not None:
                y_true = new_data[target_col]
                prediction = pd.concat([y_true, y_pred], axis=1)
                prediction.rename(columns={target_col: "TARGET"}, inplace=True)
                score = evaluate(
                    prediction,
                    target_type=model.target_type,
                )
                score["TARGET"] = f"TARGET_{target_number}"

                if model.target_type == "classification":
                    scores_clf.append(score)
                else:
                    scores_reg.append(score)

            # Add predictions to the output dataframe
            if isinstance(y_pred, pd.DataFrame):
                y_pred = y_pred.add_prefix(f"TARGET_{target_number}_")
                new_data = pd.concat([new_data, y_pred], axis=1)
            else:
                y_pred.name = f"TARGET_{target_number}_PRED"
                new_data = pd.concat([new_data, y_pred], axis=1)

        # Format scores
        if len(scores_reg) > 0:
            scores_reg = pd.DataFrame(scores_reg).set_index("TARGET")
        if len(scores_clf) > 0:
            scores_clf = pd.DataFrame(scores_clf).set_index("TARGET")

        # Log summary
        total_time = sum(prediction_times.values())
        summary_lines = [
            "",
            "=" * 60,
            "  PREDICTION COMPLETE",
            "=" * 60,
            f"  Rows predicted: {new_data.shape[0]}",
            f"  Total time: {total_time:.2f}s",
            "",
        ]

        # Add scores if available
        if len(scores_reg) > 0 or len(scores_clf) > 0:
            summary_lines.append("  Evaluation scores (TARGET columns found):")
            if len(scores_reg) > 0:
                for target in scores_reg.index:
                    row = scores_reg.loc[target]
                    summary_lines.append(f"    {target}: RMSE={row.get('RMSE', 'N/A'):.4f}, R²={row.get('R2', 'N/A'):.4f}")
            if len(scores_clf) > 0:
                for target in scores_clf.index:
                    row = scores_clf.loc[target]
                    summary_lines.append(f"    {target}: Precision={row.get('PRECISION', 'N/A'):.4f}, Recall={row.get('RECALL', 'N/A'):.4f}, ROC_AUC={row.get('ROC_AUC', 'N/A'):.4f}")
        else:
            summary_lines.append("  No TARGET columns in input data (no evaluation scores)")

        summary_lines.append("=" * 60)
        logger.info("\n".join(summary_lines))

        return new_data, scores_reg, scores_clf

    def get_scores(self, target_number: int):
        """
        Get all model scores for a specific target from the database.

        Args:
            target_number (int): Target number to get scores for

        Returns:
            pd.DataFrame: DataFrame with scores for each model.
                For regression: DATE, MODEL_NAME, EVAL_DATA_STD, RMSE, MAE, MAPE, R2,
                    RMSE_STD_RATIO, MAM, MAD, MAE_MAM_RATIO, MAE_MAD_RATIO, BIAS
                For classification: DATE, MODEL_NAME, EVAL_DATA_STD, LOGLOSS, ACCURACY,
                    PRECISION, RECALL, F1, ROC_AUC, AVG_PRECISION, THRESHOLDS,
                    PRECISION_AT_THRESHOLD, RECALL_AT_THRESHOLD, F1_AT_THRESHOLD
        """
        # Find the best model for this target
        best_model = self.experiment.get_best_model(target_number)

        if best_model is None:
            raise ValueError(f"No best model found for TARGET_{target_number}")

        # Determine if classification or regression
        is_classification = target_number in self.target_clf

        # Build DataFrame from models
        scores_data = []
        for m in best_model.models:
            if is_classification:
                score_row = {
                    "DATE": m.created_at,
                    "MODEL_NAME": m.model_type.name if m.model_type else None,
                    "EVAL_DATA_STD": m.eval_data_std,
                    "LOGLOSS": m.logloss,
                    "ACCURACY": m.accuracy,
                    "PRECISION": m.precision,
                    "RECALL": m.recall,
                    "F1": m.f1,
                    "ROC_AUC": m.roc_auc,
                    "AVG_PRECISION": m.avg_precision,
                    "THRESHOLDS": m.thresholds,
                    "PRECISION_AT_THRESHOLD": m.precision_at_threshold,
                    "RECALL_AT_THRESHOLD": m.recall_at_threshold,
                    "F1_AT_THRESHOLD": m.f1_at_threshold,
                }
            else:
                score_row = {
                    "DATE": m.created_at,
                    "MODEL_NAME": m.model_type.name if m.model_type else None,
                    "EVAL_DATA_STD": m.eval_data_std,
                    "RMSE": m.rmse,
                    "MAE": m.mae,
                    "MAPE": m.mape,
                    "R2": m.r2,
                    "RMSE_STD_RATIO": m.rmse_std_ratio,
                    "MAM": m.mam,
                    "MAD": m.mad,
                    "MAE_MAM_RATIO": m.mae_mam_ratio,
                    "MAE_MAD_RATIO": m.mae_mad_ratio,
                    "BIAS": m.bias,
                }
            scores_data.append(score_row)

        df = pd.DataFrame(scores_data)

        # Order by optimization metric
        from lecrapaud.utils import get_metric_direction

        metric = self.get_optimization_metric(target_number)
        direction = get_metric_direction(metric)
        ascending = direction == "minimize"

        if metric.upper() in df.columns:
            df = df.sort_values(by=metric.upper(), ascending=ascending)

        return df

    def get_threshold(self, target_number: int):
        """
        Get the best thresholds for a specific target from the database.

        Args:
            target_number (int): Target number to get thresholds for

        Returns:
            dict: Dictionary with threshold information for each class
        """
        # Find the best model for this target
        best_model = self.experiment.get_best_model(target_number)

        if best_model is None:
            raise ValueError(f"No best model found for TARGET_{target_number}")

        thresholds = best_model.thresholds

        if thresholds is None:
            raise ValueError(f"No thresholds found for TARGET_{target_number}")

        if isinstance(thresholds, str):
            thresholds = ast.literal_eval(thresholds)

        return thresholds

    def get_prediction(self, target_number: int, model_name: str | None = None):
        """Load predictions for a specific model.

        Args:
            target_number: Target number
            model_name: Name of the model

        Returns:
            DataFrame with predictions
        """
        if model_name is None:
            model_name = self.get_best_model_name(target_number)

        # Find best model for the target
        best_model = self.experiment.get_best_model(target_number)

        if best_model:
            # Find model record for the specific model
            model_record = next(
                (
                    m
                    for m in best_model.models
                    if m.model_type.name == model_name
                ),
                None,
            )

            if model_record:
                prediction = ArtifactService.load_dataframe(
                    experiment_id=self.experiment.id,
                    data_type="prediction",
                    model_id=model_record.id,
                )
                if prediction is not None:
                    return prediction

        raise ValueError(f"Prediction not found for TARGET_{target_number}/{model_name}")

    def get_feature_summary(self):
        summary = ArtifactService.load_dataframe(
            experiment_id=self.experiment.id,
            data_type="feature_summary",
        )
        if summary is not None:
            return summary
        raise FileNotFoundError("Feature summary not found")

    def load_model(self, target_number: int, model_name: str = None) -> LeCrapaudModel:
        """Load a model for a specific target.

        Args:
            target_number: Target number
            model_name: Name of the model to load. If None, loads the best model.

        Returns:
            LeCrapaudModel instance with the loaded model
        """
        target = self.experiment.get_target(target_number)
        if not target:
            raise ValueError(f"Target TARGET_{target_number} not found for experiment {self.experiment.id}")

        return LeCrapaudModel(
            experiment_id=self.experiment.id,
            target_id=target.id,
            target_number=target_number,
            model_name=model_name,
        )

    def get_optimization_metric(self, target_number: int) -> str:
        """
        Get the optimization metric for a specific target.

        Args:
            target_number (int): Target number

        Returns:
            str: Optimization metric (e.g., "LOGLOSS", "RMSE", "ROC_AUC")
        """
        from lecrapaud.utils import get_default_metric

        # Check if per-target metric is defined
        if isinstance(self.optimization_metric, dict) and target_number in self.optimization_metric:
            return self.optimization_metric[target_number]

        # Backward compatibility: if string, use for all targets
        if isinstance(self.optimization_metric, str):
            return self.optimization_metric

        # Auto: use default based on target type
        target_type = "classification" if target_number in self.target_clf else "regression"
        return get_default_metric(target_type)

    def get_best_model_name(self, target_number: int) -> str:
        """
        Get the best model name for a target.

        Args:
            target_number (int): Target number

        Returns:
            str: Best model name

        Raises:
            ValueError: If no best model found for the target
        """
        best_model = self.experiment.get_best_model(target_number)
        if best_model is None:
            raise ValueError(f"No best model found for TARGET_{target_number}")
        if best_model.model is None:
            raise ValueError(f"No best model record found for TARGET_{target_number}")
        return best_model.model.model_type.name

    def plot_feature_importance(
        self, target_number: int, model_name: str | None = None, top_n=30
    ):
        """
        Plot feature importance ranking.

        Args:
            target_number (int): Target variable number
            model_name (str): Name of the model to load (default: best model)
            top_n (int): Number of top features to display
        """
        if model_name is None:
            model_name = self.get_best_model_name(target_number)

        lecrapaud_model = self.load_model(target_number, model_name)
        model = lecrapaud_model._model
        experiment = self.experiment

        # Get feature names
        feature_names = experiment.get_features(target_number)

        # Get feature importances based on model type
        if hasattr(model, "feature_importances_"):
            # For sklearn tree models
            importances = model.feature_importances_
            importance_type = "Gini"
        elif hasattr(model, "get_score"):
            # For xgboost models
            importance_dict = model.get_score(importance_type="weight")
            importances = np.zeros(len(feature_names))
            for i, feat in enumerate(feature_names):
                if feat in importance_dict:
                    importances[i] = importance_dict[feat]
            importance_type = "Weight"
        elif hasattr(model, "feature_importance") and hasattr(model, "feature_name"):
            # For lightgbm models - align importances with feature_names
            lgb_importances = model.feature_importance(importance_type="split")
            lgb_features = model.feature_name()
            # Create dict mapping feature name -> importance
            importance_dict = dict(zip(lgb_features, lgb_importances))
            # Map to our feature_names order
            importances = np.array([importance_dict.get(f, 0) for f in feature_names])
            importance_type = "Split"
        elif hasattr(model, "get_feature_importance"):
            # For CatBoost models
            importances = model.get_feature_importance()
            importance_type = "Feature importance"
        elif hasattr(model, "coef_"):
            # For linear models
            importances = np.abs(model.coef_.flatten())
            importance_type = "Absolute coefficient"
        else:
            raise ValueError(
                f"Model {model_name} does not support feature importance calculation"
            )

        # Create a DataFrame for easier manipulation
        importance_df = pd.DataFrame(
            {"feature": feature_names[: len(importances)], "importance": importances}
        )

        # Sort features by importance and take top N
        importance_df = importance_df.sort_values("importance", ascending=False).head(
            top_n
        )

        # Create the plot
        plt.figure(figsize=(10, max(6, len(importance_df) * 0.3)))
        ax = sns.barplot(
            data=importance_df,
            x="importance",
            y="feature",
            palette="viridis",
            orient="h",
        )

        # Add value labels
        for i, v in enumerate(importance_df["importance"]):
            ax.text(v, i, f"{v:.4f}", color="black", ha="left", va="center")

        plt.title(f"Feature Importance ({importance_type})")
        plt.tight_layout()
        plt.show()

        return importance_df

    def print_model_estimators(self, target_number: int, model_name: str = None):
        """Print estimators info for ensemble models (e.g., RandomForest, BaggingClassifier).

        Args:
            target_number: Target number
            model_name: Name of the model (default: best model)
        """
        lecrapaud_model = self.load_model(target_number, model_name)
        model = lecrapaud_model._model

        if not hasattr(model, "estimators_"):
            raise ValueError(f"Model {model_name or lecrapaud_model.model_name} does not have estimators")

        for i in range(min(100, len(model.estimators_))):
            if hasattr(model.estimators_[i], "get_depth"):
                logger.info(f"Estimator {i}: depth={model.estimators_[i].get_depth()}")
            else:
                logger.info(f"Estimator {i}: {model.estimators_[i]}")

    def get_model_info(self, target_number: int, model_name: str = None):
        """Get model info (for Keras models: count_params and summary).

        Args:
            target_number: Target number
            model_name: Name of the model (default: best model)
        """
        lecrapaud_model = self.load_model(target_number, model_name)
        model = lecrapaud_model._model

        if hasattr(model, "count_params") and hasattr(model, "summary"):
            model.count_params()
            model.summary()
        else:
            logger.info(f"Model: {model}")
            if hasattr(model, "get_params"):
                logger.info(f"Params: {model.get_params()}")

    def plot_evaluation_for_classification(
        self, target_number: int, model_name: str = None
    ):
        prediction = self.get_prediction(target_number, model_name)
        thresholds = self.get_threshold(target_number)

        plot_evaluation_for_classification(prediction)

        for class_label, metrics in thresholds.items():
            threshold = metrics["threshold"]
            precision = metrics["precision"]
            recall = metrics["recall"]
            if threshold is not None:
                tmp_pred = prediction[["TARGET", "PRED", class_label]].copy()
                tmp_pred.rename(columns={class_label: 1}, inplace=True)
                print(f"Class {class_label}:")
                plot_threshold(tmp_pred, threshold, precision, recall)
            else:
                print(f"No threshold found for class {class_label}")

    def plot_evaluation_for_regression(
        self, target_number: int, model_name: str = None
    ):
        """
        Plot evaluation metrics for regression tasks.

        Displays:
        1. Actual vs Predicted scatter plot
        2. Residuals vs Predicted (heteroscedasticity check)
        3. Residuals histogram (normality check)
        4. QQ plot (normality check)

        Args:
            target_number (int): Target number
            model_name (str): Model name to evaluate (default: best model)
        """
        prediction = self.get_prediction(target_number, model_name)
        plot_evaluation_for_regression(prediction)

    def get_best_params(self, target_number: int) -> dict | None:
        """
        Get the best model parameters for a specific target.

        Args:
            target_number (int): The target number to get best params for.

        Returns:
            dict | None: The best model parameters for the target, or None if not found.
        """
        return self.experiment.get_best_params(target_number)

    def get_all_target_best_params(self) -> dict:
        """
        Get the best model parameters for all targets.

        Returns:
            dict: A dictionary with target numbers as keys and their best parameters as values.
        """
        return self.experiment.get_all_best_params()

    def plot_pca_scatter(
        self,
        target_number: int,
        pca_type: str = "all",
        components: tuple = (0, 1),
        figsize: tuple = (12, 5),
    ):
        """
        Visualise les données dans l'espace PCA en 2D avec coloration par classe.
        Fonctionne uniquement pour les tâches de classification.

        Args:
            target_number (int): Numéro de la target à visualiser
            pca_type (str): Type de PCA à visualiser ("embedding", "cross_sectional", "temporal", "all")
            components (tuple): Tuple des composantes à afficher (par défaut (0,1))
            figsize (tuple): Taille de la figure
        """
        # Vérifier que c'est une tâche de classification
        if target_number not in self.target_clf:
            raise ValueError(
                f"Target {target_number} n'est pas une tâche de classification. "
                f"Targets de classification disponibles: {self.target_clf}"
            )

        # Charger les données PCA pour visualisation
        data = ArtifactService.load_dataframe(
            experiment_id=self.experiment.id,
            data_type="pca_visualization",
        )
        if data is None:
            # Fallback to full for backward compatibility
            data = ArtifactService.load_dataframe(
                experiment_id=self.experiment.id,
                data_type="full",
            )
        if data is None:
            raise FileNotFoundError(
                f"Données PCA non trouvées pour l'expérience {self.experiment.id}. Exécutez d'abord fit()."
            )
        target_col = f"TARGET_{target_number}"

        if target_col not in data.columns:
            raise ValueError(f"Target {target_number} non trouvée dans les données.")

        # Identifier les colonnes PCA selon le type
        pca_cols = {}
        if pca_type in ["embedding", "all"]:
            pca_cols["embedding"] = [col for col in data.columns if "_pca_" in col]
        if pca_type in ["cross_sectional", "all"]:
            pca_cols["cross_sectional"] = [
                col for col in data.columns if col.startswith("CS_PC_")
            ]
        if pca_type in ["temporal", "all"]:
            pca_cols["temporal"] = [
                col for col in data.columns if col.startswith("TMP_PC_")
            ]

        # Vérifier qu'on a des colonnes PCA
        total_cols = sum(len(cols) for cols in pca_cols.values())
        if total_cols == 0:
            raise ValueError(f"Aucune colonne PCA trouvée pour le type '{pca_type}'")

        # Grouper par type de PCA et créer des groupes logiques
        pca_groups = {}
        for type_name, cols in pca_cols.items():
            if not cols:
                continue

            if type_name == "embedding":
                # Grouper par base_column
                groups = {}
                for col in cols:
                    base_col = col.replace("_pca_", "_").split("_")[0]
                    if base_col not in groups:
                        groups[base_col] = []
                    groups[base_col].append(col)
                pca_groups.update({f"{type_name}_{k}": v for k, v in groups.items()})

            elif type_name in ["cross_sectional", "temporal"]:
                # Grouper par nom PCA (entre les underscores)
                groups = {}
                prefix = "CS_PC_" if type_name == "cross_sectional" else "TMP_PC_"
                for col in cols:
                    parts = col.replace(prefix, "").split("_")
                    if len(parts) >= 2:
                        name = "_".join(
                            parts[:-1]
                        )  # Tout sauf le dernier (numéro composante)
                        if name not in groups:
                            groups[name] = []
                        groups[name].append(col)
                pca_groups.update({f"{type_name}_{k}": v for k, v in groups.items()})

        # Créer les subplots en colonnes pour meilleure lisibilité
        n_groups = len(pca_groups)
        if n_groups == 0:
            raise ValueError("Aucun groupe PCA trouvé")

        # Organiser en colonnes (1 plot par ligne, 1 colonne)
        n_rows = n_groups
        n_cols = 1

        fig, axes = plt.subplots(
            n_rows, n_cols, figsize=(figsize[0], figsize[1] * n_groups)
        )
        if n_groups == 1:
            axes = [axes]
        else:
            axes = axes.flatten() if n_groups > 1 else [axes]

        # Préparer les données (retirer les NaN)
        data_clean = data.dropna(subset=[target_col])
        y = data_clean[target_col].astype(int)

        # Créer une palette de couleurs flashy et visibles
        class_labels = sorted(y.unique())
        n_classes = len(class_labels)

        # Couleurs flashy : bleu, rouge, vert, orange, violet, cyan, magenta
        flashy_colors = [
            "#1f77b4",  # Bleu vif pour classe 0
            "#ff4444",  # Rouge vif pour classe 1
            "#2ca02c",  # Vert vif pour classe 2
            "#ff7f0e",  # Orange vif pour classe 3
            "#9467bd",  # Violet pour classe 4
            "#17becf",  # Cyan pour classe 5
            "#e377c2",  # Magenta pour classe 6
            "#bcbd22",  # Olive pour classe 7
        ]

        # Mapper chaque classe à sa couleur
        color_map = {}
        for i, class_label in enumerate(class_labels):
            color_map[class_label] = flashy_colors[i % len(flashy_colors)]

        for idx, (group_name, group_cols) in enumerate(pca_groups.items()):
            ax = axes[idx]

            # Vérifier qu'on a au moins les composantes demandées
            if len(group_cols) < max(components) + 1:
                ax.text(
                    0.5,
                    0.5,
                    f"Pas assez de composantes\ndans {group_name}",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                )
                ax.set_title(group_name)
                continue

            # Sélectionner les composantes
            group_cols_sorted = sorted(group_cols)
            pc1_col = group_cols_sorted[components[0]]
            pc2_col = group_cols_sorted[components[1]]

            # Données pour ce groupe (retirer NaN)
            subset = data_clean[[pc1_col, pc2_col, target_col]].dropna()
            if len(subset) == 0:
                ax.text(
                    0.5,
                    0.5,
                    f"Pas de données valides\npour {group_name}",
                    ha="center",
                    va="center",
                    transform=ax.transAxes,
                )
                ax.set_title(group_name)
                continue

            X_pc1 = subset[pc1_col]
            X_pc2 = subset[pc2_col]
            y_subset = subset[target_col].astype(int)

            # Scatter plot par classe avec couleurs flashy
            for class_label in sorted(y_subset.unique()):
                mask = y_subset == class_label
                ax.scatter(
                    X_pc1[mask],
                    X_pc2[mask],
                    c=color_map[class_label],
                    label=f"Classe {class_label}",
                    alpha=0.7,
                    s=50,
                    edgecolors="white",
                    linewidth=0.5,
                )

            ax.set_xlabel(f"PC{components[0]+1}")
            ax.set_ylabel(f"PC{components[1]+1}")
            ax.set_title(f'{group_name.replace("_", " ").title()}')
            ax.legend()
            ax.grid(True, alpha=0.3)

        # Plus besoin de cacher des axes car chaque plot a son propre axe

        plt.tight_layout()
        plt.suptitle(
            f"Visualisation PCA 2D - Target {target_number}", y=1.02, fontsize=14
        )
        plt.show()

    def plot_pca_variance(self, pca_type: str = "all", figsize: tuple = (15, 5)):
        """
        Visualise la variance expliquée par les composantes PCA.
        Fonctionne pour classification et régression.

        Args:
            pca_type (str): Type de PCA à visualiser ("embedding", "cross_sectional", "temporal", "all")
            figsize (tuple): Taille de la figure
        """
        # Charger les objets PCA sauvegardés from database
        pca_objects = {}

        # PCA Embedding
        if pca_type in ["embedding", "all"]:
            try:
                pcas_embedding = ArtifactService.load_artifact(
                    experiment_id=self.experiment.id,
                    artifact_type="pca",
                    artifact_name="pcas",
                )
                if pcas_embedding:
                    pca_objects["embedding"] = pcas_embedding
            except Exception:
                logger.warning("Impossible de charger les PCA embedding")

        # PCA Cross-sectional
        if pca_type in ["cross_sectional", "all"]:
            try:
                pcas_cs = ArtifactService.load_artifact(
                    experiment_id=self.experiment.id,
                    artifact_type="pca",
                    artifact_name="pcas_cross_sectional",
                )
                if pcas_cs:
                    pca_objects["cross_sectional"] = pcas_cs
            except Exception:
                logger.warning("Impossible de charger les PCA cross-sectional")

        # PCA Temporal
        if pca_type in ["temporal", "all"]:
            try:
                pcas_temporal = ArtifactService.load_artifact(
                    experiment_id=self.experiment.id,
                    artifact_type="pca",
                    artifact_name="pcas_temporal",
                )
                if pcas_temporal:
                    pca_objects["temporal"] = pcas_temporal
            except Exception:
                logger.warning("Impossible de charger les PCA temporal")

        if not pca_objects:
            raise ValueError(
                f"Aucun objet PCA trouvé pour le type '{pca_type}'. "
                "Assurez-vous d'avoir exécuté fit() avec des configurations PCA."
            )

        # Collecter toutes les variances expliquées
        variance_data = []

        for type_name, pca_dict in pca_objects.items():
            for name, pca_obj in pca_dict.items():

                # Récupérer l'objet PCA selon le type
                if type_name == "embedding":
                    # Pour embedding, l'objet est directement une PCA
                    explained_var = pca_obj.explained_variance_ratio_
                    pca_name = f"{type_name}_{name}"
                else:
                    # Pour cross_sectional et temporal, c'est un Pipeline
                    try:
                        if (
                            hasattr(pca_obj, "named_steps")
                            and "pca" in pca_obj.named_steps
                        ):
                            explained_var = pca_obj.named_steps[
                                "pca"
                            ].explained_variance_ratio_
                        else:
                            continue
                        pca_name = f"{type_name}_{name}"
                    except:
                        continue

                # Ajouter les données
                for i, var in enumerate(explained_var):
                    variance_data.append(
                        {
                            "pca_type": type_name,
                            "pca_name": pca_name,
                            "component": i + 1,
                            "explained_variance": var,
                            "cumulative_variance": np.sum(explained_var[: i + 1]),
                        }
                    )

        if not variance_data:
            raise ValueError("Aucune donnée de variance trouvée dans les objets PCA")

        df_var = pd.DataFrame(variance_data)

        # Créer les subplots en colonnes verticales pour meilleure lisibilité
        unique_pcas = df_var["pca_name"].unique()
        n_pcas = len(unique_pcas)

        if n_pcas == 0:
            raise ValueError("Aucune PCA trouvée")

        # Organiser en colonnes (1 plot par ligne, 1 colonne)
        n_rows = n_pcas
        n_cols = 1

        fig, axes = plt.subplots(
            n_rows, n_cols, figsize=(figsize[0], figsize[1] * n_pcas)
        )
        if n_pcas == 1:
            axes = [axes]
        else:
            axes = axes.flatten() if n_pcas > 1 else [axes]

        colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

        for idx, pca_name in enumerate(unique_pcas):
            ax = axes[idx]
            pca_data = df_var[df_var["pca_name"] == pca_name].sort_values("component")

            # Bar plot pour variance individuelle
            bars = ax.bar(
                pca_data["component"],
                pca_data["explained_variance"],
                alpha=0.7,
                color=colors[idx % len(colors)],
                label="Variance individuelle",
            )

            # Line plot pour variance cumulative
            ax2 = ax.twinx()
            line = ax2.plot(
                pca_data["component"],
                pca_data["cumulative_variance"],
                "ro-",
                linewidth=2,
                markersize=4,
                label="Variance cumulative",
            )

            # Annotations
            for i, (comp, var, cum_var) in enumerate(
                zip(
                    pca_data["component"],
                    pca_data["explained_variance"],
                    pca_data["cumulative_variance"],
                )
            ):
                if var > 0.05:  # Seulement si > 5%
                    ax.text(
                        comp,
                        var + 0.01,
                        f"{var:.3f}",
                        ha="center",
                        va="bottom",
                        fontsize=8,
                    )
                if i < 5:  # Seulement les 5 premiers pour la lisibilité
                    ax2.text(
                        comp + 0.1,
                        cum_var,
                        f"{cum_var:.3f}",
                        ha="left",
                        va="center",
                        fontsize=8,
                        color="red",
                    )

            # Styling
            ax.set_xlabel("Composante PCA")
            ax.set_ylabel("Variance expliquée", color="blue")
            ax2.set_ylabel("Variance cumulative", color="red")
            ax.set_title(pca_name.replace("_", " ").title())
            ax.grid(True, alpha=0.3)
            ax.set_ylim(0, max(pca_data["explained_variance"]) * 1.1)
            ax2.set_ylim(0, 1.05)

            # Légende
            lines1, labels1 = ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax.legend(lines1 + lines2, labels1 + labels2, loc="upper right")

        # Plus besoin de cacher des axes car chaque plot a son propre axe

        plt.tight_layout()
        plt.suptitle(f"Variance expliquée par les composantes PCA", y=1.02, fontsize=14)
        plt.show()

        # Retourner un summary
        summary = (
            df_var.groupby("pca_name")
            .agg({"explained_variance": ["sum", "max"], "component": "count"})
            .round(4)
        )
        summary.columns = [
            "variance_totale",
            "variance_max_composante",
            "nb_composantes",
        ]

        return summary

    def _get_lime_explainer(self, target_number: int):
        """
        Helper method to create LIME explainer and load required data.

        Args:
            target_number (int): Target number

        Returns:
            tuple: (explainer, predict_fn, X_train, model, features)
        """
        # Charger le modèle depuis la base de données
        model = self.load_model(target_number)

        # Charger les features
        features = self.experiment.get_features(target_number)

        # Charger les données preprocessées from database
        data_type = "train_scaled" if model.need_scaling else "train"
        X_train_df = ArtifactService.load_dataframe(
            experiment_id=self.experiment.id,
            data_type=data_type,
        )
        if X_train_df is None:
            raise FileNotFoundError(
                f"Training data not found for experiment {self.experiment.id}"
            )
        X_train = X_train_df[features]

        # Préparer la fonction de prédiction
        if model.target_type == "classification":
            predict_fn = lambda x: model._model.predict_proba(
                pd.DataFrame(x, columns=features)
            )
            class_names = ["0", "1"]  # Assume binary classification
            mode = "classification"
        else:
            predict_fn = lambda x: model._model.predict(
                pd.DataFrame(x, columns=features)
            ).values.ravel()
            class_names = None
            mode = "regression"

        # Créer l'explainer LIME
        explainer = lime.lime_tabular.LimeTabularExplainer(
            X_train.values,
            feature_names=features,
            class_names=class_names,
            mode=mode,
            discretize_continuous=True,
        )

        return explainer, predict_fn, X_train, model, features

    def plot_lime_explanation(
        self,
        target_number: int,
        instance_idx: int = 0,
        n_features: int = 10,
        figsize: tuple = (10, 6),
    ):
        """
        Visualise l'explication LIME pour une instance donnée du test set.

        Args:
            target_number (int): Numéro de la target à expliquer
            instance_idx (int): Index de l'instance à expliquer dans X_test (défaut: 0)
            n_features (int): Nombre de features à afficher
            figsize (tuple): Taille de la figure
        """
        explainer, predict_fn, X_train, model, features = self._get_lime_explainer(target_number)

        # Charger X_test pour expliquer des instances non vues from database
        test_data_type = "test_scaled" if model.need_scaling else "test"
        X_test_df = ArtifactService.load_dataframe(
            experiment_id=self.experiment.id,
            data_type=test_data_type,
        )
        if X_test_df is None:
            raise FileNotFoundError(
                f"Test data not found for experiment {self.experiment.id}"
            )
        X_test = X_test_df[features]

        if instance_idx >= len(X_test):
            raise ValueError(
                f"Instance {instance_idx} non trouvée. Max: {len(X_test)-1}"
            )

        # Expliquer l'instance
        instance = X_test.iloc[instance_idx].values
        explanation = explainer.explain_instance(
            instance, predict_fn, num_features=n_features
        )

        # Affichage personnalisé
        fig, ax = plt.subplots(figsize=figsize)

        # Récupérer les données d'explication
        exp_list = explanation.as_list()

        # Séparer features et importances
        feature_names = [item[0] for item in exp_list]
        importances = [item[1] for item in exp_list]

        # Créer le graphique horizontal
        colors = ["red" if x < 0 else "green" for x in importances]
        y_pos = np.arange(len(feature_names))

        bars = ax.barh(y_pos, importances, color=colors, alpha=0.7)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(feature_names)
        ax.set_xlabel("Contribution LIME")

        # Ajouter les valeurs sur les barres
        for i, (bar, importance) in enumerate(zip(bars, importances)):
            width = bar.get_width()
            ax.text(
                width + (0.01 if width >= 0 else -0.01),
                bar.get_y() + bar.get_height() / 2,
                f"{importance:.3f}",
                ha="left" if width >= 0 else "right",
                va="center",
                fontsize=9,
            )

        # Titre et grille
        prediction = predict_fn(instance.reshape(1, -1))
        if model.target_type == "classification":
            pred_text = f"Proba classe 1: {prediction[0][1]:.3f}"
        else:
            pred_text = f"Prédiction: {prediction[0]:.3f}"

        ax.set_title(
            f"Explication LIME - Target {target_number} - Instance {instance_idx}\n{pred_text}"
        )
        ax.grid(True, alpha=0.3, axis="x")
        ax.axvline(x=0, color="black", linestyle="-", linewidth=0.5)

        plt.show()

        return explanation

    def plot_lime_summary(
        self,
        target_number: int,
        n_features: int = 10,
        sample_size: int = 100,
        num_exps_desired: int = 5,
        figsize: tuple = (12, 8),
    ):
        """
        Visualise un résumé global des explications LIME via SP-LIME (Submodular Pick).

        SP-LIME sélectionne un ensemble représentatif d'instances qui ensemble
        couvrent les features les plus importantes du modèle.

        Args:
            target_number (int): Numéro de la target à expliquer
            n_features (int): Nombre de features par explication (défaut: 10)
            sample_size (int): Nombre d'instances à considérer (défaut: 100)
            num_exps_desired (int): Nombre d'explications représentatives à sélectionner (défaut: 5)
            figsize (tuple): Taille de la figure

        Returns:
            tuple: (sp_obj, summary_df) - L'objet SubmodularPick et le DataFrame des importances
        """
        from lime.submodular_pick import SubmodularPick

        explainer, predict_fn, X_train, model, features = self._get_lime_explainer(target_number)

        # Échantillonner depuis X_train
        sample_size = min(sample_size, len(X_train))
        X_sample = X_train.sample(n=sample_size, random_state=42)

        logger.info(f"SP-LIME: sélection de {num_exps_desired} explications représentatives parmi {sample_size} instances...")

        # Utiliser SubmodularPick pour sélectionner les explications représentatives
        sp_obj = SubmodularPick(
            explainer,
            X_sample.values,
            predict_fn,
            num_features=n_features,
            num_exps_desired=num_exps_desired,
        )

        # Collecter les importances globales depuis les explications sélectionnées
        feature_importances = {feat: [] for feat in features}

        for exp in sp_obj.sp_explanations:
            for feat_desc, importance in exp.as_list():
                for feat in features:
                    if feat in feat_desc:
                        feature_importances[feat].append(abs(importance))
                        break

        # Calculer les statistiques
        summary_data = []
        for feat in features:
            if feature_importances[feat]:
                summary_data.append({
                    "feature": feat,
                    "mean_importance": np.mean(feature_importances[feat]),
                    "std_importance": np.std(feature_importances[feat]),
                    "count": len(feature_importances[feat]),
                })

        summary_df = pd.DataFrame(summary_data)
        summary_df = summary_df.sort_values("mean_importance", ascending=False)

        # Plot 1: Bar plot des importances globales
        fig, axes = plt.subplots(1, 2, figsize=figsize)

        # Gauche: Importance moyenne des features
        ax1 = axes[0]
        top_features = summary_df.head(n_features)
        y_pos = np.arange(len(top_features))
        ax1.barh(
            y_pos,
            top_features["mean_importance"],
            xerr=top_features["std_importance"],
            color="steelblue",
            alpha=0.7,
            capsize=3,
        )
        ax1.set_yticks(y_pos)
        ax1.set_yticklabels(top_features["feature"])
        ax1.invert_yaxis()
        ax1.set_xlabel("Importance moyenne")
        ax1.set_title(f"Feature Importance (SP-LIME)")
        ax1.grid(True, alpha=0.3, axis="x")

        # Droite: Matrice de couverture des features par les explications
        ax2 = axes[1]
        coverage_matrix = []
        for i, exp in enumerate(sp_obj.sp_explanations):
            row = {feat: 0 for feat in top_features["feature"]}
            for feat_desc, importance in exp.as_list():
                for feat in top_features["feature"]:
                    if feat in feat_desc:
                        row[feat] = importance
                        break
            coverage_matrix.append(row)

        coverage_df = pd.DataFrame(coverage_matrix)
        if not coverage_df.empty:
            sns.heatmap(
                coverage_df.T,
                ax=ax2,
                cmap="RdBu_r",
                center=0,
                xticklabels=[f"Exp {i+1}" for i in range(len(sp_obj.sp_explanations))],
                yticklabels=True,
            )
            ax2.set_title(f"Contributions par explication")
            ax2.set_xlabel("Explications représentatives")

        plt.suptitle(
            f"SP-LIME Summary - Target {target_number} ({model.target_type})",
            fontsize=12,
        )
        plt.tight_layout()
        plt.show()

        return sp_obj, summary_df

    def _get_shap_explainer(self, target_number: int):
        """
        Helper method to create SHAP explainer and load required data.

        Args:
            target_number (int): Target number

        Returns:
            tuple: (explainer, X_train, model, actual_model)
        """
        # Charger le modèle depuis la base de données
        model = self.load_model(target_number)

        # Charger les features
        features = self.experiment.get_features(target_number)

        # Charger les données preprocessées from database
        data_type = "train_scaled" if model.need_scaling else "train"
        X_train_df = ArtifactService.load_dataframe(
            experiment_id=self.experiment.id,
            data_type=data_type,
        )
        if X_train_df is None:
            raise FileNotFoundError(
                f"Training data not found for experiment {self.experiment.id}"
            )
        X_train = X_train_df[features].astype(float)

        # Créer l'explainer SHAP directement sur le modèle
        actual_model = model._model

        explainer = shap.Explainer(actual_model, X_train)

        return explainer, X_train, model, actual_model

    def get_shap_values(
        self,
        target_number: int,
        X_sample: pd.DataFrame = None,
        sample_size: int = 1000,
    ):
        """
        Calculate SHAP values for a target.

        Args:
            target_number (int): Target number
            X_sample (pd.DataFrame, optional): Data to explain. If None, samples from X_train.
            sample_size (int): Number of samples if X_sample is None (default: 1000)

        Returns:
            tuple: (shap_values, X_sample, explainer, model)
        """
        explainer, X_train, model, actual_model = self._get_shap_explainer(target_number)

        # Use provided sample or sample from X_train
        if X_sample is None:
            sample_size = min(sample_size, len(X_train))
            X_sample = X_train.sample(n=sample_size, random_state=42)
        else:
            X_sample = X_sample.astype(float)

        # Calculer les valeurs SHAP
        logger.info(f"Calcul des valeurs SHAP pour {len(X_sample)} instances...")
        shap_values = explainer.shap_values(X_sample)

        return shap_values, X_sample, explainer, model

    def plot_shap_values(
        self,
        target_number: int,
        plot_type: Literal["bar", "dot", "violin", "beeswarm"] = "dot",
        max_display: int = 20,
        figsize: tuple = (10, 8),
        sample_size: int = 1000,
    ):
        """
        Visualise les valeurs SHAP (summary plot).

        Args:
            target_number (int): Numéro de la target à expliquer
            plot_type (Literal["bar", "dot", "violin", "beeswarm"]): Type de plot
                - "bar": Graphique en barres montrant l'importance moyenne absolue de chaque feature.
                         Idéal pour un aperçu rapide de l'importance globale des features.
                - "dot": (défaut) Nuage de points où chaque point est une instance.
                         La position X montre l'impact SHAP, la couleur indique la valeur de la feature.
                         Permet de voir comment les valeurs des features influencent les prédictions.
                - "violin": Similaire à "dot" mais avec des violons pour montrer la distribution.
                         Utile pour voir la densité des valeurs SHAP à différents niveaux.
                - "beeswarm": Comme "dot" mais les points sont arrangés pour éviter le chevauchement.
                              Meilleure visibilité quand beaucoup d'instances ont des valeurs similaires.
            max_display (int): Nombre maximum de features à afficher
            figsize (tuple): Taille de la figure
            sample_size (int): Nombre d'instances à utiliser pour le calcul SHAP (default: 1000)

        Returns:
            numpy.ndarray: Les valeurs SHAP calculées

        Examples:
            # Importance globale des features
            experiment.plot_shap_values(target_number=1, plot_type="bar")

            # Voir l'impact détaillé avec les valeurs des features
            experiment.plot_shap_values(target_number=1, plot_type="dot")

            # Distribution des impacts SHAP
            experiment.plot_shap_values(target_number=1, plot_type="violin")
        """
        shap_values, X_sample, explainer, model = self.get_shap_values(
            target_number, sample_size=sample_size
        )

        # Summary plot
        plt.figure(figsize=figsize)

        # Plot SHAP summary - adaptable aux différents types de modèles
        if model.target_type == "classification":
            # Pour classification binaire, utiliser les valeurs de la classe positive
            if isinstance(shap_values, list) and len(shap_values) > 1:
                # Classification binaire: classe 1 (positive)
                shap.summary_plot(
                    shap_values[1],
                    X_sample,
                    max_display=max_display,
                    show=False,
                    plot_type=plot_type,
                )
            else:
                # Classification avec une seule sortie ou multiclass
                values_to_plot = (
                    shap_values[0] if isinstance(shap_values, list) else shap_values
                )
                shap.summary_plot(
                    values_to_plot,
                    X_sample,
                    max_display=max_display,
                    show=False,
                    plot_type=plot_type,
                )
        else:
            # Régression
            values_to_plot = (
                shap_values[0] if isinstance(shap_values, list) else shap_values
            )
            shap.summary_plot(
                values_to_plot,
                X_sample,
                max_display=max_display,
                show=False,
                plot_type=plot_type,
            )

        plt.title(f"Valeurs SHAP - Target {target_number} ({model.target_type})")
        plt.show()

        return shap_values

    def plot_shap_waterfall(
        self,
        target_number: int,
        instance_idx: int = 0,
        max_display: int = 20,
        figsize: tuple = (10, 8),
    ):
        """
        Visualise l'explication SHAP waterfall pour une instance donnée du test set.

        Args:
            target_number (int): Numéro de la target à expliquer
            instance_idx (int): Index de l'instance à expliquer dans X_test
            max_display (int): Nombre maximum de features à afficher
            figsize (tuple): Taille de la figure
        """
        explainer, X_train, model, actual_model = self._get_shap_explainer(target_number)

        # Charger X_test pour expliquer des instances non vues from database
        features = self.experiment.get_features(target_number)
        test_data_type = "test_scaled" if model.need_scaling else "test"
        X_test_df = ArtifactService.load_dataframe(
            experiment_id=self.experiment.id,
            data_type=test_data_type,
        )
        if X_test_df is None:
            raise FileNotFoundError(
                f"Test data not found for experiment {self.experiment.id}"
            )
        X_test = X_test_df[features].astype(float)

        if instance_idx >= len(X_test):
            raise ValueError(
                f"Instance {instance_idx} non trouvée. Max: {len(X_test)-1}"
            )

        # Préparer les données de l'instance
        instance_data = X_test.iloc[instance_idx : instance_idx + 1]

        # Calculer les valeurs SHAP pour l'instance
        logger.info(f"Calcul des valeurs SHAP pour l'instance {instance_idx}...")
        shap_values = explainer.shap_values(instance_data)

        # Waterfall plot
        plt.figure(figsize=figsize)

        # Créer l'objet Explanation pour le waterfall plot
        if model.target_type == "classification":
            # Pour classification binaire, prendre les valeurs de la classe 1
            if isinstance(shap_values, list) and len(shap_values) > 1:
                values = shap_values[1][0]  # Classe 1, première instance
                base_value = explainer.expected_value[1]
            else:
                # Cas où shap_values n'est pas une liste ou une seule classe
                values = (
                    shap_values[0] if isinstance(shap_values, list) else shap_values[0]
                )
                base_value = (
                    explainer.expected_value[0]
                    if isinstance(explainer.expected_value, list)
                    else explainer.expected_value
                )
        else:
            # Pour régression
            values = shap_values[0] if isinstance(shap_values, list) else shap_values[0]
            base_value = (
                explainer.expected_value[0]
                if isinstance(explainer.expected_value, list)
                else explainer.expected_value
            )

        # Créer l'objet Explanation
        explanation = shap.Explanation(
            values=values, base_values=base_value, data=instance_data.iloc[0]
        )

        # Plot waterfall
        shap.waterfall_plot(explanation, max_display=max_display, show=False)

        # Ajouter des informations sur la prédiction
        if model.target_type == "classification":
            prediction = actual_model.predict_proba(instance_data)
            pred_text = f"Proba classe 1: {prediction[0][1]:.3f}"
        else:
            prediction = actual_model.predict(instance_data)
            pred_value = prediction[0] if hasattr(prediction, "__len__") else prediction
            pred_text = f"Prédiction: {pred_value:.3f}"

        plt.title(
            f"SHAP Waterfall - Target {target_number} - Instance {instance_idx}\n{pred_text}"
        )
        plt.show()

        return shap_values

    def plot_tree(
        self,
        target_number: int,
        tree_index: int = 0,
        max_depth: int = None,
        figsize: tuple = (20, 10),
        **kwargs,
    ):
        """
        Visualise un arbre de décision du modèle.

        Args:
            target_number (int): Numéro de la target
            tree_index (int): Index de l'arbre à visualiser (défaut: 0)
            max_depth (int): Profondeur maximale à afficher (défaut: None = tout)
            figsize (tuple): Taille de la figure
            **kwargs: Arguments supplémentaires selon le type de modèle
                - Pour sklearn: filled, rounded, proportion, precision, class_names, etc.
                - Pour XGBoost: rankdir, num_trees, yes_color, no_color
                - Pour LightGBM: show_info, precision, orientation
                - Pour CatBoost: pool (requis pour CatBoost)

        Examples:
            # Arbre sklearn avec couleurs
            experiment.plot_tree(target_number=1, filled=True, rounded=True)

            # Premier arbre XGBoost
            experiment.plot_tree(target_number=1, tree_index=0)

            # Arbre LightGBM horizontal
            experiment.plot_tree(target_number=1, orientation='horizontal')

            # CatBoost nécessite les données
            experiment.plot_tree(target_number=1, pool=Pool(X, y))
        """
        # Charger le modèle depuis la base de données
        model = self.load_model(target_number)

        # Charger les features
        features = self.experiment.get_features(target_number)

        # Extraire le modèle réel
        actual_model = model._model

        # Identifier le type de modèle
        model_type = actual_model.__class__.__name__

        plt.figure(figsize=figsize)

        # Visualisation selon le type de modèle
        if (
            "DecisionTree" in model_type
            or "RandomForest" in model_type
            or "ExtraTrees" in model_type
        ):
            # Scikit-learn trees
            from sklearn.tree import plot_tree

            # Pour les ensembles, prendre un estimateur
            if hasattr(actual_model, "estimators_"):
                tree_to_plot = actual_model.estimators_[tree_index]
                if hasattr(tree_to_plot, "tree_"):  # RandomForest avec sklearn trees
                    tree_to_plot = tree_to_plot
                else:  # Peut être un autre type d'estimateur
                    tree_to_plot = tree_to_plot
            else:
                tree_to_plot = actual_model

            # Paramètres par défaut pour sklearn
            default_kwargs = {
                "feature_names": features,
                "filled": True,
                "rounded": True,
                "proportion": False,
                "precision": 2,
                "fontsize": 10,
            }

            # Pour classification, ajouter les noms de classes
            if model.target_type == "classification":
                if "class_names" not in kwargs:
                    # Essayer de récupérer les classes
                    if hasattr(actual_model, "classes_"):
                        default_kwargs["class_names"] = [
                            str(c) for c in actual_model.classes_
                        ]
                    else:
                        default_kwargs["class_names"] = ["0", "1"]  # Défaut binaire

            # Fusionner avec les kwargs utilisateur
            plot_kwargs = {**default_kwargs, **kwargs}

            # Limiter la profondeur si demandé
            if max_depth is not None:
                plot_kwargs["max_depth"] = max_depth

            plot_tree(tree_to_plot, **plot_kwargs)
            plt.title(f"Arbre {tree_index} - {model.model_name.upper()}")

        elif "XGB" in model_type or "xgboost" in model_type.lower():
            # XGBoost trees
            try:
                import xgboost as xgb

                # Paramètres par défaut
                default_kwargs = {
                    "rankdir": "TB",  # Top to bottom
                    "num_trees": tree_index,
                }

                plot_kwargs = {**default_kwargs, **kwargs}

                # XGBoost utilise graphviz, donc on doit gérer différemment
                ax = plt.gca()
                xgb.plot_tree(actual_model, ax=ax, **plot_kwargs)
                plt.title(f"Arbre {tree_index} - XGBoost")

            except ImportError:
                raise ImportError(
                    "XGBoost n'est pas installé ou graphviz manquant. "
                    "Installez avec: pip install xgboost et installez graphviz"
                )

        elif "LGBM" in model_type or "lightgbm" in model_type.lower():
            # LightGBM trees
            try:
                import lightgbm as lgb

                # Paramètres par défaut
                default_kwargs = {
                    "tree_index": tree_index,
                    "show_info": ["split_gain", "leaf_count", "internal_value"],
                    "precision": 3,
                    "orientation": "vertical",
                }

                plot_kwargs = {**default_kwargs, **kwargs}

                # Retirer tree_index des kwargs car il est passé séparément
                plot_kwargs.pop("tree_index", None)

                ax = lgb.plot_tree(
                    actual_model, tree_index=tree_index, figsize=figsize, **plot_kwargs
                )
                plt.title(f"Arbre {tree_index} - LightGBM")

            except ImportError:
                raise ImportError(
                    "LightGBM n'est pas installé ou graphviz manquant. "
                    "Installez avec: pip install lightgbm et installez graphviz"
                )

        elif "CatBoost" in model_type:
            # CatBoost trees
            try:
                # CatBoost nécessite plus de configuration
                if "pool" not in kwargs:
                    # Essayer de charger les données pour créer un Pool
                    logger.warning(
                        "CatBoost nécessite un Pool object. "
                        "Passez pool=Pool(X, y) dans les kwargs."
                    )

                    # Tentative de création automatique du pool from database
                    X_train_df = ArtifactService.load_dataframe(
                        experiment_id=self.experiment.id,
                        data_type="train",
                    )
                    if X_train_df is not None:
                        X_train = X_train_df[features]
                        from catboost import Pool

                        pool = Pool(X_train)
                    else:
                        raise ValueError(
                            "Impossible de créer automatiquement le Pool CatBoost. "
                            "Passez pool=Pool(X, y) dans les arguments."
                        )
                else:
                    pool = kwargs.pop("pool")

                # CatBoost plot_tree retourne un objet graphviz.Digraph
                tree_plot = actual_model.plot_tree(tree_idx=tree_index, pool=pool)

                # Afficher l'image dans matplotlib
                import io
                from PIL import Image as PILImage

                # Convertir le Digraph en bytes PNG
                png_bytes = tree_plot.pipe(format="png")
                img = PILImage.open(io.BytesIO(png_bytes))
                plt.imshow(img)
                plt.axis("off")
                plt.title(f"Arbre {tree_index} - CatBoost")

            except ImportError as e:
                raise ImportError(f"CatBoost visualization error: {str(e)}")
            except Exception as e:
                logger.error(f"Erreur CatBoost: {str(e)}")
                raise

        else:
            raise ValueError(
                f"Type de modèle non supporté pour la visualisation d'arbre: {model_type}. "
                "Supportés: DecisionTree, RandomForest, ExtraTrees, XGBoost, LightGBM, CatBoost"
            )

        plt.tight_layout()
        plt.show()

        # Retourner des infos utiles
        info = {
            "model_type": model_type,
            "model_name": model.model_name,
            "tree_index": tree_index,
            "n_features": len(features),
        }

        # Ajouter le nombre d'arbres si ensemble
        if hasattr(actual_model, "n_estimators"):
            info["n_trees"] = actual_model.n_estimators
        elif hasattr(actual_model, "get_params"):
            params = actual_model.get_params()
            if "n_estimators" in params:
                info["n_trees"] = params["n_estimators"]

        return info

    def summary(self, target_number: int, experiment_id: int = None):
        """
        Generate a comprehensive summary for a target including scores, plots and analysis.

        This method displays:
        1. Scores table for all models
        2. Model evaluation plots:
           - Classification: confusion matrix, ROC curve, PR curve, threshold analysis
           - Regression: actual vs predicted, residuals analysis, QQ plot
        3. PCA scatter & variance plots (if columns_pca is not empty)
        4. Feature importance plot
        5. SHAP values plot
        6. LIME summary plot (SP-LIME)
        7. Tree plot (if best model is tree-based)

        Args:
            target_number (int): Target number to summarize
            experiment_id (int, optional): Experiment ID to load. If not provided,
                uses self.experiment.

        Returns:
            pd.DataFrame: The scores DataFrame
        """
        # Load experiment if experiment_id is provided
        if experiment_id is not None:
            experiment = Experiment.get(experiment_id)
            if experiment is None:
                raise ValueError(f"Experiment with id={experiment_id} not found")
            self._load_experiment(experiment)

        if self.experiment is None:
            raise ValueError("No experiment loaded. Provide experiment_id or load an experiment first.")

        # 1. Get and display scores
        print(f"=" * 60)
        print(f"SUMMARY FOR TARGET_{target_number}")
        print(f"=" * 60)
        print(f"\n📊 MODEL SCORES\n")

        scores_df = self.get_scores(target_number)
        print(scores_df.to_string())

        # Get best model info
        bm = self.experiment.get_best_model(target_number)

        if bm is None:
            raise ValueError(f"No best model found for TARGET_{target_number}")

        best_model_name = bm.model.model_type.name if bm.model else None
        is_classification = target_number in self.target_clf

        print(f"\n🏆 Best model: {best_model_name}")

        # 2. Model evaluation plots
        if is_classification:
            print(f"\n📈 CLASSIFICATION EVALUATION\n")
            try:
                self.plot_evaluation_for_classification(target_number, model_name=best_model_name)
            except Exception as e:
                logger.warning(f"Could not plot classification evaluation: {e}")
        else:
            print(f"\n📈 REGRESSION EVALUATION\n")
            try:
                self.plot_evaluation_for_regression(target_number, model_name=best_model_name)
            except Exception as e:
                logger.warning(f"Could not plot regression evaluation: {e}")

        # 3. PCA plots if columns_pca is not empty
        if self.columns_pca:
            print(f"\n🔍 PCA ANALYSIS\n")
            try:
                if is_classification:
                    self.plot_pca_scatter(target_number)
                self.plot_pca_variance()
            except Exception as e:
                logger.warning(f"Could not plot PCA: {e}")

        # 4. Feature importance
        print(f"\n📊 FEATURE IMPORTANCE\n")
        try:
            self.plot_feature_importance(target_number)
        except Exception as e:
            logger.warning(f"Could not plot feature importance: {e}")

        # 5. SHAP values
        print(f"\n🎯 SHAP VALUES\n")
        try:
            self.plot_shap_values(target_number)
        except Exception as e:
            logger.warning(f"Could not plot SHAP values: {e}")

        # 6. LIME summary (SP-LIME)
        print(f"\n🍋 LIME SUMMARY (SP-LIME)\n")
        try:
            self.plot_lime_summary(target_number)
        except Exception as e:
            logger.warning(f"Could not plot LIME summary: {e}")

        # 7. Tree plot if best model is tree-based
        tree_models = [
            "decision_tree", "random_forest", "xgb", "lgb", "catboost",
            "adaboost", "bagging", "extra_trees"
        ]
        if best_model_name and best_model_name.lower() in tree_models:
            print(f"\n🌳 TREE VISUALIZATION\n")
            try:
                self.plot_tree(target_number)
            except Exception as e:
                logger.warning(f"Could not plot tree: {e}")

        print(f"\n" + "=" * 60)
        print(f"END OF SUMMARY")
        print(f"=" * 60)

        return scores_df
