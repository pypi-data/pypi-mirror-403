from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Date,
    Float,
    JSON,
    Table,
    ForeignKey,
    BigInteger,
    Index,
    TIMESTAMP,
    UniqueConstraint,
)
from sqlalchemy import desc, asc, cast, text, func

from sqlalchemy.orm import relationship, Mapped, mapped_column, DeclarativeBase

from lecrapaud.db.session import get_db
from lecrapaud.models.base import Base
from lecrapaud.config import LECRAPAUD_TABLE_PREFIX


class BestModel(Base):
    """SQLAlchemy model for best model tracking per experiment-target pair.

    Serves as a container for all models trained for a specific experiment
    and target combination. Tracks which model is currently marked as best
    and stores shared configuration like thresholds.

    Attributes:
        id: Unique best model entry identifier.
        params: Best model hyperparameters (JSON).
        thresholds: Classification thresholds (JSON).
        score: Best model scores (JSON).
        model_path: Legacy file path (deprecated).
        model_type_id: Type of the best model.
        model_id: Reference to the currently selected best Model.
        target_id: Associated target ID.
        experiment_id: Associated experiment ID.
        model_type: Relationship to ModelType.
        model: The currently selected best Model.
        models: All trained models for this experiment-target pair.
        experiment: Relationship to Experiment.
        target: Relationship to Target.
    """

    __tablename__ = f"{LECRAPAUD_TABLE_PREFIX}_best_models"

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
    params = Column(JSON)
    thresholds = Column(JSON)
    score = Column(JSON)
    model_path = Column(String(255))
    model_type_id = Column(
        BigInteger,
        ForeignKey(f"{LECRAPAUD_TABLE_PREFIX}_model_types.id", ondelete="CASCADE"),
    )
    model_id = Column(
        BigInteger,
        ForeignKey(f"{LECRAPAUD_TABLE_PREFIX}_models.id", ondelete="SET NULL"),
    )
    target_id = Column(
        BigInteger,
        ForeignKey(f"{LECRAPAUD_TABLE_PREFIX}_targets.id", ondelete="CASCADE"),
        nullable=False,
    )
    experiment_id = Column(
        BigInteger,
        ForeignKey(f"{LECRAPAUD_TABLE_PREFIX}_experiments.id", ondelete="CASCADE"),
        nullable=False,
    )

    model_type = relationship("ModelType", lazy="selectin")
    model = relationship(
        "Model",
        foreign_keys=[model_id],
        lazy="selectin",
        post_update=True,  # Break circular dependency: insert first, then update FK
    )
    models = relationship(
        "Model",
        back_populates="best_model",
        cascade="all, delete-orphan",
        lazy="selectin",
        foreign_keys="[Model.best_model_id]",
    )
    experiment = relationship(
        "Experiment", back_populates="best_models", lazy="selectin"
    )
    target = relationship("Target", back_populates="best_models", lazy="selectin")

    __table_args__ = (
        UniqueConstraint(
            "target_id", "experiment_id", name="uq_best_model_composite"
        ),
    )
