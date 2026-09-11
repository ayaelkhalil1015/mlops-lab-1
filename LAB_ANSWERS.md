# Lab 1 Answers

## Question 1

`uv init` created the Python project structure and configuration files. In this
repo, `pyproject.toml` defines the project metadata and dependencies, while
`uv.lock` records exact package versions for reproducible installs.

## Question 2

`dvc init` created the DVC project configuration under `.dvc/` and DVC ignore
files. DVC configuration and metadata such as `.dvc/config` and `data.dvc`
belong in Git; the DVC cache and actual dataset files do not.

## Question 3

DVC credentials configured with `--global` are stored outside the repository in
the user's DVC config directory. Repository config is in `.dvc/config`, and
local private config is in `.dvc/config.local`. Secrets must not be committed or
uploaded to GitHub.

## Question 4

After `dvc add data`, `.gitignore` was updated to ignore `/data`. This prevents
the actual Food-11 image files from being tracked by Git while allowing
`data.dvc` to be committed.

## Question 5

`data.dvc` contains metadata for the tracked `data/` output: the hash, size,
file count, and path. It is a pointer to a DVC data version, not the dataset
itself and not the DVC cache.

## Question 6

After `git push`, GitHub stores source code, project files, DVC config, and
`data.dvc`. After `dvc push`, DagsHub stores the actual dataset objects. In this
repo, the raw version and processed version were pushed to the DagsHub S3 DVC
remote.

## Question 7

A fresh Git clone contains files such as `src/`, `pyproject.toml`, `uv.lock`,
`.dvc/config`, and `data.dvc`, but not `data/`. Running `dvc pull` downloads the
dataset from DagsHub and restores `food11_raw`, `food11_processed`, and
`food11_processed_mini`.

## Question 8

Checking out the raw-only Git commit `5f76b1d` and running `dvc checkout`
changed `data/` back to only `food11_raw`. Returning to `main` and running
`dvc checkout` restored the latest version with raw, processed, and mini
datasets.
