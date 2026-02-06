import os

import pygame
import sys
from datetime import datetime
import psutil

# --- CONFIGURATION ---
pygame.init()
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480
FPS = 30

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE_UI = (0, 162, 255)
BLUE_CLICK = (180, 230, 255)  # Couleur plus claire lors du clic
RED = (255, 30, 30)
GRAY_DARK = (40, 40, 40)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.NOFRAME)
clock = pygame.time.Clock()


# --- CHARGEMENT DES ICONES ---

def load_and_color_icon(path, color, size=(50, 50)):
    """Charge un PNG et le teinte avec la couleur choisie"""
    try:
        surface = pygame.image.load(path).convert_alpha()
        surface = pygame.transform.scale(surface, size)

        # Création du filtre de couleur
        color_surf = pygame.Surface(size, pygame.SRCALPHA)
        color_surf.fill(color)

        # Application de la couleur (multiplication)
        surface.blit(color_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return surface
    except Exception as e:
        print(f"Erreur chargement {path}: {e}")
        # Surface de secours en cas d'erreur
        fallback = pygame.Surface(size)
        fallback.fill(RED)
        return fallback


# Remplacez les chemins ci-dessous par vos fichiers réels
paths = {
    "power": "on-off-button.png",
    "desktop": "desktop-monitor.png",
    "raspi": "stats.png",
    "clock": "clock.png"
}

# Dictionnaire pour stocker les icônes (Normal et Cliqué)
icons = {
    "power": {"off": load_and_color_icon(paths["power"], BLUE_UI), "on": load_and_color_icon(paths["power"], WHITE)},
    "desktop": {"off": load_and_color_icon(paths["desktop"], BLUE_UI),
                "on": load_and_color_icon(paths["desktop"], WHITE)},
    "raspi": {"off": load_and_color_icon(paths["raspi"], BLUE_UI), "on": load_and_color_icon(paths["raspi"], WHITE)},
    "clock": {"off": load_and_color_icon(paths["clock"], BLUE_UI), "on": load_and_color_icon(paths["clock"], WHITE)}
}

# --- CLASSES JAUGES ---

class GaugeRound:

    def __init__(self, diameter, gauge_image, gauge_arrow_image, position, sizeGauge, arrow_length, title=""):
        self.diameter = diameter

        self.gauge_image = pygame.image.load(gauge_image)
        self.gauge_image = pygame.transform.scale(self.gauge_image, sizeGauge)

        # Charger l'image de l'aiguille et calculer son ratio d'aspect
        arrow_original = pygame.image.load(gauge_arrow_image)
        original_width = arrow_original.get_width()
        original_height = arrow_original.get_height()
        aspect_ratio = original_width / original_height

        # Redimensionner en gardant le ratio d'aspect (arrow_length est la hauteur)
        new_width = int(arrow_length * aspect_ratio)
        self.gauge_arrow_image = pygame.transform.scale(arrow_original, (new_width, arrow_length))

        self.position = position
        self.sizeGauge = sizeGauge
        self.arrow_length = arrow_length
        self.title = title

    def show(self, fenetre, rotation):
        fenetre.blit(self.gauge_image, self.position)

        # Rotation de l'aiguille
        rotated_arrow = pygame.transform.rotate(self.gauge_arrow_image, rotation)
        # Centrer l'aiguille en utilisant la taille réelle de la jauge
        center_x = self.position[0] + self.sizeGauge[0] // 2
        center_y = self.position[1] + self.sizeGauge[1] // 2
        arrow_rect = rotated_arrow.get_rect(center=(center_x, center_y))
        fenetre.blit(rotated_arrow, arrow_rect.topleft)

        # Afficher le titre sous la jauge
        if self.title:
            font = pygame.font.Font(None, 32)
            text = font.render(self.title, True, WHITE)
            text_rect = text.get_rect(center=(center_x, self.position[1] + self.sizeGauge[1] + 20))
            fenetre.blit(text, text_rect)

class GaugeTemperature(GaugeRound):

    def __init__(self, diameter, gauge_image, gauge_arrow_image, position, sizeGauge, arrow_length, title=""):
        super().__init__(diameter, gauge_image, gauge_arrow_image, position, sizeGauge, arrow_length, title)

    def show(self, fenetre, value):
        rotation = 50 - (value * 25 / 10)
        super().show(fenetre, rotation)

class GaugeCPU(GaugeRound):

    def __init__(self, diameter, gauge_image, gauge_arrow_image, position, sizeGauge, arrow_length, title="", smoothing_samples=10):
        super().__init__(diameter, gauge_image, gauge_arrow_image, position, sizeGauge, arrow_length, title)
        self.smoothing_samples = smoothing_samples
        self.values_history = []

    def show(self, fenetre, value):
        # Ajouter la nouvelle valeur à l'historique
        self.values_history.append(value)

        # Garder seulement les N dernières valeurs
        if len(self.values_history) > self.smoothing_samples:
            self.values_history.pop(0)

        # Calculer la moyenne pour le lissage
        smoothed_value = sum(self.values_history) / len(self.values_history)

        rotation = 50 - (smoothed_value * 25 / 10)
        super().show(fenetre, rotation)

# --- ETATS ---
current_view = "main"
# Variables pour gérer l'animation de clic
clicked_btn = None  # Stocke le bouton actuellement pressé

# Zones tactiles
rect_power = pygame.Rect(30, 370, 120, 80)
rect_desktop = pygame.Rect(340, 370, 120, 80)
rect_switch = pygame.Rect(650, 370, 120, 80)

# --- INITIALISATION DES JAUGES ---
# Configuration des jauges avec padding
GAUGE_SIZE = 200
ARROW_SIZE = 25
PADDING = 50
GAUGE_Y = 100  # Position verticale des jauges

# Positions des 3 jauges
jaugeTemp = GaugeTemperature(GAUGE_SIZE, "Compteur.png", "Aiguille.png",
                             (50, GAUGE_Y), (GAUGE_SIZE, GAUGE_SIZE), ARROW_SIZE, title="TEMPÉRATURE")
jaugeCpu = GaugeCPU(GAUGE_SIZE, "CompteurCpu.png", "Aiguille.png",
                    (50 + GAUGE_SIZE + PADDING, GAUGE_Y), (GAUGE_SIZE, GAUGE_SIZE), ARROW_SIZE, title="CPU")
jaugeRam = GaugeCPU(GAUGE_SIZE, "CompteurRam.png", "Aiguille.png",
                    (50 + (GAUGE_SIZE + PADDING) * 2, GAUGE_Y), (GAUGE_SIZE, GAUGE_SIZE), ARROW_SIZE, title="RAM")


# --- DESSIN DES COMPOSANTS ---

def draw_bottom_nav():
    # Liste des boutons pour itérer facilement
    buttons = [
        ("power", rect_power),
        ("desktop", rect_desktop),
        ("switch", rect_switch)
    ]

    for name, rect in buttons:
        # Couleur du cadre si cliqué
        is_active = (clicked_btn == name)
        border_col = WHITE if is_active else BLUE_UI

        pygame.draw.rect(screen, border_col, rect, 2, border_radius=12)

        # Sélection de l'image
        img_key = name
        if name == "switch":
            img_key = "raspi" if current_view == "main" else "clock"

        state = "on" if is_active else "off"
        img = icons[img_key][state]

        screen.blit(img, img.get_rect(center=rect.center))


# --- PANNEAUX ---

def show_main():
    screen.fill(BLACK)
    now = datetime.now().strftime("%H : %M")
    font_time = pygame.font.Font(None, 240)
    text = font_time.render(now, True, WHITE)
    screen.blit(text, text.get_rect(center=(400, 200)))
    draw_bottom_nav()

def get_cpu_temp():
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            return float(f.read()) / 1000.0
    except: return 0.0

def get_cpu_usage():
    return psutil.cpu_percent(interval=0.1)

def show_stats():
    screen.fill(BLACK)

    # Données
    temp = get_cpu_temp()
    cpu = get_cpu_usage()
    ram = psutil.virtual_memory().percent

    # Afficher les 3 jauges avec images
    jaugeTemp.show(screen, temp)
    jaugeCpu.show(screen, cpu)
    jaugeRam.show(screen, ram)

    draw_bottom_nav()


# --- BOUCLE PRINCIPALE ---

def main():
    global current_view, clicked_btn
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Gestion du clic (Appui)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if rect_power.collidepoint(event.pos):
                    clicked_btn = "power"
                elif rect_desktop.collidepoint(event.pos):
                    clicked_btn = "desktop"
                elif rect_switch.collidepoint(event.pos):
                    clicked_btn = "switch"

            # Gestion du relâchement (Action)
            if event.type == pygame.MOUSEBUTTONUP:
                if clicked_btn == "power" and rect_power.collidepoint(event.pos):
                    os.system("sudo shutdown -h now")
                elif clicked_btn == "desktop" and rect_desktop.collidepoint(event.pos):
                    running = False
                elif clicked_btn == "switch" and rect_switch.collidepoint(event.pos):
                    current_view = "stats" if current_view == "main" else "main"

                clicked_btn = None  # Reset l'état visuel

        if current_view == "main":
            show_main()
        else:
            show_stats()

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == '__main__':
    main()