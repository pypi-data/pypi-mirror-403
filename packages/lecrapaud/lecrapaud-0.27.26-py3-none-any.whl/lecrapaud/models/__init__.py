"""SQLAlchemy ORM models for LeCrapaud.

This module provides database models for storing experiment metadata,
model results, feature selections, and artifacts. All models inherit
from Base which provides common CRUD operations.

Classes:
    Base: Abstract base class with CRUD operations.
    Experiment: Stores experiment metadata and configuration.
    Target: Defines prediction targets (classification/regression).
    Feature: Stores feature metadata and types.
    FeatureSelection: Links experiments to selected features.
    FeatureSelectionRank: Stores feature importance rankings.
    BestModel: Tracks the best model for each experiment-target pair.
    Model: Stores individual model training results and metrics.
    ModelType: Registry of model types (lgb, xgb, catboost, etc.).
    ExperimentArtifact: Binary storage for models and scalers.
    ExperimentData: Binary storage for DataFrames.
"""

from lecrapaud.models.base import Base
from lecrapaud.models.experiment import Experiment
from lecrapaud.models.experiment_artifact import ExperimentArtifact
from lecrapaud.models.experiment_data import ExperimentData
from lecrapaud.models.feature_selection_rank import FeatureSelectionRank, FeatureSelectionMethod
from lecrapaud.models.feature_selection import FeatureSelection
from lecrapaud.models.feature import Feature, FeatureType
from lecrapaud.models.best_model import BestModel
from lecrapaud.models.model_type import ModelType
from lecrapaud.models.model import Model
from lecrapaud.models.target import Target

__all__ = [
    "Base",
    "Experiment",
    "ExperimentArtifact",
    "ExperimentData",
    "FeatureSelectionRank",
    "FeatureSelectionMethod",
    "FeatureSelection",
    "Feature",
    "FeatureType",
    "BestModel",
    "ModelType",
    "Model",
    "Target",
]
