# Audit des variables — Résidences Azur

Une ligne par variable : disponible **au moment où la réservation est enregistrée** ? Conservée ? Pourquoi ?

| Variable | Disponible à la réservation ? | Conservée ? | Justification |
|---|---|---|---|
| `id_reservation` | oui | **non** | Identifiant technique, aucun pouvoir prédictif |
| `site` | oui | oui (cat.) | Les deux résidences n'ont pas le même profil de clientèle |
| `annule` | sans objet | **cible** | Variable à prédire |
| `date_reservation`, `date_arrivee` | oui | oui → **dérivées** | Brutes inexploitables ; donnent `delai_jours`, `mois_arrivee`, `jour_semaine_arrivee` |
| `nuits_week_end`, `nuits_semaine` | oui | oui → `nuits_total` | Longueur du séjour |
| `nb_adultes`, `nb_enfants`, `nb_bebes` | oui | oui → `nb_personnes`, `avec_enfants` | Composition du séjour (3 valeurs manquantes sur `nb_enfants` → imputation médiane) |
| `formule` | oui | oui (cat.) | Formule de repas connue à la réservation |
| `pays_client` | oui | oui → `pays_groupe` | 474 valeurs manquantes + pays rares : regroupés en 10 principaux + « Autre » |
| `origine_commerciale` | oui | oui (cat.) | Origine de la réservation (la plus fréquente : « Agence en ligne ») |
| `canal_vente` | oui | oui (cat.) | Canal de vente, lié au risque (intermédiaire ≠ direct) |
| `client_fidele` | oui | oui | Fidélité connue à la réservation |
| `annulations_passees` | oui | oui | Comportement passé du client : très prédictif |
| `sejours_honores_passes` | oui | oui | Complète l'historique |
| `logement_demande` | oui | **non** | Sans `logement_attribue`, la variable seule ne dit rien |
| `logement_attribue` | **non** | **non** | Attribué à l'arrivée : logement différent → 4,5 % d'annulations vs 37 % sinon. Signal trop fort, connu après coup |
| `nb_modifications` | **non** | **non** | Vaut 0 à l'enregistrement par définition ; >0 → 13 % vs 0 → 37 % : mesure un historique postérieur |
| `garantie` | oui | oui (cat.) | « Non remboursable » ≈ 99 % d'annulations : variable **légitime** (choisie à la réservation) ; l'artefact probable est que les annulations tarifées y sont enregistrées — à discuter avec l'exploitation |
| `id_agence` | oui | oui → `via_agence` | L'identifiant est anonymisé ; sa **présence** compte (34,9 % vs 21,5 %) |
| `id_entreprise` | oui | **non** | Vide à 94 % : trop manquant pour être utile tel quel |
| `jours_attente_confirmation` | **non** | **non** | N'existe qu'après confirmation du dossier → fuite d'information |
| `profil_client` | oui | oui (cat.) | Individuel / contrat / groupe connu à la réservation |
| `tarif_nuit` | oui | oui (borné [0, 500]) | Prix connu ; valeurs impossibles corrigées (−8 €, 6 372 €) |
| `nb_places_parking` | **non** | **non** | Dès 1 place demandée : **0 % d'annulation** → rempli à l'arrivée, pas à la réservation |
| `nb_demandes_speciales` | oui | oui | Demandes formulées à la réservation |
| `code_promo` | oui | **non** | ~12 codes d'environ 9 000 lignes chacun, même taux d'annulation (31–35 %) : ne dit rien |
| `indice_affinite` | oui | **non** | Même moyenne dans les deux classes (0,498 vs 0,494), AUPRC inchangée sans elle : aucun pouvoir prédictif |
| `statut_dossier` | **non** | **non** | **Fuite d'information** : statut final, prédit `annule` à 100 % |
| `date_statut` | **non** | **non** | Date du statut final, postérieure à la décision |

## Variables dérivées créées (`features.py`)

| Variable dérivée | Construction | Pourquoi |
|---|---|---|
| `delai_jours` | `date_arrivee − date_reservation`, borné [0, 731] | Facteur dominant : ~6 % d'annulations le jour même, ~64 % au-delà d'un an |
| `mois_arrivee`, `jour_semaine_arrivee` | extraction des dates | Saisonnalité (été, week-ends) |
| `nuits_total` | `nuits_semaine + nuits_week_end` | Taille du séjour |
| `nb_personnes` | `adultes + enfants + bébés` | Taille du groupe |
| `avec_enfants` | `enfants + bébés > 0` | Les familles annulent différemment |
| `via_agence` | `id_agence` non nul | Passage par intermédiaire |
| `pays_groupe` | 10 pays principaux + « Autre » | Évite des modalités à un seul exemple |

## Sens des valeurs manquantes

- `id_agence` vide = réservation **sans agence** (information, pas un trou) → `via_agence`
- `id_entreprise` vide = pas un contrat entreprise (94 % des lignes)
- `nb_enfants` (3 valeurs) : imputation médiane = 0
- `pays_client` (474 valeurs) : regroupé en « Autre »
