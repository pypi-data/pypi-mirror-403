"""Utility functions and logging setup for LeCrapaud.

This module provides various utility functions used throughout the LeCrapaud
framework, including logging configuration, file operations, text processing,
metrics handling, and JSON serialization helpers.

The module also defines the METRICS_CONFIG dictionary for optimization metrics
and EVAL_METRIC_MAPPING for library-specific metric translations.
"""

import pandas as pd
import numpy as np
import logging
from logging.handlers import RotatingFileHandler
import shutil
import os
import subprocess
from datetime import datetime, date
from ftfy import fix_text
import unicodedata
import re
import string

from lecrapaud.directories import logger_dir
from lecrapaud.config import LOGGING_LEVEL, PYTHON_ENV


_LECRAPAUD_LOGGER_ALREADY_CONFIGURED = False


def setup_logger():
    """Configure and return the LeCrapaud logger.

    Sets up logging with both console and file handlers based on the
    current environment (Development, Production, Test, Worker).
    Also initializes Sentry integration if configured.

    The logger is configured only once; subsequent calls return the
    existing logger instance.

    Returns:
        logging.Logger: Configured logger instance for LeCrapaud.
    """
    name = "lecrapaud"

    global _LECRAPAUD_LOGGER_ALREADY_CONFIGURED
    if _LECRAPAUD_LOGGER_ALREADY_CONFIGURED:  # ← bail out if done before
        return logging.getLogger(name)

    print(
        f"Setting up logger for {name} with PYTHON_ENV {PYTHON_ENV} and LOGGING_LEVEL {LOGGING_LEVEL}"
    )
    # ------------------------------------------------------------------ #
    #  Real configuration happens only on the FIRST call                 #
    # ------------------------------------------------------------------ #
    fmt = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(format=fmt, datefmt=datefmt)  # root format
    formatter = logging.Formatter(fmt, datefmt=datefmt)

    logger = logging.getLogger(name)

    log_level = getattr(logging, LOGGING_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    # pick a file according to environment
    env_file = {
        "Development": "dev.log",
        "Production": "prod.log",
        "Test": "test.log",
        "Worker": "worker.log",
    }.get(PYTHON_ENV, "app.log")

    if logger_dir:
        file_handler = RotatingFileHandler(
            f"{logger_dir}/{env_file}",
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)

    try:
        from lecrapaud.integrations.sentry_integration import init_sentry

        if init_sentry():
            logger.info("Sentry logging enabled")
    except Exception as exc:
        logger.info(f"Sentry logging disabled: {exc}")

    _LECRAPAUD_LOGGER_ALREADY_CONFIGURED = True
    return logger


logger = setup_logger()


def get_df_name(obj, namespace):
    """Get the variable name of an object in a given namespace.

    Args:
        obj: The object to find the name of.
        namespace: Dictionary of name-to-object mappings (e.g., locals()).

    Returns:
        str: The variable name that references the object.
    """
    return [name for name in namespace if namespace[name] is obj][0]


def pprint(item):
    """Pretty print an item to the logger with all rows visible.

    Args:
        item: Item to print (typically a pandas DataFrame).
    """
    with pd.option_context("display.max_rows", None):
        logger.info(item)


def object_to_dict(obj):
    """Recursively convert an object and its attributes to a dictionary.

    Args:
        obj: Object to convert. Can be a dict, list, or object with __dict__.

    Returns:
        dict or list: Dictionary representation of the object.
    """
    if isinstance(obj, dict):
        return {k: object_to_dict(v) for k, v in obj.items()}
    elif hasattr(obj, "__dict__"):
        return {k: object_to_dict(v) for k, v in obj.__dict__.items()}
    elif isinstance(obj, list):
        return [object_to_dict(i) for i in obj]
    else:
        return obj


def copy_any(src, dst):
    """Copy a file or directory to a destination.

    Uses shutil.copytree for directories and shutil.copy2 for files.
    copy2 preserves file metadata.

    Args:
        src: Source path (file or directory).
        dst: Destination path.
    """
    if os.path.isdir(src):
        # Copy folder using copytree
        shutil.copytree(src, dst)
    else:
        # Copy file using copy2 (which preserves metadata)
        shutil.copy2(src, dst)


def contains_best(folder_path):
    """Check if a folder contains saved model files.

    Searches recursively for files with '.best' or '.keras' in their names,
    which indicate saved LeCrapaud models.

    Args:
        folder_path: Path to the directory to search.

    Returns:
        bool: True if model files are found, False otherwise.
    """
    # Iterate over all files and folders in the specified directory
    for root, dirs, files in os.walk(folder_path):
        # Check each file and folder name for '.best' or '.keras'
        for name in files + dirs:
            if ".best" in name or ".keras" in name:
                return True
    return False


def get_folder_sizes(directory=os.path.expanduser("~")):
    """Calculate and display folder sizes in a directory.

    Uses the 'du' command to calculate sizes and logs results
    sorted by size in descending order.

    Args:
        directory: Directory to analyze. Defaults to user's home directory.
    """
    folder_sizes = {}

    for folder in os.listdir(directory):
        folder_path = os.path.join(directory, folder)
        if os.path.isdir(folder_path):
            try:
                size = (
                    subprocess.check_output(["du", "-sk", folder_path])
                    .split()[0]
                    .decode("utf-8")
                )
                folder_sizes[folder] = int(size)
            except subprocess.CalledProcessError:
                logger.info(f"Skipping {folder_path}: Permission Denied")

    sorted_folders = sorted(folder_sizes.items(), key=lambda x: x[1], reverse=True)
    logger.info(f"{'Folder':<50}{'Size (MB)':>10}")
    logger.info("=" * 60)
    for folder, size in sorted_folders:
        logger.info(f"{folder:<50}{size / (1024*1024):>10.2f}")


def create_cron_job(
    script_path,
    venv_path,
    log_file,
    pythonpath,
    cwd,
    job_frequency="* * * * *",
    cron_name="My Custom Cron Job",
):
    """
    Creates a cron job to run a Python script with a virtual environment, logging output, and setting PYTHONPATH and CWD.

    Parameters:
    - script_path (str): Path to the Python script to run.
    - venv_path (str): Path to the virtual environment's Python interpreter.
    - log_file (str): Path to the log file for output.
    - pythonpath (str): Value for the PYTHONPATH environment variable.
    - cwd (str): Working directory from which the script should run.
    - job_frequency (str): Cron timing syntax (default is every minute).
    - cron_name (str): Name to identify the cron job.
    """
    # Construct the cron command
    cron_command = (
        f"{job_frequency} /bin/zsh -c 'pgrep -fl python | grep -q {os.path.basename(script_path)} "
        f'|| (echo -e "Cron job {cron_name} started at $(date)" >> {log_file} && cd {cwd} && '
        f"PYTHONPATH={pythonpath} {venv_path}/bin/python {script_path} >> {log_file} 2>&1)'"
    )

    # Check existing cron jobs and remove any with the same comment
    subprocess.run(f"(crontab -l | grep -v '{cron_name}') | crontab -", shell=True)

    # Add the new cron job with the comment
    full_cron_job = f"{cron_command} # {cron_name}\n"
    subprocess.run(f'(crontab -l; echo "{full_cron_job}") | crontab -', shell=True)
    logger.info(f"Cron job created: {full_cron_job}")


def remove_all_cron_jobs():
    """
    Removes all cron jobs for the current user.
    """
    try:
        # Clear the user's crontab
        subprocess.run("crontab -r", shell=True, check=True)
        logger.info("All cron jobs have been removed successfully.")
    except subprocess.CalledProcessError:
        logger.info(
            "Failed to remove cron jobs. There may not be any cron jobs to remove, or there could be a permissions issue."
        )


def serialize_timestamp(dict: dict):
    """Convert timestamp objects to ISO format strings in a list of dicts.

    Args:
        dict: List of dictionaries that may contain datetime objects.

    Returns:
        list: List of dictionaries with timestamps converted to ISO strings.
    """
    def convert(obj):
        if isinstance(obj, (datetime, date, pd.Timestamp)):
            return obj.isoformat()

        return obj

    return [{k: convert(v) for k, v in item.items()} for item in dict]


def remove_accents(text: str) -> str:
    """
    Cleans the text of:
    - Broken Unicode
    - Accents
    - Control characters (including \x00, \u0000, etc.)
    - Escape sequences
    - Non-printable characters
    - Excessive punctuation (like ........ or !!!!)
    """

    # Step 1: Fix mojibake and broken Unicode
    text = fix_text(text)

    # Step 2 bis: Normalize accents
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ASCII", "ignore").decode("utf8")

    # Step 3: Remove known weird tokens
    text = text.replace("<|endoftext|>", "")
    text = text.replace("\u0000", "").replace("\x00", "")

    # Step 4: Remove raw control characters (e.g., \x1f)
    text = "".join(c for c in text if unicodedata.category(c)[0] != "C" or c == "\n")

    # Step 5: Remove literal escape sequences like \xNN
    text = re.sub(r"\\x[0-9a-fA-F]{2}", "", text)

    # Step 6: Remove non-printable characters
    printable = set(string.printable)
    text = "".join(c for c in text if c in printable)

    # Step 7: Collapse repeated punctuation (e.g., ........ → .)
    text = re.sub(r"([!?.])\1{2,}", r"\1", text)  # !!!!!! → !
    text = re.sub(r"([-—])\1{1,}", r"\1", text)  # ------ → -
    text = re.sub(r"([,.]){4,}", r"\1", text)  # ...... → .

    return text.strip()


def serialize_for_json(obj):
    """
    Recursively convert any object into a JSON-serializable structure.
    Handles NumPy types, datetime objects, and class instances.
    """
    import numpy as np
    from datetime import datetime, date
    import pandas as pd

    # Handle NumPy types
    if isinstance(obj, (np.integer, np.int64, np.int32, np.int16)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)

    # Handle datetime types
    elif isinstance(obj, (datetime, date, pd.Timestamp)):
        return obj.isoformat()

    # Handle basic Python types
    elif isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    elif isinstance(obj, dict):
        return {str(k): serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return [serialize_for_json(v) for v in obj]
    elif isinstance(obj, type):
        # A class/type object like int, str, etc.
        return obj.__name__
    elif hasattr(obj, "__class__"):
        # For other objects, return their string representation
        return f"{obj.__class__.__name__}()"
    else:
        return str(obj)


def strip_timestamp_suffix(name: str) -> str:
    """Remove timestamp suffix from an experiment name.

    Removes suffixes matching the pattern '_YYYYMMDD_HHMMSS' from the end
    of experiment names.

    Args:
        name: Experiment name potentially containing a timestamp suffix.

    Returns:
        str: Name with timestamp suffix removed.

    Example:
        >>> strip_timestamp_suffix("my_experiment_20240115_143022")
        'my_experiment'
    """
    # Matches an underscore followed by 8 digits, another underscore, then 6 digits at the end
    return re.sub(r"_\d{8}_\d{6}$", "", name)


def get_run_dir(
    base_dir: str,
    experiment_name: str,
    target_name: str,
    model_name: str,
    run_id: str = None,
) -> tuple[str, str]:
    """Generate a run directory path following the new folder structure.

    Creates a directory structure for storing run artifacts:
    {base_dir}/{base_experiment_name}/{target_name}/{model_name}/{run_id}/

    The base_experiment_name is derived by stripping the timestamp suffix
    from the full experiment name, so runs from different experiment sessions
    with the same base name are grouped together.

    Args:
        base_dir: Base directory (typically 'tmp').
        experiment_name: Full experiment name (may include timestamp suffix).
        target_name: Target identifier (e.g., 'TARGET_1').
        model_name: Model type identifier (e.g., 'lgb', 'xgb', 'catboost').
        run_id: Optional run identifier. If not provided, generates a
                timestamp in YYYYMMDD_HHMMSS format.

    Returns:
        tuple[str, str]: A tuple of (run_directory_path, run_id).
            The directory is created if it doesn't exist.

    Example:
        >>> run_dir, run_id = get_run_dir("tmp", "stock_pred_20260128_175156", "TARGET_1", "lgb")
        >>> # Returns: ("tmp/stock_pred/TARGET_1/lgb/20260128_180000", "20260128_180000")
    """
    from pathlib import Path

    base_name = strip_timestamp_suffix(experiment_name)

    if run_id is None:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    run_dir = Path(base_dir) / base_name / target_name / model_name / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    return str(run_dir), run_id


def validate_no_nan_inf(df: pd.DataFrame, stage: str) -> None:
    """
    Validate that a DataFrame contains no NaN or Inf values.
    Raises a comprehensive ValueError if issues are found.

    Args:
        df: DataFrame to validate
        stage: Name of the processing stage (e.g., "feature engineering", "model preprocessing")
    """
    # Check for NaN values
    nan_mask = df.isnull()
    nan_counts = nan_mask.sum()
    cols_with_nan = nan_counts[nan_counts > 0].sort_values(ascending=False)

    # Check for Inf values (only in numeric columns)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    inf_counts = {}
    for col in numeric_cols:
        try:
            values = df[col].to_numpy(dtype=float, na_value=np.nan)
            inf_count = np.isinf(values).sum()
            if inf_count > 0:
                inf_counts[col] = inf_count
        except (TypeError, ValueError):
            continue
    cols_with_inf = pd.Series(inf_counts).sort_values(ascending=False) if inf_counts else pd.Series(dtype=int)
    inf_mask = pd.DataFrame()
    if len(cols_with_inf) > 0:
        inf_mask = df[cols_with_inf.index].apply(
            lambda x: np.isinf(x.to_numpy(dtype=float, na_value=np.nan))
        )

    if len(cols_with_nan) == 0 and len(cols_with_inf) == 0:
        return  # All good

    # Build comprehensive error message
    error_parts = [
        f"Data validation failed after {stage}.",
        f"Total rows: {len(df):,}",
    ]

    if len(cols_with_nan) > 0:
        total_nan = nan_counts.sum()
        rows_with_nan = nan_mask.any(axis=1).sum()
        error_parts.append("")
        error_parts.append("=== NaN VALUES DETECTED ===")
        error_parts.append(f"Total NaN values: {total_nan:,}")
        error_parts.append(f"Rows affected: {rows_with_nan:,} ({100*rows_with_nan/len(df):.1f}%)")
        error_parts.append(f"Columns with NaN ({len(cols_with_nan)}):")
        for col, count in cols_with_nan.head(20).items():
            pct = 100 * count / len(df)
            error_parts.append(f"  - {col}: {count:,} ({pct:.1f}%)")
        if len(cols_with_nan) > 20:
            error_parts.append(f"  ... and {len(cols_with_nan) - 20} more columns")

        # Show sample rows with NaN
        sample_nan_rows = df[nan_mask.any(axis=1)].head(3)
        if not sample_nan_rows.empty:
            nan_cols_in_sample = [col for col in cols_with_nan.index[:10] if col in sample_nan_rows.columns]
            if nan_cols_in_sample:
                error_parts.append("")
                error_parts.append("Sample rows with NaN (first 3, showing affected columns):")
                error_parts.append(sample_nan_rows[nan_cols_in_sample].to_string())

    if len(cols_with_inf) > 0:
        total_inf = cols_with_inf.sum()
        rows_with_inf = inf_mask.any(axis=1).sum() if not inf_mask.empty else 0
        error_parts.append("")
        error_parts.append("=== INFINITE VALUES DETECTED ===")
        error_parts.append(f"Total Inf values: {total_inf:,}")
        error_parts.append(f"Rows affected: {rows_with_inf:,} ({100*rows_with_inf/len(df):.1f}%)")
        error_parts.append(f"Columns with Inf ({len(cols_with_inf)}):")
        for col, count in cols_with_inf.head(20).items():
            pct = 100 * count / len(df)
            error_parts.append(f"  - {col}: {count:,} ({pct:.1f}%)")
        if len(cols_with_inf) > 20:
            error_parts.append(f"  ... and {len(cols_with_inf) - 20} more columns")

    error_parts.append("")
    error_parts.append("=== SUGGESTED ACTIONS ===")
    error_parts.append("1. Check your input data for missing values before calling fit()")
    error_parts.append("2. Ensure date columns are properly formatted")
    error_parts.append("3. Check encoding/scaling columns exist and have valid values")

    raise ValueError("\n".join(error_parts))


# Metrics configuration for optimization
# direction: "minimize" or "maximize"
# valid_for: "classification", "regression", or "both"
METRICS_CONFIG = {
    # Classification metrics
    "LOGLOSS": {"direction": "minimize", "valid_for": "classification"},
    "ROC_AUC": {"direction": "maximize", "valid_for": "classification"},
    "AVG_PRECISION": {"direction": "maximize", "valid_for": "classification"},
    "ACCURACY": {"direction": "maximize", "valid_for": "classification"},
    "PRECISION": {"direction": "maximize", "valid_for": "classification"},
    "RECALL": {"direction": "maximize", "valid_for": "classification"},
    "F1": {"direction": "maximize", "valid_for": "classification"},
    # Regression metrics
    "RMSE": {"direction": "minimize", "valid_for": "regression"},
    "MAE": {"direction": "minimize", "valid_for": "regression"},
    "MAPE": {"direction": "minimize", "valid_for": "regression"},
    "R2": {"direction": "maximize", "valid_for": "regression"},
}


def get_default_metric(target_type: str) -> str:
    """Get the default optimization metric for a target type."""
    return "RMSE" if target_type == "regression" else "LOGLOSS"


def get_metric_direction(metric: str) -> str:
    """Get the optimization direction for a metric ('minimize' or 'maximize')."""
    if metric not in METRICS_CONFIG:
        raise ValueError(
            f"Unknown metric: {metric}. Valid metrics: {list(METRICS_CONFIG.keys())}"
        )
    return METRICS_CONFIG[metric]["direction"]


def is_metric_better(new_score: float, best_score: float, metric: str) -> bool:
    """Check if new_score is better than best_score for the given metric."""
    direction = get_metric_direction(metric)
    if direction == "minimize":
        return new_score < best_score
    else:
        return new_score > best_score


def get_initial_best_score(metric: str) -> float:
    """Get the initial 'worst' score for a metric (to be improved upon)."""
    import numpy as np

    direction = get_metric_direction(metric)
    return np.inf if direction == "minimize" else -np.inf


def validate_metric_for_target_type(metric: str, target_type: str) -> None:
    """Validate that a metric is appropriate for the given target type."""
    if metric not in METRICS_CONFIG:
        raise ValueError(
            f"Unknown metric: {metric}. Valid metrics: {list(METRICS_CONFIG.keys())}"
        )
    valid_for = METRICS_CONFIG[metric]["valid_for"]
    if valid_for != "both" and valid_for != target_type:
        raise ValueError(
            f"Metric '{metric}' is only valid for {valid_for}, not {target_type}. "
            f"Valid {target_type} metrics: {[k for k, v in METRICS_CONFIG.items() if v['valid_for'] in (target_type, 'both')]}"
        )


# Mapping from our metric names to library-specific eval_metric names
# Format: {metric: {library: {binary: name, multiclass: name} or name}}
EVAL_METRIC_MAPPING = {
    # XGBoost mappings
    "xgboost": {
        "LOGLOSS": {"binary": "logloss", "multiclass": "mlogloss"},
        "ROC_AUC": {"binary": "auc", "multiclass": "auc"},
        "AVG_PRECISION": {"binary": "aucpr", "multiclass": "aucpr"},
        "RMSE": "rmse",
        "MAE": "mae",
        "MAPE": "mape",
    },
    # LightGBM mappings
    "lightgbm": {
        "LOGLOSS": {"binary": "binary_logloss", "multiclass": "multi_logloss"},
        "ROC_AUC": {"binary": "auc", "multiclass": "auc_mu"},
        "AVG_PRECISION": {"binary": "average_precision", "multiclass": "average_precision"},
        "RMSE": "rmse",
        "MAE": "mae",
        "MAPE": "mape",
    },
    # CatBoost mappings
    "catboost": {
        "LOGLOSS": {"binary": "Logloss", "multiclass": "MultiClass"},
        "ROC_AUC": {"binary": "AUC", "multiclass": "AUC"},
        "AVG_PRECISION": {"binary": "PRAUC", "multiclass": "PRAUC"},
        "ACCURACY": {"binary": "Accuracy", "multiclass": "Accuracy"},
        "RMSE": "RMSE",
        "MAE": "MAE",
        "MAPE": "MAPE",
        "R2": "R2",
    },
}


def get_feature_search_range(n_samples: int, n_available_features: int, max_features: int = None) -> tuple[int, int]:
    """
    Calculate the [min, max] range of features to explore based on number of observations.

    Uses curse of dimensionality principles:
    - min_features: log₂(n) with floor at 10
    - max_features: min(√n, n/10) - the more conservative of the two

    Args:
        n_samples: Number of observations
        n_available_features: Number of features available after ranking
        max_features: Optional user-specified maximum (overrides computed max)

    Returns:
        (min_features, max_features): Tuple of min and max features to search
    """
    import numpy as np

    # Minimum: log₂(n) with floor at 10
    min_features = max(10, int(np.log2(max(n_samples, 1))))

    # Maximum: min(√n, n/10) - the more conservative of the two
    max_by_sqrt = int(np.sqrt(n_samples))
    max_by_ratio = n_samples // 10
    computed_max = min(max_by_sqrt, max_by_ratio)

    # Use user-specified max_features if provided, otherwise use computed
    if max_features is not None:
        final_max = min(max_features, n_available_features)
    else:
        final_max = min(computed_max, n_available_features)

    # Ensure max >= min
    final_max = max(final_max, min_features)

    # Cap at available features
    final_max = min(final_max, n_available_features)
    min_features = min(min_features, final_max)

    return min_features, final_max


def get_eval_metric(metric: str, library: str, is_binary: bool = True) -> str:
    """
    Get the library-specific eval_metric name for a given metric.

    Args:
        metric: Our metric name (e.g., "LOGLOSS", "ROC_AUC")
        library: The library name ("xgboost", "lightgbm", "catboost")
        is_binary: Whether it's binary classification (vs multiclass)

    Returns:
        The library-specific eval_metric name
    """
    library = library.lower()
    if library not in EVAL_METRIC_MAPPING:
        raise ValueError(f"Unknown library: {library}")

    lib_mapping = EVAL_METRIC_MAPPING[library]
    if metric not in lib_mapping:
        # Fallback to default for this library
        logger.warning(
            f"Metric '{metric}' not available as eval_metric for {library}. "
            f"Using library default."
        )
        return None

    mapping = lib_mapping[metric]
    if isinstance(mapping, dict):
        return mapping["binary"] if is_binary else mapping["multiclass"]
    return mapping
