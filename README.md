# MLOps Labs - Food-11

This repository contains Lab 1 and Lab 2 of the MLOps course.

## Lab 1 - Git, DVC and Data Preparation

Lab 1 prepares the Food-11 dataset and sets up reproducible data versioning.
The workflow uses Git for source code and project metadata, and DVC with
DagsHub for the dataset files.

Main files:

- `src/food11/data.py`
- `data.dvc`
- `LAB_ANSWERS.md`

### Environment Setup

Install dependencies with:

```powershell
uv sync
```

The project uses Python 3.12. Lab 1 uses Pillow for image preprocessing and
DVC with S3 support for data versioning.

### Git and DVC Architecture

Git tracks project files such as source code, `pyproject.toml`, `uv.lock`,
`.dvc/config`, and `data.dvc`. DVC tracks the actual Food-11 dataset files
under `data/` and stores them in the configured DagsHub remote.

The DVC remote uses DagsHub's S3-compatible storage:

```text
s3://dvc
endpoint: https://dagshub.com/ayaelkhalil1015/mlops-lab-1.s3
```

Credentials are stored locally in `.dvc/config.local` and are not committed.

### Dataset Structure

After pulling the latest DVC version, `data/` contains:

```text
data/
  food11_raw/
  food11_processed/
  food11_processed_mini/
```

Each dataset contains the Food-11 splits:

```text
training/
evaluation/
validation/
```

The processed datasets are organized by class name and use 128x128 RGB images.
The mini dataset contains at most 100 images per split and class.

### Preprocessing

Run preprocessing with:

```powershell
uv run python ./src/food11/data.py
```

The script reads `data/food11_raw`, resizes images to 128x128, converts them to
RGB, and writes both the full processed dataset and the mini dataset.

### Restore Data

After cloning the repository, Git provides `data.dvc` but not the actual image
files. Restore the dataset with:

```powershell
uv sync
uv run dvc pull
```

### Reproducibility

The committed `data.dvc` file identifies the exact data version. Running
`dvc pull` restores the dataset version that matches the current Git commit.
Switching Git commits and running `dvc checkout` updates the local `data/`
directory to the data version referenced by that commit.

## Lab 2 - Model Training and MLflow

Lab 2 adds model training and experiment tracking. The training code uses a
pretrained ResNet18 model adapted to the 11 Food-11 classes, trains it with
PyTorch, and logs runs with MLflow.

The experiments compare hyperparameters using learning rate and batch size. The
training script supports both the mini and full processed Food-11 datasets.

Main files:

- `src/food11/train.py`
- `LAB2_ANSWERS.md`

Local MLflow outputs such as `mlflow.db` and `mlruns/` are intentionally not
tracked by Git. The Food-11 data remains managed by DVC.
