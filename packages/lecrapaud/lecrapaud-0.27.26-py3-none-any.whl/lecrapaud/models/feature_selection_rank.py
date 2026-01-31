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
    UniqueConstraint,
)
from sqlalchemy import desc, asc, cast, text, func

from sqlalchemy.orm import relationship, Mapped, mapped_column, DeclarativeBase, validates
from sqlalchemy.dialects.mysql import insert

from lecrapaud.db.session import get_db
from lecrapaud.models.base import Base, with_db
from lecrapaud.config import LECRAPAUD_TABLE_PREFIX


class FeatureSelectionMethod(str, Enum):
    """Enum for feature selection method names.

    Inherits from str to allow direct comparison with string values
    and automatic JSON serialization.
    """
    CHI2 = "Chi2"
    ANOVA = "ANOVA"
    FI = "FI"
    KENDALLS_TAU = "Kendall's Tau"
    MUTUAL_INFORMATION = "Mutual Information"
    PCA = "PCA"
    RFE = "RFE"
    PEARSONS_R = "Pearson's R"
    SPEARMANS_R = "Spearman's R"
    SFS = "SFS"
    ENSEMBLE = "ensemble"

    @classmethod
    def get_all_values(cls) -> list[str]:
        """Return all method names as strings."""
        return [m.value for m in cls]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Check if a value is a valid method name."""
        return value in cls.get_all_values()


class FeatureSelectionRank(Base):
    """SQLAlchemy model for feature importance rankings.

    Stores the ranking and score of a feature for a specific selection
    method (Chi2, ANOVA, mutual information, etc.). Multiple rankings
    exist per feature selection - one for each method used.

    Attributes:
        id: Unique rank identifier.
        score: Feature importance score from the selection method.
        pvalue: Statistical p-value if applicable.
        support: Number of methods that selected this feature.
        rank: Feature rank (1 = most important).
        method: Selection method used (see FeatureSelectionMethod enum).
        training_time: Time taken for this method in seconds.
        feature_id: Associated feature ID.
        feature_selection_id: Associated feature selection ID.
        feature: Relationship to Feature.
        feature_selection: Relationship to FeatureSelection.
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
    score = Column(Float)
    pvalue = Column(Float)
    support = Column(Integer)
    rank = Column(Integer)
    method = Column(String(50))
    training_time = Column(Integer)
    feature_id = Column(
        BigInteger,
        ForeignKey(f"{LECRAPAUD_TABLE_PREFIX}_features.id", ondelete="CASCADE"),
    )
    feature_selection_id = Column(
        BigInteger,
        ForeignKey(
            f"{LECRAPAUD_TABLE_PREFIX}_feature_selections.id", ondelete="CASCADE"
        ),
    )

    feature = relationship("Feature", lazy="selectin")
    feature_selection = relationship(
        "FeatureSelection", back_populates="feature_selection_ranks", lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint(
            "feature_id",
            "feature_selection_id",
            "method",
            name="uq_feature_selection_rank_composite",
        ),
    )

    @validates("method")
    def validate_method(self, key, value):
        """Validate that method is a valid FeatureSelectionMethod value.

        Accepts both enum members and string values.
        """
        if value is None:
            return value

        # Convert enum to string value
        if isinstance(value, FeatureSelectionMethod):
            return value.value

        # Validate string value
        if not FeatureSelectionMethod.is_valid(value):
            valid_methods = FeatureSelectionMethod.get_all_values()
            raise ValueError(
                f"Invalid method '{value}'. Must be one of: {valid_methods}"
            )
        return value
