import pandas as pd
import numpy as np
from datetime import timedelta
import matplotlib.pyplot as plt
import seaborn as sns
import os
import time
from tqdm import tqdm
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

# feature selection
from sklearn.feature_selection import (
    f_classif,
    f_regression,
    mutual_info_classif,
    mutual_info_regression,
    chi2,
    SelectPercentile,
    SelectFpr,
    RFE,
    SelectFromModel,
)
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from xgboost import XGBClassifier, XGBRegressor
from sklearn.model_selection import TimeSeriesSplit, train_test_split
from sklearn.metrics import (
    root_mean_squared_error,
    log_loss,
    make_scorer,
    roc_auc_score,
)
from mlxtend.feature_selection import SequentialFeatureSelector
from scipy.stats import spearmanr, kendalltau

# Internal
from lecrapaud.directories import tmp_dir
from lecrapaud.utils import logger
from lecrapaud.config import PYTHON_ENV
from lecrapaud.models import (
    Experiment,
    Target,
    Feature,
    FeatureType,
    FeatureSelection,
    FeatureSelectionRank,
    FeatureSelectionMethod,
)
from lecrapaud.search_space import all_models
from lecrapaud.mixins import LeCrapaudEstimatorMixin
from lecrapaud.services import ArtifactService

# Annoying Warnings
warnings.filterwarnings("ignore", category=FutureWarning)


def load_train_data(experiment_id: int):
    """Load train, val, test data from database via ArtifactService."""
    logger.info("Loading data...")
    train = ArtifactService.load_dataframe(experiment_id=experiment_id, data_type="train")
    val = ArtifactService.load_dataframe(experiment_id=experiment_id, data_type="val")
    test = ArtifactService.load_dataframe(experiment_id=experiment_id, data_type="test")

    train_scaled = ArtifactService.load_dataframe(experiment_id=experiment_id, data_type="train_scaled")
    val_scaled = ArtifactService.load_dataframe(experiment_id=experiment_id, data_type="val_scaled")
    test_scaled = ArtifactService.load_dataframe(experiment_id=experiment_id, data_type="test_scaled")

    return train, val, test, train_scaled, val_scaled, test_scaled


