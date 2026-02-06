import pygame
import sys
from datetime import datetime
import psutil
import os

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480
FPS = 30

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.NOFRAME)
clock = pygame.time.Clock()

pygame.mouse.set_visible(False)

class GaugeRound:

    def __init__(self, diameter, gauge_image, gauge_arrow_image, position, sizeGauge, arrow_length):
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

    def show(self, fenetre, rotation):
        fenetre.blit(self.gauge_image, self.position)

        # Rotation de l'aiguille
        rotated_arrow = pygame.transform.rotate(self.gauge_arrow_image, rotation)
        # Centrer l'aiguille en utilisant la taille réelle de la jauge
        center_x = self.position[0] + self.sizeGauge[0] // 2
        center_y = self.position[1] + self.sizeGauge[1] // 2
        arrow_rect = rotated_arrow.get_rect(center=(center_x, center_y))
        fenetre.blit(rotated_arrow, arrow_rect.topleft)

class GaugeTemperature(GaugeRound):

    def __init__(self, diameter, gauge_image, gauge_arrow_image, position, sizeGauge, arrow_length):
        super().__init__(diameter, gauge_image, gauge_arrow_image, position, sizeGauge, arrow_length)

    def show(self, fenetre, value):
        rotation = 50 - (value * 25 / 10)
        super().show(fenetre, rotation)

class GaugeCPU(GaugeRound):

    def __init__(self, diameter, gauge_image, gauge_arrow_image, position, sizeGauge, arrow_length, smoothing_samples=10):
        super().__init__(diameter, gauge_image, gauge_arrow_image, position, sizeGauge, arrow_length)
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

def get_cpu_temp():
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            return float(f.read()) / 1000.0
    except: return 0.0

def get_cpu_usage():
    return psutil.cpu_percent(interval=0.1)

# Configuration des jauges avec padding
GAUGE_SIZE = 200
ARROW_SIZE = 25
PADDING = 20
GAUGE_Y = (SCREEN_HEIGHT - GAUGE_SIZE) // 2  # Centrer verticalement
TOTAL_WIDTH = GAUGE_SIZE * 3 + PADDING * 2
START_X = (SCREEN_WIDTH - TOTAL_WIDTH) // 2  # Centrer horizontalement

jaugeTemp = GaugeTemperature(GAUGE_SIZE, "Compteur.png", "Aiguille.png",
                             (START_X, GAUGE_Y), (GAUGE_SIZE, GAUGE_SIZE), ARROW_SIZE)
jaugeCpu = GaugeCPU(GAUGE_SIZE, "CompteurCpu.png", "Aiguille.png",
                    (START_X + GAUGE_SIZE + PADDING, GAUGE_Y), (GAUGE_SIZE, GAUGE_SIZE), ARROW_SIZE)
jaugeRam = GaugeCPU(GAUGE_SIZE, "CompteurRam.png", "Aiguille.png",
                    (START_X + (GAUGE_SIZE + PADDING) * 2, GAUGE_Y), (GAUGE_SIZE, GAUGE_SIZE), ARROW_SIZE)
def main():
    while True:

        screen.fill((0, 0, 0))
        # Affichage de la jauge de température
        temp = get_cpu_temp()
        jaugeTemp.show(screen, temp)

        temp = get_cpu_usage()
        jaugeCpu.show(screen, temp)

        ram = psutil.virtual_memory().percent
        jaugeRam.show(screen, ram)

        pygame.display.flip()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

if __name__ == '__main__':
    main()
