import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import time
import os
import json
import warnings
import joblib
from pathlib import Path
import pickle
import ast

# ML models
from sklearn.model_selection import TimeSeriesSplit, StratifiedKFold, KFold
from sklearn.metrics import (
    mean_absolute_percentage_error,
    root_mean_squared_error,
    mean_absolute_error,
    r2_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    log_loss,
    roc_auc_score,
    roc_curve,
    auc,
    precision_recall_curve,
    average_precision_score,
    confusion_matrix,
)
from sklearn.preprocessing import LabelBinarizer
import lightgbm as lgb
import xgboost as xgb

# DL models - imported lazily when needed
# import tensorflow as tf
# import keras
# K = tf.keras.backend

# Optimization
import ray
from ray.tune import Tuner, TuneConfig, with_parameters, RunConfig
from ray.tune.search.hyperopt import HyperOptSearch
from ray.tune.search.bayesopt import BayesOptSearch
from ray.tune.logger import TBXLoggerCallback
from ray.tune.schedulers import ASHAScheduler
from ray.air import session

# HyperOpt standalone
from hyperopt import hp, fmin, tpe, Trials, STATUS_OK, space_eval

# Internal library
from lecrapaud.search_space import all_models
from lecrapaud.utils import logger, serialize_for_json, get_run_dir, strip_timestamp_suffix
from lecrapaud.config import PYTHON_ENV, LECRAPAUD_OPTIMIZATION_BACKEND
from lecrapaud.feature_selection import load_train_data
from lecrapaud.models import (
    ModelType,
    BestModel,
    Model,
    Target,
    Experiment,
)
from lecrapaud.mixins import LeCrapaudEstimatorMixin
from lecrapaud.services import ArtifactService
from lecrapaud.model import (
    LeCrapaudModel,
    find_best_threshold,
)

os.environ["COVERAGE_FILE"] = str(Path(".coverage").resolve())

# Suppress XGBoost and LightGBM logging
import logging

logging.getLogger("lightgbm").setLevel(logging.ERROR)
logging.getLogger("xgboost").setLevel(logging.ERROR)

# Set global verbosity for XGBoost
xgb.set_config(verbosity=0)

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")

# Reproducible result
np.random.seed(42)

_tf_initialized = False

def _init_tensorflow():
    """Initialize tensorflow with deterministic settings (lazy)."""
    global _tf_initialized
    if _tf_initialized:
        return
    import tensorflow as tf
    import keras
    keras.utils.set_random_seed(42)
    tf.config.experimental.enable_op_determinism()
    _tf_initialized = True


# test configuration
def test_hardware():
    import tensorflow as tf
    devices = tf.config.list_physical_devices()
    logger.info("\nDevices: ", devices)

    gpus = tf.config.list_physical_devices("GPU")
    if gpus:
        details = tf.config.experimental.get_device_details(gpus[0])
        logger.info("GPU details: ", details)


# Suppress specific warning messages related to file system monitor
# logging.getLogger("ray").setLevel(logging.CRITICAL)
# logging.getLogger("ray.train").setLevel(logging.CRITICAL)
# logging.getLogger("ray.tune").setLevel(logging.CRITICAL)
# logging.getLogger("ray.autoscaler").setLevel(logging.CRITICAL)
# logging.getLogger("ray.raylet").setLevel(logging.CRITICAL)
# logging.getLogger("ray.monitor").setLevel(logging.CRITICAL)
# logging.getLogger("ray.dashboard").setLevel(logging.CRITICAL)
# logging.getLogger("ray.gcs_server").setLevel(logging.CRITICAL)

warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")


def trainable_cv(
    params,
    x_train,
    y_train,
    x_val,
    y_val,
    model_name,
    target_type,
    experiment_name,
    target_number,
    create_model,
    n_splits=3,
    plot=False,
    log_dir=None,
    target_clf_thresholds: dict = None,
    time_series=True,
    recurrent=False,
    use_class_weights=True,
    optimization_metric=None,
):
    """Cross-validation version of trainable for hyperopt.

    Uses TimeSeriesSplit for temporal data or StratifiedKFold/KFold for i.i.d. data.
    Returns pooled metrics (single logloss/RMSE calculated on all concatenated predictions).
    """
    # Combine train and validation data for cross-validation
    if recurrent:
        x_train_val = np.concatenate([x_train, x_val], axis=0)
        y_train_val = np.concatenate([y_train, y_val], axis=0)
    else:
        x_train_val = pd.concat([x_train, x_val], axis=0)
        y_train_val = pd.concat([y_train, y_val], axis=0)
        # Store original index for later use if needed
        original_index = x_train_val.index.copy()
        # Reset index for proper iloc indexing with CV splits
        x_train_val = x_train_val.reset_index(drop=True)
        y_train_val = y_train_val.reset_index(drop=True)

    # Choose appropriate cross-validation splitter
    if time_series:
        # Time series split for temporal data
        n_samples = len(x_train_val)
        test_size = int(n_samples / (n_splits + 1))  # Ensure reasonable test size
        cv_splitter = TimeSeriesSplit(n_splits=n_splits, test_size=test_size)
    else:
        # Stratified or regular K-fold for i.i.d. data
        if target_type == "classification":
            cv_splitter = StratifiedKFold(
                n_splits=n_splits, shuffle=True, random_state=42
            )
        else:
            cv_splitter = KFold(n_splits=n_splits, shuffle=True, random_state=42)

    # Store all predictions and true values for pooled metrics
    all_predictions = []
    all_y_true = []
    fold_times = []

    # Get splits based on the CV strategy
    if time_series or target_type == "regression":
        splits = cv_splitter.split(x_train_val)
    else:
        # For stratified split, we need to pass y
        if recurrent:
            # Extract the target from the 2D array (first column is target)
            y_for_split = y_train_val[:, 0]
        else:
            y_for_split = y_train_val
        splits = cv_splitter.split(x_train_val, y_for_split)

    for fold_idx, (train_idx, val_idx) in enumerate(splits):
        # Extract fold data
        if recurrent:
            x_fold_train = x_train_val[train_idx]
            y_fold_train = y_train_val[train_idx]
            x_fold_val = x_train_val[val_idx]
            y_fold_val = y_train_val[val_idx]
        else:
            x_fold_train = x_train_val.iloc[train_idx]
            y_fold_train = y_train_val.iloc[train_idx]
            x_fold_val = x_train_val.iloc[val_idx]
            y_fold_val = y_train_val.iloc[val_idx]

        # Train model for this fold
        model = LeCrapaudModel(
            model_name=model_name,
            target_type=target_type,
            target_number=target_number,
            create_model=create_model,
            plot=False,  # Disable individual fold plots
            log_dir=log_dir,
            use_class_weights=use_class_weights,
            optimization_metric=optimization_metric,
        )

        if recurrent:
            timesteps = params["timesteps"]
            x_fold_train = x_fold_train[:, -timesteps:, :]
            x_fold_val = x_fold_val[:, -timesteps:, :]

        # Fit model
        model.fit(x_fold_train, y_fold_train, x_fold_val, y_fold_val, params)

        # Get predictions
        y_pred = model.predict(x_fold_val)

        # Handle recurrent model indexing
        if recurrent:
            y_fold_val = pd.DataFrame(
                y_fold_val, columns=["TARGET", "index"]
            ).set_index("index")
            y_pred.index = y_fold_val.index

        # Store predictions and true values
        all_predictions.append(y_pred)
        all_y_true.append(y_fold_val)

    # Concatenate all fold predictions
    if target_type == "classification":
        # For classification, we need to handle probability columns
        all_pred_df = pd.concat(all_predictions, axis=0)
        all_y_series = pd.concat(all_y_true, axis=0)
        # Ensure we have a DataFrame with TARGET column
        if isinstance(all_y_series, pd.Series):
            all_y_df = pd.DataFrame({"TARGET": all_y_series})
        else:
            all_y_df = all_y_series
    else:
        # For regression, just concatenate the predictions
        all_pred_series = pd.concat(all_predictions, axis=0)
        all_y_series = pd.concat(all_y_true, axis=0)
        all_pred_df = pd.DataFrame({"PRED": all_pred_series})
        all_y_df = pd.DataFrame({"TARGET": all_y_series})

    # Create combined prediction DataFrame
    prediction = pd.concat([all_y_df[["TARGET"]], all_pred_df], axis=1)

    # Calculate pooled metrics
    score = {
        "DATE": datetime.now(),
        "MODEL_NAME": model_name,
        "EVAL_DATA_STD": prediction["TARGET"].std(),
    }

    # Unscale if needed (for regression with scaling)
    if (
        model.need_scaling
        and target_type == "regression"
        and model.scaler_y is not None
    ):
        prediction.loc[:, "TARGET"] = model.scaler_y.inverse_transform(
            prediction[["TARGET"]].values
        )
        prediction.loc[:, "PRED"] = model.scaler_y.inverse_transform(
            prediction[["PRED"]].values
        )

    # Evaluate with pooled predictions
    score.update(evaluate(prediction, target_type, target_clf_thresholds))

    metric = "RMSE" if target_type == "regression" else "LOGLOSS"
    logger.debug(f"{model_name} CV pooled {metric}: {score[metric]:.4f}")

    # Report to Ray if in Ray context
    if session.get_session():
        session.report(metrics=score)
    return score


