"""rename_model_to_model_type

Revision ID: f723ecc52b89
Revises: b2c3d4e5f6g7
Create Date: 2026-01-26 19:42:20.930251

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from lecrapaud.config import LECRAPAUD_TABLE_PREFIX

# revision identifiers, used by Alembic.
revision: str = 'f723ecc52b89'
down_revision: Union[str, None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Rename table models -> model_types
    op.rename_table(f'{LECRAPAUD_TABLE_PREFIX}_models', f'{LECRAPAUD_TABLE_PREFIX}_model_types')

    # 2. Rename column model_id -> model_type_id in model_selection_scores
    op.alter_column(f'{LECRAPAUD_TABLE_PREFIX}_model_selection_scores', 'model_id',
                    new_column_name='model_type_id',
                    existing_type=sa.BigInteger(),
                    existing_nullable=False)

    # 3. Rename column best_model_id -> best_model_type_id in model_selections
    op.alter_column(f'{LECRAPAUD_TABLE_PREFIX}_model_selections', 'best_model_id',
                    new_column_name='best_model_type_id',
                    existing_type=sa.BigInteger(),
                    existing_nullable=True)


def downgrade() -> None:
    # 1. Rename column best_model_type_id -> best_model_id in model_selections
    op.alter_column(f'{LECRAPAUD_TABLE_PREFIX}_model_selections', 'best_model_type_id',
                    new_column_name='best_model_id',
                    existing_type=sa.BigInteger(),
                    existing_nullable=True)

    # 2. Rename column model_type_id -> model_id in model_selection_scores
    op.alter_column(f'{LECRAPAUD_TABLE_PREFIX}_model_selection_scores', 'model_type_id',
                    new_column_name='model_id',
                    existing_type=sa.BigInteger(),
                    existing_nullable=False)

    # 3. Rename table model_types -> models
    op.rename_table(f'{LECRAPAUD_TABLE_PREFIX}_model_types', f'{LECRAPAUD_TABLE_PREFIX}_models')
