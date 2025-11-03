import streamlit as st
import random
from deuces import Card, Evaluator, Deck
from itertools import product
from typing import List

# --- Configuration de la Page ---
st.set_page_config(page_title="BarnaPoker", page_icon="🃏", layout="centered")

# -------------------------------------------------------------------
# ⚠️ ACTION REQUISE : Mettez à jour ces deux lignes ! ⚠️
VOTRE_NOM_UTILISATEUR_GITHUB = "Ano-nyme-brut"
VOTRE_NOM_DE_DEPOT_GITHUB = "BarnaPoker" 
# -------------------------------------------------------------------

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

ORDRE_VALEUR = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10, '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2}
ORDRE_COULEUR = {'s': 4, 'h': 3, 'd': 2, 'c': 1} 


# --- Définitions de Cartes ---
VALEURS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
COULEURS = ['h', 'd', 'c', 's']
CARTES_ABREGEES = [v + c for v, c in product(VALEURS, COULEURS)]


def get_carte_fr(abr):
    valeur = abr[0]
    couleur_abr = abr[1]
    valeur_fr = next((k for k, v in VALEURS_TRADUCTION.items() if v == valeur), valeur).capitalize()
    couleur_fr = ABREVIATIONS_COULEURS[couleur_abr]
    return f"{valeur_fr} {couleur_fr}"

def sort_cartes(carte_fr):
    parties = carte_fr.lower().split()
    valeur_abr = VALEURS_TRADUCTION.get(parties[0]) or VALEURS_TRADUCTION.get(parties[0][0])
    couleur_abr = COULEURS_TRADUCTION.get(parties[-1])
    ordre_couleur = ORDRE_COULEUR.get(couleur_abr, 0)
    ordre_valeur = ORDRE_VALEUR.get(valeur_abr, 0)
    return (ordre_couleur, -ordre_valeur) 

CARTES_DISPONIBLES_FR = sorted([get_carte_fr(abr) for abr in CARTES_ABREGEES], key=sort_cartes)


def get_button_value(card_fr):
    valeur_fr = card_fr.split(' ')[0].lower()
    
    for key, short_code in VALEURS_TRADUCTION.items():
        if key == valeur_fr:
            return short_code
            
    return valeur_fr.upper()

# --- Fonctions de Logique (Conversion, Calcul, Affichage) ---

def parse_card_to_int(card_str_fr):
    parties = card_str_fr.lower().replace('-', ' ').split()
    if len(parties) < 2: raise ValueError(f"Format invalide : '{card_str_fr}'.")
    valeur_input = parties[0]
    couleur_input = parties[-1] 
    valeur_abr = VALEURS_TRADUCTION.get(valeur_input) or VALEURS_TRADUCTION.get(valeur_input[0])
    couleur_abr = COULEURS_TRADUCTION.get(couleur_input)
    if not valeur_abr or not couleur_abr: raise ValueError(f"Carte non reconnue : '{card_str_fr}'")
    return Card.new(valeur_abr + couleur_abr)

def parse_card_to_filename(card_str_fr):
    parties = card_str_fr.lower().replace('-', ' ').split()
    if len(parties) < 2: return None
    valeur_input = parties[0]
    couleur_input = parties[-1] 
    valeur_abr = VALEURS_TRADUCTION.get(valeur_input) or VALEURS_TRADUCTION.get(valeur_input[0])
    couleur_abr = COULEURS_TRADUCTION.get(couleur_input)
    if not valeur_abr or not couleur_abr: return None
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
        if score_joueur < meilleur_score_adverse: victoires += 1
        elif score_joueur == meilleur_score_adverse: egalites += 1
            
    equite = (victoires + egalites / 2) / NB_SIMULATIONS * 100
    return round(equite, 2)

def get_conseil_et_analyse(equite, taille_pot, mise_a_payer):
    equite_perc = round(equite, 2)
    
    if mise_a_payer == 0:
        cote_pot_perc = None
        if equite > 75: conseil = "🔥 MISER FORT (VALUE BET)"
        elif equite > 55: conseil = "🟢 MISER MOYEN"
        else: conseil = "➡️ CHECKER"
        return conseil, equite_perc, cote_pot_perc
            
    nouveau_pot = taille_pot + mise_a_payer
    cote_pot = mise_a_payer / nouveau_pot
    cote_pot_perc = round(cote_pot * 100, 2)

    if equite >= 60: conseil = "🔥🔥 RELANCER (RAISE)"
    elif equite >= cote_pot * 100: conseil = "🟢 SUIVRE (CALL)"
    else: conseil = "🔴 SE COUCHER (FOLD)"
        
    return conseil, equite_perc, cote_pot_perc

