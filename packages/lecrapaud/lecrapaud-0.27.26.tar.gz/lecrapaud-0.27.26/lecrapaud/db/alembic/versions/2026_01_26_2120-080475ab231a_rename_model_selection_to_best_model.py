"""rename_model_selection_to_best_model

Revision ID: 080475ab231a
Revises: f723ecc52b89
Create Date: 2026-01-26 21:20:29.363327

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from lecrapaud.config import LECRAPAUD_TABLE_PREFIX

# revision identifiers, used by Alembic.
revision: str = '080475ab231a'
down_revision: Union[str, None] = 'f723ecc52b89'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _fk_exists(conn, table_name, constraint_name):
    """Check if a foreign key constraint exists."""
    result = conn.execute(sa.text(f"""
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = '{table_name}'
        AND CONSTRAINT_NAME = '{constraint_name}'
        AND CONSTRAINT_TYPE = 'FOREIGN KEY'
    """))
    return result.scalar() > 0


def _column_exists(conn, table_name, column_name):
    """Check if a column exists."""
    result = conn.execute(sa.text(f"""
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = '{table_name}'
        AND COLUMN_NAME = '{column_name}'
    """))
    return result.scalar() > 0


def _constraint_exists(conn, table_name, constraint_name):
    """Check if a constraint (any type) exists."""
    result = conn.execute(sa.text(f"""
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = '{table_name}'
        AND CONSTRAINT_NAME = '{constraint_name}'
    """))
    return result.scalar() > 0


def upgrade() -> None:
    conn = op.get_bind()

    # Step 1: Rename model_selection_scores -> models
    # Rename column model_selection_id -> best_model_id if it exists (might already be renamed)
    if _column_exists(conn, f'{LECRAPAUD_TABLE_PREFIX}_model_selection_scores', 'model_selection_id'):
        op.alter_column(
            f'{LECRAPAUD_TABLE_PREFIX}_model_selection_scores',
            'model_selection_id',
            new_column_name='best_model_id',
            existing_type=sa.BigInteger(),
            existing_nullable=False
        )

    # Rename table model_selection_scores -> models
    op.rename_table(
        f'{LECRAPAUD_TABLE_PREFIX}_model_selection_scores',
        f'{LECRAPAUD_TABLE_PREFIX}_models'
    )

    # Step 2: Rename model_selections -> best_models
    # Rename column best_model_selection_score_id -> best_model_id
    if _column_exists(conn, f'{LECRAPAUD_TABLE_PREFIX}_model_selections', 'best_model_selection_score_id'):
        op.alter_column(
            f'{LECRAPAUD_TABLE_PREFIX}_model_selections',
            'best_model_selection_score_id',
            new_column_name='best_model_id',
            existing_type=sa.BigInteger(),
            existing_nullable=True
        )

    # Rename table model_selections -> best_models
    op.rename_table(
        f'{LECRAPAUD_TABLE_PREFIX}_model_selections',
        f'{LECRAPAUD_TABLE_PREFIX}_best_models'
    )

    # Step 3: Create new foreign keys (if they don't already exist)
    # FK from models.best_model_id -> best_models.id
    if not _fk_exists(conn, f'{LECRAPAUD_TABLE_PREFIX}_models', f'{LECRAPAUD_TABLE_PREFIX}_models_ibfk_2'):
        op.create_foreign_key(
            f'{LECRAPAUD_TABLE_PREFIX}_models_ibfk_2',
            f'{LECRAPAUD_TABLE_PREFIX}_models',
            f'{LECRAPAUD_TABLE_PREFIX}_best_models',
            ['best_model_id'],
            ['id'],
            ondelete='CASCADE'
        )

    # FK from best_models.best_model_id -> models.id
    if not _fk_exists(conn, f'{LECRAPAUD_TABLE_PREFIX}_best_models', f'fk_{LECRAPAUD_TABLE_PREFIX}_best_models_best_model'):
        op.create_foreign_key(
            f'fk_{LECRAPAUD_TABLE_PREFIX}_best_models_best_model',
            f'{LECRAPAUD_TABLE_PREFIX}_best_models',
            f'{LECRAPAUD_TABLE_PREFIX}_models',
            ['best_model_id'],
            ['id'],
            ondelete='SET NULL'
        )

    # Step 4: Update experiment_artifacts - rename model_selection_score_id -> model_id
    if _column_exists(conn, f'{LECRAPAUD_TABLE_PREFIX}_experiment_artifacts', 'model_selection_score_id'):
        op.alter_column(
            f'{LECRAPAUD_TABLE_PREFIX}_experiment_artifacts',
            'model_selection_score_id',
            new_column_name='model_id',
            existing_type=sa.BigInteger(),
            existing_nullable=True
        )

    # Create FK for model_id (if not exists)
    if not _fk_exists(conn, f'{LECRAPAUD_TABLE_PREFIX}_experiment_artifacts', f'{LECRAPAUD_TABLE_PREFIX}_experiment_artifacts_ibfk_3'):
        op.create_foreign_key(
            f'{LECRAPAUD_TABLE_PREFIX}_experiment_artifacts_ibfk_3',
            f'{LECRAPAUD_TABLE_PREFIX}_experiment_artifacts',
            f'{LECRAPAUD_TABLE_PREFIX}_models',
            ['model_id'],
            ['id'],
            ondelete='CASCADE'
        )

    # Step 5: Update experiment_datas - rename model_selection_score_id -> model_id
    # Drop old unique constraint if it exists
    if _constraint_exists(conn, f'{LECRAPAUD_TABLE_PREFIX}_experiment_datas', f'uq_{LECRAPAUD_TABLE_PREFIX}_experiment_datas_composite'):
        op.drop_constraint(
            f'uq_{LECRAPAUD_TABLE_PREFIX}_experiment_datas_composite',
            f'{LECRAPAUD_TABLE_PREFIX}_experiment_datas',
            type_='unique'
        )

    if _column_exists(conn, f'{LECRAPAUD_TABLE_PREFIX}_experiment_datas', 'model_selection_score_id'):
        op.alter_column(
            f'{LECRAPAUD_TABLE_PREFIX}_experiment_datas',
            'model_selection_score_id',
            new_column_name='model_id',
            existing_type=sa.BigInteger(),
            existing_nullable=True
        )

    # Create FK for model_id (if not exists)
    if not _fk_exists(conn, f'{LECRAPAUD_TABLE_PREFIX}_experiment_datas', f'{LECRAPAUD_TABLE_PREFIX}_experiment_datas_ibfk_3'):
        op.create_foreign_key(
            f'{LECRAPAUD_TABLE_PREFIX}_experiment_datas_ibfk_3',
            f'{LECRAPAUD_TABLE_PREFIX}_experiment_datas',
            f'{LECRAPAUD_TABLE_PREFIX}_models',
            ['model_id'],
            ['id'],
            ondelete='CASCADE'
        )

    # Recreate unique constraint with new column name (if not exists)
    if not _constraint_exists(conn, f'{LECRAPAUD_TABLE_PREFIX}_experiment_datas', f'uq_{LECRAPAUD_TABLE_PREFIX}_experiment_data_composite'):
        op.create_unique_constraint(
            f'uq_{LECRAPAUD_TABLE_PREFIX}_experiment_data_composite',
            f'{LECRAPAUD_TABLE_PREFIX}_experiment_datas',
            ['experiment_id', 'target_id', 'data_type', 'model_id']
        )


def downgrade() -> None:
    conn = op.get_bind()

    # Step 1: Revert experiment_datas
    if _constraint_exists(conn, f'{LECRAPAUD_TABLE_PREFIX}_experiment_datas', f'uq_{LECRAPAUD_TABLE_PREFIX}_experiment_data_composite'):
        op.drop_constraint(
            f'uq_{LECRAPAUD_TABLE_PREFIX}_experiment_data_composite',
            f'{LECRAPAUD_TABLE_PREFIX}_experiment_datas',
            type_='unique'
        )

    if _fk_exists(conn, f'{LECRAPAUD_TABLE_PREFIX}_experiment_datas', f'{LECRAPAUD_TABLE_PREFIX}_experiment_datas_ibfk_3'):
        op.drop_constraint(
            f'{LECRAPAUD_TABLE_PREFIX}_experiment_datas_ibfk_3',
            f'{LECRAPAUD_TABLE_PREFIX}_experiment_datas',
            type_='foreignkey'
        )

    if _column_exists(conn, f'{LECRAPAUD_TABLE_PREFIX}_experiment_datas', 'model_id'):
        op.alter_column(
            f'{LECRAPAUD_TABLE_PREFIX}_experiment_datas',
            'model_id',
            new_column_name='model_selection_score_id',
            existing_type=sa.BigInteger(),
            existing_nullable=True
        )

    # Step 2: Revert experiment_artifacts
    if _fk_exists(conn, f'{LECRAPAUD_TABLE_PREFIX}_experiment_artifacts', f'{LECRAPAUD_TABLE_PREFIX}_experiment_artifacts_ibfk_3'):
        op.drop_constraint(
            f'{LECRAPAUD_TABLE_PREFIX}_experiment_artifacts_ibfk_3',
            f'{LECRAPAUD_TABLE_PREFIX}_experiment_artifacts',
            type_='foreignkey'
        )

    if _column_exists(conn, f'{LECRAPAUD_TABLE_PREFIX}_experiment_artifacts', 'model_id'):
        op.alter_column(
            f'{LECRAPAUD_TABLE_PREFIX}_experiment_artifacts',
            'model_id',
            new_column_name='model_selection_score_id',
            existing_type=sa.BigInteger(),
            existing_nullable=True
        )

    # Step 3: Drop new constraints and FKs
    if _constraint_exists(conn, f'{LECRAPAUD_TABLE_PREFIX}_best_models', 'uq_best_model_composite'):
        op.drop_constraint(
            'uq_best_model_composite',
            f'{LECRAPAUD_TABLE_PREFIX}_best_models',
            type_='unique'
        )

    if _constraint_exists(conn, f'{LECRAPAUD_TABLE_PREFIX}_models', 'uq_model_composite'):
        op.drop_constraint(
            'uq_model_composite',
            f'{LECRAPAUD_TABLE_PREFIX}_models',
            type_='unique'
        )

    if _fk_exists(conn, f'{LECRAPAUD_TABLE_PREFIX}_best_models', f'fk_{LECRAPAUD_TABLE_PREFIX}_best_models_best_model'):
        op.drop_constraint(
            f'fk_{LECRAPAUD_TABLE_PREFIX}_best_models_best_model',
            f'{LECRAPAUD_TABLE_PREFIX}_best_models',
            type_='foreignkey'
        )

    if _fk_exists(conn, f'{LECRAPAUD_TABLE_PREFIX}_models', f'{LECRAPAUD_TABLE_PREFIX}_models_ibfk_2'):
        op.drop_constraint(
            f'{LECRAPAUD_TABLE_PREFIX}_models_ibfk_2',
            f'{LECRAPAUD_TABLE_PREFIX}_models',
            type_='foreignkey'
        )

    # Step 4: Rename best_models -> model_selections
    op.rename_table(
        f'{LECRAPAUD_TABLE_PREFIX}_best_models',
        f'{LECRAPAUD_TABLE_PREFIX}_model_selections'
    )

    if _column_exists(conn, f'{LECRAPAUD_TABLE_PREFIX}_model_selections', 'best_model_id'):
        op.alter_column(
            f'{LECRAPAUD_TABLE_PREFIX}_model_selections',
            'best_model_id',
            new_column_name='best_model_selection_score_id',
            existing_type=sa.BigInteger(),
            existing_nullable=True
        )

    # Step 5: Rename models -> model_selection_scores
    op.rename_table(
        f'{LECRAPAUD_TABLE_PREFIX}_models',
        f'{LECRAPAUD_TABLE_PREFIX}_model_selection_scores'
    )

    if _column_exists(conn, f'{LECRAPAUD_TABLE_PREFIX}_model_selection_scores', 'best_model_id'):
        op.alter_column(
            f'{LECRAPAUD_TABLE_PREFIX}_model_selection_scores',
            'best_model_id',
            new_column_name='model_selection_id',
            existing_type=sa.BigInteger(),
            existing_nullable=False
        )

    # Step 6: Recreate old constraints and FKs
    op.create_unique_constraint(
        'uq_model_selection_composite',
        f'{LECRAPAUD_TABLE_PREFIX}_model_selections',
        ['target_id', 'experiment_id']
    )

    op.create_unique_constraint(
        'uq_model_selection_score_composite',
        f'{LECRAPAUD_TABLE_PREFIX}_model_selection_scores',
        ['model_type_id', 'model_selection_id']
    )

    op.create_foreign_key(
        f'{LECRAPAUD_TABLE_PREFIX}_model_selection_scores_ibfk_2',
        f'{LECRAPAUD_TABLE_PREFIX}_model_selection_scores',
        f'{LECRAPAUD_TABLE_PREFIX}_model_selections',
        ['model_selection_id'],
        ['id'],
        ondelete='CASCADE'
    )

    op.create_foreign_key(
        f'fk_{LECRAPAUD_TABLE_PREFIX}_model_selections_best_score',
        f'{LECRAPAUD_TABLE_PREFIX}_model_selections',
        f'{LECRAPAUD_TABLE_PREFIX}_model_selection_scores',
        ['best_model_selection_score_id'],
        ['id'],
        ondelete='SET NULL'
    )

    op.create_unique_constraint(
        f'uq_{LECRAPAUD_TABLE_PREFIX}_experiment_datas_composite',
        f'{LECRAPAUD_TABLE_PREFIX}_experiment_datas',
        ['experiment_id', 'target_id', 'data_type', 'model_selection_score_id']
    )
