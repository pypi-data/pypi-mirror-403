"""
Artifact Service for storing and retrieving experiment artifacts from the database.

Handles serialization/deserialization of:
- Sklearn objects (scalers, PCAs, transformers) via joblib
- Keras models via model.save() to BytesIO
- DataFrames via parquet compression
- Python objects (lists, dicts) via JSON
"""

import io
import json
from typing import Any, Optional

import joblib
import pandas as pd

from lecrapaud.models.experiment_artifact import ExperimentArtifact
from lecrapaud.models.experiment_data import ExperimentData
from lecrapaud.models.base import with_db
from lecrapaud.utils import logger


class ArtifactService:
    """Service for saving and loading experiment artifacts to/from database."""

    # --- Artifact Methods (binary objects like models, scalers, etc.) ---

    @staticmethod
    @with_db
    def save_artifact(
        experiment_id: int,
        artifact_type: str,
        artifact_name: str,
        obj: Any,
        target_id: int = None,
        model_id: int = None,
        serialization_format: str = "joblib",
        db=None,
    ) -> ExperimentArtifact:
        """
        Serialize and save an artifact to the database.

        Args:
            experiment_id: ID of the experiment
            artifact_type: Type of artifact ('scaler', 'pca', 'transformer', 'model', 'thresholds', 'features')
            artifact_name: Name of the artifact (e.g., 'scaler_x', 'pcas_temporal', 'xgboost.best')
            obj: The object to serialize and store
            target_id: Optional target ID for target-specific artifacts
            model_id: Optional Model ID to link model artifacts to their scores
            serialization_format: 'joblib', 'keras', or 'json'
            db: Database session

        Returns:
            ExperimentArtifact: The saved artifact record
        """
        # Serialize the object
        data = ArtifactService._serialize(obj, serialization_format)

        # Check if artifact already exists
        existing = ExperimentArtifact.find_artifact(
            experiment_id=experiment_id,
            artifact_type=artifact_type,
            artifact_name=artifact_name,
            target_id=target_id,
            db=db,
        )

        if existing:
            # Update existing artifact
            existing.data = data
            existing.serialization_format = serialization_format
            existing.model_id = model_id
            existing = db.merge(existing)
            db.commit()
            db.refresh(existing)
            logger.debug(
                f"Updated artifact: {artifact_type}/{artifact_name} for experiment {experiment_id}"
            )
            return existing

        # Create new artifact
        artifact = ExperimentArtifact(
            experiment_id=experiment_id,
            target_id=target_id,
            model_id=model_id,
            artifact_type=artifact_type,
            artifact_name=artifact_name,
            data=data,
            serialization_format=serialization_format,
        )
        artifact = artifact.save(db=db)
        logger.debug(
            f"Saved artifact: {artifact_type}/{artifact_name} for experiment {experiment_id}"
        )
        return artifact

    @staticmethod
    @with_db
    def load_artifact(
        experiment_id: int,
        artifact_type: str,
        artifact_name: str,
        target_id: int = None,
        db=None,
    ) -> Optional[Any]:
        """
        Load and deserialize an artifact from the database.

        Args:
            experiment_id: ID of the experiment
            artifact_type: Type of artifact
            artifact_name: Name of the artifact
            target_id: Optional target ID for target-specific artifacts
            db: Database session

        Returns:
            The deserialized object, or None if not found
        """
        artifact = ExperimentArtifact.find_artifact(
            experiment_id=experiment_id,
            artifact_type=artifact_type,
            artifact_name=artifact_name,
            target_id=target_id,
            db=db,
        )

        if artifact is None:
            logger.debug(
                f"Artifact not found: {artifact_type}/{artifact_name} for experiment {experiment_id}"
            )
            return None

        return ArtifactService._deserialize(artifact.data, artifact.serialization_format)

    @staticmethod
    @with_db
    def delete_artifact(
        experiment_id: int,
        artifact_type: str,
        artifact_name: str,
        target_id: int = None,
        db=None,
    ) -> bool:
        """Delete an artifact from the database."""
        artifact = ExperimentArtifact.find_artifact(
            experiment_id=experiment_id,
            artifact_type=artifact_type,
            artifact_name=artifact_name,
            target_id=target_id,
            db=db,
        )
        if artifact:
            db.delete(artifact)
            db.commit()
            return True
        return False

    # --- DataFrame Methods (train, val, test, predictions, feature scores) ---

    @staticmethod
    @with_db
    def save_dataframe(
        experiment_id: int,
        data_type: str,
        df: pd.DataFrame,
        target_id: int = None,
        model_id: int = None,
        db=None,
    ) -> ExperimentData:
        """
        Save a DataFrame to the database as compressed parquet.

        Args:
            experiment_id: ID of the experiment
            data_type: Type of data ('train', 'val', 'test', 'full', 'train_scaled', etc.,
                       'prediction', 'feature_scores_{method}', 'scores_tracking')
            df: The DataFrame to store
            target_id: Optional target ID for target-specific data (feature scores, scores_tracking)
            model_id: Required for 'prediction' data_type
            db: Database session

        Returns:
            ExperimentData: The saved data record
        """
        # Serialize DataFrame to parquet bytes
        # Convert object columns with non-serializable types to strings
        df_copy = df.copy()
        for col in df_copy.columns:
            if df_copy[col].dtype == "object":
                df_copy[col] = df_copy[col].astype(str)
        buffer = io.BytesIO()
        df_copy.to_parquet(buffer, compression="snappy", index=True)
        data = buffer.getvalue()

        # Check if data already exists
        if data_type == "prediction" and model_id:
            existing = ExperimentData.find_prediction(
                model_id=model_id, db=db
            )
        else:
            existing = ExperimentData.find_data(
                experiment_id=experiment_id, data_type=data_type, target_id=target_id, db=db
            )

        if existing:
            # Update existing data
            existing.data = data
            existing.row_count = len(df)
            existing.column_count = len(df.columns)
            existing = db.merge(existing)
            db.commit()
            db.refresh(existing)
            logger.debug(f"Updated data: {data_type} for experiment {experiment_id}")
            return existing

        # Create new data entry
        experiment_data = ExperimentData(
            experiment_id=experiment_id,
            target_id=target_id,
            model_id=model_id,
            data_type=data_type,
            data=data,
            row_count=len(df),
            column_count=len(df.columns),
        )
        experiment_data = experiment_data.save(db=db)
        logger.debug(f"Saved data: {data_type} for experiment {experiment_id}")
        return experiment_data

    @staticmethod
    @with_db
    def load_dataframe(
        experiment_id: int,
        data_type: str,
        target_id: int = None,
        model_id: int = None,
        db=None,
    ) -> Optional[pd.DataFrame]:
        """
        Load a DataFrame from the database.

        Args:
            experiment_id: ID of the experiment
            data_type: Type of data
            target_id: Optional target ID for target-specific data
            model_id: Required for 'prediction' data_type
            db: Database session

        Returns:
            pd.DataFrame or None if not found
        """
        if data_type == "prediction" and model_id:
            data_record = ExperimentData.find_prediction(
                model_id=model_id, db=db
            )
        else:
            data_record = ExperimentData.find_data(
                experiment_id=experiment_id, data_type=data_type, target_id=target_id, db=db
            )

        if data_record is None:
            logger.warning(f"Data not found: {data_type} for experiment {experiment_id}")
            return None

        buffer = io.BytesIO(data_record.data)
        return pd.read_parquet(buffer)

    @staticmethod
    @with_db
    def delete_dataframe(
        experiment_id: int,
        data_type: str,
        target_id: int = None,
        model_id: int = None,
        db=None,
    ) -> bool:
        """Delete a DataFrame from the database."""
        if data_type == "prediction" and model_id:
            data_record = ExperimentData.find_prediction(
                model_id=model_id, db=db
            )
        else:
            data_record = ExperimentData.find_data(
                experiment_id=experiment_id, data_type=data_type, target_id=target_id, db=db
            )

        if data_record:
            db.delete(data_record)
            db.commit()
            return True
        return False

    # --- Serialization Helpers ---

    @staticmethod
    def _serialize(obj: Any, format: str) -> bytes:
        """Serialize an object to bytes."""
        if format == "joblib":
            buffer = io.BytesIO()
            joblib.dump(obj, buffer)
            return buffer.getvalue()
        elif format == "keras":
            # For Keras models, use save() with BytesIO
            buffer = io.BytesIO()
            obj.save(buffer)
            return buffer.getvalue()
        elif format == "json":
            return json.dumps(obj).encode("utf-8")
        else:
            raise ValueError(f"Unknown serialization format: {format}")

    @staticmethod
    def _deserialize(data: bytes, format: str) -> Any:
        """Deserialize bytes to an object."""
        if format == "joblib":
            buffer = io.BytesIO(data)
            return joblib.load(buffer)
        elif format == "keras":
            # For Keras models, need to use load_model
            import tempfile
            import os

            # Keras load_model requires a file path, so we use a temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".keras") as f:
                f.write(data)
                temp_path = f.name
            try:
                from keras.models import load_model

                return load_model(temp_path)
            finally:
                os.unlink(temp_path)
        elif format == "json":
            return json.loads(data.decode("utf-8"))
        else:
            raise ValueError(f"Unknown serialization format: {format}")

    # --- Convenience Methods ---

    @staticmethod
    @with_db
    def save_model(
        experiment_id: int,
        target_id: int,
        model_name: str,
        model: Any,
        model_id: int,
        is_keras: bool = False,
        db=None,
    ) -> ExperimentArtifact:
        """Convenience method to save a trained model.

        Args:
            experiment_id: Experiment ID
            target_id: Target ID
            model_name: Model name with extension (e.g., 'xgboost.best', 'lstm.keras')
            model: The trained model object
            model_id: Model ID to link the model to its score
            is_keras: Whether the model is a Keras model
            db: Database session

        Returns:
            ExperimentArtifact: The saved artifact record
        """
        serialization_format = "keras" if is_keras else "joblib"
        return ArtifactService.save_artifact(
            experiment_id=experiment_id,
            artifact_type="model",
            artifact_name=model_name,
            obj=model,
            target_id=target_id,
            model_id=model_id,
            serialization_format=serialization_format,
            db=db,
        )

    @staticmethod
    @with_db
    def load_model(
        experiment_id: int,
        target_id: int,
        model_name: str,
        db=None,
    ) -> Optional[Any]:
        """Load a trained model by name.

        Args:
            experiment_id: Experiment ID
            target_id: Target ID
            model_name: Model name (e.g., "xgboost"). Will try both .best and .keras extensions.
            db: Database session

        Returns:
            The loaded model, or None if not found
        """
        # If model_name already has extension, use it directly
        if model_name.endswith(".best") or model_name.endswith(".keras"):
            return ArtifactService.load_artifact(
                experiment_id=experiment_id,
                artifact_type="model",
                artifact_name=model_name,
                target_id=target_id,
                db=db,
            )

        # Try .best first (sklearn models), then .keras (recurrent models)
        model = ArtifactService.load_artifact(
            experiment_id=experiment_id,
            artifact_type="model",
            artifact_name=f"{model_name}.best",
            target_id=target_id,
            db=db,
        )
        if model:
            return model

        return ArtifactService.load_artifact(
            experiment_id=experiment_id,
            artifact_type="model",
            artifact_name=f"{model_name}.keras",
            target_id=target_id,
            db=db,
        )

    @staticmethod
    @with_db
    def load_model_by_model_id(
        model_id: int,
        db=None,
    ) -> Optional[Any]:
        """Load a trained model by its Model ID.

        Args:
            model_id: Model ID
            db: Database session

        Returns:
            The loaded model, or None if not found
        """
        artifact = (
            db.query(ExperimentArtifact)
            .filter(
                ExperimentArtifact.model_id == model_id,
                ExperimentArtifact.artifact_type == "model",
            )
            .first()
        )
        if artifact:
            return ArtifactService._deserialize(
                artifact.data, artifact.serialization_format
            )
        return None

    # Alias for backwards compatibility
    load_model_by_score = load_model_by_model_id

    @staticmethod
    @with_db
    def save_scaler(
        experiment_id: int,
        scaler_name: str,
        scaler: Any,
        target_id: int = None,
        db=None,
    ) -> ExperimentArtifact:
        """Convenience method to save a scaler."""
        return ArtifactService.save_artifact(
            experiment_id=experiment_id,
            artifact_type="scaler",
            artifact_name=scaler_name,
            obj=scaler,
            target_id=target_id,
            serialization_format="joblib",
            db=db,
        )

    @staticmethod
    @with_db
    def load_scaler(
        experiment_id: int,
        scaler_name: str,
        target_id: int = None,
        db=None,
    ) -> Optional[Any]:
        """Convenience method to load a scaler."""
        return ArtifactService.load_artifact(
            experiment_id=experiment_id,
            artifact_type="scaler",
            artifact_name=scaler_name,
            target_id=target_id,
            db=db,
        )

    @staticmethod
    @with_db
    def save_features(
        experiment_id: int,
        target_id: int,
        features: list,
        db=None,
    ) -> ExperimentArtifact:
        """Convenience method to save selected features list."""
        return ArtifactService.save_artifact(
            experiment_id=experiment_id,
            artifact_type="features",
            artifact_name="selected_features",
            obj=features,
            target_id=target_id,
            serialization_format="json",
            db=db,
        )

    @staticmethod
    @with_db
    def load_features(
        experiment_id: int,
        target_id: int,
        db=None,
    ) -> Optional[list]:
        """Convenience method to load selected features list."""
        return ArtifactService.load_artifact(
            experiment_id=experiment_id,
            artifact_type="features",
            artifact_name="selected_features",
            target_id=target_id,
            db=db,
        )

    @staticmethod
    @with_db
    def save_thresholds(
        experiment_id: int,
        target_id: int,
        thresholds: dict,
        db=None,
    ) -> ExperimentArtifact:
        """Convenience method to save classification thresholds."""
        return ArtifactService.save_artifact(
            experiment_id=experiment_id,
            artifact_type="thresholds",
            artifact_name="classification_thresholds",
            obj=thresholds,
            target_id=target_id,
            serialization_format="json",
            db=db,
        )

    @staticmethod
    @with_db
    def load_thresholds(
        experiment_id: int,
        target_id: int,
        db=None,
    ) -> Optional[dict]:
        """Convenience method to load classification thresholds."""
        return ArtifactService.load_artifact(
            experiment_id=experiment_id,
            artifact_type="thresholds",
            artifact_name="classification_thresholds",
            target_id=target_id,
            db=db,
        )

    @staticmethod
    @with_db
    def load_best_model(
        experiment_id: int,
        target_id: int,
        db=None,
    ) -> Optional[Any]:
        """Load the best model for a target based on BestModel.model_id.

        Returns:
            The best model object, or None if not found
        """
        from lecrapaud.models import BestModel

        # Find the BestModel for this experiment/target
        bm = (
            db.query(BestModel)
            .filter(
                BestModel.experiment_id == experiment_id,
                BestModel.target_id == target_id,
            )
            .first()
        )

        if not bm or not bm.model_id:
            logger.warning(
                f"No best model found for experiment {experiment_id}, target {target_id}"
            )
            return None

        # Load model by its model ID
        return ArtifactService.load_model_by_score(
            model_id=bm.model_id,
            db=db,
        )
