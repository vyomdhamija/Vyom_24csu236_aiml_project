import json
import os

import joblib
import pandas as pd

MODEL_DIR = os.path.dirname(__file__)

_model = None
_categories = None
_feature_importance = None
_toxicity_stats = None


def _model_path():
    return os.path.join(MODEL_DIR, "fungi_model.pkl")


def load_model():
    global _model
    if _model is None:
        if not os.path.exists(_model_path()):
            raise FileNotFoundError("fungi_model.pkl not found. Run train.py first.")
        _model = joblib.load(_model_path())
    return _model


def _load_json(filename):
    path = os.path.join(MODEL_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"{filename} not found. Run train.py first.")
    with open(path, "r") as f:
        return json.load(f)


def get_categories():
    global _categories
    if _categories is None:
        _categories = _load_json("categories.json")
    return _categories


def get_feature_importance():
    global _feature_importance
    if _feature_importance is None:
        _feature_importance = _load_json("feature_importance.json")
    return _feature_importance


def get_toxicity_stats():
    global _toxicity_stats
    if _toxicity_stats is None:
        _toxicity_stats = _load_json("toxicity_stats.json")
    return _toxicity_stats


def predict_toxicity(mushroom: dict) -> dict:
    """
    Returns prediction payload mapping Class 1 probabilities (Poisonous).
    """
    model = load_model()
    df = pd.DataFrame([mushroom])
    prob = model.predict_proba(df)[0][1] 
    prediction = model.predict(df)[0]
    
    return {
        "toxicity_probability": round(float(prob) * 100, 2),
        "is_poisonous": bool(prediction)
    }