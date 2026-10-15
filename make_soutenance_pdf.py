"""Régénère le PDF de préparation à la soutenance avec les chiffres réels."""
from fpdf import FPDF


def clean(s):
    return (s.replace("–", "-").replace("—", "-").replace("€", " EUR")
             .replace("×", "x").replace("∈", "dans").replace("→", "->")
             .replace("«", '"').replace("»", '"').replace("’", "'")
             .replace("•", "-").replace("≈", "~").replace(" ", " "))


class Doc(FPDF):
    def h1(self, t):
        self.set_font("helvetica", "B", 20); self.set_text_color(0, 74, 143)
        self.cell(0, 12, clean(t), new_x="LMARGIN", new_y="NEXT")

    def h2(self, t):
        self.set_font("helvetica", "B", 14); self.set_text_color(0, 74, 143)
        self.cell(0, 9, clean(t), new_x="LMARGIN", new_y="NEXT")

    def h3(self, t):
        self.set_font("helvetica", "B", 11); self.set_text_color(0, 0, 0)
        self.cell(0, 7, clean(t), new_x="LMARGIN", new_y="NEXT")

    def p(self, t):
        self.set_font("helvetica", "", 10); self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5.5, clean(t)); self.ln(1)

    def say(self, t):
        self.set_font("helvetica", "I", 10); self.set_text_color(60, 60, 60)
        self.multi_cell(0, 5.5, clean(t)); self.ln(1)


pdf = Doc()
pdf.set_auto_page_break(True, 15)

# Page 1
pdf.add_page()
pdf.h1("Soutenance groupe 4 – Résidences Azur")
pdf.p("15 octobre 2026 · Clément Bastien, Mohammed Adam Berkani, Romain Lefevre")
pdf.h2("Mode d'emploi")
pdf.p("Ce document prépare les 15 minutes de soutenance : 10 minutes de présentation "
      "et démonstration, puis 5 minutes de questions où chaque membre doit répondre "
      "au moins une fois. Les chiffres viennent du notebook final (sans les fuites, "
      "avec un jeu de validation).")
pdf.p("Trois règles pour l'oral :")
pdf.p("1. Chaque choix se défend avec un chiffre : c'est ce que la grille valorise.\n"
      "2. Si on ne sait pas, on le dit, puis on explique comment on le vérifierait.\n"
      "3. Tout le monde doit pouvoir expliquer tout le code.")

pdf.h2("Script oral, slide par slide")
pdf.h3("Slide 1 – Problème et seuil économique")
pdf.say("« Un séjour sur trois est annulé, le logement reste vide. Notre modèle estime "
        "la probabilité d'annulation à l'enregistrement pour décider qui appeler. "
        "Un appel coûte 6 €, évite l'annulation une fois sur trois, et une annulation "
        "évitée rapporte ~100 € : appeler est rentable quand p dépasse 0,18. »")
pdf.h3("Slide 2 – Des données au protocole")
pdf.say("« 112 188 réservations. Premier constat : 28 204 lignes strictement identiques, "
        "surtout des réservations de groupe — si on les garde, la même ligne peut se "
        "retrouver dans l'entraînement et le test. On n'en garde qu'une, avant tout "
        "découpage. On retire aussi 705 réservations à 0 nuit et 385 à 0 adulte. »")
pdf.say("« Deuxième choix : découpage chronologique, pas au hasard — on apprend sur le "
        "passé pour prédire l'avenir. Le taux d'annulation monte : 22 % à "
        "l'entraînement, 26 % en validation, 31 % au test. Trois jeux : entraînement "
        "(60 %), validation (20 %, pour tous les choix), test (20 %, une seule fois). »")
pdf.h3("Slide 3 – Audit : les fuites, chiffrées")
pdf.say("« statut_dossier prédit la cible à 100 % : c'est le statut final. Trois "
        "variables en zone grise : une place de parking demandée → 0 % d'annulation "
        "(rempli à l'arrivée) ; un logement attribué différent de la demande → 4,5 % "
        "d'annulations contre 37 % (attribué à l'arrivée) ; nb_modifications vaut 0 à "
        "l'enregistrement. Les retirer fait passer l'AUPRC de 0,66 à 0,61 : la baisse "
        "mesure le gain illusoire des fuites. »")
pdf.h3("Slide 4 – Variables dérivées")
pdf.say("« Les dates brutes deviennent le délai de réservation (6 % d'annulations le "
        "jour même, 64 % au-delà d'un an), le mois et le jour d'arrivée, la taille du "
        "séjour, le passage par agence et le pays regroupé en 10 + Autre. Sans elles, "
        "la logistique tombe de 0,58 à 0,51 en validation. »")
pdf.h3("Slide 5 – Échelle de méthodes")
pdf.say("« Même découpage, même métrique, mesuré sur la validation. Baseline : 0,26. "
        "Logistique : 0,58. Arbre profondeur 3 : sous-apprentissage (0,43) ; profondeur "
        "8 choisie sur la validation (0,56) ; arbre illimité : 1,00 en train, 0,36 en "
        "validation — il mémorise. Forêt réglée min_samples_leaf=50 : 0,604, le "
        "meilleur score de validation : c'est notre modèle final. Boosting : 0,59. "
        "MLP en bonus : 0,58, 60 fois plus lent — sur des données tabulaires, les "
        "arbres restent meilleurs, comme vu en cours. »")
