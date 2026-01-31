import pandas as pd
import numpy as np
from typing import Optional

from sklearn.preprocessing import StandardScaler

from lecrapaud.utils import logger, validate_no_nan_inf
from lecrapaud.search_space import all_models
from lecrapaud.mixins import LeCrapaudTransformerMixin
from lecrapaud.models import Experiment
from lecrapaud.services import ArtifactService


class ModelPreprocessor(LeCrapaudTransformerMixin):
    """Model preprocessing pipeline for feature scaling.

    This class handles feature scaling (StandardScaler) for models that require
    normalized inputs (e.g., neural networks, SVM). It automatically determines
    whether scaling is needed based on the models being used.

    Args:
        experiment: LeCrapaud experiment instance for context and artifact storage.
        **kwargs: Additional configuration parameters that override experiment context.
            - target_numbers: List of target numbers to process.
            - target_clf: List of classification target numbers.
            - models_idx: List of model indices to train.

    Attributes:
        scaler_x_: Fitted StandardScaler for features.
        scalers_y_: Dict of fitted scalers for regression targets.
        need_scaling_: Whether scaling is needed for the configured models.
        all_features: List of all feature names to use.

    Example:
        >>> from lecrapaud import ModelPreprocessor
        >>> mp = ModelPreprocessor(experiment=experiment)
        >>> mp.fit(train_data)
        >>> scaled_data = mp.transform(test_data)
    """

    def __init__(
        self,
        experiment=None,
        **kwargs,
    ):
        # The mixin will set defaults from DEFAULT_PARAMS, then experiment.context, then kwargs
        super().__init__(experiment=experiment, **kwargs)

        # Set experiment ID if experiment is available
        if self.experiment:
            self.experiment_id = self.experiment.id
            self.all_features = self.experiment.get_all_features(
                date_column=self.date_column, group_column=self.group_column
            )

    def fit(self, X, y=None):
        """
        Fit the model preprocessor (learns scaling parameters).

        Args:
            X (pd.DataFrame): Training data
            y: Target values (ignored)

        Returns:
            self: Returns self for chaining
        """
        X, y = self._validate_data(X, y)

        # Filter columns to keep only features and targets
        if hasattr(self, "all_features"):
            columns_to_keep = self.all_features + [
                f"TARGET_{i}" for i in self.target_numbers
            ]
            duplicates = [
                col for col in set(columns_to_keep) if columns_to_keep.count(col) > 1
            ]
            if duplicates:
                raise ValueError(
                    f"Doublons détectés dans columns_to_keep: {duplicates}"
                )
            X = X[columns_to_keep]

        # Determine if we need scaling
        self.need_scaling_ = any(
            t not in self.target_clf for t in self.target_numbers
        ) and any(all_models[i].get("need_scaling") for i in self.models_idx)

        if self.need_scaling_:
            logger.debug("Fitting scalers...")
            _, self.scaler_x_, self.scalers_y_ = self.scale_data(X)

            # Save scalers if experiment is available
            if self.experiment:
                ArtifactService.save_scaler(
                    experiment_id=self.experiment_id,
                    scaler_name="scaler_x",
                    scaler=self.scaler_x_,
                )
                # Save target scalers
                for target_number in self.target_numbers:
                    if target_number not in self.target_clf:
                        # Get target_id for this target
                        target = next(
                            (t for t in self.experiment.targets if t.name == f"TARGET_{target_number}"),
                            None
                        )
                        target_id = target.id if target else None
                        scaler_y = self.scalers_y_[f"scaler_y_{target_number}"]
                        ArtifactService.save_scaler(
                            experiment_id=self.experiment_id,
                            scaler_name=f"scaler_y_{target_number}",
                            scaler=scaler_y,
                            target_id=target_id,
                        )

        self._set_fitted()
        self.data = X

        # Validate no NaN or Inf values remain after preprocessing
        validate_no_nan_inf(self.data, "model preprocessing (scaling)")

        return self

    def get_data(self):
        """
        Get the transformed data after model preprocessing.

        Returns:
            pd.DataFrame: The transformed data
        """
        self._check_is_fitted()
        return self.data

    def transform(self, X):
        """
        Transform the input data (apply scaling if fitted).

        Args:
            X (pd.DataFrame): Input data

        Returns:
            pd.DataFrame: Scaled data (or original if no scaling needed)
        """
        # Compute need_scaling_ if not already set
        if not hasattr(self, "need_scaling_"):
            from lecrapaud.search_space import all_models as models_config
            self.need_scaling_ = any(
                t not in self.target_clf for t in self.target_numbers
            ) and any(models_config[i].get("need_scaling") for i in self.models_idx)

        # No scaling needed - return X directly
        if not self.need_scaling_:
            return X

        # Filter columns if needed (only keep TARGET columns that exist)
        if hasattr(self, "all_features"):
            columns_to_keep = self.all_features + [
                f"TARGET_{i}" for i in self.target_numbers if f"TARGET_{i}" in X.columns
            ]
            X = X[columns_to_keep]

        # Allow loading persisted artifacts even in a fresh instance
        if not getattr(self, "is_fitted_", False) and self.experiment:
            scaler = ArtifactService.load_scaler(
                experiment_id=self.experiment_id,
                scaler_name="scaler_x",
            )
            if scaler is not None:
                self.scaler_x_ = scaler
                self.is_fitted_ = True

        self._check_is_fitted()
        X, _ = self._validate_data(X, reset=False)

        # Load scalers if not in memory
        if not hasattr(self, "scaler_x_") and self.experiment:
            self.scaler_x_ = ArtifactService.load_scaler(
                experiment_id=self.experiment_id,
                scaler_name="scaler_x",
            )

        # Apply scaling
        if hasattr(self, "scaler_x_") and self.scaler_x_ is not None:
            X_scaled, _, _ = self.scale_data(
                X, scaler_x=self.scaler_x_, scalers_y=getattr(self, "scalers_y_", None)
            )
            return X_scaled

        return X

    # scaling
    def scale_data(
        self,
        df: pd.DataFrame,
        scaler_x=None,
        scalers_y: Optional[list] = None,
    ):
        logger.debug("Scale data...")
        X = df.loc[:, ~df.columns.str.contains("^TARGET_")]

        if scaler_x:
            # Ensure columns are in the same order as when the scaler was fitted
            if hasattr(scaler_x, "feature_names_in_"):
                X = X[scaler_x.feature_names_in_]
            X_scaled = pd.DataFrame(
                scaler_x.transform(X), columns=list(X.columns), index=X.index
            )
        else:
            scaler_x = StandardScaler()  # MinMaxScaler(feature_range=(-1,1))
            X_scaled = pd.DataFrame(
                scaler_x.fit_transform(X), columns=list(X.columns), index=X.index
            )

        # Determine which targets need to be scaled (only if they exist in df)
        targets_numbers_to_scale = [
            i for i in self.target_numbers
            if i not in self.target_clf and f"TARGET_{i}" in df.columns
        ]

        # Dictionary to store scaled target data
        scaled_targets = {}

        if scalers_y and targets_numbers_to_scale:
            for target_number in targets_numbers_to_scale:
                y = df[[f"TARGET_{target_number}"]]
                scaled_targets[target_number] = pd.DataFrame(
                    scalers_y[f"scaler_y_{target_number}"].transform(y.values),
                    columns=y.columns,
                    index=y.index,
                )
        elif targets_numbers_to_scale:
            scalers_y = {}
            for target_number in targets_numbers_to_scale:
                scaler_y = StandardScaler()
                y = df[[f"TARGET_{target_number}"]]

                scaled_y = pd.DataFrame(
                    scaler_y.fit_transform(y.values),
                    columns=y.columns,
                    index=y.index,
                )
                # Note: Scalers are saved in the fit() method via ArtifactService

                scalers_y[f"scaler_y_{target_number}"] = scaler_y
                scaled_targets[target_number] = scaled_y

        # Reconstruct y_scaled in the original order
        if scaled_targets:
            y_scaled = pd.concat(
                [
                    scaled_targets[target_number]
                    for target_number in targets_numbers_to_scale
                ],
                axis=1,
            )
        else:
            y_scaled = pd.DataFrame(index=df.index)

        y_not_scaled = df[
            df.columns.intersection([f"TARGET_{i}" for i in self.target_clf])
        ]

        # Build final dataframe - keep scaler's feature order, then add targets
        parts_to_concat = [X_scaled]
        if not y_scaled.empty:
            parts_to_concat.append(y_scaled)
        if not y_not_scaled.empty:
            parts_to_concat.append(y_not_scaled)
        df_scaled = pd.concat(parts_to_concat, axis=1)

        return df_scaled, scaler_x, scalers_y


