from __future__ import annotations

import os
from io import BytesIO

import mlflow
import numpy as np
import torch
from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image
from torchvision import transforms
from torchvision.models import ResNet18_Weights


MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
MODEL_URI = "models:/food11@champion"

# Same order used by torchvision.datasets.ImageFolder in train.py.
CLASS_NAMES = [
    "Bread",
    "Dairy product",
    "Dessert",
    "Egg",
    "Fried food",
    "Meat",
    "Noodles-Pasta",
    "Rice",
    "Seafood",
    "Soup",
    "Vegetable-Fruit",
]

weights = ResNet18_Weights.DEFAULT
preprocess = transforms.Compose(
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

app = FastAPI(title="Food-11 Model API")
model = None


@app.on_event("startup")
def load_model() -> None:
    global model
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    model = mlflow.pyfunc.load_model(MODEL_URI)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def read_image(file_bytes: bytes) -> Image.Image:
    try:
        image = Image.open(BytesIO(file_bytes))
        return image.convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid image file") from exc


def softmax(logits: np.ndarray) -> np.ndarray:
    logits = logits.astype(np.float64)
    logits = logits - np.max(logits)
    exp = np.exp(logits)
    return exp / np.sum(exp)


@app.post("/predict")
async def predict(file: UploadFile = File(...)) -> dict[str, float | str]:
    if model is None:
        raise HTTPException(status_code=503, detail="Model is not loaded")

    image = read_image(await file.read())
    tensor = preprocess(image).unsqueeze(0)
    batch = tensor.detach().cpu().numpy().astype(np.float32)

    outputs = model.predict(batch)
    if isinstance(outputs, torch.Tensor):
        outputs = outputs.detach().cpu().numpy()

    logits = np.asarray(outputs)
    if logits.ndim > 1:
        logits = logits[0]

    probabilities = softmax(logits)
    class_index = int(np.argmax(probabilities))

    return {
        "category": CLASS_NAMES[class_index],
        "confidence": float(probabilities[class_index]),
    }