pdf.h3("Slide 6 – Seuil et gain")
pdf.say("« On trace le gain réel — vraie annulation × 100/3 € moins 6 € d'appel — selon "
        "le seuil. L'optimum est vers 0,12 (94 k€ au test, 74 % des dossiers appelés) ; "
        "le seuil économique 0,18 reste proche du plateau et plus prudent (88 k€, "
        "57 % d'appels). On garde 0,18 par défaut, réglable dans l'application. »")
pdf.h3("Slide 7 – Démo et limites")
pdf.say("« Démo : réservation lointaine par agence → probabilité haute, appeler ; "
        "réservation directe récente → probabilité basse ; on bouge le curseur : la "
        "décision change ; 0 adulte ou arrivée avant la réservation → message "
        "d'erreur ; /docs renvoie 422 sur une entrée invalide ; pytest passe. »")
pdf.say("« Limites : les annulations montent dans le temps (dérive à surveiller, PSI) ; "
        "la garantie non remboursable à 99 % d'annulations est à expliquer avec le "
        "métier ; le pays pèse lourd — zone grise à confirmer. »")

# Page questions
pdf.add_page()
pdf.h2("Questions probables du jury")
pdf.h3("Variables et fuites")
pdf.p("Comment avez-vous repéré les fuites ? — Pour chaque variable : la connaît-on à "
      "l'instant de la réservation ? Puis le taux d'annulation par valeur : 0 % ou "
      "100 % est suspect (parking : 0 % dès 1 place).")
pdf.p("Pourquoi le logement attribué est-il une fuite ? — Un client déçu pourrait "
      "annuler : on aurait alors plus d'annulations quand le logement diffère. C'est "
      "l'inverse (4,5 % contre 37 %) : le logement est attribué à l'arrivée, un client "
      "qui a annulé n'en reçoit jamais.")
pdf.p("Pourquoi garder le pays ? — Donné à la réservation normalement. Zone grise : "
      "s'il était rempli à l'arrivée, ce serait une fuite — à confirmer avec le métier.")
pdf.h3("Modèles et évaluation")
pdf.p("Pourquoi l'AUPRC ? — Toujours prédire « honoré » donne 67 % d'accuracy sans "
      "détecter une annulation. L'AUPRC mesure si les dossiers à risque sont en tête, "
      "indépendamment du seuil.")
pdf.p("Pourquoi un découpage dans le temps ? — En production on prédit l'avenir ; "
      "le taux d'annulation dérive (22 → 26 → 31 %). Un découpage au hasard "
      "surestimerait le score.")
pdf.p("La logistique fait 0,613 au test, mieux que votre forêt (0,602) : pourquoi ? — "
      "On a choisi sur la validation, où la forêt gagnait (0,604 contre 0,580). "
      "Changer de modèle à cause du test, ce serait utiliser le test pour choisir : "
      "tricher. L'écart au test est dans le bruit du changement de taux de base.")
pdf.p("Votre forêt : 0,71 en train, 0,60 en validation — elle sur-apprend ? — Un peu, "
      "mais une partie de l'écart vient du taux d'annulation différent entre les jeux "
      "(l'AUPRC dépend du taux de base). Le réglage min_samples_leaf=50 limite "
      "justement la mémorisation.")
pdf.h3("Application et code")
pdf.p("Pourquoi sauvegarder le pipeline entier ? — Le modèle seul ne sait pas lire les "
      "données brutes : le pipeline contient le calcul des variables, la préparation "
      "et le modèle.")
pdf.p("À quoi sert features.py ? — model.pkl ne stocke que le nom de build_features ; "
      "le fichier doit être livré et importé par l'app et l'API.")
pdf.p("Si on envoie 0 adulte à l'API ? — Le schéma Pydantic refuse avec un 422, avant "
      "le modèle. Une date impossible (2023-02-30) pareil, grâce aux champs date.")
pdf.p("Que testez-vous ? — Probabilité ∈ [0,1], entrée incohérente refusée, API : "
      "valide → 200, jour même → 200, date impossible / 0 nuit / champ manquant → 422.")
pdf.p("Déployer une nouvelle version ? — Ré-entraîner avec train.py, incrémenter "
      "version_modele dans model_meta.json ; /health l'expose.")

# Page chiffres clés
pdf.add_page()
pdf.h2("Chiffres clés à avoir en tête")
for l in [
    "Taux d'annulation : 33 % brut ; 22 % train, 26 % validation, 31 % test",
    "Découpage : 49 809 train / 16 485 val / 16 735 test (chronologique, date d'arrivée)",
    "Seuil économique : 6 € / (100 € × 1/3) = 0,18",
    "Fuites : parking 0 % dès 1 place ; logement différent 4,5 % vs 37 % ; statut 100 %",
    "Effet des fuites : AUPRC ~0,66 avec → 0,61 sans",
    "Variables dérivées : logistique 0,51 → 0,58 en validation",
    "Modèle retenu : forêt min_leaf=50 — val 0,604, test 0,602, AUC 0,784, ~1,5 s",
    "Sur-apprentissage : arbre illimité 1,00 train / 0,36 validation",
    "Gain au test : tout le monde 73 k€ ; seuil 0,18 → 88 k€ (9 507 appels, 57 %) ; "
    "seuil 0,12 → 94 k€ (12 384 appels, 74 %)",
    "MLP bonus : 0,581 en validation, 26 s (60× plus lent que la logistique)",
]:
    pdf.p("- " + l)

pdf.output("Soutenance groupe 4 – Résidences Azur.pdf")
print("PDF régénéré")
