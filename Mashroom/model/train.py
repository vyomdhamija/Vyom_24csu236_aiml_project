import os
import json
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score

MODEL_DIR = os.path.join(os.path.dirname(__file__))
os.makedirs(MODEL_DIR, exist_ok=True)

# Support locating the CSV whether ran from root or model folder
possible_paths = [
    "mashroom_data.csv",
    os.path.join(MODEL_DIR, "mashroom_data.csv"),
    os.path.join(MODEL_DIR, "..", "mashroom_data.csv")
]

csv_path = None
for p in possible_paths:
    if os.path.exists(p):
        csv_path = p
        break

if not csv_path:
    raise FileNotFoundError("Could not find mashroom_data.csv. Please place it in the root or model directory.")

print(f"Loading dataset from: {csv_path}")

# IMPORTANT: The dataset uses semicolons instead of commas
df = pd.read_csv(csv_path, sep=';')

if 'class' not in df.columns:
    raise ValueError("Dataset is missing the expected 'class' target column.")

# -------------------------------------------------------------
# Clean & Prepare data
# -------------------------------------------------------------
# Classification mapping: p (poisonous) = 1, e (edible) = 0
df['target'] = (df['class'] == 'p').astype(int)

# Curated list of features to keep the UI manageable but the model strong
NEEDED_COLUMNS = [
    "cap-diameter", "stem-height", "cap-shape", "cap-surface", 
    "cap-color", "does-bruise-or-bleed", "gill-attachment", 
    "gill-spacing", "gill-color", "habitat", "season", "target"
]

df = df[NEEDED_COLUMNS]

X = df.drop("target", axis=1)
y = df["target"]

numeric_features = ["cap-diameter", "stem-height"]
categorical_features = [
    "cap-shape", "cap-surface", "cap-color", "does-bruise-or-bleed", 
    "gill-attachment", "gill-spacing", "gill-color", "habitat", "season"
]

# Ensure numeric coercion 
for col in numeric_features:
    X[col] = pd.to_numeric(X[col], errors="coerce")
    
# Treat missing strings safely
for col in categorical_features:
    X[col] = X[col].apply(lambda x: str(x) if pd.notnull(x) and str(x).strip() != '' else 'unknown')

numeric_transformer = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler()) 
])

categorical_transformer = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(handle_unknown="ignore")),
])

preprocessor = ColumnTransformer([
    ("num", numeric_transformer, numeric_features),
    ("cat", categorical_transformer, categorical_features),
])

model = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        random_state=42,
        n_jobs=-1,
    )),
])

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("Training Fungal Toxicity ML pipeline...")
model.fit(X_train, y_train)

predictions = model.predict(X_test)
probs = model.predict_proba(X_test)[:, 1]
acc = accuracy_score(y_test, predictions)
auc = roc_auc_score(y_test, probs)

print("\nModel Performance")
print("-" * 30)
print(f"Accuracy : {acc:.3f}")
print(f"ROC-AUC  : {auc:.3f}")

joblib.dump(model, os.path.join(MODEL_DIR, "fungi_model.pkl"))
print("\nModel saved as fungi_model.pkl")

# -------------------------------------------------------------
# Export metadata 
# -------------------------------------------------------------
categories = {}
for col in categorical_features:
    unique_vals = [str(x) for x in X[col].unique() if str(x).lower() != 'nan']
    categories[col] = sorted(unique_vals)

categories["cap_range"] = [float(X["cap-diameter"].min()), float(X["cap-diameter"].max())]
categories["stem_range"] = [float(X["stem-height"].min()), float(X["stem-height"].max())]

with open(os.path.join(MODEL_DIR, "categories.json"), "w") as f:
    json.dump(categories, f, indent=2)

# Feature importance mapped back to column names
feature_names = model.named_steps["preprocessor"].get_feature_names_out()
importances = model.named_steps["classifier"].feature_importances_

agg_importance = {col: 0.0 for col in X.columns}
for fname, imp in zip(feature_names, importances):
    clean_name = fname.replace("num__", "").replace("cat__", "")
    for col in X.columns:
        if clean_name.startswith(col):
            agg_importance[col] += float(imp)
            break

total = sum(agg_importance.values()) or 1.0
top_importance = dict(sorted({k: v / total for k, v in agg_importance.items()}.items(), key=lambda kv: kv[1], reverse=True)[:6])

with open(os.path.join(MODEL_DIR, "feature_importance.json"), "w") as f:
    json.dump(top_importance, f, indent=2)

# Stats for contextual comparisons (toxicity by habitat and season)
risk_by_habitat = df.groupby('habitat')['target'].mean().round(3).to_dict()
risk_by_season = df.groupby('season')['target'].mean().round(3).to_dict()

with open(os.path.join(MODEL_DIR, "toxicity_stats.json"), "w") as f:
    json.dump({
        "by_habitat": risk_by_habitat,
        "by_season": risk_by_season,
        "overall_risk": float(df["target"].mean()),
        "accuracy": round(float(acc), 3),
        "auc": round(float(auc), 3)
    }, f, indent=2)

print("Metadata exported: categories.json, feature_importance.json, toxicity_stats.json")