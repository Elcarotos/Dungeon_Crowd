import pygame
import random
import os
import math
import array
import json

# --- Initialisation de Pygame (incluant le mixer AVANT les imports de modules) ---
pygame.init()
pygame.mixer.init() # Initialisation du mixer pour les sons déplacée ici

# --- Importe le module de gestion des ennemis ---
# Assurez-vous que Monster_Gestion.py est dans le même répertoire
from Monster_Gestion import Particle, Projectile, Monstre, MonstreRapide, MonstreStatique, creer_monstre

# --- Paramètres du jeu ---
LARGEUR, HAUTEUR = 800, 600
# MODIFICATION: Définir le mode plein écran et conserver la résolution
FENETRE = pygame.display.set_mode((LARGEUR, HAUTEUR), pygame.FULLSCREEN)
pygame.display.set_caption("Dungeon Crow")

# --- Couleurs ---
BLANC = (255, 255, 255)
NOIR = (0, 0, 0)
ROUGE = (255, 0, 0) # Couleur des PV et des monstres
VERT = (0, 255, 0) # Couleur des PV et des potions de soin
BLEU = (0, 0, 255) # Couleur du chevalier et de la traînée de dash
JAUNE = (255, 255, 0) # Couleur pour le débogage de la hitbox
GRIS_CLAIR = (200, 200, 200)
GRIS_FONCE = (50, 50, 50)
GRIS_CONTOUR = (30, 30, 30)
COULEUR_RECHARGE_VIDE = (150, 150, 150) # Gris pour l'indicateur non rechargé
COULEUR_RECHARGE_PLEINE = (0, 200, 0) # Vert pour l'indicateur rechargé
COULEUR_BOUTON_SELECTIONNE = (100, 100, 255) # Bleu clair pour le bouton sélectionné
COULEUR_XP_BARRE = (0, 150, 255) # Bleu pour la barre d'XP

# --- Couleurs pour les effets néon/glow ---
GLOW_ROUGE = (255, 50, 50, 150)  # Rouge plus clair avec transparence pour monstres/particules
GLOW_BLEU = (50, 50, 255, 150)   # Bleu plus clair avec transparence pour joueur
GLOW_ORANGE = (255, 165, 0, 80) # Orange avec transparence réduite pour l'épée
GLOW_BLEU_PARTICULES = (50, 50, 255, 200) # Bleu pour les particules de désintégration du joueur
COULEUR_DASH_TRAIL = (50, 150, 255, 180) # Bleu plus clair et semi-transparent pour la traînée de dash
GLOW_VERT_PARTICULES = (0, 255, 0, 200) # Vert pour les particules de soin
GLOW_JAUNE_PARTICULES = (255, 255, 0, 200) # Jaune pour les particules de niveau supérieur

# --- Chargement des images ou création de substituts en couleur ---
CHEVALIER_IMAGE = pygame.Surface((60, 60))
CHEVALIER_IMAGE.fill(BLEU)

ARRIERE_PLAN_IMAGE = pygame.Surface((LARGEUR, HAUTEUR))
ARRIERE_FANCHE_IMAGE = pygame.Surface((LARGEUR, HAUTEUR)) # Pour le background de la désintégration
ARRIERE_PLAN_IMAGE.fill((100, 100, 100))
ARRIERE_FANCHE_IMAGE.fill((50, 50, 50)) # Un peu plus sombre pour la désintégration

