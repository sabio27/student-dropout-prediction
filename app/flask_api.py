"""
API Flask — Prédiction du risque d'abandon scolaire
Auteur : Sabio
Cours : Technologie de l'Intelligence Artificielle

Endpoints :
    GET  /              → page d'accueil (info API)
    GET  /health        → health check
    GET  /model-info    → métadonnées du modèle
    POST /predict       → prédiction (JSON)
"""

from pathlib import Path
import joblib
import pandas as pd
from flask import Flask, request, jsonify

# ─── Initialisation ───────────────────────────────────────────────────
app = Flask(__name__)

MODEL_PATH = Path(__file__).parent.parent / "models" / "best_model.pkl"
artifacts = joblib.load(MODEL_PATH)

model = artifacts['model']
scaler = artifacts['scaler']
feature_names = artifacts['feature_names']
model_name = artifacts['model_name']
metrics = artifacts['metrics']

# ─── Feature engineering (identique au notebook) ──────────────────────
def compute_features(payload: dict) -> pd.DataFrame:
    """Transforme le payload JSON en DataFrame prêt pour le modèle."""
    age = payload['age']
    gender = payload['gender']
    average_grade = payload['average_grade']
    absenteeism_rate = payload['absenteeism_rate']
    internet_access = payload['internet_access']
    study_time_hours = payload['study_time_hours']
    extra_activities = payload['extra_activities']

    # Features engineered
    epsilon = 1e-6
    presence_absence_ratio = (1 - absenteeism_rate) / (absenteeism_rate + epsilon)
    presence_absence_ratio = min(presence_absence_ratio, 20)

    global_score = (
        (average_grade / 20) * 0.5
        + (1 - absenteeism_rate) * 0.3
        + (study_time_hours / 5) * 0.2
    )

    input_dict = {
        'age': age,
        'average_grade': average_grade,
        'absenteeism_rate': absenteeism_rate,
        'study_time_hours': study_time_hours,
        'gender_Male': 1 if gender == 'Male' else 0,
        'internet_access_Yes': 1 if internet_access == 'Yes' else 0,
        'extra_activities_Yes': 1 if extra_activities == 'Yes' else 0,
        'presence_absence_ratio': presence_absence_ratio,
        'global_score': global_score,
    }

    return pd.DataFrame([input_dict])[feature_names]

# ─── Endpoints ────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "api": "Prédiction Abandon Scolaire",
        "author": "Sabio",
        "model": model_name,
        "endpoints": {
            "GET /": "Information API",
            "GET /health": "Health check",
            "GET /model-info": "Métadonnées du modèle",
            "POST /predict": "Prédiction (JSON)"
        },
        "example_payload": {
            "age": 19,
            "gender": "Male",
            "average_grade": 11.5,
            "absenteeism_rate": 0.25,
            "internet_access": "Yes",
            "study_time_hours": 2.0,
            "extra_activities": "No"
        }
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "model_loaded": True})


@app.route("/model-info", methods=["GET"])
def model_info():
    return jsonify({
        "model_name": model_name,
        "features": feature_names,
        "metrics": {k: round(v, 4) for k, v in metrics.items()}
    })


@app.route("/predict", methods=["POST"])
def predict():
    try:
        payload = request.get_json()
        if payload is None:
            return jsonify({"error": "JSON body required"}), 400

        # Validation des champs obligatoires
        required = ['age', 'gender', 'average_grade', 'absenteeism_rate',
                    'internet_access', 'study_time_hours', 'extra_activities']
        missing = [f for f in required if f not in payload]
        if missing:
            return jsonify({"error": f"Champs manquants : {missing}"}), 400

        # Préparation + prédiction
        input_df = compute_features(payload)
        input_scaled = scaler.transform(input_df)

        prediction = int(model.predict(input_scaled)[0])
        proba = model.predict_proba(input_scaled)[0]
        risk_proba = float(proba[1])

        # Niveau de risque
        if risk_proba < 0.3:
            level = "FAIBLE"
        elif risk_proba < 0.6:
            level = "MODÉRÉ"
        else:
            level = "ÉLEVÉ"

        return jsonify({
            "prediction": prediction,
            "prediction_label": "Risque d'abandon" if prediction == 1 else "Pas de risque",
            "risk_probability": round(risk_proba, 4),
            "risk_level": level,
            "global_score": round(float(input_df['global_score'].iloc[0]), 4),
            "presence_absence_ratio": round(float(input_df['presence_absence_ratio'].iloc[0]), 4)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Lancement ────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f" API Flask lancée — modèle : {model_name}")
    print(f"   Métriques : F1={metrics['f1_score']:.3f}, "
          f"Accuracy={metrics['accuracy']:.3f}")
    app.run(host="0.0.0.0", port=5000, debug=False)