def trainable(
    params,
    x_train,
    y_train,
    x_val,
    y_val,
    model_name,
    target_type,
    experiment_name,
    target_number,
    create_model,
    plot=False,
    log_dir=None,
    target_clf_thresholds: dict = None,
    use_class_weights=True,
    optimization_metric=None,
):
    """Standalone version of train_model that doesn't depend on self"""
    # Create model engine
    model = LeCrapaudModel(
        model_name=model_name,
        target_type=target_type,
        target_number=target_number,
        create_model=create_model,
        plot=plot,
        log_dir=log_dir,
        use_class_weights=use_class_weights,
        optimization_metric=optimization_metric,
    )

    logger.debug(
        f"TARGET_{target_number} - Training a {model.model_name} at {datetime.now()} : {experiment_name}, TARGET_{target_number}"
    )

    if model.recurrent:
        timesteps = params["timesteps"]
        x_train = x_train[:, -timesteps:, :]
        x_val = x_val[:, -timesteps:, :]

    # Compile and fit model on train set
    model.fit(x_train, y_train, x_val, y_val, params)

    # Prediction on val set
    y_pred = model.predict(x_val)

    # fix for recurrent model because x_val has no index as it is a 3D np array
    if model.recurrent:
        y_val = pd.DataFrame(y_val, columns=["TARGET", "index"]).set_index("index")
        y_pred.index = y_val.index

    prediction = pd.concat([y_val, y_pred], axis=1)

    # Unscale the data
    if (
        model.need_scaling
        and model.target_type == "regression"
        and model.scaler_y is not None
    ):
        # scaler_y needs 2D array with shape (-1, 1)
        prediction.loc[:, "TARGET"] = model.scaler_y.inverse_transform(
            prediction[["TARGET"]].values
        )
        prediction.loc[:, "PRED"] = model.scaler_y.inverse_transform(
            prediction[["PRED"]].values
        )

    # Evaluate model
    score = {
        "DATE": datetime.now(),
        "MODEL_NAME": model.model_name,
        "EVAL_DATA_STD": prediction["TARGET"].std(),
    }

    score.update(evaluate(prediction, target_type, target_clf_thresholds))

    metric = "RMSE" if target_type == "regression" else "LOGLOSS"
    logger.debug(f"{model.model_name} scores on validation set: {score[metric]:.4f}")

    # Report to Ray if in Ray context
    if session.get_session():
        session.report(metrics=score)
        return score

    return score, model, prediction


