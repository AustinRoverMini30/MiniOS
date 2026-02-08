import pygame


class ProgressBar:
    def __init__(self, position, size, bg_color=(40, 40, 40), fill_color=(0, 162, 255), border_color=(255, 255, 255)):
        """
        Crée une barre de progression.

        Args:
            position: Tuple (x, y) pour la position
            size: Tuple (width, height) pour la taille
            bg_color: Couleur de fond
            fill_color: Couleur de remplissage
            border_color: Couleur de la bordure
        """
        self.position = position
        self.size = size
        self.bg_color = bg_color
        self.fill_color = fill_color
        self.border_color = border_color
        self.progress = 0.0  # Valeur entre 0.0 et 1.0

    def set_progress(self, progress):
        """Définit la progression (0.0 à 1.0)"""
        self.progress = max(0.0, min(1.0, progress))

    def show(self, screen):
        """Affiche la barre de progression"""
        x, y = self.position
        width, height = self.size

        # Dessiner le fond
        pygame.draw.rect(screen, self.bg_color, (x, y, width, height), border_radius=5)

        # Dessiner la barre de progression
        if self.progress > 0:
            fill_width = int(width * self.progress)
            pygame.draw.rect(screen, self.fill_color, (x, y, fill_width, height), border_radius=5)

        # Dessiner la bordure
        pygame.draw.rect(screen, self.border_color, (x, y, width, height), 2, border_radius=5)

        # Afficher le pourcentage au centre
        font = pygame.font.Font(None, 30)
        percentage_text = f"{int(self.progress * 100)}%"
        text_surface = font.render(percentage_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(x + width // 2, y + height // 2))
        screen.blit(text_surface, text_rect)

