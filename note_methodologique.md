# Note méthodologique — Résidences Azur

Groupe : 4  ·  Classe : SQY  ·  Membres : Clément Bastien, Romain Liénard, Mohammed Adam Berkani

## 1. Problème et décision métier

Résidences Azur perd environ un séjour sur trois par annulation tardive. Le
modèle estime, **à l'enregistrement de la réservation**, la probabilité
d'annulation afin que l'équipe commerciale appelle les dossiers à risque.

Un appel coûte **6 €** et évite l'annulation **une fois sur trois** ; une
annulation évitée rapporte **~100 €**. L'appel est rentable si
`p × 100/3 > 6 €`, soit un **seuil économique de 0,18**, réglable dans
l'application.

**Métrique principale : l'AUPRC.** La classe positive est minoritaire (~33 %) :
l'accuracy serait trompeuse et la décision repose sur un seuil. L'AUPRC mesure
la qualité du tri des dossiers indépendamment du seuil.

## 2. Variables

**Fuites d'information écartées** (preuves chiffrées dans le notebook) :
`statut_dossier` prédit `annule` à 100 % (statut final) ; `date_statut` et
`jours_attente_confirmation` n'existent qu'après la décision ; et trois
variables en « zone grise » : `logement_attribue` (connu à l'arrivée seulement —
4,5 % d'annulations si différent de la demande), `nb_modifications` (vaut 0 à
l'enregistrement par définition), `nb_places_parking` (**0 % d'annulation** dès
qu'une place est demandée : renseigné après réservation).

Les retirer fait passer l'AUPRC de ~0,66 à **0,61** : cette baisse mesure le
gain illusoire que les fuites apportaient — un signe d'évaluation honnête.

Variables écartées car sans valeur : `id_reservation`, `id_entreprise` (94 %
vide), `code_promo` (12 codes, ~9 000 lignes chacun, même taux ~33 %),
`indice_affinite` (même moyenne dans les deux classes).

**Variables dérivées** (`build_features` de `features.py`) : `delai_jours`
(arrivée − réservation, borné [0, 731], facteur dominant), `mois_arrivee`,
`jour_semaine_arrivee`, `nuits_total`, `nb_personnes`, `avec_enfants`,
`via_agence`, `pays_groupe` (10 pays + « Autre »). `tarif_nuit` borné [0, 500].

## 3. Méthodes

Découpage **chronologique en trois jeux** : entraînement (60 % des arrivées les
plus anciennes), **validation** (20 % suivantes — choix des réglages et du
modèle), test (20 % les plus récentes, utilisé une seule fois).

| Modèle | AUPRC validation | AUPRC train | Temps |
|---|---|---|---|
| Baseline (taux moyen) | 0,260 | 0,221 | 0,2 s |
| Régression logistique | 0,580 | 0,589 | 0,4 s |
| Arbre prof. 3 / 5 / 8 / 12 | 0,430 → 0,562 → 0,510 | monte jusqu'à 0,785 | <0,5 s |
| Arbre illimité | 0,356 | **1,000** | 0,5 s |
| Forêt (min_leaf 50, réglé sur la validation) | **0,604** | 0,734 | 1,0 s |
| Gradient boosting (HGB) | 0,592 | 0,778 | 0,9 s |
| MLP (bonus, 64 neurones) | 0,581 | 0,786 | 26 s |

Lecture : l'arbre illimité mémorise (train 1,00, val 0,36). La forêt réglée et
le boosting dominent en validation, mais avec un écart train/val marqué ; la
logistique est proche et sans sur-apprentissage. **Modèle retenu : régression
logistique** — interprétable, robuste, et au test elle fait mieux (0,613 contre
0,602 pour la forêt). Le MLP n'apporte rien : données tabulaires, peu
d'interactions non linéaires exploitables, et 60× plus lent.

## 4. Résultats et évaluation

- **Dédoublonnage** : 28 204 lignes identiques hors identifiant supprimées ;
  nettoyage des 705 réservations à 0 nuit et 385 à 0 adulte.
- **Découpage chronologique** : le taux d'annulation varie dans le temps
  (22 % train / 26 % validation / 31 % test) — un split aléatoire mélangerait
  passé et futur, et ces taux différents rendent les AUPRC train/test non
  directement comparables.
- **Scores** : AUPRC test **0,613** (baseline 0,311), AUC 0,773.
- **Seuil** : la courbe de gain réel `y × 100/3 − 6` sur la validation donne un
  optimum vers 0,12 ; le seuil économique théorique 0,18 reste proche du
  plateau — on le conserve (≈ 40 % des dossiers appelés). Une courbe de
  calibration montre que les probabilités sont bien ordonnées.
- **Variables influentes** (permutation) : délai de réservation, garantie,
  historique d'annulations, canal de vente — cohérent avec l'EDA.

## 5. Application et tests

- `python app.py` : Gradio, 10 champs (variables influentes), autres variables
  aux valeurs par défaut, curseur de seuil lu dans `model_meta.json`, entrées
  validées (dates réelles, jour même accepté, champs vides refusés).
- `uvicorn api:api` : `POST /predict`, schéma Pydantic avec `Literal` et vraies
  dates → entrée invalide ou incohérente (arrivée avant réservation, 0 nuit) →
  **422** ; `/health` expose la version du modèle et le seuil.
- `pytest` : 11 tests — probabilité dans [0, 1], entrée invalide refusée,
  jour même accepté (200), date impossible / 0 nuit / champ manquant → 422.

## 6. Limites et veille

- Les taux d'annulation diffèrent entre train (22 %) et test (31 %) : surveiller
  la **dérive** et ré-entraîner périodiquement.
- `garantie = non remboursable` → 99 % d'annulations : variable légitime (choisie
  à la réservation) mais probablement artefact d'enregistrement des annulations
  tarifées — à vérifier avec l'exploitation.
- Variables en zone grise écartées (parking, modifications, logement attribué) :
  l'hypothèse « inconnu à la réservation » doit être confirmée par le métier.
- Coûts 6 € / 100 € / efficacité 1/3 = ordres de grandeur : recaler le seuil
  avec les vrais coûts.
- Équité : `pays_client` peut introduire un biais ; à auditer.
- Avec plus de temps : calibration des probabilités (Platt/isotonic), LightGBM,
  réglage plus fin du MLP.

## 7. Usage d'assistants de code

Le projet a été rédigé avec l'aide de Devin (assistant de code Cognition) pour
l'ensemble des fichiers (`features.py`, `train.py`, `app.py`, `api.py`,
`test_app.py`, `notebook.ipynb`, cette note), et relu/corrigé avec un second
assistant (revue des fuites de variables, protocole entraînement/validation/test,
validation Pydantic, tests). Le groupe a vérifié : les choix de variables (fuites
identifiées et chiffrées), l'échelle de méthodes, le tableau récapitulatif, le
fonctionnement de l'application et de l'API, et le passage des tests.