class ModelSelector(LeCrapaudEstimatorMixin):
    """Model selection and hyperparameter optimization.

    This class handles model training, hyperparameter optimization (via HyperOpt or Ray Tune),
    and selection of the best model based on validation performance. It supports both
    classical ML models (XGBoost, LightGBM, CatBoost, etc.) and deep learning models
    (LSTM, GRU, TCN, Transformer).

    Args:
        experiment: LeCrapaud experiment instance for context and artifact storage.
        target_number: Target number (1-indexed) for which to train models.
        **kwargs: Additional configuration parameters that override experiment context.
            - models_idx: List of model names/indices to train.
            - perform_hyperopt: Whether to perform hyperparameter optimization.
            - number_of_trials: Number of hyperopt trials (default: 20).
            - perform_crossval: Use cross-validation during hyperopt.
            - optimization_metric: Metric to optimize (e.g., 'RMSE', 'ROC_AUC').
            - use_class_weights: Use class weights for imbalanced data.
            - target_clf_thresholds: Classification thresholds per target.

    Attributes:
        best_model_: The best trained model after fit().
        target_type: 'classification' or 'regression' based on target_clf.
        metric: The optimization metric being used.
        features: List of selected features for this target.

    Example:
        >>> from lecrapaud import ModelSelector
        >>> ms = ModelSelector(experiment=experiment, target_number=1)
        >>> ms.fit(data_dict)  # dict with train/val/test splits
        >>> best = ms.get_best_model()
    """

    def __init__(
        self,
        experiment: Experiment = None,
        target_number: int = None,
        **kwargs,
    ):
        # The mixin will set defaults from DEFAULT_PARAMS, then experiment.context, then kwargs
        super().__init__(experiment=experiment, **kwargs)

        self.target_number = target_number

        # Handle target_clf_thresholds for specific target
        # Handle both string and integer keys for backward compatibility
        if self.target_number and self.target_clf_thresholds:
            # Try both integer and string versions of the target number
            if self.target_number in self.target_clf_thresholds:
                self.target_clf_thresholds = self.target_clf_thresholds[
                    self.target_number
                ]
            elif str(self.target_number) in self.target_clf_thresholds:
                self.target_clf_thresholds = self.target_clf_thresholds[
                    str(self.target_number)
                ]

        # Derived attributes
        if self.target_number is not None:
            self.target_type = (
                "classification"
                if self.target_number in self.target_clf
                else "regression"
            )
            # Use configurable optimization metric or default (per-target support)
            from lecrapaud.utils import (
                get_default_metric,
                validate_metric_for_target_type,
            )
            optimization_metric = getattr(self, "optimization_metric", {})
            # Handle per-target dict format
            if isinstance(optimization_metric, dict) and self.target_number in optimization_metric:
                self.metric = optimization_metric[self.target_number]
            # Backward compatibility: string applies to all targets
            elif isinstance(optimization_metric, str):
                self.metric = optimization_metric
            # Auto: use default based on target type
            else:
                self.metric = get_default_metric(self.target_type)
            validate_metric_for_target_type(self.metric, self.target_type)

        # Set paths and features if experiment is available
        if self.experiment:
            self.experiment_dir = self.experiment.path
            self.experiment_id = self.experiment.id

            if self.target_number is not None:
                self.features = self.experiment.get_features(self.target_number)

            self.all_features = self.experiment.get_all_features(
                date_column=self.date_column, group_column=self.group_column
            )

    # Main training function
    def fit(self, X, y=None, reshaped_data=None, best_params=None):
        """
        Fit the model selector (train and select best model).

        Args:
            X: Either a DataFrame or a dict with train/val/test data
            y: Target values (ignored, uses TARGET columns)
            reshaped_data: Optional reshaped data for recurrent models
            best_params: Optional pre-defined best parameters

        Returns:
            self: Returns self for chaining
        """
        logger.info(f"  Processing TARGET_{self.target_number} ({self.target_type})...")

        # Handle both DataFrame and dict inputs
        if isinstance(X, dict):
            self.data = X
            self.reshaped_data = reshaped_data
        else:
            # For simple DataFrame input, we expect it to be just training data
            # This is less common for ModelSelector which typically needs train/val/test
            raise ValueError("ModelSelector requires a dict with train/val/test data")
        # Get all parameters from experiment context
        context = self.experiment.context
        self.experiment_name = context.get("experiment_name", "")
        self.plot = context.get("plot", True)
        self.number_of_trials = context.get("number_of_trials", 20)
        self.perform_crossval = context.get("perform_crossval", False)
        self.preserve_model = context.get("preserve_model", True)
        self.perform_hyperopt = context.get("perform_hyperopt", True)

        if self.experiment_id is None:
            raise ValueError("Please provide a experiment.")

        if self.data:
            train = self.data["train"]
            val = self.data["val"]
            test = self.data["test"]
            train_scaled = self.data["train_scaled"]
            val_scaled = self.data["val_scaled"]
            test_scaled = self.data["test_scaled"]
        else:
            (
                train,
                val,
                test,
                train_scaled,
                val_scaled,
                test_scaled,
            ) = load_train_data(self.experiment_id)

        if (
            any(all_models[i].get("recurrent") for i in self.models_idx)
            and not self.time_series
        ):
            ValueError(
                "You need to set time_series to true to use recurrent model, or remove recurrent models from models_idx chosen"
            )

        if (
            any(all_models[i].get("recurrent") for i in self.models_idx)
            and self.time_series
        ):
            if self.reshaped_data is None:
                raise ValueError("reshaped_data is not provided.")

            logger.info("Loading reshaped data...")
            x_train_reshaped = self.reshaped_data["x_train_reshaped"]
            y_train_reshaped = self.reshaped_data["y_train_reshaped"]
            x_val_reshaped = self.reshaped_data["x_val_reshaped"]
            y_val_reshaped = self.reshaped_data["y_val_reshaped"]
            x_test_reshaped = self.reshaped_data["x_test_reshaped"]
            y_test_reshaped = self.reshaped_data["y_test_reshaped"]

        # create model selection in db
        target = Target.find_by(name=f"TARGET_{self.target_number}")
        if not target:
            raise ValueError(f"Target TARGET_{self.target_number} not found in database")
        self.target_id = target.id  # Store target_id for use in saving data

        best_model_entry = BestModel.upsert(
            target_id=target.id,
            experiment_id=self.experiment_id,
        )
        if not best_model_entry or not best_model_entry.id:
            raise ValueError(
                f"Failed to create BestModel for target_id={target.id}, "
                f"experiment_id={self.experiment_id}"
            )
        logger.debug(f"Created BestModel with id={best_model_entry.id}")

        # Initialize scores_tracking in memory
        scores_tracking_records = []

        # STEP 1 : TRAINING MODELS
        for i in self.models_idx:
            config = all_models[i]
            recurrent = config["recurrent"]
            need_scaling = config["need_scaling"]
            model_name = config["model_name"]

            if recurrent is False and config[self.target_type] is None:
                continue  # for naive bayes models that cannot be used in regression

            # Check if model already exists in database (skip if preserve_model is False)
            if self.preserve_model:
                existing_model_type = ModelType.find_by(name=model_name, type=self.target_type)
                if existing_model_type:
                    existing_model = Model.find_by(
                        best_model_id=best_model_entry.id,
                        model_type_id=existing_model_type.id
                    )
                    if existing_model and existing_model.params:
                        logger.debug(f"  Skipping {model_name} - already exists in database")
                        continue

            logger.info(f"  Training {model_name} for TARGET_{self.target_number}...")

            # Create run directory following new folder structure
            from lecrapaud.directories import tmp_dir
            run_dir, run_id = get_run_dir(
                base_dir=tmp_dir,
                experiment_name=self.experiment_name,
                target_name=f"TARGET_{self.target_number}",
                model_name=model_name,
            )
            self.run_dir = run_dir
            self.run_id = run_id

            # Getting data
            if recurrent:
                # Clear cluster from previous Keras session graphs.
                import tensorflow as tf
                tf.keras.backend.clear_session()

                features_idx = [
                    i
                    for i, e in enumerate(self.all_features)
                    if e in set(self.features)
                ]
                # TODO: Verify that features_idx are the right one, because scaling can re-arrange columns (should be good)...
                x_train = x_train_reshaped[:, :, features_idx]
                y_train = y_train_reshaped[:, [self.target_number, 0]]
                x_val = x_val_reshaped[:, :, features_idx]
                y_val = y_val_reshaped[:, [self.target_number, 0]]
                x_test = x_test_reshaped[:, :, features_idx]
                y_test = y_test_reshaped[:, [self.target_number, 0]]
            else:
                config = config[self.target_type]

                if need_scaling and self.target_type == "regression":
                    x_train = train_scaled[self.features]
                    y_train = train_scaled[f"TARGET_{self.target_number}"].rename(
                        "TARGET"
                    )
                    x_val = val_scaled[self.features]
                    y_val = val_scaled[f"TARGET_{self.target_number}"].rename("TARGET")
                    x_test = test_scaled[self.features]
                    y_test = test_scaled[f"TARGET_{self.target_number}"].rename(
                        "TARGET"
                    )
                else:
                    x_train = train[self.features]
                    y_train = train[f"TARGET_{self.target_number}"].rename("TARGET")
                    x_val = val[self.features]
                    y_val = val[f"TARGET_{self.target_number}"].rename("TARGET")
                    x_test = test[self.features]
                    y_test = test[f"TARGET_{self.target_number}"].rename("TARGET")

            log_dir = get_log_dir(self.run_dir)

            # Instantiate model
            model = LeCrapaudModel(
                target_number=self.target_number,
                model_name=model_name,
                search_params=config["search_params"],
                target_type=self.target_type,
                create_model=config["create_model"],
                plot=self.plot,
                log_dir=log_dir,
                use_class_weights=self.use_class_weights,
                optimization_metric=self.metric,
            )

            # Tuning hyperparameters
            start = time.time()
            if self.perform_hyperopt:
                hyperoptimized_params = self.hyperoptimize(
                    x_train, y_train, x_val, y_val, model
                )
            elif best_params:
                hyperoptimized_params = best_params[model_name]
            else:
                # Try to load best_params from database
                existing_model_type = ModelType.find_by(name=model_name, type=self.target_type)
                existing_model = None
                if existing_model_type:
                    existing_model = Model.find_by(
                        best_model_id=best_model_entry.id,
                        model_type_id=existing_model_type.id
                    )
                if existing_model and existing_model.params:
                    hyperoptimized_params = existing_model.params
                else:
                    raise FileNotFoundError(
                        f"Could not find {model_name} in current data. Try to run an hyperoptimization by setting `perform_hyperopt` to true, or pass `best_params`"
                    )

            # Always evaluate on test set (no cross-validation here)
            # The hyperopt already did CV if needed to find best params
            score, model, pred = self.train_model(
                params=hyperoptimized_params,
                x_train=pd.concat([x_train, x_val], axis=0),
                y_train=pd.concat([y_train, y_val], axis=0),
                x_val=x_test,
                y_val=y_test,
                model=model,
            )
            stop = time.time()
            training_time = stop - start

            logger.debug(f"Model training finished in {training_time:.2f} seconds")
            logger.debug(f"👉 {model.model_name} scores on test set:")
            for metric, value in score.items():
                if isinstance(value, (int, float)):
                    logger.debug(f"  {metric}: {value:.4f}")

            # Verify model_type_id is set (should have been set by LeCrapaudModel.fit())
            if model.model_type_id is None:
                raise ValueError(
                    f"model_type_id is None for {model.model_name}. "
                    "This indicates the model was not properly registered in the database."
                )

            # Create Model record first to get its ID for linking to the model artifact
            drop_cols = [
                "DATE",
                "MODEL_NAME",
            ]
            score_data_for_db = {k: v for k, v in score.items() if k not in drop_cols}
            score_data_for_db = {k.lower(): v for k, v in score_data_for_db.items()}
            logger.debug(
                f"Creating Model: model_type_id={model.model_type_id}, "
                f"best_model_id={best_model_entry.id}"
            )
            model_record = Model.upsert(
                model_type_id=model.model_type_id,
                best_model_id=best_model_entry.id,
                params=serialize_for_json(hyperoptimized_params),
                training_time=training_time,
                **score_data_for_db,
            )
            if not model_record:
                raise ValueError(
                    f"Failed to create Model for model_type_id={model.model_type_id}, "
                    f"best_model_id={best_model_entry.id}"
                )
            logger.debug(f"Created Model with id={model_record.id}")

            # Save best model to database, linked to its record
            model.save(
                experiment_id=self.experiment_id,
                target_id=self.target_id,
                model_id=model_record.id,
            )

            # Save predictions to database with model_id
            ArtifactService.save_dataframe(
                experiment_id=self.experiment_id,
                data_type="prediction",
                df=pred,
                model_id=model_record.id,
            )

            # Create run.json with metadata
            run_metadata = {
                "run_id": self.run_id,
                "experiment_id": self.experiment_id,
                "experiment_name": self.experiment_name,
                "experiment_base_name": strip_timestamp_suffix(self.experiment_name),
                "target_id": self.target_id,
                "target_name": f"TARGET_{self.target_number}",
                "model_type": model_name,
                "model_id": model_record.id,
                "best_model_id": best_model_entry.id,
                "created_at": datetime.now().isoformat(),
                "status": "completed",
                "best_loss": score.get(self.metric),
                "metric": self.metric,
                "training_time": training_time,
                "params": serialize_for_json(hyperoptimized_params),
            }
            run_json_path = f"{self.run_dir}/run.json"
            with open(run_json_path, "w") as f:
                json.dump(run_metadata, f, indent=2)

            # Accumulate scores in memory
            scores_tracking_records.append(score)

        # STEP 2 :FINDING BEST MODEL OVERALL
        # Build scores_tracking DataFrame from accumulated records
        scores_tracking = pd.DataFrame(scores_tracking_records)

        # Sort by metric (ascending for minimize metrics, descending for maximize)
        from lecrapaud.utils import get_metric_direction
        ascending = get_metric_direction(self.metric) == "minimize"
        scores_tracking.sort_values(self.metric, ascending=ascending, inplace=True)

        # Save scores_tracking to database
        ArtifactService.save_dataframe(
            experiment_id=self.experiment_id,
            data_type="scores_tracking",
            df=scores_tracking,
            target_id=self.target_id,
        )
        best_score_overall = scores_tracking.iloc[0, :]
        best_model_name = best_score_overall["MODEL_NAME"]
        if self.target_type == "classification":
            best_thresholds = best_score_overall["THRESHOLDS"]
            if isinstance(best_thresholds, str):
                best_thresholds = ast.literal_eval(best_thresholds)
            # Save thresholds to database via ArtifactService
            ArtifactService.save_thresholds(
                experiment_id=self.experiment_id,
                target_id=target.id,
                thresholds=best_thresholds,
            )
        else:
            best_thresholds = None

        # Get best model params from Model
        best_model_type = ModelType.find_by(name=best_model_name, type=self.target_type)
        if not best_model_type:
            raise ValueError(f"ModelType not found: name={best_model_name}, type={self.target_type}")

        best_model_record = Model.find_by(
            best_model_id=best_model_entry.id,
            model_type_id=best_model_type.id,
        )
        if not best_model_record:
            logger.warning(
                f"Model not found for best_model_id={best_model_entry.id}, "
                f"model_type_id={best_model_type.id}"
            )
        best_model_params = best_model_record.params if best_model_record else {}

        # Save to db
        best_model_entry = BestModel.get(best_model_entry.id)
        model_type = ModelType.find_by(
            name=best_score_overall["MODEL_NAME"], type=self.target_type
        )
        best_model_entry.model_type_id = model_type.id
        best_model_entry.params = serialize_for_json(best_model_params)
        best_model_entry.thresholds = best_thresholds
        if best_model_record:
            best_model_entry.model_id = best_model_record.id

        drop_cols = [
            "DATE",
            "MODEL_NAME",
        ]
        best_score_overall = {
            k: v for k, v in best_score_overall.items() if k not in drop_cols
        }
        score_data = {k.lower(): v for k, v in best_score_overall.items()}
        best_model_entry.score = serialize_for_json(score_data)

        logger.debug(
            f"Saving BestModel: model_type_id={best_model_entry.model_type_id}, "
            f"model_id={best_model_entry.model_id}"
        )
        best_model_entry.save()

        # Format a clean summary
        def fmt(val):
            """Format numeric values nicely."""
            if val is None:
                return "N/A"
            if isinstance(val, (int, float)):
                if abs(val) >= 1000 or (abs(val) < 0.01 and val != 0):
                    return f"{val:.2e}"
                return f"{val:.4f}"
            return str(val)

        summary_lines = [
            "",
            "=" * 60,
            f"  MODEL SELECTION COMPLETE - TARGET_{self.target_number}",
            "=" * 60,
            f"  Best Model: {best_model_name}",
            f"  Optimized for: {self.metric}",
            "",
        ]

        if self.target_type == "regression":
            summary_lines.extend([
                "  Regression Metrics:",
                f"    RMSE:  {fmt(best_score_overall.get('RMSE'))}",
                f"    MAE:   {fmt(best_score_overall.get('MAE'))}",
                f"    R²:    {fmt(best_score_overall.get('R2'))}",
            ])
        else:
            summary_lines.extend([
                "  Classification Metrics:",
                f"    LogLoss:   {fmt(best_score_overall.get('LOGLOSS'))}",
                f"    Accuracy:  {fmt(best_score_overall.get('ACCURACY'))}",
                f"    ROC AUC:   {fmt(best_score_overall.get('ROC_AUC'))}",
                f"    F1:        {fmt(best_score_overall.get('F1'))}",
            ])

        summary_lines.append("=" * 60)
        logger.info("\n".join(summary_lines))

        # Load best model from database
        self.best_model_ = LeCrapaudModel(
            model_name=best_model_name,
            target_type=self.target_type,
            target_number=self.target_number,
            experiment_id=self.experiment_id,
            target_id=self.target_id,
        )
        self._set_fitted()
        return self

    def get_best_model(self):
        """
        Get the best trained model.

        Returns:
            The best model found during training
        """
        self._check_is_fitted()
        return self.best_model_

    def hyperoptimize(self, x_train, y_train, x_val, y_val, model: LeCrapaudModel):
        """Choose between Ray Tune and HyperOpt standalone based on configuration."""
        if LECRAPAUD_OPTIMIZATION_BACKEND == "hyperopt":
            return self.hyperoptimize_hyperopt(x_train, y_train, x_val, y_val, model)
        elif LECRAPAUD_OPTIMIZATION_BACKEND == "ray":
            return self.hyperoptimize_ray(x_train, y_train, x_val, y_val, model)
        else:
            raise ValueError(
                f"Invalid optimization backend: {LECRAPAUD_OPTIMIZATION_BACKEND}."
            )

    def hyperoptimize_hyperopt(self, x_train, y_train, x_val, y_val, model: LeCrapaudModel):
        """Hyperparameter optimization using HyperOpt standalone (Celery-friendly)."""

        logger.debug("Start tuning hyperparameters with HyperOpt standalone...")

        # Convert Ray search space to HyperOpt search space
        def convert_search_space(ray_space):
            """Convert Ray Tune search space to HyperOpt format."""
            from ray.tune.search.sample import Categorical, Float, Integer

            hp_space = {}
            for key, value in ray_space.items():
                if isinstance(value, Float):
                    if (
                        hasattr(value, "sampler")
                        and value.sampler.__class__.__name__ == "LogUniform"
                    ):
                        # LogUniform distribution
                        hp_space[key] = hp.loguniform(
                            key, np.log(value.lower), np.log(value.upper)
                        )
                    else:
                        # Uniform distribution
                        hp_space[key] = hp.uniform(key, value.lower, value.upper)
                elif isinstance(value, Integer):
                    # Integer uniform distribution
                    hp_space[key] = hp.randint(key, value.lower, value.upper)
                elif isinstance(value, Categorical):
                    # Categorical/choice distribution
                    hp_space[key] = hp.choice(key, value.categories)
                elif isinstance(value, dict):
                    # Nested dict, recurse
                    hp_space[key] = convert_search_space(value)
                else:
                    # Static value or unknown type
                    hp_space[key] = value
            return hp_space

        # Create objective function for HyperOpt
        def objective(params):
            """Objective function to minimize."""
            try:
                # Convert numpy types to native Python types
                params = serialize_for_json(params)

                # Use existing trainable function based on perform_crossval
                if self.perform_crossval:
                    score = trainable_cv(
                        params,
                        x_train,
                        y_train,
                        x_val,
                        y_val,
                        model.model_name,
                        self.target_type,
                        self.experiment_name,
                        self.target_number,
                        model.create_model,
                        n_splits=3,
                        plot=model.plot,
                        log_dir=model.log_dir,
                        target_clf_thresholds=self.target_clf_thresholds,
                        time_series=self.time_series,
                        recurrent=model.recurrent,
                        use_class_weights=self.use_class_weights,
                        optimization_metric=self.metric,
                    )
                else:
                    score, _, _ = trainable(
                        params,
                        x_train,
                        y_train,
                        x_val,
                        y_val,
                        model.model_name,
                        self.target_type,
                        self.experiment_name,
                        self.target_number,
                        model.create_model,
                        plot=model.plot,
                        log_dir=model.log_dir,
                        target_clf_thresholds=self.target_clf_thresholds,
                        use_class_weights=self.use_class_weights,
                        optimization_metric=self.metric,
                    )

                # HyperOpt always minimizes, so negate for maximize metrics
                from lecrapaud.utils import get_metric_direction
                metric_value = score[self.metric]
                if get_metric_direction(self.metric) == "maximize":
                    loss = -metric_value  # Negate to convert maximize to minimize
                else:
                    loss = metric_value

                # Log trial info
                logger.debug(f"Trial completed - {self.metric}: {metric_value:.4f}")

                return {
                    "loss": loss,
                    "status": STATUS_OK,
                    "score": score,  # Keep full score dict for analysis
                }

            except Exception as e:
                logger.error(f"Trial failed: {str(e)}")
                return {"loss": float("inf"), "status": STATUS_OK, "error": str(e)}

        # Convert search space
        hp_search_space = convert_search_space(model.search_params)

        # Run optimization
        trials = Trials()
        best_params = fmin(
            fn=objective,
            space=hp_search_space,
            algo=tpe.suggest,
            max_evals=self.number_of_trials,
            trials=trials,
            verbose=True,
            show_progressbar=True,
        )

        # Get the actual parameter values (not just indices for hp.choice)
        best_params = space_eval(hp_search_space, best_params)

        # Convert numpy types to native Python types
        best_params = serialize_for_json(best_params)

        # Get best score from trials
        best_trial_idx = np.argmin([t["result"]["loss"] for t in trials.trials])
        best_score = trials.trials[best_trial_idx]["result"].get("score", {})

        # Log results
        logger.debug(f"Best hyperparameters found were:\n{best_params}")
        logger.debug(f"Best Scores found were:\n{best_score}")

        # Create summary DataFrame for consistency with Ray version
        results_df = pd.DataFrame(
            [
                {
                    "trial_id": i,
                    self.metric: t["result"]["loss"],
                    **{
                        k: v
                        for k, v in t["result"].get("score", {}).items()
                        if isinstance(v, (int, float))
                    },
                }
                for i, t in enumerate(trials.trials)
                if t["result"]["status"] == STATUS_OK
            ]
        )

        if not results_df.empty:
            logger.debug(f"Markdown table with all trials :\n{results_df.to_markdown()}")

        # Save trial history for analysis
        trials_path = f"{self.run_dir}/hyperopt_trials.pkl"
        with open(trials_path, "wb") as f:
            pickle.dump(trials, f)

        # Collect and save hyperopt errors
        errors = []
        for i, t in enumerate(trials.trials):
            if t["result"].get("error"):
                errors.append({
                    "trial_id": i,
                    "error": t["result"]["error"],
                    "params": serialize_for_json(t["misc"]["vals"]),
                })
        if errors:
            errors_path = f"{self.run_dir}/hyperopt_errors.json"
            with open(errors_path, "w") as f:
                json.dump(errors, f, indent=2)

        return best_params

    def hyperoptimize_ray(self, x_train, y_train, x_val, y_val, model: LeCrapaudModel):
        from lecrapaud.utils import get_metric_direction

        def collect_error_logs(run_dir: str, storage_path: str):
            output_error_file = f"{run_dir}/hyperopt_errors.json"
            errors = []

            # Walk through the ray_results directory
            for root, dirs, files in os.walk(storage_path):
                # Check if 'error.txt' exists in the current directory
                if "error.txt" in files:
                    error_file_path = os.path.join(root, "error.txt")
                    logger.info(f"Processing error file: {error_file_path}")
                    with open(error_file_path, "r") as infile:
                        errors.append({
                            "source": error_file_path,
                            "error": infile.read(),
                        })

            if errors:
                with open(output_error_file, "w") as f:
                    json.dump(errors, f, indent=2)
                logger.info(f"All errors written to {output_error_file}")

        logger.debug("Start tuning hyperparameters...")

        storage_path = f"{self.run_dir}/ray_results"

        # Initialize Ray with the runtime environment
        ray.init(
            runtime_env={
                "excludes": [
                    ".git/**/*",
                    "**/*.pyc",
                    "**/__pycache__",
                    "**/data/*",
                    "**/notebooks/*",
                    "**/tests/*",
                    "**/docs/*",
                    "**/.pytest_cache/*",
                    "**/venv/*",
                    "**/.venv/*",
                    "**/build/*",
                    "**/dist/*",
                    "**/*.egg-info/*",
                ]
            }
        )

        # Choose between regular trainable or CV version based on perform_crossval flag
        # perform_crossval controls whether to use CV during hyperopt
        if self.perform_crossval:
            trainable_fn = trainable_cv
            additional_params = {
                "n_splits": 3,  # Can be made configurable
                "time_series": self.time_series,  # Controls whether to use TimeSeriesSplit or StratifiedKFold
                "recurrent": model.recurrent,
            }
        else:
            trainable_fn = trainable
            additional_params = {}

        tuner = Tuner(
            trainable=with_parameters(
                trainable_fn,
                x_train=x_train,
                y_train=y_train,
                x_val=x_val,
                y_val=y_val,
                model_name=model.model_name,
                target_type=self.target_type,
                experiment_name=self.experiment_name,
                target_number=self.target_number,
                create_model=model.create_model,
                plot=model.plot,
                log_dir=model.log_dir,
                target_clf_thresholds=self.target_clf_thresholds,
                **additional_params,
            ),
            param_space=model.search_params,
            tune_config=TuneConfig(
                metric=self.metric,
                mode="min" if get_metric_direction(self.metric) == "minimize" else "max",
                search_alg=HyperOptSearch(),
                num_samples=self.number_of_trials,
                scheduler=ASHAScheduler(max_t=100, grace_period=10),
            ),
            run_config=RunConfig(
                stop={"training_iteration": 100},
                storage_path=storage_path,
                callbacks=[TBXLoggerCallback()],
            ),
        )
        try:
            results = tuner.fit()

            best_result = results.get_best_result(
                self.metric,
                "min" if get_metric_direction(self.metric) == "minimize" else "max"
            )
            best_params = best_result.config
            best_score = best_result.metrics

            # log results
            logger.debug(f"Best hyperparameters found were:\n{best_params}")
            logger.debug(f"Best Scores found were:\n{best_score}")
            logger.debug(
                f"Markdown table with all trials :\n{results.get_dataframe().to_markdown()}"
            )
            # Collect errors in single file
            collect_error_logs(run_dir=self.run_dir, storage_path=storage_path)

        except Exception as e:
            raise Exception(e)

        finally:
            ray.shutdown()

        return best_params

    def train_model(self, params, x_train, y_train, x_val, y_val, model: LeCrapaudModel):
        # Use the standalone training function to avoid duplication
        # For train_model, we pass the data directly (not as Ray references)
        return trainable(
            params,
            x_train,
            y_train,
            x_val,
            y_val,
            model.model_name,
            self.target_type,
            self.experiment_name,
            self.target_number,
            model.create_model,
            model.plot,
            log_dir=model.log_dir,
            target_clf_thresholds=self.target_clf_thresholds,
            use_class_weights=self.use_class_weights,
            optimization_metric=self.metric,
        )

