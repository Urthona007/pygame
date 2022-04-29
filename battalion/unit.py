""" Utilities for hexl units. """
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

    def write(self, f):
        f.write(f"    {self.type} {self.get_name()} {self.strength} {self.x} {self.y}\n")

    def get_name(self):
        if " " in self.name:
            return f"\"{self.name}"
        return {self.name}

def get_unit_by_name(name, game_dict):
    """ Get unit by name. """
    for player in game_dict["players"]:
        for battalion in player.battalion:
            for this_unit in battalion.units:
                if this_unit.name == name:
                    return this_unit
    game_dict["logger"].error(f"unit {name} not found?!")
    return None

def attack_double_pulse_interpolation(interpolation):
    """ Get interpolation value for a double pulse attack animation.  """
    if interpolation < 0.25:
        interpolation *= 2
    elif interpolation < 0.5:
        interpolation = 0.5 - (interpolation - 0.25)*2
    elif interpolation < 0.75:
        interpolation = (interpolation - 0.5) * 2
    else:
        interpolation = 0.5 - (interpolation - 0.75)*2
    return interpolation

def draw_units(screen, game_dict, time_delta):
    """ Draw all the units. """
    player_unit_color = ((240, 0, 0),(0, 200, 240))
    animating = False
    for player in game_dict["players"]:
        for battalion in player.battalion:
            for this_unit in battalion.units:
                if this_unit.status == "active":
                    if this_unit.animating:
                        game_cmd = this_unit.animation_cmd
                        start_x_offset, start_y_offset = \
                            get_hex_offset(game_cmd.hexs[0], game_dict)
                        end_x_offset, end_y_offset = get_hex_offset(game_cmd.hexs[1], game_dict)
                        interpolation = \
                            (this_unit.animation_duration - this_unit.animation_countdown) \
                            / this_unit.animation_duration
                        assert 0.0 <= interpolation <= 1.0
                        if game_cmd.cmd == "MV":
                            x_offset = start_x_offset + (end_x_offset - start_x_offset) \
                                * interpolation
                            y_offset = start_y_offset + (end_y_offset - start_y_offset) \
                                * interpolation
                        else:
                            assert game_cmd.cmd == "ATTACK"
                            # 0->1 to 0->1->0->1->0 double thrust
                            interpolation = attack_double_pulse_interpolation(interpolation)
                            x_offset = start_x_offset + (end_x_offset - start_x_offset) \
                                * interpolation
                            y_offset = start_y_offset + (end_y_offset - start_y_offset) \
                                * interpolation
                        this_unit.animation_countdown -= time_delta
                        if this_unit.animation_countdown < 0:
                            this_unit.animation_countdown = 0
                            this_unit.animating = False
                            if game_cmd.cmd == "ATTACK":
                                game_dict["logger"].info(f"{game_cmd.e_unit.name} destroyed!")
                                game_cmd.e_unit.x = game_cmd.e_unit.y = -1
                                game_cmd.e_unit.status = "destroyed"
                        animating = True
                    else:
                        x_offset, y_offset = get_hex_offset((this_unit.x, this_unit.y), game_dict)

                    draw.rect(screen, player_unit_color[player.idx], \
                        (x_offset + game_dict['unit_x_offset'], \
                        y_offset + game_dict['unit_y_offset'], \
                        game_dict['unit_width'], game_dict['unit_width']))
    return animating
