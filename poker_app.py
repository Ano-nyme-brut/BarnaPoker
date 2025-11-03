import streamlit as st
import random
from deuces import Card, Evaluator, Deck
from itertools import product
import os
from typing import List

# --- Configuration de la Page ---
st.set_page_config(page_title="BarnaPoker", page_icon="🃏", layout="centered")

# -------------------------------------------------------------------
# ⚠️ ACTION REQUISE : Mettez à jour ces deux lignes ! ⚠️
VOTRE_NOM_UTILISATEUR_GITHUB = "Ano-nyme-brut"
VOTRE_NOM_DE_DEPOT_GITHUB = "BarnaPoker" 
# -------------------------------------------------------------------

# Construction du chemin de base vers vos images sur GitHub
BASE_IMAGE_URL = f"https://raw.githubusercontent.com/{VOTRE_NOM_UTILISATEUR_GITHUB}/{VOTRE_NOM_DE_DEPOT_GITHUB}/main/images/"


# --- Configuration de la Simulation ---
NB_ADVERSAIRES = 1
NB_SIMULATIONS = 10000
evaluator = Evaluator()

# --- Dictionnaires de Traduction et Tri ---
VALEURS_TRADUCTION = {
    '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', '8': '8', '9': '9',
    'dix': 'T', 't': 'T', 'valet': 'J', 'v': 'J', 'dame': 'Q', 'd': 'Q', 'roi': 'K', 'r': 'K', 'as': 'A', 'a': 'A'
}
COULEURS_TRADUCTION = {
    'cœur': 'h', 'coeur': 'h', 'carreau': 'd', 'pique': 's', 'trèfle': 'c', 'trefle': 'c'
}
ABREVIATIONS_COULEURS = {'h': 'Cœur', 'd': 'Carreau', 'c': 'Trèfle', 's': 'Pique'}

# Dictionnaire pour le tri : A, K, Q, J, T, 9, 8, 7, 6, 5, 4, 3, 2 (décroissant)
ORDRE_VALEUR = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10, '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2}
ORDRE_COULEUR = {'s': 4, 'h': 3, 'd': 2, 'c': 1} # Ordre arbitraire pour le visuel


# --- Génération et Tri des Cartes ---
VALEURS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
COULEURS = ['h', 'd', 'c', 's']
CARTES_ABREGEES = [v + c for v, c in product(VALEURS, COULEURS)]

def get_carte_fr(abr):
    """Convertit l'abréviation interne (ex: 'As') en format français (ex: 'As Pique')."""
    valeur = abr[0]
    couleur_abr = abr[1]
    valeur_fr = next((k for k, v in VALEURS_TRADUCTION.items() if v == valeur), valeur).capitalize()
    couleur_fr = ABREVIATIONS_COULEURS[couleur_abr]
    return f"{valeur_fr} {couleur_fr}"

def sort_cartes(carte_fr):
    """Fonction de tri pour ranger les cartes par Couleur puis par Valeur."""
    parties = carte_fr.lower().split()
    valeur_abr = VALEURS_TRADUCTION.get(parties[0]) or VALEURS_TRADUCTION.get(parties[0][0])
    couleur_abr = COULEURS_TRADUCTION.get(parties[-1])
    
    # Priorité 1: Couleur (Trèfle, Carreau, Cœur, Pique)
    ordre_couleur = ORDRE_COULEUR.get(couleur_abr, 0)
    # Priorité 2: Valeur (As, Roi, Dame...)
    ordre_valeur = ORDRE_VALEUR.get(valeur_abr, 0)
    
    # Tri par Couleur (ASC), puis par Valeur (DESC)
    return (ordre_couleur, -ordre_valeur) 

# Liste des 52 cartes en français, triée par couleur et valeur.
CARTES_DISPONIBLES_FR = sorted([get_carte_fr(abr) for abr in CARTES_ABREGEES], key=sort_cartes)


# --- Fonctions de Logique ---

def parse_card_to_int(card_str_fr):
    """Convertit 'As Coeur' en l'entier de la bibliothèque deuces."""
    parties = card_str_fr.lower().replace('-', ' ').split()
    if len(parties) < 2: raise ValueError(f"Format invalide : '{card_str_fr}'.")
    valeur_input = parties[0]
    couleur_input = parties[-1] 
    valeur_abr = VALEURS_TRADUCTION.get(valeur_input) or VALEURS_TRADUCTION.get(valeur_input[0])
    couleur_abr = COULEURS_TRADUCTION.get(couleur_input)
    if not valeur_abr or not couleur_abr:
        raise ValueError(f"Carte non reconnue : '{card_str_fr}'")
    return Card.new(valeur_abr + couleur_abr)

