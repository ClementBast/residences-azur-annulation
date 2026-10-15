"""API FastAPI : probabilité d'annulation d'une réservation.

Lancement : uvicorn api:api --reload   (documentation interactive sur /docs)

- POST /predict reçoit une réservation en JSON (schéma Pydantic validé : types,
  bornes, modalités autorisées, vraies dates) et renvoie la probabilité
  d'annulation ; les mêmes champs que l'application Gradio ;
- une entrée invalide est rejetée avec le code 422 avant d'atteindre le modèle ;
- le pipeline est chargé une seule fois au démarrage du service ;
- le seuil et la version du modèle sont lus dans model_meta.json.
"""
import datetime
import json
from typing import Literal

import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

import features  # noqa: F401  (nécessaire au dé-picklage de build_features)
from app import construire_ligne

with open("model_meta.json", encoding="utf-8") as f:
    META = json.load(f)
SEUIL_DEFAUT = META["seuil_economique"]
VERSION_MODELE = META["version_modele"]


class Reservation(BaseModel):
    """Réservation telle que saisie au moment de l'enregistrement.

    Les champs date sont de vraies dates : une date impossible
    (ex. 2023-02-30) est refusée par Pydantic avec un 422.
    """

    site: Literal["Urbaine", "Littoral"]
    date_reservation: datetime.date
    date_arrivee: datetime.date
    nuits: int = Field(ge=1, le=365)
    nb_adultes: int = Field(ge=1, le=20)
    garantie: Literal["Aucune", "Non remboursable", "Remboursable"]
    canal_vente: Literal[
        "Intermédiaire", "Direct", "Entreprise",
        "Réseau de distribution", "Non renseigné",
    ]
    client_fidele: int = Field(ge=0, le=1)
    annulations_passees: int = Field(ge=0, le=100)
    tarif_nuit: float = Field(ge=0, le=5000)


api = FastAPI(title="Résidences Azur — risque d'annulation")
modele = joblib.load("model.pkl")


@api.get("/health")
def health():
    return {
        "statut": "ok",
        "version_modele": VERSION_MODELE,
        "seuil_defaut": SEUIL_DEFAUT,
    }


@api.post("/predict")
def predict(resa: Reservation, seuil: float | None = None):
    if resa.date_arrivee < resa.date_reservation:
        # Incohérence métier : 422 comme une entrée mal formée.
        raise HTTPException(
            status_code=422,
            detail="date_arrivee ne peut pas être antérieure à date_reservation",
        )
    seuil_utilise = SEUIL_DEFAUT if seuil is None else float(seuil)
    ligne = construire_ligne(
        resa.site, resa.date_reservation, resa.date_arrivee, resa.nuits,
        resa.nb_adultes, resa.garantie, resa.canal_vente, resa.client_fidele,
        resa.annulations_passees, resa.tarif_nuit,
    )
    p = float(modele.predict_proba(ligne)[:, 1][0])
    return {
        "probabilite_annulation": p,
        "appeler": p >= seuil_utilise,
        "seuil": seuil_utilise,
        "version_modele": VERSION_MODELE,
    }
