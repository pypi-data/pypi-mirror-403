"""fix_method_names

Revision ID: 0e47cb122c58
Revises: 138173cbee80
Create Date: 2026-01-28 17:21:57.466999

This migration normalizes method names in feature_selection_ranks table:
- 'chi2' -> 'Chi2'
- 'Person's R' -> 'Pearson's R'
- Any other case variations
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from lecrapaud.config import LECRAPAUD_TABLE_PREFIX

# revision identifiers, used by Alembic.
revision: str = '0e47cb122c58'
down_revision: Union[str, None] = '721327520692'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # Fix method names in feature_selection_ranks table
    # Mapping: (old_value, new_value)
    method_fixes = [
        ('chi2', 'Chi2'),
        ("Person's R", "Pearson's R"),
    ]

    for old_value, new_value in method_fixes:
        result = conn.execute(
            sa.text(f"""
                UPDATE `{LECRAPAUD_TABLE_PREFIX}_feature_selection_ranks`
                SET method = :new_value
                WHERE method = :old_value
            """),
            {"old_value": old_value, "new_value": new_value}
        )
        if result.rowcount > 0:
            print(f"  Updated {result.rowcount} records: '{old_value}' -> '{new_value}'")

    # Also fix data_type in experiment_datas table (feature_scores_* patterns)
    data_type_fixes = [
        ('feature_scores_chi2', 'feature_scores_Chi2'),
        ("feature_scores_Person's R", "feature_scores_Pearson's R"),
    ]

    for old_value, new_value in data_type_fixes:
        result = conn.execute(
            sa.text(f"""
                UPDATE `{LECRAPAUD_TABLE_PREFIX}_experiment_datas`
                SET data_type = :new_value
                WHERE data_type = :old_value
            """),
            {"old_value": old_value, "new_value": new_value}
        )
        if result.rowcount > 0:
            print(f"  Updated {result.rowcount} data_type records: '{old_value}' -> '{new_value}'")

    print("Method names normalization complete")


def downgrade() -> None:
    conn = op.get_bind()

    # Revert method names (though this is rarely needed)
    method_fixes = [
        ('Chi2', 'chi2'),
        ("Pearson's R", "Person's R"),
    ]

    for old_value, new_value in method_fixes:
        conn.execute(
            sa.text(f"""
                UPDATE `{LECRAPAUD_TABLE_PREFIX}_feature_selection_ranks`
                SET method = :new_value
                WHERE method = :old_value
            """),
            {"old_value": old_value, "new_value": new_value}
        )

    # Revert data_type in experiment_datas
    data_type_fixes = [
        ('feature_scores_Chi2', 'feature_scores_chi2'),
        ("feature_scores_Pearson's R", "feature_scores_Person's R"),
    ]

    for old_value, new_value in data_type_fixes:
        conn.execute(
            sa.text(f"""
                UPDATE `{LECRAPAUD_TABLE_PREFIX}_experiment_datas`
                SET data_type = :new_value
                WHERE data_type = :old_value
            """),
            {"old_value": old_value, "new_value": new_value}
        )

    print("Method names reverted")
