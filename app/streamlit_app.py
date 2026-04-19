
"""
Application Streamlit — Prédiction du risque d'abandon scolaire
Auteur : Koffi Koffi Ambroise
Cours : Technologie de l'Intelligence Artificielle
"""

import streamlit as st
import pandas as pd
import joblib
from pathlib import Path

# ─── Configuration ────────────────────────────────────────────────
st.set_page_config(
    page_title="Prédiction Abandon Scolaire",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS pour compacter
st.markdown("""
    <style>
    .block-container {padding-top: 1.5rem; padding-bottom: 1rem;}
    h1 {margin-top: 0; padding-top: 0; font-size: 1.8rem !important;}
    .stSlider {padding-bottom: 0.2rem;}
    .result-box {
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 10px;
    }
    .placeholder-box {
        padding: 50px 20px;
        border: 2px dashed #bdc3c7;
        border-radius: 10px;
        text-align: center;
        color: #7f8c8d;
    }
    </style>
""", unsafe_allow_html=True)

# ─── Chargement du modèle ────────────────────────────────────────
@st.cache_resource
def load_model():
    model_path = Path(__file__).parent.parent / "models" / "best_model.pkl"
    return joblib.load(model_path)

artifacts = load_model()
model = artifacts['model']
scaler = artifacts['scaler']
feature_names = artifacts['feature_names']
model_name = artifacts['model_name']
metrics = artifacts['metrics']

# ─── Sidebar (collapsed par défaut) ──────────────────────────────
with st.sidebar:
    st.subheader("Modèle")
    st.write(f"**{model_name}**")
    st.metric("Accuracy", f"{metrics['accuracy']:.1%}")
    st.metric("F1-score", f"{metrics['f1_score']:.1%}")
    st.metric("Precision", f"{metrics['precision']:.1%}")
    st.metric("Recall", f"{metrics['recall']:.1%}")
    st.caption("Auteur : Koffi Koffi Ambroise")

# ─── Titre compact ───────────────────────────────────────────────
st.markdown("### Prédiction du Risque d'Abandon Scolaire")

# ─── Deux colonnes : Formulaire | Résultat ───────────────────────
col_form, col_result = st.columns([5, 4], gap="medium")

with col_form:
    with st.form("prediction_form"):
        st.markdown("**Informations académiques**")
        c1, c2 = st.columns(2)
        with c1:
            average_grade = st.slider("Moyenne /20", 0.0, 20.0, 12.0, 0.1)
            absenteeism_rate = st.slider("Taux absence", 0.0, 0.5, 0.2, 0.01)
        with c2:
            study_time_hours = st.slider("Étude (h/j)", 0.0, 5.0, 2.0, 0.1)
            age = st.number_input("Âge", 15, 24, 19)

        st.markdown("**Profil**")
        c3, c4, c5 = st.columns(3)
        with c3:
            gender = st.selectbox("Genre", ["Feminin", "Masculin"])
        with c4:
            internet_access = st.selectbox("Internet", ["Oui", "Non"])
        with c5:
            extra_activities = st.selectbox("Activités", ["Oui", "Non"])

        submitted = st.form_submit_button(
            "Prédire le risque", use_container_width=True, type="primary"
        )

with col_result:
    if not submitted:
        st.markdown(
            "<div class='placeholder-box'>"
            "<h4>Résultat de la prédiction</h4>"
            "<p>Remplissez le formulaire et cliquez sur<br><b>Prédire le risque</b></p>"
            "</div>",
            unsafe_allow_html=True
        )
    else:
        # Feature engineering
        epsilon = 1e-6
        presence_absence_ratio = (1 - absenteeism_rate) / (absenteeism_rate + epsilon)
        presence_absence_ratio = min(presence_absence_ratio, 20)
        global_score = (
            (average_grade / 20) * 0.5
            + (1 - absenteeism_rate) * 0.3
            + (study_time_hours / 5) * 0.2
        )

        # Construction du vecteur
        input_dict = {
            'age': age,
            'average_grade': average_grade,
            'absenteeism_rate': absenteeism_rate,
            'study_time_hours': study_time_hours,
            'gender_Male': 1 if gender == 'Masculin' else 0,
            'internet_access_Yes': 1 if internet_access == 'Oui' else 0,
            'extra_activities_Yes': 1 if extra_activities == 'Oui' else 0,
            'presence_absence_ratio': presence_absence_ratio,
            'global_score': global_score,
        }
        input_df = pd.DataFrame([input_dict])[feature_names]
        input_scaled = scaler.transform(input_df)
        risk_proba = float(model.predict_proba(input_scaled)[0][1])

        # Niveau de risque
        if risk_proba < 0.3:
            level, color, mark = "FAIBLE", "#2ecc71", "[OK]"
        elif risk_proba < 0.6:
            level, color, mark = "MODERE", "#f39c12", "[!]"
        else:
            level, color, mark = "ELEVE", "#e74c3c", "[!!]"

        # Box résultat
        st.markdown(
            f"<div class='result-box' style='background:{color}22;"
            f"border-left:6px solid {color};'>"
            f"<h3 style='margin:0;color:{color};'>{mark} Risque {level}</h3>"
            f"<h2 style='margin:8px 0 0 0;color:{color};'>{risk_proba:.1%}</h2>"
            f"<small>probabilité d'abandon</small>"
            f"</div>",
            unsafe_allow_html=True
        )

        st.progress(risk_proba)

        # Métriques compactes
        m1, m2 = st.columns(2)
        m1.metric("Score global", f"{global_score:.2f}")
        m2.metric("Ratio P/A", f"{presence_absence_ratio:.1f}")

        # Recommandations condensées
        st.markdown("**Recommandations**")
        recos = []
        if average_grade < 10:
            recos.append("Soutien académique (tutorat)")
        if absenteeism_rate > 0.30:
            recos.append("Suivi absentéisme")
        if study_time_hours < 1:
            recos.append("Accompagnement temps d'étude")
        if level == "ELEVE":
            recos.append("Entretien urgent conseiller pédagogique")
        elif level == "MODERE":
            recos.append("Suivi rapproché mensuel")
        else:
            recos.append("Profil favorable, accompagnement standard")

        for r in recos:
            st.markdown(f"- {r}")