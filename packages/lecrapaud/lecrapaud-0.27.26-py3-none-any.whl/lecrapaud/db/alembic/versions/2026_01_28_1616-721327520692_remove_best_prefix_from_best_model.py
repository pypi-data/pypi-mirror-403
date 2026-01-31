"""remove_best_prefix_from_best_model

Revision ID: 721327520692
Revises: dc9b28c3e796
Create Date: 2026-01-28 16:16:25.655079

Remove the 'best_' prefix from columns in the best_models table:
- best_model_params -> params
- best_thresholds -> thresholds
- best_score -> score
- best_model_path -> model_path
- best_model_type_id -> model_type_id
- best_model_id -> model_id

Also rename in models table:
- best_params -> params
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from lecrapaud.config import LECRAPAUD_TABLE_PREFIX

# revision identifiers, used by Alembic.
revision: str = '721327520692'
down_revision: Union[str, None] = 'dc9b28c3e796'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename columns in best_models table to remove 'best_' prefix
    op.alter_column(
        f'{LECRAPAUD_TABLE_PREFIX}_best_models',
        'best_model_params',
        new_column_name='params',
        existing_type=sa.JSON(),
        existing_nullable=True
    )
    op.alter_column(
        f'{LECRAPAUD_TABLE_PREFIX}_best_models',
        'best_thresholds',
        new_column_name='thresholds',
        existing_type=sa.JSON(),
        existing_nullable=True
    )
    op.alter_column(
        f'{LECRAPAUD_TABLE_PREFIX}_best_models',
        'best_score',
        new_column_name='score',
        existing_type=sa.JSON(),
        existing_nullable=True
    )
    op.alter_column(
        f'{LECRAPAUD_TABLE_PREFIX}_best_models',
        'best_model_path',
        new_column_name='model_path',
        existing_type=sa.String(255),
        existing_nullable=True
    )
    op.alter_column(
        f'{LECRAPAUD_TABLE_PREFIX}_best_models',
        'best_model_type_id',
        new_column_name='model_type_id',
        existing_type=sa.BigInteger(),
        existing_nullable=True
    )
    op.alter_column(
        f'{LECRAPAUD_TABLE_PREFIX}_best_models',
        'best_model_id',
        new_column_name='model_id',
        existing_type=sa.BigInteger(),
        existing_nullable=True
    )

    # Rename best_params -> params in models table
    op.alter_column(
        f'{LECRAPAUD_TABLE_PREFIX}_models',
        'best_params',
        new_column_name='params',
        existing_type=sa.JSON(),
        existing_nullable=True
    )


def downgrade() -> None:
    # Revert: rename params -> best_params in models table
    op.alter_column(
        f'{LECRAPAUD_TABLE_PREFIX}_models',
        'params',
        new_column_name='best_params',
        existing_type=sa.JSON(),
        existing_nullable=True
    )

    # Revert: add 'best_' prefix back to columns in best_models
    op.alter_column(
        f'{LECRAPAUD_TABLE_PREFIX}_best_models',
        'model_id',
        new_column_name='best_model_id',
        existing_type=sa.BigInteger(),
        existing_nullable=True
    )
    op.alter_column(
        f'{LECRAPAUD_TABLE_PREFIX}_best_models',
        'model_type_id',
        new_column_name='best_model_type_id',
        existing_type=sa.BigInteger(),
        existing_nullable=True
    )
    op.alter_column(
        f'{LECRAPAUD_TABLE_PREFIX}_best_models',
        'model_path',
        new_column_name='best_model_path',
        existing_type=sa.String(255),
        existing_nullable=True
    )
    op.alter_column(
        f'{LECRAPAUD_TABLE_PREFIX}_best_models',
        'score',
        new_column_name='best_score',
        existing_type=sa.JSON(),
        existing_nullable=True
    )
    op.alter_column(
        f'{LECRAPAUD_TABLE_PREFIX}_best_models',
        'thresholds',
        new_column_name='best_thresholds',
        existing_type=sa.JSON(),
        existing_nullable=True
    )
    op.alter_column(
        f'{LECRAPAUD_TABLE_PREFIX}_best_models',
        'params',
        new_column_name='best_model_params',
        existing_type=sa.JSON(),
        existing_nullable=True
    )
