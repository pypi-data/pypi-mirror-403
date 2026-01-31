from enum import Enum
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
)
from sqlalchemy import desc, asc, cast, text, func

from sqlalchemy.orm import relationship, Mapped, mapped_column, DeclarativeBase, validates

from lecrapaud.db.session import get_db
from lecrapaud.models.base import Base
from lecrapaud.models.feature_selection import (
    lecrapaud_feature_selection_association,
)


class FeatureType(str, Enum):
    """Enum for feature types.

    Inherits from str to allow direct comparison with string values
    and automatic JSON serialization.
    """
    CATEGORICAL = "categorical"
    NUMERICAL = "numerical"

    @classmethod
    def get_all_values(cls) -> list[str]:
        """Return all type names as strings."""
        return [t.value for t in cls]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Check if a value is a valid type name."""
        return value in cls.get_all_values()


class Feature(Base):
    """SQLAlchemy model for feature metadata.

    Stores information about individual features used in experiments.
    Features are linked to feature selections through a many-to-many
    relationship.

    Attributes:
        id: Unique feature identifier.
        name: Feature column name (unique across all features).
        type: Feature type (categorical or numerical).
        feature_selections: Feature selections containing this feature.
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
    name = Column(String(50), nullable=False, unique=True)
    type = Column(String(50))

    @validates("type")
    def validate_type(self, key, value):
        """Validate that type is a valid FeatureType value.

        Accepts both enum members and string values.
        """
        if value is None:
            return value

        # Convert enum to string value
        if isinstance(value, FeatureType):
            return value.value

        # Validate string value
        if not FeatureType.is_valid(value):
            valid_types = FeatureType.get_all_values()
            raise ValueError(
                f"Invalid type '{value}'. Must be one of: {valid_types}"
            )
        return value

    feature_selections = relationship(
        "FeatureSelection",
        secondary=lecrapaud_feature_selection_association,
        back_populates="features",
        lazy="selectin",
    )
