# Audit des variables — Résidences Azur

Une ligne par variable : disponible **au moment où la réservation est enregistrée** ? Conservée ? Pourquoi ?

| Variable | Disponible à la réservation ? | Conservée ? | Justification |
|---|---|---|---|
| `id_reservation` | oui | **non** | Identifiant technique, aucun pouvoir prédictif |
| `site` | oui | oui (cat.) | Les deux résidences n'ont pas le même profil de clientèle |
| `annule` | sans objet | **cible** | Variable à prédire |
| `date_reservation`, `date_arrivee` | oui | oui → **dérivées** | Brutes inexploitables ; donnent `delai_jours`, `mois_arrivee`, `jour_semaine_arrivee` |
| `nuits_week_end`, `nuits_semaine` | oui | oui → `nuits_total` | Longueur du séjour |
| `nb_adultes`, `nb_enfants`, `nb_bebes` | oui | oui → `nb_personnes` | Composition du séjour (3 valeurs manquantes sur `nb_enfants` → imputation médiane) |
| `formule` | oui | oui (cat.) | Formule de repas connue à la réservation |
| `pays_client` | oui | oui → `pays_groupe` | 474 valeurs manquantes + pays rares : regroupés en 10 principaux + « Autre » |
| `origine_commerciale` | oui | oui (cat.) | Origine de la réservation (Direct, Agence…) |
| `canal_vente` | oui | oui (cat.) | Canal de vente, très lié au risque (intermédiaire ≠ direct) |
| `client_fidele` | oui | oui | Historique de fidélité connu |
| `annulations_passees` | oui | oui | Comportement passé du client : très prédictif |
| `sejours_honores_passes` | oui | oui | Complète l'historique |
| `logement_demande`, `logement_attribue` | oui | oui → `meme_logement` | Un logement attribué différent de la demande mécontente le client |
| `nb_modifications` | oui | oui | Modifications du dossier visibles à l'enregistrement |
| `garantie` | oui | oui (cat.) | Type de garantie, facteur majeur (non remboursable → ~99 % d'annulations) |
| `id_agence` | oui | oui → `via_agence` | L'identifiant lui-même est anonymisé ; c'est sa **présence** qui compte (34,9 % vs 21,5 %) |
| `id_entreprise` | oui | **non** | Vide à 94 % : trop manquant pour être utile tel quel |
| `jours_attente_confirmation` | **non** | **non** | N'existe qu'après confirmation du dossier → fuite d'information |
| `profil_client` | oui | oui (cat.) | Individuel / contrat / groupe connu à la réservation |
| `tarif_nuit` | oui | oui (borné [0, 500]) | Prix connu ; valeurs impossibles corrigées (−8 €, 6 372 €) |
| `nb_places_parking`, `nb_demandes_speciales` | oui | oui | Demandes formulées à la réservation |
| `code_promo` | oui | **non** | Chaîne libre très rare par valeur ; le signal est capté par canal/origine |
| `indice_affinite` | oui | oui | Indice marketing déjà calculé, disponible |
| `statut_dossier` | **non** | **non** | **Fuite d'information** : prédit `annule` à 100 % (statut final) |
| `date_statut` | **non** | **non** | Date du statut final, postérieure à la décision |

## Variables dérivées créées (`features.py`)

| Variable dérivée | Construction | Pourquoi |
|---|---|---|
| `delai_jours` | `date_arrivee − date_reservation`, borné [0, 731] | Facteur dominant : ~6 % d'annulations le jour même, ~64 % au-delà d'un an |
| `mois_arrivee`, `jour_semaine_arrivee` | extraction des dates | Saisonnalité (été, week-ends) |
| `nuits_total` | `nuits_semaine + nuits_week_end` | Taille du séjour |
| `nb_personnes` | `adultes + enfants + bébés` | Taille du groupe |
| `meme_logement` | `demande == attribue` | Déception si logement différent |
| `via_agence` | `id_agence` non nul | Passage par intermédiaire |
| `pays_groupe` | 10 pays principaux + « Autre » | Évite des modalités à un seul exemple |
