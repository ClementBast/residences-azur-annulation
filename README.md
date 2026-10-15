# Résidences Azur — prédiction d'annulation

Projet de groupe (IA / Machine Learning, IPSSI). Modèle qui estime, à
l'enregistrement d'une réservation, la **probabilité d'annulation**, avec une
application Gradio et une API FastAPI pour décider quels dossiers appeler.

## Installation

Python **3.11** recommandé.

```bash
pip install -r requirements.txt
```

## Utilisation

```bash
python train.py      # ré-entraîne le pipeline depuis data/reservations_azur.csv
                     # et écrit model.pkl + model_meta.json
python app.py        # interface Gradio sur http://localhost:7860
uvicorn api:api      # API FastAPI sur http://localhost:8000 (docs : /docs)
pytest               # 11 tests : app + API (valide → 200, invalide → 422)
jupyter notebook     # notebook.ipynb : démarche complète, exécuté
```

## Fichiers

| Fichier | Rôle |
|---|---|
| `features.py` | variables dérivées partagées par train/app/api (indispensable : `model.pkl` y fait référence) |
| `train.py` | entraîne et sauvegarde le pipeline entier |
| `app.py` / `api.py` | application Gradio / API FastAPI |
| `test_app.py` | tests pytest |
| `notebook.ipynb` | EDA, audit des fuites, échelle de méthodes, évaluation |
| `audit_variables.md` | une ligne par variable : disponible ? conservée ? pourquoi |
| `note_methodologique.md` | note de 2–3 pages |
| `soutenance.pptx` | support de soutenance (7 slides) |
| `data/` | jeu de données (nécessaire pour `train.py` et le notebook) |
