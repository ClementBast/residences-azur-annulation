"""Tests pytest : lancement avec `pytest` depuis ce dossier.

Application :
- la prédiction renvoie une probabilité entre 0 et 1 ;
- une entrée incohérente est refusée avec un message clair.

API :
- réservation valide → 200 et une probabilité ;
- réservation le jour même → 200 (acceptée) ;
- schéma invalide → 422 ; date impossible → 422 ; 0 nuit → 422 ;
  champ manquant → 422 ; arrivée avant réservation → 422.
"""
from fastapi.testclient import TestClient

import app
from api import api

RESERVATION_VALIDE = {
    "site": "Urbaine",
    "date_reservation": "2023-01-15",
    "date_arrivee": "2023-06-01",
    "nuits": 4,
    "nb_adultes": 2,
    "garantie": "Aucune",
    "canal_vente": "Intermédiaire",
    "client_fidele": 0,
    "annulations_passees": 0,
    "tarif_nuit": 110,
}

ARGS_APP = (
    "Urbaine", "2023-01-15", "2023-06-01", 4, 2,
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


def test_app_date_impossible():
    # 30 février n'existe pas : refusé, pas de plantage.
    sortie, _ = app.predire(
        0.18, "Urbaine", "2023-02-30", "2023-06-01", *ARGS_APP[3:]
    )
    assert "invalide" in sortie.lower()


def test_app_champ_vide():
    sortie, _ = app.predire(
        0.18, "Urbaine", "2023-01-15", "2023-06-01", None, 2,
        "Aucune", "Intermédiaire", 0, 0, 110,
    )
    assert "invalide" in sortie.lower()


def test_api_predict_valide():
    client = TestClient(api)
    r = client.post("/predict", json=RESERVATION_VALIDE)
    assert r.status_code == 200
    corps = r.json()
    assert 0.0 <= corps["probabilite_annulation"] <= 1.0
    assert isinstance(corps["appeler"], bool)
    assert corps["version_modele"]


def test_api_jour_meme_accepte():
    client = TestClient(api)
    meme_jour = dict(RESERVATION_VALIDE, date_arrivee="2023-01-15")
    r = client.post("/predict", json=meme_jour)
    assert r.status_code == 200


def test_api_date_impossible_422():
    client = TestClient(api)
    invalide = dict(RESERVATION_VALIDE, date_arrivee="2023-02-30")
    r = client.post("/predict", json=invalide)
    assert r.status_code == 422


def test_api_zero_nuit_422():
    client = TestClient(api)
    invalide = dict(RESERVATION_VALIDE, nuits=0)
    r = client.post("/predict", json=invalide)
    assert r.status_code == 422


def test_api_champ_manquant_422():
    client = TestClient(api)
    incomplet = {k: v for k, v in RESERVATION_VALIDE.items() if k != "garantie"}
    r = client.post("/predict", json=incomplet)
    assert r.status_code == 422


def test_api_arrivee_avant_resa_422():
    client = TestClient(api)
    invalide = dict(
        RESERVATION_VALIDE,
        date_reservation="2023-06-01", date_arrivee="2023-01-15",
    )
    r = client.post("/predict", json=invalide)
    assert r.status_code == 422


def test_api_schema_invalide_422():
    client = TestClient(api)
    invalide = dict(RESERVATION_VALIDE, nb_adultes=-3, garantie="???")
    r = client.post("/predict", json=invalide)
    assert r.status_code == 422
