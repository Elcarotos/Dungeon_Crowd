import pygame
import random
import math
import array

# --- Couleurs (doivent correspondre à celles de votre jeu principal) ---
NOIR = (0, 0, 0)
ROUGE = (255, 0, 0)
VERT = (0, 255, 0)
BLANC = (255, 255, 255)
GLOW_ROUGE = (255, 50, 50, 150)
GLOW_ORANGE = (255, 165, 0, 80)
# Nouvelle couleur pour le monstre kamikaze et ses particules
COULEUR_KAMIKAZE = (0, 200, 0) # Vert foncé
GLOW_VERT_EXPLOSION = (0, 255, 0, 180) # Vert brillant pour l'explosion


# --- Dimensions des images (doivent correspondre à celles de votre jeu principal) ---
# Ces surfaces sont créées ici pour que le module soit autonome.
# Dans votre jeu principal, vous devriez les définir une seule fois.
MONSTRE_IMAGE = pygame.Surface((50, 50))
MONSTRE_IMAGE.fill(ROUGE)

MONSTRE_RAPIDE_IMAGE = pygame.Surface((40, 40))
MONSTRE_RAPIDE_IMAGE.fill((255, 100, 0))

MONSTRE_STATIQUE_IMAGE = pygame.Surface((70, 70))
MONSTRE_STATIQUE_IMAGE.fill((100, 0, 100))

# Nouvelle image pour le monstre kamikaze
MONSTRE_KAMIKAZE_IMAGE = pygame.Surface((45, 45))
MONSTRE_KAMIKAZE_IMAGE.fill(COULEUR_KAMIKAZE)


PROJECTILE_IMAGE = pygame.Surface((15, 15), pygame.SRCALPHA)
pygame.draw.circle(PROJECTILE_IMAGE, (255, 255, 0), (7, 7), 7) # Projectile jaune

# --- Sons (utilisez des sons factices pour l'autonomie du module) ---
# Vous devrez utiliser les sons de votre jeu principal lors de l'intégration.
def create_dummy_sound(frequency=440, duration=100, volume=0.1):
    # Ceci est un substitut pour le développement autonome du module.
    # Dans le jeu principal, vous devriez les définir une seule fois.
    # Assurez-vous que pygame.mixer.init() est appelé avant d'utiliser cette fonction.
    try:
        sample_rate = pygame.mixer.get_init()[0]
    except:
        # Fallback if mixer is not initialized for standalone testing
        sample_rate = 44100
    bits = 16
    max_sample = 2**(bits - 1) - 1
    num_samples = int(sample_rate * duration / 1000.0)
    samples = []
    for i in range(num_samples):
        t = float(i) / sample_rate
        sample_value = int(volume * max_sample * math.sin(2 * math.pi * frequency * t))
        samples.append(sample_value)
    sound_array = array.array('h', samples)
    return pygame.mixer.Sound(sound_array)

# Ces lignes sont maintenant conditionnelles pour l'exécution autonome
# Dans Dungeon_Debug.py, assurez-vous que pygame.mixer.init() est appelé AVANT l'importation de ce module.
# Le jeu principal doit gérer ses propres sons.
try:
    SON_DEGATS = create_dummy_sound(220, 75)
    SON_PROJECTILE = create_dummy_sound(550, 30)
    # Nouveau son pour l'explosion du kamikaze
    SON_EXPLOSION = create_dummy_sound(100, 200, volume=0.3) # Basse fréquence pour une explosion
except pygame.error:
    # Fallback pour le mode non-test ou si le mixer n'est pas initialisé
    print("Pygame mixer non initialisé dans Monster_Gestion.py. Les sons ne seront pas joués.")
    class DummySound:
        def play(self):
            pass
    SON_DEGATS = DummySound()
    SON_PROJECTILE = DummySound()
    SON_EXPLOSION = DummySound()


# --- Constantes pour les dimensions de l'écran (doivent correspondre à celles de votre jeu principal) ---
LARGEUR, HAUTEUR = 800, 600

# --- Groupes de sprites (doivent être passés depuis le jeu principal) ---
# Ces variables sont laissées ici car elles sont utilisées dans les classes,
# mais leurs groupes seront en fait fournis par le jeu principal.
tous_les_sprites_global = pygame.sprite.Group() 
monstres_global = pygame.sprite.Group()
particles_global = pygame.sprite.Group()
projectiles_global = pygame.sprite.Group()


