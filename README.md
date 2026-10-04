# Prediction  du risque d'abandon scolaire

Mini-projet de Machine Learning : Classification binaire predisant la reussite scolaire

## Structure du projet
Techno_IA_Proj/
├── data/
│   ├── raw/              # Données brutes
│   └── processed/        # Données nettoyées
├── notebooks/            # Jupyter notebooks d'analyse
├── src/                  # Code Python modulaire
├── models/               # Modèles entraînés (.pkl)
├── app/                  # Application Streamlit
├── reports/              # Rapport et figures
│   └── figures/
├── requirements.txt      # Dépendances Python
└── README.md

## Installation

```bash
python -m venv venv
source venv/Scripts/activate   # Git Bash / Linux / Mac
pip install -r requirements.txt
```

## Lancer le notebook

```bash
jupyter notebook
```

## Lancer la démo Streamlit

```bash
streamlit run app/streamlit_app.py
```

## Algorithmes testés

- Logistic Regression
- Random Forest
- Support Vector Machine

