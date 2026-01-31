<div align="center">

<img src="https://s3.amazonaws.com/pix.iemoji.com/images/emoji/apple/ios-12/256/frog-face.png" width=120 alt="crapaud"/>

## Welcome to LeCrapaud

**An all-in-one machine learning framework**

[![PyPI version](https://badge.fury.io/py/lecrapaud.svg)](https://badge.fury.io/py/lecrapaud)
[![Python versions](https://img.shields.io/pypi/pyversions/lecrapaud.svg)](https://pypi.org/project/lecrapaud)

</div>

## Introduction

LeCrapaud is a high-level Python library for end-to-end machine learning workflows on tabular or time series data. It provides a simple API to handle feature engineering, model selection, training, and prediction, all in a reproducible and modular way.

## Key Features

- End-to-end machine learning training in one command, with feature engineering, feature selection, preprocessing, model selection, and prediction
- Modular pipeline: Feature engineering, preprocessing, selection, and modeling can also be run as independent steps
- Automated model selection and hyperparameter optimization
- Easy integration with pandas DataFrames
- Supports both regression and classification tasks
- Simple API for both full pipeline and step-by-step usage
- Ready for production and research workflows

## Installation

```sh
pip install lecrapaud
```

## Quick Start

```python
from lecrapaud import LeCrapaud

# Optional: Set database URI (otherwise uses DB_URI env var)
LeCrapaud.set_uri("mysql+pymysql://user:password@host:port/dbname")

# Create experiment instance with configuration
lc = LeCrapaud(
    experiment_name="my_experiment",
    target_numbers=[1],
    target_clf=[1],
    models_idx=["lgb", "xgb"],
)

# Fit on training data
lc.fit(data)

# Make predictions
predictions, scores_reg, scores_clf = lc.predict(new_data)
```

## API Reference

### Creating Experiments

```python
from lecrapaud import LeCrapaud

# Create a new experiment (training happens when fit() is called)
lc = LeCrapaud(
    experiment_name="my_experiment",
    target_numbers=[1, 2],
    target_clf=[2],  # TARGET_2 is classification
    columns_drop=[...],
    columns_date=[...],
    # ... other config options
)
```

### Training Models

```python
# Train with automatic hyperparameter optimization
lc.fit(your_dataframe)

# Train with custom hyperparameters (skip hyperopt)
lc.fit(your_dataframe, best_params={
    1: {"xgb": {...}, "lgb": {...}},
    2: {"xgb": {...}, "lgb": {...}},
})
```

### Making Predictions

```python
# Make predictions on new data
predictions, reg_scores, clf_scores = lc.predict(new_data)
```

**Output format:**
- `predictions` DataFrame with:
  - Regression targets: `TARGET_{i}_PRED` column
  - Classification targets: `TARGET_{i}_PRED` (predicted class) and probability columns per class: `TARGET_{i}_{class_value}` (e.g., `TARGET_2_0`, `TARGET_2_1` for binary)
- `reg_scores` and `clf_scores` DataFrames (only if `new_data` includes `TARGET_i` columns)

### Loading Existing Experiments

```python
# Load experiment by ID
lc = LeCrapaud.get(id=123)

# Get best experiment by name (highest score)
lc = LeCrapaud.get_best_experiment_by_name("my_experiment")

# Get last experiment by name
lc = LeCrapaud.get_last_experiment_by_name("my_experiment")
```

### Class Methods for Experiment Management

```python
# List all experiments (optionally filter by name)
experiments = LeCrapaud.list_experiments(name="my_experiment")
experiments = LeCrapaud.list_experiments()  # all experiments

# Compare scores of experiments with same name
scores_df = LeCrapaud.compare_experiment_scores("my_experiment")
# Returns DataFrame with columns: experiment, target, rmse, mae, mape, r2,
#                                 logloss, accuracy, roc_auc, avg_precision, f1
```

## Complete Parameter Reference

### Experiment Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `experiment_name` | str | `"experiment"` | Name prefix for the experiment |
| `date_column` | str | `None` | Name of the date column (required for time series) |
| `group_column` | str | `None` | Name of the group column (required for panel data) |

### Feature Engineering Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `columns_drop` | list | `[]` | Columns to drop during feature engineering |
| `columns_boolean` | list | `[]` | Columns to convert to boolean features |
| `columns_date` | list | `[]` | Date columns for cyclical encoding |
| `columns_te_groupby` | list | `[]` | Groupby columns for target encoding |
| `columns_te_target` | list | `[]` | Target columns for target encoding |
| `fourier_order` | int | `1` | Fourier order for cyclical features |

### Preprocessing Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `time_series` | bool | `False` | Enable time series mode |
| `val_size` | float | `0.2` | Validation set fraction |
| `test_size` | float | `0.2` | Test set fraction |
| `columns_pca` | list | `[]` | Columns for PCA/embedding transformation |
| `pca_temporal` | list | `[]` | Temporal PCA config (e.g., lag features) |
| `pca_cross_sectional` | list | `[]` | Cross-sectional PCA config (e.g., market regime) |
| `columns_onehot` | list | `[]` | Columns for one-hot encoding |
| `columns_binary` | list | `[]` | Columns for binary encoding |
| `columns_ordinal` | list | `[]` | Columns for ordinal encoding |
| `columns_frequency` | list | `[]` | Columns for frequency encoding |

### Feature Selection Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `percentile` | float | `20` | Percentage of features to keep per selection method |
| `corr_threshold` | float | `80` | Maximum correlation threshold (%) between features |
| `max_features` | int | `None` | Max features to keep. `None` = auto-computed: min(sqrt(n), n/10) based on n_samples |
| `max_p_value` | float | `0.05` | Universal p-value threshold for statistical tests |
| `max_p_value_categorical` | float | `0.05` | Maximum p-value for categorical feature selection (Chi2) |
| `min_correlation` | float | `0.1` | Minimum correlation magnitude for Spearman/Kendall |
| `cumulative_importance` | float | `0.80` | Cumulative threshold for MI and FI (80%) |
| `auto_select_feature_count` | bool | `True` | Automatically find optimal number of features using validation score |

### Model Selection Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `target_numbers` | list | `[]` | List of target indices to predict (e.g., `[1, 2]` for TARGET_1, TARGET_2) |
| `target_clf` | list | `[]` | Classification target indices |
| `models_idx` | list | `[]` | Model names/indices to train (e.g., `["xgb", "lgb", "catboost"]`) |
| `max_timesteps` | int | `120` | Maximum timesteps for recurrent models |
| `perform_hyperopt` | bool | `True` | Enable hyperparameter optimization |
| `number_of_trials` | int | `20` | Number of hyperopt trials |
| `perform_crossval` | bool | `False` | Enable cross-validation during hyperopt |
| `plot` | bool | `True` | Show plots during training |
| `preserve_model` | bool | `True` | Save the best model to database |
| `target_clf_thresholds` | dict | `{}` | Classification thresholds per target |
| `use_class_weights` | bool | `True` | Use class weights for imbalanced classification |
| `optimization_metric` | dict/str | `{}` | Per-target metrics: `{1: "ROC_AUC", 2: "RMSE"}`, empty = auto |

## Supported Models

### Classical/Ensemble Models

| Model Name | Description |
|------------|-------------|
| `linear` | Linear/Logistic Regression |
| `sgd` | Stochastic Gradient Descent |
| `naive_bayes` | Naive Bayes Classifier |
| `bagging_naive_bayes` | Bagging Naive Bayes |
| `svm` | Support Vector Machine |
| `tree` | Decision Tree |
| `forest` | Random Forest |
| `adaboost` | AdaBoost |
| `xgb` | XGBoost |
| `lgb` | LightGBM |
| `catboost` | CatBoost |

### Recurrent/Deep Learning Models

| Model Name | Description |
|------------|-------------|
| `LSTM-1` | Single-layer LSTM head on tabular sequences |
| `LSTM-2` | Two stacked LSTM layers |
| `LSTM-2-Deep` | Deeper head on top of stacked LSTMs |
| `BiLSTM-1` | Bidirectional single-layer LSTM |
| `BiLSTM-2` | Bidirectional two-layer LSTM |
| `GRU-1` | Single-layer GRU |
| `GRU-2` | Two stacked GRU layers |
| `GRU-2-Deep` | Deeper head on top of stacked GRUs |
| `BiGRU-1` | Bidirectional single-layer GRU |
| `BiGRU-2` | Bidirectional two-layer GRU |
| `TCN-1` | Temporal Convolutional Network baseline |
| `TCN-2` | Two-layer TCN |
| `TCN-2-Deep` | Deeper TCN |
| `BiTCN-1` | Bidirectional TCN |
| `BiTCN-2` | Bidirectional two-layer TCN |
| `Seq2Seq` | Encoder-decoder with attention for sequences |
| `Transformer` | Transformer encoder stack for tabular sequences |

## Feature Selection Methods

LeCrapaud uses an ensemble approach to feature selection, combining multiple methods:

| Method | Type | Use Case |
|--------|------|----------|
| Chi2 | Statistical | Categorical features, classification |
| ANOVA | Statistical | Numerical features, classification |
| Pearson | Correlation | Linear relationships, regression |
| Spearman | Correlation | Monotonic relationships |
| Kendall | Correlation | Ordinal data |
| Mutual Information | Information | Non-linear relationships |
| Feature Importance | Model-based | Tree ensemble importance |
| RFE | Wrapper | Recursive feature elimination |
| SFS | Wrapper | Sequential forward selection |
| PCA | Dimensionality | Variance-based reduction |
| Ensemble | Combined | Aggregated ranking from all methods |

## Optimization Metrics

The `optimization_metric` parameter controls which metric is optimized during feature selection (auto feature count) and model selection (hyperopt).

### Classification Metrics

| Metric | Direction | Description |
|--------|-----------|-------------|
| `LOGLOSS` | minimize | Log loss (default for classification) |
| `ROC_AUC` | maximize | Area under ROC curve |
| `AVG_PRECISION` | maximize | Average precision (PR-AUC) |
| `ACCURACY` | maximize | Classification accuracy |
| `PRECISION` | maximize | Precision score |
| `RECALL` | maximize | Recall score |
| `F1` | maximize | F1 score |

### Regression Metrics

| Metric | Direction | Description |
|--------|-----------|-------------|
| `RMSE` | minimize | Root mean squared error (default) |
| `MAE` | minimize | Mean absolute error |
| `MAPE` | minimize | Mean absolute percentage error |
| `R2` | maximize | R-squared coefficient of determination |

```python
# Example: Optimize for ROC AUC instead of default LOGLOSS
lc = LeCrapaud(
    target_numbers=[1],
    target_clf=[1],
    optimization_metric="ROC_AUC",
    ...
)
```

## Database Configuration (Required)

LeCrapaud requires access to a MySQL database to store experiments and results.

### Option 1: Class Method (Recommended)

```python
LeCrapaud.set_uri("mysql+pymysql://user:password@host:port/dbname")
```

### Option 2: Environment Variables

```sh
# Individual variables
export DB_USER=lecrapaud
export DB_PASSWORD=lecrapaud
export DB_HOST=127.0.0.1
export DB_PORT=3306
export DB_NAME=lecrapaud

# Or full URI
export DB_URI="mysql+pymysql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
```

### Quick MySQL Setup (Local, macOS)

**Docker (fastest):**
```sh
docker run --name lecrapaud-mysql -e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=lecrapaud -p 3306:3306 -d mysql:8
```

**Homebrew MySQL:**
```sh
brew install mysql
brew services start mysql
mysql -uroot
CREATE DATABASE lecrapaud;
CREATE USER 'lecrapaud'@'localhost' IDENTIFIED BY 'lecrapaud';
GRANT ALL PRIVILEGES ON lecrapaud.* TO 'lecrapaud'@'localhost';
FLUSH PRIVILEGES;
```

### Database Storage Architecture

LeCrapaud uses a **database-only storage** approach. All artifacts and data are stored directly in the database:

| Category | Description | Storage |
|----------|-------------|---------|
| **Scalers** | `scaler_x`, `scaler_y_{target}` | Binary (joblib) |
| **Transformers** | Column transformers for encoding | Binary (joblib) |
| **PCAs** | `pcas`, `pcas_cross_sectional`, `pcas_temporal` | Binary (joblib) |
| **Models** | Trained ML models | Binary (joblib/h5) |
| **Features** | Selected features, all features lists | Binary (joblib) |
| **Thresholds** | Classification thresholds | Binary (joblib) |
| **DataFrames** | Train, validation, test splits | Binary (parquet) |
| **Predictions** | Model predictions | Binary (parquet) |

## Embeddings Configuration (Optional)

If you want to use the `columns_pca` embedding feature for text columns:

### OpenAI Embeddings (Default)

```sh
export OPENAI_API_KEY=sk-...
```

### Ollama Embeddings (Local, Free)

```sh
# Install Ollama: https://ollama.ai
ollama pull nomic-embed-text

# Configure LeCrapaud
export EMBEDDING_PROVIDER=ollama
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

## Explainability Features

LeCrapaud provides comprehensive model explainability tools.

### Feature Importance

```python
lc.plot_feature_importance(target_number=1)
```

### LIME Explanations

```python
lc.plot_lime_explanation(
    target_number=1,
    instance_idx=0,
    num_features=10
)
```

### SHAP Values

```python
# Summary plot
lc.plot_shap_values(
    target_number=1,
    plot_type="dot",  # "bar", "dot", "violin", "beeswarm"
    max_display=20
)

# Waterfall plot for individual predictions
lc.plot_shap_waterfall(
    target_number=1,
    instance_idx=0
)
```

### Tree Visualization

```python
lc.plot_tree(
    target_number=1,
    tree_index=0,
    max_depth=3
)
```

### PCA Visualization

```python
# 2D scatter plot
lc.plot_pca_scatter(
    target_number=1,
    pca_type="all",  # "embedding", "cross_sectional", "temporal", "all"
    components=(0, 1)
)

# Variance explained
lc.plot_pca_variance(pca_type="all")
```

## Modular Usage (sklearn Compatibility)

You can use individual pipeline components:

```python
from lecrapaud import FeatureEngineer, FeaturePreprocessor, FeatureSelector

# Create components with experiment context
feature_eng = FeatureEngineer(experiment=experiment)
feature_prep = FeaturePreprocessor(experiment=experiment)
feature_sel = FeatureSelector(experiment=experiment, target_number=1)

# Use sklearn fit/transform pattern
feature_eng.fit(data)
data_eng = feature_eng.get_data()

feature_prep.fit(data_eng)
data_preprocessed = feature_prep.transform(data_eng)

feature_sel.fit(data_preprocessed)

# Or use in sklearn Pipeline
from sklearn.pipeline import Pipeline
pipeline = Pipeline([
    ('feature_eng', FeatureEngineer(experiment=experiment)),
    ('feature_prep', FeaturePreprocessor(experiment=experiment))
])
```

## Expected Data Format

- Both `your_dataframe` and `new_data` should be pandas `DataFrame` objects.
- `your_dataframe` must contain all feature columns **plus one column per target** named `TARGET_i` (e.g., `TARGET_1`, `TARGET_2`).
- LeCrapaud trains one model per target listed in `target_numbers`; classification targets are those listed in `target_clf`.
- `new_data` should include only the feature columns (no `TARGET_i`, unless you want to evaluate on an extra test set).

## Example: Time Series Configuration

```python
context = {
    "experiment_name": "energy_forecast",
    "date_column": "timestamp",
    "group_column": "site_id",
    "time_series": True,
    "val_size": 0.2,
    "test_size": 0.2,

    # Feature engineering
    "columns_drop": ["equipment_id"],
    "columns_boolean": ["is_weekend"],
    "columns_date": ["timestamp"],
    "columns_onehot": ["weather_condition"],
    "columns_binary": ["region"],

    # PCA on temporal blocks (auto-creates lags)
    "pca_temporal": [
        {"name": "LAST_48_LOAD", "column": "load_kw", "lags": 48},
        {"name": "LAST_24_TEMP", "column": "temperature_c", "lags": 24},
    ],
    # Cross-sectional PCA across sites
    "pca_cross_sectional": [
        {"name": "SITE_LOAD_FACTORS", "index": "timestamp", "columns": "site_id", "value": "load_kw"}
    ],

    # Feature selection
    "corr_threshold": 80,
    "max_features": 30,
    "auto_select_feature_count": True,

    # Model selection
    "target_numbers": [1],
    "target_clf": [],
    "models_idx": ["lgb", "xgb"],
    "perform_hyperopt": True,
    "number_of_trials": 40,
    "optimization_metric": "RMSE",
}

lc = LeCrapaud(**context)
lc.fit(your_dataframe)
```

## Using Alembic in Your Project

If you use Alembic for migrations and share the same database with LeCrapaud, add this filter to your `env.py`:

```python
def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and name.startswith(f"{LECRAPAUD_TABLE_PREFIX}_"):
        return False  # Ignore LeCrapaud tables
    return True

context.configure(
    # ... other options ...
    include_object=include_object,
)
```

## Contributing

### How We Work

- Use conventional commits (e.g., `feat: add lgbm tuner`, `fix: handle missing target`)
- Create feature branches (`feat/...`, `fix/...`) off `main`; keep PRs focused and small
- Before opening a PR: `make format && make lint && make test`
- Write/adjust tests when changing behavior or adding features
- Documentation is part of the change: update README/examples/docstrings when APIs change

### Development Setup

```sh
python -m venv .venv
source .venv/bin/activate
make install
# Optional GPU deps
make install-gpu
```

---

Pierre Gallet 2025