# Nouvelle classe pour les particules
class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color, size, lifetime, velocity):
        super().__init__()
        self.size = size
        self.lifetime = lifetime  # en millisecondes
        self.spawn_time = pygame.time.get_ticks()
        self.color = color # Stocke la couleur RGBA
        self.velocity = pygame.math.Vector2(velocity)
        
        self.image = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, self.color[:3], (size, size), size)
        self.rect = self.image.get_rect(center=(x, y))
        
        self.image.set_alpha(self.color[3] if len(self.color) == 4 else 255)

    def update(self):
        time_elapsed = pygame.time.get_ticks() - self.spawn_time
        if time_elapsed > self.lifetime:
            self.kill()
            return

        self.rect.x += self.velocity.x
        self.rect.y += self.velocity.y

        initial_alpha = self.color[3] if len(self.color) == 4 else 255
        alpha = initial_alpha - int(initial_alpha * (time_elapsed / self.lifetime))
        if alpha < 0: alpha = 0
        self.image.set_alpha(alpha)


class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y):
        super().__init__()
        self.image = PROJECTILE_IMAGE
        self.rect = self.image.get_rect(center=(x, y))
        self.vitesse = 7
        
        dx = target_x - x
        dy = target_y - y
        distance = math.sqrt(dx**2 + dy**2)
        if distance > 0:
            self.velocity = pygame.math.Vector2(dx / distance * self.vitesse, dy / distance * self.vitesse)
        else:
            self.velocity = pygame.math.Vector2(0, 0)

    def update(self):
        self.rect.x += self.velocity.x
        self.rect.y += self.velocity.y
        # Supprimer le projectile s'il sort de l'écran
        if not pygame.Rect(0, 0, LARGEUR, HAUTEUR).colliderect(self.rect): # Utilise LARGEUR/HAUTEUR globales
            self.kill()