def display_selected_cards(card_list: List[str], title: str, cols: int):
    if not card_list: return
    
    st.markdown(f"#### {title}")
    card_cols = st.columns(cols)
    
    for i, card_fr in enumerate(card_list):
        if card_fr:
            with card_cols[i % cols]:
                img_file = parse_card_to_filename(card_fr)
                
                if img_file:
                    st.image(BASE_IMAGE_URL + img_file, use_container_width=True) 
                
                st.markdown(f"<p style='text-align: center; font-size: 14px; margin-top: -10px;'>{card_fr}</p>", unsafe_allow_html=True) 


# --- Logique de Clic des Boutons (Séparée) ---

def add_to_hand(card):
    if len(st.session_state.hand_list) < 2 and card not in st.session_state.hand_list and card not in st.session_state.board_list:
        st.session_state.hand_list.append(card)

def add_to_board(card):
    if len(st.session_state.board_list) < 5 and card not in st.session_state.board_list and card not in st.session_state.hand_list:
        st.session_state.board_list.append(card)

def clear_hand():
    st.session_state.hand_list = []
    
def clear_board():
    st.session_state.board_list = []
    
# CORRECTION: Fonction de réinitialisation sans st.rerun pour éviter l'APIException
def reset_stats_action():
    st.session_state.wins = 0
    st.session_state.losses = 0

# --- Interface Streamlit ("BarnaPoker") ---

