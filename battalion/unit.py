""" Utilities for hexl units. """
from pygame import draw #pylint: disable=E0401
from hexl import get_hex_offset

def draw_units(screen, game_dict):
    """ Draw all the units. """
    player_unit_color = ((240, 0, 0),(0, 200, 240))
    for player in game_dict["players"]:
        for battalion in player.battalion:
            for this_unit in battalion.units:
                x_offset, y_offset = get_hex_offset(this_unit.x, this_unit.y, game_dict)
                draw.rect(screen, player_unit_color[player.idx], \
                    (x_offset + game_dict['unit_x_offset'], y_offset + game_dict['unit_y_offset'], \
                    game_dict['unit_width'], game_dict['unit_width']))

class Unit():
    """ Basic game piece. """
    def __init__(self, type, strength, x, y, player):
        self.type = type
        self.strength = strength
        self.x = x
        self.y = y
        self.player = player # warning, chance of info in 2 places.
