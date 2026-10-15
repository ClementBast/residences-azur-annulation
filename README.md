# Squelette de projet

Fichiers du dossier :

| Fichier | Rôle |
|---|---|
| `cahier_des_charges.md` | cahier des charges du projet |
| `train.py` | **à écrire** : construire le pipeline final (préparation + modèle), l'évaluer et le sauvegarder dans `model.pkl` |
| `app.py` | application Gradio : **à implémenter par le groupe** (spécification en tête du fichier) |
| `api.py` | API FastAPI : **à implémenter par le groupe** (spécification en tête du fichier) |
| `test_app.py` | tests `pytest` : **à implémenter par le groupe** |
| `requirements.txt` | dépendances aux versions figées (à garder à jour) |
| `note_methodologique.md` | modèle de la note de 2 à 3 pages |

Le jeu de données du projet est `reservations_azur.csv`, dans le dossier `data/` à côté de ce dossier (chemin `../data/reservations_azur.csv`, valeur par défaut de `train.py`).

Pour l'application et l'API, appuyez-vous sur le TD 3 (`partie_3/17_td_deploiement`), le notebook `16_deploiement_modele` (partie 4) et les slides de déploiement.

## Pour votre projet

1. Écrire `train.py` : variables retenues, variables dérivées dans le pipeline, modèle final choisi dans le notebook (voir l'échelle de méthodes du cahier des charges).
2. Écrire `app.py` (Gradio), `api.py` (FastAPI) et `test_app.py`.
3. Vérifier dans un terminal neuf que `python app.py`, `uvicorn api:api` et `pytest` fonctionnent depuis le dossier rendu (avec `features.py` si vos variables dérivées sont des fonctions à vous).
4. Déposer l'archive `groupeN_CLASSE.zip` sur Teams avant 15h30 (liste des livrables : section 5 du cahier des charges).
