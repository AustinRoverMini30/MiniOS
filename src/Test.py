import io
import os
import shutil
import zipfile
import pygame
import subprocess
from datetime import datetime
import psutil
import requests

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

def get_current_version():
    with open("../VERSION", "r") as f:
        return f.read().strip()

def get_latest_version_from_github(repo_owner, repo_name):
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()["tag_name"].lstrip("v")  # Supprime le "v" si présent
    return None

def check_for_updates():
    current_version = get_current_version()
    latest_version = get_latest_version_from_github("AustinRoverMini30", "MiniOS")

    if latest_version and latest_version != current_version:
        print(f"Une nouvelle version est disponible : {latest_version} (vous avez {current_version})")
        download_latest_release(latest_version)
        return latest_version
    else:
        print("Votre version est à jour.")
        return None

def download_latest_release(version):
    print(version)
    # URL de la release (remplace par l'URL de ton ZIP)
    release_url = f"https://github.com/AustinRoverMini30/MiniOS/archive/refs/tags/v{version}.zip"
    response = requests.get(release_url, stream=True)

    if response.status_code == 200:
        # Extraire le ZIP directement à la racine du projet
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
            # Détecter s'il y a un dossier racine unique dans l'archive (ex: MiniOS-<tag>/...)
            all_names = [name for name in zip_file.namelist() if name and not name.endswith('/')]
            first_components = [name.split('/', 1)[0] for name in zip_file.namelist() if name]
            root_folder = None
            if first_components:
                first = first_components[0]
                if all(comp == first for comp in first_components):
                    root_folder = first

            project_root = os.path.abspath('..')

            for member in zip_file.infolist():
                member_name = member.filename
                # Ignorer les répertoires explicites
                if member_name.endswith('/'):
                    continue

                # Enlever le dossier racine unique si présent
                if root_folder and member_name.startswith(root_folder + '/'):
                    rel_path = member_name[len(root_folder) + 1:]
                else:
                    rel_path = member_name

                if not rel_path:
                    # cas où on tombe sur l'entrée du dossier racine lui-même
                    continue

                # Normaliser et empêcher l'écriture hors du répertoire du projet
                dest_path = os.path.normpath(os.path.join(project_root, rel_path))
                if not dest_path.startswith(project_root):
                    print(f"Chemin ignoré (tentative d'évasion) : {member_name}")
                    continue

                os.makedirs(os.path.dirname(dest_path), exist_ok=True)

                # Extraire le fichier en écrasant si nécessaire
                with zip_file.open(member) as src, open(dest_path, 'wb') as dst:
                    shutil.copyfileobj(src, dst)

                # Restaurer les permissions exécutables si nécessaire
                if member.external_attr >> 16:
                    try:
                        os.chmod(dest_path, member.external_attr >> 16)
                    except Exception:
                        pass

        print(f"Mise à jour vers la version {version} terminée !")

        # Après la mise à jour, tenter de lancer launcher.sh à la racine du projet
        try:
            launcher_path = os.path.join(project_root, 'launcher.sh')
            if os.path.exists(launcher_path):
                try:
                    os.chmod(launcher_path, 0o755)
                except Exception:
                    pass

                print('Lancement de launcher.sh...')
                # Fermer proprement pygame si en cours
                try:
                    pygame.quit()
                except Exception:
                    pass

                # Lancer le script et quitter ce processus
                try:
                    # Utiliser Popen pour détacher le nouveau processus
                    subprocess.Popen([launcher_path], cwd=project_root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                except Exception as e:
                    print(f"Erreur en lançant launcher.sh : {e}")

                # Quitter l'application actuelle
                sys.exit(0)
            else:
                print('launcher.sh introuvable à la racine du projet ; mise à jour terminée sans relance.')
        except Exception as e:
            print(f"Erreur lors du lancement post-mise-à-jour : {e}")
    else:
        print("Échec du téléchargement de la mise à jour.")

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
    "power": "../assets/on-off-button.png",
    "desktop": "../assets/desktop-monitor.png",
    "raspi": "../assets/stats.png",
    "clock": "../assets/clock.png"
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

class Indicator:

    def __init__(self, size, color_on, color_off, icon, methode=None):
        self.size = size
        self.color_on = color_on
        self.color_off = color_off
        self.state = False
        self.icon = pygame.image.load(icon)
        self.icon = pygame.transform.scale(self.icon, (size[1] - 10, size[1] - 10))
        self.methode = methode
        self.hitbox = pygame.Rect(0, 0, size[0], size[1])

    def show(self, fenetre, position):
        color = self.color_on if self.state else self.color_off
        pygame.draw.rect(fenetre, color, (*position, *self.size), border_radius=2)
        fenetre.blit(self.icon, self.icon.get_rect(center=(position[0] + self.size[0] // 2, position[1] + self.size[1] // 2)))
        self.hitbox = pygame.Rect(position[0], position[1], self.size[0], self.size[1])

    def on_click(self):
        if (self.methode != None):
            self.methode()

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

class IndicatorBox:

    def __init__(self, position, size, color, weight):
        self.position = position
        self.size = size
        self.color = color
        self.weight = weight
        self.indicators = []

    def add_indicator(self, indicator):
        self.indicators.append(indicator)

    def show(self, fenetre):
        pygame.draw.rect(fenetre, self.color, (*self.position, *self.size), self.weight)

        x_temp = 20
        y_temp = 20

        for indicator in self.indicators:
            indicator.show(fenetre, (self.position[0] + x_temp, self.position[1] + y_temp))

            x_temp += indicator.size[0] + 10

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
GAUGE_Y = 20

# Positions des 3 jauges
jaugeTemp = GaugeTemperature(GAUGE_SIZE, "../assets/Compteur.png", "../assets/Aiguille.png",
                             (50, GAUGE_Y), (GAUGE_SIZE, GAUGE_SIZE), ARROW_SIZE, title="TEMPÉRATURE")
jaugeCpu = GaugeCPU(GAUGE_SIZE, "../assets/CompteurCpu.png", "../assets/Aiguille.png",
                    (50 + GAUGE_SIZE + PADDING, GAUGE_Y), (GAUGE_SIZE, GAUGE_SIZE), ARROW_SIZE, title="CPU")
jaugeRam = GaugeCPU(GAUGE_SIZE, "../assets/CompteurRam.png", "../assets/Aiguille.png",
                    (50 + (GAUGE_SIZE + PADDING) * 2, GAUGE_Y), (GAUGE_SIZE, GAUGE_SIZE), ARROW_SIZE, title="RAM")

wifiIndic = Indicator((100, 30), (255, 100, 0), GRAY_DARK, "../assets/wifi.png")
fanIndic = Indicator((100, 30), (50, 0, 255), GRAY_DARK, "../assets/fan.png")
updateIndic = Indicator((100, 30), (0, 255, 0), GRAY_DARK, "../assets/update.png", methode=check_for_updates)

indicatorsBox = IndicatorBox((20, GAUGE_SIZE + 70), (SCREEN_WIDTH-40, 70), WHITE, 2)
indicatorsBox.add_indicator(wifiIndic)
indicatorsBox.add_indicator(fanIndic)
indicatorsBox.add_indicator(updateIndic)

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

    wifiIndic.state = psutil.net_if_stats().get('wlan0', None) and psutil.net_if_stats()['wlan0'].isup
    fanIndic.state = False

    # Afficher les 3 jauges avec images
    jaugeTemp.show(screen, temp)
    jaugeCpu.show(screen, cpu)
    jaugeRam.show(screen, ram)

    indicatorsBox.show(screen)

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
                elif updateIndic.hitbox.collidepoint(event.pos):
                    updateIndic.on_click()

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