def evaluate(
    prediction: pd.DataFrame,
    target_type: str,
    target_clf_thresholds: dict = None,
):
    """Evaluate model performance and compute metrics.

    Computes comprehensive metrics for regression (RMSE, MAE, MAPE, R2) or
    classification (LogLoss, Accuracy, Precision, Recall, F1, ROC AUC) tasks.

    Args:
        prediction: DataFrame with columns:
            - TARGET: True labels
            - PRED: Predicted values/labels
            - For classification: probability columns (0, 1, ...) for each class
        target_type: Either 'classification' or 'regression'.
        target_clf_thresholds: Thresholds for classification tasks.
            Format: {"precision": 0.8} or {"recall": 0.9}.

    Returns:
        dict: Dictionary of computed metrics.
            For regression: RMSE, MAE, MAPE, R2, BIAS, etc.
            For classification: LOGLOSS, ACCURACY, PRECISION, RECALL, F1,
                ROC_AUC, AVG_PRECISION, THRESHOLDS, etc.

    Example:
        >>> scores = evaluate(predictions, 'classification', {"precision": 0.8})
        >>> print(f"Accuracy: {scores['ACCURACY']:.4f}")
    """
    score = {}
    y_true = prediction["TARGET"]
    y_pred = prediction["PRED"]

    # Set default threshold if not provided
    if target_clf_thresholds is None:
        target_clf_thresholds = {"precision": 0.80}

    if target_type == "regression":
        # Main metrics
        score["RMSE"] = root_mean_squared_error(y_true, y_pred)
        score["MAE"] = mean_absolute_error(y_true, y_pred)
        score["MAPE"] = mean_absolute_percentage_error(y_true, y_pred)
        score["R2"] = r2_score(y_true, y_pred)

        # Robustness: avoid division by zero
        std_target = y_true.std()
        mean_target = y_true.mean()
        median_target = y_true.median()

        # RMSE / STD
        score["RMSE_STD_RATIO"] = (
            float(100 * score["RMSE"] / std_target) if std_target else 1000
        )

        # Median absolute deviation (MAD)
        mam = (y_true - mean_target).abs().median()  # Median Abs around Mean
        mad = (y_true - median_target).abs().median()  # Median Abs around Median
        score["MAM"] = mam
        score["MAD"] = mad
        score["MAE_MAM_RATIO"] = (
            float(100 * score["MAE"] / mam) if mam else 1000
        )  # MAE / MAD → Plus stable, moins sensible aux outliers.
        score["MAE_MAD_RATIO"] = (
            float(100 * score["MAE"] / mad) if mad else 1000
        )  # MAE / Médiane des écarts absolus autour de la moyenne: Moins robuste aux outliers

        # Bias metrics: Average error divided by ground truth
        # Bias = mean(predictions - actuals) / mean(actuals)
        mean_error = (y_pred - y_true).mean()
        score["BIAS"] = (
            float(mean_error / mean_target) if mean_target != 0 else float("inf")
        )

    else:

        labels = np.unique(y_true)
        num_classes = labels.size
        y_pred_proba = (
            prediction[1] if num_classes == 2 else prediction.iloc[:, 2:].values
        )
        # if num_classes > 2:
        #     lb = LabelBinarizer(sparse_output=False)  # Change to True for sparse matrix
        #     lb.fit(labels)
        #     y_true_onhot = lb.transform(y_true)
        #     y_pred_onehot = lb.transform(y_pred)

        score["LOGLOSS"] = log_loss(y_true, y_pred_proba)
        score["ACCURACY"] = accuracy_score(y_true, y_pred)
        score["PRECISION"] = precision_score(
            y_true,
            y_pred,
            average=("binary" if num_classes == 2 else "macro"),
        )
        score["RECALL"] = recall_score(
            y_true,
            y_pred,
            average=("binary" if num_classes == 2 else "macro"),
        )
        score["F1"] = f1_score(
            y_true,
            y_pred,
            average=("binary" if num_classes == 2 else "macro"),
        )
        score["ROC_AUC"] = float(roc_auc_score(y_true, y_pred_proba, multi_class="ovr"))
        score["AVG_PRECISION"] = average_precision_score(
            y_true, y_pred_proba, average="macro"
        )

        # Store the complete thresholds dictionary
        if len(target_clf_thresholds.keys()) > 1:
            raise ValueError(
                f"Only one metric can be specified for threshold optimization. found {target_clf_thresholds.keys()}"
            )
        # Get the single key-value pair or use defaults
        metric, value = (
            next(iter(target_clf_thresholds.items()))
            if target_clf_thresholds
            else ("precision", 0.8)
        )

        score["THRESHOLDS"] = find_best_threshold(prediction, metric, value)

        # Collect valid metrics across all classes (works for both binary and multiclass)
        valid_metrics = [
            m for m in score["THRESHOLDS"].values() if m["threshold"] is not None
        ]

        if valid_metrics:
            score["PRECISION_AT_THRESHOLD"] = np.mean(
                [m["precision"] for m in valid_metrics]
            )
            score["RECALL_AT_THRESHOLD"] = np.mean([m["recall"] for m in valid_metrics])
            score["F1_AT_THRESHOLD"] = np.mean([m["f1"] for m in valid_metrics])
        else:
            score["PRECISION_AT_THRESHOLD"] = None
            score["RECALL_AT_THRESHOLD"] = None
            score["F1_AT_THRESHOLD"] = None

    return score


