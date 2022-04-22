""" Utilities for hexl units. """
from ast import literal_eval
from hexl import get_hex_offset
from pygame import draw #pylint: disable=E0401

class Unit():
    """ Basic game piece. """
    def __init__(self, unit_type, name, strength, x, y, player):
        self.type = unit_type
        self.name = name
        self.strength = strength
        self.x = x
        self.y = y
        self.player = player # warning, chance of info in 2 places.
        self.status = "active"
        self.animating = False
        self.animation_cmd = ""
        self.animation_countdown = 2 # seconds
        self.animation_duration = 2 # seconds

def get_unit_by_name(name, game_dict):
    """ Get unit by name. """
    for player in game_dict["players"]:
        for battalion in player.battalion:
            for this_unit in battalion.units:
                if this_unit.name == name:
                    return this_unit
    print(f"ERROR: unit {name} not found?!")
    return None

def draw_units(screen, game_dict, time_delta):
    """ Draw all the units. """
    player_unit_color = ((240, 0, 0),(0, 200, 240))
    animating = False
    for player in game_dict["players"]:
        for battalion in player.battalion:
            for this_unit in battalion.units:
                if this_unit.status == "active":
                    if this_unit.animating:
                        cmd = this_unit.animation_cmd
                        assert "MV" == cmd[0]
                        start_hex = literal_eval(cmd[1]+cmd[2])
                        start_x_offset, start_y_offset = get_hex_offset(start_hex[0], start_hex[1], game_dict)
                        assert "->" == cmd[3]
                        end_hex = literal_eval(cmd[4]+cmd[5])
                        end_x_offset, end_y_offset = get_hex_offset(end_hex[0], end_hex[1], game_dict)
                        interpolation = (this_unit.animation_duration - this_unit.animation_countdown) \
                            / this_unit.animation_duration
                        x_offset = start_x_offset + (end_x_offset - start_x_offset) * interpolation
                        y_offset = start_y_offset + (end_y_offset - start_y_offset) * interpolation
                        this_unit.animation_countdown -= time_delta
                        if this_unit.animation_countdown < 0:
                            this_unit.animation_countdown = 0
                            this_unit.animating = False
                        animating = True
                    else:
                        x_offset, y_offset = get_hex_offset(this_unit.x, this_unit.y, game_dict)

                    draw.rect(screen, player_unit_color[player.idx], \
                        (x_offset + game_dict['unit_x_offset'], \
                        y_offset + game_dict['unit_y_offset'], \
                        game_dict['unit_width'], game_dict['unit_width']))
    return animating