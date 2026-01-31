"""LeCrapaudModel - Model wrapper for training and prediction."""

import ast
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

import joblib
# Heavy ML imports are loaded lazily in methods that use them
# import lightgbm as lgb
# import xgboost as xgb
# import tensorflow as tf
# import keras
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import LabelBinarizer
from sklearn.metrics import precision_recall_curve
from tensorboardX import SummaryWriter
from pydantic import BaseModel

from lecrapaud.search_space import all_models
from lecrapaud.utils import logger
from lecrapaud.services import ArtifactService


class LeCrapaudModel:
    """Unified model wrapper for training and prediction in LeCrapaud.

    This class provides a consistent interface for training and using various
    model types including scikit-learn estimators, gradient boosting libraries
    (XGBoost, LightGBM, CatBoost), and recurrent neural networks (Keras/TensorFlow).

    The model handles automatic metric selection, class weight computation for
    imbalanced datasets, early stopping, TensorBoard logging, and model
    persistence to the database.

    Args:
        model_name: Name of the model type (e.g., "lgb", "xgb", "catboost", "lstm").
        target_type: Type of target ("classification" or "regression").
        target_number: Target index number for multi-target experiments.
        path: File path for loading/saving models (backward compatibility).
        experiment_id: Database experiment ID for model storage.
        target_id: Database target ID for model storage.
        search_params: Hyperparameters from optimization search.
        create_model: Callable that creates the model instance.
        plot: Whether to plot training progress.
        log_dir: Directory for TensorBoard logs.
        use_class_weights: Whether to use class weights for imbalanced data.
        optimization_metric: Metric to optimize during training.

    Attributes:
        _model: The underlying trained model instance.
        threshold: Classification threshold(s) for prediction.
        model_type_id: Database ID of the registered model type.
        recurrent: Whether this is a recurrent neural network.
        need_scaling: Whether the model requires scaled features.
        scaler_y: Target scaler for regression models that need scaling.

    Example:
        >>> model = LeCrapaudModel(
        ...     model_name="lgb",
        ...     target_type="classification",
        ...     experiment_id=1,
        ...     target_id=1,
        ... )
        >>> model.fit(x_train, y_train, x_val, y_val, params)
        >>> predictions = model.predict(x_test)
    """

    def __init__(
        self,
        model_name: str = None,
        target_type: str = None,
        target_number: int = None,
        path: str = None,
        experiment_id: int = None,
        target_id: int = None,
        search_params: dict = {},
        create_model=None,
        plot: bool = False,
        log_dir: str = None,
        use_class_weights: bool = True,
        optimization_metric: str = None,
    ):
        self.threshold = None
        self.model_id = None
        self.path = path
        self.experiment_id = experiment_id
        self.target_id = target_id
        self.target_number = target_number
        self.use_class_weights = use_class_weights
        self.optimization_metric = optimization_metric
        self.model_name = model_name
        self.target_type = target_type

        # Look up target_type from database if not provided
        if not self.target_type and self.target_id:
            from lecrapaud.models import Target
            target = Target.find_by(id=self.target_id)
            if target:
                self.target_type = target.type

        # Load model from database
        if experiment_id and target_id:
            self._load_from_db()

        config = [
            config for config in all_models if config["model_name"] == self.model_name
        ]
        if config is None or len(config) == 0:
            Exception(
                f"Model {self.model_name} is not supported by this library."
                f"Choose a model from the list of supported models: {[model['model_name'] for model in all_models].join(', ')}"
            )
        config = config[0]

        self.recurrent = config["recurrent"]
        self.need_scaling = config["need_scaling"]
        self.search_params = search_params
        self.create_model = create_model
        self.plot = plot
        self.log_dir = log_dir

        # Load scaler_y from database if available
        if self.need_scaling and self.target_type == "regression":
            if self.experiment_id and self.target_id:
                self.scaler_y = ArtifactService.load_scaler(
                    experiment_id=self.experiment_id,
                    scaler_name=f"scaler_y_{self.target_number}",
                    target_id=self.target_id,
                )
            elif self.path:
                # Fallback to file-based loading for backward compatibility
                scaler_path = f"{self.path}/scaler_y.pkl"
                if os.path.exists(scaler_path):
                    self.scaler_y = joblib.load(scaler_path)
                else:
                    self.scaler_y = None
            else:
                self.scaler_y = None
        else:
            self.scaler_y = None

    def fit(self, *args):
        """Train the model using the appropriate fitting method.

        Automatically selects the fitting method based on model type:
        - fit_recurrent for RNN/LSTM models
        - fit_boosting for LightGBM and XGBoost
        - fit_catboost for CatBoost
        - fit_sklearn for scikit-learn compatible models

        Args:
            *args: Training arguments (x_train, y_train, x_val, y_val, params).

        Returns:
            The trained model instance.

        Raises:
            ValueError: If model type registration fails.
        """
        if self.recurrent:
            fit = self.fit_recurrent
        elif (self.model_name == "lgb") or (self.model_name == "xgb"):
            fit = self.fit_boosting
        elif self.model_name == "catboost":
            fit = self.fit_catboost
        else:
            fit = self.fit_sklearn
        model = fit(*args)

        # Register model in database and store its ID
        from lecrapaud.models import ModelType
        model_type_db = ModelType.upsert(
            name=self.model_name,
            type=self.target_type,
        )
        if model_type_db is None:
            raise ValueError(
                f"Failed to upsert ModelType record for name={self.model_name}, type={self.target_type}"
            )
        self.model_type_id = model_type_db.id
        logger.debug(f"Registered model type {self.model_name} with id={self.model_type_id}")

        return model

    def fit_sklearn(self, x_train, y_train, x_val, y_val, params):
        """Train a scikit-learn compatible model.

        Handles sample weighting for imbalanced classification and
        probability calibration for SVM models with hinge loss.

        Args:
            x_train: Training features.
            y_train: Training targets.
            x_val: Validation features (unused for sklearn).
            y_val: Validation targets (unused for sklearn).
            params: Model parameters passed to create_model.

        Returns:
            The trained sklearn model.
        """

        # Create & Compile the model
        model = self.create_model(**params)

        # Train the model
        logger.debug("Fitting the model...")
        logger.debug(f"x_train shape: {x_train.shape}, x_val shape: {x_val.shape}")
        logger.debug(f"y_train shape: {y_train.shape}, y_val shape: {y_val.shape}")

        # Compute sample weights for imbalanced classification
        sample_weight = None
        if self.target_type == "classification" and self.use_class_weights:
            from sklearn.utils.class_weight import compute_sample_weight
            sample_weight = compute_sample_weight('balanced', y_train)

        model.fit(x_train, y_train, sample_weight=sample_weight)

        if (
            self.target_type == "classification"
            and "loss" in model.get_params().keys()
            and "hinge" in model.get_params()["loss"]
        ):
            # This is for SVC models with hinge loss
            # You should use CalibratedClassifierCV when you are working with classifiers that do not natively output well-calibrated probability estimates.
            # TODO: investigate if we should use calibration for random forest, gradiant boosting models, and bagging models
            logger.debug(
                f"Re-Calibrating {self.model_name} to get predict probabilities..."
            )
            calibrator = CalibratedClassifierCV(model, method="sigmoid", cv=3, n_jobs=-1)
            model = calibrator.fit(x_train, y_train)

        logger.debug(f"Successfully created a {self.model_name} at {datetime.now()}")

        self._model = model

        return model

    def fit_catboost(self, x_train, y_train, x_val, y_val, params):
        """
        Train CatBoost models with native early stopping and log metrics to TensorBoard.
        Also supports plotting of the primary eval metric if self.plot is True.
        """
        from lecrapaud.model_selection import plot_training_progress

        # Prepare constructor parameters
        ctor_params = dict(params) if params else {}
        early_stopping_rounds = ctor_params.pop("early_stopping_rounds", None)
        # Alias support: num_boost_round -> iterations
        num_boost_round = ctor_params.pop("num_boost_round", None)
        if num_boost_round is not None and "iterations" not in ctor_params:
            ctor_params["iterations"] = num_boost_round

        # Determine classification/regression setup
        labels = np.unique(y_train)
        num_class = (
            labels.size
            if self.target_type == "classification" and labels.size > 2
            else 1
        )
        is_binary = num_class == 2

        # Determine eval_metric based on optimization_metric or use defaults
        from lecrapaud.utils import get_eval_metric, get_default_metric

        if self.target_type == "regression":
            ctor_params.setdefault("loss_function", "RMSE")
            default_eval_metric = "RMSE"
        else:
            if num_class <= 2:
                ctor_params.setdefault("loss_function", "Logloss")
                default_eval_metric = "Logloss"
            else:
                ctor_params.setdefault("loss_function", "MultiClass")
                default_eval_metric = "MultiClass"

        # Use optimization_metric if set, otherwise use default
        if self.optimization_metric:
            eval_metric = get_eval_metric(
                self.optimization_metric, "catboost", is_binary=(num_class <= 2)
            )
            if eval_metric is None:
                eval_metric = default_eval_metric
        else:
            eval_metric = ctor_params.get("eval_metric", default_eval_metric)
        ctor_params.setdefault("eval_metric", eval_metric)

        # Add class weights for imbalanced classification
        if self.target_type == "classification" and self.use_class_weights:
            if is_binary:
                scale_pos_weight = sum(y_train == 0) / max(sum(y_train == 1), 1)
                ctor_params.setdefault("scale_pos_weight", scale_pos_weight)
            else:
                ctor_params.setdefault("auto_class_weights", "Balanced")

        # Instantiate CatBoost model from provided constructor
        model = self.create_model(**ctor_params, allow_writing_files=False)

        # Train with eval_set and early stopping
        logger.debug(f"Fitting the model {self.model_name}...")
        logger.debug(f"x_train shape: {x_train.shape}, x_val shape: {x_val.shape}")
        logger.debug(f"y_train shape: {y_train.shape}, y_val shape: {y_val.shape}")

        model.fit(
            x_train,
            y_train,
            eval_set=[(x_val, y_val)],
            use_best_model=True,
            early_stopping_rounds=early_stopping_rounds,
            verbose=False,
        )

        # Retrieve evaluation results
        evals_result = model.get_evals_result()
        # CatBoost commonly uses 'learn' and 'validation' (or 'validation_0')
        learn_key = "learn"
        val_key = None
        for k in evals_result.keys():
            if k != learn_key:
                val_key = k
                break

        # Ensure eval_metric exists; otherwise fallback to first available metric
        if eval_metric not in evals_result.get(learn_key, {}):
            if evals_result.get(learn_key):
                eval_metric = next(iter(evals_result[learn_key].keys()))

        # TensorBoard logging
        writer = SummaryWriter(self.log_dir)
        try:
            # learn_scores = evals_result.get(learn_key, {}).get(eval_metric, [])
            val_scores = (
                evals_result.get(val_key, {}).get(eval_metric, []) if val_key else []
            )
            # for i, v in enumerate(learn_scores):
            #     writer.add_scalar(f"CatBoost/train/{eval_metric}", v, i)
            for i, v in enumerate(val_scores):
                writer.add_scalar(f"CatBoost/{eval_metric}", v, i)
        finally:
            writer.close()

        # Optional plotting of training progress
        if self.plot and eval_metric and learn_key in evals_result and val_key:
            logs = {
                "train": evals_result[learn_key].get(eval_metric, []),
                "val": evals_result[val_key].get(eval_metric, []),
            }
            plot_training_progress(
                logs=logs,
                model_name=self.model_name,
                target_number=self.target_number,
                title_suffix=f"Training Progress - {eval_metric}",
            )

        logger.debug(
            f"Successfully created a {self.model_name} at {datetime.now()}"
        )

        self._model = model
        return model

    def fit_boosting(self, x_train, y_train, x_val, y_val, params):
        """Train a LightGBM or XGBoost model with early stopping.

        Uses the native C++ libraries for efficient training with
        validation-based early stopping and TensorBoard logging.

        Args:
            x_train: Training features.
            y_train: Training targets.
            x_val: Validation features for early stopping.
            y_val: Validation targets for early stopping.
            params: Dictionary with 'model_params', 'num_boost_round',
                   and 'early_stopping_rounds'.

        Returns:
            The trained booster model.
        """
        import lightgbm as lgb
        import xgboost as xgb
        from lecrapaud.model_selection import plot_training_progress

        # Create a TensorBoardX writer
        writer = SummaryWriter(self.log_dir)
        evals_result = {}

        # Training
        labels = np.unique(y_train)
        num_class = (
            labels.size
            if self.target_type == "classification" and labels.size > 2
            else 1
        )
        is_binary = num_class == 2
        logger.debug(f"Fitting the model {self.model_name}...")
        logger.debug(f"x_train shape: {x_train.shape}, x_val shape: {x_val.shape}")
        logger.debug(f"y_train shape: {y_train.shape}, y_val shape: {y_val.shape}")

        # Compute class weights for imbalanced classification
        scale_pos_weight = 1
        sample_weight = None
        if self.target_type == "classification" and self.use_class_weights:
            if is_binary:
                scale_pos_weight = sum(y_train == 0) / max(sum(y_train == 1), 1)
            else:
                from sklearn.utils.class_weight import compute_sample_weight
                sample_weight = compute_sample_weight('balanced', y_train)

        if self.model_name == "lgb":
            train_data = lgb.Dataset(x_train, label=y_train, weight=sample_weight)
            val_data = lgb.Dataset(x_val, label=y_val)

            def tensorboard_callback(env):
                for i, metric in enumerate(env.evaluation_result_list):
                    metric_name, _, metric_value, _ = metric
                    writer.add_scalar(
                        f"LightGBM/{metric_name}", metric_value, env.iteration
                    )

            loss = (
                "regression"
                if self.target_type == "regression"
                else ("binary" if num_class <= 2 else "multiclass")
            )
            # Determine eval_metric based on optimization_metric or use defaults
            from lecrapaud.utils import get_eval_metric
            default_eval_metric = (
                "rmse"
                if self.target_type == "regression"
                else ("binary_logloss" if num_class <= 2 else "multi_logloss")
            )
            if self.optimization_metric:
                eval_metric = get_eval_metric(
                    self.optimization_metric, "lightgbm", is_binary=(num_class <= 2)
                )
                if eval_metric is None:
                    eval_metric = default_eval_metric
            else:
                eval_metric = default_eval_metric
            # Add scale_pos_weight for binary classification
            lgb_params = {
                **params["model_params"],
                "objective": loss,
                "metric": eval_metric,
                "num_class": num_class,
                "verbose": -1,
                "verbose_eval": False,
            }
            if is_binary and self.use_class_weights:
                lgb_params["scale_pos_weight"] = scale_pos_weight

            model = lgb.train(
                params=lgb_params,
                num_boost_round=params["num_boost_round"],
                train_set=train_data,
                valid_sets=[train_data, val_data],
                valid_names=["train", "val"],
                callbacks=[
                    lgb.early_stopping(
                        stopping_rounds=params["early_stopping_rounds"], verbose=False
                    ),
                    lgb.record_evaluation(evals_result),
                    tensorboard_callback,
                    lgb.log_evaluation(period=0),  # Disable evaluation logging
                ],
            )
        else:
            # Add sample weights to DMatrix for multiclass
            train_data = xgb.DMatrix(x_train, label=y_train, weight=sample_weight)
            val_data = xgb.DMatrix(x_val, label=y_val)

            class TensorBoardCallback(xgb.callback.TrainingCallback):

                def __init__(self, log_dir: str):
                    self.writer = SummaryWriter(log_dir=log_dir)

                def after_iteration(
                    self,
                    model,
                    epoch: int,
                    evals_log: xgb.callback.TrainingCallback.EvalsLog,
                ) -> bool:
                    if not evals_log:
                        return False

                    for data, metric in evals_log.items():
                        for metric_name, log in metric.items():
                            score = (
                                log[-1][0] if isinstance(log[-1], tuple) else log[-1]
                            )
                            self.writer.add_scalar(f"XGBoost/{data}", score, epoch)

                    return False

            tensorboard_callback = TensorBoardCallback(self.log_dir)

            loss = (
                "reg:squarederror"
                if self.target_type == "regression"
                else ("binary:logistic" if num_class <= 2 else "multi:softprob")
            )
            # Determine eval_metric based on optimization_metric or use defaults
            from lecrapaud.utils import get_eval_metric
            default_eval_metric = (
                "rmse"
                if self.target_type == "regression"
                else ("logloss" if num_class <= 2 else "mlogloss")
            )
            if self.optimization_metric:
                eval_metric = get_eval_metric(
                    self.optimization_metric, "xgboost", is_binary=(num_class <= 2)
                )
                if eval_metric is None:
                    eval_metric = default_eval_metric
            else:
                eval_metric = default_eval_metric
            # Build XGBoost params with scale_pos_weight for binary classification
            xgb_params = {
                **params["model_params"],
                "objective": loss,
                "eval_metric": eval_metric,
                "num_class": num_class,
            }
            if is_binary and self.use_class_weights:
                xgb_params["scale_pos_weight"] = scale_pos_weight

            # XGBoost verbosity already set globally
            model = xgb.train(
                params=xgb_params,
                num_boost_round=params["num_boost_round"],
                dtrain=train_data,
                evals=[(val_data, "val"), (train_data, "train")],
                callbacks=[
                    xgb.callback.EarlyStopping(
                        rounds=params["early_stopping_rounds"], save_best=True
                    ),
                    # Removed EvaluationMonitor to suppress logs
                    tensorboard_callback,
                ],
                evals_result=evals_result,  # Record evaluation result
                verbose_eval=False,  # Disable evaluation logging
            )

        self.model_name = self.create_model
        logger.debug(f"Successfully created a {self.model_name} at {datetime.now()}")

        # Close the writer after training is done
        writer.close()

        if self.plot:
            # Plot training progress
            plot_training_progress(
                logs={
                    "train": evals_result["train"][eval_metric],
                    "val": evals_result["val"][eval_metric],
                },
                model_name=self.model_name,
                target_number=self.target_number,
                title_suffix=f"Training Progress - {eval_metric}",
            )

        self._model = model

        return model

    def fit_recurrent(self, x_train, y_train, x_val, y_val, params):
        """Train a recurrent neural network (LSTM/GRU) model.

        Uses Keras/TensorFlow for training with early stopping and
        TensorBoard logging. Handles both regression and classification
        with automatic loss function selection.

        Args:
            x_train: Training features with shape (samples, timesteps, features).
            y_train: Training targets.
            x_val: Validation features.
            y_val: Validation targets.
            params: Dictionary with 'learning_rate', 'clipnorm', 'batch_size',
                   and 'epochs'.

        Returns:
            The trained Keras model.
        """
        import tensorflow as tf
        import keras
        from keras.callbacks import EarlyStopping, TensorBoard
        from keras.metrics import Precision, Recall
        from keras.losses import BinaryCrossentropy, CategoricalCrossentropy
        from keras.optimizers import Adam
        K = tf.keras.backend
        from lecrapaud.model_selection import plot_training_progress

        # metrics functions
        def rmse_tf(y_true, y_pred):
            y_true, y_pred = unscale_tf(y_true, y_pred)
            results = K.sqrt(K.mean(K.square(y_pred - y_true)))
            return results

        def mae_tf(y_true, y_pred):
            y_true, y_pred = unscale_tf(y_true, y_pred)
            results = K.mean(K.abs(y_pred - y_true))
            return results

        def unscale_tf(y_true, y_pred):
            if self.target_type == "regression":
                scale = K.constant(self.scaler_y.scale_[0])
                mean = K.constant(self.scaler_y.mean_[0])

                y_true = K.mul(y_true, scale)
                y_true = K.bias_add(y_true, mean)

                y_pred = K.mul(y_pred, scale)
                y_pred = K.bias_add(y_pred, mean)
            return y_true, y_pred

        # Create the model
        labels = np.unique(y_train[:, 0])
        num_class = labels.size if self.target_type == "classification" else None
        input_shape = (x_train.shape[1], x_train.shape[2])
        model = self.create_model(params, input_shape, self.target_type, num_class)

        # Compile the model
        loss = (
            rmse_tf
            if self.target_type == "regression"
            else (
                BinaryCrossentropy(from_logits=False)
                if num_class <= 2
                else CategoricalCrossentropy(from_logits=False)
            )
        )
        optimizer = Adam(
            learning_rate=params["learning_rate"], clipnorm=params["clipnorm"]
        )
        metrics = (
            [mae_tf]
            if self.target_type == "regression"
            else (
                ["accuracy", Precision(), Recall()]
                if num_class <= 2
                else ["categorical_accuracy"]
            )
        )
        model.compile(optimizer=optimizer, loss=loss, metrics=metrics)

        # Callbacks
        tensorboard_callback = TensorBoard(log_dir=self.log_dir)
        early_stopping_callback = EarlyStopping(
            monitor="val_loss",
            patience=3,
            restore_best_weights=True,
            start_from_epoch=5,
        )

        # Custom callbacks
        class PrintTrainableWeights(keras.callbacks.Callback):
            def on_epoch_end(self, epoch, logs={}):
                logger.info(model.trainable_variables)

        class GradientCalcCallback(keras.callbacks.Callback):
            def __init__(self):
                self.epoch_gradient = []

            def get_gradient_func(self, model):
                # grads = K.gradients(model.total_loss, model.trainable_weights)
                grads = K.gradients(model.loss, model.trainable_weights)
                # inputs = model.model.inputs + model.targets + model.sample_weights
                # use below line of code if above line doesn't work for you
                # inputs = model.model._feed_inputs + model.model._feed_targets + model.model._feed_sample_weights
                inputs = (
                    model._feed_inputs
                    + model._feed_targets
                    + model._feed_sample_weights
                )
                func = K.function(inputs, grads)
                return func

            def on_epoch_end(self, epoch, logs=None):
                get_gradient = self.get_gradient_func(model)
                grads = get_gradient([x_val, y_val[:, 0], np.ones(len(y_val[:, 0]))])
                self.epoch_gradient.append(grads)

        # Train the model
        # Compute class weights before transforming y_train (need original labels)
        class_weight_dict = None
        if self.target_type == "classification" and self.use_class_weights:
            from sklearn.utils.class_weight import compute_class_weight

            y_train_flat = y_train[:, 0].flatten()
            class_weights = compute_class_weight(
                "balanced", classes=np.unique(y_train_flat), y=y_train_flat
            )
            class_weight_dict = dict(enumerate(class_weights))

        if self.target_type == "classification" and num_class > 2:
            lb = LabelBinarizer(sparse_output=False)  # Change to True for sparse matrix
            lb.fit(labels)
            y_train = lb.transform(y_train[:, 0].flatten())
            y_val = lb.transform(y_val[:, 0].flatten())
        else:
            y_train = y_train[:, 0].flatten()
            y_val = y_val[:, 0].flatten()

        logger.debug("Fitting the model...")
        logger.debug(f"x_train shape: {x_train.shape}, x_val shape: {x_val.shape}")
        logger.debug(f"y_train shape: {y_train.shape}, y_val shape: {y_val.shape}")

        history = model.fit(
            x_train,
            y_train,
            batch_size=params["batch_size"],
            verbose=0,
            epochs=params["epochs"],
            shuffle=False,
            validation_data=(x_val, y_val),
            callbacks=[early_stopping_callback, tensorboard_callback],
            class_weight=class_weight_dict,
        )

        logger.debug(f"Successfully created a {self.model_name} at {datetime.now()}")
        # logger.info(pd.DataFrame(gradiant.epoch_gradient))

        if self.plot:
            # Plot training progress using the utility function
            plot_training_progress(
                logs=history.history,
                model_name=self.model_name,
                target_number=self.target_number,
            )

        self._model = model

        return model

    def predict(
        self,
        data: pd.DataFrame | np.ndarray,
        threshold: float = 0.5,
    ):
        """Function to get prediction from model. Support sklearn, keras and boosting models such as xgboost and lgboost

        Args:
            - data: the data for prediction
            - threshold: the threshold for classification
        """
        if not self._model:
            raise Exception(
                "Model is not fitted, cannot predict, run model.fit() first, or pass a fitted model when creating the Model object to the `model` parameter."
            )
        model = self._model

        if self.threshold and threshold == 0.5:
            threshold = self.threshold

        # Determine index for output
        if isinstance(data, pd.DataFrame):
            index = data.index
        elif isinstance(data, np.ndarray):
            index = pd.RangeIndex(start=0, stop=data.shape[0])
        else:
            raise ValueError(
                "Unsupported data type: expected pd.DataFrame or np.ndarray"
            )

        # Keras, LightGBM, XGBoost
        if self.recurrent or self.model_name in ["lgb", "xgb"]:
            if self.model_name == "xgb":
                import xgboost as xgb
                data_input = xgb.DMatrix(data)
                pred_raw = model.predict(data_input)
            else:
                pred_raw = model.predict(data)

            if pred_raw.ndim == 1:
                pred_raw = pred_raw.reshape(-1, 1)

            if self.target_type == "classification":
                num_class = pred_raw.shape[1] if pred_raw.ndim > 1 else 2
                if num_class <= 2:
                    pred_proba = pd.DataFrame(
                        {0: 1 - pred_raw.ravel(), 1: pred_raw.ravel()}, index=index
                    )
                else:
                    pred_proba = pd.DataFrame(
                        pred_raw, columns=range(num_class), index=index
                    )

                pred_df = apply_thresholds(pred_proba, threshold, pred_proba.columns)
            else:
                pred_df = pd.Series(pred_raw.ravel(), index=index, name="PRED")

        # Sklearn
        else:
            if self.target_type == "classification":
                pred_proba = pd.DataFrame(
                    model.predict_proba(data),
                    index=index,
                    columns=[
                        int(c) if isinstance(c, float) and c.is_integer() else c
                        for c in model.classes_
                    ],
                )
                pred_df = apply_thresholds(pred_proba, threshold, model.classes_)
            else:
                pred_df = pd.Series(model.predict(data), index=index, name="PRED")

        return pred_df

    def save(self, experiment_id=None, target_id=None, model_id=None):
        """Save model to database.

        Args:
            experiment_id: Experiment ID for database storage
            target_id: Target ID for database storage
            model_id: Model ID to link the model to its score
        """
        experiment_id = experiment_id or self.experiment_id
        target_id = target_id or self.target_id

        if not experiment_id or not target_id:
            raise ValueError("experiment_id and target_id are required to save model")

        if not model_id:
            raise ValueError("model_id is required to save model")

        # Use .keras extension for recurrent models, .best for others
        extension = ".keras" if self.recurrent else ".best"
        ArtifactService.save_model(
            experiment_id=experiment_id,
            target_id=target_id,
            model_name=f"{self.model_name}{extension}",
            model=self._model,
            model_id=model_id,
            is_keras=self.recurrent,
        )

    def _load_from_db(self):
        """Load model from database."""
        from lecrapaud.models import BestModel, Model, ModelType

        best_model_entry = BestModel.find_by(
            experiment_id=self.experiment_id,
            target_id=self.target_id,
        )
        if not best_model_entry:
            raise ValueError(
                f"No BestModel found for experiment_id={self.experiment_id}, "
                f"target_id={self.target_id}"
            )

        if self.model_name:
            # Load specific model by name and type
            model_type_record = ModelType.find_by(name=self.model_name, type=self.target_type)
            if not model_type_record:
                raise ValueError(f"ModelType '{self.model_name}' ({self.target_type}) not found in database")

            model_record = Model.find_by(
                model_type_id=model_type_record.id,
                best_model_id=best_model_entry.id,
            )
            if not model_record:
                raise ValueError(
                    f"No model found for '{self.model_name}' in this experiment"
                )

            model = ArtifactService.load_model_by_model_id(
                model_id=model_record.id,
            )
        else:
            # Load best model
            if not best_model_entry.model_id:
                raise ValueError(
                    f"No best model set for experiment_id={self.experiment_id}, "
                    f"target_id={self.target_id}"
                )

            best_model_record = Model.find_by(
                id=best_model_entry.model_id
            )
            if best_model_record and best_model_record.model_type:
                self.model_name = best_model_record.model_type.name

            model = ArtifactService.load_model_by_model_id(
                model_id=best_model_entry.model_id,
            )

        if model:
            self._model = model
            # Load threshold from database for classification
            if self.target_type == "classification":
                self.threshold = ArtifactService.load_thresholds(
                    experiment_id=self.experiment_id,
                    target_id=self.target_id,
                )
            logger.debug(
                f"Loaded model {self.model_name} from database"
            )
        else:
            raise ValueError(f"Could not load model from database (experiment_id={self.experiment_id}, target_id={self.target_id}, model_name={self.model_name})")


