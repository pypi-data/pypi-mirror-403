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
from lecrapaud.models.experiment import lecrapaud_experiment_target_association


class Target(Base):
    """SQLAlchemy model for prediction targets.

    Represents a prediction target (e.g., TARGET_0, TARGET_1) that can be
    either a classification or regression task. Targets are shared across
    experiments through a many-to-many relationship.

    Attributes:
        id: Unique target identifier.
        name: Target name (e.g., "TARGET_0").
        type: Target type ("classification" or "regression").
        description: Optional human-readable description.
        experiments: Relationship to associated experiments.
        feature_selections: Selected features for this target.
        best_models: Best model records for this target.
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
    name = Column(String(50), nullable=False)
    type = Column(String(50), nullable=False)
    description = Column(String(255))

    experiments = relationship(
        "Experiment",
        secondary=lecrapaud_experiment_target_association,
        back_populates="targets",
        lazy="selectin",
    )
    feature_selections = relationship(
        "FeatureSelection",
        back_populates="target",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    best_models = relationship(
        "BestModel",
        back_populates="target",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint(
            "name",
            "type",
            name="uq_target_composite",
        ),
    )
