# Note méthodologique — Résidences Azur

Groupe : 4  ·  Classe : ……  ·  Membres : Clément Bastien, Romain Liénard, Mohammed Adam Berkani

## 1. Problème et décision métier

Résidences Azur perd environ un séjour sur trois par annulation tardive. Le
modèle estime, **à l'enregistrement de la réservation**, la probabilité
d'annulation afin que l'équipe commerciale appelle les dossiers à risque.

Un appel coûte **6 €** et évite l'annulation **une fois sur trois** ; une
annulation évitée rapporte **~100 €**. L'appel est rentable si
`p × 100/3 > 6 €`, soit un **seuil économique de 0,18**, réglable dans
l'application.

**Métrique principale : l'AUPRC.** La classe positive est minoritaire (33 %) :
l'accuracy serait trompeuse et la décision repose sur un seuil. L'AUPRC mesure
la qualité du tri des dossiers indépendamment du seuil.

## 2. Variables

**Fuite d'information écartée.** `statut_dossier` prédit `annule` à 100 % et
`jours_attente_confirmation` n'existe qu'après l'enregistrement : les deux sont
exclus, ainsi que `date_statut`. Détail par variable dans `audit_variables.md`.

**Variables dérivées** (fonction `build_features` de `features.py`, partagée par
`train.py`, `app.py` et `api.py`) :

- `delai_jours` (arrivée − réservation, borné [0, 731]) : le facteur dominant,
  6 % d'annulations le jour même contre 64 % au-delà d'un an ;
- `mois_arrivee`, `jour_semaine_arrivee` : saisonnalité ;
- `nuits_total`, `nb_personnes` : taille du séjour ;
- `meme_logement` : demandé ≠ attribué ;
- `via_agence` : présence d'un `id_agence` (34,9 % vs 21,5 % d'annulations) ;
- `pays_groupe` : 10 pays principaux + « Autre ».

`tarif_nuit` est borné à [0, 500] (valeurs impossibles : −8 €, 6 372 €).

## 3. Méthodes

Même découpage chronologique (test = 20 % des arrivées les plus récentes) et
même métrique pour tous les paliers :

| Modèle | AUPRC train | AUPRC test | Temps (s) |
|---|---|---|---|
| Baseline (taux moyen) | 0,229 | 0,311 | 0,1 |
| Régression logistique sans dérivées | 0,583 | 0,606 | 0,7 |
| Régression logistique avec dérivées | 0,637 | **0,659** | 0,7 |
| Arbre profondeur 3 | 0,429 | 0,461 | 0,5 |
| Arbre profondeur 8 (CV) | 0,660 | 0,576 | 0,5 |
| Arbre illimité | 1,000 | 0,416 | 0,8 |
| Forêt aléatoire | 1,000 | 0,640 | 1,5 |
| Gradient boosting (HGB) | 0,791 | 0,655 | 0,9 |

Les variables dérivées apportent +0,05 d'AUPRC à la logistique. L'arbre
illimité et la forêt mémorisent l'entraînement (1,00) sans généraliser mieux —
sur-apprentissage visible. Boosting et logistique sont au coude à coude au test ;
on retient la **régression logistique** : performance égale, aucun
sur-apprentissage (train ≈ test) et coefficients interprétables.

## 4. Résultats et évaluation

- **Dédoublonnage** : 28 204 lignes identiques hors identifiant supprimées
  avant évaluation, sinon elles gonflent le score.
- **Découpage chronologique** sur `date_arrivee` (coupure 2023-05-01) : en
  production, le modèle prédit des réservations futures ; un découpage aléatoire
  surestimerait la performance.
- **Scores** : AUPRC test 0,659 (baseline 0,311), AUC 0,813,
  train 0,637 → pas de sur-apprentissage (confirmé par la courbe
  d'apprentissage qui converge).
- **Seuil 0,18** : déclenche ~7 900 appels sur 16 815 réservations de test,
  pour un gain espéré de ~83 000 €.
- **Variables influentes** (permutation) : délai de réservation, garantie,
  historique d'annulations, canal de vente, fidélité — cohérent avec l'EDA.

## 5. Application et tests

- `python app.py` : interface Gradio, 10 champs (les variables les plus
  influentes), autres variables aux valeurs par défaut, curseur de seuil,
  entrées validées.
- `uvicorn api:api` : `POST /predict` validé par un schéma Pydantic, entrée
  invalide → **422** avant d'atteindre le modèle ; `/health` pour le suivi.
- `pytest` : probabilité dans [0, 1], entrée incohérente refusée dans l'app,
  réservation valide → 200, invalide → 422.
- Le pipeline entier (ingénierie + préparation + modèle) est dans `model.pkl` ;
  `features.py` accompagne le modèle car la fonction `build_features` y est
  référencée par le pickle.

## 6. Limites et veille

- Le taux d'annulation du test (31 %) diffère de l'entraînement : surveiller la
  **dérive** (canaux de vente, politique de garantie) et ré-entraîner
  périodiquement.
- `garantie = non remboursable` → 99 % d'annulations : probablement un artefact
  de données (annulations tarifées) plutôt qu'un effet causal ; à vérifier avec
  l'exploitation avant d'y appuyer la politique d'appel.
- Le coût 6 € / gain 100 € / efficacité 1/3 sont des ordres de grandeur : le
  seuil doit être recalé avec les vrais coûts mesurés.
- Équité : `pays_client` peut introduire un biais de traitement ; à auditer.
- Avec plus de temps : réglage des hyperparamètres par CV, calibration des
  probabilités (Platt/isotonic), comparaison LightGBM et MLP.

## 7. Usage d'assistants de code

Le projet a été rédigé avec l'aide de Devin (assistant de code Cognition) pour
l'ensemble des fichiers : `features.py`, `train.py`, `app.py`, `api.py`,
`test_app.py`, `notebook.ipynb` et cette note. Le groupe a vérifié : les choix
de variables (fuite identifiée sur `statut_dossier`), les résultats de l'échelle
de méthodes, les valeurs du tableau récapitulatif, le fonctionnement de
l'application et de l'API, et le passage des tests.