class Threshold(BaseModel):
    threshold: float
    precision: float
    recall: float
    f1: float


class Thresholds(BaseModel):
    thresholds: dict[str, Threshold]


def find_best_threshold(
    prediction: pd.DataFrame, metric: str = "recall", target_value: float | None = None
) -> Thresholds:
    """Find optimal classification thresholds for each class.

    Analyzes the precision-recall curve to find thresholds that optimize
    the specified metric, optionally with a minimum target value constraint.
    Supports both binary and multiclass classification.

    Args:
        prediction: DataFrame with 'TARGET' column and class probability columns.
        metric: Metric to optimize ('recall', 'precision', or 'f1').
        target_value: Minimum acceptable value for the metric. If None,
                     simply maximizes the metric.

    Returns:
        dict: Per-class dictionary with 'threshold', 'precision', 'recall',
              and 'f1' values.

    Example:
        >>> thresholds = find_best_threshold(predictions, metric="recall", target_value=0.9)
        >>> # Returns thresholds achieving at least 90% recall per class
    """
    def _normalize_class_label(cls):
        if isinstance(cls, (np.integer, int)):
            return int(cls)
        if isinstance(cls, (float, np.floating)) and cls.is_integer():
            return int(cls)
        if isinstance(cls, str):
            try:
                as_float = float(cls)
                if as_float.is_integer():
                    return int(as_float)
            except ValueError:
                pass
        return cls

    """
    General function to find best threshold optimizing recall, precision, or f1.

    Supports both binary and multiclass classification.

    Parameters:
    - prediction (pd.DataFrame): must contain 'TARGET' and class probability columns.
    - metric (str): 'recall', 'precision', or 'f1'.
    - target_value (float | None): minimum acceptable value for the chosen metric.

    Returns:
    - Thresholds: {class_label: {'threshold', 'precision', 'recall', 'f1'}}
    """
    assert metric in {"recall", "precision", "f1"}, "Invalid metric"
    y_true = prediction["TARGET"]
    pred_cols = [
        col for col in prediction.columns if col not in ["ID", "TARGET", "PRED"]
    ]
    classes = (
        [1]
        if len(pred_cols) <= 2
        else sorted({_normalize_class_label(cls) for cls in y_true.unique()}, key=str)
    )

    results = {}
    for raw_cls in classes:
        cls = _normalize_class_label(raw_cls)
        cls_str = str(cls)
        if cls_str not in prediction.columns and cls not in prediction.columns:
            logger.warning(f"Missing predicted probabilities for class '{cls}'")
            results[cls_str] = {
                "threshold": None,
                "precision": None,
                "recall": None,
                "f1": None,
            }
            continue

        # Binarize for one-vs-rest
        y_binary = (y_true == int(cls)).astype(int)
        y_scores = prediction[cls] if cls in prediction.columns else prediction[cls_str]

        precision, recall, thresholds = precision_recall_curve(y_binary, y_scores)
        precision, recall = precision[1:], recall[1:]  # Align with thresholds
        thresholds = thresholds

        f1 = 2 * (precision * recall) / (precision + recall + 1e-10)

        metric_values = {"precision": precision, "recall": recall, "f1": f1}

        values = metric_values[metric]

        if target_value is not None:
            if metric == "recall":
                # Only keep recall >= target
                valid_indices = [i for i, r in enumerate(recall) if r >= target_value]
                if valid_indices:
                    # Pick the highest threshold
                    best_idx = max(valid_indices, key=lambda i: thresholds[i])
                else:
                    logger.warning(
                        f"[Class {cls}] No threshold with recall ≥ {target_value}"
                    )
                    best_idx = int(np.argmax(recall))  # fallback

            elif metric == "precision":
                # Only keep precision ≥ target and recall > 0
                valid_indices = [
                    i
                    for i, (p, r) in enumerate(zip(precision, recall))
                    if p >= target_value and r > 0
                ]
                if valid_indices:
                    # Among valid ones, pick the one with highest recall
                    best_idx = max(valid_indices, key=lambda i: recall[i])
                else:
                    logger.warning(
                        f"[Class {cls}] No threshold with precision ≥ {target_value}"
                    )
                    # fallback: meilleure precision parmi ceux avec recall>0
                    cand = np.where(recall > 0)[0]
                    if cand.size:
                        best_idx = cand[int(np.argmax(precision[cand]))]
                        logger.warning(
                            f"[Class {cls}] Fallback to best precision with recall>0: "
                            f"idx={best_idx}, precision={precision[best_idx]:.4f}, recall={recall[best_idx]:.4f}"
                        )
                    else:
                        logger.error(f"[Class {cls}] No threshold achieves recall>0.")
                        best_idx = None

            elif metric == "f1":
                valid_indices = [i for i, val in enumerate(f1) if val >= target_value]
                if valid_indices:
                    best_idx = max(valid_indices, key=lambda i: f1[i])
                else:
                    logger.warning(
                        f"[Class {cls}] No threshold with f1 ≥ {target_value}"
                    )
                    best_idx = int(np.argmax(f1))  # fallback
        else:
            best_idx = int(np.argmax(values))  # no constraint, get best value

        if best_idx is None:
            results[cls_str] = {
                "threshold": None,
                "precision": None,
                "recall": None,
                "f1": None,
            }
            continue

        results[cls_str] = {
            "threshold": float(thresholds[best_idx]),
            "precision": float(precision[best_idx]),
            "recall": float(recall[best_idx]),
            "f1": float(f1[best_idx]),
        }

    # Log comprehensive summary
    summary_lines = [
        "",
        "-" * 60,
        "  THRESHOLD DETERMINATION SUMMARY",
        "-" * 60,
        f"  Optimization metric: {metric.upper()}",
        f"  Target constraint: {metric} ≥ {target_value}" if target_value else "  Target constraint: None (maximize metric)",
        "",
    ]

    for cls_str, res in results.items():
        if res["threshold"] is None:
            summary_lines.append(f"  Class {cls_str}: NO VALID THRESHOLD FOUND")
        else:
            # Determine why this threshold was chosen
            if target_value is not None:
                actual_value = res[metric]
                if actual_value >= target_value:
                    reason = f"✓ {metric}={actual_value:.4f} meets target ≥ {target_value}"
                else:
                    reason = f"✗ FALLBACK: best achievable {metric}={actual_value:.4f} < {target_value}"
            else:
                reason = f"maximizes {metric}"

            summary_lines.extend([
                f"  Class {cls_str}:",
                f"    Threshold: {res['threshold']:.4f}",
                f"    Precision: {res['precision']:.4f}",
                f"    Recall:    {res['recall']:.4f}",
                f"    F1:        {res['f1']:.4f}",
                f"    Reason:    {reason}",
                "",
            ])

    summary_lines.append("-" * 60)
    logger.info("\n".join(summary_lines))

    return results