# utils
def get_log_dir(run_dir: str):
    """Generates a structured log directory path for TensorBoard within a run directory.

    Args:
        run_dir: The run directory path (e.g., tmp/stock_pred/TARGET_1/lgb/20260128_175156/).

    Returns:
        str: Path to the tensorboard subdirectory within the run directory.
    """
    log_dir = Path(run_dir) / "tensorboard"
    log_dir.mkdir(parents=True, exist_ok=True)
    return str(log_dir)


def plot_training_progress(
    logs, model_name, target_number, title_suffix="Training Progress"
):
    """
    Plot training and validation metrics during model training.

    Args:
        logs: DataFrame or dict containing training history
        model_name: Name of the model being trained
        target_number: Target number for the model
        title_suffix: Optional suffix for the plot title
    """
    if isinstance(logs, dict):
        logs = pd.DataFrame(logs)

    if logs.empty:
        return

    # Style configuration
    colors = {
        "train": "#2E86AB",  # Blue
        "val": "#E94F37",    # Red
    }

    fig, ax = plt.subplots(figsize=(12, 5))

    # Determine which columns to plot
    train_col = None
    val_col = None

    if "loss" in logs.columns:
        train_col = "loss"
    elif "train" in logs.columns:
        train_col = "train"

    if "val_loss" in logs.columns:
        val_col = "val_loss"
    elif "val" in logs.columns:
        val_col = "val"

    # Plot training curve
    if train_col:
        train_values = logs[train_col]
        ax.plot(
            train_values,
            lw=2,
            color=colors["train"],
            label=f"Train ({train_values.iloc[-1]:.4f})",
            alpha=0.9
        )

    # Plot validation curve
    if val_col:
        val_values = logs[val_col]
        ax.plot(
            val_values,
            lw=2,
            color=colors["val"],
            label=f"Validation ({val_values.iloc[-1]:.4f})",
            alpha=0.9
        )

        # Mark best epoch (minimum validation loss)
        best_epoch = val_values.idxmin()
        best_val = val_values.min()
        ax.axvline(
            x=best_epoch,
            color=colors["val"],
            linestyle="--",
            alpha=0.5,
            lw=1.5
        )
        ax.scatter(
            [best_epoch],
            [best_val],
            color=colors["val"],
            s=100,
            zorder=5,
            edgecolors="white",
            linewidths=2
        )
        ax.annotate(
            f"Best: {best_val:.4f}\n(epoch {best_epoch})",
            xy=(best_epoch, best_val),
            xytext=(10, 10),
            textcoords="offset points",
            fontsize=9,
            color=colors["val"],
            fontweight="bold"
        )

    # If no standard columns found, plot all available
    if train_col is None and val_col is None:
        for i, col in enumerate(logs.columns):
            color = plt.cm.tab10(i)
            if "val" in col.lower():
                ax.plot(logs[col], "--", lw=2, color=color, label=f"Val {col}")
            else:
                ax.plot(logs[col], lw=2, color=color, label=f"Train {col}")

    # Styling
    ax.set_title(
        f"{model_name.upper()} - Target {target_number}\n{title_suffix}",
        fontsize=12,
        fontweight="bold"
    )
    ax.set_xlabel("Epoch / Iteration", fontsize=10)
    ax.set_ylabel("Loss", fontsize=10)

    # Grid styling
    ax.grid(True, alpha=0.3, linestyle="-", linewidth=0.5)
    ax.set_axisbelow(True)

    # Legend
    ax.legend(loc="upper right", framealpha=0.9, fontsize=9)

    # Clean up spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.show()