def lancer_app():
    
    # --- Initialisation de la Mémoire de Session ---
    if 'wins' not in st.session_state: st.session_state.wins = 0
    if 'losses' not in st.session_state: st.session_state.losses = 0
    if 'hand_list' not in st.session_state: st.session_state.hand_list = []
    if 'board_list' not in st.session_state: st.session_state.board_list = []


    def increment_wins(): st.session_state.wins += 1
    def increment_losses(): st.session_state.losses += 1
    
    # --- En-tête (Titre et Logo) ---
    col_logo, col_titre = st.columns([1, 3])
    with col_logo:
        st.image(f"https://github.com/{VOTRE_NOM_UTILISATEUR_GITHUB}/{VOTRE_NOM_DE_DEPOT_GITHUB}/blob/main/barnaPoker.png?raw=true", width=150)
    with col_titre:
        st.title("BarnaPoker 🃏")
        st.subheader("L'outil essentiel pour devenir un joueur gagnant.")
        
    st.markdown("---")

    # --- Section de Bienvenue / Description ---
    st.markdown("""
        ### Bienvenue, Stratège.
        **BarnaPoker** vous offre une **analyse instantanée** de votre position mathématique (Équité) pour vous aider à prendre la décision optimale.
        Cliquez sur les cartes, lisez le conseil, et enregistrez vos résultats !
    """)
    st.markdown("---")


    # --- Affichage des Statistiques de Session ---
    st.header("📊 Historique & Statistiques")
    
    total_mains = st.session_state.wins + st.session_state.losses
    taux_reussite = st.session_state.wins / total_mains * 100 if total_mains > 0 else 0
    
    stat_cols = st.columns(3)
    stat_cols[0].metric("Mains Gagnées", st.session_state.wins, "🟢")
    stat_cols[1].metric("Mains Perdues", st.session_state.losses, "🔴")
    stat_cols[2].metric("Taux de Réussite", f"{taux_reussite:.1f}%", "🎯")
    
    # Bouton de Réinitialisation des stats (Utilise on_click pour l'action)
    if st.button("Réinitialiser les Statistiques", on_click=reset_stats_action, type="default"):
        pass # L'action est dans le callback
        
    st.markdown("---")

    # --- Configuration de la Grille ---
    COLS_PAR_COULEUR = 13 
    st.markdown("""
        <style>
        .stButton>button {
            width: 100%;
            margin: 2px 0;
            padding: 5px 0;
            font-size: 10px; 
            height: 30px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    CARTES_PAR_COULEUR = {
        'Pique': [], 'Cœur': [], 'Carreau': [], 'Trèfle': []
    }
    for c in CARTES_DISPONIBLES_FR:
        if 'Pique' in c: CARTES_PAR_COULEUR['Pique'].append(c)
        elif 'Cœur' in c: CARTES_PAR_COULEUR['Cœur'].append(c)
        elif 'Carreau' in c: CARTES_PAR_COULEUR['Carreau'].append(c)
        elif 'Trèfle' in c: CARTES_PAR_COULEUR['Trèfle'].append(c)

    # 1. Saisie des cartes du joueur (GRILLE DE BOUTONS)
    st.header("1. Saisie des Cartes")
    
    # Affichage des Mains
    col_btn_clear_hand, col_empty = st.columns([1, 3])
    with col_btn_clear_hand:
        st.button("Vider la Main", on_click=clear_hand, type="secondary")
    display_selected_cards(st.session_state.hand_list, "Votre Main :", 2)
    
    # Affichage du Board
    col_btn_clear_board, col_empty_2 = st.columns([1, 3])
    with col_btn_clear_board:
        st.button("Vider le Board", on_click=clear_board, type="secondary")
    display_selected_cards(st.session_state.board_list, "Cartes Communes :", 5)

    st.markdown("---")
    
    # --- GRILLE DE SÉLECTION COMPLÈTE ---
    all_used_cards = st.session_state.hand_list + st.session_state.board_list
    
    if len(st.session_state.hand_list) < 2:
        st.info("Cliquez sur la grille ci-dessous pour ajouter votre **Main** (2 cartes)...")
    elif len(st.session_state.board_list) < 5:
        st.info("Cliquez sur la grille ci-dessous pour ajouter les **Cartes Communes** (Board - min 3, max 5)...")
    else:
        st.success("Toutes les cartes sont sélectionnées (Main + Board).")
    
    for couleur, cartes in CARTES_PAR_COULEUR.items():
        st.markdown(f"**{couleur} :**")
        cols = st.columns(COLS_PAR_COULEUR)
        
        for i, card in enumerate(cartes):
            
            is_disabled = card in all_used_cards
            
            if len(st.session_state.hand_list) < 2:
                action = (add_to_hand, (card,))
                help_text = "Ajouter à la Main"
            elif len(st.session_state.board_list) < 5:
                action = (add_to_board, (card,))
                help_text = "Ajouter au Board"
            else:
                action = (lambda x: None, (card,))
                is_disabled = True
                help_text = "Sélection maximum atteinte"

            
            button_label = get_button_value(card)
            
            with cols[i]:
                st.button(
                    button_label, 
                    key=f'btn_{card}', 
                    disabled=is_disabled, 
                    on_click=action[0], 
                    args=action[1],
                    help=help_text
                )

    st.markdown("---")
    
    # 2. Variables de Jeu
    st.header("2. Variables de Jeu")
    var_cols = st.columns(2)
    taille_pot = var_cols[0].number_input("Taille du pot actuel :", min_value=1, value=100)
    mise_a_payer = var_cols[1].number_input("Montant à payer :", min_value=0, value=25)

    st.markdown("---")
    
    # 3. Bouton de calcul
    if st.button("CALCULER LE CONSEIL (Simuler 10k Mains)", type="primary", use_container_width=True):
        
        try:
            # 1. Vérification des entrées
            if len(st.session_state.hand_list) != 2:
                st.error("❌ Erreur : Veuillez sélectionner **exactement 2 cartes** pour votre Main.")
                return

            if len(st.session_state.board_list) not in [3, 4, 5]:
                st.error("❌ Erreur : Le Board doit contenir **3, 4 ou 5 cartes**.")
                return

            # 2. Conversion finale
            main_joueur_int = [parse_card_to_int(c) for c in st.session_state.hand_list]
            cartes_communes_int = [parse_card_to_int(c) for c in st.session_state.board_list]

            # 3. Calcul
            with st.spinner(f"Analyse des {NB_SIMULATIONS} scénarios en cours..."):
                equite = get_equity(main_joueur_int, cartes_communes_int, NB_ADVERSAIRES)
            
            nom_combinaison = evaluator.class_to_string(evaluator.get_rank_class(evaluator.evaluate(cartes_communes_int, main_joueur_int)))
            st.success(f"Votre combinaison actuelle : **{nom_combinaison}**")

            conseil, equite_perc, cote_pot_perc = get_conseil_et_analyse(equite, taille_pot, mise_a_payer)

            st.header("Analyse de la Rentabilité")
            col_eq, col_cote = st.columns(2)
            col_eq.metric(label="Équité (Votre % de victoire)", value=f"{equite_perc}%")
            
            if cote_pot_perc is not None: col_cote.metric(label="Cote du Pot (Rentabilité min.)", value=f"{cote_pot_perc}%")
            else: col_cote.metric(label="Cote du Pot", value="N/A (Check)")

            st.markdown("---")
            st.header("➡️ CONSEIL DU BOT :")
            st.markdown(f"## {conseil}")
            
            # --- Boutons GAGNER / PERDU ---
            st.markdown("---")
            st.subheader("Enregistrez le résultat de la main :")
            stat_btn_cols = st.columns(2)
            
            stat_btn_cols[0].button("🟢 J'AI GAGNÉ", on_click=increment_wins, use_container_width=True, type="primary")
            stat_btn_cols[1].button("🔴 J'AI PERDU", on_click=increment_losses, use_container_width=True)

        except Exception as e:
            st.error(f"❌ Une erreur s'est produite : {e}")


if __name__ == "__main__":
    lancer_app()
