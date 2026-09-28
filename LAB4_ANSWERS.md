# Lab 4 - Answers

## Q1
Without a volume, the MLflow SQLite database and artifacts are stored inside
the container's writable filesystem. Stopping the container keeps the data, but
removing the container deletes it. A newly created container therefore starts
with an empty MLflow server.

## Q2
A named volume is managed by Docker and persists independently of the
containers. A bind mount could also persist the data, but it depends on a
specific host filesystem path and its permissions, making the setup less
portable.

## Q3
Docker Compose creates a default private network for the services. It also
provides DNS resolution using service names, so the hostname `mlflow` resolves
to the MLflow container. Therefore the inference service can use
`http://mlflow:5000`.

## Q4
Using the `INFERENCE_URL` environment variable keeps the frontend independent
of the deployment environment. Locally it can use `127.0.0.1:8000`, while in
Docker Compose it can use `http://inference:8000`, without changing the
application code.

## Q5
Only MLflow and the frontend publish ports to the host. The inference service
does not need a host port because the frontend communicates with it through
the private Docker Compose network using `http://inference:8000`.

The published ports are:
- MLflow: `5000:5000`
- Frontend: `8501:8501`

The inference service only exposes port 8000 inside the Compose network.

## Q6
`depends_on` controls container startup order, but it does not guarantee that
MLflow is fully ready before the inference service starts.

Therefore, the inference service may start while MLflow is still unavailable
and fail when trying to load the model. The problem can be inspected using:

`docker compose logs inference`

## Q7
`docker compose ps` showed that MLflow and the frontend publish ports to the
host:

- MLflow publishes port 5000.
- Frontend publishes port 8501.
- Inference has port 8000 internally but does not publish it to the host.

The frontend successfully communicated with the inference service through the
Compose network and returned a Food-11 prediction.

## Q8
Initially, Version 1 was referenced by the `champion` alias. For the experiment,
the same model was registered again as Version 2 and the `champion` alias was
moved to Version 2.

Changing the alias in MLflow did not immediately change the model used by the
running inference service because the model is loaded once when the FastAPI
application starts.

Before restarting inference:

`champion -> Version 2`

but the running inference process still had Version 1 loaded in memory.

After:

`docker compose restart inference`

the inference application started again, resolved `food11@champion`, and loaded
Version 2.

The lab describes this operation using the Staging model stage. In this project,
the `champion` model alias is used as the deployment pointer instead.

## Q9
Restarting the inference container is sufficient because the model is fetched
from MLflow at application startup. The model itself is not baked into the
Docker image.

Therefore, changing which model version `champion` references does not require
rebuilding the Docker image. Restarting the inference service makes it load the
currently referenced model.

## Q10
After running:

`docker compose down`

and then:

`docker compose up -d`

the registered `food11` model and its `champion` alias were still present.
This is because `docker compose down` removes the containers and network but
does not remove the named `mlflow-data` volume.

After running:

`docker compose down -v`

and starting the stack again, MLflow was empty. The `-v` option deleted the
named volume containing the MLflow SQLite database and artifacts.

This demonstrates that the named volume provides persistence independently of
the lifecycle of the containers.

## Q11
Docker Compose is designed primarily for running a multi-container application
on a single Docker host. It does not provide full multi-machine orchestration,
high availability, automatic failover, or production-scale load balancing.

To run multiple inference replicas behind a load balancer and allow MLflow to
survive the failure of a machine, an orchestration platform such as Kubernetes
could be used.

For MLflow high availability, the SQLite database and local Docker volume would
also need to be replaced by shared durable infrastructure, such as an external
database and shared artifact storage.