# Reshape into 3D tensors for recurrent models
def reshape_time_series(
    experiment: Experiment,
    features: list,
    train: pd.DataFrame,
    val: pd.DataFrame = None,
    test: pd.DataFrame = None,
    timesteps: int = 120,
):
    # always scale for recurrent layers : train should be scaled
    group_column = experiment.context.group_column

    target_columns = train.columns.intersection(
        [f"TARGET_{i}" for i in experiment.context.target_numbers]
    )

    data = pd.concat([train, val, test], axis=0)

    def reshape_df(df: pd.DataFrame, group_series: pd.Series, timesteps: int):
        fill_value = [[[0] * len(df.columns)]]

        def shiftsum(x, timesteps: int):
            tmp = x.copy()
            for i in range(1, timesteps):
                tmp = x.shift(i, fill_value=fill_value) + tmp
            return tmp

        logger.info("Grouping each feature in a unique column with list...")
        df_reshaped = df.apply(list, axis=1).apply(lambda x: [list(x)])
        df_reshaped = pd.concat([df_reshaped, group_series], axis=1)

        logger.info("Grouping features and creating timesteps...")
        df_reshaped = (
            df_reshaped.groupby(group_column)[0]
            .apply(lambda x: shiftsum(x, timesteps))
            .reset_index(group_column, drop=True)
            .rename("RECURRENT_FEATURES")
        )
        df_reshaped = pd.DataFrame(df_reshaped)

        return df_reshaped

    data_reshaped = reshape_df(data[features], data[group_column], timesteps)

    data_reshaped[target_columns] = data[target_columns]

    logger.info("Separating train, val, test data and creating np arrays...")
    train_reshaped = data_reshaped.loc[train.index]

    x_train_reshaped = np.array(train_reshaped["RECURRENT_FEATURES"].values.tolist())
    y_train_reshaped = np.array(train_reshaped[target_columns].reset_index())

    reshaped_data = {
        "x_train_reshaped": x_train_reshaped,
        "y_train_reshaped": y_train_reshaped,
    }

    if val is not None:
        val_reshaped = data_reshaped.loc[val.index]
        x_val_reshaped = np.array(val_reshaped["RECURRENT_FEATURES"].values.tolist())
        y_val_reshaped = np.array(val_reshaped[target_columns].reset_index())
        reshaped_data["x_val_reshaped"] = x_val_reshaped
        reshaped_data["y_val_reshaped"] = y_val_reshaped

    if test is not None:
        test_reshaped = data_reshaped.loc[test.index]
        x_test_reshaped = np.array(test_reshaped["RECURRENT_FEATURES"].values.tolist())
        y_test_reshaped = np.array(test_reshaped[target_columns].reset_index())
        reshaped_data["x_test_reshaped"] = x_test_reshaped
        reshaped_data["y_test_reshaped"] = y_test_reshaped

    return reshaped_data
