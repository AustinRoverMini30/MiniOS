import pygame


class Indicator:

    def __init__(self, size, color_on, color_off, icon, methode=None, text=""):
        self.size = size
        self.color_on = color_on
        self.color_off = color_off
        self.state = False
        self.icon = pygame.image.load(icon)
        self.icon = pygame.transform.scale(self.icon, (size[1] - 10, size[1] - 10))
        self.methode = methode
        self.hitbox = pygame.Rect(0, 0, size[0], size[1])
        self.text = text

    def show(self, fenetre, position):
        color = self.color_on if self.state else self.color_off
        pygame.draw.rect(fenetre, color, (*position, *self.size), border_radius=2)
        fenetre.blit(self.icon, self.icon.get_rect(center=(position[0] + self.size[0] // 2, position[1] + self.size[1] // 2)))
        self.hitbox = pygame.Rect(position[0], position[1], self.size[0], self.size[1])

    def on_click(self):
        if (self.methode != None):
            self.methode()

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
