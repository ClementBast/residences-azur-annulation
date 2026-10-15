"""Application Gradio : estimer la probabilité d'annulation d'une réservation.

Lancement : python app.py

- 10 champs de saisie (les variables les plus influentes) ; les autres prennent
  une valeur par défaut (modalité la plus fréquente / médiane de l'entraînement),
  fixée dans DEFAULTS ci-dessous ;
- sortie : probabilité d'annulation + recommandation « appeler / ne pas appeler » ;
- un curseur règle le seuil de décision (défaut : seuil économique 0,18) ;
- les entrées sont validées (dates cohérentes, bornes numériques) ;
- le pipeline sauvegardé (model.pkl) contient la fonction build_features de
  features.py : l'import de features est donc indispensable au chargement.
"""
import joblib
import pandas as pd

import features  # noqa: F401  (nécessaire au dé-picklage de build_features)

MODEL_PATH = "model.pkl"
SEUIL_DEFAUT = 0.18  # seuil économique : 6 € / (100 € / 3)

# Valeurs par défaut (modalité la plus fréquente ou médiane du jeu d'entraînement).
DEFAULTS = {
    "id_reservation": "WEB-000",
    "nb_enfants": 0.0,
    "nb_bebes": 0,
    "formule": "Petit-déjeuner",
    "pays_client": "FRA",
    "origine_commerciale": "Direct",
    "sejours_honores_passes": 0,
    "logement_demande": "L10",
    "logement_attribue": "L10",
    "nb_modifications": 0,
    "id_agence": None,
    "id_entreprise": None,
    "jours_attente_confirmation": 0,
    "profil_client": "Individuel",
    "nb_places_parking": 0,
    "nb_demandes_speciales": 0,
    "code_promo": "",
    "indice_affinite": 0.5,
    "statut_dossier": "Séjour effectué",
    "date_statut": "2023-01-01",
}

_MODELE = None


def charger_modele():
    """Charge le pipeline une seule fois (au premier appel)."""
    global _MODELE
    if _MODELE is None:
        _MODELE = joblib.load(MODEL_PATH)
    return _MODELE


def construire_ligne(site, date_reservation, date_arrivee, nuits_semaine,
                     nuits_week_end, nb_adultes, garantie, canal_vente,
                     client_fidele, annulations_passees, tarif_nuit):
    """Assemble les champs saisis + les valeurs par défaut en une ligne CSV."""
    ligne = dict(DEFAULTS)
    ligne.update(
        site=site,
        date_reservation=str(date_reservation)[:10],
        date_arrivee=str(date_arrivee)[:10],
        nuits_semaine=int(nuits_semaine),
        nuits_week_end=int(nuits_week_end),
        nb_adultes=int(nb_adultes),
        garantie=garantie,
        canal_vente=canal_vente,
        client_fidele=int(client_fidele),
        annulations_passees=int(annulations_passees),
        tarif_nuit=float(tarif_nuit),
    )
    return pd.DataFrame([ligne])


def probabilite_annulation(site, date_reservation, date_arrivee, nuits_semaine,
                           nuits_week_end, nb_adultes, garantie, canal_vente,
                           client_fidele, annulations_passees, tarif_nuit):
    """Renvoie la probabilité d'annulation entre 0 et 1 (utilisée par les tests)."""
    ligne = construire_ligne(
        site, date_reservation, date_arrivee, nuits_semaine, nuits_week_end,
        nb_adultes, garantie, canal_vente, client_fidele, annulations_passees,
        tarif_nuit,
    )
    return float(charger_modele().predict_proba(ligne)[:, 1][0])


def predire(seuil, site, date_reservation, date_arrivee, nuits_semaine,
            nuits_week_end, nb_adultes, garantie, canal_vente, client_fidele,
            annulations_passees, tarif_nuit):
    """Point d'entrée de l'interface : valide les entrées, prédit, recommande."""
    try:
        if nb_adultes < 1:
            raise ValueError("Il faut au moins un adulte.")
        if nuits_semaine + nuits_week_end < 1:
            raise ValueError("Le séjour doit durer au moins une nuit.")
        if tarif_nuit < 0:
            raise ValueError("Le tarif ne peut pas être négatif.")
        if str(date_arrivee)[:10] <= str(date_reservation)[:10]:
            raise ValueError("L'arrivée doit être postérieure à la réservation.")
    except ValueError as e:
        return f"Entrée invalide : {e}", 0.0

    p = probabilite_annulation(
        site, date_reservation, date_arrivee, nuits_semaine, nuits_week_end,
        nb_adultes, garantie, canal_vente, client_fidele, annulations_passees,
        tarif_nuit,
    )
    reco = "APPELER le client" if p >= seuil else "Ne pas appeler"
    detail = (
        f"{reco} — probabilité d'annulation {p:.1%} (seuil {seuil:.0%}).\n"
        f"Coût de l'appel : 6 € ; gain espéré : {p * 100 / 3:.2f} € "
        f"(annulation évitée 1 fois sur 3, valeur ~100 €)."
    )
    return detail, p


def lancer():
    import gradio as gr

    with gr.Blocks(title="Résidences Azur — risque d'annulation") as demo:
        gr.Markdown("# Risque d'annulation — Résidences Azur")
        seuil = gr.Slider(
            0.05, 0.9, value=SEUIL_DEFAUT, step=0.01,
            label="Seuil de décision (appeler si probabilité ≥ seuil)",
        )
        with gr.Row():
            site = gr.Dropdown(["Urbaine", "Littoral"], value="Urbaine", label="Site")
            date_reservation = gr.Textbox(value="2023-01-15", label="Date de réservation")
            date_arrivee = gr.Textbox(value="2023-06-01", label="Date d'arrivée")
        with gr.Row():
            nuits_semaine = gr.Number(value=3, minimum=0, label="Nuits en semaine")
            nuits_week_end = gr.Number(value=1, minimum=0, label="Nuits de week-end")
            nb_adultes = gr.Number(value=2, minimum=1, label="Adultes")
        with gr.Row():
            garantie = gr.Dropdown(
                ["Aucune", "Non remboursable", "Remboursable"],
                value="Aucune", label="Garantie",
            )
            canal_vente = gr.Dropdown(
                ["Intermédiaire", "Direct", "Entreprise", "Réseau de distribution"],
                value="Intermédiaire", label="Canal de vente",
            )
            client_fidele = gr.Radio([0, 1], value=0, label="Client fidèle")
        with gr.Row():
            annulations_passees = gr.Number(
                value=0, minimum=0, label="Annulations passées")
            tarif_nuit = gr.Number(value=110, minimum=0, label="Tarif par nuit (€)")
        sortie = gr.Textbox(label="Recommandation")
        proba = gr.Number(label="Probabilité d'annulation")
        bouton = gr.Button("Évaluer", variant="primary")
        bouton.click(
            predire,
            [seuil, site, date_reservation, date_arrivee, nuits_semaine,
             nuits_week_end, nb_adultes, garantie, canal_vente, client_fidele,
             annulations_passees, tarif_nuit],
            [sortie, proba],
        )
    demo.launch()


if __name__ == "__main__":
    lancer()
