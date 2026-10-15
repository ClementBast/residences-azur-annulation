"""Entraîne le pipeline final et le sauvegarde dans model.pkl.

Usage : python train.py
        python train.py --data ../data/reservations_azur.csv

Protocole (justifié dans note_methodologique.md) :
  - dédoublonnage des lignes identiques (hors identifiant et cible) ;
  - découpage chronologique sur la date d'arrivée : les ~20 % les plus récentes
    forment le test, car en production le modèle prédit des réservations futures ;
  - un seul objet sauvegardé : FunctionTransformer(ingénierie) +
    ColumnTransformer(imputation + encodage) + LogisticRegression ;
    la régression logistique est retenue car elle égale le boosting au test
    sans sur-apprentissage (AUPRC train ≈ test) et reste interprétable ;
  - métrique principale : l'AUPRC (classe minoritaire et décision de seuil) ;
  - seuil économique : un appel coûte 6 € et évite l'annulation dans 1 cas sur 3,
    une annulation évitée vaut ~100 €. On appelle si
        p * (100 € / 3) > 6 €   <=>   p > 0,18.
"""
import argparse
import json
import time

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from features import FEATURES_CAT, FEATURES_NUM, build_features

DATA_PATH = "data/reservations_azur.csv"
TARGET = "annule"
DATE_SPLIT = "date_arrivee"
TEST_FRACTION = 0.2

# Seuil économique : 6 € / (100 € / 3) = 0,18.
SEUIL_DEFAUT = 0.18


def build_pipeline() -> Pipeline:
    """Renvoie l'objet complet (ingénierie + préparation + modèle)."""
    prep = ColumnTransformer(
        [
            (
                "num",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                FEATURES_NUM,
            ),
            (
                "cat",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                FEATURES_CAT,
            ),
        ]
    )
    return Pipeline(
        [
            ("features", FunctionTransformer(build_features, validate=False)),
            ("preparation", prep),
            ("modele", LogisticRegression(max_iter=1000)),
        ]
    )


def main(data_path: str) -> None:
    df = pd.read_csv(data_path, parse_dates=["date_reservation", "date_arrivee"])

    # Lignes identiques : même réservation dupliquée (hors id et cible) —
    # on n'en garde qu'une pour ne pas gonfler l'évaluation.
    cols_doublon = [c for c in df.columns if c not in ("id_reservation", TARGET)]
    df = df.drop_duplicates(subset=cols_doublon).reset_index(drop=True)

    y = df[TARGET]
    X = df.drop(columns=[TARGET])

    # Découpage chronologique : entraîner sur le passé, tester sur les arrivées
    # les plus récentes, comme en production.
    ordre = X[DATE_SPLIT].sort_values()
    date_coupure = ordre.quantile(1 - TEST_FRACTION)
    masque_test = X[DATE_SPLIT] >= date_coupure
    X_train, X_test = X[~masque_test], X[masque_test]
    y_train, y_test = y[~masque_test], y[masque_test]

    pipe = build_pipeline()
    debut = time.perf_counter()
    pipe.fit(X_train, y_train)
    temps_train = time.perf_counter() - debut

    proba = pipe.predict_proba(X_test)[:, 1]
    metriques = {
        "auprc_test": float(average_precision_score(y_test, proba)),
        "auc_test": float(roc_auc_score(y_test, proba)),
        "auprc_train": float(
            average_precision_score(y_train, pipe.predict_proba(X_train)[:, 1])
        ),
        "taux_annulation_test": float(y_test.mean()),
        "seuil_economique": SEUIL_DEFAUT,
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "date_coupure": str(date_coupure.date()),
        "temps_train_s": round(temps_train, 2),
    }
    for k, v in metriques.items():
        print(f"{k:>22} : {v}")

    joblib.dump(pipe, "model.pkl")
    with open("model_meta.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "modele": "LogisticRegression",
                "features_num": FEATURES_NUM,
                "features_cat": FEATURES_CAT,
                "cible": TARGET,
                "protocole": "dedoublonnage + decoupage chronologique sur date_arrivee",
                "versions": {
                    "sklearn": sklearn.__version__,
                    "pandas": pd.__version__,
                    "numpy": np.__version__,
                },
                **metriques,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print("model.pkl et model_meta.json ecrits.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=DATA_PATH)
    args = parser.parse_args()
    main(args.data)