class FeatureSelector(LeCrapaudEstimatorMixin):
    """Feature selection using an ensemble of statistical and model-based methods.

    This class performs feature selection using multiple methods (Chi2, ANOVA,
    Pearson/Spearman correlation, Mutual Information, Feature Importance, RFE, PCA)
    and combines their rankings to select the most relevant features.

    Args:
        experiment: LeCrapaud experiment instance for context and artifact storage.
        target_number: Target number (1-indexed) for which to select features.
        **kwargs: Additional configuration parameters that override experiment context.
            - percentile: Percentage of features to keep per method (default: 20).
            - corr_threshold: Maximum correlation threshold between features (default: 80).
            - max_features: Maximum number of features to keep (None = auto).
            - max_p_value: P-value threshold for statistical tests (default: 0.05).
            - min_correlation: Minimum correlation magnitude (default: 0.1).
            - cumulative_importance: Cumulative threshold for MI/FI (default: 0.80).
            - auto_select_feature_count: Auto-optimize feature count (default: True).

    Attributes:
        selected_features_: List of selected feature names after fit().
        target_type: 'classification' or 'regression' based on target_clf.

    Example:
        >>> from lecrapaud import FeatureSelector
        >>> fs = FeatureSelector(experiment=experiment, target_number=1)
        >>> fs.fit(preprocessed_data)
        >>> features = fs.get_selected_features()
    """
    def __init__(self, experiment=None, target_number=None, **kwargs):
        # The mixin will set defaults from DEFAULT_PARAMS, then experiment.context, then kwargs
        super().__init__(experiment=experiment, **kwargs)

        self.target_number = target_number

        # Derived attributes
        if self.target_number is not None and hasattr(self, "target_clf"):
            self.target_type = (
                "classification"
                if self.target_number in self.target_clf
                else "regression"
            )

        # Set experiment ID if experiment is available
        if self.experiment:
            self.experiment_id = self.experiment.id

    # Main feature selection function
    def fit(self, X, y=None, single_process=True):
        """
        Fit the feature selector.

        Args:
            X (pd.DataFrame): Input features
            y: Target values (ignored, uses TARGET columns in X)
            single_process (bool): if True, run all feature selection methods in a single process

        Returns:
            self: Returns self for chaining (sklearn convention)
        """
        # Validate data
        X, y = self._validate_data(X, y)

        # Store train data
        self.train = X

        # Check that target_number is set
        if self.target_number is None:
            raise ValueError("target_number must be set before fitting")

        target_number = self.target_number
        target_type = self.target_type

        # Create the feature selection in db
        target = Target.find_by(name=f"TARGET_{target_number}")
        self.target_id = target.id  # Store target_id for use in selection methods
        percentile = self.percentile
        corr_threshold = self.corr_threshold
        max_features = self.max_features

        feature_selection = FeatureSelection.upsert(
            target_id=target.id,
            experiment_id=self.experiment_id,
        )
        feature_map = {f.name: f.id for f in Feature.get_all(limit=20000)}

        # Check if features already exist in database
        existing_features = ArtifactService.load_features(
            experiment_id=self.experiment_id,
            target_id=target.id,
        )
        if existing_features:
            return existing_features

        self.X = self.train.loc[:, ~self.train.columns.str.contains("^TARGET_")]
        self.y = self.train[f"TARGET_{target_number}"]

        logger.info(f"  Processing TARGET_{target_number} ({target_type})...")

        # Let's start by removing very low variance feature and extremly correlated features
        # This is needed to reduce nb of feature but also for methods such as anova or chi2 that requires independent, non constant, non full 0 features
        self.X = self.remove_low_variance_columns()
        features_uncorrelated, features_correlated = self.remove_correlated_features(
            90, vizualize=False
        )
        self.X = self.X[features_uncorrelated]

        logger.debug(
            f"""
            \nWe first have removed {len(features_correlated)} features with correlation greater than 90%
            \nWe are looking to capture {percentile}% of {len(self.X.columns)} features, i.e. {int(len(self.X.columns)*percentile/100)} features, with different feature selection methods
            \nWe will then remove above {corr_threshold}% correlated features, keeping the one with the best ranks
            \nFinally, we will keep only the best ranked features (max_features={max_features or 'auto'})
            """
        )

        start = time.time()

        # handling categorical features (only if classification)
        self.X_categorical, self.X_numerical = get_features_by_types(self.X)

        # Initialize to empty list - will be populated if categorical features exist
        categorical_features_selected = []

        if target_type == "classification" and self.X_categorical.shape[1] > 0:
            feat_scores = self.select_categorical_features(percentile=percentile)
            rows = []
            for row in feat_scores.itertuples(index=False):
                feature_id = feature_map.get(row.features)

                rows.append(
                    {
                        "feature_selection_id": feature_selection.id,
                        "feature_id": feature_id,
                        "method": row.method,
                        "score": None if pd.isna(row.score) else row.score,
                        "pvalue": None if pd.isna(row.pvalue) else row.pvalue,
                        "support": row.support,
                        "rank": None if pd.isna(row.rank) else row.rank,
                        "training_time": row.training_time,
                    }
                )

            if len(rows) == 0:
                logger.warning(
                    f"No categorical features selected for TARGET_{target_number}"
                )

            FeatureSelectionRank.bulk_upsert(rows=rows)

            categorical_features_selected = feat_scores[feat_scores["support"]][
                "features"
            ].values.tolist()

        results = []
        params = {"percentile": percentile}
        if single_process:
            results = [
                self.select_feature_by_linear_correlation(**params),
                self.select_feature_by_nonlinear_correlation(**params),
                self.select_feature_by_mi(**params),
                self.select_feature_by_feat_imp(**params),
                self.select_feature_by_rfe(**params),
                self.select_feature_by_pca(**params),
                # self.select_feature_by_sfs(
                #     **params
                # ), # TODO: this is taking too long
            ]
        else:
            # Use ProcessPoolExecutor to run tasks in parallel
            # TODO: not sure it's efficient from previous tests... especially because rfe and sfs methods are doing parallel processing already, this can create overhead
            with ProcessPoolExecutor() as executor:
                # Submit different functions to be executed in parallel
                futures = [
                    executor.submit(
                        self.select_feature_by_linear_correlation,
                        **params,
                    ),
                    executor.submit(
                        self.select_feature_by_nonlinear_correlation,
                        **params,
                    ),
                    executor.submit(
                        self.select_feature_by_mi,
                        **params,
                    ),
                    executor.submit(
                        self.select_feature_by_feat_imp,
                        **params,
                    ),
                    executor.submit(
                        self.select_feature_by_rfe,
                        **params,
                    ),
                    executor.submit(
                        self.select_feature_by_pca,
                        **params,
                    ),
                    # executor.submit(
                    #     self.select_feature_by_sfs,
                    #     **params,
                    # ),  # TODO: this is taking too long
                ]

                # Wait for all futures to complete and gather the results
                with tqdm(total=len(futures)) as pbar:
                    for future in as_completed(futures):
                        results.append(future.result())
                        pbar.update(1)

        logger.info(f"Finished feature selection for target {target_number}")

        stop = time.time()

        # Once all tasks are completed, start by inserting results to db
        feat_scores = pd.concat(
            results,
            axis=0,
        )

        logger.debug("Inserting feature selection results to db...")
        rows = []
        for row in feat_scores.itertuples(index=False):
            feature_id = feature_map.get(row.features)

            rows.append(
                {
                    "feature_selection_id": feature_selection.id,
                    "feature_id": feature_id,
                    "method": row.method,
                    "score": None if pd.isna(row.score) else row.score,
                    "pvalue": None if pd.isna(row.pvalue) else row.pvalue,
                    "support": row.support,
                    "rank": None if pd.isna(row.rank) else row.rank,
                    "training_time": row.training_time,
                }
            )

        if len(rows) == 0:
            logger.warning(f"No numerical features selected for TARGET_{target_number}")

        FeatureSelectionRank.bulk_upsert(rows=rows)

        # Merge the results
        logger.debug("Merging feature selection methods...")
        features_selected = feat_scores[feat_scores["support"]][["features", "rank"]]
        features_selected.sort_values("rank", inplace=True)
        features_selected.drop_duplicates("features", inplace=True)

        features_selected_list = features_selected["features"].values.tolist()

        # Save ensemble features for all numerical features with global ranking
        logger.debug("Saving ensemble features with global ranking...")
        numerical_features_in_data = self.X_numerical.columns.tolist()
        ensemble_rows = []

        # Create global ranking for ALL numerical features (1 to n, no null values)
        all_numerical_scores = pd.concat(results, axis=0)
        all_numerical_scores = (
            all_numerical_scores.groupby("features")
            .agg({"rank": "mean"})  # Average rank across all methods
            .reset_index()
        )
        all_numerical_scores.sort_values("rank", inplace=True)
        all_numerical_scores["global_rank"] = range(1, len(all_numerical_scores) + 1)

        for feature in numerical_features_in_data:
            feature_id = feature_map.get(feature)
            if feature_id:
                is_selected = feature in features_selected_list

                # Get global rank (no null values - all features get a rank)
                if feature in all_numerical_scores["features"].values:
                    global_rank = all_numerical_scores[
                        all_numerical_scores["features"] == feature
                    ]["global_rank"].values[0]
                else:
                    # Fallback: assign last rank + position for features not in results
                    global_rank = (
                        len(all_numerical_scores)
                        + numerical_features_in_data.index(feature)
                        + 1
                    )

                ensemble_rows.append(
                    {
                        "feature_selection_id": feature_selection.id,
                        "feature_id": feature_id,
                        "method": FeatureSelectionMethod.ENSEMBLE.value,
                        "score": None,
                        "pvalue": None,
                        "support": (
                            2 if is_selected else 0
                        ),  # 2 = in aggregated features
                        "rank": global_rank,
                        "training_time": 0,
                    }
                )

        FeatureSelectionRank.bulk_upsert(rows=ensemble_rows)

        # analysis 1
        features_selected_by_every_methods = set(results[0]["features"].values.tolist())
        for df in results[1:]:
            features_selected_by_every_methods &= set(
                df["features"].values.tolist()
            )  # intersection
        features_selected_by_every_methods = list(features_selected_by_every_methods)
        logger.debug(
            f"We selected {len(features_selected_list)} features and {len(features_selected_by_every_methods)} were selected unanimously:"
        )
        logger.debug(features_selected_by_every_methods)
        # Save features before correlation removal to database
        ArtifactService.save_dataframe(
            experiment_id=self.experiment_id,
            data_type="features_before_corr",
            df=pd.DataFrame({"features": features_selected_list}),
            target_id=self.target_id,
        )

        # removing correlated features
        self.X = self.X[features_selected_list]
        features, features_correlated = self.remove_correlated_features(corr_threshold)
        # Save features before max limitation to database
        ArtifactService.save_dataframe(
            experiment_id=self.experiment_id,
            data_type="features_before_max",
            df=pd.DataFrame({"features": features}),
            target_id=self.target_id,
        )

        # Update support for features after correlation removal (before max)
        logger.debug("Updating ensemble features after correlation removal...")
        for row in ensemble_rows:
            feature = Feature.get(row["feature_id"]).name
            if feature in features:
                row["support"] = 1  # 1 = survived correlation removal

        # Determine optimal feature count
        if self.auto_select_feature_count:
            logger.debug("Auto-selecting optimal feature count...")
            optimal_count = self._find_optimal_feature_count(features)
            features = features[:optimal_count]
        else:
            # Compute max_features if not specified
            from lecrapaud.utils import get_feature_search_range
            n_samples = len(self.X)
            _, computed_max = get_feature_search_range(
                n_samples=n_samples,
                n_available_features=len(features),
                max_features=max_features,
            )
            logger.info(f"Using max_features={computed_max} (n_samples={n_samples})...")
            features = features[:computed_max]

        # adding categorical features selected
        features += (
            categorical_features_selected if target_type == "classification" else []
        )

        # Final update for features after max limitation (final selection)
        logger.debug("Finalizing ensemble features...")
        for row in ensemble_rows:
            feature = Feature.get(row["feature_id"]).name
            if feature in features and row["support"] == 1:
                row["support"] = 2  # 2 = in final selection

        # Re-save all ensemble data with updated support values
        FeatureSelectionRank.bulk_upsert(rows=ensemble_rows)
        logger.debug(
            f"Final pre-selection: {len(features)} features below {corr_threshold}% out of {len(features_selected_list)} features, and rejected {len(features_correlated)} features, {100*len(features)/len(features_selected_list):.2f}% features selected"
        )

        # Save final selected features to database
        ArtifactService.save_dataframe(
            experiment_id=self.experiment_id,
            data_type="features_final",
            df=pd.DataFrame({"features": features}),
            target_id=self.target_id,
        )

        # analysis 2
        features_selected_by_every_methods_uncorrelated = list(
            set(features) & set(features_selected_by_every_methods)
        )
        logger.debug(
            f"In this pre-selection, there is {len(features_selected_by_every_methods_uncorrelated)} features from the {len(features_selected_by_every_methods)} selected unanimously\n"
        )
        logger.debug(
            features_selected[
                features_selected["features"].isin(features)
            ].to_markdown()
        )

        # Save features to database via ArtifactService
        ArtifactService.save_features(
            experiment_id=self.experiment_id,
            target_id=target.id,
            features=features,
        )

        # save in db feature selection relationship
        db_features = Feature.filter(name__in=features)
        # Order matters, to keep the same order in db as in features, we need: map features by name
        feature_by_name = {f.name: f for f in db_features}
        # Reorder them according to original `features` list
        ordered_db_features = [
            feature_by_name[name] for name in features if name in feature_by_name
        ]

        feature_selection = FeatureSelection.get(feature_selection.id)
        feature_selection = feature_selection.add_features(ordered_db_features)
        feature_selection.training_time = stop - start
        feature_selection.save()

        # Log comprehensive summary
        n_numerical = len([f for f in features if f not in categorical_features_selected])
        n_categorical = len([f for f in features if f in categorical_features_selected])
        summary_lines = [
            "",
            "-" * 60,
            f"  FEATURE SELECTION COMPLETE - TARGET_{target_number}",
            "-" * 60,
            f"  Target type: {target_type}",
            f"  Method: {'auto-optimized' if self.auto_select_feature_count else 'fixed max_features'}",
            "",
            f"  Features selected: {len(features)}",
            f"    - Numerical:    {n_numerical}",
            f"    - Categorical:  {n_categorical}",
            "",
            f"  Selection process:",
            f"    - Initial features:     {len(self.X.columns)}",
            f"    - After correlation <{corr_threshold}%: {len(features_uncorrelated)}",
            f"    - Final selection:      {len(features)}",
            "",
            f"  Time: {stop - start:.1f}s",
            "-" * 60,
        ]
        logger.info("\n".join(summary_lines))

        # Store selected features for later access
        self.selected_features_ = features
        self._set_fitted()
        return self

    def get_selected_features(self):
        """
        Get the list of selected features after fitting.

        Returns:
            list: Selected feature names
        """
        self._check_is_fitted()
        return self.selected_features_

    # Remove correlation
    # ------------------

    def remove_low_variance_columns(self, threshold: float = 1e-10) -> pd.DataFrame:
        """
        Removes columns with very low variance (including constant columns).

        Parameters:
            threshold (float): Minimum variance required to keep a column.
                            Default is 1e-10 to eliminate near-constant features.

        Returns:
            pd.DataFrame: Cleaned DataFrame without low-variance columns.
        """
        X = self.X

        low_var_cols = [
            col
            for col in X.columns
            if pd.api.types.is_numeric_dtype(X[col])
            and np.nanvar(X[col].values) < threshold
        ]

        if low_var_cols:
            logger.info(f"🧹 Removed {len(low_var_cols)} low-variance columns:")
            logger.info(low_var_cols)

        return X.drop(columns=low_var_cols, errors="ignore")

    def remove_correlated_features(self, corr_threshold: int, vizualize: bool = False):
        X = self.X
        features = X.columns
        # Create correlation matrix, select upper triangle & remove features with correlation greater than threshold
        corr_matrix = X[features].corr().abs()

        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        features_uncorrelated = [
            column
            for column in upper.columns
            if all(upper[column].dropna() <= corr_threshold / 100)
        ]
        features_correlated = [
            column
            for column in upper.columns
            if any(upper[column] > corr_threshold / 100)
        ]

        if vizualize:
            features_selected_visualization = (
                X[features]
                .corr()
                .where(np.triu(np.ones(len(features)), k=1).astype(bool))
                .fillna(0)
            )
            # Plot the heatmap
            plt.figure(figsize=(10, 8))
            sns.heatmap(
                corr_matrix,
                annot=True,
                cmap="coolwarm",
                center=0,
                linewidths=1,
                linecolor="black",
            )
            plt.title(f"Correlation Matrix")
            plt.show()

            logger.info(f"\n{features_selected_visualization.describe().to_string()}")
            logger.info(f"\n{features_selected_visualization.to_string()}")
        return features_uncorrelated, features_correlated

    # Auto feature count selection
    # ----------------------------

    def _find_optimal_feature_count(self, features_ranked: list) -> int:
        """
        Find the optimal number of features by testing different counts
        and evaluating on a validation set using the configured optimization metric.

        Args:
            features_ranked: List of feature names sorted by rank (best first)

        Returns:
            int: Optimal number of features
        """
        from sklearn.metrics import (
            log_loss,
            accuracy_score,
            precision_score,
            recall_score,
            f1_score,
            average_precision_score,
            mean_absolute_error,
            mean_absolute_percentage_error,
            r2_score,
        )
        from lecrapaud.utils import (
            get_default_metric,
            get_initial_best_score,
            is_metric_better,
            validate_metric_for_target_type,
        )

        X = self.X[features_ranked]
        y = self.y

        # Determine optimization metric for this target
        optimization_metric = getattr(self, "optimization_metric", {})
        if isinstance(optimization_metric, dict) and self.target_number in optimization_metric:
            metric = optimization_metric[self.target_number]
        elif isinstance(optimization_metric, str):
            metric = optimization_metric
        else:
            metric = get_default_metric(self.target_type)
        validate_metric_for_target_type(metric, self.target_type)

        # Split into train_sub and validation
        X_train_sub, X_val, y_train_sub, y_val = train_test_split(
            X,
            y,
            test_size=0.20,
            random_state=42,
            stratify=y if self.target_type == "classification" else None,
        )

        # Calculate class weights for imbalanced classification
        n_classes = len(np.unique(y_train_sub)) if self.target_type == "classification" else 0
        is_binary = n_classes == 2
        scale_pos_weight = 1
        sample_weight = None

        if self.target_type == "classification" and getattr(self, 'use_class_weights', True):
            if is_binary:
                # Binary classification: use scale_pos_weight
                scale_pos_weight = sum(y_train_sub == 0) / max(sum(y_train_sub == 1), 1)
            else:
                # Multiclass: compute sample weights based on class frequencies
                from sklearn.utils.class_weight import compute_sample_weight
                sample_weight = compute_sample_weight('balanced', y_train_sub)

        optimal_score = get_initial_best_score(metric)
        nb_total_features = len(features_ranked)

        # Calculate search range based on number of samples and available features
        from lecrapaud.utils import get_feature_search_range
        n_samples = len(X)
        min_features, max_features = get_feature_search_range(
            n_samples=n_samples,
            n_available_features=nb_total_features,
            max_features=self.max_features,
        )
        optimal_nb_features = max_features

        logger.info(
            f"Starting automatic feature count selection ({min_features} to {max_features} features), "
            f"optimizing {metric}... (n_samples={n_samples})"
        )

        # Track scores for plotting
        feature_counts = []
        scores = []

        for nb_features in tqdm(
            range(min_features, max_features + 1), desc="Finding optimal feature count"
        ):
            top_features = features_ranked[:nb_features]

            if self.target_type == "classification":
                model = XGBClassifier(
                    colsample_bytree=0.7,
                    learning_rate=0.1,
                    max_depth=3,
                    n_estimators=200,
                    subsample=0.7,
                    scale_pos_weight=scale_pos_weight if is_binary else 1,
                    verbosity=0,
                )
                model.fit(X_train_sub[top_features], y_train_sub, sample_weight=sample_weight)

                # Get predictions
                val_pred_proba = model.predict_proba(X_val[top_features])
                val_pred = model.predict(X_val[top_features])

                # Calculate the selected metric
                if metric == "LOGLOSS":
                    val_score = log_loss(y_val, val_pred_proba)
                elif metric == "ROC_AUC":
                    if is_binary:
                        val_score = roc_auc_score(y_val, val_pred_proba[:, 1])
                    else:
                        val_score = roc_auc_score(y_val, val_pred_proba, multi_class='ovr')
                elif metric == "AVG_PRECISION":
                    if is_binary:
                        val_score = average_precision_score(y_val, val_pred_proba[:, 1])
                    else:
                        val_score = average_precision_score(y_val, val_pred_proba, average="macro")
                elif metric == "ACCURACY":
                    val_score = accuracy_score(y_val, val_pred)
                elif metric == "PRECISION":
                    val_score = precision_score(
                        y_val, val_pred, average="binary" if is_binary else "macro"
                    )
                elif metric == "RECALL":
                    val_score = recall_score(
                        y_val, val_pred, average="binary" if is_binary else "macro"
                    )
                elif metric == "F1":
                    val_score = f1_score(
                        y_val, val_pred, average="binary" if is_binary else "macro"
                    )
            else:
                model = XGBRegressor(
                    colsample_bytree=0.7,
                    learning_rate=0.1,
                    max_depth=3,
                    n_estimators=200,
                    subsample=0.7,
                    verbosity=0,
                )
                model.fit(X_train_sub[top_features], y_train_sub)
                val_predictions = model.predict(X_val[top_features])

                # Calculate the selected metric
                if metric == "RMSE":
                    val_score = root_mean_squared_error(y_val, val_predictions)
                elif metric == "MAE":
                    val_score = mean_absolute_error(y_val, val_predictions)
                elif metric == "MAPE":
                    val_score = mean_absolute_percentage_error(y_val, val_predictions)
                elif metric == "R2":
                    val_score = r2_score(y_val, val_predictions)

            # Track for plotting
            feature_counts.append(nb_features)
            scores.append(val_score)

            if is_metric_better(val_score, optimal_score, metric):
                optimal_score = val_score
                optimal_nb_features = nb_features

        logger.info(
            f"Optimal number of features: {optimal_nb_features}/{nb_total_features}. "
            f"Optimal {metric} on validation: {optimal_score:.4f}"
        )

        # Plot if enabled
        if getattr(self, "plot", False) and feature_counts:
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(feature_counts, scores, marker="o", linewidth=1, markersize=3)
            ax.axvline(x=optimal_nb_features, color="r", linestyle="--", label=f"Optimal: {optimal_nb_features}")
            ax.scatter([optimal_nb_features], [optimal_score], color="r", s=100, zorder=5)
            ax.set_xlabel("Number of Features")
            ax.set_ylabel(metric)
            ax.set_title(f"Feature Count Optimization - TARGET_{self.target_number}")
            ax.legend()
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.show()

        return optimal_nb_features

    # Filter methods
    # ----------------

    def select_categorical_features(self, percentile):
        X, y = self.X_categorical, self.y

        start = time.time()
        logger.debug("Running Chi2 for categorical features...")
        feat_selector = SelectPercentile(chi2, percentile=percentile).fit(X, y)
        feat_scores = pd.DataFrame()
        feat_scores["score"] = feat_selector.scores_
        feat_scores["pvalue"] = feat_selector.pvalues_
        feat_scores["support"] = feat_selector.get_support()
        feat_scores["features"] = X.columns
        feat_scores["rank"] = feat_scores["score"].rank(method="first", ascending=False)
        feat_scores["method"] = FeatureSelectionMethod.CHI2.value

        # Apply both percentile and p-value filtering
        # Keep features that satisfy BOTH conditions: within percentile AND p-value < threshold
        feat_scores["support"] = feat_scores["support"] & (
            feat_scores["pvalue"] <= self.max_p_value_categorical
        )

        feat_scores.sort_values("rank", ascending=True, inplace=True)
        stop = time.time()
        training_time = timedelta(seconds=(stop - start)).total_seconds()
        feat_scores["training_time"] = training_time

        logger.debug(
            f"Chi2 evaluation selected {feat_scores['support'].sum()} features in {training_time:.2f} seconds (percentile={percentile}%, p-value<={self.max_p_value_categorical})"
        )

        # Save Chi2 feature scores to database
        ArtifactService.save_dataframe(
            experiment_id=self.experiment_id,
            data_type="feature_scores_Chi2",
            df=feat_scores,
            target_id=self.target_id,
        )

        return feat_scores

    # Linear correlation (Pearson's R for regression and ANOVA for classification)
    def select_feature_by_linear_correlation(self, percentile: int = 20):
        X, y, target_type = self.X_numerical, self.y, self.target_type

        start = time.time()
        test_type = FeatureSelectionMethod.PEARSONS_R.value if target_type == "regression" else FeatureSelectionMethod.ANOVA.value
        logger.debug(f"Running {test_type}...")

        model = f_regression if target_type == "regression" else f_classif
        # Compute scores for all features (percentile=100 to get all scores)
        feat_selector = SelectPercentile(model, percentile=100).fit(X, y)
        feat_scores = pd.DataFrame()
        feat_scores["score"] = feat_selector.scores_
        feat_scores["pvalue"] = feat_selector.pvalues_
        feat_scores["features"] = X.columns
        feat_scores["rank"] = feat_scores["score"].rank(method="first", ascending=False)
        feat_scores["method"] = test_type

        # Dynamic threshold: p-value based selection
        feat_scores["support"] = feat_scores["pvalue"] <= self.max_p_value

        feat_scores.sort_values("rank", ascending=True, inplace=True)
        stop = time.time()
        training_time = timedelta(seconds=(stop - start)).total_seconds()
        feat_scores["training_time"] = training_time

        logger.debug(
            f"{test_type} evaluation selected {feat_scores['support'].sum()} features in {training_time:.2f} seconds (p-value<={self.max_p_value})"
        )

        # Save linear correlation feature scores to database
        ArtifactService.save_dataframe(
            experiment_id=self.experiment_id,
            data_type=f"feature_scores_{test_type.replace(' ', '_')}",
            df=feat_scores,
            target_id=self.target_id,
        )

        return feat_scores

    # Non-Linear correlation (Spearsman's R for regression and Kendall's Tau for classification)
    def select_feature_by_nonlinear_correlation(self, percentile: int = 20):
        X, y, target_type = self.X_numerical, self.y, self.target_type

        start = time.time()

        def model(X_model, y_model):
            X_model = pd.DataFrame(X_model)
            y_model = pd.Series(y_model)

            method = "spearman" if target_type == "regression" else "kendall"

            corr_scores = []
            p_values = []

            for col in X_model.columns:
                if method == "spearman":
                    corr, pval = spearmanr(X_model[col], y_model)
                else:  # Kendall's Tau for classification
                    corr, pval = kendalltau(X_model[col], y_model)

                corr_scores.append(abs(corr))  # Keeping absolute correlation
                p_values.append(pval)

            return np.array(corr_scores), np.array(p_values)

        test_type = FeatureSelectionMethod.SPEARMANS_R.value if target_type == "regression" else FeatureSelectionMethod.KENDALLS_TAU.value
        logger.debug(f"Running {test_type}...")

        # Compute scores for all features (percentile=100 to get all scores)
        feat_selector = SelectPercentile(model, percentile=100).fit(X, y)
        feat_scores = pd.DataFrame()
        feat_scores["score"] = feat_selector.scores_
        feat_scores["pvalue"] = feat_selector.pvalues_
        feat_scores["features"] = X.columns
        feat_scores["rank"] = feat_scores["score"].rank(method="first", ascending=False)
        feat_scores["method"] = test_type

        # Dynamic threshold: p-value AND minimum correlation magnitude
        feat_scores["support"] = (
            (feat_scores["pvalue"] <= self.max_p_value) &
            (feat_scores["score"] >= self.min_correlation)
        )

        feat_scores.sort_values("rank", ascending=True, inplace=True)
        stop = time.time()
        training_time = timedelta(seconds=(stop - start)).total_seconds()
        feat_scores["training_time"] = training_time

        logger.debug(
            f"{test_type} evaluation selected {feat_scores['support'].sum()} features in {training_time:.2f} seconds (p-value<={self.max_p_value}, |r|>={self.min_correlation})"
        )

        # Save nonlinear correlation feature scores to database
        ArtifactService.save_dataframe(
            experiment_id=self.experiment_id,
            data_type=f"feature_scores_{test_type.replace(' ', '_').replace(chr(39), '')}",
            df=feat_scores,
            target_id=self.target_id,
        )

        return feat_scores

    # Mutual Information
    def select_feature_by_mi(self, percentile: int = 20):
        X, y, target_type = self.X_numerical, self.y, self.target_type

        start = time.time()
        logger.debug("Running Mutual Information...")
        model = (
            mutual_info_regression
            if target_type == "regression"
            else mutual_info_classif
        )
        # Compute scores for all features (percentile=100 to get all scores)
        feat_selector = SelectPercentile(model, percentile=100).fit(X, y)
        feat_scores = pd.DataFrame()
        feat_scores["score"] = feat_selector.scores_
        feat_scores["features"] = X.columns
        feat_scores["rank"] = feat_scores["score"].rank(method="first", ascending=False)
        feat_scores["method"] = FeatureSelectionMethod.MUTUAL_INFORMATION.value

        # Dynamic threshold: cumulative importance (select features explaining X% of total MI)
        sorted_scores = feat_scores.sort_values("score", ascending=False).reset_index(drop=True)
        total_mi = sorted_scores["score"].sum()
        if total_mi > 0:
            cumulative_mi = sorted_scores["score"].cumsum()
            n_selected = (cumulative_mi < total_mi * self.cumulative_importance).sum() + 1
            n_selected = min(n_selected, len(sorted_scores))  # Cap at total features
            selected_features = sorted_scores.head(n_selected)["features"].tolist()
            feat_scores["support"] = feat_scores["features"].isin(selected_features)
        else:
            feat_scores["support"] = False

        feat_scores.sort_values("rank", ascending=True, inplace=True)
        stop = time.time()
        training_time = timedelta(seconds=(stop - start)).total_seconds()
        feat_scores["training_time"] = training_time

        logger.debug(
            f"MI evaluation selected {feat_scores['support'].sum()} features in {training_time:.2f} seconds (cumulative>={self.cumulative_importance*100:.0f}%)"
        )

        # Save MI feature scores to database
        ArtifactService.save_dataframe(
            experiment_id=self.experiment_id,
            data_type="feature_scores_MI",
            df=feat_scores,
            target_id=self.target_id,
        )

        return feat_scores

    # Intrisic/embeedded method
    # ----------------

    # feature importance
    def select_feature_by_feat_imp(self, percentile: int = 20):
        X, y, target_type = self.X_numerical, self.y, self.target_type

        start = time.time()
        logger.debug("Running Feature importance...")

        params = {
            "n_estimators": 500,
            "max_depth": 2**3,
            "random_state": 42,
            "n_jobs": -1,
        }

        estimator = (
            RandomForestClassifier(**params)
            if target_type == "classification"
            else RandomForestRegressor(**params)
        )

        # Fit the estimator to get all feature importances
        estimator.fit(X, y)

        feat_scores = pd.DataFrame()
        feat_scores["score"] = estimator.feature_importances_
        feat_scores["features"] = X.columns
        feat_scores["rank"] = feat_scores["score"].rank(method="first", ascending=False)
        feat_scores["method"] = FeatureSelectionMethod.FI.value

        # Dynamic threshold: cumulative importance (select features explaining X% of total importance)
        sorted_scores = feat_scores.sort_values("score", ascending=False).reset_index(drop=True)
        total_importance = sorted_scores["score"].sum()
        if total_importance > 0:
            cumulative_importance = sorted_scores["score"].cumsum()
            n_selected = (cumulative_importance < total_importance * self.cumulative_importance).sum() + 1
            n_selected = min(n_selected, len(sorted_scores))  # Cap at total features
            selected_features = sorted_scores.head(n_selected)["features"].tolist()
            feat_scores["support"] = feat_scores["features"].isin(selected_features)
        else:
            feat_scores["support"] = False

        feat_scores.sort_values("rank", ascending=True, inplace=True)

        stop = time.time()
        training_time = timedelta(seconds=(stop - start)).total_seconds()
        feat_scores["training_time"] = training_time

        logger.debug(
            f"Feat importance evaluation selected {feat_scores['support'].sum()} features in {training_time:.2f} seconds (cumulative>={self.cumulative_importance*100:.0f}%)"
        )

        # Save FI feature scores to database
        ArtifactService.save_dataframe(
            experiment_id=self.experiment_id,
            data_type="feature_scores_FI",
            df=feat_scores,
            target_id=self.target_id,
        )

        return feat_scores

    # Wrapper method
    # ----------------

    # recursive feature elimination
    def select_feature_by_rfe(self, percentile: int = 20):
        """
        RFE (Recursive Feature Elimination)

        Début: toutes les features
            ↓
        Train model → rank par importance
            ↓
        Supprime les moins importantes
            ↓
        Répète jusqu'à N features
        - Élimine progressivement les features les moins utiles
        - Le ranking vient de l'ordre d'élimination
        """
        X, y, target_type = self.X_numerical, self.y, self.target_type

        start = time.time()
        logger.debug("Running Recursive Feature Elimination...")

        params = {
            "max_depth": 2**3,
            "random_state": 42,
        }
        estimator = (
            DecisionTreeClassifier(**params)
            if target_type == "classification"
            else DecisionTreeRegressor(**params)
        )
        rfe = RFE(estimator, n_features_to_select=percentile / 100, step=4, verbose=0)
        feat_selector = rfe.fit(X, y)

        feat_scores = pd.DataFrame(
            {
                "score": 0.0,  # Default feature importance
                "support": feat_selector.get_support(),
                "features": X.columns,
                "rank": 0,
                "method": FeatureSelectionMethod.RFE.value,
            }
        )
        feat_scores.loc[
            feat_scores["features"].isin(feat_selector.get_feature_names_out()), "score"
        ] = list(feat_selector.estimator_.feature_importances_)
        feat_scores["rank"] = feat_scores["score"].rank(method="first", ascending=False)
        feat_scores.sort_values("rank", ascending=True, inplace=True)

        stop = time.time()
        training_time = timedelta(seconds=(stop - start)).total_seconds()
        feat_scores["training_time"] = training_time

        logger.debug(
            f"RFE evaluation selected {feat_scores['support'].sum()} features in {training_time:.2f} seconds"
        )

        # Save RFE feature scores to database
        ArtifactService.save_dataframe(
            experiment_id=self.experiment_id,
            data_type="feature_scores_RFE",
            df=feat_scores,
            target_id=self.target_id,
        )

        return feat_scores

    # PCA-based feature selection
    def select_feature_by_pca(self, percentile: int = 20):
        """PCA-based feature selection.

        Scores features based on their contribution to principal components,
        weighted by the explained variance of each component.

        Features that contribute heavily to components explaining more variance
        get higher scores.
        """
        from sklearn.preprocessing import StandardScaler

        X, y = self.X_numerical, self.y
        start = time.time()

        logger.debug("Running PCA feature selection...")

        # Standardize features (PCA is sensitive to scale)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Fit PCA with all components to analyze variance
        pca = PCA()
        pca.fit(X_scaled)

        # Log variance analysis
        cumulative_variance = np.cumsum(pca.explained_variance_ratio_)
        n_components_80 = np.argmax(cumulative_variance >= 0.80) + 1
        n_components_90 = np.argmax(cumulative_variance >= 0.90) + 1
        n_components_95 = np.argmax(cumulative_variance >= 0.95) + 1

        logger.info(f"PCA Variance Analysis:")
        logger.info(f"  - Total features: {len(X.columns)}")
        logger.info(f"  - Components for 80% variance: {n_components_80}")
        logger.info(f"  - Components for 90% variance: {n_components_90}")
        logger.info(f"  - Components for 95% variance: {n_components_95}")
        logger.info(f"  - First 5 components explain: {cumulative_variance[min(4, len(cumulative_variance)-1)]*100:.1f}%")

        # Determine how many components to use for scoring
        # Use cumulative_importance parameter (default 0.80)
        n_components_threshold = np.argmax(cumulative_variance >= self.cumulative_importance) + 1

        # Calculate feature scores based on loadings weighted by explained variance
        # loadings = pca.components_ (shape: n_components x n_features)
        loadings = pca.components_[:n_components_threshold]  # Only important components
        variance_weights = pca.explained_variance_ratio_[:n_components_threshold]

        # Score = sum of |loading| × variance_weight for each component
        # This gives higher scores to features contributing to high-variance components
        feature_scores = np.sum(np.abs(loadings) * variance_weights[:, np.newaxis], axis=0)

        # Build result DataFrame
        feat_scores = pd.DataFrame()
        feat_scores["features"] = X.columns
        feat_scores["score"] = feature_scores
        feat_scores["pvalue"] = None  # PCA doesn't produce p-values
        feat_scores["rank"] = feat_scores["score"].rank(method="first", ascending=False).astype(int)
        feat_scores["method"] = FeatureSelectionMethod.PCA.value

        # Support: use cumulative importance threshold on feature scores
        sorted_scores = feat_scores.sort_values("score", ascending=False).reset_index(drop=True)
        total_score = sorted_scores["score"].sum()
        if total_score > 0:
            cumulative_score = sorted_scores["score"].cumsum()
            n_selected = (cumulative_score < total_score * self.cumulative_importance).sum() + 1
            n_selected = min(n_selected, len(sorted_scores))
            selected_features = sorted_scores.head(n_selected)["features"].tolist()
            feat_scores["support"] = feat_scores["features"].isin(selected_features)
        else:
            feat_scores["support"] = False

        training_time = time.time() - start
        feat_scores["training_time"] = training_time

        logger.info(
            f"PCA evaluation selected {feat_scores['support'].sum()} features "
            f"in {training_time:.2f} seconds "
            f"(using {n_components_threshold} components explaining "
            f"{self.cumulative_importance*100:.0f}% variance)"
        )

        # Save PCA feature scores to database
        ArtifactService.save_dataframe(
            experiment_id=self.experiment_id,
            data_type="feature_scores_PCA",
            df=feat_scores,
            target_id=self.target_id,
        )

        return feat_scores.sort_values("rank")

    # SequentialFeatureSelector (loss based, possibility to do forwards or backwards selection or removal)
    def select_feature_by_sfs(self, percentile: int = 20):
        """
        SFS Forward (exemple avec 5 features: A, B, C, D, E)

        Étape 0: []  (aucune feature)
                ↓
                Train 5 modèles (CV) avec: [A], [B], [C], [D], [E]
                → [B] donne meilleur score
                ↓
        Étape 1: [B]
                ↓
                Train 4 modèles (CV) avec: [B,A], [B,C], [B,D], [B,E]
                → [B,D] donne meilleur score
                ↓
        Étape 2: [B, D]
                ↓
                Train 3 modèles (CV) avec: [B,D,A], [B,D,C], [B,D,E]
                → [B,D,A] donne meilleur score
                ↓
        Étape 3: [B, D, A]  → STOP (k_features atteint)

        Modèles entraînés: 5 + 4 + 3 = 12 fits (× nb folds CV)

        ---
        SFS Backward (même exemple, on veut garder 3 features)

        Étape 0: [A, B, C, D, E]  (toutes)
                ↓
                Train 5 modèles (CV) sans: A, sans B, sans C, sans D, sans E
                → sans C donne meilleur score
                ↓
        Étape 1: [A, B, D, E]
                ↓
                Train 4 modèles (CV) sans: A, sans B, sans D, sans E
                → sans E donne meilleur score
                ↓
        Étape 2: [A, B, D]  → STOP (k_features atteint)

        ---
        SFS Floating (forward=True, floating=True)

        Étape 1: [] → ajoute B → [B]
                ↓
        Étape 2: [B] → ajoute D → [B, D]
                ↓
                FLOATING CHECK: retirer B ou D améliore le score?
                → Non, on garde [B, D]
                ↓
        Étape 3: [B, D] → ajoute A → [B, D, A]
                ↓
                FLOATING CHECK: retirer B, D ou A améliore le score?
                → Oui! retirer B améliore → [D, A]
                ↓
                RE-ADD: ajouter quelle feature?
                → ajoute E → [D, A, E]
                ↓
        Étape 4: [D, A, E]  → STOP

        Floating permet de "corriger" des choix sous-optimaux faits au début.
        """
        X, y, target_type = self.X_numerical, self.y, self.target_type

        start = time.time()
        logger.debug("Running Sequential Feature Selection...")
        warnings.filterwarnings("ignore", category=FutureWarning)

        params = {
            "max_depth": 2**3,
            "random_state": 42,
        }
        estimator = (
            DecisionTreeClassifier(**params)
            if target_type == "classification"
            else DecisionTreeRegressor(**params)
        )

        n_splits = 3
        n_samples = len(X)
        test_size = int(n_samples / (n_splits + 4))
        tscv = TimeSeriesSplit(n_splits=n_splits, test_size=test_size)

        # Determine scoring function based on optimization_metric
        from lecrapaud.utils import get_default_metric, get_metric_direction
        from sklearn.metrics import (
            accuracy_score,
            precision_score,
            recall_score,
            f1_score,
            average_precision_score,
            mean_absolute_error,
            mean_absolute_percentage_error,
            r2_score,
        )

        # Determine optimization metric for this target
        optimization_metric = getattr(self, "optimization_metric", {})
        if isinstance(optimization_metric, dict) and self.target_number in optimization_metric:
            metric = optimization_metric[self.target_number]
        elif isinstance(optimization_metric, str):
            metric = optimization_metric
        else:
            metric = get_default_metric(target_type)

        # Map metrics to sklearn scorers
        # Note: mlxtend SFS expects higher scores to be better, so we need to handle direction
        metric_direction = get_metric_direction(metric)
        greater_is_better = metric_direction == "maximize"

        if metric == "LOGLOSS":
            score_function = make_scorer(
                log_loss, response_method="predict_proba", greater_is_better=False
            )
        elif metric == "ROC_AUC":
            score_function = make_scorer(
                roc_auc_score, response_method="predict_proba", greater_is_better=True
            )
        elif metric == "AVG_PRECISION":
            score_function = make_scorer(
                average_precision_score, response_method="predict_proba", greater_is_better=True
            )
        elif metric == "ACCURACY":
            score_function = make_scorer(accuracy_score, greater_is_better=True)
        elif metric == "PRECISION":
            score_function = make_scorer(
                precision_score, average="binary" if len(np.unique(y)) == 2 else "macro",
                greater_is_better=True
            )
        elif metric == "RECALL":
            score_function = make_scorer(
                recall_score, average="binary" if len(np.unique(y)) == 2 else "macro",
                greater_is_better=True
            )
        elif metric == "F1":
            score_function = make_scorer(
                f1_score, average="binary" if len(np.unique(y)) == 2 else "macro",
                greater_is_better=True
            )
        elif metric == "RMSE":
            score_function = make_scorer(root_mean_squared_error, greater_is_better=False)
        elif metric == "MAE":
            score_function = make_scorer(mean_absolute_error, greater_is_better=False)
        elif metric == "MAPE":
            score_function = make_scorer(mean_absolute_percentage_error, greater_is_better=False)
        elif metric == "R2":
            score_function = make_scorer(r2_score, greater_is_better=True)
        else:
            # Fallback to defaults
            score_function = (
                make_scorer(log_loss, response_method="predict_proba", greater_is_better=False)
                if target_type == "classification"
                else make_scorer(root_mean_squared_error, greater_is_better=False)
            )

        logger.info(f"SFS using {metric} as scoring metric")

        sfs = SequentialFeatureSelector(
            estimator,
            k_features=int(percentile * X.shape[1] / 100),
            forward=True,
            floating=True,  # Enables dynamic feature elimination
            scoring=score_function,
            cv=tscv,
            n_jobs=-1,
            verbose=0,
        )

        feat_selector = sfs.fit(X, y)

        # Extract selected features and their scores
        selected_features = set(feat_selector.k_feature_names_)
        feat_subsets = feat_selector.subsets_

        # Create DataFrame for feature scores
        feat_scores = pd.DataFrame(
            {
                "features": X.columns,
                "support": X.columns.isin(
                    selected_features
                ),  # TODO: comprendre pourquoi le support n'est pas correct (les bons scores ne sont pas toujours choisis)
                "score": 1000,
                "rank": None,
                "method": FeatureSelectionMethod.SFS.value,
            }
        )

        # Sort subsets by score (lower is better)
        sorted_subsets = sorted(
            feat_subsets.items(), key=lambda item: item[1]["avg_score"]
        )

        # Record score per feature (first appearance)
        feature_score_map = {}
        for step in sorted_subsets:
            step = step[1]
            for feature in step["feature_names"]:
                if feature not in feature_score_map:
                    feature_score_map[feature] = step["avg_score"]

        # Assign scores
        for feature, score in feature_score_map.items():
            feat_scores.loc[feat_scores["features"] == feature, "score"] = score

        # rank by score (lower = better)
        feat_scores["rank"] = (
            feat_scores["score"].rank(method="first", ascending=True).astype(int)
        )

        feat_scores.sort_values("rank", ascending=True, inplace=True)

        stop = time.time()
        training_time = timedelta(seconds=(stop - start)).total_seconds()
        feat_scores["training_time"] = training_time

        logger.debug(
            f"SFS evaluation selected {feat_scores['support'].sum()} features in {training_time:.2f} seconds"
        )

        # Save SFS feature scores to database
        ArtifactService.save_dataframe(
            experiment_id=self.experiment_id,
            data_type="feature_scores_SFS",
            df=feat_scores,
            target_id=self.target_id,
        )

        return feat_scores