def parse_card_to_filename(card_str_fr):
    """Convertit 'As Coeur' en nom de fichier 'AS.png'."""
    parties = card_str_fr.lower().replace('-', ' ').split()
    if len(parties) < 2: return None
    valeur_input = parties[0]
    couleur_input = parties[-1] 
    valeur_abr = VALEURS_TRADUCTION.get(valeur_input) or VALEURS_TRADUCTION.get(valeur_input[0])
    couleur_abr = COULEURS_TRADUCTION.get(couleur_input)
    if not valeur_abr or not couleur_abr:
        return None
    return (valeur_abr + couleur_abr).upper() + ".png"

@st.cache_data(show_spinner=False)
def get_equity(main_joueur, cartes_communes, nb_adversaires):
    paquet_virtuel = Deck()
    paquet_complet = paquet_virtuel.cards
    cartes_utilisees = [c for c in main_joueur] + [c for c in cartes_communes]
    paquet_restant = [c for c in paquet_complet if c not in cartes_utilisees]
    nb_cartes_restantes = 5 - len(cartes_communes)
    victoires = 0
    egalites = 0
    
    for _ in range(NB_SIMULATIONS):
        paquet_simu = list(paquet_restant) 
        random.shuffle(paquet_simu)
        cartes_complementaires = paquet_simu[:nb_cartes_restantes]
        board_final = cartes_communes + cartes_complementaires
        offset = nb_cartes_restantes
        adversaires_mains = [
            paquet_simu[offset + i*2 : offset + i*2 + 2] 
            for i in range(nb_adversaires)
        ]
        score_joueur = evaluator.evaluate(board_final, main_joueur)
        scores_adversaires = [evaluator.evaluate(board_final, adv_main) for adv_main in adversaires_mains]
        meilleur_score_adverse = min(scores_adversaires) if scores_adversaires else float('inf')
        if score_joueur < meilleur_score_adverse:
            victoires += 1
        elif score_joueur == meilleur_score_adverse:
            egalites += 1
            
    equite = (victoires + egalites / 2) / NB_SIMULATIONS * 100
    return round(equite, 2)

def get_conseil_et_analyse(equite, taille_pot, mise_a_payer):
    equite_perc = round(equite, 2)
    
    if mise_a_payer == 0:
        cote_pot_perc = None
        if equite > 75: conseil = "🔥 MISER FORT (VALUE BET) : Vous avez une main très forte, misez pour la valeur !"
        elif equite > 55: conseil = "🟢 MISER MOYEN : Main potentiellement gagnante."
        else: conseil = "➡️ CHECKER : Ne misez pas sans avantage clair."
        return conseil, equite_perc, cote_pot_perc
            
    nouveau_pot = taille_pot + mise_a_payer
    cote_pot = mise_a_payer / nouveau_pot
    cote_pot_perc = round(cote_pot * 100, 2)

    if equite >= 60: conseil = "🔥🔥 RELANCER (RAISE) : Votre main est très forte. Mettez la pression pour gagner plus !"
    elif equite >= cote_pot * 100: conseil = "🟢 SUIVRE (CALL) : Mathématiquement, le call est rentable à long terme."
    else: conseil = "🔴 SE COUCHER (FOLD) : Votre équité est inférieure à la cote du pot. Le call est une erreur coûteuse."
        
    return conseil, equite_perc, cote_pot_perc

# --- Fonction d'affichage des cartes sélectionnées ---
def display_selected_cards(card_list: List[str], title: str, cols: int):
    """Affiche les images des cartes dans une ligne de colonnes."""
    if not card_list:
        return
    
    st.markdown(f"#### {title}")
    card_cols = st.columns(cols)
    for i, card_fr in enumerate(card_list):
        if card_fr:
            with card_cols[i % cols]:
                img_file = parse_card_to_filename(card_fr)
                if img_file:
                    st.image(BASE_IMAGE_URL + img_file, use_column_width='always')

# --- Interface Streamlit ("BarnaPoker") ---

