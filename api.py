"""API FastAPI : probabilité d'annulation d'une réservation.

Lancement : uvicorn api:api --reload   (documentation interactive sur /docs)

- POST /predict reçoit une réservation en JSON (schéma Pydantic validé : types,
  bornes, modalités autorisées) et renvoie la probabilité d'annulation ;
- une entrée invalide est rejetée avec le code 422 avant d'atteindre le modèle ;
- le pipeline est chargé une seule fois au démarrage du service.
"""
import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

import features  # noqa: F401  (nécessaire au dé-picklage de build_features)
from app import DEFAULTS, construire_ligne

SEUIL_DEFAUT = 0.18


class Reservation(BaseModel):
    """Réservation telle que saisie au moment de l'enregistrement."""

    site: str = Field(pattern="^(Urbaine|Littoral)$")
    date_reservation: str = Field(
        pattern=r"^\d{4}-\d{2}-\d{2}$", examples=["2023-01-15"])
    date_arrivee: str = Field(
        pattern=r"^\d{4}-\d{2}-\d{2}$", examples=["2023-06-01"])
    nuits_semaine: int = Field(ge=0, le=365)
    nuits_week_end: int = Field(ge=0, le=104)
    nb_adultes: int = Field(ge=1, le=20)
    garantie: str = Field(pattern="^(Aucune|Non remboursable|Remboursable)$")
    canal_vente: str = Field(
        pattern="^(Intermédiaire|Direct|Entreprise|Réseau de distribution|Non renseigné)$")
    client_fidele: int = Field(ge=0, le=1)
    annulations_passees: int = Field(ge=0, le=100)
    tarif_nuit: float = Field(ge=0, le=5000)


api = FastAPI(title="Résidences Azur — risque d'annulation")
modele = joblib.load("model.pkl")


@api.get("/health")
def health():
    return {"statut": "ok", "seuil_defaut": SEUIL_DEFAUT}


@api.post("/predict")
def predict(resa: Reservation):
    if resa.date_arrivee <= resa.date_reservation:
        # Incohérence métier : 422 comme une entrée mal formée.
        raise HTTPException(
            status_code=422,
            detail="date_arrivee doit être postérieure à date_reservation",
        )
    ligne = construire_ligne(
        resa.site, resa.date_reservation, resa.date_arrivee, resa.nuits_semaine,
        resa.nuits_week_end, resa.nb_adultes, resa.garantie, resa.canal_vente,
        resa.client_fidele, resa.annulations_passees, resa.tarif_nuit,
    )
    p = float(modele.predict_proba(ligne)[:, 1][0])
    return {
        "probabilite_annulation": p,
        "appeler": p >= SEUIL_DEFAUT,
        "seuil": SEUIL_DEFAUT,
    }
