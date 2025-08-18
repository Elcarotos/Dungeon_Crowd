# map_gestion.py
import pygame
import random
import math

# --- Couleurs (doivent être définies ou importées) ---
NOIR = (0, 0, 0)
BLANC = (255, 255, 255)
GRIS_CLAIR = (200, 200, 200)
GRIS_FONCE = (50, 50, 50)
GRIS_CONTOUR = (30, 30, 30)
COULEUR_BOUTON_SELECTIONNE = (100, 100, 255) # Bleu clair pour le bouton sélectionné
COULEUR_VERROUILLE = (100, 100, 100) # Couleur pour les éléments verrouillés
COULEUR_NOEUD_CARTE_DEVERROUILLE = (150, 200, 150) # Vert clair pour les nœuds
COULEUR_NOEUD_CARTE_SELECTIONNE = (255, 255, 0) # Jaune pour les nœuds sélectionnés
COULEUR_NOEUD_CARTE_TERMINE = (0, 100, 0) # Vert foncé pour les nœuds terminés

# --- Paramètres du jeu (doivent être définis ou importés) ---
LARGEUR, HAUTEUR = 800, 600

# MODIFICATION: Définition des nœuds de la carte avec positions statiques et 'total_rounds'
MAP_NODE_RADIUS = 60 # Rayon des cercles de la carte
MAP_PADDING = 80 # Marge autour des nœuds de la carte pour éviter les bords

map_nodes = [
    {'name': 'Forêt Obscure', 'start_round': 1, 'total_rounds': 10, 'pos': (150, 200)}, # 10 manches
    {'name': 'Cavernes Glauques', 'start_round': 1, 'total_rounds': 15, 'pos': (400, 150)}, # 15 manches
    {'name': 'Donjon Oublié', 'start_round': 1, 'total_rounds': 20, 'pos': (650, 250)}, # 20 manches
    {'name': 'Pics Maudits', 'start_round': 1, 'total_rounds': 25, 'pos': (250, 400)}, # 25 manches
    {'name': 'Abîmes Infernaux', 'start_round': 1, 'total_rounds': 30, 'pos': (550, 450)}, # 30 manches
]

current_map_node_index = 0 # Index du nœud de carte actuellement sélectionné
map_node_buttons = [] # Liste des objets Bouton pour les nœuds de la carte

# NOUVEAU: Variable pour indiquer qu'un démarrage de niveau est demandé
map_node_start_requested = False