def apply_thresholds(
    pred_proba: pd.DataFrame, threshold: Thresholds | float, classes
) -> pd.DataFrame:
    """
    Apply thresholds to predicted probabilities.

    Parameters:
    - pred_proba (pd.DataFrame): Probabilities per class.
    - threshold (Thresholds | float): Global threshold (float) or per-class dict from `find_best_threshold`.
    - classes (iterable): List or array of class labels (used for binary classification).

    Returns:
    - pd.DataFrame with "PRED" column and original predicted probabilities.
    """

    # Case 1: Per-class thresholds
    if not isinstance(threshold, (int, float)):
        if isinstance(threshold, str):
            threshold = ast.literal_eval(threshold)
        class_predictions = []
        class_probabilities = []

        for class_label, metrics in threshold.items():
            # Get threshold from structured dict
            _threshold = (
                metrics.get("threshold") if isinstance(metrics, dict) else metrics[0]
            )
            if _threshold is not None:
                class_label = int(class_label)
                if class_label not in pred_proba.columns:
                    continue  # skip missing class
                col = pred_proba[class_label]
                exceeded = col >= _threshold
                class_predictions.append(
                    pd.Series(
                        np.where(exceeded, class_label, -1), index=pred_proba.index
                    )
                )
                class_probabilities.append(
                    pd.Series(np.where(exceeded, col, -np.inf), index=pred_proba.index)
                )

        # For each row:
        # 1. If any threshold is exceeded, take the class with highest probability among exceeded
        # 2. If no threshold is exceeded, take the class with highest probability overall
        if class_predictions:
            preds_df = pd.concat(class_predictions, axis=1)
            probs_df = pd.concat(class_probabilities, axis=1)

            def select_class(row_pred, row_prob, row_orig):
                exceeded = row_pred >= 0
                if exceeded.any():
                    return row_pred.iloc[row_prob.argmax()]
                return row_orig.idxmax()

            pred = pd.Series(
                [
                    select_class(
                        preds_df.loc[idx], probs_df.loc[idx], pred_proba.loc[idx]
                    )
                    for idx in pred_proba.index
                ],
                index=pred_proba.index,
                name="PRED",
            )
        else:
            # fallback: take max probability if no thresholds apply
            pred = pred_proba.idxmax(axis=1).rename("PRED")

    # Case 2: Global scalar threshold (e.g., 0.5 for binary)
    else:
        if len(classes) == 2:
            # Binary classification: threshold on positive class
            pos_class = classes[1]
            pred = (pred_proba[pos_class] >= threshold).astype(int).rename("PRED")
        else:
            # Multiclass: default to max probability
            pred = pred_proba.idxmax(axis=1).rename("PRED")

    return pd.concat([pred, pred_proba], axis=1)


