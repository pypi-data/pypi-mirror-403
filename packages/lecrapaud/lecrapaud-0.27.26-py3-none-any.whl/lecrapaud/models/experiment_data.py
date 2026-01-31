from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
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


class ExperimentData(Base):
    """
    Stores DataFrame data for experiments (train, val, test datasets, predictions, feature scores).

    data_type values:
        - 'full': Full dataset before splitting
        - 'train': Training set
        - 'val': Validation set
        - 'test': Test set
        - 'train_scaled': Scaled training set
        - 'val_scaled': Scaled validation set
        - 'test_scaled': Scaled test set
        - 'prediction': Model predictions (requires model_id)
        - 'feature_scores_{method}': Feature selection scores (requires target_id)
        - 'scores_tracking': Model scores tracking (requires target_id)

    Data is stored as Parquet-compressed binary for efficiency.
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
        nullable=True,
        index=True,
    )

    data_type = Column(String(50), nullable=False)
    data = Column(LargeBinary, nullable=False)
    row_count = Column(Integer, nullable=True)
    column_count = Column(Integer, nullable=True)

    # Relationships
    experiment = relationship("Experiment", lazy="selectin")
    target = relationship("Target", lazy="selectin")
    model = relationship("Model", lazy="selectin")

    __table_args__ = (
        UniqueConstraint(
            "experiment_id",
            "target_id",
            "data_type",
            "model_id",
            name=f"uq_{LECRAPAUD_TABLE_PREFIX}_experiment_data_composite",
        ),
    )

    @classmethod
    @with_db
    def find_data(cls, experiment_id: int, data_type: str, target_id: int = None, db=None):
        """Find a specific data entry by experiment, type, and optionally target."""
        query = db.query(cls).filter(
            cls.experiment_id == experiment_id,
            cls.data_type == data_type,
        )
        if target_id is not None:
            query = query.filter(cls.target_id == target_id)
        else:
            query = query.filter(cls.target_id.is_(None))
        return query.first()

    @classmethod
    @with_db
    def find_prediction(cls, model_id: int, db=None):
        """Find prediction by model selection score ID."""
        return (
            db.query(cls)
            .filter(
                cls.model_id == model_id,
                cls.data_type == "prediction",
            )
            .first()
        )

    @classmethod
    @with_db
    def find_all_data(cls, experiment_id: int, db=None):
        """Find all data entries for an experiment."""
        return db.query(cls).filter(cls.experiment_id == experiment_id).all()
