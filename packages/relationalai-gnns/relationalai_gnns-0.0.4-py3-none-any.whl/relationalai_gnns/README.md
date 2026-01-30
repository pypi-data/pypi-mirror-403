# GNN-RLE SDK Documentation

## Overview

The ***GNN-RLE SDK*** is a Python interface to the GNN Relational Learning Engine (GNN-RLE). It enables users to define graph-structured data, configure models, train models, run inference, and monitor training jobs through a high-level API.

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
2. [Core Components](#core-components)
    - [Provider](#provider)
    - [Connector](#connector)
    - [GNNTable](#gnntable)
      - [Column Dtypes](#column-dtypes)
    - [Task](#task)
      - [Node Tasks](#node-tasks)
      - [Link Tasks](#link-tasks)
      - [Time columns](#time-columns)
    - [Dataset](#dataset)
    - [TrainerConfig](#trainerconfig)
    - [Trainer](#trainer)
        - [Training a Model](#training-a-model)
        - [Running Inference](#running-inference)
    - [JobMonitor](#jobmonitor)
    - [JobManager](#jobmanager)
3. [Notebooks](#notebooks)
4. [License](#license)

---

## System Requirements

If you want to visualize the database schema you will need to install Graphviz.
Make sure Graphviz is installed on your system (for the `dot` binary to be available):

- macOS: `brew install graphviz`
- Ubuntu: `sudo apt install graphviz`
- Windows: [Download Graphviz](https://graphviz.org/download/) and add it to your PATH

To verify the installation on a Jupyter Notebook you can run the command:
```python
!which dot
```
which should point to the location that Graphviz is installed, or you can use the following sanity check:
```python
 from graphviz import Digraph

dot = Digraph()
dot.node('A')
dot.node('B')
dot.edge('A', 'B')
dot.render('test-output.gv', view=False)
```

As a workaround if `dot` is in a known location you can try setting the path explicitly at the start of your imports:
```python
import os
os.environ["PATH"] += os.pathsep + "/opt/homebrew/bin"
```


---

## Installation

To install the SDK first create and activate a conda environment:

```bash
conda create -n rai_gnn_env python==3.11
conda activate rai_gnn_env
```

👉 **Option A: Install from source (recommended for development)**

From the root folder of the repository:

```bash
pip install -e .
```

👉 **Option B: Install from a prebuilt wheel**

Download the wheel file from:
[Google Drive link](https://drive.google.com/drive/folders/1dYF_yhkRyVUGjZcqBcAIgpEIAyl1R4CE)

Then install it:

```bash
pip install relationalai_gnns-0.1.0-py3-none-any.whl
```

---

## Core Components

### Provider

The Provider class is your gateway to managing GNN engines in Snowflake. It enables you to:
- Create and delete GNN engines
- List available engines
- Resume suspended engines
- Monitor engine status

#### Authentication Methods

The Provider supports three authentication methods:

1. **Password Authentication** 🔑
```python
snowflake_config = {
    "account": os.getenv("ACCOUNT_NAME"),
    "user": os.getenv("USER_NAME"),
    "password": os.getenv("PASSWORD"),
    "warehouse": os.getenv("WAREHOUSE"),
    "app_name": os.getenv("APP_NAME"),
    "auth_method": "password"
}
```

2. **Key Pair Authentication** 🔐
```python
snowflake_config = {
    "account": os.getenv("ACCOUNT_NAME"),
    "user": os.getenv("USER_NAME"),
    "private_key_path": os.getenv("PRIVATE_KEY_PATH"),
    "warehouse": os.getenv("WAREHOUSE"),
    "app_name": os.getenv("APP_NAME"),
    "auth_method": "key_pair"
}
```

3. **OAuth Token Authentication** 🔓
```python
snowflake_config = {
    "account": os.getenv("ACCOUNT_NAME"),
    "oauth_token": os.getenv("ACCESS_TOKEN"),
    "warehouse": os.getenv("WAREHOUSE"),
    "app_name": os.getenv("APP_NAME"),
    "auth_method": "oauth"
}
```

#### Basic Usage

1. **Initialize the Provider**
```python
from relationalai_gnns import Provider

provider = Provider(**snowflake_config)
```

2. **List Available Engines**
```python
# List all engines
engines = provider.list_gnns()
```

3. **Create a New Engine**
```python
# Available sizes: "GPU_NV_S" or "HIGHMEM_X64_S"
provider.create_gnn(
    name="my_engine",
    size="GPU_NV_S"  # or "HIGHMEM_X64_S"
)
```

4. **Get Engine Details**
```python
# Returns engine status
engine_info = provider.get_gnn("my_engine")
```

5. **Manage Engine State**
```python
# Resume a suspended engine
provider.resume_gnn(name="my_engine")

# Delete an engine when no longer needed
provider.delete_gnn(name="my_engine")
```

⚠️ **Important Notes:**
- Engine names must be unique within your account
- Engines are automatically suspended after a period of inactivity
- Suspended engines can be resumed using `resume_gnn()`

### Connector

Establishes a connection to a data source. Example:

```python
from relationalai_gnns import SnowflakeConnector

# we initialize the connector passing the
# snowflake creadentials as well as the engine
# that we want to use
connector = SnowflakeConnector(
    **snowflake_config,
    engine_name = "engine_name"
)
```

---

### GNNTable

Represents a table that will be used as a node in the GNN. Supports:

- Primary key definition
- Foreign key definitions
- Time column definition
- Selection of input columns and column data type configuration

```python
from relationalai_gnns import GNNTable, ForeignKey
from relationalai_gnns import ColumnDType

# create a table with a primary key
# column data types are automatically populated
student_table = GNNTable(
    connector=connector,
    name="Students",
    source="...STUDENTS",
    primary_key="studentId"
)

# show table contents
student_table.show_table()

# create second table
class_table = GNNTable(
    connector=connector,
    name="Classes",
    source="...CLASSES",
    primary_key="classId"
)

# drop column from a GNN Table
class_table.remove_column(col_name="credits")
# add it back
class_table.add_column(col_name="credits", dtype=ColumnDType.category_t)

# change column dtype
class_table.update_column_dtype(col_name="credits", dtype=ColumnDType('float'))

# unset and set primary keys
class_table.unset_primary_key(col_name="classId")
class_table.set_primary_key(col_name="classId")

# create a table with a foreign key
student_takes_class_table = GNNTable(
    connector=connector,
    name="StudentsTakeClass",
    source="...STUDENTS_TAKE_CLASS",
    foreign_keys=[ForeignKey(column_name="studentId", link_to="Students.studentId"),
                  ForeignKey(column_name"classId", link_to="Classes.classId")]
)

# set and unset foreign keys
student_takes_class_table.unset_foreign_key(ForeignKey(column_name="studentId", link_to="Students.studentId"))
student_takes_class_table.set_foreign_key(ForeignKey(column_name="studentId", link_to="Students.studentId"))

# set and unset time column -- does not exist in this table
# student_takes_class_table.set_time_column(col_name="date")
# student_takes_class_table.unset_time_column(col_name="date")

# validate table
student_takes_class_table.validate_table()

```
A `GNNTable` can have multiple foreign keys, one primary key and one time column.
A `GNNTable` cannnot have multiple primary keys or time columns.
A `GNNTable` must have at least one primary key or a foreign key.

Note: The `GNNTable` does not provide access to the actual data (it does not load
a dataframe with the data from a Snowflake table). The `GNNTable` describes the
***metadata*** of a database table.

⚠️ **Important Note:**
Ensure your application has the necessary permissions to access the databases you intend to read from and write to. Without these grants, the GNN engine will not be able to query data or store results.

Below are example SQL statements to grant the required permissions.
**Tip:** For security, grant access only to the specific databases, schemas, and tables your application needs.

```sql
-- Grant usage on the database to the application
GRANT USAGE ON DATABASE <DB_NAME> TO APPLICATION <APP_NAME>;

-- Grant usage on the schema to the application
GRANT USAGE ON SCHEMA <DB_NAME>.<SCHEMA_NAME> TO APPLICATION <APP_NAME>;

-- Grant read access to a specific table
GRANT SELECT ON TABLE <DB_NAME>.<SCHEMA_NAME>.<TABLE_NAME> TO APPLICATION <APP_NAME>;

-- Grant write access to create tables in a specific schema
GRANT CREATE TABLE ON SCHEMA <DB_NAME>.<SCHEMA_NAME> TO APPLICATION <APP_NAME>;
```

**Replace** `<DB_NAME>`, `<SCHEMA_NAME>`, `<TABLE_NAME>`, and `<APP_NAME>` with your actual database, schema, table, and application names.

**Best Practice:**
- Only grant the minimum permissions required for your use case.
- Avoid granting access to all schemas or tables unless absolutely necessary.

---


#### Column DTypes

When a user creates a `GNNTable()` object, the learning engine automatically performs dtype inference for all columns in the table. A column's `dtype` determines how it will be encoded and interpreted by the graph neural network model.

The following column dtypes are supported:

- `ColumnDType('text')`
Used for columns containing free-form text. These will be encoded appropriately for NLP processing.

- `ColumnDType('integer')`
Used for columns containing integer values.

- `ColumnDType('float')`
Used for columns containing floating-point numbers.

- `ColumnDType('category')`
Used for columns with discrete categorical values.

- `ColumnDType('multi_categorical')`
Used for columns containing multiple categorical values, typically represented as a list (e.g., ['car', 'red']).

- `ColumnDType('embedding')`
Used for columns containing fixed-size embedding vectors (e.g., outputs from external models). All embeddings in the column must have the same dimensionality.

- `ColumnDType('datetime')`
Used for columns containing date or timestamp information. Time columns must always be of type datetime.


---

### Task

Defines the GNN learning task.

- **NodeTask**: For node classification and regression tasks.
- **LinkTask**: For link prediction tasks.

```python
from relationalai_gnns import LinkTask, NodeTask, TaskType
from relationalai_gnns import EvaluationMetric

# Example: Defining a node classification task for binary classification.
#
# - source_entity_table: the table containing the entities (nodes) we want to classify.
# - source_entity_column: the column that uniquely identifies each entity in the table.
# - target_column: the column of the task table that contains the labels used for training,
#   validation, and (optionally) testing (users can choose not to provide labels for the test
#   data).
#
# The task_data_source maps each dataset split to the corresponding table name.
node_task = NodeTask(
    connector=connector,
    name="my_node_task",
    task_data_source={
        "train": "...TRAIN",
        "test": "...TEST",
        "validation": "...VALIDATION"
    },
    source_entity_column="studentId",
    source_entity_table="Students",
    target_column="label",
    task_type=TaskType.BINARY_CLASSIFICATION
)

# Show task
node_task.show_task()

# Add an evaluation metric (other than the default)
node_task.set_evaluation_metric(EvaluationMetric(name="accuracy"))

# Example: Defining a link prediction task (e.g., recommending articles to customers).
#
# - source_entity_table: the table containing the entities we are making recommendations for (e.g., customers).
# - source_entity_column: the column that uniquely identifies each source entity.
# - target_entity_table: the table containing the items to recommend (e.g., articles).
# - target_entity_column: the column that uniquely identifies each target entity.
#
# The task_data_source specifies the data used for training and validation.
user_item_purchase_task = LinkTask(
    connector=connector,
    name="user_item_purchase",
    task_data_source={
        "train": "...TRAIN",
        "validation": "...VALIDATION",
    },
    source_entity_column="customer_id",
    source_entity_table="customers",
    target_entity_column="article_id",
    target_entity_table="articles",
    task_type=TaskType.LINK_PREDICTION,
    evaluation_metric=EvaluationMetric(name="link_prediction_map", eval_at_k=12)
)

# Set the time column of the task
user_item_purchase_task.set_time_column(col_name="timestamp")
```

#### Node tasks
- `TaskType.BINARY_CLASSIFICATION`: Describes a binary classification task. Labels can be of any dtype. The restriction is that labels can take only two values.
- `TaskType.MULTICLASS_CLASSIFICATION`: Similar to binary classification, but the target column can have up to N distinct classes, where N > 2.
- `TaskType.MULTILABEL_CLASSIFICATION`:  In a multi-label classification problem each instance can belong to 1 or more out of N total classes. The multi-label classification labels are represented as a list, the list having the classes each instance belongs to. Labels inside the list can be of any dtype.
- `TaskType.REGRESSION`: Used for regression problems where targets are expected to be either float or int dtypes.

#### Link tasks
- `TaskType.LINK_PREDICTION`: This is a classic link prediction problem during which we try to identify a list of the top-k most similar destination entities given a source entity. Targets (specified by the `target_entity_column`) are expected to be formatted as a list.
- `TaskType.REPEATED_LINK_PREDICTION`: This is a modified version of a link prediction problem (one can think of it as casting link prediction to a node classification problem). Here we are trying to identify the list of the top-k destination entities that a given source entity will visit again. Targets (specified by the `target_entity_column`) are expected to be formatted as a list.

#### Time columns
When creating a `GNNTable()` object or defining a task, you have the option to specify one of the dataset's columns as a **time column**. Time columns are essential for **temporal tasks**, ensuring that the model respects the chronological order of events and avoids information leakage.

To understand their role, let's consider a forecasting example.

Suppose we want to train a model to predict the sales of a store on a given date. A sample task table for this regression task might look like:

| STORE\_ID | DATE       | SALES |
| --------- | ---------- | ----- |
| 123       | 10/12/2022 | 500   |
| 123       | 11/12/2022 | 600   |
| 456       | 10/12/2022 | 500   |
| 456       | 11/12/2022 | 500   |


This table contains sales data for two stores over two days. When training a forecasting model, it's critical that the model only has access to data from dates prior to the one it is predicting. If future information is included during training, it will lead to information leakage and overfitting.

By marking a column (e.g., DATE) as a time column, the learning engine enforces this temporal constraint. It will only use data:

- strictly before the prediction date (<), or

- up to and including the prediction date (<=),

depending on how the task is configured. The choice between < and <= depends on the specific requirements of your problem.
When defining the task, the user can set `current_time = True` (<=) or  `current_time = False` (<) to choose the desired behavior.

⚠️ **Important Note:** Only one time column is allowed per table.

---

### Dataset

Combines all tables and the task definition into a dataset ready for training:

```python
from relationalai_gnns import Dataset
from IPython.display import Image, display

dataset = Dataset(
    connector=connector,
    dataset_name="my_first_dataset",
    tables=[student_table, class_table, student_takes_class_table],
    task_description=node_task
)

# visualize dataset
graph = dataset.visualize_dataset()
plt = Image(graph.create_png())
display(plt)
```

A dataset is uniquely identified by its experiment name, which is automatically generated. You can access the experiment name via `dataset.experiment_name` (it is also visible in the MLflow platform and through the `JobMonitor` object).

---

### TrainerConfig

Defines training parameters:

```python
from relationalai_gnns import TrainerConfig

config = TrainerConfig(
    connector=connector,
    n_epochs=10,
    device="cuda",
    patience=5
)
```

🔧 Trainer Configuration Parameters
<details>
<summary><strong>General Settings</strong></summary>

| Parameter | Type  | Description                                                                                |
| --------- | ----- | ------------------------------------------------------------------------------------------ |
| `device`  | `str` | Device to perform training, inference, and feature extraction. One of `"cuda"` or `"cpu"`. |
| `seed`    | `int` | Random seed for reproducibility. Default: `42`.                                            |
</details>
<details>
<summary><strong>Training Settings</strong></summary>

| Parameter          | Type            | Description                                                                                                                        |
| ------------------ | --------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `n_epochs`         | `int`           | Number of training epochs. An epoch corresponds to a full pass over the training data.                                             |
| `max_iters`        | `Optional[int]` | Maximum number of batch iterations per epoch. If `None`, all batches are processed. Otherwise, limits iterations. Default: `None`. |
| `train_batch_size` | `int`           | Batch size for training. Default: `128`.                                                                                           |
| `val_batch_size`   | `int`           | Batch size for validation. Default: `128`.                                                                                         |
| `eval_every`       | `int`           | Frequency (in epochs) to evaluate on the validation set. Default: `1`.                                                             |
| `patience`         | `int`           | Number of epochs without improvement before early stopping. Default: `5`.                                                          |
| `lr`               | `float`         | Learning rate. Default: `0.001`.                                                                                                   |
| `T_max`            | `int`           | Max iterations for cosine annealing scheduler. Defaults to `n_epochs` if `None`. Default: `None`.                                  |
| `eta_min`          | `int`           | Minimum learning rate for cosine annealing. Default: `1e-8`.                                                                       |
</details>
<details>
<summary><strong>Label & Loss Settings</strong></summary>

| Parameter               | Type    | Description                                                              |
| ----------------------- | ------- | ------------------------------------------------------------------------ |
| `label_smoothing`       | `bool`  | Whether to apply label smoothing (for classification). Default: `False`. |
| `label_smoothing_alpha` | `float` | Smoothing parameter α ∈ (0, 1). Default: `0.1`.                          |
| `clamp_min`             | `int`   | Minimum output value for regression tasks. Default: `0`.                 |
| `clamp_max`             | `int`   | Maximum output value for regression tasks. Default: `100`.               |
</details>
<details>
<summary><strong>Graph Neural Network (GNN) Settings</strong></summary>

| Parameter                 | Type                                                   | Description                                                                  |
| ------------------------- | ------------------------------------------------------ | ---------------------------------------------------------------------------- |
| `channels`                | `Optional[int]`                                        | Hidden channels for GNN, encoders, and prediction heads. Default: `128`.     |
| `gnn_layers`              | `Optional[int]`                                        | Number of GNN layers. Defaults to `len(fanouts)` if `None`. Default: `None`. |
| `fanouts`                 | `Optional[List[int]]`                                  | Neighbors to sample per GNN layer. E.g., `[128, 64]`. Default: `[128, 64]`.  |
| `conv_aggregation`        | `Literal["mean", "max", "sum"]`                        | Aggregation method for convolutions. Default: `"mean"`.                      |
| `hetero_conv_aggregation` | `Literal["mean", "max", "sum"]`                        | Aggregation across edge types in heterogeneous graphs. Default: `"sum"`.     |
| `gnn_norm`                | `Literal["batch_norm", "layer_norm", "instance_norm"]` | Normalization for GNN layers. Default: `"layer_norm"`.                       |
</details>
<details>
<summary><strong>Prediction Head Settings</strong></summary>

| Parameter     | Type                                  | Description                                                         |
| ------------- | ------------------------------------- | ------------------------------------------------------------------- |
| `head_layers` | `Optional[int]`                       | Number of MLP layers in the prediction head. Default: `1`.          |
| `head_norm`   | `Literal["batch_norm", "layer_norm"]` | Normalization for the MLP prediction head. Default: `"batch_norm"`. |
</details>
<details>
<summary><strong>Temporal Settings</strong></summary>

| Parameter              | Type                         | Description                                                                                                          |
| ---------------------- | ---------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `use_temporal_encoder` | `bool`                       | Whether to use a temporal encoding model. Default: `True`.                                                           |
| `temporal_strategy`    | `Literal["uniform", "last"]` | Strategy for temporal neighbor sampling. `"uniform"` ignores time; `"last"` picks most recent. Default: `"uniform"`. |
</details>
<details> <summary><strong>Negative Sampling (Link Prediction)</strong></summary>

| Parameter                    | Type            | Description                                                                                           |
| ---------------------------- | --------------- | ----------------------------------------------------------------------------------------------------- |
| `num_negative`               | `Optional[int]` | Number of negative samples per source node (for link prediction). Default: `10`.                      |
| `negative_sampling_strategy` | `Optional[str]` | Strategy: `"random"` or `"degree_based"`. `"degree_based"` favors popular nodes. Default: `"random"`. |
</details>
<details>
<summary><strong>Embeddings & Shallow Features</strong></summary>

| Parameter                 | Type                                                       | Description                                                                                                                                                      |
| ------------------------- | ---------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `text_embedder`           | `Literal["model2vec-potion-base-4M", "bert-base-distill"]` | Text embedding model. Default: `"model2vec-potion-base-4M"`.                                                                                                     |
| `id_awareness`            | `bool`                                                     | Whether to use ID-awareness embeddings. [See source](https://github.com/RelationalAI/gnn-learning-engine/blob/main/src/modeling/model.py#L15). Default: `False`. |
| `shallow_embeddings_list` | `List[str]`                                                | Tables to assign learnable shallow embeddings. Default: `[]`.                                                                                                    |
</details>


---

### Trainer

Used to perform training and inference.

Every time you execute `fit`, `predict`, or `fit_predict` using a `Trainer` object, a job is created and queued for execution. Only one job can be executed at a time. These functions return an instance of a `JobMonitor` object (e.g., `train_job` in the example above).

To initialize a `Trainer` object, pass in the connector and training configuration:

```python
from relationalai_gnns import Trainer

trainer = Trainer(connector=connector, config=config)
```

#### Training a Model

To train a model, call the `.fit()` function and pass the dataset you want to use for training:


```python
train_job = trainer.fit(dataset=dataset)
```

Notice that by calling `.fit()` we initialize a training job (here `train_job` is an object
of type: [`JobMonitor`](#jobmonitor)).

#### Running Inference

Before performing inference, you must specify where the output data should be saved. Data are saved in Snowflake tables.

```python
from relationalai_gnns import OutputConfig

# Save the data to a Snowflake table; specify the database
# and schema (make sure the engine has write permissions)
output_config_snowflake = OutputConfig.snowflake(
    database_name="DATABASE_NAME",
    schema_name="PUBLIC"
)
```

We provide several ways to run inference. In the simplest scenario, you can use a model that has just been trained. Each trained model has a unique identifier, `model_run_id`, provided by MLFlow. After training completes (you can verify this via the job's status), you can access the model's run ID with `train_job.model_run_id`, where `train_job` is an instance of a `JobMonitor` object.

Example of running inference using a trained model:
```python
inference_job = trainer.predict(
    output_alias="EXPERIMENT_1",
    output_config=output_config_snowflake,
    test_batch_size=128,
    dataset=dataset,
    model_run_id=train_job.model_run_id,
    extract_embeddings=True
)
```

In the example above:
- `test_batch_size` is set to 128
- Inference is run on the test set from dataset
- The call returns a `JobMonitor` object that tracks the status of the job

By default, the engine will write the predictions to a table named `PREDICTIONS` in the schema defined in the `OutputConfig`. The predictions will be stored in a table named:
```sql
DATABASE_NAME.PUBLIC.PREDICTIONS_EXPERIMENT_1
```
The `output_alias` (e.g., `EXPERIMENT_1`) helps differentiate results from multiple inference jobs. The application is not permitted to overwrite existing tables. If a table with the same alias already exists, an error is raised.


***Embedding Extraction***

When performing inference, you can also extract embeddings by setting `extract_embeddings=True`. For:

- Node classification: embeddings are returned for the source entity table (as defined in the `NodeTask`)
- Link prediction: embeddings are returned for both source and target entity tables (as defined in the `LinkTask`)

***Embedding table naming convention***

- Source entity embeddings:
```sql
DATABASE_NAME.PUBLIC.EMBEDDINGS_SRC_COL_NAME_ALIAS
```
- Destination entity embeddings:
```sql
DATABASE_NAME.PUBLIC.EMBEDDINGS_TGT_COL_NAME_ALIAS
```
Where:
- `SRC_COL_NAME`/ `TGT_COL_NAME`: source/target entity column names from the task
-  `ALIAS` is the `output_alias` specified as an argument in the `predict()`

**Other inference options**

***✅ Inference using a registered model***:

You can register a trained model in MLFlow by calling `register_model()` on a `JobMonitor object`. For example:

```python
train_job.register_model(model_name="a_test_model")
```
Successful registration returns a message like:

```
✅ Successfully registered model 'a_test_model' with version '1' for job '4e61de75-91eb-49da-8233-89d6c21c6108'
```
Notice that we also add a model version to the registered model name. To perform inference with a registered
model we simply need to add the registered model name and version to `predict()`. As an example:
```python
inference_job = trainer.predict(
    output_alias="TEST_REG_MODEL",
    output_config=output_config_snowflake,
    dataset=dataset,
    registered_model_name="a_test_model",
    version="1",
    extract_embeddings=True
)
```

You can access registered models for a job via:

```python
train_job.registered_models
```
⚠️ Important Note: When a user registers a model using the MLflow UI, MLflow automatically creates a version for the model. This version is displayed as **Version X**, where **X** is the version number. However, the actual version identifier is simply **X** (the numeric part only, without the **Version** prefix).

To load such a model using the SDK, make sure to provide only the version number as a string (e.g., **"1"**, not **"Version 1"**).

***🧪 Inference using an experiment name***:

You can run inference using just an experiment name, without redefining tables, tasks, or datasets. This allows a minimal setup — just initialize the `Trainer` and run:

```python
inference_job = trainer.predict(
    output_alias="EXP_1",
    output_config=output_config_snowflake,
    experiment_name="dataset_name/task_type/task_name",
    test_batch_size=128,
    test_table="GNN_DEMO_TF.TF_LINK_PRED.TEST",
    model_run_id=train_job_1.model_run_id
)
```

Note: When using an experiment name, you must specify the test table path explicitly.

***🏆 Inference using the best model***:

You can also select the model with the best validation results for a dataset or experiment. The engine will choose the best-performing model based on a specified evaluation metric.

```python
# select a metric of interest
metric_of_interest = EvaluationMetric(name="link_prediction_map", eval_at_k=12)
# run inference finding the best model for that metric
inference_job = trainer.predict(
    output_alias="EXP_BEST",
    output_config=output_config,
    dataset=dataset,
    test_batch_size=128,
    model_selection_strategy="best",
    evaluation_metric=metric_of_interest
)
```

***🔁 Training and Inference***
If you'd like to train a model and immediately run inference on the test set, use `fit_predict()`:

```python
inference_job = trainer.fit_predict(
    output_alias="EXP_ALIAS",
    dataset=dataset,
    output_config=output_config,
    test_batch_size=128,
    extract_embeddings=True
)
```

---

### JobMonitor

Used to monitor jobs for training and inference. A job can have the following statuses:
- QUEUED: A job is queued and it is waiting for execution.
- COMPLETED: A job has been completed (e.g., the model has been trained).
- RUNNING: A job is currently beeing executed.
- CANCELED: The job has been canceled by the user.
- FAILED: The job has failed (an error occured).

Using a `JobMonitor` object we can see the current status of a job, obtain the
`model_run_id` (the unique model identifier provided by MLFLow) of a trained model,
stream the logs of the current running job, cancel a job, and get information about
job metadata (such as the model results when a model has finished training).
Below are some example functionalities of a `JobMonitor` object:

```python
# create a job and send it to the queue
train_job = trainer.fit(dataset=dataset)

# request the job status
train_job.get_status()

# get a model run id (can be used to run inference with a specific model)
train_job.model_run_id

# cancel the current job (either removes the job from the queue or stops executing training/inference)
train_job.cancel()

# stream the logs of a job that is running
train_job.stream_logs()

# register a model to MLFLOW that can be later used for inference
train_job.register_model("my_first_model")

```

---

### JobManager

While the `JobMonitor` class can be used to track individual jobs, the `JobManager` class
gives a holistic view of all jobs executed by the user. It also allows one to recover jobs
that might have been lost due to repeated python function calls (see example below).

Example usage:

```python
from relationalai_gnns import JobManager
# create a JobManager
job_manager = JobManager(connector=connector)
# list all jobs and their statuses
job_manager.show_jobs()
# recover a job using it's job ID
foo_job = job_manager.fetch_job("01bbe3b2-0205-0e72-001d-f987ec094ee2")
# we can also cancel a job using the JobManager
job_manager.cancel_job("01bbe3b2-0205-0e72-001d-f987ec094ee2")
```

⚠️ **Important Note:** After an engine is suspended, job IDs will no longer be available. However, experiment results and model run IDs will remain accessible via MLflow—unless the application has been uninstalled.


---

## Notebooks

- [Churn prediction](../notebooks/NodeClassification_spcs_na.ipynb) (binary node classification) using the H&M dataset.
- [Recommendations](../notebooks/LinkPrediction_spsc_na.ipynb) (link prediction using the H&M dataset)

---
## License

This project is licensed under the Apache License 2.0.
See the [LICENSE](LICENSE) file for details.
