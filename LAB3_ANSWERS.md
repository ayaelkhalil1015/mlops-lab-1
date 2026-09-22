# Lab 3 - Docker Answers

## Q1
The registered Food-11 model is Version 1.

A run artifact is the model output associated with a specific MLflow experiment run. A registered model gives the model a stable name and version, making it easier to manage and deploy.

## Q2
MLflow aliases such as `champion` and `challenger` replace the older stage-based approach. An alias is a movable pointer to a model version. For example, `champion` currently points to Version 1. If a better Version 2 is registered later, the alias can be moved to Version 2 without changing the serving application.

## Q3
Using `models:/food11@champion` decouples the serving API from a specific model file or version. The application always loads the model referenced by the `champion` alias, so a newer model can be deployed by changing the alias instead of modifying the API code.

## Q4
The dependency files (`pyproject.toml` and `uv.lock`) are copied before the source code so Docker can cache the dependency installation layer. If only the application source changes, Docker can reuse the dependency layer instead of reinstalling all dependencies.

## Q5
The multi-stage image had a disk usage of 2.41 GB and a content size of 525 MB. The naive single-stage image had a disk usage of 2.14 GB and a content size of 460 MB.

In this experiment, the multi-stage image was not smaller. The largest layer was the copied `.venv`, around 1.75 GB. Multi-stage builds separate the build environment from the runtime environment, but they do not automatically guarantee a smaller final image.

## Q6
`.dockerignore` prevents unnecessary files and directories such as `data/`, `mlruns/`, `mlflow.db`, `.venv/`, and `.git/` from being sent in the Docker build context. This reduces unnecessary build context, avoids accidentally including large datasets or local artifacts, and makes builds cleaner.

## Q7
Inside a container, `127.0.0.1` refers to the container itself, not the host computer. `host.docker.internal` allows a Docker Desktop container to access a service running on the host.

In our environment, the container used `http://host.docker.internal:5000` to reach the MLflow server.

## Q8
After stopping the first container, a new container was successfully started from the same `food11-api:latest` image without rebuilding it.

This works because the application code and dependencies are already packaged in the Docker image. The model is resolved at runtime through MLflow. In our setup, the local MLflow artifact directory was also mounted into the container because the model artifacts were stored on the local filesystem.

## Q9
To run the application on another machine or deployment platform, the Docker image should be pushed to an image registry such as Docker Hub or GitHub Container Registry. The other machine can then pull the same tagged image or image digest and run it. Git stores the source code and Dockerfile, while the container registry stores the built Docker image.