# plots
def plot_evaluation_for_classification(prediction: dict):
    """
    Plot evaluation metrics for classification tasks (both binary and multiclass).

    Args:
        prediction (pd.DataFrame): Should be a df with:
            - TARGET: true labels
            - PRED: predicted labels
            - For binary: column '1' or 1 for positive class probabilities
            - For multiclass: columns 2 onwards for class probabilities
    """
    y_true = prediction["TARGET"]
    y_pred = prediction["PRED"]

    # Plot confusion matrix
    plot_confusion_matrix(y_true, y_pred)

    # Determine if binary or multiclass
    unique_labels = np.unique(y_true)
    unique_labels = np.sort(unique_labels)
    n_classes = len(unique_labels)

    if n_classes <= 2:
        # Binary classification
        y_pred_proba = prediction[1] if 1 in prediction.columns else prediction["1"]

        # Compute and plot ROC curve
        fpr, tpr, _ = roc_curve(y_true, y_pred_proba)
        roc_auc = auc(fpr, tpr)

        plt.figure(figsize=(8, 8))
        plt.plot(
            fpr,
            tpr,
            color="darkorange",
            lw=2,
            label=f"ROC curve (area = {roc_auc:0.2f})",
        )
        plt.plot([0, 1], [0, 1], color="navy", lw=2, linestyle="--")
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.title("ROC Curve")
        plt.legend(loc="lower right")
        plt.show()

        # Compute and plot precision-recall curve
        precision, recall, _ = precision_recall_curve(y_true, y_pred_proba)
        average_precision = average_precision_score(y_true, y_pred_proba)

        plt.figure(figsize=(8, 8))
        plt.step(recall, precision, color="b", alpha=0.2, where="post")
        plt.fill_between(recall, precision, step="post", alpha=0.2, color="b")
        plt.xlabel("Recall")
        plt.ylabel("Precision")
        plt.ylim([0.0, 1.05])
        plt.xlim([0.0, 1.0])
        plt.title(f"Precision-Recall Curve: AP={average_precision:0.2f}")
        plt.show()

    else:
        # Multiclass classification
        # Get class probabilities
        pred_cols = [
            col for col in prediction.columns if col not in ["ID", "TARGET", "PRED"]
        ]
        y_pred_proba = prediction[pred_cols].values

        # Compute ROC curve and ROC area for each class
        fpr = dict()
        tpr = dict()
        roc_auc = dict()

        plt.figure(figsize=(10, 8))
        colors = plt.cm.get_cmap("tab10")(np.linspace(0, 1, n_classes))

        for i, (label, color) in enumerate(zip(unique_labels, colors)):
            y_true_binary = (y_true == label).astype(int)
            y_score = y_pred_proba[:, i]

            fpr[i], tpr[i], _ = roc_curve(y_true_binary, y_score)
            roc_auc[i] = auc(fpr[i], tpr[i])

            plt.plot(
                fpr[i],
                tpr[i],
                color=color,
                lw=2,
                label=f"Class {label} (area = {roc_auc[i]:0.2f})",
            )

        plt.plot([0, 1], [0, 1], "k--", lw=2)
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.title("Multiclass ROC Curves (One-vs-Rest)")
        plt.legend(loc="lower right")
        plt.show()

        # Compute PR curve for each class
        plt.figure(figsize=(10, 8))

        for i, (label, color) in enumerate(zip(unique_labels, colors)):
            y_true_binary = (y_true == label).astype(int)
            y_score = y_pred_proba[:, i]

            precision, recall, _ = precision_recall_curve(y_true_binary, y_score)
            average_precision = average_precision_score(y_true_binary, y_score)

            plt.step(
                recall,
                precision,
                color=color,
                alpha=0.8,
                where="post",
                label=f"Class {label} (AP = {average_precision:0.2f})",
            )

        plt.xlabel("Recall")
        plt.ylabel("Precision")
        plt.ylim([0.0, 1.05])
        plt.xlim([0.0, 1.0])
        plt.title("Multiclass Precision-Recall Curves")
        plt.legend(loc="lower left")
        plt.show()


