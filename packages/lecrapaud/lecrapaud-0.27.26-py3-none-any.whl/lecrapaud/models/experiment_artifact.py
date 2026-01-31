from sqlalchemy import (
    Column,
    BigInteger,
    String,
    LargeBinary,
    ForeignKey,
    TIMESTAMP,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from lecrapaud.models.base import Base, with_db
from lecrapaud.config import LECRAPAUD_TABLE_PREFIX


class ExperimentArtifact(Base):
    """
    Stores binary artifacts for experiments (models, scalers, transformers, etc.).

    artifact_type values:
        - 'scaler': Sklearn scalers (scaler_x, scaler_y_1, etc.)
        - 'pca': PCA transformers (pcas, pcas_cross_sectional, pcas_temporal)
        - 'transformer': Power transformers and other sklearn transformers
        - 'model': Trained ML models (sklearn, keras, etc.)
        - 'thresholds': Classification thresholds
        - 'features': Selected features lists

    serialization_format values:
        - 'joblib': Serialized with joblib (sklearn objects, most models)
        - 'keras': Keras/TensorFlow models saved with model.save()
        - 'json': JSON serializable objects (lists, dicts)
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

    experiment_id = Column(
        BigInteger,
        ForeignKey(f"{LECRAPAUD_TABLE_PREFIX}_experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_id = Column(
        BigInteger,
        ForeignKey(f"{LECRAPAUD_TABLE_PREFIX}_targets.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    model_id = Column(
        BigInteger,
        ForeignKey(
            f"{LECRAPAUD_TABLE_PREFIX}_models.id", ondelete="CASCADE"
        ),
        nullable=True,  # Only set for model artifacts
        index=True,
    )

    artifact_type = Column(String(50), nullable=False)
    artifact_name = Column(String(100), nullable=False)
    data = Column(LargeBinary, nullable=False)
    serialization_format = Column(String(20), nullable=False, default="joblib")

    # Relationships
    experiment = relationship("Experiment", lazy="selectin")
    target = relationship("Target", lazy="selectin")
    model = relationship("Model", lazy="selectin")

    __table_args__ = (
        UniqueConstraint(
            "experiment_id",
            "target_id",
            "artifact_type",
            "artifact_name",
            name=f"uq_{LECRAPAUD_TABLE_PREFIX}_experiment_artifact_composite",
        ),
    )

    @classmethod
    @with_db
    def find_artifact(
        cls,
        experiment_id: int,
        artifact_type: str,
        artifact_name: str,
        target_id: int = None,
        db=None,
    ):
        """Find a specific artifact by its identifiers."""
        query = db.query(cls).filter(
            cls.experiment_id == experiment_id,
            cls.artifact_type == artifact_type,
            cls.artifact_name == artifact_name,
        )
        if target_id is not None:
            query = query.filter(cls.target_id == target_id)
        else:
            query = query.filter(cls.target_id.is_(None))
        return query.first()

    @classmethod
    @with_db
    def find_artifacts_by_type(
        cls,
        experiment_id: int,
        artifact_type: str,
        target_id: int = None,
        db=None,
    ):
        """Find all artifacts of a specific type for an experiment."""
        query = db.query(cls).filter(
            cls.experiment_id == experiment_id,
            cls.artifact_type == artifact_type,
        )
        if target_id is not None:
            query = query.filter(cls.target_id == target_id)
        return query.all()
