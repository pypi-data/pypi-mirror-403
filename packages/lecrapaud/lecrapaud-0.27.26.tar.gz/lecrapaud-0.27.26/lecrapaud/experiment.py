"""Experiment creation and management module.

This module provides functions to create new LeCrapaud experiments,
setting up directories, targets, and database records.
"""

import os
from pathlib import Path

import pandas as pd
import joblib
from datetime import datetime

# Set up coverage file path
os.environ["COVERAGE_FILE"] = str(Path(".coverage").resolve())

# Internal imports
from lecrapaud.directories import tmp_dir
from lecrapaud.models import Experiment, Target
from lecrapaud.db.session import get_db
from lecrapaud.services import ArtifactService


def create_experiment(
    data: pd.DataFrame,
    experiment_name: str,
    date_column: str | None = None,
    group_column: str | None = None,
    **kwargs: dict,
) -> "Experiment":
    """Create a new LeCrapaud experiment from data.

    Sets up the experiment directory structure, registers targets in the
    database, and creates the experiment record with associated metadata.

    Args:
        data: Input data as a DataFrame.
        experiment_name: Name for the experiment. A timestamp suffix is
                        added automatically for new experiments.
        date_column: Column name containing dates for time series experiments.
        group_column: Column name for grouping data.
        **kwargs: Additional context parameters. Must include:
            - target_numbers: List of target column indices.
            - target_clf: List of target numbers that are classification tasks.
            - time_series: Whether this is a time series experiment.

    Returns:
        Experiment: The created experiment database record.

    Raises:
        ValueError: If target_numbers or target_clf are not provided,
                   if date_column is missing for time series experiments,
                   or if experiment_name is not provided.

    Example:
        >>> experiment = create_experiment(
        ...     data=df,
        ...     experiment_name="my_experiment",
        ...     target_numbers=[0, 1],
        ...     target_clf=[0],
        ... )
    """
    if "target_numbers" not in kwargs or "target_clf" not in kwargs:
        raise ValueError(
            "You should specify context in kwargs to create experiment. target_clf and target_numbers must be present"
        )

    if isinstance(data, str):
        raise ValueError("Loading experiments from file path is no longer supported. Pass a DataFrame directly.")

    experiment_name = f"{experiment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    if kwargs.get("time_series") and not date_column:
        raise ValueError("date_column must be provided for time series experiments")

    if experiment_name is None:
        raise ValueError("experiment_name must be provided")

    dates = {}
    if date_column:
        dates["start_date"] = pd.to_datetime(data[date_column].iat[0])
        dates["end_date"] = pd.to_datetime(data[date_column].iat[-1])

    groups = {}
    if group_column:
        groups["number_of_groups"] = data[group_column].nunique()
        groups["list_of_groups"] = sorted(data[group_column].unique().tolist())

    with get_db() as db:
        all_targets = Target.get_all(db=db)
        targets = [
            target
            for target in all_targets
            if int(target.name.split("_")[-1]) in kwargs["target_numbers"]
        ]
        number_of_targets = len(targets)

        experiment_dir = f"{tmp_dir}/{experiment_name}"
        os.makedirs(experiment_dir, exist_ok=True)

        # Create or update experiment (without targets relation)
        experiment = Experiment.upsert(
            db=db,
            name=experiment_name,
            path=Path(experiment_dir).resolve(),
            size=data.shape[0],
            number_of_targets=number_of_targets,
            **groups,
            **dates,
            context={
                "date_column": date_column,
                "group_column": group_column,
                "experiment_name": experiment_name,
                **kwargs,
            },
        )

        # Set targets relationship after creation/update
        experiment.targets = targets
        experiment.save(db=db)

        return experiment
