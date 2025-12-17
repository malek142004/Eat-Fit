from fastapi import FastAPI
import joblib
import numpy as np

model = joblib.load("no_show_model.joblib")
scaler = joblib.load("scaler.joblib")

app = FastAPI(title="No-Show Prediction API")

@app.get("/")
def root():
    return {"status": "API is running"}

@app.post("/predict")
def predict(features: list):
    X = np.array(features).reshape(1, -1)
    X_scaled = scaler.transform(X)

    proba = model.predict_proba(X_scaled)[0][1]

    if proba >= 0.7:
        action = "SMS + Email + Alternative Slot"
    elif proba >= 0.4:
        action = "Send SMS reminder"
    else:
        action = "No action"

    return {
        "proba_no_show": round(float(proba), 2),
        "action": action
    }