def plot_confusion_matrix(y_true, y_pred):
    # Calculate confusion matrix
    cm = confusion_matrix(y_true, y_pred)

    # Get unique, sorted class labels
    labels = np.unique(np.concatenate((y_true, y_pred)))
    labels = np.sort(labels)

    # Calculate class distribution
    class_dist = np.bincount(y_true.astype(int))
    class_dist_pct = class_dist / len(y_true) * 100

    # Create figure with two subplots stacked vertically
    fig = plt.figure(figsize=(10, 12))

    # Subplot 1: Confusion Matrix
    ax1 = plt.subplot(2, 1, 1)  # Changed to 2 rows, 1 column, first subplot

    # Create a custom colormap (blue to white to red)
    cmap = sns.diverging_palette(220, 10, as_cmap=True)

    # Plot heatmap with better styling
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap=cmap,
        center=0,
        linewidths=0.5,
        linecolor="lightgray",
        cbar_kws={"label": "Number of Samples"},
        ax=ax1,
    )

    # Add title and labels with better styling
    ax1.set_title("Confusion Matrix", fontsize=14, pad=20, weight="bold")
    ax1.set_xlabel("Predicted Label", fontsize=12, labelpad=10)
    ax1.set_ylabel("True Label", fontsize=12, labelpad=10)

    # Set tick labels to be centered and more readable
    ax1.set_xticks(np.arange(len(labels)) + 0.5)
    ax1.set_yticks(np.arange(len(labels)) + 0.5)
    ax1.set_xticklabels(labels, fontsize=10)
    ax1.set_yticklabels(labels, fontsize=10, rotation=0)

    # Add grid lines for better readability
    ax1.set_xticks(np.arange(len(labels) + 1) - 0.5, minor=True)
    ax1.set_yticks(np.arange(len(labels) + 1) - 0.5, minor=True)
    ax1.grid(which="minor", color="w", linestyle="-", linewidth=2)
    ax1.tick_params(which="minor", bottom=False, left=False)

    # Subplot 2: Class Distribution
    ax2 = plt.subplot(2, 1, 2)  # Changed to 2 rows, 1 column, second subplot

    # Create a bar plot for class distribution
    bars = ax2.bar(
        labels.astype(str),
        class_dist_pct,
        color=sns.color_palette("viridis", len(labels)),
    )

    # Add percentage labels on top of bars
    for bar in bars:
        height = bar.get_height()
        ax2.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 1,
            f"{height:.1f}%",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    # Add title and labels
    ax2.set_title("Class Distribution", fontsize=14, pad=20, weight="bold")
    ax2.set_xlabel("Class", fontsize=12, labelpad=10)
    ax2.set_ylabel("Percentage of Total Samples", fontsize=12, labelpad=10)
    ax2.set_ylim(0, 100)
    ax2.grid(axis="y", linestyle="--", alpha=0.7)

    # Add total count annotation
    total = len(y_true)
    ax2.text(
        0.5,
        -0.15,  # Adjusted y-position for better spacing
        f"Total samples: {total:,}",
        transform=ax2.transAxes,
        ha="center",
        fontsize=10,
        bbox=dict(
            facecolor="white",
            alpha=0.8,
            edgecolor="lightgray",
            boxstyle="round,pad=0.5",
        ),
    )

    # Adjust layout to prevent overlap with more vertical space
    plt.tight_layout(rect=[0, 0.03, 1, 0.98])
    plt.show()


