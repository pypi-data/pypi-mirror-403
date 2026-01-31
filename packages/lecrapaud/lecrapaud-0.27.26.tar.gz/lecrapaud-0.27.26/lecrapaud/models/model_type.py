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


class ModelType(Base):
    """SQLAlchemy model for the model type registry.

    Stores unique combinations of model name and task type. Acts as a
    lookup table for referencing models consistently across experiments.

    Attributes:
        id: Unique model type identifier.
        name: Model name (e.g., "lgb", "xgb", "catboost", "random_forest").
        type: Task type ("classification" or "regression").

    Note:
        The (name, type) combination is unique, so "lgb" for classification
        and "lgb" for regression are separate entries.
    """

    __tablename__ = f"{LECRAPAUD_TABLE_PREFIX}_model_types"

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

    __table_args__ = (
        UniqueConstraint("name", "type", name="uq_model_composite"),
        {"extend_existing": True},
    )