class Monstre(pygame.sprite.Sprite):
    def __init__(self, x, y, joueur_ref, tous_les_sprites_group, particles_group):
        super().__init__()
        self.image = MONSTRE_IMAGE
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vitesse = random.randint(1, 2)
        self.pv_max = 50
        self.pv = self.pv_max
        self.degats_attaque = 15
        self.temps_derniere_attaque = 0
        self.delai_attaque = 1000
        self.xp_value = 10 # XP donné à la mort

        self.joueur_ref = joueur_ref # Référence au joueur pour l'XP
        self.tous_les_sprites = tous_les_sprites_group
        self.particles = particles_group

        self.cible_joueur = None

    def mouvement(self, joueur_rect): # Ajout de joueur_rect pour ciblage
        if joueur_rect:
            dx = joueur_rect.centerx - self.rect.centerx
            dy = joueur_rect.centery - self.rect.centery
            
            distance = math.sqrt(dx**2 + dy**2)
            if distance > 0:
                dx_norm = dx / distance
                dy_norm = dy / distance
                
                self.rect.x += dx_norm * self.vitesse
                self.rect.y += dy_norm * self.vitesse
        # S'assurer que les monstres restent dans les limites de l'écran
        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(LARGEUR, self.rect.right)
        self.rect.top = max(0, self.rect.top)
        self.rect.bottom = min(HAUTEUR, self.rect.bottom)


    def attaquer(self, joueur):
        temps_actuel = pygame.time.get_ticks()
        if temps_actuel - self.temps_derniere_attaque > self.delai_attaque and self.rect.colliderect(joueur.rect):
            self.temps_derniere_attaque = temps_actuel
            SON_DEGATS.play() # Jouer le son de dégâts
            joueur.prendre_degats(self.degats_attaque)

    def prendre_degats(self, degats):
        self.pv -= degats
        SON_DEGATS.play() # Jouer le son de dégâts
        if self.pv < 0:
            self.pv = 0
        if self.pv == 0:
            # Créer des particules à la mort du monstre
            for _ in range(15): # 15 particules
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(2, 5)
                velocity = (speed * math.cos(angle), speed * math.sin(angle))
                # Utilise GLOW_ROUGE pour les particules du monstre
                particle = Particle(self.rect.centerx, self.rect.centery, GLOW_ROUGE, random.randint(2, 5), random.randint(300, 800), velocity)
                self.tous_les_sprites.add(particle)
                self.particles.add(particle) # Ajouter au nouveau groupe de particules
            if self.joueur_ref: # S'assurer que la référence au joueur existe
                self.joueur_ref.add_xp(self.xp_value) # Le joueur gagne de l'XP
            self.kill()

    def dessiner_barre_vie(self, surface):
        barre_longueur = 50
        barre_hauteur = 7
        remplissage = (self.pv / self.pv_max) * barre_longueur
        
        bordure_rect_x = self.rect.centerx - (barre_longueur // 2)
        bordure_rect_y = self.rect.y - 10
        bordure_rect = pygame.Rect(bordure_rect_x, bordure_rect_y, barre_longueur, barre_hauteur)
        
        remplissage_rect = pygame.Rect(bordure_rect_x, bordure_rect_y, remplissage, barre_hauteur)
        
        pygame.draw.rect(surface, ROUGE, bordure_rect)
        pygame.draw.rect(surface, VERT, remplissage_rect)
        pygame.draw.rect(surface, NOIR, bordure_rect, 1)

    def draw(self, surface):
        glow_size_increase = 5
        for i in range(2):
            glow_surface = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            glow_surface.blit(self.image, (0,0))
            
            glow_color_with_alpha = (GLOW_ROUGE[0], GLOW_ROUGE[1], GLOW_ROUGE[2], GLOW_ROUGE[3] // (i + 1))
            glow_surface.fill(glow_color_with_alpha, special_flags=pygame.BLEND_RGBA_ADD)
            
            scaled_glow = pygame.transform.smoothscale(glow_surface, (self.rect.width + i * glow_size_increase, self.rect.height + i * glow_size_increase))
            scaled_glow_rect = scaled_glow.get_rect(center=self.rect.center)
            surface.blit(scaled_glow, scaled_glow_rect)
        
        surface.blit(self.image, self.rect)


class MonstreRapide(Monstre):
    def __init__(self, x, y, joueur_ref, tous_les_sprites_group, particles_group):
        super().__init__(x, y, joueur_ref, tous_les_sprites_group, particles_group)
        self.image = MONSTRE_RAPIDE_IMAGE
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vitesse = random.randint(3, 4)
        self.pv_max = 40
        self.pv = self.pv_max
        self.degats_attaque = 10
        self.delai_attaque = 800
        self.xp_value = 15

    def draw(self, surface):
        glow_size_increase = 4
        for i in range(2):
            glow_surface = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            glow_surface.blit(self.image, (0,0))
            glow_color_with_alpha = (GLOW_ORANGE[0], GLOW_ORANGE[1], GLOW_ORANGE[2], GLOW_ORANGE[3] // (i + 1))
            glow_surface.fill(glow_color_with_alpha, special_flags=pygame.BLEND_RGBA_ADD)
            
            scaled_glow = pygame.transform.smoothscale(glow_surface, (self.rect.width + i * glow_size_increase, self.rect.height + i * glow_size_increase))
            scaled_glow_rect = scaled_glow.get_rect(center=self.rect.center)
            surface.blit(scaled_glow, scaled_glow_rect)
        
        surface.blit(self.image, self.rect)


class MonstreStatique(Monstre):
    def __init__(self, x, y, joueur_ref, tous_les_sprites_group, particles_group, projectiles_group):
        super().__init__(x, y, joueur_ref, tous_les_sprites_group, particles_group)
        self.image = MONSTRE_STATIQUE_IMAGE
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vitesse = 0
        self.pv_max = 50
        self.pv = self.pv_max
        self.degats_attaque = 25
        self.delai_attaque = 2000
        self.temps_dernier_tir = 0
        self.xp_value = 20
        self.projectiles = projectiles_group

    def mouvement(self, joueur_rect):
        pass

    def tirer(self, joueur_rect, round_start_cooldown_active):
        temps_actuel = pygame.time.get_ticks()
        if self.joueur_ref and self.joueur_ref.alive() and not round_start_cooldown_active and \
           (temps_actuel - self.temps_dernier_tir > self.delai_attaque):
            SON_PROJECTILE.play()
            projectile = Projectile(self.rect.centerx, self.rect.centery, joueur_rect.centerx, joueur_rect.centery)
            self.tous_les_sprites.add(projectile)
            self.projectiles.add(projectile)
            self.temps_dernier_tir = temps_actuel

    def update(self, joueur_rect, round_start_cooldown_active):
        if self.pv <= 0:
            for _ in range(15):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(2, 5)
                velocity = (speed * math.cos(angle), speed * math.sin(angle))
                particle = Particle(self.rect.centerx, self.rect.centery, GLOW_ROUGE, random.randint(2, 5), random.randint(300, 800), velocity)
                self.tous_les_sprites.add(particle)
                self.particles.add(particle)
            if self.joueur_ref:
                self.joueur_ref.add_xp(self.xp_value)
            self.kill()
            return

        self.tirer(joueur_rect, round_start_cooldown_active)


class MonstreKamikaze(Monstre):
    def __init__(self, x, y, joueur_ref, tous_les_sprites_group, particles_group):
        super().__init__(x, y, joueur_ref, tous_les_sprites_group, particles_group)
        self.image = MONSTRE_KAMIKAZE_IMAGE
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vitesse = random.randint(2, 3)
        self.pv_max = 30
        self.pv = self.pv_max
        self.degats_attaque = 0
        self.xp_value = 25
        self.rayon_explosion = 80
        self.degats_explosion = 30

    def mouvement(self, joueur_rect):
        super().mouvement(joueur_rect)

        if self.rect.colliderect(self.joueur_ref.rect):
            self._exploser()

    def prendre_degats(self, degats):
        super().prendre_degats(degats)

    def _exploser(self):
        SON_EXPLOSION.play()
        self.joueur_ref.prendre_degats(self.degats_explosion)
        
        for _ in range(30):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(4, 8)
            velocity = (speed * math.cos(angle), speed * math.sin(angle))
            particle = Particle(self.rect.centerx, self.rect.centery, GLOW_VERT_EXPLOSION, random.randint(3, 7), random.randint(400, 1000), velocity)
            self.tous_les_sprites.add(particle)
            self.particles.add(particle)
        
        if self.joueur_ref:
            self.joueur_ref.add_xp(self.xp_value)
        self.kill()

    def draw(self, surface):
        glow_size_increase = 6
        for i in range(2):
            glow_surface = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            glow_surface.blit(self.image, (0,0))
            glow_color_with_alpha = (GLOW_VERT_EXPLOSION[0], GLOW_VERT_EXPLOSION[1], GLOW_VERT_EXPLOSION[2], GLOW_VERT_EXPLOSION[3] // (i + 1))
            glow_surface.fill(glow_color_with_alpha, special_flags=pygame.BLEND_RGBA_ADD)
            
            scaled_glow = pygame.transform.smoothscale(glow_surface, (self.rect.width + i * glow_size_increase, self.rect.height + i * glow_size_increase))
            scaled_glow_rect = scaled_glow.get_rect(center=self.rect.center)
            surface.blit(scaled_glow, scaled_glow_rect)
        
        surface.blit(self.image, self.rect)

# --- Fonction utilitaire pour sélectionner un type de monstre basé sur les probabilités ---
def select_monster_type(spawn_rates):
    """
    Sélectionne une classe de monstre basée sur les probabilités données.
    Les probabilités doivent sommer à 1.0.
    """
    rand_pick = random.random()
    cumulative_prob = 0.0
    for monster_class, probability in spawn_rates.items():
        cumulative_prob += probability
        if rand_pick < cumulative_prob:
            return monster_class
    # Fallback au cas où les probabilités ne somment pas exactement à 1.0 ou pour d'autres erreurs.
    # Ceci ne devrait normalement pas être atteint si les probabilités sont bien configurées.
    return Monstre

# --- Définition des taux d'apparition des monstres ---
# Les probabilités doivent être ajustées de manière à ce que leur somme soit égale à 1.0.
MONSTER_SPAWN_RATES = {
    Monstre: 0.45,         # 45% de chance pour le monstre de base (rouge)
    MonstreRapide: 0.25,   # 25% de chance pour le monstre rapide (orange)
    MonstreStatique: 0.15, # 15% de chance pour le monstre statique (violet)
    MonstreKamikaze: 0.15, # 15% de chance pour le monstre kamikaze (vert)
}


def creer_monstre(nombre_monstres, joueur_instance, tous_les_sprites_group, monstres_group, particles_group, projectiles_group, round_start_cooldown_active):
    """
    Crée le nombre spécifié de monstres et les ajoute aux groupes de sprites.
    :param nombre_monstres: Le nombre de monstres à créer.
    :param joueur_instance: Référence à l'instance du joueur pour le ciblage et l'XP.
    :param tous_les_sprites_group: Le groupe de tous les sprites (utilisé pour les particules/projectiles générés par les monstres).
    :param monstres_group: Le groupe des sprites de monstres.
    :param particles_group: Le groupe des sprites de particules.
    :param projectiles_group: Le groupe des sprites de projectiles.
    :param round_start_cooldown_active: Indique si le compte à rebours de début de manche est actif.
    """
    for _ in range(nombre_monstres):
        x = random.randint(0, LARGEUR - MONSTRE_STATIQUE_IMAGE.get_width())
        y = random.randint(0, HAUTEUR - 150)
        
        # Sélectionne le type de monstre à créer
        chosen_monster_class = select_monster_type(MONSTER_SPAWN_RATES)

        monstre = None
        if chosen_monster_class == MonstreStatique:
            # Logique de position spéciale pour les monstres statiques
            while math.hypot(x - joueur_instance.rect.centerx, y - joueur_instance.rect.centery) < 200:
                x = random.randint(0, LARGEUR - MONSTRE_STATIQUE_IMAGE.get_width())
                y = random.randint(0, HAUTEUR - 150)
            monstre = chosen_monster_class(x, y, joueur_instance, tous_les_sprites_group, particles_group, projectiles_group)
        else:
            # Tous les autres types de monstres ont le même constructeur
            monstre = chosen_monster_class(x, y, joueur_instance, tous_les_sprites_group, particles_group)

        monstres_group.add(monstre)