EPEE_BASE_IMAGE = pygame.Surface((20, 50), pygame.SRCALPHA)
pygame.draw.rect(EPEE_BASE_IMAGE, GRIS_CLAIR, (5, 0, 10, 30))
pygame.draw.rect(EPEE_BASE_IMAGE, (150, 75, 0), (0, 30, 20, 10))
EPEE_PIVOT_OFFSET = pygame.math.Vector2(EPEE_BASE_IMAGE.get_width() // 2, EPEE_BASE_IMAGE.get_height())

POTION_SOIN_IMAGE = pygame.Surface((30, 30), pygame.SRCALPHA)
pygame.draw.circle(POTION_SOIN_IMAGE, VERT, (15, 15), 15)
pygame.draw.rect(POTION_SOIN_IMAGE, BLANC, (12, 5, 6, 10))

# --- Chargement des sons (remplacés par des sons factices) ---
def create_dummy_sound(frequency=440, duration=100, volume=0.1):
    sample_rate = pygame.mixer.get_init()[0] if pygame.mixer.get_init() else 44100
    bits = 16 # 16-bit samples
    max_sample = 2**(bits - 1) - 1 # Max value for 16-bit signed integer
    num_samples = int(sample_rate * duration / 1000.0)
    
    samples = []
    for i in range(num_samples):
        t = float(i) / sample_rate
        sample_value = int(volume * max_sample * math.sin(2 * math.pi * frequency * t))
        samples.append(sample_value)

    # Convert samples to a byte array (16-bit signed integers)
    # 'h' for signed short (16-bit)
    sound_array = array.array('h', samples)
    
    return pygame.mixer.Sound(sound_array)

SON_ATTAQUE = create_dummy_sound(880, 50)
SON_NIVEAU_SUP = create_dummy_sound(1000, 150)
SON_POTION = create_dummy_sound(660, 100)
SON_TOURBILLON = create_dummy_sound(700, 200)

# --- Classes du jeu ---

class Bouton:
    def __init__(self, x, y, largeur, hauteur, texte, couleur_normale, action=None):
        self.rect = pygame.Rect(x, y, largeur, hauteur)
        self.texte = texte
        self.couleur_normale = couleur_normale
        self.couleur_active_ui = COULEUR_BOUTON_SELECTIONNE # Couleur pour le survol/sélection
        self.action = action
        self.font = pygame.font.Font(None, 30)
        self.is_selected = False

    def dessiner(self, surface):
        if self.is_selected:
            couleur_a_dessiner = self.couleur_active_ui
        else:
            couleur_a_dessiner = self.couleur_normale
            
        pygame.draw.rect(surface, couleur_a_dessiner, self.rect)
        pygame.draw.rect(surface, GRIS_CONTOUR, self.rect, 2) 

        # Ajuster la taille de la police si le texte est trop long
        temp_font = self.font
        text_surface = temp_font.render(self.texte, True, NOIR)
        while text_surface.get_width() > self.rect.width - 10: # 10px de marge
            font_size = temp_font.get_height() - 2
            if font_size <= 16: # Taille minimale de la police pour lisibilité
                break
            temp_font = pygame.font.Font(None, font_size)
            text_surface = temp_font.render(self.texte, True, NOIR)

        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def set_selected(self, state):
        self.is_selected = state

class Joueur(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = CHEVALIER_IMAGE
        self.rect = self.image.get_rect()
        self.rect.center = (LARGEUR // 2, HAUTEUR - 50)
        
        # Statistiques de base du joueur
        self.BASE_PV_MAX = 100
        self.BASE_DEGATS_ATTAQUE = 35
        self.BASE_VITESSE = 5
        self.BASE_RECHARGE_DASH = 1000
        self.BASE_RECHARGE_TOURBILLON = 5000

        self.vitesse = self.BASE_VITESSE
        self.pv_max = self.BASE_PV_MAX
        self.pv = self.pv_max
        self.degats_attaque = self.BASE_DEGATS_ATTAQUE
        self.temps_derniere_attaque = 0
        self.delai_attaque = 500

        self.est_en_attaque = False
        self.duree_attaque = 200
        self.direction_attaque = pygame.math.Vector2(0, -1)

        self.est_en_dash = False
        self.duree_dash = 150
        self.vitesse_dash = 15
        self.temps_dernier_dash = 0
        self.recharge_dash = self.BASE_RECHARGE_DASH
        self.direction_dash_x = 0
        self.direction_dash_y = 0

        self.epee_hitbox = pygame.Rect(0,0,0,0)

        # Paramètres de la traînée du dash
        self.last_dash_particle_time = 0
        self.dash_particle_interval = 30 # Intervalle pour générer une particule de traînée

        # Attaque Tourbillon (nouvelle compétence)
        self.est_en_tourbillon = False
        self.duree_tourbillon = 300 # Durée de l'attaque tourbillon en ms
        self.temps_debut_tourbillon = 0
        self.recharge_tourbillon = self.BASE_RECHARGE_TOURBILLON # Temps de recharge en ms
        self.temps_dernier_tourbillon = 0
        self.tourbillon_hitbox = pygame.Rect(0,0,0,0)

        # Progression du joueur
        self.level = 1
        self.xp = 0
        self.xp_needed_for_level_up = 100 # XP nécessaire pour le niveau 2
        self.xp_base_needed = 100 # Base pour le calcul de l'XP nécessaire
        self.skill_points = 0 # Points de compétence

        # Niveaux des améliorations (réinitialisés à chaque partie)
        self.upgrade_levels = {
            "degats": 0,
            "pv_max": 0,
            "vitesse": 0,
            "recharge_dash": 0,
            "recharge_tourbillon": 0
        }
        self.upgrade_costs = {
            "degats": 1,
            "pv_max": 1,
            "vitesse": 1,
            "recharge_dash": 1,
            "recharge_tourbillon": 1
        }
        self.upgrade_effects = {
            "degats": 5, # +5 dégâts par niveau
            "pv_max": 10, # +10 PV max par niveau
            "vitesse": 0.5, # +0.5 vitesse par niveau
            "recharge_dash": -50, # -50ms recharge dash par niveau
            "recharge_tourbillon": -200 # -200ms recharge tourbillon par niveau
        }
        # Limites d'amélioration pour éviter des valeurs trop extrêmes
        self.upgrade_limits = {
            "recharge_dash": 500, # Minimum 500ms
            "recharge_tourbillon": 1000 # Minimum 1000ms
        }
        # Stats pour les profils (ces informations sont persistantes)
        self.profile_name = "Nouveau Profil"
        self.highest_round = 0
        self.total_play_time = 0 # En millisecondes


    # Méthode pour exporter les données du joueur dans un dictionnaire
    def to_dict(self):
        # Pour les profils, seules les informations de suivi sont sauvegardées.
        # Les statistiques de jeu spécifiques sont réinitialisées à chaque partie.
        return {
            "profile_name": self.profile_name,
            "highest_round": self.highest_round,
            "total_play_time": self.total_play_time
        }

    # Méthode pour charger les données du joueur depuis un dictionnaire
    def from_dict(self, data):
        # Charge uniquement les informations de suivi du profil.
        # Les statistiques de jeu et les niveaux d'amélioration sont réinitialisés au début de chaque nouvelle partie.
        self.profile_name = data.get("profile_name", "Nouveau Profil")
        self.highest_round = data.get("highest_round", 0)
        self.total_play_time = data.get("total_play_time", 0)


    def deplacement(self, joystick_axes=None):
        dx, dy = 0, 0

        if self.est_en_dash:
            self.rect.x += self.direction_dash_x * self.vitesse_dash
            self.rect.y += self.direction_dash_y * self.vitesse_dash
            
            # Créer des particules pour la traînée du dash
            current_time = pygame.time.get_ticks()
            if current_time - self.last_dash_particle_time > self.dash_particle_interval:
                # Créer une particule à la position du joueur
                particle_size = random.randint(8, 15) # Taille des particules de la traînée augmentée
                particle_lifetime = random.randint(600, 1200) # Durée de vie des particules augmentée
                
                # Légère variation de vitesse pour un effet plus organique
                velocity_x = random.uniform(-1, 1)
                velocity_y = random.uniform(-1, 1)
                
                # Utilise la classe Particle importée
                particle = Particle(self.rect.centerx, self.rect.centery, COULEUR_DASH_TRAIL, particle_size, particle_lifetime, (velocity_x, velocity_y))
                tous_les_sprites.add(particle)
                particles.add(particle)
                self.last_dash_particle_time = current_time

        else:
            if joystick_axes:
                joystick_deadzone = 0.1
                if abs(joystick_axes[0]) > joystick_deadzone:
                    dx += joystick_axes[0]
                if abs(joystick_axes[1]) > joystick_deadzone:
                    dy += joystick_axes[1]
            
            mouvement_vector = pygame.math.Vector2(dx, dy)
            if mouvement_vector.length() > 0:
                mouvement_vector.normalize_ip()
                self.rect.x += mouvement_vector.x * self.vitesse
                self.rect.y += mouvement_vector.y * self.vitesse
        
        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(LARGEUR, self.rect.right)
        self.rect.top = max(0, self.rect.top)
        self.rect.bottom = min(HAUTEUR, self.rect.bottom)


    def attaquer(self, monstres_group_ref, direction_attaque_input): 
        temps_actuel = pygame.time.get_ticks()
        if temps_actuel - self.temps_derniere_attaque > self.delai_attaque:
            SON_ATTAQUE.play() # Jouer le son d'attaque
            self.temps_derniere_attaque = temps_actuel
            self.est_en_attaque = True
            self.direction_attaque = direction_attaque_input # Utilise la direction de l'input (joystick)
            
            angle = 0
            if self.direction_attaque == pygame.math.Vector2(0, -1):
                angle = 0
            elif self.direction_attaque == pygame.math.Vector2(0, 1):
                angle = 180
            elif self.direction_attaque == pygame.math.Vector2(-1, 0):
                angle = 90
            elif self.direction_attaque == pygame.math.Vector2(1, 0):
                angle = -90
            elif self.direction_attaque == pygame.math.Vector2(-1, -1):
                angle = 45
            elif self.direction_attaque == pygame.math.Vector2(1, -1):
                angle = -45
            elif self.direction_attaque == pygame.math.Vector2(1, 1):
                angle = -135
            
            rotated_epee = pygame.transform.rotate(EPEE_BASE_IMAGE, angle)
            
            offset_from_player_center = self.direction_attaque * (self.rect.width / 2 + 20)
            epee_final_pos = self.rect.center + offset_from_player_center
            
            if self.direction_attaque.x != 0 and self.direction_attaque.y == 0:
                hitbox_width = rotated_epee.get_width() + 15
                hitbox_height = rotated_epee.get_height() + 5
            elif self.direction_attaque.y != 0 and self.direction_attaque.x == 0:
                hitbox_width = rotated_epee.get_width() + 5
                hitbox_height = rotated_epee.get_height() + 15
            else:
                hitbox_width = rotated_epee.get_width() + 10
                hitbox_height = rotated_epee.get_height() + 10

            self.epee_hitbox = pygame.Rect(0, 0, hitbox_width, hitbox_height)
            self.epee_hitbox.center = epee_final_pos

            degats_infliges = self.degats_attaque
            if self.est_en_dash:
                degats_infliges *= 2

            for monstre in monstres_group_ref: # Utilise le groupe passé en paramètre
                if self.epee_hitbox.colliderect(monstre.rect):
                    monstre.prendre_degats(degats_infliges)

    def dash(self, joystick_axes=None):
        temps_actuel = pygame.time.get_ticks()
        if not self.est_en_dash and (temps_actuel - self.temps_dernier_dash > self.recharge_dash):
            dx, dy = 0, 0
            if joystick_axes:
                joystick_deadzone = 0.1
                if abs(joystick_axes[0]) > joystick_deadzone:
                    dx += joystick_axes[0]
                if abs(joystick_axes[1]) > joystick_deadzone:
                    dy += joystick_axes[1]
            else:
                # Si aucune direction de joystick n'est fournie, dash vers le bas par défaut
                dx, dy = 0, 1 

            if dx != 0 or dy != 0:
                self.est_en_dash = True
                self.temps_dernier_dash = temps_actuel
                magnitude = math.sqrt(dx**2 + dy**2)
                if magnitude > 0:
                    self.direction_dash_x = dx / magnitude
                    self.direction_dash_y = dy / magnitude
                self.last_dash_particle_time = 0 # Réinitialiser le timer pour la génération de particules de traînée

    def whirlwind_attack(self):
        temps_actuel = pygame.time.get_ticks()
        # Assurez-vous que les groupes de sprites sont accessibles ici (variables globales ou passés en paramètre)
        if not self.est_en_tourbillon and (temps_actuel - self.temps_dernier_tourbillon > self.recharge_tourbillon):
            SON_TOURBILLON.play() # Jouer le son de l'attaque tourbillon
            self.est_en_tourbillon = True
            self.temps_debut_tourbillon = temps_actuel
            self.temps_dernier_tourbillon = temps_actuel
            
            # Définir la hitbox du tourbillon (plus grande que l'épée normale)
            tourbillon_radius = self.rect.width * 1.5 # Rayon de l'attaque tourbillon
            self.tourbillon_hitbox = pygame.Rect(0, 0, tourbillon_radius * 2, tourbillon_radius * 2)
            self.tourbillon_hitbox.center = self.rect.center

            # Particules pour l'effet de l'attaque tourbillon
            for _ in range(20): # Plus de particules pour un effet plus visible
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(2, 6) # Vitesse plus élevée pour les particules
                # Les particules s'éloignent du joueur
                velocity = (speed * math.cos(angle), speed * math.sin(angle))
                # Utilise la classe Particle importée
                particle = Particle(self.rect.centerx, self.rect.centery, GLOW_ORANGE, random.randint(4, 8), random.randint(300, 800), velocity)
                tous_les_sprites.add(particle)
                particles.add(particle)

            # Infliger des dégâts aux monstres dans la zone du tourbillon
            for monstre in monstres: # Utilise le groupe de monstres global
                if self.tourbillon_hitbox.colliderect(monstre.rect):
                    monstre.prendre_degats(self.degats_attaque * 0.8) # Dégâts réduits pour le tourbillon

    def prendre_degats(self, degats):
        if not self.est_en_dash:
            self.pv -= degats
            if self.pv < 0:
                self.pv = 0

    def prendre_soin(self, montant_soin):
        self.pv += montant_soin
        self.pv = min(self.pv, self.pv_max)
        SON_POTION.play() # Jouer le son de la potion

    def add_xp(self, amount):
        self.xp += amount
        while self.xp >= self.xp_needed_for_level_up:
            self.level_up()

    def level_up(self):
        self.level += 1
        self.xp -= self.xp_needed_for_level_up
        self.xp_needed_for_level_up = int(self.xp_base_needed * (1.5 ** (self.level - 1))) # Augmente l'XP nécessaire
        self.pv = self.pv_max # Soigne le joueur entièrement
        self.skill_points += 1 # Gagne un point de compétence
        SON_NIVEAU_SUP.play() # Jouer le son de niveau supérieur

        # Particules de niveau supérieur
        for _ in range(20):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(3, 7)
            velocity = (speed * math.cos(angle), speed * math.sin(angle) - random.uniform(0, 2))
            # Utilise la classe Particle importée
            particle = Particle(self.rect.centerx, self.rect.centery, GLOW_JAUNE_PARTICULES, random.randint(4, 8), random.randint(600, 1200), velocity)
            tous_les_sprites.add(particle)
            particles.add(particle)

    def upgrade_stat(self, stat_name):
        if self.skill_points >= self.upgrade_costs[stat_name]:
            if stat_name == "degats":
                self.degats_attaque += self.upgrade_effects[stat_name]
            elif stat_name == "pv_max":
                self.pv_max += self.upgrade_effects[stat_name]
            elif stat_name == "vitesse":
                self.vitesse += self.upgrade_effects[stat_name]
            elif stat_name == "recharge_dash":
                # S'assurer que la recharge ne descend pas en dessous d'une limite
                new_recharge = self.recharge_dash + self.upgrade_effects[stat_name]
                self.recharge_dash = max(self.upgrade_limits["recharge_dash"], new_recharge)
            elif stat_name == "recharge_tourbillon":
                # S'assurer que la recharge ne descend pas en dessous d'une limite
                new_recharge = self.recharge_tourbillon + self.upgrade_effects[stat_name]
                self.recharge_tourbillon = max(self.upgrade_limits["recharge_tourbillon"], new_recharge)
            
            self.skill_points -= self.upgrade_costs[stat_name]
            self.upgrade_levels[stat_name] += 1
            return True
        return False


    def update(self):
        temps_actuel = pygame.time.get_ticks()
        if self.est_en_attaque and (temps_actuel - self.temps_derniere_attaque > self.duree_attaque):
            self.est_en_attaque = False
            self.epee_hitbox = pygame.Rect(0,0,0,0)

        if self.est_en_dash:
            if (temps_actuel - self.temps_dernier_dash > self.duree_dash):
                self.est_en_dash = False
        
        if self.est_en_tourbillon and (temps_actuel - self.temps_debut_tourbillon > self.duree_tourbillon):
            self.est_en_tourbillon = False
            self.tourbillon_hitbox = pygame.Rect(0,0,0,0)


    def dessiner_barre_vie(self, surface):
        barre_longueur = 100
        barre_hauteur = 10
        
        bordure_rect_x = self.rect.centerx - (barre_longueur // 2)
        bordure_rect_y = self.rect.y - 15
        bordure_rect = pygame.Rect(bordure_rect_x, bordure_rect_y, barre_longueur, barre_hauteur)
        
        remplissage = (self.pv / self.pv_max) * barre_longueur
        remplissage_rect = pygame.Rect(bordure_rect_x, bordure_rect_y, remplissage, barre_hauteur)
        
        pygame.draw.rect(surface, ROUGE, bordure_rect)
        pygame.draw.rect(surface, VERT, remplissage_rect)
        pygame.draw.rect(surface, NOIR, bordure_rect, 2)

    def dessiner_epee(self, surface):
        if self.est_en_attaque:
            angle = 0
            if self.direction_attaque == pygame.math.Vector2(0, -1):
                angle = 0
            elif self.direction_attaque == pygame.math.Vector2(0, 1):
                angle = 180
            elif self.direction_attaque == pygame.math.Vector2(-1, 0):
                angle = 90
            elif self.direction_attaque == pygame.math.Vector2(1, 0):
                angle = -90
            elif self.direction_attaque == pygame.math.Vector2(-1, -1):
                angle = 45
            elif self.direction_attaque == pygame.math.Vector2(1, -1):
                angle = -45
            elif self.direction_attaque == pygame.math.Vector2(-1, 1):
                angle = 135
            elif self.direction_attaque == pygame.math.Vector2(1, 1):
                angle = -135
            
            rotated_epee = pygame.transform.rotate(EPEE_BASE_IMAGE, angle)
            
            offset_from_player_center = self.direction_attaque * (self.rect.width / 2 + 20)
            epee_final_pos = self.rect.center + offset_from_player_center
            
            rotated_epee_rect = rotated_epee.get_rect(center=epee_final_pos)

            # Dessiner le glow de l'épée 
            # Réduit le nombre de couches et l'augmentation de taille
            for i in range(1, 0, -1): # Seulement 1 couche pour un glow léger
                glow_surface = pygame.Surface(rotated_epee.get_size(), pygame.SRCALPHA)
                glow_surface.blit(rotated_epee, (0,0))
                glow_surface.fill(GLOW_ORANGE, special_flags=pygame.BLEND_RGBA_ADD)
                
                scaled_glow = pygame.transform.smoothscale(glow_surface, (rotated_epee.get_width() + i * 1, rotated_epee.get_height() + i * 1)) # Taille d'augmentation plus petite
                scaled_glow_rect = scaled_glow.get_rect(center=rotated_epee_rect.center)
                surface.blit(scaled_glow, scaled_glow_rect)

            surface.blit(rotated_epee, rotated_epee_rect)

    def dessiner_dash_recharge_indicator(self, surface):
        temps_actuel = pygame.time.get_ticks()
        temps_ecoule_depuis_dash = temps_actuel - self.temps_dernier_dash
        pourcentage_recharge = min(1.0, temps_ecoule_depuis_dash / self.recharge_dash)

        indicator_center_x = self.rect.centerx - 15 # Décalé pour ne pas chevaucher le tourbillon
        indicator_center_y = self.rect.bottom + 15
        indicator_radius = 10

        pygame.draw.circle(surface, COULEUR_RECHARGE_VIDE, (indicator_center_x, indicator_center_y), indicator_radius, 2)

        if pourcentage_recharge < 1.0:
            start_angle = math.radians(90) 
            end_angle = math.radians(90 - (pourcentage_recharge * 360))

            points = [(indicator_center_x, indicator_center_y)]
            for angle_deg in range(int(math.degrees(start_angle)), int(math.degrees(end_angle)) -1, -5): 
                x = indicator_center_x + indicator_radius * math.cos(math.radians(angle_deg))
                y = indicator_center_y - indicator_radius * math.sin(math.radians(angle_deg))
                points.append((x, y))
            x_end = indicator_center_x + indicator_radius * math.cos(end_angle)
            y_end = indicator_center_y - indicator_radius * math.sin(end_angle)
            points.append((x_end, y_end))
            
            if len(points) > 2:
                pygame.draw.polygon(surface, COULEUR_RECHARGE_PLEINE, points) 
        else:
            pygame.draw.circle(surface, COULEUR_RECHARGE_PLEINE, (indicator_center_x, indicator_center_y), indicator_radius)

    def dessiner_whirlwind_indicator(self, surface):
        temps_actuel = pygame.time.get_ticks()
        temps_ecoule_depuis_tourbillon = temps_actuel - self.temps_dernier_tourbillon
        pourcentage_recharge = min(1.0, temps_ecoule_depuis_tourbillon / self.recharge_tourbillon)

        indicator_center_x = self.rect.centerx + 15 # Décalé pour ne pas chevaucher le dash
        indicator_center_y = self.rect.bottom + 15
        indicator_radius = 10

        pygame.draw.circle(surface, COULEUR_RECHARGE_VIDE, (indicator_center_x, indicator_center_y), indicator_radius, 2)

        if pourcentage_recharge < 1.0:
            start_angle = math.radians(90) 
            end_angle = math.radians(90 - (pourcentage_recharge * 360))

            points = [(indicator_center_x, indicator_center_y)]
            for angle_deg in range(int(math.degrees(start_angle)), int(math.degrees(end_angle)) -1, -5): 
                x = indicator_center_x + indicator_radius * math.cos(math.radians(angle_deg))
                y = indicator_center_y - indicator_radius * math.sin(math.radians(angle_deg))
                points.append((x, y))
            x_end = indicator_center_x + indicator_radius * math.cos(end_angle)
            y_end = indicator_center_y - indicator_radius * math.sin(end_angle)
            points.append((x_end, y_end))
            
            if len(points) > 2:
                pygame.draw.polygon(surface, COULEUR_RECHARGE_PLEINE, points)
        else:
            pygame.draw.circle(surface, COULEUR_RECHARGE_PLEINE, (indicator_center_x, indicator_center_y), indicator_radius)

class PotionDeSoin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.initial_image = POTION_SOIN_IMAGE.copy()
        self.image = self.initial_image
        self.rect = self.initial_image.get_rect(center=(x, y))
        self.montant_soin = 25
        self.spawn_time = pygame.time.get_ticks()
        self.initial_radius = self.initial_image.get_width() // 2

    def update(self):
        current_time = pygame.time.get_ticks()
        time_elapsed = current_time - self.spawn_time
        time_remaining = POTION_DESPAWN_DURATION - time_elapsed
        
        if time_remaining <= 0:
            self.kill()
        else:
            pourcentage_restant = time_remaining / POTION_DESPAWN_DURATION
            new_radius = int(self.initial_radius * pourcentage_restant)
            
            if new_radius < 1:
                new_radius = 1 
            
            new_size = (new_radius * 2, new_radius * 2)
            self.image = pygame.transform.scale(self.initial_image, new_size)
            self.rect = self.image.get_rect(center=self.rect.center)

# --- Groupes de sprites ---
tous_les_sprites = pygame.sprite.Group()
monstres = pygame.sprite.Group()
potions_de_soin = pygame.sprite.Group()
particles = pygame.sprite.Group() # Nouveau groupe pour les particules
projectiles = pygame.sprite.Group() # Nouveau groupe pour les projectiles

# --- Variables globales pour l'état du jeu ---
joueur = None
joystick = None
round_number = 1
last_potion_spawn_time = 0
running = True
game_state = "MAIN_MENU" 
player_death_time = 0
PLAYER_DEATH_ANIMATION_DURATION = 1500 # Durée de l'animation de désintégration en ms

round_start_cooldown_active = False
round_start_cooldown_timer = 0
ROUND_COOLDOWN_DURATION = 1000

selected_button_index = -1
current_selectable_buttons = []
joystick_menu_active = False # Indique si le menu joystick est actif pour la navigation générale
menu_just_opened = False # Nouveau drapeau pour la sélection initiale

POTION_DESPAWN_DURATION = 3000 # Durée de vie des potions réduite à 3 secondes
potion_spawn_interval = 7000
max_potions_on_screen = 2

previous_game_state = "MAIN_MENU" # Pour suivre l'état précédent avant d'entrer dans un sous-menu

# Temps de jeu pour le profil actuel
current_game_session_start_time = 0

# Niveau de luminosité (0.0 à 1.0)
brightness_level = 1.0
# Surface temporaire pour appliquer la luminosité
brightness_surface = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
brightness_surface.fill((0, 0, 0, 0)) # Initialise avec une surface transparente

# Nouvelle variable globale pour le délai du menu
menu_entry_cooldown_timer = 0
MENU_ENTRY_COOLDOWN_DURATION = 200 # 200 ms de délai

# --- Gestion des profils de joueur ---
PROFILES_FILE = "player_profiles.json"
TEMP_PROFILES_FILE = "player_profiles.json.tmp" 
MAX_PROFILES = 3
profiles = []
current_profile_slot = -1 # Indique quel profil est actuellement chargé (-1 si aucun)

# --- Gestion des réglages ---
SETTINGS_FILE = "settings.json"
TEMP_SETTINGS_FILE = "settings.json.tmp"

def load_profiles():
    global profiles
    profiles = [] 

    # Liste des fichiers à tenter de charger, par ordre de préférence
    # Le fichier principal, puis le fichier temporaire (qui pourrait être une sauvegarde d'une écriture atomique échouée)
    files_to_try = [PROFILES_FILE, TEMP_PROFILES_FILE]
    
    loaded_successfully = False
    for filepath in files_to_try:
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list) and all(isinstance(p, dict) for p in data):
                        profiles = data
                        loaded_successfully = True
                        print(f"Profils chargés depuis {filepath}.")
                        break 
                    else:
                        print(f"Format de données inattendu dans {filepath}.")
            except json.JSONDecodeError:
                print(f"Erreur de lecture du fichier de profils {filepath}. Fichier corrompu ou incomplet.")
            except Exception as e:
                print(f"Erreur inattendue lors du chargement des profils depuis {filepath}: {e}")
        else:
            print(f"Fichier {filepath} non trouvé.")

    
    if not loaded_successfully:
        print("Aucun profil valide n'a pu être chargé. Création de profils par défaut.")
        profiles = []

    
    if len(profiles) < MAX_PROFILES:
        while len(profiles) < MAX_PROFILES:
            profiles.append({"name": f"Profil {len(profiles) + 1}", "data": None})
    elif len(profiles) > MAX_PROFILES:
        profiles = profiles[:MAX_PROFILES]
    
    for i in range(MAX_PROFILES):
        if not isinstance(profiles[i], dict):
            profiles[i] = {"name": f"Profil {i + 1}", "data": None}
        if "data" not in profiles[i]:
            profiles[i]["data"] = None
        if "name" not in profiles[i]:
            profiles[i]["name"] = f"Profil {i + 1}"

    if loaded_successfully and os.path.exists(TEMP_PROFILES_FILE):
        try:
            os.remove(TEMP_PROFILES_FILE)
            print(f"Ancien fichier temporaire {TEMP_PROFILES_FILE} supprimé.")
        except OSError as e:
            print(f"Erreur lors du nettoyage du fichier temporaire après chargement réussi: {e}")


def save_profiles():
    try:
        temp_dir = os.path.dirname(PROFILES_FILE)
        if temp_dir and not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        temp_filepath = os.path.join(temp_dir, os.path.basename(PROFILES_FILE) + ".tmp")
        
        with open(temp_filepath, 'w') as f:
            json.dump(profiles, f, indent=4)
            f.flush() # Force le tampon en mémoire à être écrit sur le disque
            os.fsync(f.fileno()) # S'assure que les données sont physiquement écrites sur le disque
        
        if not os.path.exists(temp_filepath) or os.path.getsize(temp_filepath) == 0:
            print(f"Erreur: Le fichier temporaire {temp_filepath} est vide ou n'a pas été créé correctement.")
            return # Ne pas procéder au remplacement si le fichier temporaire est défectueux

        # Supprimer explicitement l'ancien fichier de profils avant de renommer le nouveau
        if os.path.exists(PROFILES_FILE):
            try:
                os.remove(PROFILES_FILE)
                print(f"Ancien fichier de profils {PROFILES_FILE} supprimé.")
            except OSError as e:
                print(f"Erreur lors de la suppression de l'ancien fichier de profils: {e}")
                # Si la suppression échoue, nous continuerons avec os.rename qui pourrait tenter d'écraser
                # mais cela peut indiquer un problème sous-jacent.

        # Renommer (déplacer) le fichier temporaire vers la destination finale
        os.rename(temp_filepath, PROFILES_FILE)
        print("Profils sauvegardés avec succès.")

    except Exception as e:
        print(f"Erreur lors de la sauvegarde des profils: {e}")
        # Tenter de nettoyer le fichier temporaire si une erreur s'est produite avant le remplacement
        if os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
                print(f"Fichier temporaire {temp_filepath} supprimé suite à l'erreur.")
            except OSError as cleanup_e:
                print(f"Erreur lors du nettoyage du fichier temporaire: {cleanup_e}")


def save_current_profile_data():
    global profiles, joueur, current_profile_slot, round_number, current_game_session_start_time
    # Sauvegarde UNIQUEMENT si un slot de profil est actif ET que ce slot n'est PAS marqué comme supprimé (data n'est pas None)
    # Cela empêche de sauvegarder par inadvertance des données par défaut sur un slot supprimé.
    if current_profile_slot != -1 and profiles[current_profile_slot]["data"] is not None and joueur:
        # Mettre à jour highest_round et total_play_time avant de sauvegarder
        joueur.highest_round = max(joueur.highest_round, round_number)
        if current_game_session_start_time != 0:
            joueur.total_play_time += (pygame.time.get_ticks() - current_game_session_start_time)
            current_game_session_start_time = 0 # Réinitialiser après sauvegarde

        profiles[current_profile_slot]["data"] = joueur.to_dict()
        save_profiles()
        print(f"Profil {profiles[current_profile_slot]['name']} sauvegardé.")
    else:
        print("Aucun profil actif ou données de profil valides pour sauvegarder.")

def load_profile_data(slot_index):
    global joueur, current_profile_slot, current_game_session_start_time
    if 0 <= slot_index < MAX_PROFILES and profiles[slot_index]["data"] is not None:
        player_data = profiles[slot_index]["data"]
        joueur = Joueur() # Crée une nouvelle instance de joueur
        # Charge uniquement les informations de suivi (non les stats de jeu)
        joueur.from_dict(player_data) 
        current_profile_slot = slot_index
        # Le temps de session est démarré au reset_game_with_profile
        print(f"Profil {profiles[slot_index]['name']} chargé.")
        return True
    return False

def create_new_profile(slot_index):
    global joueur, current_profile_slot, current_game_session_start_time
    joueur = Joueur() # Crée un nouveau joueur par défaut
    joueur.profile_name = f"Profil {slot_index + 1}" # Nom par défaut pour le nouveau profil
    joueur.highest_round = 0 # Nouveau profil commence à la manche 0
    joueur.total_play_time = 0 # Nouveau profil commence à 0 temps de jeu
    profiles[slot_index]["data"] = joueur.to_dict() # Sauvegarde les stats par défaut (uniquement meta ici)
    current_profile_slot = slot_index
    save_profiles()
    # Le temps de session est démarré au reset_game_with_profile
    print(f"Nouveau profil {joueur.profile_name} créé.")
    return True

# --- Fonction de réinitialisation du jeu (modifiée pour les profils) ---
def reset_game_with_profile():
    global joueur, round_number, last_potion_spawn_time, game_state, selected_button_index, joystick_menu_active
    global round_start_cooldown_active, round_start_cooldown_timer, player_death_time, menu_just_opened, previous_game_state
    global current_game_session_start_time, current_profile_slot, profiles, menu_entry_cooldown_timer

    # Vider tous les groupes de sprites pour une réinitialisation propre
    tous_les_sprites.empty()
    monstres.empty()
    potions_de_soin.empty()
    particles.empty()
    projectiles.empty()

    # Créer une nouvelle instance de joueur
    temp_joueur = Joueur() # Cela initialise temp_joueur avec les BASE_STATS et upgrade_levels à 0

    # Si un profil est chargé, charger ses informations de suivi
    if current_profile_slot != -1 and profiles[current_profile_slot]["data"] is not None:
        temp_joueur.from_dict(profiles[current_profile_slot]["data"])
    else:
        # Si aucun profil n'est sélectionné (cas initial ou erreur), utiliser un joueur par défaut
        temp_joueur.profile_name = "Joueur Invité" # Nom temporaire
        current_profile_slot = -1 # S'assurer qu'aucun slot n'est assigné pour la sauvegarde si pas de profil choisi

    # Réinitialiser les statistiques de jeu pour la nouvelle partie (même si un profil a été chargé,
    # ces stats recommencent à zéro pour la session de jeu actuelle).
    temp_joueur.level = 1
    temp_joueur.xp = 0
    temp_joueur.xp_needed_for_level_up = temp_joueur.xp_base_needed # Réinitialiser la barre d'XP
    temp_joueur.skill_points = 0
    
    # Réinitialiser toutes les stats de combat à leurs valeurs de base
    temp_joueur.pv_max = temp_joueur.BASE_PV_MAX
    temp_joueur.pv = temp_joueur.pv_max # Soigne le joueur entièrement
    temp_joueur.degats_attaque = temp_joueur.BASE_DEGATS_ATTAQUE
    temp_joueur.vitesse = temp_joueur.BASE_VITESSE
    temp_joueur.recharge_dash = temp_joueur.BASE_RECHARGE_DASH
    temp_joueur.recharge_tourbillon = temp_joueur.BASE_RECHARGE_TOURBILLON
    temp_joueur.upgrade_levels = { # Réinitialiser les niveaux de compétences
        "degats": 0,
        "pv_max": 0,
        "vitesse": 0,
        "recharge_dash": 0,
        "recharge_tourbillon": 0
    }

    joueur = temp_joueur # Assigner l'instance réinitialisée au joueur global

    tous_les_sprites.add(joueur)

    # Réinitialiser les variables de jeu spécifiques à la partie
    round_number = 1
    # Utilise la fonction creer_monstre du module Monster_Gestion
    creer_monstre(2, joueur, tous_les_sprites, monstres, particles, projectiles, round_start_cooldown_active)
    last_potion_spawn_time = pygame.time.get_ticks()
    round_start_cooldown_active = True
    round_start_cooldown_timer = pygame.time.get_ticks()

    # Réinitialiser l'état de l'interface et les flags
    deselect_all_buttons()
    joystick_menu_active = False
    menu_just_opened = False
    previous_game_state = "PLAYING"
    game_state = "PLAYING"
    player_death_time = 0
    current_game_session_start_time = pygame.time.get_ticks() # Démarre le timer de session pour la nouvelle partie
    menu_entry_cooldown_timer = pygame.time.get_ticks() # Start cooldown for game entry


# --- Fonction de création de monstres (réalisée par Monster_Gestion.py) ---
# La fonction creer_monstre est maintenant importée et utilisée directement.
# La définition locale ici est supprimée.


# --- Fonction pour quitter le jeu ---
def quitter_le_jeu():
    global running
    save_current_profile_data() # Sauvegarder le profil avant de quitter
    save_settings() # Sauvegarder les réglages avant de quitter
    running = False

# --- Fonction pour afficher la page des contrôles ---
def show_controls_page():
    global game_state, menu_just_opened, previous_game_state, menu_entry_cooldown_timer
    previous_game_state = game_state # Sauvegarder l'état actuel avant de changer
    game_state = "CONTROLS"
    menu_just_opened = True # Set flag to trigger initial selection
    menu_entry_cooldown_timer = pygame.time.get_ticks() # Start cooldown
    deselect_all_buttons() # Ensure all buttons are deselected when entering controls


# --- Fonction pour afficher le menu des compétences ---
def show_skill_menu():
    global game_state, menu_just_opened, previous_game_state, menu_entry_cooldown_timer
    previous_game_state = game_state # Sauvegarder l'état actuel avant de changer
    game_state = "SKILL_MENU"
    menu_just_opened = True # Set flag to trigger initial selection
    menu_entry_cooldown_timer = pygame.time.get_ticks() # Start cooldown
    deselect_all_buttons() # Ensure all buttons are deselected when entering skill menu


# --- Fonction pour revenir au jeu ---
def return_to_game():
    global game_state, joystick_menu_active, menu_just_opened, previous_game_state, menu_entry_cooldown_timer
    game_state = "PLAYING"
    joystick_menu_active = False
    deselect_all_buttons() # Ensure all buttons are deselected when returning to game
    menu_just_opened = False # Not in a menu anymore
    previous_game_state = "PLAYING" # Réinitialiser previous_game_state à PLAYING
    menu_entry_cooldown_timer = pygame.time.get_ticks() # Start cooldown

# --- Fonction pour revenir au menu principal ---
def return_to_main_menu():
    global game_state, joystick_menu_active, menu_just_opened, previous_game_state, menu_entry_cooldown_timer
    save_current_profile_data() # Sauvegarder le profil avant de retourner au menu principal
    game_state = "MAIN_MENU"
    joystick_menu_active = True
    menu_just_opened = True
    deselect_all_buttons()
    # previous_game_state est déjà correctement défini par la fonction appelante (e.g., show_settings_menu, show_profile_menu)
    # ou par le passage à GAME_OVER. Il ne faut pas le réinitialiser ici à "MAIN_MENU" systématiquement.
    menu_entry_cooldown_timer = pygame.time.get_ticks() # Start cooldown

# --- Fonction pour afficher le menu d'options in-game ---
def show_options_menu():
    global game_state, menu_just_opened, joystick_menu_active, previous_game_state, menu_entry_cooldown_timer
    # IMPORTANT: previous_game_state est l'état AVANT d'entrer dans ce menu (OPTIONS_MENU)
    # ou l'état d'où on vient si on y retourne (e.g., CONTROLS).
    # Il est mis à jour avant le changement de game_state dans les fonctions appelantes.
    game_state = "OPTIONS_MENU"
    joystick_menu_active = True
    menu_just_opened = True
    menu_entry_cooldown_timer = pygame.time.get_ticks() # Start cooldown
    deselect_all_buttons() # Ensure all buttons are deselected when entering options menu


# --- Nouvelle fonction pour afficher le menu des profils ---
def show_profile_menu():
    global game_state, menu_just_opened, joystick_menu_active, previous_game_state, menu_entry_cooldown_timer
    previous_game_state = game_state
    game_state = "PROFILE_MENU"
    joystick_menu_active = True
    menu_just_opened = True
    load_profiles() # S'assurer que les profils sont à jour avant d'afficher le menu
    menu_entry_cooldown_timer = pygame.time.get_ticks() # Start cooldown
    deselect_all_buttons() # Ensure all buttons are deselected when entering profile menu


# --- Nouvelle fonction pour afficher le menu des réglages (luminosité, etc.) ---
def show_settings_menu():
    global game_state, menu_just_opened, joystick_menu_active, previous_game_state, menu_entry_cooldown_timer
    previous_game_state = game_state
    game_state = "SETTINGS_MENU" # Nouveau game_state
    joystick_menu_active = True
    menu_just_opened = True
    menu_entry_cooldown_timer = pygame.time.get_ticks() # Start cooldown
    deselect_all_buttons() # Ensure all buttons are deselected when entering settings menu

# Fonction pour revenir au menu précédent (utilisé dans CONTROLS)
def return_to_previous_menu():
    global game_state, joystick_menu_active, menu_just_opened, previous_game_state, menu_entry_cooldown_timer
    # Si l'état précédent était le menu d'options, y retourner
    if previous_game_state == "OPTIONS_MENU":
        show_options_menu()
    # Sinon, retourner au menu principal (comportement par défaut)
    else:
        return_to_main_menu()
    menu_entry_cooldown_timer = pygame.time.get_ticks() # Start cooldown


# --- Fonctions pour régler la luminosité ---
def increase_brightness():
    global brightness_level
    # Augmente par pas de 0.1 et arrondit à une décimale
    brightness_level = round(min(1.0, brightness_level + 0.1), 1) 
    save_settings() # Sauvegarder la nouvelle luminosité
    print(f"Luminosité: {brightness_level:.1f}")

def decrease_brightness():
    global brightness_level
    # Diminue par pas de 0.1, pas moins de 0.1 (10%) et arrondit à une décimale
    brightness_level = round(max(0.1, brightness_level - 0.1), 1) 
    save_settings() # Sauvegarder la nouvelle luminosité
    print(f"Luminosité: {brightness_level:.1f}")


# --- Fonctions d'amélioration (appelées par les boutons) ---
def upgrade_degats():
    joueur.upgrade_stat("degats")
def upgrade_pv():
    joueur.upgrade_stat("pv_max")
def upgrade_vitesse():
    joueur.upgrade_stat("vitesse")
def upgrade_dash():
    joueur.upgrade_stat("recharge_dash")
def upgrade_tourbillon():
    joueur.upgrade_stat("recharge_tourbillon")

# Fonctions pour les boutons de profil
def select_profile(slot_index):
    global current_profile_slot, joueur # Added joueur to global to modify it
    if profiles[slot_index]["data"] is not None:
        load_profile_data(slot_index) # This loads data into joueur and sets current_profile_slot
    else:
        create_new_profile(slot_index) # This creates a new joueur and sets current_profile_slot
    
    # Une fois le profil (ou un nouveau joueur) chargé/créé, démarrer la partie avec ses stats
    reset_game_with_profile()

# --- Nouvelle fonction pour demander confirmation de suppression de profil ---
def ask_confirm_delete_profile(slot_index):
    global game_state, profile_slot_to_delete, menu_just_opened, previous_game_state, menu_entry_cooldown_timer
    if profiles[slot_index]["data"] is not None: # Seulement si des données existent
        profile_slot_to_delete = slot_index
        previous_game_state = game_state # Stocker l'état actuel (PROFILE_MENU)
        game_state = "CONFIRM_DELETE_PROFILE"
        menu_just_opened = True # Déclencher la sélection initiale des boutons de confirmation
        deselect_all_buttons() # Désélectionner les boutons du menu précédent
        menu_entry_cooldown_timer = pygame.time.get_ticks() # Start cooldown
    else:
        print(f"Pas de données à supprimer pour le profil {slot_index + 1}.") # Optionnel : donner un feedback

# --- Nouvelle fonction pour confirmer la suppression de profil ---
def confirm_delete_profile():
    global profiles, profile_slot_to_delete, game_state, menu_just_opened, current_profile_slot, joueur, menu_entry_cooldown_timer
    if profile_slot_to_delete != -1:
        profiles[profile_slot_to_delete]["data"] = None # Marque comme supprimé
        profiles[profile_slot_to_delete]["name"] = f"Profil {profile_slot_to_delete + 1}" # Réinitialise le nom
        
        # Si le profil actuellement chargé est celui qui est supprimé, le désélectionner
        if current_profile_slot == profile_slot_to_delete:
            current_profile_slot = -1 # Aucun profil actuellement chargé
            joueur = Joueur() # Réinitialise l'objet joueur à un état par défaut

        save_profiles() # Sauvegarde la liste de profils mise à jour (avec la suppression marquée)
        print(f"Profil {profile_slot_to_delete + 1} supprimé.")
        profile_slot_to_delete = -1 # Réinitialise l'index

    # Retourne au menu de sélection de profil après la suppression
    game_state = "PROFILE_MENU"
    menu_just_opened = True # Déclenche la re-sélection des boutons du menu de profil
    menu_entry_cooldown_timer = pygame.time.get_ticks() # Start cooldown

# --- Nouvelle fonction pour annuler la suppression de profil ---
def cancel_delete_profile():
    global profile_slot_to_delete, game_state, menu_just_opened, menu_entry_cooldown_timer
    profile_slot_to_delete = -1 # Réinitialiser l'index
    game_state = "PROFILE_MENU"
    menu_just_opened = True # Déclenche la re-sélection des boutons du menu de profil
    menu_entry_cooldown_timer = pygame.time.get_ticks() # Start cooldown


# Définition des nouvelles dimensions pour les boutons généraux des menus
BUTTON_GENERAL_WIDTH = 280 # Increased width for better text fit
BUTTON_GENERAL_HEIGHT = 65 # Increased height
BUTTON_X_OFFSET_CENTER = LARGEUR // 2 - BUTTON_GENERAL_WIDTH // 2
BUTTON_VERTICAL_SPACING = 25 # Espacement entre les boutons

# Calculate base Y for in-game options menu buttons
OPTIONS_MENU_BASE_Y = HAUTEUR // 2 - 50

# Nouveau bouton pour reprendre le jeu (en haut du menu d'options)
bouton_reprendre = Bouton(
    BUTTON_X_OFFSET_CENTER, OPTIONS_MENU_BASE_Y - BUTTON_GENERAL_HEIGHT - BUTTON_VERTICAL_SPACING, BUTTON_GENERAL_WIDTH, BUTTON_GENERAL_HEIGHT,
    "Reprendre", GRIS_CLAIR,
    return_to_game
)

# Bouton Rejouer (en jeu, en haut à droite, sous le bouton Quitter)
# Ce bouton sera maintenant dans le menu d'options
bouton_rejouer_in_game = Bouton(
    BUTTON_X_OFFSET_CENTER, OPTIONS_MENU_BASE_Y, BUTTON_GENERAL_WIDTH, BUTTON_GENERAL_HEIGHT,
    "Renaître", GRIS_CLAIR, # Changement de texte ici
    reset_game_with_profile # Modifié pour utiliser la nouvelle fonction
)

# Nouveau bouton pour les contrôles (en jeu, sous le bouton Rejouer)
# Ce bouton sera maintenant dans le menu d'options
bouton_controles = Bouton(
    BUTTON_X_OFFSET_CENTER, OPTIONS_MENU_BASE_Y + BUTTON_GENERAL_HEIGHT + BUTTON_VERTICAL_SPACING, BUTTON_GENERAL_WIDTH, BUTTON_GENERAL_HEIGHT,
    "Contrôles", GRIS_CLAIR,
    show_controls_page
)

# Bouton Quitter (en jeu, en haut à droite) - Ce bouton sera maintenant dans le menu d'options
bouton_quitter = Bouton(
    BUTTON_X_OFFSET_CENTER, OPTIONS_MENU_BASE_Y + 2 * (BUTTON_GENERAL_HEIGHT + BUTTON_VERTICAL_SPACING), BUTTON_GENERAL_WIDTH, BUTTON_GENERAL_HEIGHT,
    "Retour menu principal", GRIS_CLAIR,
    return_to_main_menu
)


# Bouton Rejouer (sur l'écran GAME OVER)
bouton_rejouer = Bouton(
    BUTTON_X_OFFSET_CENTER, HAUTEUR // 2 + 50, BUTTON_GENERAL_WIDTH, BUTTON_GENERAL_HEIGHT,
    "Renaître", GRIS_CLAIR, # Changement de texte ici
    reset_game_with_profile # Modifié pour utiliser la nouvelle fonction
)

# Nouveau bouton Quitter (sur l'écran GAME OVER, sous le bouton Rejouer)
bouton_quitter_game_over = Bouton(
    BUTTON_X_OFFSET_CENTER, bouton_rejouer.rect.y + BUTTON_GENERAL_HEIGHT + BUTTON_VERTICAL_SPACING, BUTTON_GENERAL_WIDTH, BUTTON_GENERAL_HEIGHT,
    "Retour au menu", GRIS_CLAIR,
    return_to_main_menu
)

# Nouveau bouton pour le menu des compétences (en jeu, sous le bouton Contrôles)
# Ce bouton n'est plus dessiné en mode PLAYING, uniquement accessible par le joystick
bouton_skill_menu = Bouton(
    0, 0, 0, 0, # Position et taille par défaut, non pertinent car non dessiné directement
    "Compétences", GRIS_CLAIR,
    show_skill_menu
)

# Boutons du menu des compétences (positionnés à droite)
SKILL_BUTTON_WIDTH = 400 # Increased width for better text fit
SKILL_BUTTON_HEIGHT = 40
SKILL_BUTTON_X_OFFSET = LARGEUR - SKILL_BUTTON_WIDTH - 50 # 50 pixels de marge à droite

bouton_ameliorer_degats = Bouton(
    SKILL_BUTTON_X_OFFSET, HAUTEUR // 2 - 100, SKILL_BUTTON_WIDTH, SKILL_BUTTON_HEIGHT,
    "Améliorer Dégâts (+5) [1 SP]", GRIS_CLAIR,
    upgrade_degats
)
bouton_ameliorer_pv = Bouton(
    SKILL_BUTTON_X_OFFSET, HAUTEUR // 2 - 100 + 50, SKILL_BUTTON_WIDTH, SKILL_BUTTON_HEIGHT,
    "Améliorer PV Max (+10) [1 SP]", GRIS_CLAIR,
    upgrade_pv
)
bouton_ameliorer_vitesse = Bouton(
    SKILL_BUTTON_X_OFFSET, HAUTEUR // 2 - 100 + 100, SKILL_BUTTON_WIDTH, SKILL_BUTTON_HEIGHT,
    "Améliorer Vitesse (+0.5) [1 SP]", GRIS_CLAIR,
    upgrade_vitesse
)
bouton_ameliorer_dash = Bouton(
    SKILL_BUTTON_X_OFFSET, HAUTEUR // 2 - 100 + 150, SKILL_BUTTON_WIDTH, SKILL_BUTTON_HEIGHT,
    "Améliorer Dash (-50ms) [1 SP]", GRIS_CLAIR,
    upgrade_dash
)
bouton_ameliorer_tourbillon = Bouton(
    SKILL_BUTTON_X_OFFSET, HAUTEUR // 2 - 100 + 200, SKILL_BUTTON_WIDTH, SKILL_BUTTON_HEIGHT,
    "Améliorer Tourbillon (-200ms) [1 SP]", GRIS_CLAIR,
    upgrade_tourbillon
)

# Nouveaux boutons pour le menu principal
bouton_jouer_main_menu = Bouton(
    BUTTON_X_OFFSET_CENTER, HAUTEUR // 2 - 80, BUTTON_GENERAL_WIDTH, BUTTON_GENERAL_HEIGHT, # Positionné plus haut
    "Jouer", GRIS_CLAIR,
    show_profile_menu # L'action Jouer mène maintenant au menu des profils
)

# Nouveau bouton "Réglages" dans le menu principal
bouton_reglages_main_menu = Bouton(
    BUTTON_X_OFFSET_CENTER, bouton_jouer_main_menu.rect.y + BUTTON_GENERAL_HEIGHT + BUTTON_VERTICAL_SPACING, BUTTON_GENERAL_WIDTH, BUTTON_GENERAL_HEIGHT,
    "Réglages", GRIS_CLAIR,
    show_settings_menu # Action pour le menu des réglages
)

bouton_quitter_main_menu = Bouton(
    BUTTON_X_OFFSET_CENTER, bouton_reglages_main_menu.rect.y + BUTTON_GENERAL_HEIGHT + BUTTON_VERTICAL_SPACING, BUTTON_GENERAL_WIDTH, BUTTON_GENERAL_HEIGHT, # Sous le bouton Réglages
    "Quitter", GRIS_CLAIR,
    quitter_le_jeu
)

# Nouveau bouton "Retour" pour le menu des contrôles
bouton_retour_controles = Bouton(
    BUTTON_X_OFFSET_CENTER, HAUTEUR - 100, BUTTON_GENERAL_WIDTH, BUTTON_GENERAL_HEIGHT,
    "Retour", GRIS_CLAIR,
    return_to_previous_menu
)


# Boutons du menu des profils
# Define dimensions for profile buttons
PROFILE_CHARGE_BUTTON_WIDTH = 380 # Increased width for better text fit
PROFILE_DELETE_BUTTON_WIDTH = 120 # Shorter width for 'Supprimer' buttons
PROFILE_BUTTON_HEIGHT = 65
# Calculate X positions to ensure spacing and alignment
# Left button starts at center - half of total width - margin
# Total width for a pair: PROFILE_CHARGE_BUTTON_WIDTH + 20 (spacing) + PROFILE_DELETE_BUTTON_WIDTH
TOTAL_PROFILE_PAIR_WIDTH = PROFILE_CHARGE_BUTTON_WIDTH + 20 + PROFILE_DELETE_BUTTON_WIDTH
PROFILE_BUTTON_X_LEFT = LARGEUR // 2 - TOTAL_PROFILE_PAIR_WIDTH // 2 
PROFILE_BUTTON_X_RIGHT = PROFILE_BUTTON_X_LEFT + PROFILE_CHARGE_BUTTON_WIDTH + 20
PROFILE_BUTTON_VERTICAL_SPACING = 25

bouton_profil_1_charger = Bouton(
    PROFILE_BUTTON_X_LEFT, HAUTEUR // 2 - 80, PROFILE_CHARGE_BUTTON_WIDTH, PROFILE_BUTTON_HEIGHT,
    "Charger Profil 1", GRIS_CLAIR,
    lambda: select_profile(0)
)
bouton_profil_1_supprimer = Bouton(
    PROFILE_BUTTON_X_RIGHT, HAUTEUR // 2 - 80, PROFILE_DELETE_BUTTON_WIDTH, PROFILE_BUTTON_HEIGHT,
    "Supprimer", GRIS_CLAIR, # Default text, will be updated
    lambda: ask_confirm_delete_profile(0)
)

bouton_profil_2_charger = Bouton(
    PROFILE_BUTTON_X_LEFT, bouton_profil_1_charger.rect.y + PROFILE_BUTTON_HEIGHT + PROFILE_BUTTON_VERTICAL_SPACING, PROFILE_CHARGE_BUTTON_WIDTH, PROFILE_BUTTON_HEIGHT,
    "Charger Profil 2", GRIS_CLAIR,
    lambda: select_profile(1)
)
bouton_profil_2_supprimer = Bouton(
    PROFILE_BUTTON_X_RIGHT, bouton_profil_1_charger.rect.y + PROFILE_BUTTON_HEIGHT + PROFILE_BUTTON_VERTICAL_SPACING, PROFILE_DELETE_BUTTON_WIDTH, PROFILE_BUTTON_HEIGHT,
    "Supprimer", GRIS_CLAIR, # Default text, will be updated
    lambda: ask_confirm_delete_profile(1)
)

bouton_profil_3_charger = Bouton(
    PROFILE_BUTTON_X_LEFT, bouton_profil_2_charger.rect.y + PROFILE_BUTTON_HEIGHT + PROFILE_BUTTON_VERTICAL_SPACING, PROFILE_CHARGE_BUTTON_WIDTH, PROFILE_BUTTON_HEIGHT,
    "Charger Profil 3", GRIS_CLAIR,
    lambda: select_profile(2)
)
bouton_profil_3_supprimer = Bouton(
    PROFILE_BUTTON_X_RIGHT, bouton_profil_2_charger.rect.y + PROFILE_BUTTON_HEIGHT + PROFILE_BUTTON_VERTICAL_SPACING, PROFILE_DELETE_BUTTON_WIDTH, PROFILE_BUTTON_HEIGHT,
    "Supprimer", GRIS_CLAIR, # Default text, will be updated
    lambda: ask_confirm_delete_profile(2)
)

bouton_retour_profil_menu = Bouton(
    BUTTON_X_OFFSET_CENTER, bouton_profil_3_charger.rect.y + PROFILE_BUTTON_HEIGHT + PROFILE_BUTTON_VERTICAL_SPACING, BUTTON_GENERAL_WIDTH, BUTTON_GENERAL_HEIGHT,
    "Retour", GRIS_CLAIR,
    return_to_main_menu
)

# Boutons du menu Réglages
BRIGHTNESS_BUTTON_WIDTH = 80 # Reduced width for '+' and '-' buttons
BRIGHTNESS_BUTTON_HEIGHT = 60
BRIGHTNESS_BUTTON_SPACING = 20 # Spacing between +/- buttons and text

# Calculate positions dynamically for better centering around the text
# Text will be in the center, buttons on either side
BRIGHTNESS_TEXT_CENTER_Y = HAUTEUR // 2 - 30 # Y position of the brightness percentage text
BRIGHTNESS_BUTTONS_Y = BRIGHTNESS_TEXT_CENTER_Y + 40 # Buttons below the text

bouton_luminosite_moins = Bouton(
    LARGEUR // 2 - BRIGHTNESS_BUTTON_WIDTH - BRIGHTNESS_BUTTON_SPACING, BRIGHTNESS_BUTTONS_Y, BRIGHTNESS_BUTTON_WIDTH, BRIGHTNESS_BUTTON_HEIGHT,
    "-", GRIS_CLAIR,
    decrease_brightness
)

bouton_luminosite_plus = Bouton(
    LARGEUR // 2 + BRIGHTNESS_BUTTON_SPACING, BRIGHTNESS_BUTTONS_Y, BRIGHTNESS_BUTTON_WIDTH, BRIGHTNESS_BUTTON_HEIGHT,
    "+", GRIS_CLAIR,
    increase_brightness
)

bouton_retour_reglages = Bouton(
    BUTTON_X_OFFSET_CENTER, BRIGHTNESS_BUTTONS_Y + BRIGHTNESS_BUTTON_HEIGHT + BUTTON_VERTICAL_SPACING, BUTTON_GENERAL_WIDTH, BUTTON_GENERAL_HEIGHT,
    "Retour", GRIS_CLAIR,
    return_to_main_menu
)


# Confirmation buttons for deletion
CONFIRM_BUTTON_WIDTH = 200
CONFIRM_BUTTON_HEIGHT = 60
CONFIRM_BUTTON_SPACING = 50

bouton_oui_supprimer = Bouton(
    LARGEUR // 2 - CONFIRM_BUTTON_WIDTH - (CONFIRM_BUTTON_SPACING // 2), HAUTEUR // 2 + 50, CONFIRM_BUTTON_WIDTH, CONFIRM_BUTTON_HEIGHT,
    "OUI", GRIS_CLAIR,
    lambda: confirm_delete_profile()
)
bouton_non_annuler = Bouton(
    LARGEUR // 2 + (CONFIRM_BUTTON_SPACING // 2), HAUTEUR // 2 + 50, CONFIRM_BUTTON_WIDTH, CONFIRM_BUTTON_HEIGHT,
    "NON", GRIS_CLAIR,
    lambda: cancel_delete_profile()
)


# Global list of all buttons for easy management
all_buttons = [
    bouton_quitter, bouton_rejouer_in_game, bouton_controles, bouton_skill_menu, bouton_reprendre, # Added bouton_reprendre
    bouton_rejouer, bouton_quitter_game_over,
    bouton_ameliorer_degats, bouton_ameliorer_pv, bouton_ameliorer_vitesse,
    bouton_ameliorer_dash, bouton_ameliorer_tourbillon,
    bouton_jouer_main_menu, bouton_reglages_main_menu, bouton_quitter_main_menu,
    bouton_profil_1_charger, bouton_profil_1_supprimer,
    bouton_profil_2_charger, bouton_profil_2_supprimer,
    bouton_profil_3_charger, bouton_profil_3_supprimer,
    bouton_retour_profil_menu,
    bouton_luminosite_plus, bouton_luminosite_moins, bouton_retour_reglages,
    bouton_oui_supprimer, bouton_non_annuler,
    bouton_retour_controles # Add the new return button for controls
]

# New global variable to store the slot index to be deleted
profile_slot_to_delete = -1

# Global variables for profile menu selection (2D navigation)
profile_selected_row = 0
profile_selected_col = 0
profile_buttons_grid = [
    [bouton_profil_1_charger, bouton_profil_1_supprimer],
    [bouton_profil_2_charger, bouton_profil_2_supprimer],
    [bouton_profil_3_charger, bouton_profil_3_supprimer],
    [bouton_retour_profil_menu] # This row has only one column
]

# Global variables for settings menu selection (2D navigation)
settings_selected_row = 0
settings_selected_col = 0
settings_buttons_grid = [
    [bouton_luminosite_moins, bouton_luminosite_plus],
    [bouton_retour_reglages]
]


def deselect_all_buttons():
    """Deselects all buttons and resets the selected_button_index and current_selectable_buttons."""
    global selected_button_index, current_selectable_buttons
    for btn in all_buttons:
        btn.set_selected(False)
    selected_button_index = -1
    current_selectable_buttons = []


def update_button_selection(buttons_list, index_change):
    """
    Manages linear button selection.
    """
    global selected_button_index, current_selectable_buttons
    
    if not buttons_list:
        selected_button_index = -1
        current_selectable_buttons = []
        return

    if selected_button_index != -1 and current_selectable_buttons and \
       0 <= selected_button_index < len(current_selectable_buttons):
        current_selectable_buttons[selected_button_index].set_selected(False)

    current_selectable_buttons = buttons_list
    if not current_selectable_buttons:
        selected_button_index = -1
        return

    # If the current selected index is out of bounds or -1, initialize to 0
    if selected_button_index == -1 or not (0 <= selected_button_index < len(current_selectable_buttons)):
        selected_button_index = 0
    else:
        selected_button_index = (selected_button_index + index_change) % len(current_selectable_buttons)
        if selected_button_index < 0:
            selected_button_index += len(current_selectable_buttons)

    current_selectable_buttons[selected_button_index].set_selected(True)


def update_profile_button_selection(delta_row, delta_col):
    """
    Manages 2D button selection specifically for the PROFILE_MENU.
    """
    global profile_selected_row, profile_selected_col, selected_button_index, current_selectable_buttons

    # Deselect previously selected button
    if current_selectable_buttons and 0 <= selected_button_index < len(current_selectable_buttons):
        current_selectable_buttons[selected_button_index].set_selected(False)

    # Calculate new row and column
    new_row = profile_selected_row + delta_row
    new_col = profile_selected_col + delta_col

    # Handle row wrapping
    num_rows = len(profile_buttons_grid)
    new_row = new_row % num_rows
    if new_row < 0:
        new_row += num_rows

    # Handle column wrapping/limits for current row
    num_cols_in_new_row = len(profile_buttons_grid[new_row])
    if num_cols_in_new_row == 1: # If it's the 'Retour' button row
        new_col = 0 # Force column to 0 for single-column rows
    else: # For 2-column rows
        new_col = new_col % num_cols_in_new_row
        if new_col < 0:
            new_col += num_cols_in_new_row

    profile_selected_row = new_row
    profile_selected_col = new_col

    # Set the new selected button and update current_selectable_buttons for activation
    current_selectable_buttons = profile_buttons_grid[profile_selected_row]
    selected_button_index = profile_selected_col # The index within the sub-list (row)

    if current_selectable_buttons and 0 <= selected_button_index < len(current_selectable_buttons):
        current_selectable_buttons[selected_button_index].set_selected(True)
    else: # Fallback if for some reason selection is invalid
        selected_button_index = -1

def update_settings_button_selection(delta_row, delta_col):
    """
    Manages 2D button selection specifically for the SETTINGS_MENU.
    """
    global settings_selected_row, settings_selected_col, selected_button_index, current_selectable_buttons

    # Deselect previously selected button
    if current_selectable_buttons and 0 <= selected_button_index < len(current_selectable_buttons):
        current_selectable_buttons[selected_button_index].set_selected(False)

    # Calculate new row and column
    new_row = settings_selected_row + delta_row
    new_col = settings_selected_col + delta_col

    # Handle row wrapping
    num_rows = len(settings_buttons_grid)
    new_row = new_row % num_rows
    if new_row < 0:
        new_row += num_rows

    # Handle column wrapping/limits for current row
    num_cols_in_new_row = len(settings_buttons_grid[new_row])
    if num_cols_in_new_row == 1: # If it's the 'Retour' button row
        new_col = 0 # Force column to 0 for single-column rows
    else: # For 2-column rows
        new_col = new_col % num_cols_in_new_row
        if new_col < 0:
            new_col += num_cols_in_new_row

    settings_selected_row = new_row
    settings_selected_col = new_col

    # Set the new selected button and update current_selectable_buttons for activation
    current_selectable_buttons = settings_buttons_grid[settings_selected_row]
    selected_button_index = settings_selected_col # The index within the sub-list (row)

    if current_selectable_buttons and 0 <= selected_button_index < len(current_selectable_buttons):
        current_selectable_buttons[selected_button_index].set_selected(True)
    else: # Fallback if for some reason selection is invalid
        selected_button_index = -1


def activate_selected_button():
    global selected_button_index, current_selectable_buttons
    # Ensure selected_button_index is valid for the current list before proceeding
    if current_selectable_buttons and 0 <= selected_button_index < len(current_selectable_buttons):
        button_to_activate = current_selectable_buttons[selected_button_index]
        button_to_activate.action()
        # The game_loop will react to the game_state change and handle deselecting/re-selecting.

def load_settings():
    global brightness_level
    # Use a temporary file for atomic loading
    files_to_try = [SETTINGS_FILE, TEMP_SETTINGS_FILE]
    loaded_successfully = False
    
    for filepath in files_to_try:
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    settings_data = json.load(f)
                    if "brightness_level" in settings_data and isinstance(settings_data["brightness_level"], (int, float)):
                        brightness_level = settings_data["brightness_level"]
                        loaded_successfully = True
                        print(f"Réglages chargés depuis {filepath}.")
                        break
                    else:
                        print(f"Format de données de réglages inattendu dans {filepath}.")
            except json.JSONDecodeError:
                print(f"Erreur de lecture du fichier de réglages {filepath}. Fichier corrompu ou incomplet.")
            except Exception as e:
                print(f"Erreur inattendue lors du chargement des réglages depuis {filepath}: {e}")
        else:
            print(f"Fichier {filepath} non trouvé.")

    if not loaded_successfully:
        print("Aucun réglage valide n'a pu être chargé. Utilisation des réglages par défaut.")
        brightness_level = 1.0 # Default brightness if nothing is loaded

    # Clean up temp file if main file was loaded successfully
    if loaded_successfully and os.path.exists(TEMP_SETTINGS_FILE):
        try:
            os.remove(TEMP_SETTINGS_FILE)
            print(f"Ancien fichier temporaire {TEMP_SETTINGS_FILE} supprimé.")
        except OSError as e:
            print(f"Erreur lors du nettoyage du fichier temporaire après chargement réussi: {e}")

def save_settings():
    global brightness_level
    settings_data = {
        "brightness_level": brightness_level
    }
    try:
        temp_dir = os.path.dirname(SETTINGS_FILE)
        if temp_dir and not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        temp_filepath = os.path.join(temp_dir, os.path.basename(SETTINGS_FILE) + ".tmp")
        
        with open(temp_filepath, 'w') as f:
            json.dump(settings_data, f, indent=4)
            f.flush()
            os.fsync(f.fileno())
        
        if not os.path.exists(temp_filepath) or os.path.getsize(temp_filepath) == 0:
            print(f"Erreur: Le fichier temporaire {temp_filepath} est vide ou n'a pas été créé correctement.")
            return
            
        if os.path.exists(SETTINGS_FILE):
            try:
                os.remove(SETTINGS_FILE)
                print(f"Ancien fichier de réglages {SETTINGS_FILE} supprimé.")
            except OSError as e:
                print(f"Erreur lors de la suppression de l'ancien fichier de réglages: {e}")

        os.rename(temp_filepath, SETTINGS_FILE)
        print("Réglages sauvegardés avec succès.")

    except Exception as e:
        print(f"Erreur lors de la sauvegarde des réglages: {e}")
        if os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
                print(f"Fichier temporaire {temp_filepath} supprimé suite à l'erreur.")
            except OSError as cleanup_e:
                print(f"Erreur lors du nettoyage du fichier temporaire: {cleanup_e}")


pygame.joystick.init()
if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Manette détectée : {joystick.get_name()}")
else:
    print("Aucune manette détectée.")

# Initialisation du jeu pour commencer sur le menu principal
load_profiles() # Charger les profils au démarrage
load_settings() # Charger les réglages au démarrage (avant de créer la fenêtre si la luminosité affecte ça)
joueur = Joueur() # Initialiser un joueur par défaut pour éviter les erreurs avant le chargement

def game_loop():
    global running, last_potion_spawn_time, round_number, game_state, joueur, joystick, selected_button_index, current_selectable_buttons, joystick_menu_active
    global round_start_cooldown_active, round_start_cooldown_timer, player_death_time, menu_just_opened, previous_game_state, profiles
    global current_game_session_start_time, profile_slot_to_delete, profile_selected_row, profile_selected_col, brightness_level
    global settings_selected_row, settings_selected_col, menu_entry_cooldown_timer

    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    font_round = pygame.font.Font(None, 48)
    font_level = pygame.font.Font(None, 28)
    font_controls = pygame.font.Font(None, 30)
    font_skill_menu = pygame.font.Font(None, 22)
    font_title = pygame.font.Font(None, 72)
    font_profile_details = pygame.font.Font(None, 24) # Smaller font for profile details

    pygame.mouse.set_visible(False)

    if game_state == "MAIN_MENU":
        joystick_menu_active = True
        menu_just_opened = True
        menu_entry_cooldown_timer = pygame.time.get_ticks() # Start cooldown for initial menu

    while running:
        current_time = pygame.time.get_ticks()

        buttons_to_draw = []

        if game_state == "PLAYING":
            buttons_to_draw = []
            current_selectable_buttons = []

            if current_game_session_start_time != 0:
                time_in_this_frame = clock.get_time()
                joueur.total_play_time += time_in_this_frame

        elif game_state == "GAME_OVER":
            buttons_to_draw = [bouton_rejouer, bouton_quitter_game_over]
            current_selectable_buttons = buttons_to_draw

        elif game_state == "CONTROLS":
            buttons_to_draw = [bouton_retour_controles] # Add the return button to draw
            current_selectable_buttons = buttons_to_draw # Make it selectable
        elif game_state == "SKILL_MENU":
            buttons_to_draw = [bouton_ameliorer_degats, bouton_ameliorer_pv, bouton_ameliorer_vitesse,
                                            bouton_ameliorer_dash, bouton_ameliorer_tourbillon] 
            current_selectable_buttons = buttons_to_draw

        elif game_state == "MAIN_MENU":
            buttons_to_draw = [bouton_jouer_main_menu, bouton_reglages_main_menu, bouton_quitter_main_menu]
            current_selectable_buttons = buttons_to_draw
        
        elif game_state == "OPTIONS_MENU":
            # Buttons are already positioned correctly by their global definition
            buttons_to_draw = [bouton_reprendre, bouton_rejouer_in_game, bouton_controles, bouton_quitter] # Added bouton_reprendre
            current_selectable_buttons = buttons_to_draw
        
        elif game_state == "PROFILE_MENU":
            buttons_to_draw = [bouton_profil_1_charger, bouton_profil_1_supprimer,
                               bouton_profil_2_charger, bouton_profil_2_supprimer,
                               bouton_profil_3_charger, bouton_profil_3_supprimer,
                               bouton_retour_profil_menu]
            
            for i in range(MAX_PROFILES):
                profile_data_for_slot = profiles[i]["data"]
                charger_btn = profile_buttons_grid[i][0]
                supprimer_btn = profile_buttons_grid[i][1]

                if profile_data_for_slot is not None:
                    # Calculate total play time in H M S
                    total_seconds = profile_data_for_slot.get('total_play_time', 0) // 1000
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    seconds = total_seconds % 60
                    
                    play_time_str = ""
                    if hours > 0:
                        play_time_str += f"{int(hours)}h "
                    play_time_str += f"{int(minutes)}m {int(seconds)}s"

                    charger_btn.texte = (f"{profile_data_for_slot.get('profile_name', f'Profil {i+1}')} "
                                         f"(Manche {profile_data_for_slot.get('highest_round', 0)}) | Temps: {play_time_str}")
                    # Update the font for the charger button to fit the longer text
                    charger_btn.font = pygame.font.Font(None, 20) # Smaller font for more details
                    supprimer_btn.texte = "Supprimer"
                    supprimer_btn.couleur_normale = ROUGE
                else:
                    charger_btn.texte = f"Créer Nouveau Profil {i+1}"
                    charger_btn.font = pygame.font.Font(None, 30) # Reset to default font if new profile
                    supprimer_btn.texte = "Vide"
                    supprimer_btn.couleur_normale = GRIS_FONCE

        elif game_state == "SETTINGS_MENU":
            buttons_to_draw = [bouton_luminosite_moins, bouton_luminosite_plus, bouton_retour_reglages]

        elif game_state == "CONFIRM_DELETE_PROFILE":
            buttons_to_draw = [bouton_oui_supprimer, bouton_non_annuler]
            current_selectable_buttons = buttons_to_draw

        else: # PLAYER_DEATH_ANIMATION
            buttons_to_draw = []
            current_selectable_buttons = []

        if menu_just_opened:
            deselect_all_buttons()
            if game_state == "PROFILE_MENU":
                profile_selected_row = 0
                profile_selected_col = 0
                update_profile_button_selection(0, 0)
            elif game_state == "SETTINGS_MENU":
                settings_selected_row = 0
                settings_selected_col = 0
                update_settings_button_selection(0, 0)
            elif game_state == "OPTIONS_MENU" and previous_game_state == "CONTROLS": # Special case for returning from controls
                current_selectable_buttons = buttons_to_draw # This will be [reprendre, renaître, controles, quitter]
                selected_button_index = 2 # Select 'Contrôles' button (index 2 now)
                if current_selectable_buttons:
                    current_selectable_buttons[selected_button_index].set_selected(True)
            elif game_state == "OPTIONS_MENU" and previous_game_state == "PLAYING": # Special case for entering from play
                current_selectable_buttons = buttons_to_draw
                selected_button_index = 0 # Select 'Reprendre' button (index 0)
                if current_selectable_buttons:
                    current_selectable_buttons[selected_button_index].set_selected(True)
            elif game_state == "MAIN_MENU" and previous_game_state in ["SETTINGS_MENU", "PROFILE_MENU", "GAME_OVER"]:
                # When returning to main menu from Settings, Profile menu, or Game Over
                current_selectable_buttons = buttons_to_draw # This will be [jouer, reglages, quitter]
                if previous_game_state == "SETTINGS_MENU":
                    selected_button_index = 1 # Select 'Réglages' button (index 1)
                elif previous_game_state == "PROFILE_MENU":
                    selected_button_index = 0 # Select 'Jouer' button (index 0)
                elif previous_game_state == "GAME_OVER":
                    selected_button_index = 0 # Select 'Jouer' button (index 0)
                else:
                    selected_button_index = 0 # Default to 'Jouer' for other cases
                
                if current_selectable_buttons:
                    current_selectable_buttons[selected_button_index].set_selected(True)
            else: # For other menus with linear button selection or no selection like CONTROLS
                current_selectable_buttons = buttons_to_draw # Make sure this list is correctly assigned
                if current_selectable_buttons: # Check if there are buttons to select
                    selected_button_index = 0
                    current_selectable_buttons[selected_button_index].set_selected(True)
            menu_just_opened = False

        joystick_axes_values = None
        if joystick and joystick.get_init():
            if joystick.get_numaxes() >= 2:
                joystick_axes_values = [joystick.get_axis(0), joystick.get_axis(1)] 
            else:
                joystick_axes_values = [0.0, 0.0]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if joystick:
                if event.type == pygame.JOYBUTTONDOWN:
                    # Apply cooldown to prevent immediate navigation after menu opens
                    if current_time - menu_entry_cooldown_timer < MENU_ENTRY_COOLDOWN_DURATION:
                        continue # Skip joystick button processing for a short duration after menu opens

                    if joystick_menu_active:
                        if game_state == "PROFILE_MENU":
                            if event.button == 0:
                                if profile_selected_row < len(profile_buttons_grid) and \
                                   profile_selected_col < len(profile_buttons_grid[profile_selected_row]):
                                    profile_buttons_grid[profile_selected_row][profile_selected_col].action()
                            elif event.button == 11: # D-pad Haut
                                update_profile_button_selection(-1, 0) 
                            elif event.button == 12: # D-pad Bas
                                update_profile_button_selection(1, 0) 
                            elif event.button == 14: # D-pad Gauche
                                update_profile_button_selection(0, -1)
                            elif event.button == 13: # D-pad Droite
                                update_profile_button_selection(0, 1)
                            elif event.button == 6 or event.button == 7: # Back or Start button
                                return_to_main_menu()
                        
                        elif game_state == "SETTINGS_MENU":
                            if event.button == 0:
                                if settings_selected_row < len(settings_buttons_grid) and \
                                   settings_selected_col < len(settings_buttons_grid[settings_selected_row]):
                                    settings_buttons_grid[settings_selected_row][settings_selected_col].action()
                            elif event.button == 11: # D-pad Haut
                                update_settings_button_selection(-1, 0)
                            elif event.button == 12: # D-pad Bas
                                update_settings_button_selection(1, 0)
                            elif event.button == 14: # D-pad Gauche (moves LEFT)
                                update_settings_button_selection(0, -1)
                            elif event.button == 13: # D-pad Droite (moves RIGHT)
                                update_settings_button_selection(0, 1)
                            elif event.button == 6 or event.button == 7: # Back or Start button
                                return_to_main_menu()

                        elif game_state == "CONFIRM_DELETE_PROFILE":
                            if event.button == 0:
                                activate_selected_button()
                            elif event.button == 1:
                                cancel_delete_profile()
                            elif event.button == 14:
                                update_button_selection(current_selectable_buttons, -1)
                            elif event.button == 13:
                                update_button_selection(current_selectable_buttons, 1)
                        
                        elif event.button == 0: # A button
                            activate_selected_button()
                        elif event.button == 11: # D-pad Haut
                            update_button_selection(current_selectable_buttons, -1)
                        elif event.button == 12: # D-pad Bas
                            update_button_selection(current_selectable_buttons, 1)
                        
                        # Handle the new return button in CONTROLS menu
                        if game_state == "CONTROLS":
                            # The 'Retour' button is now handled by joystick button 0 (A)
                            # so remove the direct check for 6 or 7 here
                            pass 
                        elif game_state == "SKILL_MENU":
                            if event.button == 4: # Specific skill menu return button
                                return_to_game()
                        elif game_state == "OPTIONS_MENU":
                            if event.button == 6: # Back or Start button
                                return_to_game()
                        elif game_state == "MAIN_MENU":
                            pass # Main menu doesn't need a special back action
                                
                        continue

                    elif game_state == "PLAYING":
                        if event.button == 4: # Specific skill menu button
                            show_skill_menu()
                            joystick_menu_active = True
                        elif event.button == 6: # Back button
                            show_options_menu()
                            joystick_menu_active = True
                        elif event.button == 9: # Left Bumper for dash
                            joueur.dash(joystick_axes=joystick_axes_values)
                        elif event.button == 10: # Right Bumper for whirlwind attack
                            joueur.whirlwind_attack()
                        else: # Face buttons for normal attack
                            direction_attaque_joystick = pygame.math.Vector2(0, 0)
                            if event.button == 2: # X button (up)
                                direction_attaque_joystick.y = -1
                            elif event.button == 3: # Y button (left)
                                direction_attaque_joystick.x = -1
                            elif event.button == 0: # A button (right)
                                direction_attaque_joystick.x = 1
                            elif event.button == 1: # B button (down)
                                direction_attaque_joystick.y = 1

                            if direction_attaque_joystick.length() > 0:
                                joueur.attaquer(monstres, direction_attaque_joystick.normalize())
            
        if game_state == "PLAYING":
            if round_start_cooldown_active:
                if current_time - round_start_cooldown_timer >= ROUND_COOLDOWN_DURATION:
                    round_start_cooldown_active = False
            
            joueur.deplacement(joystick_axes_values)

            for monstre in monstres:
                if joueur.alive():
                    if isinstance(monstre, MonstreStatique):
                        monstre.update(joueur.rect, round_start_cooldown_active)
                    else:
                        if not round_start_cooldown_active:
                            monstre.mouvement(joueur.rect)
                            monstre.attaquer(joueur) 
                else:
                    monstre.vitesse = 0 

            tous_les_sprites.update() # Met à jour tous les sprites qui n'ont pas de logique spécifique dans la boucle (comme Player, Particles, Projectiles)
            potions_de_soin.update()
            particles.update()
            projectiles.update()

            if current_time - last_potion_spawn_time > potion_spawn_interval and len(potions_de_soin) < max_potions_on_screen:
                x = random.randint(50, LARGEUR - 50)
                y = random.randint(50, HAUTEUR - 100)
                potion = PotionDeSoin(x, y)
                tous_les_sprites.add(potion)
                potions_de_soin.add(potion)
                last_potion_spawn_time = current_time

            potions_ramassees = pygame.sprite.spritecollide(joueur, potions_de_soin, True)
            for potion in potions_ramassees:
                joueur.prendre_soin(potion.montant_soin)
                for _ in range(10):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(1, 4)
                    velocity = (speed * math.cos(angle), speed * math.sin(angle) - random.uniform(0, 1))
                    particle = Particle(potion.rect.centerx, potion.rect.centery, GLOW_VERT_PARTICULES, random.randint(2, 5), random.randint(300, 700), velocity)
                    tous_les_sprites.add(particle)
                    particles.add(particle)
            
            projectiles_touches = pygame.sprite.spritecollide(joueur, projectiles, True)
            for projectile in projectiles_touches:
                joueur.prendre_degats(10)

            if joueur.pv <= 0 and joueur.alive():
                game_state = "PLAYER_DEATH_ANIMATION"
                player_death_time = current_time
                if current_profile_slot != -1:
                    joueur.highest_round = max(joueur.highest_round, round_number)
                save_current_profile_data()
                for _ in range(50):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(2, 8)
                    velocity = (speed * math.cos(angle), speed * math.sin(angle) - random.uniform(0, 2))
                    particle = Particle(joueur.rect.centerx, joueur.rect.centery, GLOW_BLEU_PARTICULES, random.randint(3, 7), random.randint(500, 1500), velocity)
                    tous_les_sprites.add(particle)
                    particles.add(particle)
                joueur.kill()

            if not monstres and game_state == "PLAYING":
                round_number += 1
                nombre_nouveaux_monstres = random.randint(1 + round_number, 4 + round_number)
                creer_monstre(nombre_nouveaux_monstres, joueur, tous_les_sprites, monstres, particles, projectiles, round_start_cooldown_active)
                round_start_cooldown_active = True
                round_start_cooldown_timer = pygame.time.get_ticks()

        elif game_state == "PLAYER_DEATH_ANIMATION":
            particles.update()

            if current_time - player_death_time >= PLAYER_DEATH_ANIMATION_DURATION:
                game_state = "GAME_OVER"
                menu_just_opened = True
                deselect_all_buttons()
                joystick_menu_active = True
                menu_entry_cooldown_timer = pygame.time.get_ticks()
                for monstre in monstres:
                    monstre.kill()
                monstres.empty()

        # --- Dessin ---
        if game_state == "MAIN_MENU":
            FENETRE.fill(GRIS_FONCE)
            title_text = font_title.render("Dungeon Crow", True, BLANC)
            title_rect = title_text.get_rect(center=(LARGEUR // 2, HAUTEUR // 2 - 150))
            FENETRE.blit(title_text, title_rect)
            
            bouton_jouer_main_menu.dessiner(FENETRE)
            bouton_reglages_main_menu.dessiner(FENETRE)
            bouton_quitter_main_menu.dessiner(FENETRE)

        elif game_state == "PLAYER_DEATH_ANIMATION":
            FENETRE.blit(ARRIERE_FANCHE_IMAGE, (0, 0))

            time_since_death = current_time - player_death_time
            fade_progress = min(1.0, time_since_death / PLAYER_DEATH_ANIMATION_DURATION)

            overlay_alpha = int(255 * (1.0 - brightness_level) + (255 * fade_progress * brightness_level)) # Ensure overlay respects brightness
            overlay_surface = pygame.Surface((LARGEUR, HAUTEUR), pygame.SRCALPHA)
            overlay_surface.fill((0, 0, 0, overlay_alpha))
            FENETRE.blit(overlay_surface, (0, 0))

            text_fade_start_ratio = 0.5
            if fade_progress >= text_fade_start_ratio:
                text_fade_progress = (fade_progress - text_fade_start_ratio) / (1.0 - text_fade_start_ratio)
                text_alpha = int(255 * text_fade_progress)
                
                texte_fin = font_round.render(f"GAME OVER - Vous avez atteint la manche {round_number} !", True, ROUGE)
                texte_fin.set_alpha(text_alpha)

                texte_rect = texte_fin.get_rect(center=(LARGEUR // 2, HAUTEUR // 2 - 30))
                FENETRE.blit(texte_fin, texte_rect)

        elif game_state == "CONTROLS":
            FENETRE.fill(GRIS_FONCE)
            
            texte_titre = font_round.render("Contrôles du Jeu", True, BLANC)
            FENETRE.blit(texte_titre, (LARGEUR // 2 - texte_titre.get_width() // 2, 50))

            controls_text = [
                "Manette (Xbox/Générique):",
                "  Déplacement: Stick gauche",
                "  Dash: Bouton X (Carré sur PlayStation) / Bouton 9",
                "  Attaque Tourbillon: Gâchette gauche (L1/LB)",
                "  Attaque normale: Boutons de face (Y: Haut, X: Gauche, B: Droite, A: Bas)",
                "  Menu/Pause (Options): Bouton Back (bouton 6)",
                "  Menu Compétences: Bouton 15",
                "  Navigation menu: D-pad Haut/Bas (pour les menus linéaires)",
                "  Navigation Luminosité: D-pad Gauche/Droite",
                "  Sélection menu: Bouton A (Croix sur PlayStation)",
                "",
            ]

            y_offset = 150
            for line in controls_text:
                text_surface = font_controls.render(line, True, BLANC)
                FENETRE.blit(text_surface, (LARGEUR // 2 - text_surface.get_width() // 2, y_offset))
                y_offset += 30
            
            bouton_retour_controles.dessiner(FENETRE) # Draw the new return button
            
        elif game_state == "SKILL_MENU":
            FENETRE.fill(GRIS_FONCE)
            
            texte_titre = font_round.render("Menu des Compétences", True, BLANC)
            FENETRE.blit(texte_titre, (LARGEUR // 2 - texte_titre.get_width() // 2, 50))

            texte_skill_points = font_skill_menu.render(f"Points de compétence: {joueur.skill_points}", True, JAUNE)
            FENETRE.blit(texte_skill_points, (LARGEUR // 2 - texte_skill_points.get_width() // 2, 100))

            TEXT_X_OFFSET = 50
            
            y_offset_degats = bouton_ameliorer_degats.rect.centery - font_skill_menu.get_height() // 2
            y_offset_pv = bouton_ameliorer_pv.rect.centery - font_skill_menu.get_height() // 2
            y_offset_vitesse = bouton_ameliorer_vitesse.rect.centery - font_skill_menu.get_height() // 2
            y_offset_dash = bouton_ameliorer_dash.rect.centery - font_skill_menu.get_height() // 2
            y_offset_tourbillon = bouton_ameliorer_tourbillon.rect.centery - font_skill_menu.get_height() // 2

            texte_stats = [
                (f"Dégâts: {joueur.degats_attaque} (Niv {joueur.upgrade_levels['degats']})", y_offset_degats),
                (f"PV Max: {joueur.pv_max} (Niv {joueur.upgrade_levels['pv_max']})", y_offset_pv),
                (f"Vitesse: {joueur.vitesse:.1f} (Niv {joueur.upgrade_levels['vitesse']})", y_offset_vitesse),
                (f"Recharge Dash: {joueur.recharge_dash}ms (Niv {joueur.upgrade_levels['recharge_dash']})", y_offset_dash),
                (f"Recharge Tourbillon: {joueur.recharge_tourbillon}ms (Niv {joueur.upgrade_levels['recharge_tourbillon']})", y_offset_tourbillon)
            ]
            for stat_line, y_pos in texte_stats:
                text_surface = font_skill_menu.render(stat_line, True, BLANC)
                FENETRE.blit(text_surface, (TEXT_X_OFFSET, y_pos))


            bouton_ameliorer_degats.dessiner(FENETRE)
            bouton_ameliorer_pv.dessiner(FENETRE)
            bouton_ameliorer_vitesse.dessiner(FENETRE)
            bouton_ameliorer_dash.dessiner(FENETRE)
            bouton_ameliorer_tourbillon.dessiner(FENETRE)

        elif game_state == "OPTIONS_MENU":
            FENETRE.fill(GRIS_FONCE)
            texte_titre = font_round.render("Options", True, BLANC)
            texte_titre_rect = texte_titre.get_rect(center=(LARGEUR // 2, 50))
            FENETRE.blit(texte_titre, texte_titre_rect)

            bouton_reprendre.dessiner(FENETRE) # Draw the new "Reprendre" button
            bouton_rejouer_in_game.dessiner(FENETRE)
            bouton_controles.dessiner(FENETRE)
            bouton_quitter.dessiner(FENETRE)
            
        elif game_state == "PROFILE_MENU":
            FENETRE.fill(GRIS_FONCE)
            title_text = font_title.render("Sélection du Profil", True, BLANC)
            title_rect = title_text.get_rect(center=(LARGEUR // 2, HAUTEUR // 2 - 150))
            FENETRE.blit(title_text, title_rect)

            bouton_profil_1_charger.dessiner(FENETRE)
            bouton_profil_1_supprimer.dessiner(FENETRE)
            bouton_profil_2_charger.dessiner(FENETRE)
            bouton_profil_2_supprimer.dessiner(FENETRE)
            bouton_profil_3_charger.dessiner(FENETRE)
            bouton_profil_3_supprimer.dessiner(FENETRE)
            bouton_retour_profil_menu.dessiner(FENETRE)

        elif game_state == "SETTINGS_MENU":
            FENETRE.fill(GRIS_FONCE)
            texte_titre = font_round.render("Réglages", True, BLANC)
            FENETRE.blit(texte_titre, (LARGEUR // 2 - texte_titre.get_width() // 2, 50))

            texte_luminosite = font.render(f"Luminosité: {int(brightness_level * 100)}%", True, BLANC)
            texte_luminosite_rect = texte_luminosite.get_rect(center=(LARGEUR // 2, BRIGHTNESS_TEXT_CENTER_Y))
            FENETRE.blit(texte_luminosite, texte_luminosite_rect)

            bouton_luminosite_moins.dessiner(FENETRE)
            bouton_luminosite_plus.dessiner(FENETRE)
            bouton_retour_reglages.dessiner(FENETRE)

        elif game_state == "CONFIRM_DELETE_PROFILE":
            FENETRE.fill(GRIS_FONCE)
            texte_confirm = font_round.render(f"Voulez-vous vraiment supprimer le profil {profile_slot_to_delete + 1} ?", True, BLANC)
            texte_rect = texte_confirm.get_rect(center=(LARGEUR // 2, HAUTEUR // 2 - 50))
            FENETRE.blit(texte_confirm, texte_rect)

            bouton_oui_supprimer.dessiner(FENETRE)
            bouton_non_annuler.dessiner(FENETRE)

        else: # game_state == "PLAYING" ou "PLAYER_DEATH_ANIMATION"
            FENETRE.blit(ARRIERE_PLAN_IMAGE, (0, 0))
        
        if game_state == "PLAYING":
            for i in range(2):
                glow_surface = pygame.Surface(joueur.image.get_size(), pygame.SRCALPHA)
                glow_surface.blit(joueur.image, (0,0))
                glow_color_with_alpha = (GLOW_BLEU[0], GLOW_BLEU[1], GLOW_BLEU[2], GLOW_BLEU[3] // (i + 1))
                glow_surface.fill(glow_color_with_alpha, special_flags=pygame.BLEND_RGBA_ADD)
                
                scaled_glow = pygame.transform.smoothscale(glow_surface, (joueur.rect.width + i * 6, joueur.rect.height + i * 6))
                scaled_glow_rect = scaled_glow.get_rect(center=joueur.rect.center)
                FENETRE.blit(scaled_glow, scaled_glow_rect)
            FENETRE.blit(joueur.image, joueur.rect)

            for monstre in monstres:
                monstre.draw(FENETRE)

            potions_de_soin.draw(FENETRE)

            projectiles.draw(FENETRE)

            joueur.dessiner_epee(FENETRE)

            joueur.dessiner_barre_vie(FENETRE)
            for monstre in monstres:
                monstre.dessiner_barre_vie(FENETRE)

            joueur.dessiner_dash_recharge_indicator(FENETRE)
            joueur.dessiner_whirlwind_indicator(FENETRE)

            texte_pv_joueur = font.render(f"PV: {joueur.pv}", True, NOIR)
            FENETRE.blit(texte_pv_joueur, (10, 10))

            texte_manche = font_round.render(f"Manche: {round_number}", True, NOIR)
            FENETRE.blit(texte_manche, (LARGEUR // 2 - texte_manche.get_width() // 2, 10))

            texte_level = font_level.render(f"Niveau: {joueur.level}", True, NOIR)
            FENETRE.blit(texte_level, (10, 40))
            
            xp_bar_width = 150
            xp_bar_height = 10
            xp_bar_x = 10
            xp_bar_y = 65
            pygame.draw.rect(FENETRE, GRIS_FONCE, (xp_bar_x, xp_bar_y, xp_bar_width, xp_bar_height), 2)
            xp_fill_width = (joueur.xp / joueur.xp_needed_for_level_up) * xp_bar_width
            pygame.draw.rect(FENETRE, COULEUR_XP_BARRE, (xp_bar_x, xp_bar_y, xp_fill_width, xp_bar_height))
            
            texte_xp = font_level.render(f"XP: {joueur.xp}/{joueur.xp_needed_for_level_up}", True, NOIR)
            FENETRE.blit(texte_xp, (xp_bar_x + xp_bar_width + 5, xp_bar_y - 5))


            if round_start_cooldown_active:
                temps_restant = max(0, ROUND_COOLDOWN_DURATION - (current_time - round_start_cooldown_timer))
                texte_cooldown = font.render(f"Nouvelle manche dans: {temps_restant / 1000:.1f}s", True, NOIR)
                FENETRE.blit(texte_cooldown, (LARGEUR // 2 - texte_cooldown.get_width() // 2, HAUTEUR // 2 - 50))


        elif game_state == "GAME_OVER":
            FENETRE.fill(NOIR) 
            texte_fin = font_round.render(f"GAME OVER - Vous avez atteint la manche {round_number} !", True, ROUGE)
            texte_rect = texte_fin.get_rect(center=(LARGEUR // 2, HAUTEUR // 2 - 30))
            FENETRE.blit(texte_fin, texte_rect)
            
            bouton_rejouer.dessiner(FENETRE)
            bouton_quitter_game_over.dessiner(FENETRE)

        if game_state == "PLAYING" or game_state == "PLAYER_DEATH_ANIMATION":
            particles.draw(FENETRE)

        # Apply brightness overlay
        if brightness_level < 1.0:
            darkness_alpha = int(255 * (1.0 - brightness_level))
            brightness_surface.fill((0, 0, 0, darkness_alpha))
            FENETRE.blit(brightness_surface, (0, 0))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    game_loop()
