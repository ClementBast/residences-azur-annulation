"""Variables dérivées, partagées par train.py, app.py et api.py.

Le pipeline sauvegardé dans model.pkl contient un FunctionTransformer qui
référence build_features : ce fichier doit donc accompagner le modèle.

Variables exclues en amont (voir audit_variables.md) :
  - fuite d'information (inconnues à l'enregistrement de la réservation) :
    statut_dossier, date_statut, jours_attente_confirmation,
    logement_attribue (attribué à l'arrivée), nb_modifications (vaut 0 à
    l'enregistrement par définition), nb_places_parking (0 % d'annulation
    dès qu'une place est demandée : renseigné après réservation) ;
  - sans valeur : id_reservation (identifiant), id_entreprise (94 % vide),
    code_promo (même taux d'annulation que sans code), indice_affinite
    (même moyenne dans les deux classes).
"""
import pandas as pd

# 10 pays les plus fréquents dans l'entraînement ; les autres -> "Autre".
PAYS_PRINCIPAUX = ["FRA", "GBR", "PRT", "ESP", "DEU", "ITA", "IRL", "BEL", "BRA", "NLD"]

FEATURES_NUM = [
    "delai_jours",
    "mois_arrivee",
    "jour_semaine_arrivee",
    "nuits_total",
    "nb_personnes",
    "avec_enfants",
    "tarif_nuit",
    "annulations_passees",
    "sejours_honores_passes",
    "nb_demandes_speciales",
    "via_agence",
]

FEATURES_CAT = [
    "site",
    "formule",
    "canal_vente",
    "origine_commerciale",
    "garantie",
    "profil_client",
    "pays_groupe",
    "client_fidele",
]


def build_features(X: pd.DataFrame) -> pd.DataFrame:
    """Transforme les colonnes brutes du CSV en variables exploitables."""
    X = X.copy()

    date_resa = pd.to_datetime(X["date_reservation"])
    date_arr = pd.to_datetime(X["date_arrivee"])

    # Délai entre l'enregistrement et l'arrivée, borné à [0, 731] (2 ans).
    X["delai_jours"] = (date_arr - date_resa).dt.days.clip(0, 731)
    X["mois_arrivee"] = date_arr.dt.month
    X["jour_semaine_arrivee"] = date_arr.dt.dayofweek

    X["nuits_total"] = X["nuits_semaine"] + X["nuits_week_end"]
    X["avec_enfants"] = (
        (X["nb_enfants"].fillna(0) + X["nb_bebes"]) > 0
    ).astype(int)
    X["nb_personnes"] = X["nb_adultes"] + X["nb_enfants"].fillna(0) + X["nb_bebes"]

    # Tarifs impossibles observés dans les données (-8 €, 6 372 €).
    X["tarif_nuit"] = X["tarif_nuit"].clip(0, 500)

    X["via_agence"] = X["id_agence"].notna().astype(int)
    X["pays_groupe"] = X["pays_client"].where(
        X["pays_client"].isin(PAYS_PRINCIPAUX), "Autre"
    )

    return X[FEATURES_NUM + FEATURES_CAT]
