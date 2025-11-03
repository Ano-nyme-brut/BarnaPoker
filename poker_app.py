import streamlit as st
import random
from deuces import Card, Evaluator, Deck
from itertools import product

# --- Configuration de la Page (Doit être la 1ère commande Streamlit) ---
st.set_page_config(
    page_title="BarnaPoker",  # Titre de l'onglet du navigateur
    page_icon="🃏",          # Icône de l'onglet (emoji)
    layout="centered"         # Mettre le contenu au centre
)

# --- Configuration de la Simulation ---
NB_ADVERSAIRES = 1
NB_SIMULATIONS = 10000

# Initialise l'évaluateur de main
evaluator = Evaluator()

# --- Dictionnaires de Traduction (Inchangés) ---
VALEURS_TRADUCTION = {
    '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', '8': '8', '9': '9',
    'dix': 'T', 't': 'T', 'valet': 'J', 'v': 'J', 'dame': 'Q', 'd': 'Q', 'roi': 'K', 'r': 'K', 'as': 'A', 'a': 'A'
}
COULEURS_TRADUCTION = {
    'cœur': 'h', 'coeur': 'h', 'carreau': 'd', 'pique': 's', 'trèfle': 'c', 'trefle': 'c'
}
ABREVIATIONS_COULEURS = {'h': 'Cœur', 'd': 'Carreau', 'c': 'Trèfle', 's': 'Pique'}

# --- Listes de Cartes (Inchangées) ---
VALEURS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
COULEURS = ['h', 'd', 'c', 's']
CARTES_ABREGEES = sorted([v + c for v, c in product(VALEURS, COULEURS)])

CARTES_DISPONIBLES_FR = []
for abr in CARTES_ABREGEES:
    valeur = abr[0]
    couleur_abr = abr[1]
    valeur_fr = next((k for k, v in VALEURS_TRADUCTION.items() if v == valeur), valeur).capitalize()
    couleur_fr = ABREVIATIONS_COULEURS[couleur_abr]
    CARTES_DISPONIBLES_FR.append(f"{valeur_fr} {couleur_fr}")

# --- Fonctions de Logique (Inchangées) ---

def parse_card(card_str):
    parties = card_str.lower().replace('-', ' ').split()
    if len(parties) < 2:
        raise ValueError(f"Format de carte invalide : '{card_str}'.")
    valeur_input = parties[0]
    couleur_input = parties[-1] 
    valeur_abr = VALEURS_TRADUCTION.get(valeur_input)
    if not valeur_abr:
        valeur_abr = VALEURS_TRADUCTION.get(valeur_input[0])
        if not valeur_abr:
            raise ValueError(f"Valeur non reconnue : '{valeur_input}'")
    couleur_abr = COULEURS_TRADUCTION.get(couleur_input)
    if not couleur_abr:
        raise ValueError(f"Couleur non reconnue : '{couleur_input}'")
    return Card.new(valeur_abr + couleur_abr)

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
        if equite > 75:
            conseil = "🔥 MISER FORT (VALUE BET) : Vous avez une main très forte, misez pour la valeur !"
        elif equite > 55:
            conseil = "🟢 MISER MOYEN : Main potentiellement gagnante."
        else:
            conseil = "➡️ CHECKER : Ne misez pas sans avantage clair."
        return conseil, equite_perc, cote_pot_perc
            
    nouveau_pot = taille_pot + mise_a_payer
    cote_pot = mise_a_payer / nouveau_pot
    cote_pot_perc = round(cote_pot * 100, 2)

    if equite >= 60:
        conseil = "🔥🔥 RELANCER (RAISE) : Votre main est très forte. Mettez la pression pour gagner plus !"
    elif equite >= cote_pot * 100:
        conseil = "🟢 SUIVRE (CALL) : Mathématiquement, le call est rentable à long terme."
    else:
        conseil = "🔴 SE COUCHER (FOLD) : Votre équité est inférieure à la cote du pot. Le call est une erreur coûteuse."
        
    return conseil, equite_perc, cote_pot_perc

# --- Interface Streamlit ("BarnaPoker") ---

