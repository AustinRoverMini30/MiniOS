import pygame


class Tile:
    def __init__(self, size, position, color, icon="", icon_size=(50,50), text="", font_size=24, methode=None,
                 pressed_color=None, text_color=(255, 255, 255), pressed_text_color=None, animated=False):
        self.size = size
        self.position = position
        self.color = color
        self.pressed_color = pressed_color if pressed_color else tuple(max(0, c - 50) for c in color)
        self.text = text
        self.font_size = font_size
        self.text_color = text_color
        self.pressed_text_color = pressed_text_color if pressed_text_color else tuple(max(0, c - 50) for c in text_color)
        self.icon_size = icon_size
        self.icon_path = icon
        self.icon = None
        if icon:
            self.icon = pygame.image.load(icon).convert_alpha()
            self.icon = pygame.transform.scale(self.icon, self.icon_size)
        self.hitbox = pygame.Rect(position[0], position[1], size[0], size[1])
        self.method = methode
        self.is_pressed = False

    def load_and_color_icon(self, color):
        """Charge et colorie l'icône avec la couleur spécifiée"""
        if not self.icon_path:
            return None
        try:
            surface = pygame.image.load(self.icon_path).convert_alpha()
            surface = pygame.transform.scale(surface, self.icon_size)

            # Création du filtre de couleur
            color_surf = pygame.Surface(self.icon_size, pygame.SRCALPHA)
            color_surf.fill(color)

            # Application de la couleur (multiplication)
            surface.blit(color_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            return surface
        except Exception as e:
            print(f"Erreur chargement {self.icon_path}: {e}")
            return None

    def show(self, fenetre):
        current_color = self.pressed_color if self.is_pressed else self.color
        # Dessiner uniquement le contour (border) au lieu du rectangle plein
        # width=3 pour un contour de 3 pixels
        pygame.draw.rect(fenetre, current_color, (*self.position, *self.size), width=1, border_radius=10)

        # Couleur de l'icône et du texte selon l'état
        icon_color = self.pressed_text_color if self.is_pressed else self.text_color
        decalage = 10 if self.text else 0

        if self.icon_path:
            colored_icon = self.load_and_color_icon(icon_color)
            if colored_icon:
                icon_rect = colored_icon.get_rect(center=(self.position[0] + self.size[0] // 2, self.position[1] + self.size[1] // 2 - decalage))
                fenetre.blit(colored_icon, icon_rect)

        if self.text:
            font = pygame.font.Font(None, self.font_size)
            text_surface = font.render(self.text, True, icon_color)
            text_rect = text_surface.get_rect(center=(self.position[0] + self.size[0] // 2, self.position[1] + self.size[1] - 30))
            fenetre.blit(text_surface, text_rect)

    def check_click(self, pos):
        """Vérifie si la position est dans la hitbox"""
        return self.hitbox.collidepoint(pos)

    def press(self):
        """Active l'état pressé"""
        self.is_pressed = True

    def release(self):
        """Désactive l'état pressé"""
        self.is_pressed = False

    def on_click(self):
        if self.method is not None:
            self.method()


class ToggleTile(Tile):
    def __init__(self, size, position, color, icon="", icon_size=(50, 50), text="", font_size=24, methode=None,
                 pressed_color=None, text_color=(255, 255, 255), pressed_text_color=None):
        super().__init__(size, position, color, icon, icon_size, text, font_size, methode, pressed_color,
                         text_color, pressed_text_color)
        self.is_toggled = False
        self.rotation_angle = 0

    def show(self, fenetre):
        # Couleur selon l'état toggle au lieu de pressed
        current_color = self.pressed_color if self.is_toggled else self.color

        # Dessiner le contour
        pygame.draw.rect(fenetre, current_color, (*self.position, *self.size), width=1, border_radius=10)

        # Couleur de l'icône et du texte selon l'état toggle
        icon_color = self.pressed_text_color if self.is_toggled else self.text_color
        decalage = 10 if self.text else 0

        if self.icon_path:
            colored_icon = self.load_and_color_icon(icon_color)
            if colored_icon:
                # Si toggled, appliquer la rotation
                if self.is_toggled:
                    # Incrémenter l'angle de rotation pour l'animation
                    self.rotation_angle = (self.rotation_angle + 20) % 360
                    colored_icon = pygame.transform.rotate(colored_icon, self.rotation_angle)

                icon_rect = colored_icon.get_rect(center=(self.position[0] + self.size[0] // 2,
                                                          self.position[1] + self.size[1] // 2 - decalage))
                fenetre.blit(colored_icon, icon_rect)

        if self.text:
            font = pygame.font.Font(None, self.font_size)
            text_surface = font.render(self.text, True, icon_color)
            text_rect = text_surface.get_rect(center=(self.position[0] + self.size[0] // 2,
                                                      self.position[1] + self.size[1] - 30))
            fenetre.blit(text_surface, text_rect)

    def on_click(self):
        # Toggle l'état au lieu d'appeler directement la méthode
        self.is_toggled = not self.is_toggled
        if self.method is not None:
            self.method(self.is_toggled)
