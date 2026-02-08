import io
import os
import sys
import shutil
import zipfile
import pygame
import subprocess
import threading
from datetime import datetime
import psutil
import requests

from UpdateUtility import *
from Gauge import *
from Indicator import *
from Tile import *
from ProgressBar import *

pygame.init()
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480
FPS = 30

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE_UI = (0, 162, 255)
RED = (255, 30, 30)
GRAY_DARK = (40, 40, 40)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.NOFRAME)
clock = pygame.time.Clock()


current_view = "main"

# Variables pour la gestion de la mise à jour
update_available = False
update_version = None
update_in_progress = False
update_progress = 0.0
update_status = "En attente..."
progress_bar = None

GAUGE_SIZE = 200
ARROW_SIZE = 25
PADDING = 50
GAUGE_Y = 20

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

version = "null"

def shutdown(desktop=False):
    if not desktop:
        os.system("sudo shutdown -h now")
    pygame.quit()
    sys.exit()

def switch_view(view):
    global current_view
    global tiles
    global version
    global update_available
    global update_version
    global progress_bar
    global update_in_progress
    global update_progress
    global update_status

    current_view = view

    if (current_view == "main"):
        if clockTile in tiles:
            tiles.remove(clockTile)
        if updateDownloadTile in tiles:
            tiles.remove(updateDownloadTile)
        if statsTile not in tiles:
            tiles.append(statsTile)
    elif (current_view == "stats"):
        if statsTile in tiles:
            tiles.remove(statsTile)
        if updateDownloadTile in tiles:
            tiles.remove(updateDownloadTile)
        if clockTile not in tiles:
            tiles.append(clockTile)
    elif (current_view == "settings"):
        # Garder le bouton clock/stats
        if statsTile in tiles:
            tiles.remove(statsTile)
        if clockTile not in tiles:
            tiles.append(clockTile)

        # Retirer le bouton de téléchargement de la barre de navigation (il sera affiché à côté de la progressbar)
        if updateDownloadTile in tiles:
            tiles.remove(updateDownloadTile)

        # Vérifier les mises à jour
        current = get_current_version().strip()
        latest = check_for_updates()

        if latest and latest != current:
            update_available = True
            update_version = latest
            version = f"{current} -> {latest}"
        else:
            update_available = False
            update_version = None
            version = f"{current} : Aucune mise à jour"

        # Réinitialiser les variables de mise à jour si on revient sur la page
        if not update_in_progress:
            update_progress = 0.0
            update_status = "En attente..."

        # Créer la barre de progression si nécessaire
        if progress_bar is None:
            progress_bar = ProgressBar((150, 260), (400, 40),
                                      bg_color=GRAY_DARK,
                                      fill_color=BLUE_UI,
                                      border_color=WHITE)

# Configuration des 4 boutons en ligne
BUTTON_WIDTH = 170
BUTTON_HEIGHT = 100
BUTTON_Y = 350
BUTTON_SPACING = (SCREEN_WIDTH - 4 * BUTTON_WIDTH) / 5  # Espacement uniforme

offTile = Tile((BUTTON_WIDTH, BUTTON_HEIGHT),
               (BUTTON_SPACING, BUTTON_Y),
               BLUE_UI,
               icon="../assets/on-off-button.png",
               methode=shutdown,
               pressed_color=(0, 100, 180),
               text_color=BLUE_UI)

desktopTile = Tile((BUTTON_WIDTH, BUTTON_HEIGHT),
                   (BUTTON_SPACING * 2 + BUTTON_WIDTH, BUTTON_Y),
                   BLUE_UI,
                   icon="../assets/desktop-monitor.png",
                   methode=lambda: shutdown(desktop=True),
                   pressed_color=(0, 100, 180),
                   text_color=BLUE_UI)

settingsTile = Tile((BUTTON_WIDTH, BUTTON_HEIGHT),
                   (BUTTON_SPACING * 3 + BUTTON_WIDTH *2, BUTTON_Y),
                   BLUE_UI,
                   icon="../assets/update.png",
                   methode=lambda: switch_view("settings"),
                   pressed_color=(0, 100, 180),
                    text_color=BLUE_UI)

statsTile = Tile((BUTTON_WIDTH, BUTTON_HEIGHT),
                 (BUTTON_SPACING * 4 + BUTTON_WIDTH * 3, BUTTON_Y),
                 BLUE_UI,
                 icon="../assets/stats.png",
                 methode=lambda: switch_view("stats"),
                 pressed_color=(0, 100, 180),
                 text_color=BLUE_UI)

clockTile = Tile((BUTTON_WIDTH, BUTTON_HEIGHT),
                 (BUTTON_SPACING * 4 + BUTTON_WIDTH * 3, BUTTON_Y),
                 BLUE_UI,
                 icon="../assets/clock.png",
                 methode=lambda: switch_view("main"),
                 pressed_color=(0, 100, 180),
                 text_color=BLUE_UI)

