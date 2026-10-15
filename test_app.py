"""Tests pytest : lancement avec `pytest` depuis ce dossier.

- un test de l'application : la fonction de prédiction renvoie une probabilité
  entre 0 et 1 et refuse une entrée incohérente ;
- un test de l'API : une réservation valide renvoie 200 et une probabilité ;
- un test de l'API : une réservation invalide renvoie 422 (avant le modèle).
"""
from fastapi.testclient import TestClient

import app
from api import api

RESERVATION_VALIDES = {
    "site": "Urbaine",
    "date_reservation": "2023-01-15",
    "date_arrivee": "2023-06-01",
    "nuits_semaine": 3,
    "nuits_week_end": 1,
    "nb_adultes": 2,
    "garantie": "Aucune",
    "canal_vente": "Intermédiaire",
    "client_fidele": 0,
    "annulations_passees": 0,
    "tarif_nuit": 110,
}

ARGS_APP = (
    "Urbaine", "2023-01-15", "2023-06-01", 3, 1, 2,
    "Aucune", "Intermédiaire", 0, 0, 110,
)


def test_app_probabilite_entre_0_et_1():
    p = app.probabilite_annulation(*ARGS_APP)
    assert 0.0 <= p <= 1.0


def test_app_entree_invalide():
    # Arrivée avant la réservation : refusé avec un message clair.
    sortie, _ = app.predire(
        0.18, "Urbaine", "2023-06-01", "2023-01-15", *ARGS_APP[3:]
    )
    assert "invalide" in sortie.lower()


def test_api_predict_valide():
    client = TestClient(api)
    r = client.post("/predict", json=RESERVATION_VALIDES)
    assert r.status_code == 200
    corps = r.json()
    assert 0.0 <= corps["probabilite_annulation"] <= 1.0
    assert isinstance(corps["appeler"], bool)


def test_api_predict_invalide_422():
    client = TestClient(api)
    invalide = dict(RESERVATION_VALIDES, nb_adultes=-3, garantie="???")
    r = client.post("/predict", json=invalide)
    assert r.status_code == 422
