"""Train a ResNet18 Food-11 classifier with MLflow tracking.

Example:
    uv run python ./src/food11/train.py --dataset mini --epochs 5 --lr 0.001 --batch-size 32
"""

from __future__ import annotations

import argparse
import inspect
import sys
import urllib.error
import urllib.request
from pathlib import Path

import mlflow
import mlflow.pytorch
import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms
from torchvision.models import ResNet18_Weights


REPO_ROOT = Path(__file__).resolve().parents[2]
DATASETS = {
    "mini": REPO_ROOT / "data" / "food11_processed_mini",
    "processed": REPO_ROOT / "data" / "food11_processed",
}
SPLITS = {
    "train": "training",
    "val": "validation",
    "test": "evaluation",
}
NUM_CLASSES = 11
TRACKING_URI = "http://127.0.0.1:5000"
EXPERIMENT_NAME = "food11"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Food-11 with MLflow tracking.")
    parser.add_argument("--dataset", choices=DATASETS.keys(), required=True)
    parser.add_argument("--epochs", type=int, required=True)
    parser.add_argument("--lr", type=float, required=True)
    parser.add_argument("--batch-size", type=int, required=True)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--check-only", action="store_true")
    return parser.parse_args()


def fail(message: str) -> None:
    sys.exit(f"ERROR: {message}")


def check_mlflow_server(uri: str) -> None:
    try:
        with urllib.request.urlopen(uri, timeout=5) as response:
            if response.status >= 400:
                fail(f"MLflow server returned HTTP {response.status} at {uri}")
    except urllib.error.URLError as exc:
        fail(
            "MLflow tracking server is unreachable. Start it with: "
            "uv run mlflow server --host 127.0.0.1 --port 5000 "
            "--backend-store-uri sqlite:///mlflow.db "
            "--default-artifact-root ./mlruns"
            f"\nDetails: {exc}"
        )


def validate_dataset_root(dataset_root: Path) -> None:
    if not dataset_root.is_dir():
        fail(f"Dataset path does not exist: {dataset_root}")
    for split_dir in SPLITS.values():
        path = dataset_root / split_dir
        if not path.is_dir():
            fail(f"Missing dataset split directory: {path}")
        class_dirs = [p for p in path.iterdir() if p.is_dir()]
        if len(class_dirs) != NUM_CLASSES:
            fail(f"Expected {NUM_CLASSES} classes in {path}, found {len(class_dirs)}")


def build_dataloaders(
    dataset_root: Path, batch_size: int, num_workers: int
) -> tuple[dict[str, DataLoader], list[str]]:
    weights = ResNet18_Weights.DEFAULT
    transform = transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=weights.transforms().mean,
                std=weights.transforms().std,
            ),
        ]
    )

    image_datasets = {
        name: datasets.ImageFolder(dataset_root / split_dir, transform=transform)
        for name, split_dir in SPLITS.items()
    }
    class_names = image_datasets["train"].classes
    if len(class_names) != NUM_CLASSES:
        fail(f"Expected {NUM_CLASSES} detected classes, found {len(class_names)}")
    for name, dataset in image_datasets.items():
        if dataset.classes != class_names:
            fail(f"Class mismatch in {name} split")

    dataloaders = {
        "train": DataLoader(
            image_datasets["train"],
            batch_size=batch_size,
            shuffle=True,
            num_workers=num_workers,
        ),
        "val": DataLoader(
            image_datasets["val"],
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
        ),
        "test": DataLoader(
            image_datasets["test"],
            batch_size=batch_size,
            shuffle=False,
            num_workers=num_workers,
        ),
    }
    return dataloaders, class_names


def build_model(device: torch.device) -> nn.Module:
    model = models.resnet18(weights=ResNet18_Weights.DEFAULT)
    for param in model.parameters():
        param.requires_grad = False
    model.fc = nn.Linear(model.fc.in_features, NUM_CLASSES)
    return model.to(device)


def run_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    optimizer: torch.optim.Optimizer | None = None,
) -> tuple[float, float]:
    is_training = optimizer is not None
    model.train() if is_training else model.eval()

    total_loss = 0.0
    total_correct = 0
    total_examples = 0

    context = torch.enable_grad() if is_training else torch.no_grad()
    with context:
        for inputs, labels in dataloader:
            inputs = inputs.to(device)
            labels = labels.to(device)

            if is_training:
                optimizer.zero_grad()

            outputs = model(inputs)
            loss = criterion(outputs, labels)

            if is_training:
                loss.backward()
                optimizer.step()

            batch_size = labels.size(0)
            total_loss += loss.item() * batch_size
            total_correct += (outputs.argmax(dim=1) == labels).sum().item()
            total_examples += batch_size

    return total_loss / total_examples, total_correct / total_examples


def log_pytorch_model(model: nn.Module) -> None:
    kwargs = {"name": "model", "serialization_format": "pickle"}
    if "name" not in inspect.signature(mlflow.pytorch.log_model).parameters:
        kwargs = {"artifact_path": "model", "serialization_format": "pickle"}
    mlflow.pytorch.log_model(model, **kwargs)


def main() -> None:
    args = parse_args()
    dataset_root = DATASETS[args.dataset]
    validate_dataset_root(dataset_root)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Selected device: {device}")
    print(f"Dataset root: {dataset_root}")

    dataloaders, class_names = build_dataloaders(
        dataset_root=dataset_root,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
    )
    print(f"Detected classes ({len(class_names)}): {class_names}")

    model = build_model(device)
    if model.fc.out_features != NUM_CLASSES:
        fail(f"Model output dimension is {model.fc.out_features}, expected {NUM_CLASSES}")
    print(f"Model output classes: {model.fc.out_features}")

    if args.check_only:
        print("Check-only validation passed.")
        return

    check_mlflow_server(TRACKING_URI)
    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.fc.parameters(), lr=args.lr)

    with mlflow.start_run():
        mlflow.log_params(
            {
                "dataset": args.dataset,
                "epochs": args.epochs,
                "lr": args.lr,
                "batch_size": args.batch_size,
                "device": str(device),
                "model_name": "resnet18",
                "num_classes": NUM_CLASSES,
            }
        )

        for epoch in range(1, args.epochs + 1):
            train_loss, _ = run_epoch(
                model, dataloaders["train"], criterion, device, optimizer
            )
            val_loss, val_accuracy = run_epoch(
                model, dataloaders["val"], criterion, device
            )

            mlflow.log_metric("train_loss", train_loss, step=epoch)
            mlflow.log_metric("val_loss", val_loss, step=epoch)
            mlflow.log_metric("val_accuracy", val_accuracy, step=epoch)

            print(
                f"Epoch {epoch}/{args.epochs} "
                f"train_loss={train_loss:.4f} "
                f"val_loss={val_loss:.4f} "
                f"val_accuracy={val_accuracy:.4f}"
            )

        _, test_accuracy = run_epoch(model, dataloaders["test"], criterion, device)
        mlflow.log_metric("test_accuracy", test_accuracy)
        log_pytorch_model(model)
        print(f"test_accuracy={test_accuracy:.4f}")


if __name__ == "__main__":
    main()