def lancer_app():
    """Fonction principale de l'application Streamlit."""
    
    # --- NOUVEAU : Initialisation de la Mémoire de Session (Stats) ---
    if 'wins' not in st.session_state:
        st.session_state.wins = 0
    if 'losses' not in st.session_state:
        st.session_state.losses = 0

    # --- NOUVEAU : Fonctions de Callback pour les boutons Stats ---
    def increment_wins():
        st.session_state.wins += 1
        
    def increment_losses():
        st.session_state.losses += 1
    
    # --- En-tête (Titre et Logo) ---
    col_logo, col_titre = st.columns([1, 3])
    with col_logo:
        st.image("https://www.shutterstock.com/image-vector/poker-chip-vector-icon-logo-600nw-1029193750.jpg", width=150)
        # Remplacez le lien ci-dessus par votre propre lien d'image, ou un chemin local :
        # st.image("votre_logo.png") 
    with col_titre:
        st.title("BarnaPoker 🃏")
        st.subheader("Assistant d'Équité & Décision")
        
    st.markdown("---")

    # --- NOUVEAU : Affichage des Statistiques de Session ---
    st.header("📊 Statistiques de Session")
    stat_cols = st.columns(2)
    stat_cols[0].metric("Mains Gagnées", st.session_state.wins, "🟢")
    stat_cols[1].metric("Mains Perdues", st.session_state.losses, "🔴")
    st.markdown("---")

    # 1. Saisie des cartes du joueur
    st.header("1. Votre Main (2 Cartes)")
    
    col1, col2 = st.columns(2)
    carte1_fr = col1.selectbox("Carte 1 :", options=CARTES_DISPONIBLES_FR, key='c1')
    options_c2 = [c for c in CARTES_DISPONIBLES_FR if c != carte1_fr]
    carte2_fr = col2.selectbox("Carte 2 :", options=options_c2, key='c2')

    # 2. Saisie des cartes communes (Board)
    st.header("2. Cartes Communes (Board)")
    st.info("Remplissez les 3 cases du Flop. La 4ème (Turn) et 5ème (River) sont optionnelles.")
    
    flop_cols = st.columns(3)
    flop1 = flop_cols[0].text_input("Flop 1", placeholder="Ex: As Pique")
    flop2 = flop_cols[1].text_input("Flop 2", placeholder="Ex: Roi Coeur")
    flop3 = flop_cols[2].text_input("Flop 3", placeholder="Ex: 7 Trefle")
    
    tr_cols = st.columns(2)
    turn = tr_cols[0].text_input("Turn (4ème carte)", placeholder="Optionnel")
    river = tr_cols[1].text_input("River (5ème carte)", placeholder="Optionnel")

    # 3. Saisie des variables financières
    st.header("3. Variables de Jeu")
    
    var_cols = st.columns(2)
    taille_pot = var_cols[0].number_input("Taille du pot actuel :", min_value=1, value=100)
    mise_a_payer = var_cols[1].number_input("Montant à payer :", min_value=0, value=25)

    st.markdown("---")
    
    # 4. Bouton de calcul
    if st.button("CALCULER LE CONSEIL (Simuler 10k Mains)", type="primary", use_container_width=True):
        
        try:
            main_joueur = [parse_card(carte1_fr), parse_card(carte2_fr)]
            
            # Conversion de la saisie du board (depuis les 5 cases)
            board_list_str = [flop1, flop2, flop3, turn, river]
            board_list_fr = [c.strip() for c in board_list_str if c.strip()]
            
            cartes_communes = []
            if len(board_list_fr) > 0:
                cartes_communes = [parse_card(c) for c in board_list_fr]
            else:
                st.warning("Veuillez entrer au moins 3 cartes communes (Flop) pour un calcul utile.")
                return

            if len(cartes_communes) < 3:
                st.error("Le Flop doit contenir 3 cartes pour un calcul.")
                return
            
            toutes_cartes = main_joueur + cartes_communes
            toutes_cartes_ints = [c for c in toutes_cartes] 
            if len(toutes_cartes_ints) != len(set(toutes_cartes_ints)):
                st.error("Attention : Des cartes sont en double. Veuillez vérifier.")
                return

            # --- Affichage des résultats et calcul ---
            
            with st.spinner(f"Simulation de {NB_SIMULATIONS} mains en cours..."):
                equite = get_equity(main_joueur, cartes_communes, NB_ADVERSAIRES)
            
            nom_combinaison = evaluator.class_to_string(evaluator.get_rank_class(evaluator.evaluate(cartes_communes, main_joueur)))
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
            
            # --- NOUVEAU : Boutons GAGNER / PERDU ---
            st.markdown("---")
            st.subheader("Enregistrer le résultat de cette main :")
            stat_btn_cols = st.columns(2)
            
            # Bouton GAGNER (utilise on_click pour appeler la fonction increment_wins)
            stat_btn_cols[0].button(
                "🟢 GAGNER (Main suivante)", 
                on_click=increment_wins, 
                use_container_width=True
            )
            # Bouton PERDU
            stat_btn_cols[1].button(
                "🔴 PERDU (Main suivante)", 
                on_click=increment_losses, 
                use_container_width=True
            )

        except ValueError as ve:
            st.error(f"Erreur de Saisie : {ve}. Vérifiez l'orthographe et le format (ex: 'As Coeur, Roi Pique').")
        except Exception as e:
            st.error(f"Une erreur inattendue s'est produite : {e}")

if __name__ == "__main__":
    lancer_app()