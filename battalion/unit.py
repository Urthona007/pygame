import hex
import pygame

def draw_units(screen, units, game_dict):
    for player in units:
        for unit in player:
            x_offset, y_offset = hex.get_hex_offset(unit.x, unit.y, game_dict)
            rect = pygame.draw.rect(screen, (0, 240, 240), \
                (x_offset + game_dict['unit_x_offset'], y_offset + game_dict['unit_y_offset'], \
                 game_dict['unit_width'], game_dict['unit_width']))

class unit():
    def __init__(self, type, strength, x, y, player):
        self.type = type
        self.strength = strength
        self.x = x
        self.y = y
        self.player = player # warning, chance of info in 2 places.