""" Utilities for hexl units. """
from numpy import cos, pi
from hexl import get_hex_offset
from pygame import draw #pylint: disable=E0401

class Unit():
    """ Basic game piece. """
    def __init__(self, *, unit_type, name, attack, strength, movement_allowance, starting_hex, \
        player_num):
        self.type = unit_type
        self.name = name
        self.attack = attack
        self.strength = strength
        self.health = 2
        self.movement_allowance = movement_allowance
        self.hex = starting_hex
        self.player_num = player_num # warning, chance of info in 2 places.
        self.status = "active"
        self.animating = False
        self.animation_cmd = ""
        self.animation_countdown = 2 # seconds, these get overwritten
        self.animation_duration = 2 # seconds

    def write(self, f):
        """ write function """
        f.write(f"    {self.type} {self.get_name()} {self.attack} {self.strength} {self.movement_allowance} {self.hex}\n")

    def get_name(self):
        """ return name, with double quotes when necessary. """
        if " " in self.name:
            return f"\"{self.name}\""
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

def get_animating_unit_hex_offset(this_unit, game_dict):
    """ Get the hex offset of an animating unit."""
    # Determine number of spans and span_duration.  A 2 hex move would have 2
    # spans.
    num_spans = len(this_unit.animation_cmd.hexes) - 1
    span_duration = this_unit.animation_duration / num_spans

    # Overall interpolation is where we are in the entire animation.
    # Local interpolation will be where we are on a span.  Solve for
    # these along with the start_span index into the hex list
    overall_interpolation = \
        (this_unit.animation_duration - this_unit.animation_countdown) \
        / this_unit.animation_duration
    assert 0.0 <= overall_interpolation <= 1.0
    start_span = 0
    while (start_span+1)*span_duration < \
        this_unit.animation_duration - this_unit.animation_countdown:
        start_span += 1

    start_x_offset, start_y_offset = \
        get_hex_offset(this_unit.animation_cmd.hexes[start_span], game_dict)
    end_x_offset, end_y_offset = \
        get_hex_offset(this_unit.animation_cmd.hexes[start_span+1], game_dict)

    # Handle animation based on whether a MV or an ATTACK
    if this_unit.animation_cmd.cmd == "MV":
        # Add in "snap"
        local_interpolation = (overall_interpolation - start_span/num_spans) \
                * num_spans
        assert 0.0 <= local_interpolation <= 1.0
        local_interpolation = (1 - cos(local_interpolation*pi))/2
        x_offset = start_x_offset + (end_x_offset - start_x_offset) \
            * local_interpolation
        y_offset = start_y_offset + (end_y_offset - start_y_offset) \
            * local_interpolation
    else:
        assert this_unit.animation_cmd.cmd == "ATTACK"
        # 0->1 to 0->1->0->1->0 double thrust
        interpolation = attack_double_pulse_interpolation(overall_interpolation)
        x_offset = start_x_offset + (end_x_offset - start_x_offset) \
            * interpolation
        y_offset = start_y_offset + (end_y_offset - start_y_offset) \
            * interpolation
    return x_offset, y_offset

def draw_units(screen, game_dict, time_delta):
    """ Draw all the units. """
    player_unit_color = ((240, 0, 0),(0, 200, 240))
    animating = False
    for p_idx, player in enumerate(game_dict["players"]):
        unit_list = get_player_active_units(player)
        for this_unit in unit_list:
            if this_unit.animating:
                x_offset, y_offset = get_animating_unit_hex_offset(this_unit, game_dict)

                # Advance countdown time.  When countdown is complete, update the game
                # status with results of the completed command.
                this_unit.animation_countdown -= time_delta
                if this_unit.animation_countdown < 0:
                    this_unit.animation_countdown = 0
                    this_unit.animating = False
                    if this_unit.animation_cmd.cmd == "ATTACK":
                        game_dict["logger"].info( \
                            f"ELIM {this_unit.animation_cmd.e_unit.get_name()} destroyed!")
                        this_unit.animation_cmd.e_unit.hex = (-99, -99)
                        this_unit.animation_cmd.e_unit.status = "destroyed"
                    elif this_unit.animation_cmd.cmd == "MV":
                        this_unit.hex = this_unit.animation_cmd.hexes[-1]
                animating = True
            else:
                x_offset, y_offset = get_hex_offset(this_unit.hex, game_dict)

            unit_x_offset = game_dict["map_multiplier"] * 0.35
            unit_y_offset = game_dict["map_multiplier"] * 0.675
            unit_width = game_dict["map_multiplier"] * 0.67

            draw.rect(screen, player_unit_color[p_idx], \
                (x_offset + unit_x_offset, \
                y_offset + unit_y_offset, \
                unit_width, unit_width))
    return animating

def units_animating(game_dict):
    """ Returns true if any units animating."""
    unit_list = get_active_units(game_dict)
    for u in unit_list:
        if u.animating:
            return True
    return False

def get_active_units(game_dict):
    """ Get list of all active units."""
    unit_list = get_player_active_units(game_dict["players"][0])
    unit_list += get_player_active_units(game_dict["players"][1])
    return unit_list

def get_player_active_units(player):
    """ Get list of all of a player's units."""
    unit_list = []
    for battalion in player.battalion:
        for unit in battalion.units:
            if unit.status == "active":
                unit_list.append(unit)
    return unit_list

def get_player_active_units_and_hexes(player):
    """ Get list of hexes occupied by a player's units."""
    unit_list = get_player_active_units(player)
    unit_hex_list = []
    for u in unit_list:
        unit_hex_list.append(u.hex)
    return unit_list, unit_hex_list