def plot_evaluation_for_regression(prediction: pd.DataFrame, figsize: tuple = (14, 10)):
    """
    Plot evaluation metrics for regression tasks.

    Displays:
    1. Actual vs Predicted scatter plot
    2. Residuals vs Predicted (heteroscedasticity check)
    3. Residuals histogram (normality check)
    4. QQ plot (normality check)

    Args:
        prediction (pd.DataFrame): Should have columns 'TARGET' and 'PRED'
        figsize (tuple): Figure size
    """
    from scipy import stats

    y_true = prediction["TARGET"].values
    y_pred = prediction["PRED"].values
    residuals = y_true - y_pred

    # Calculate metrics for display
    rmse = np.sqrt(np.mean(residuals**2))
    mae = np.mean(np.abs(residuals))
    r2 = 1 - (np.sum(residuals**2) / np.sum((y_true - np.mean(y_true))**2))

    fig, axes = plt.subplots(2, 2, figsize=figsize)

    # 1. Actual vs Predicted
    ax1 = axes[0, 0]
    ax1.scatter(y_true, y_pred, alpha=0.5, edgecolors='none', s=20)

    # Perfect prediction line
    min_val = min(y_true.min(), y_pred.min())
    max_val = max(y_true.max(), y_pred.max())
    ax1.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='Perfect prediction')

    # Regression line
    z = np.polyfit(y_true, y_pred, 1)
    p = np.poly1d(z)
    ax1.plot(np.sort(y_true), p(np.sort(y_true)), 'b-', lw=1, alpha=0.8, label=f'Fit: y={z[0]:.2f}x+{z[1]:.2f}')

    ax1.set_xlabel('Actual')
    ax1.set_ylabel('Predicted')
    ax1.set_title(f'Actual vs Predicted\nR² = {r2:.4f}')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)

    # 2. Residuals vs Predicted
    ax2 = axes[0, 1]
    ax2.scatter(y_pred, residuals, alpha=0.5, edgecolors='none', s=20)
    ax2.axhline(y=0, color='r', linestyle='--', lw=2)

    # Add LOWESS smoothing line to detect patterns
    try:
        from statsmodels.nonparametric.smoothers_lowess import lowess
        smoothed = lowess(residuals, y_pred, frac=0.3)
        ax2.plot(smoothed[:, 0], smoothed[:, 1], 'g-', lw=2, label='LOWESS')
        ax2.legend()
    except ImportError:
        pass

    ax2.set_xlabel('Predicted')
    ax2.set_ylabel('Residuals')
    ax2.set_title('Residuals vs Predicted\n(Check for heteroscedasticity)')
    ax2.grid(True, alpha=0.3)

    # 3. Residuals Histogram
    ax3 = axes[1, 0]
    n, bins, patches = ax3.hist(residuals, bins=50, density=True, alpha=0.7, color='steelblue', edgecolor='white')

    # Fit normal distribution
    mu, std = stats.norm.fit(residuals)
    x = np.linspace(residuals.min(), residuals.max(), 100)
    ax3.plot(x, stats.norm.pdf(x, mu, std), 'r-', lw=2, label=f'Normal fit\nμ={mu:.2f}, σ={std:.2f}')

    # Add skewness and kurtosis
    skewness = stats.skew(residuals)
    kurtosis = stats.kurtosis(residuals)
    ax3.text(0.95, 0.95, f'Skewness: {skewness:.3f}\nKurtosis: {kurtosis:.3f}',
             transform=ax3.transAxes, ha='right', va='top',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    ax3.set_xlabel('Residuals')
    ax3.set_ylabel('Density')
    ax3.set_title('Residuals Distribution\n(Check for normality)')
    ax3.legend(loc='upper left')
    ax3.grid(True, alpha=0.3)

    # 4. QQ Plot
    ax4 = axes[1, 1]
    stats.probplot(residuals, dist="norm", plot=ax4)
    ax4.set_title('Q-Q Plot\n(Check for normality)')
    ax4.grid(True, alpha=0.3)

    # Add metrics summary
    fig.suptitle(f'Regression Evaluation\nRMSE: {rmse:.4f} | MAE: {mae:.4f} | R²: {r2:.4f}',
                 fontsize=14, fontweight='bold', y=1.02)

    plt.tight_layout()
    plt.show()

    # Print interpretation guide
    print("\n📊 Interpretation Guide:")
    print("─" * 50)
    print("1. Actual vs Predicted: Points should be close to the red dashed line")
    print("2. Residuals vs Predicted: Should show random scatter around 0 (no pattern)")
    print("3. Residuals Histogram: Should be bell-shaped (normal distribution)")
    print("4. Q-Q Plot: Points should follow the red line for normality")
    print("─" * 50)