def start_update():
    """Démarre le téléchargement et l'installation de la mise à jour"""
    global update_in_progress, update_version, update_progress, update_status

    if update_in_progress or not update_version:
        return

    update_in_progress = True
    update_progress = 0.0
    update_status = "Démarrage..."

    # Lancer le téléchargement dans un thread séparé
    def update_thread():
        global update_progress, update_status

        def progress_callback(downloaded, total):
            global update_progress
            if total > 0:
                update_progress = downloaded / total

        def status_callback(status):
            global update_status
            update_status = status

        # Extraire le numéro de version (enlever le 'v' si présent)
        version_number = update_version.strip().lstrip('v')
        download_latest_release(version_number, progress_callback, status_callback)

    thread = threading.Thread(target=update_thread, daemon=True)
    thread.start()

updateDownloadTile = Tile((BUTTON_WIDTH, BUTTON_HEIGHT),
                          (BUTTON_SPACING * 4 + BUTTON_WIDTH * 3, BUTTON_Y),
                          (0, 200, 100),  # Vert pour indiquer le téléchargement
                          icon="../assets/update.png",
                          text="Télécharger",
                          font_size=26,
                          methode=start_update,
                          pressed_color=(0, 150, 70),
                          text_color=WHITE,
                          pressed_text_color=(200, 200, 200))

tiles = [offTile, desktopTile, settingsTile, statsTile]

switch_view("main")

def draw_bottom_nav():
    for tile in tiles:
        tile.show(screen)

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

    temp = get_cpu_temp()
    cpu = get_cpu_usage()
    ram = psutil.virtual_memory().percent

    wifiIndic.state = psutil.net_if_stats().get('wlan0', None) and psutil.net_if_stats()['wlan0'].isup
    fanIndic.state = False

    jaugeTemp.show(screen, temp)
    jaugeCpu.show(screen, cpu)
    jaugeRam.show(screen, ram)

    indicatorsBox.show(screen)

    draw_bottom_nav()

def show_settings():
    screen.fill(BLACK)

    # Afficher la version
    try:
        font = pygame.font.Font(None, 50)
        version_txt = font.render(version, True, WHITE)
    except Exception as e:
        print(e)
        font = pygame.font.Font(None, 50)
        version_txt = font.render("ERROR", True, WHITE)
    screen.blit(version_txt, version_txt.get_rect(center=(400, 180)))

    # Afficher la barre de progression et le bouton si une mise à jour est disponible
    if update_available and progress_bar:
        # Mettre à jour la barre de progression
        progress_bar.set_progress(update_progress)
        progress_bar.show(screen)

        # Afficher le statut de la mise à jour
        font_status = pygame.font.Font(None, 28)
        status_txt = font_status.render(update_status, True, WHITE)
        screen.blit(status_txt, status_txt.get_rect(center=(400, 320)))

        # Afficher le bouton de téléchargement à côté de la barre de progression
        # Repositionner temporairement le bouton pour l'afficher à côté de la progressbar
        download_button_x = 570  # À droite de la barre de progression
        download_button_y = 240  # Aligné avec la barre
        download_button_width = 120
        download_button_height = 60

        # Créer un rectangle pour le bouton de téléchargement
        download_rect = pygame.Rect(download_button_x, download_button_y, download_button_width, download_button_height)

        # Déterminer la couleur selon l'état
        if update_in_progress:
            button_color = (100, 100, 100)  # Gris si en cours
            text_color = (200, 200, 200)
        else:
            button_color = (0, 200, 100)  # Vert si disponible
            text_color = WHITE

        # Dessiner le bouton avec contour (fileté)
        pygame.draw.rect(screen, button_color, download_rect, width=1, border_radius=5)

        # Afficher l'icône du bouton (plus petite)
        try:
            icon = pygame.image.load("../assets/update.png").convert_alpha()
            icon = pygame.transform.scale(icon, (30, 30))
            # Colorer l'icône
            color_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
            color_surf.fill(text_color)
            icon.blit(color_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            icon_rect = icon.get_rect(center=(download_button_x + download_button_width // 2, download_button_y + 20))
            screen.blit(icon, icon_rect)
        except Exception as e:
            print(f"Erreur icône: {e}")

        # Afficher le texte du bouton
        font_button = pygame.font.Font(None, 22)
        if update_in_progress:
            button_text = "En cours..."
        else:
            button_text = "Télécharger"
        button_txt = font_button.render(button_text, True, text_color)
        button_txt_rect = button_txt.get_rect(center=(download_button_x + download_button_width // 2, download_button_y + 45))
        screen.blit(button_txt, button_txt_rect)

        # Stocker le rectangle pour la détection de clic (on le fait dans la boucle principale)
        # Pour l'instant, on stocke les coordonnées dans des variables globales
        globals()['download_button_rect'] = download_rect

    draw_bottom_nav()

def main():
    global current_view
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Clic gauche
                    # Vérifier d'abord si on clique sur le bouton de téléchargement dans la vue settings
                    if current_view == "settings" and update_available and not update_in_progress:
                        download_rect = globals().get('download_button_rect')
                        if download_rect and download_rect.collidepoint(event.pos):
                            start_update()
                            continue

                    # Gérer les clics sur les tiles de navigation
                    for tile in tiles:
                        if tile.check_click(event.pos):
                            tile.press()
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Relâchement clic gauche
                    for tile in tiles:
                        if tile.is_pressed:
                            tile.release()
                            if tile.check_click(event.pos):
                                tile.on_click()

        if current_view == "main":
            show_main()
        elif current_view == "stats":
            show_stats()
        elif current_view == "settings":
            show_settings()

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == '__main__':
    main()