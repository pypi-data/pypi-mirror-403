"""add artifact and data storage tables

Revision ID: a1b2c3d4e5f6
Revises: 99108bd42b68
Create Date: 2026-01-21 18:14:00

This migration creates the experiment_artifacts and experiment_datas tables
for database-based artifact storage, and adds best_model_selection_score_id
to model_selections.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from lecrapaud.config import LECRAPAUD_TABLE_PREFIX


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "99108bd42b68"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use LONGBLOB for MySQL to handle large binary data (models can be >64KB)
    # LargeBinary defaults to BLOB (64KB max) on MySQL
    data_column_type = sa.LargeBinary().with_variant(mysql.LONGBLOB(), "mysql")

    # Create experiment_artifacts table (pluralized to match SQLAlchemy model)
    op.create_table(
        f"{LECRAPAUD_TABLE_PREFIX}_experiment_artifacts",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("experiment_id", sa.BigInteger(), nullable=False),
        sa.Column("target_id", sa.BigInteger(), nullable=True),
        sa.Column("model_selection_score_id", sa.BigInteger(), nullable=True),
        sa.Column("artifact_type", sa.String(50), nullable=False),
        sa.Column("artifact_name", sa.String(100), nullable=False),
        sa.Column("data", data_column_type, nullable=False),
        sa.Column("serialization_format", sa.String(20), nullable=False, default="joblib"),
        sa.ForeignKeyConstraint(
            ["experiment_id"],
            [f"{LECRAPAUD_TABLE_PREFIX}_experiments.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["target_id"],
            [f"{LECRAPAUD_TABLE_PREFIX}_targets.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["model_selection_score_id"],
            [f"{LECRAPAUD_TABLE_PREFIX}_model_selection_scores.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "experiment_id",
            "target_id",
            "artifact_type",
            "artifact_name",
            name=f"uq_{LECRAPAUD_TABLE_PREFIX}_experiment_artifact_composite",
        ),
    )
    op.create_index(
        f"ix_{LECRAPAUD_TABLE_PREFIX}_experiment_artifacts_experiment_id",
        f"{LECRAPAUD_TABLE_PREFIX}_experiment_artifacts",
        ["experiment_id"],
    )
    op.create_index(
        f"ix_{LECRAPAUD_TABLE_PREFIX}_experiment_artifacts_target_id",
        f"{LECRAPAUD_TABLE_PREFIX}_experiment_artifacts",
        ["target_id"],
    )
    op.create_index(
        f"ix_{LECRAPAUD_TABLE_PREFIX}_experiment_artifacts_model_selection_score_id",
        f"{LECRAPAUD_TABLE_PREFIX}_experiment_artifacts",
        ["model_selection_score_id"],
    )

    # Create experiment_datas table (pluralized to match SQLAlchemy model)
    op.create_table(
        f"{LECRAPAUD_TABLE_PREFIX}_experiment_datas",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("experiment_id", sa.BigInteger(), nullable=False),
        sa.Column("target_id", sa.BigInteger(), nullable=True),
        sa.Column("model_selection_score_id", sa.BigInteger(), nullable=True),
        sa.Column("data_type", sa.String(50), nullable=False),
        sa.Column("data", data_column_type, nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("column_count", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["experiment_id"],
            [f"{LECRAPAUD_TABLE_PREFIX}_experiments.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["target_id"],
            [f"{LECRAPAUD_TABLE_PREFIX}_targets.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["model_selection_score_id"],
            [f"{LECRAPAUD_TABLE_PREFIX}_model_selection_scores.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "experiment_id",
            "target_id",
            "data_type",
            "model_selection_score_id",
            name=f"uq_{LECRAPAUD_TABLE_PREFIX}_experiment_datas_composite",
        ),
    )
    op.create_index(
        f"ix_{LECRAPAUD_TABLE_PREFIX}_experiment_datas_experiment_id",
        f"{LECRAPAUD_TABLE_PREFIX}_experiment_datas",
        ["experiment_id"],
    )
    op.create_index(
        f"ix_{LECRAPAUD_TABLE_PREFIX}_experiment_datas_target_id",
        f"{LECRAPAUD_TABLE_PREFIX}_experiment_datas",
        ["target_id"],
    )
    op.create_index(
        f"ix_{LECRAPAUD_TABLE_PREFIX}_experiment_datas_model_selection_score_id",
        f"{LECRAPAUD_TABLE_PREFIX}_experiment_datas",
        ["model_selection_score_id"],
    )

    # Add best_model_selection_score_id to model_selections
    op.add_column(
        f'{LECRAPAUD_TABLE_PREFIX}_model_selections',
        sa.Column('best_model_selection_score_id', sa.BigInteger(), nullable=True)
    )
    op.create_foreign_key(
        f'fk_{LECRAPAUD_TABLE_PREFIX}_model_selections_best_score',
        f'{LECRAPAUD_TABLE_PREFIX}_model_selections',
        f'{LECRAPAUD_TABLE_PREFIX}_model_selection_scores',
        ['best_model_selection_score_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Drop best_model_selection_score_id from model_selections
    op.drop_constraint(
        f'fk_{LECRAPAUD_TABLE_PREFIX}_model_selections_best_score',
        f'{LECRAPAUD_TABLE_PREFIX}_model_selections',
        type_='foreignkey'
    )
    op.drop_column(
        f'{LECRAPAUD_TABLE_PREFIX}_model_selections',
        'best_model_selection_score_id'
    )

    # Drop experiment_datas table
    op.drop_index(
        f"ix_{LECRAPAUD_TABLE_PREFIX}_experiment_datas_model_selection_score_id",
        table_name=f"{LECRAPAUD_TABLE_PREFIX}_experiment_datas",
    )
    op.drop_index(
        f"ix_{LECRAPAUD_TABLE_PREFIX}_experiment_datas_target_id",
        table_name=f"{LECRAPAUD_TABLE_PREFIX}_experiment_datas",
    )
    op.drop_index(
        f"ix_{LECRAPAUD_TABLE_PREFIX}_experiment_datas_experiment_id",
        table_name=f"{LECRAPAUD_TABLE_PREFIX}_experiment_datas",
    )
    op.drop_table(f"{LECRAPAUD_TABLE_PREFIX}_experiment_datas")

    # Drop experiment_artifacts table
    op.drop_index(
        f"ix_{LECRAPAUD_TABLE_PREFIX}_experiment_artifacts_model_selection_score_id",
        table_name=f"{LECRAPAUD_TABLE_PREFIX}_experiment_artifacts",
    )
    op.drop_index(
        f"ix_{LECRAPAUD_TABLE_PREFIX}_experiment_artifacts_target_id",
        table_name=f"{LECRAPAUD_TABLE_PREFIX}_experiment_artifacts",
    )
    op.drop_index(
        f"ix_{LECRAPAUD_TABLE_PREFIX}_experiment_artifacts_experiment_id",
        table_name=f"{LECRAPAUD_TABLE_PREFIX}_experiment_artifacts",
    )
    op.drop_table(f"{LECRAPAUD_TABLE_PREFIX}_experiment_artifacts")