# utils
# TODO : can we use this to select the ideal number of features ?
def feature_selection_analysis(feature_selection_id: int, n_components: int = 5):

    feature_selection = FeatureSelection.get(feature_selection_id)
    experiment_dir = feature_selection.experiment.path
    features = [f.name for f in feature_selection.features]
    target = feature_selection.target.name
    target_number = target.split("_")[1]

    train, val, train_scaled, val_scaled, _scaler_y = load_train_data(
        experiment_dir, target_number, target_type=feature_selection.target.type
    )
    train = train[features + [target]]
    train_scaled = train_scaled[features + [target]]

    logger.info("Plot features correlation with target variable...")

    correlations = train.corr()[target].sort_values(ascending=False)

    plt.figure(figsize=(12, 6))
    sns.barplot(x=correlations.index, y=correlations.values, palette="coolwarm")
    plt.xticks(rotation=90)
    plt.title("Feature correlation with target variable")
    plt.ylabel("Correlation")
    plt.xlabel("Features")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.show()

    plt.figure(figsize=(14, 10))
    sns.heatmap(train.corr(), annot=True, fmt=".2f", cmap="coolwarm", linewidths=0.5)
    plt.title("Correlation Matrix")
    plt.show()

    logger.info("Plot explained variance by components...")
    n_components = min(len(features), n_components)
    pca = PCA(n_components=n_components)
    X_pca = pca.fit_transform(train_scaled)

    explained_variance = pca.explained_variance_ratio_

    plt.figure(figsize=(10, 7))
    plt.bar(
        range(1, len(explained_variance) + 1),
        explained_variance,
        label="Explained Variance",
    )
    plt.plot(
        range(1, len(explained_variance) + 1),
        np.cumsum(explained_variance),
        label="Cumulative Explained Variance",
        color="orange",
        marker="o",
    )
    plt.title("Explained Variance by Components")
    plt.xlabel("Number of Components")
    plt.ylabel("Explained Variance")
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.show()

    logger.info("Main PCA vs target variable...")
    plt.scatter(
        X_pca[:, 0],
        X_pca[:, 1],
        c=train[target],
        cmap="coolwarm",
        alpha=0.7,
    )
    plt.title("PCA of target variable")
    plt.xlabel("First Principal Component")
    plt.ylabel("Second Principal Component")
    plt.colorbar()
    plt.show()


def get_features_by_types(df: pd.DataFrame, sample_categorical_threshold: int = 15):
    categorical_features = [
        col
        for col in df.columns
        if df[col].nunique() <= sample_categorical_threshold
        and df[col].dtype in ["int64", "Int64"]
        and (df[col] >= 0).all()
    ]
    df_categorical = df[categorical_features]
    logger.debug(f"Number of categorical features: {len(categorical_features)}")

    numerical_features = list(set(df.columns).difference(set(categorical_features)))
    df_numerical = df[numerical_features]
    logger.debug(f"Number of numerical features: {len(numerical_features)}")

    return df_categorical, df_numerical