def lancer_app():
    
    # --- Initialisation de la Mémoire de Session (Stats) ---
    if 'wins' not in st.session_state: st.session_state.wins = 0
    if 'losses' not in st.session_state: st.session_state.losses = 0

    def increment_wins(): st.session_state.wins += 1
    def increment_losses(): st.session_state.losses += 1
    
    # --- En-tête (Titre et Logo) ---
    col_logo, col_titre = st.columns([1, 3])
    with col_logo:
        # ⚠️ Votre logo personnel ⚠️
        st.image(f"https://github.com/{VOTRE_NOM_UTILISATEUR_GITHUB}/{VOTRE_NOM_DE_DEPOT_GITHUB}/blob/main/barnaPoker.png?raw=true", width=150)
    with col_titre:
        st.title("BarnaPoker 🃏")
        st.subheader("Assistant d'Équité & Décision")
        
    st.markdown("---")

    # --- Affichage des Statistiques de Session ---
    st.header("📊 Statistiques de Session")
    stat_cols = st.columns(2)
    stat_cols[0].metric("Mains Gagnées", st.session_state.wins, "🟢")
    stat_cols[1].metric("Mains Perdues", st.session_state.losses, "🔴")
    st.markdown("---")

    # 1. Saisie des cartes du joueur (Sélecteur Multiple - LIMITE À 2)
    st.header("1. Votre Main (Sélectionnez 2 Cartes)")
    
    # 🚨 SÉLECTION MULTIPLE POUR LA MAIN
    main_joueur_fr = st.multiselect(
        "Cartes en Main :", 
        options=CARTES_DISPONIBLES_FR, 
        max_selections=2, # Limite à 2 cartes
        key='hand_select',
        placeholder="Sélectionnez deux cartes..."
    )

    # Affichage des cartes sélectionnées (Main)
    display_selected_cards(main_joueur_fr, "Main sélectionnée :", 2)
    st.markdown("---")
    
    # 2. Saisie des cartes communes (Sélecteur Multiple - LIMITE À 5)
    st.header("2. Cartes Communes (Sélectionnez 3 à 5 Cartes)")
    
    # Créer la liste des cartes disponibles pour le board
    cartes_disponibles_board = [c for c in CARTES_DISPONIBLES_FR if c not in main_joueur_fr]

    # 🚨 SÉLECTION MULTIPLE POUR LE BOARD
    board_list_fr = st.multiselect(
        "Cartes sur la Table (Flop, Turn, River) :", 
        options=cartes_disponibles_board, 
        max_selections=5, # Limite à 5 cartes max
        key='board_select',
        placeholder="Sélectionnez les cartes du Flop (min 3)..."
    )

    # Affichage des cartes sélectionnées (Board)
    display_selected_cards(board_list_fr, "Board sélectionné :", 5)
    st.markdown("---")

    # 3. Saisie des variables financières (Inchangé)
    st.header("3. Variables de Jeu")
    var_cols = st.columns(2)
    taille_pot = var_cols[0].number_input("Taille du pot actuel :", min_value=1, value=100)
    mise_a_payer = var_cols[1].number_input("Montant à payer :", min_value=0, value=25)

    st.markdown("---")
    
    # 4. Bouton de calcul
    if st.button("CALCULER LE CONSEIL (Simuler 10k Mains)", type="primary", use_container_width=True):
        
        try:
            # Vérifications de la main et du board
            if len(main_joueur_fr) != 2:
                st.error("Veuillez sélectionner **exactement 2 cartes** pour votre main.")
                return

            if len(board_list_fr) < 3:
                st.error("Veuillez sélectionner **au moins 3 cartes** (le Flop) sur la table.")
                return

            # Conversion pour la logique de calcul
            main_joueur_int = [parse_card_to_int(c) for c in main_joueur_fr]
            cartes_communes_int = [parse_card_to_int(c) for c in board_list_fr]
            
            # --- Affichage des résultats et calcul ---
            with st.spinner(f"Simulation de {NB_SIMULATIONS} mains en cours..."):
                equite = get_equity(main_joueur_int, cartes_communes_int, NB_ADVERSAIRES)
            
            nom_combinaison = evaluator.class_to_string(evaluator.get_rank_class(evaluator.evaluate(cartes_communes_int, main_joueur_int)))
            st.success(f"Votre combinaison actuelle : **{nom_combinaison}**")

            conseil, equite_perc, cote_pot_perc = get_conseil_et_analyse(equite, taille_pot, mise_a_payer)

            st.header("Analyse de la Rentabilité")
            col_eq, col_cote = st.columns(2)
            col_eq.metric(label="Équité (Vos chances de gagner)", value=f"{equite_perc}%")
            
            if cote_pot_perc is not None:
                col_cote.metric(label="Cote du Pot (Rentabilité minimum)", value=f"{cote_pot_perc}%")
            else:
                col_cote.metric(label="Cote du Pot", value="N/A (Check)")

            st.markdown("---")
            st.header("➡️ CONSEIL DU BOT :")
            st.markdown(f"## {conseil}")
            
            # --- Boutons GAGNER / PERDU ---
            st.markdown("---")
            st.subheader("Enregistrer le résultat de cette main :")
            stat_btn_cols = st.columns(2)
            
            stat_btn_cols[0].button("🟢 GAGNER (Main suivante)", on_click=increment_wins, use_container_width=True)
            stat_btn_cols[1].button("🔴 PERDU (Main suivante)", on_click=increment_losses, use_container_width=True)

        except Exception as e:
            st.error(f"Une erreur s'est produite : {e}")
            if "not found in" in str(e):
                st.error("Vérifiez que votre nom d'utilisateur et de dépôt GitHub sont corrects dans le code source.")
                st.error(f"Vérifiez aussi que le logo (barnaPoker.png) et les cartes (ex: AS.png) sont bien présents dans le dossier images/ de votre dépôt.")


if __name__ == "__main__":
    lancer_app()
