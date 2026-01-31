from itertools import chain
import pandas as pd
import os
import shutil

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    JSON,
    Table,
    ForeignKey,
    BigInteger,
    TIMESTAMP,
    UniqueConstraint,
    func,
    event,
)
from sqlalchemy.orm import relationship, aliased, mapper
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func
from statistics import fmean as mean
from lecrapaud.models.best_model import BestModel
from lecrapaud.models.model import Model

from lecrapaud.models.base import Base, with_db
from lecrapaud.models.utils import create_association_table
from lecrapaud.utils import logger, contains_best, strip_timestamp_suffix

# jointures
lecrapaud_experiment_target_association = create_association_table(
    name="experiment_target_association",
    table1="experiments",
    column1="experiment",
    table2="targets",
    column2="target",
)


class Experiment(Base):
    """SQLAlchemy model for experiment metadata and configuration.

    Stores all information about a LeCrapaud experiment including data
    characteristics, date ranges, target relationships, and cached scores.

    Attributes:
        id: Unique experiment identifier.
        name: Experiment name (unique, with timestamp suffix).
        path: Filesystem path to experiment directory.
        size: Total number of samples in the dataset.
        train_size: Number of training samples.
        val_size: Number of validation samples.
        test_size: Number of test samples.
        number_of_groups: Count of unique groups in group_column.
        list_of_groups: JSON list of group values.
        number_of_targets: Count of prediction targets.
        start_date: Earliest date in the dataset.
        end_date: Latest date in the dataset.
        context: JSON blob with experiment configuration.
        score: Cached normalized score across all targets.
        best_rmse: Cached best RMSE score.
        best_logloss: Cached best LogLoss score.
        targets: Relationship to Target models.
        best_models: Relationship to BestModel records.
        feature_selections: Relationship to FeatureSelection records.
    """

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    name = Column(String(255), nullable=False)
    path = Column(String(255))  # we do not have this at creation time
    size = Column(Integer, nullable=False)
    train_size = Column(Integer)
    val_size = Column(Integer)
    test_size = Column(Integer)
    number_of_groups = Column(Integer)
    list_of_groups = Column(JSON)
    number_of_targets = Column(Integer)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    train_start_date = Column(DateTime)
    train_end_date = Column(DateTime)
    val_start_date = Column(DateTime)
    val_end_date = Column(DateTime)
    test_start_date = Column(DateTime)
    test_end_date = Column(DateTime)
    context = Column(JSON)

    # Cached/stored score fields
    score = Column(Float)
    best_rmse = Column(Float)
    best_logloss = Column(Float)

    feature_selections = relationship(
        "FeatureSelection",
        back_populates="experiment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    targets = relationship(
        "Target",
        secondary=lecrapaud_experiment_target_association,
        back_populates="experiments",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint(
            "name",
            name="uq_experiments_composite",
        ),
    )

    # Relationships
    best_models = relationship(
        "BestModel",
        back_populates="experiment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Hooks
    # @event.listens_to(Experiment, "after_commit")
    # def set_score(mapper, connection, target):
    #     target.score = target.score

    # Properties
    @hybrid_property
    def rmse_scores(self):
        """best RMSE scores across all best models, for each targets."""
        # Get the minimum RMSE for each best model
        return [
            min(m.rmse for m in bm.models if m.rmse is not None)
            for bm in self.best_models
            if any(m.rmse is not None for m in bm.models)
        ]

    @hybrid_property
    def logloss_scores(self):
        """best LogLoss scores across all best models, for each targets."""
        # Get the minimum LogLoss for each best model
        return [
            min(
                m.logloss
                for m in bm.models
                if m.logloss is not None
            )
            for bm in self.best_models
            if any(m.logloss is not None for m in bm.models)
        ]

    @hybrid_property
    def calculate_best_rmse(self):
        """Calculate best RMSE score within targets, across all model selections."""
        return min(self.rmse_scores) if self.rmse_scores else None

    @hybrid_property
    def calculate_best_logloss(self):
        """Calculate best LogLoss score within targets, across all model selections."""
        return min(self.logloss_scores) if self.logloss_scores else None

    @hybrid_property
    def calculate_score(self):
        # Calculate a combined score: average of normalized best RMSE and LogLoss per targets
        # This ensures we're comparing apples to apples by normalizing the scores

        if not self.rmse_scores and not self.logloss_scores:
            logger.error(
                f"No experiments found with RMSE or LogLoss scores for experiment {self.id}"
            )
            return None

        # Normalize scores (subtract min and divide by range)
        # Guard against division by zero when only one observation or all equal
        # Let's gather all the data from similar experiments to calculate the range

        similar_experiments = Experiment.get_all_by_name(name=self.name)
        if not similar_experiments:
            similar_experiments = [self]
        rmse_scores = [
            score for exp in similar_experiments for score in exp.rmse_scores or []
        ]
        logloss_scores = [
            score for exp in similar_experiments for score in exp.logloss_scores or []
        ]

        # Handle empty score lists
        if not rmse_scores and not logloss_scores:
            return None

        min_rmse = min(rmse_scores) if rmse_scores else float("inf")
        max_rmse = max(rmse_scores) if rmse_scores else float("-inf")
        range_rmse = max_rmse - min_rmse if rmse_scores else 0
        min_logloss = min(logloss_scores) if logloss_scores else float("inf")
        max_logloss = max(logloss_scores) if logloss_scores else float("-inf")
        range_logloss = max_logloss - min_logloss if logloss_scores else 0

        # Calculate combined score for each experiment
        normed_scores = []

        # Add normalized RMSE scores if available
        if self.rmse_scores:
            for rmse_score in self.rmse_scores:
                # Normalize both scores (safe when range == 0)
                norm_rmse = (
                    0.0 if range_rmse == 0 else (rmse_score - min_rmse) / range_rmse
                )
                normed_scores.append(norm_rmse)

        # Add normalized LogLoss scores if available
        if self.logloss_scores:
            for logloss_score in self.logloss_scores:
                norm_logloss = (
                    0.0
                    if range_logloss == 0
                    else (logloss_score - min_logloss) / range_logloss
                )
                normed_scores.append(norm_logloss)

        # Calculate score (average of normalized scores)
        if not normed_scores:
            return None

        score = sum(normed_scores) / len(normed_scores)
        return score

    @hybrid_property
    def avg_rmse(self):
        """Average within targets of best RMSE score across all model selections ."""
        return mean(self.rmse_scores) if self.rmse_scores else None

    @hybrid_property
    def avg_logloss(self):
        """Average within targets of best LogLoss score across all model selections ."""
        return mean(self.logloss_scores) if self.logloss_scores else None

    # Class methods
    @classmethod
    @with_db
    def get_all_by_name(cls, name: str | None = None, limit: int = 1000, db=None):
        """
        Find the most recently created experiment that contains the given name string.

        Args:
            session: SQLAlchemy session
            name (str): String to search for in experiment names

        Returns:
            Experiment or None: The most recent matching experiment or None if not found
        """
        base_name = strip_timestamp_suffix(name)
        if name is not None:
            return (
                db.query(cls)
                .filter(cls.name.ilike(f"%{base_name}%"))
                .order_by(cls.created_at.desc())
                .limit(limit)
                .all()
            )
        return db.query(cls).order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    @with_db
    def get_last_by_name(cls, name: str, db=None):
        """
        Find the most recently created experiment that contains the given name string.

        Args:
            session: SQLAlchemy session
            name (str): String to search for in experiment names

        Returns:
            Experiment or None: The most recent matching experiment or None if not found
        """
        base_name = strip_timestamp_suffix(name)
        return (
            db.query(cls)
            .filter(cls.name.ilike(f"%{base_name}%"))
            .order_by(cls.created_at.desc())
            .first()
        )

    @classmethod
    @with_db
    def get_best_by_score(cls, name: str, db=None):
        """
        Find the experiment with the best normalized score across RMSE and LogLoss.

        Returns:
            Experiment or None: The experiment with the best score or None if not found
        """
        experiments = Experiment.get_all_by_name(name=name)
        if not experiments:
            logger.error(f"No experiments found with the given name: {name}")
            return None

        experiments = [
            exp
            for exp in experiments
            if all(
                [contains_best(f"{exp.path}/{target.name}") for target in exp.targets]
            )
        ]
        if not experiments:
            logger.error(
                f"No fully trained experiments found with the given name: {name}"
            )
            return None

        scored_experiments = []
        for experiment in experiments:
            # Use calculated score if cached score is not available
            score = (
                experiment.score
                if experiment.score is not None
                else experiment.calculate_score
            )
            if score is not None:
                scored_experiments.append((experiment, score))

        if not scored_experiments:
            logger.error(
                f"No experiments with calculable scores found with the given name: {name}"
            )
            return None

        scored_experiments.sort(key=lambda x: x[1])
        return scored_experiments[0][0]

    # Instance methods
    def best_score(self, target_number: int) -> dict:
        """
        Returns the scores for the best model of the specified target.

        Args:
            target_number (int): The target number to get scores for

        Returns:
            dict: A dictionary containing the experiment name, target number, and the best model's scores
        """
        # Find the target
        target_name = f"TARGET_{target_number}"
        target = next((t for t in self.targets if t.name == target_name), None)

        if not target:
            return {
                "experiment_name": self.name,
                "target_number": target_number,
                "error": f"Target {target_name} not found in this experiment",
                "scores": {},
            }

        # Find the best model for this target
        best_model_entry = next(
            (bm for bm in self.best_models if bm.target_id == target.id), None
        )

        if not best_model_entry or not best_model_entry.models:
            return {
                "experiment_name": self.name,
                "target_number": target_number,
                "error": "No model found for this target",
                "scores": {},
            }

        # Get the best model score based on lowest logloss or rmse
        model_scores = best_model_entry.models

        # Determine if we should use logloss or rmse based on what's available
        if any(m.logloss is not None for m in model_scores):
            # Classification: find lowest logloss
            best_score = min(
                (m for m in model_scores if m.logloss is not None),
                key=lambda x: x.logloss,
            )
        elif any(m.rmse is not None for m in model_scores):
            # Regression: find lowest rmse
            best_score = min(
                (m for m in model_scores if m.rmse is not None), key=lambda x: x.rmse
            )
        else:
            return {
                "experiment_name": self.name,
                "target_number": target_number,
                "error": "No scores found for the best model",
                "scores": {},
            }

        # Use the best score found
        score = best_score
        available_metrics = [
            "rmse",
            "mae",
            "r2",
            "logloss",
            "accuracy",
            "precision",
            "recall",
            "f1",
            "roc_auc",
        ]

        scores = {}
        for metric in available_metrics:
            value = getattr(score, metric, None)
            if value is not None:
                scores[metric] = value

        # Get the model info
        model_info = {
            "model_type": (score.model.model_type.type if score.model and score.model.model_type else "unknown"),
            "model_name": (score.model.model_type.name if score.model and score.model.model_type else "unknown"),
            "training_time_seconds": score.training_time,
        }

        return {
            "experiment_name": self.name,
            "target_number": target_number,
            "model": model_info,
            "scores": scores,
        }

    def get_target(self, target_number: int):
        """Get target by target number.

        :param target_number: the target number (e.g., 1 for TARGET_1)
        :return: Target object or None
        """
        target_name = f"TARGET_{target_number}"
        return next((t for t in self.targets if t.name == target_name), None)

    def get_best_model(self, target_number: int):
        """Get BestModel for a target number.

        :param target_number: the target number (e.g., 1 for TARGET_1)
        :return: BestModel object or None
        """
        target = self.get_target(target_number)
        if not target:
            return None
        return next((bm for bm in self.best_models if bm.target_id == target.id), None)

    @with_db
    def get_features(self, target_number: int, db=None):
        # Ensure we have a fresh instance attached to the session
        self = db.merge(self)
        targets = [t for t in self.targets if t.name == f"TARGET_{target_number}"]
        if targets:
            target_id = targets[0].id
            feature_selection = [
                fs for fs in self.feature_selections if fs.target_id == target_id
            ]
            if feature_selection:
                feature_selection = feature_selection[0]
                features = [f.name for f in feature_selection.features]
                return features

        # fallback to database artifact if no features found via relationship
        from lecrapaud.services import ArtifactService

        target = [t for t in self.targets if t.name == f"TARGET_{target_number}"]
        target_id = target[0].id if target else None
        features = ArtifactService.load_features(
            experiment_id=self.id,
            target_id=target_id,
        )
        if features:
            return features

        raise ValueError(
            f"No features found for experiment {self.id}, target {target_number}"
        )

    @with_db
    def get_all_features(
        self, date_column: str = None, group_column: str = None, db=None
    ):
        # Ensure we have a fresh instance attached to the session
        self = db.merge(self)
        target_idx = [target.id for target in self.targets]
        _all_features = chain.from_iterable(
            [f.name for f in fs.features]
            for fs in self.feature_selections
            if fs.target_id in target_idx
        )
        _all_features = list(_all_features)

        # fallback to database artifact if no features found via relationship
        if len(_all_features) == 0:
            from lecrapaud.services import ArtifactService

            _all_features = ArtifactService.load_artifact(
                experiment_id=self.id,
                artifact_type="features",
                artifact_name="all_features",
            )
            if _all_features is None:
                _all_features = []

        all_features = []
        if date_column:
            all_features.append(date_column)
        if group_column:
            all_features.append(group_column)
        all_features += _all_features
        all_features = list(dict.fromkeys(all_features))

        return all_features

    def update_cached_scores(self):
        """
        Update the cached score fields with calculated values.
        This should be called after model training is complete.
        """
        self.score = self.calculate_score
        self.best_rmse = self.calculate_best_rmse
        self.best_logloss = self.calculate_best_logloss

        return self

    def get_best_params(self, target_number: int) -> dict | None:
        """
        Get the best model parameters for a specific target.

        Args:
            target_number (int): The target number to get best params for

        Returns:
            dict | None: The best model parameters for the target, or None if not found
        """
        target_name = f"TARGET_{target_number}"
        best_model_entry = next(
            (bm for bm in self.best_models if bm.target and bm.target.name == target_name),
            None
        )
        if best_model_entry:
            return best_model_entry.params
        return None

    def get_all_best_params(self) -> dict:
        """
        Get the best model parameters for all targets.

        Returns:
            dict: A dictionary with target numbers as keys and their best parameters as values
        """
        all_best_params = {}
        for best_model_entry in self.best_models:
            if best_model_entry.target and best_model_entry.params:
                # Extract target number from target name (e.g., "TARGET_1" -> 1)
                target_name = best_model_entry.target.name
                if target_name.startswith("TARGET_"):
                    try:
                        target_number = int(target_name.split("_")[1])
                        all_best_params[target_number] = best_model_entry.params
                    except (IndexError, ValueError):
                        logger.warning(f"Could not parse target number from {target_name}")
        return all_best_params


# Event listener to delete experiment folder when experiment is deleted
@event.listens_for(Experiment, "after_delete")
def delete_experiment_folder(mapper, connection, target):
    """
    Delete the experiment folder when an experiment is deleted from the database.

    Args:
        mapper: SQLAlchemy mapper
        connection: Database connection
        target: The Experiment instance being deleted
    """
    if target.path and os.path.exists(target.path):
        try:
            shutil.rmtree(target.path)
            logger.info(f"Deleted experiment folder: {target.path}")
        except OSError as e:
            logger.error(f"Failed to delete experiment folder {target.path}: {e}")
