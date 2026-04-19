
"""
Application Streamlit — Prédiction du risque d'abandon scolaire
Auteur : Sabio
Cours : Technologie de l'Intelligence Artificielle
"""

import streamlit as st
import numpy as np
import pandas as pd
import joblib
from pathlib import Path

# ─── Configuration de la page ─────────────────────────────────────────
st.set_page_config(
    page_title="Prédiction Abandon Scolaire",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Chargement du modèle ─────────────────────────────────────────────
@st.cache_resource
def load_model():
    model_path = Path(__file__).parent.parent / "models" / "best_model.pkl"
    return joblib.load(model_path)

try:
    artifacts = load_model()
    model = artifacts['model']
    scaler = artifacts['scaler']
    feature_names = artifacts['feature_names']
    model_name = artifacts['model_name']
    metrics = artifacts['metrics']
except Exception as e:
    st.error(f" Erreur de chargement du modèle : {e}")
    st.stop()

# ─── Sidebar ─────────────────────────────────────────────────────────
with st.sidebar:
    st.title(" À propos")
    st.markdown(f"""
    ### Modèle utilisé
    **{model_name}**
    
    ### Performances (test set)
    - Accuracy : **{metrics['accuracy']:.2%}**
    - Precision : **{metrics['precision']:.2%}**
    - Recall : **{metrics['recall']:.2%}**
    - F1-score : **{metrics['f1_score']:.2%}**
    
    ---
    ### Contexte
    Cet outil prédit si un étudiant présente un risque d'abandon scolaire,
    à partir de ses caractéristiques académiques et comportementales.
    
    ### Cours
    Technologie de l'Intelligence Artificielle
    
    ### Auteur
    Sabio
    """)

# ─── Titre principal ─────────────────────────────────────────────────
st.title(" Prédiction du Risque d'Abandon Scolaire")
st.markdown(
    "Renseignez les informations de l'étudiant ci-dessous pour estimer "
    "son risque d'abandon scolaire."
)
st.divider()

# ─── Formulaire ──────────────────────────────────────────────────────
with st.form("prediction_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(" Informations académiques")
        average_grade = st.slider(
            "Moyenne générale (/20)", 0.0, 20.0, 12.0, 0.1,
            help="Moyenne actuelle de l'étudiant sur 20"
        )
        absenteeism_rate = st.slider(
            "Taux d'absence (0 = jamais absent, 0.5 = 50% d'absences)",
            0.0, 0.5, 0.2, 0.01,
            help="Proportion de cours manqués"
        )
        study_time_hours = st.slider(
            "Temps d'étude journalier (heures)",
            0.0, 5.0, 2.0, 0.1,
            help="Moyenne d'heures étudiées par jour hors cours"
        )
    
    with col2:
        st.subheader(" Profil étudiant")
        age = st.number_input("Âge", 15, 24, 19)
        gender = st.radio("Genre", ["Female", "Male"], horizontal=True)
        internet_access = st.radio(
            "Accès Internet au domicile", ["Yes", "No"], horizontal=True
        )
        extra_activities = st.radio(
            "Activités extrascolaires", ["Yes", "No"], horizontal=True
        )
    
    st.divider()
    submitted = st.form_submit_button(
        " Prédire le risque", use_container_width=True, type="primary"
    )

# ─── Prédiction ──────────────────────────────────────────────────────
if submitted:
    # Feature engineering identique au notebook
    epsilon = 1e-6
    presence_absence_ratio = (1 - absenteeism_rate) / (absenteeism_rate + epsilon)
    presence_absence_ratio = min(presence_absence_ratio, 20)
    
    global_score = (
        (average_grade / 20) * 0.5 +
        (1 - absenteeism_rate) * 0.3 +
        (study_time_hours / 5) * 0.2
    )
    
    # Construction du vecteur de features dans l'ordre attendu par le modèle
    input_dict = {
        'age': age,
        'average_grade': average_grade,
        'absenteeism_rate': absenteeism_rate,
        'study_time_hours': study_time_hours,
        'gender_Male': 1 if gender == 'Male' else 0,
        'internet_access_Yes': 1 if internet_access == 'Yes' else 0,
        'extra_activities_Yes': 1 if extra_activities == 'Yes' else 0,
        'presence_absence_ratio': presence_absence_ratio,
        'global_score': global_score
    }
    
    # Réordonner selon feature_names du pkl
    input_df = pd.DataFrame([input_dict])[feature_names]
    
    # Normalisation avec le scaler entraîné
    input_scaled = scaler.transform(input_df)
    
    # Prédiction
    prediction = model.predict(input_scaled)[0]
    proba = model.predict_proba(input_scaled)[0]
    risk_proba = proba[1]  # proba classe 1 (abandon)
    
    # ─── Affichage des résultats ─────────────────────────────────────
    st.divider()
    st.header(" Résultat de la prédiction")
    
    # Détermination du niveau de risque
    if risk_proba < 0.3:
        level, color, emoji, msg = "FAIBLE", "#2ecc71", "Risque d'abandon faible"
    elif risk_proba < 0.6:
        level, color, emoji, msg = "MODÉRÉ", "#f39c12",  "Risque d'abandon modéré"
    else:
        level, color, emoji, msg = "ÉLEVÉ", "#e74c3c", "Risque d'abandon élevé"
    
    res_col1, res_col2, res_col3 = st.columns([1, 2, 1])
    with res_col2:
        st.markdown(
            f"<div style='background:{color}22;border-left:6px solid {color};"
            f"padding:20px;border-radius:8px;text-align:center;'>"
            f"<h2 style='margin:0;color:{color};'>{emoji} Risque {level}</h2>"
            f"<p style='font-size:18px;margin:10px 0;'>{msg}</p>"
            f"<h3 style='margin:0;color:{color};'>"
            f"Probabilité d'abandon : {risk_proba:.1%}</h3>"
            f"</div>",
            unsafe_allow_html=True
        )
    
    st.markdown("###  Détail probabiliste")
    st.progress(risk_proba, text=f"Probabilité d'abandon : {risk_proba:.1%}")
    
    met_col1, met_col2, met_col3 = st.columns(3)
    met_col1.metric("Score global calculé", f"{global_score:.3f}")
    met_col2.metric("Ratio présence/absence", f"{presence_absence_ratio:.2f}")
    met_col3.metric("Moyenne pondérée/20", f"{average_grade:.2f}")
    
    # Recommandations
    st.markdown("###  Recommandations")
    recos = []
    if average_grade < 10:
        recos.append(" **Soutien académique** : Mettre en place tutorat ou cours de rattrapage.")
    if absenteeism_rate > 0.30:
        recos.append(" **Absentéisme** : Identifier les causes (santé, personnel, motivation).")
    if study_time_hours < 1:
        recos.append(" **Temps d'étude** : Accompagner la mise en place d'une routine.")
    
    if level == "ÉLEVÉ":
        recos.append(" **Entretien urgent** avec un conseiller pédagogique recommandé.")
    elif level == "MODÉRÉ":
        recos.append(" **Suivi rapproché** : Entretien de motivation et check-in mensuel.")
    else:
        recos.append(" **Profil favorable** : Continuer l'accompagnement standard.")
    
    for reco in recos:
        st.markdown(f"- {reco}")

# ─── Pied de page ────────────────────────────────────────────────────
st.divider()
st.caption(
    "© 2026 Sabio — Projet Technologie IA | "
    "Modèle entraîné sur un dataset de 300 étudiants"
)