from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    JSON,
    ForeignKey,
    BigInteger,
    TIMESTAMP,
    UniqueConstraint,
)
from sqlalchemy import func
from sqlalchemy.orm import relationship
from lecrapaud.models.base import Base
from lecrapaud.config import LECRAPAUD_TABLE_PREFIX


class Model(Base):
    """SQLAlchemy model for trained model results and metrics.

    Stores the training results for a single model type trained during
    model selection. Contains all evaluation metrics for both regression
    and classification tasks.

    Attributes:
        id: Unique model identifier.
        params: Hyperparameters used for training (JSON).
        model_path: Legacy file path (deprecated).
        training_time: Training duration in seconds.
        model_type_id: Reference to ModelType.
        best_model_id: Reference to parent BestModel.
        eval_data_std: Standard deviation of evaluation data.
        rmse: Root Mean Square Error (regression).
        mae: Mean Absolute Error (regression).
        mape: Mean Absolute Percentage Error (regression).
        r2: R-squared score (regression).
        logloss: Log Loss (classification).
        accuracy: Accuracy score (classification).
        precision: Precision score (classification).
        recall: Recall score (classification).
        f1: F1 score (classification).
        roc_auc: ROC AUC score (classification).
        thresholds: Classification thresholds (JSON).
        model_type: Relationship to ModelType.
        best_model: Relationship to parent BestModel.
    """

    __tablename__ = f"{LECRAPAUD_TABLE_PREFIX}_models"

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

    # From ModelTraining
    params = Column(JSON)
    model_path = Column(String(255))
    training_time = Column(Integer)
    model_type_id = Column(
        BigInteger, ForeignKey(f"{LECRAPAUD_TABLE_PREFIX}_model_types.id"), nullable=False
    )
    best_model_id = Column(
        BigInteger,
        ForeignKey(f"{LECRAPAUD_TABLE_PREFIX}_best_models.id", ondelete="CASCADE"),
        nullable=False,
    )

    # From Score (excluding type and training_time which is already in ModelTraining)
    eval_data_std = Column(Float)
    rmse = Column(Float)
    rmse_std_ratio = Column(Float)
    mae = Column(Float)
    mape = Column(Float)
    mam = Column(Float)
    mad = Column(Float)
    mae_mam_ratio = Column(Float)
    mae_mad_ratio = Column(Float)
    r2 = Column(Float)
    bias = Column(Float)
    logloss = Column(Float)
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1 = Column(Float)
    roc_auc = Column(Float)
    avg_precision = Column(Float)
    thresholds = Column(JSON)
    precision_at_threshold = Column(Float)
    recall_at_threshold = Column(Float)
    f1_at_threshold = Column(Float)

    # Relationships
    model_type = relationship("ModelType", lazy="selectin")
    best_model = relationship(
        "BestModel",
        back_populates="models",
        lazy="selectin",
        foreign_keys=[best_model_id],
    )

    __table_args__ = (
        UniqueConstraint(
            "model_type_id", "best_model_id", name="uq_model_composite"
        ),
    )