def plot_threshold(prediction, threshold, precision, recall):
    y_pred_proba = prediction[1] if 1 in prediction.columns else prediction["1"]
    y_true = prediction["TARGET"]

    predicted_positive = (y_pred_proba >= threshold).sum()
    predicted_negative = (y_pred_proba < threshold).sum()
    f1_scores = 2 * (precision * recall) / (precision + recall + 1e-10)
    per_predicted_positive = predicted_positive / len(y_pred_proba)
    per_predicted_negative = predicted_negative / len(y_pred_proba)

    print(
        f"""Threshold: {threshold*100:.2f}
        Precision: {precision*100:.2f}
        Recall: {recall*100:.2f}
        F1-score: {f1_scores*100:.2f}
        % of score over {threshold}: {predicted_positive}/{len(y_pred_proba)} = {per_predicted_positive*100:.2f}%
        % of score under {threshold}: {predicted_negative}/{len(y_pred_proba)} = {per_predicted_negative*100:.2f}%"""
    )

    # Visualizing the scores of positive and negative classes
    plt.figure(figsize=(10, 6))
    sns.histplot(
        y_pred_proba[y_true == 1],
        color="blue",
        label="Positive Class",
        bins=30,
        kde=True,
        alpha=0.6,
    )
    sns.histplot(
        y_pred_proba[y_true == 0],
        color="red",
        label="Negative Class",
        bins=30,
        kde=True,
        alpha=0.6,
    )
    plt.axvline(
        x=threshold,
        color="green",
        linestyle="--",
        label=f"Threshold at {round(threshold, 3)}",
    )
    plt.title("Distribution of Predicted Probabilities")
    plt.xlabel("Predicted Probabilities")
    plt.ylabel("Frequency")
    plt.legend()
    plt.show()
    return threshold
