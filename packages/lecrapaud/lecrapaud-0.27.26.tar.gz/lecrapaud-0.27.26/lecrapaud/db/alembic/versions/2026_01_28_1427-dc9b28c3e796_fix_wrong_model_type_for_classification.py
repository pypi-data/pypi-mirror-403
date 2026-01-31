"""fix_wrong_model_type_for_classification

Revision ID: dc9b28c3e796
Revises: 080475ab231a
Create Date: 2026-01-28 14:27:19

This migration fixes Model records that were incorrectly created with
mismatched ModelType for targets. It:
1. Finds Model records where target.type != model_type.type (bad models)
2. If a good Model exists (same best_model_id, same model_type.name, correct type):
   - Transfer artifacts/datas/best_model.best_model_id to it
   - Delete the bad model
3. If no good Model exists:
   - Update the bad model's model_type_id to point to the correct ModelType
4. Always update best_model.best_model_type_id to point to the correct ModelType
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from lecrapaud.config import LECRAPAUD_TABLE_PREFIX

# revision identifiers, used by Alembic.
revision: str = 'dc9b28c3e796'
down_revision: Union[str, None] = '080475ab231a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix Model records with mismatched ModelType for targets."""
    conn = op.get_bind()

    # Step 1: Find ALL bad Model records where target.type != model_type.type
    # Include whether a good model exists or not
    result = conn.execute(sa.text(f"""
        SELECT
            bad_m.id as bad_model_id,
            good_m.id as good_model_id,
            t.type as target_type,
            bad_mt.type as bad_model_type,
            bad_mt.name as model_name,
            bad_m.best_model_id,
            correct_mt.id as correct_model_type_id
        FROM {LECRAPAUD_TABLE_PREFIX}_models bad_m
        JOIN {LECRAPAUD_TABLE_PREFIX}_model_types bad_mt ON bad_m.model_type_id = bad_mt.id
        JOIN {LECRAPAUD_TABLE_PREFIX}_best_models bm ON bad_m.best_model_id = bm.id
        JOIN {LECRAPAUD_TABLE_PREFIX}_targets t ON bm.target_id = t.id
        -- Find the correct ModelType (same name, correct type)
        LEFT JOIN {LECRAPAUD_TABLE_PREFIX}_model_types correct_mt ON (
            correct_mt.name = bad_mt.name
            AND correct_mt.type = t.type
        )
        -- Find the "good" Model with same best_model_id, same model_type.name, correct type
        LEFT JOIN {LECRAPAUD_TABLE_PREFIX}_models good_m ON (
            good_m.best_model_id = bad_m.best_model_id
            AND good_m.id != bad_m.id
            AND good_m.model_type_id = correct_mt.id
        )
        WHERE
            -- Mismatch: target.type != model_type.type
            t.type != bad_mt.type
    """))

    rows = result.fetchall()

    if not rows:
        print("No incorrect Model records found to fix")
        return

    print(f"Found {len(rows)} incorrect Model records to fix")

    # Separate into two cases: with good model and without
    with_good_model = [(row[0], row[1], row[2], row[3], row[4], row[5], row[6]) for row in rows if row[1] is not None]
    without_good_model = [(row[0], row[1], row[2], row[3], row[4], row[5], row[6]) for row in rows if row[1] is None]

    print(f"  - {len(with_good_model)} have a good model to transfer to")
    print(f"  - {len(without_good_model)} need model_type_id correction")

    # ==========================================
    # Case A: Good model exists - transfer and delete bad model
    # ==========================================
    for bad_model_id, good_model_id, target_type, bad_model_type, model_name, best_model_id, correct_mt_id in with_good_model:
        print(f"  Transferring Bad Model {bad_model_id} ({bad_model_type}) -> Good Model {good_model_id} ({target_type}, {model_name})")

        # A1: Update BestModel.best_model_id to point to the good Model
        result = conn.execute(sa.text(f"""
            UPDATE {LECRAPAUD_TABLE_PREFIX}_best_models
            SET best_model_id = :good_id
            WHERE best_model_id = :bad_id
        """), {"good_id": good_model_id, "bad_id": bad_model_id})
        if result.rowcount > 0:
            print(f"    Updated {result.rowcount} BestModel(s): best_model_id {bad_model_id} -> {good_model_id}")

        # A2: Transfer artifacts (or nullify if duplicate exists)
        duplicate_artifact_ids = conn.execute(sa.text(f"""
            SELECT bad_art.id
            FROM {LECRAPAUD_TABLE_PREFIX}_experiment_artifacts bad_art
            JOIN {LECRAPAUD_TABLE_PREFIX}_experiment_artifacts good_art ON (
                good_art.experiment_id = bad_art.experiment_id
                AND (good_art.target_id = bad_art.target_id OR (good_art.target_id IS NULL AND bad_art.target_id IS NULL))
                AND good_art.artifact_type = bad_art.artifact_type
                AND good_art.artifact_name = bad_art.artifact_name
                AND good_art.model_id = :good_id
            )
            WHERE bad_art.model_id = :bad_id
        """), {"good_id": good_model_id, "bad_id": bad_model_id}).fetchall()

        if duplicate_artifact_ids:
            ids_to_nullify = [r[0] for r in duplicate_artifact_ids]
            print(f"    Setting model_id=NULL for {len(ids_to_nullify)} duplicate artifacts")
            for art_id in ids_to_nullify:
                conn.execute(sa.text(f"""
                    UPDATE {LECRAPAUD_TABLE_PREFIX}_experiment_artifacts
                    SET model_id = NULL
                    WHERE id = :art_id
                """), {"art_id": art_id})

        result = conn.execute(sa.text(f"""
            UPDATE {LECRAPAUD_TABLE_PREFIX}_experiment_artifacts
            SET model_id = :good_id
            WHERE model_id = :bad_id
        """), {"good_id": good_model_id, "bad_id": bad_model_id})
        if result.rowcount > 0:
            print(f"    Transferred {result.rowcount} artifacts")

        # A3: Transfer datas (or nullify if duplicate exists)
        duplicate_data_ids = conn.execute(sa.text(f"""
            SELECT bad_data.id
            FROM {LECRAPAUD_TABLE_PREFIX}_experiment_datas bad_data
            JOIN {LECRAPAUD_TABLE_PREFIX}_experiment_datas good_data ON (
                good_data.experiment_id = bad_data.experiment_id
                AND (good_data.target_id = bad_data.target_id OR (good_data.target_id IS NULL AND bad_data.target_id IS NULL))
                AND good_data.data_type = bad_data.data_type
                AND good_data.model_id = :good_id
            )
            WHERE bad_data.model_id = :bad_id
        """), {"good_id": good_model_id, "bad_id": bad_model_id}).fetchall()

        if duplicate_data_ids:
            ids_to_nullify = [r[0] for r in duplicate_data_ids]
            print(f"    Setting model_id=NULL for {len(ids_to_nullify)} duplicate datas")
            for data_id in ids_to_nullify:
                conn.execute(sa.text(f"""
                    UPDATE {LECRAPAUD_TABLE_PREFIX}_experiment_datas
                    SET model_id = NULL
                    WHERE id = :data_id
                """), {"data_id": data_id})

        result = conn.execute(sa.text(f"""
            UPDATE {LECRAPAUD_TABLE_PREFIX}_experiment_datas
            SET model_id = :good_id
            WHERE model_id = :bad_id
        """), {"good_id": good_model_id, "bad_id": bad_model_id})
        if result.rowcount > 0:
            print(f"    Transferred {result.rowcount} datas")

        # A4: Delete the bad Model
        conn.execute(sa.text(f"""
            DELETE FROM {LECRAPAUD_TABLE_PREFIX}_models
            WHERE id = :bad_id
        """), {"bad_id": bad_model_id})
        print(f"    Deleted bad Model {bad_model_id}")

    # ==========================================
    # Case B: No good model - update model_type_id
    # ==========================================
    for bad_model_id, _, target_type, bad_model_type, model_name, best_model_id, correct_mt_id in without_good_model:
        if correct_mt_id is None:
            print(f"  WARNING: No correct ModelType found for Model {bad_model_id} ({model_name}, {target_type})")
            continue

        print(f"  Correcting Model {bad_model_id}: model_type {bad_model_type} -> {target_type} (name={model_name})")

        # B1: Update the bad model's model_type_id to the correct ModelType
        conn.execute(sa.text(f"""
            UPDATE {LECRAPAUD_TABLE_PREFIX}_models
            SET model_type_id = :correct_mt_id
            WHERE id = :bad_id
        """), {"correct_mt_id": correct_mt_id, "bad_id": bad_model_id})
        print(f"    Updated model_type_id to {correct_mt_id}")

    # ==========================================
    # Step 2: Update ALL best_models.best_model_type_id to match correct ModelType
    # ==========================================
    print("\nUpdating best_model_type_id for all BestModels...")
    result = conn.execute(sa.text(f"""
        UPDATE {LECRAPAUD_TABLE_PREFIX}_best_models bm
        JOIN {LECRAPAUD_TABLE_PREFIX}_targets t ON bm.target_id = t.id
        JOIN {LECRAPAUD_TABLE_PREFIX}_model_types old_mt ON bm.best_model_type_id = old_mt.id
        JOIN {LECRAPAUD_TABLE_PREFIX}_model_types correct_mt ON (
            correct_mt.name = old_mt.name
            AND correct_mt.type = t.type
        )
        SET bm.best_model_type_id = correct_mt.id
        WHERE old_mt.type != t.type
    """))
    if result.rowcount > 0:
        print(f"  Updated {result.rowcount} BestModel(s) best_model_type_id")

    # ==========================================
    # Step 3: Clean up orphaned ModelType records
    # ==========================================
    result = conn.execute(sa.text(f"""
        DELETE mt FROM {LECRAPAUD_TABLE_PREFIX}_model_types mt
        LEFT JOIN {LECRAPAUD_TABLE_PREFIX}_models m ON m.model_type_id = mt.id
        LEFT JOIN {LECRAPAUD_TABLE_PREFIX}_best_models bm ON bm.best_model_type_id = mt.id
        WHERE mt.type IN ('regression', 'classification')
        AND m.id IS NULL
        AND bm.id IS NULL
    """))
    if result.rowcount > 0:
        print(f"  Cleaned up {result.rowcount} orphaned ModelType records")

    print("\nMigration complete")


def downgrade() -> None:
    """Downgrade is not supported - the bad data cannot be recreated."""
    pass