# --- Classes du jeu (doivent être importées ou définies) ---
# Ceci est une version simplifiée de la classe Bouton pour ce module.
# La version complète devrait être importée de votre fichier principal.
class Bouton:
    def __init__(self, x, y, largeur, hauteur, texte, couleur_normale, action=None):
        self.rect = pygame.Rect(x, y, largeur, hauteur)
        self.texte = texte
        self.couleur_normale = couleur_normale
        self.couleur_active_ui = COULEUR_BOUTON_SELECTIONNE # Couleur pour le survol/sélection
        self.action = action
        self.font = pygame.font.Font(None, 30)
        self.is_selected = False
        self.is_locked = False # Utilisé pour indiquer si un bouton est interactif

    def dessiner(self, surface):
        current_color = self.couleur_normale
        if self.is_locked:
            current_color = COULEUR_VERROUILLE # Les boutons verrouillés apparaissent grisés
        elif self.is_selected:
            current_color = self.couleur_active_ui
            
        pygame.draw.rect(surface, current_color, self.rect)
        pygame.draw.rect(surface, GRIS_CONTOUR, self.rect, 2) 

        temp_font = self.font
        text_surface = temp_font.render(self.texte, True, NOIR)
        while text_surface.get_width() > self.rect.width - 10: 
            font_size = temp_font.get_height() - 2
            if font_size <= 16:
                break
            temp_font = pygame.font.Font(None, font_size)
            text_surface = temp_font.render(self.texte, True, NOIR)

        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def gerer_evenement(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                if self.action and not self.is_locked:
                    self.action()

    def set_selected(self, state):
        self.is_selected = state

    def set_locked(self, state):
        self.is_locked = state


# --- Fonctions de gestion de la carte ---
def initialize_map_buttons(return_to_main_menu_func, MAP_MENU_X_OFFSET_CENTER, BUTTON_GENERAL_HEIGHT, BUTTON_VERTICAL_SPACING):
    """
    Initializes the map node buttons and the return button for the map menu.
    
    Args:
        return_to_main_menu_func: The function to call when the "Retour menu principale" button is pressed.
        MAP_MENU_X_OFFSET_CENTER: The X offset for centering the return button.
        BUTTON_GENERAL_HEIGHT: The general height of buttons for spacing calculations.
        BUTTON_VERTICAL_SPACING: The vertical spacing between buttons.
    """
    global map_node_buttons, map_nodes, HAUTEUR, MAP_NODE_RADIUS, GRIS_CLAIR, NOIR
    
    map_node_buttons.clear() 
    
    for i, node in enumerate(map_nodes):
        center_x, center_y = node['pos']
        node_name = node['name']
        button_text = f"{node_name}" 

        btn = Bouton(
            center_x - MAP_NODE_RADIUS, 
            center_y - MAP_NODE_RADIUS, 
            2 * MAP_NODE_RADIUS, 
            2 * MAP_NODE_RADIUS,
            button_text, 
            GRIS_CLAIR, 
            lambda index=i: select_map_node(index) 
        )
        btn.set_locked(False) 
        map_node_buttons.append(btn)
        
    return_main_menu_y = HAUTEUR - 70
    bouton_return_main_menu = Bouton(
        MAP_MENU_X_OFFSET_CENTER, return_main_menu_y, 350, BUTTON_GENERAL_HEIGHT, # Use appropriate width
        "Retour menu principale", GRIS_CLAIR, 
        return_to_main_menu_func
    )
    bouton_return_main_menu.set_locked(False) 
    map_node_buttons.append(bouton_return_main_menu)

def select_map_node(node_index):
    """
    Selects a map node and triggers the start of the selected level if it's a map node.
    
    Args:
        node_index: The index of the map node to select.
    """
    global current_map_node_index, map_node_buttons, map_nodes, map_node_start_requested
    
    if 0 <= node_index < len(map_nodes): 
        current_map_node_index = node_index
        for btn in map_node_buttons: # Deselect all map node buttons
            btn.set_selected(False)
        if 0 <= node_index < len(map_node_buttons): # Select the specific map node button
            map_node_buttons[node_index].set_selected(True)
        print(f"Nœud de carte sélectionné: {map_nodes[node_index]['name']}")
        map_node_start_requested = True # NOUVEAU: Demande de démarrage du niveau

    else: 
        # Si l'index ne correspond pas à un nœud de carte (c'est le bouton "Retour menu principale")
        if map_node_buttons and 0 <= node_index < len(map_node_buttons):
            map_node_buttons[node_index].set_selected(True)
        map_node_start_requested = False # S'assurer que le drapeau est à False pour le bouton retour

def draw_map_menu(surface, font_title, font_map_level_name, font_map_level_round, joueur_completed_levels):
    """
    Draws the map menu on the given surface.
    
    Args:
        surface: The pygame surface to draw on.
        font_title: Font for the menu title.
        font_map_level_name: Font for the map node names.
        font_map_level_round: Font for the map node round information.
        joueur_completed_levels: List of completed level names from the player object.
    """
    global map_nodes, map_node_buttons, MAP_NODE_RADIUS, HAUTEUR, LARGEUR
    global COULEUR_NOEUD_CARTE_DEVERROUILLE, COULEUR_NOEUD_CARTE_TERMINE, COULEUR_NOEUD_CARTE_SELECTIONNE, GRIS_CONTOUR, BLANC, NOIR, GRIS_FONCE

    surface.fill(GRIS_FONCE)
    title_text = font_title.render("Sélection du Niveau", True, BLANC)
    title_rect = title_text.get_rect(center=(LARGEUR // 2, 50))
    surface.blit(title_text, title_rect)

    for i, node in enumerate(map_nodes):
        center_x, center_y = node['pos']
        node_btn = map_node_buttons[i] 
        
        circle_color = COULEUR_NOEUD_CARTE_DEVERROUILLE
        text_color = NOIR
        status_text_display = f"Manches: {node['total_rounds']}"

        if node['name'] in joueur_completed_levels:
            circle_color = COULEUR_NOEUD_CARTE_TERMINE 
            status_text_display = "TERMINÉ"
            text_color = BLANC 

        pygame.draw.circle(surface, circle_color, (center_x, center_y), MAP_NODE_RADIUS)
        pygame.draw.circle(surface, GRIS_CONTOUR, (center_x, center_y), MAP_NODE_RADIUS, 2)

        if node_btn.is_selected:
            pygame.draw.circle(surface, COULEUR_NOEUD_CARTE_SELECTIONNE, (center_x, center_y), MAP_NODE_RADIUS + 5, 3) 

        node_name_surface = font_map_level_name.render(node['name'], True, text_color)
        node_name_rect = node_name_surface.get_rect(center=(center_x, center_y - 10))
        surface.blit(node_name_surface, node_name_rect)

        status_text = font_map_level_round.render(status_text_display, True, text_color)
        status_text_rect = status_text.get_rect(center=(center_x, center_y + 15))
        surface.blit(status_text, status_text_rect)

    # The last button in map_node_buttons is always the "Retour menu principale" button
    if map_node_buttons:
        map_node_buttons[-1].dessiner(surface)

def update_map_button_selection(index_change):
    """
    Updates the selection of buttons in the map menu.
    
    Args:
        index_change: The amount to change the selected index by (+1 for next, -1 for previous).
    """
    global current_map_node_index, map_node_buttons
    
    if not map_node_buttons:
        current_map_node_index = -1
        return

    # Deselect the currently selected button, if any
    for btn in map_node_buttons:
        btn.set_selected(False)

    # Calculate the new selected index
    if current_map_node_index == -1 or not (0 <= current_map_node_index < len(map_node_buttons)):
        current_map_node_index = 0
    else:
        current_map_node_index = (current_map_node_index + index_change) % len(map_node_buttons)
        if current_map_node_index < 0:
            current_map_node_index += len(map_node_buttons)

    # Select the new button
    if map_node_buttons:
        map_node_buttons[current_map_node_index].set_selected(True)
    
    # If the selected button is not the "Retour" button, update current_map_node_index to reflect the level
    if current_map_node_index < len(map_nodes):
        pass # current_map_node_index already holds the correct index for map nodes
    else:
        # If the "Retour" button is selected, set current_map_node_index to -1
        # This prevents it from being confused with a map node.
        current_map_node_index = -1
