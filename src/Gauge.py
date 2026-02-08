import pygame


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
            text = font.render(self.title, True, (255,255,255))
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
