""" Utilities for hexl units. """
from numpy import cos, pi
from hexl import get_hex_offset
from pygame import draw #pylint: disable=E0401

class Unit():
    """ Basic game piece. """
    def __init__(self, unit_type, name, strength, movement_allowance, starting_hex, player):
        self.type = unit_type
        self.name = name
        self.strength = strength
        self.movement_allowance = movement_allowance
        self.hex = starting_hex
        self.player = player # warning, chance of info in 2 places.
        self.status = "active"
        self.animating = False
        self.animation_cmd = ""
        self.animation_countdown = 2 # seconds
        self.animation_duration = 2 # seconds

    def write(self, f):
        """ write function """
        f.write(f"    {self.type} {self.get_name()} {self.strength} {self.hex}\n")

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

                        # Determine number of spans and span_duration.  A 2 hex move would have 2
                        # spans.
                        num_spans = len(game_cmd.hexs) - 1
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
                            get_hex_offset(game_cmd.hexs[start_span], game_dict)
                        end_x_offset, end_y_offset = \
                            get_hex_offset(game_cmd.hexs[start_span+1], game_dict)

                        # Handle animation based on whether a MV or an ATTACK
                        if game_cmd.cmd == "MV":
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
                            assert game_cmd.cmd == "ATTACK"
                            # 0->1 to 0->1->0->1->0 double thrust
                            interpolation = attack_double_pulse_interpolation(overall_interpolation)
                            x_offset = start_x_offset + (end_x_offset - start_x_offset) \
                                * interpolation
                            y_offset = start_y_offset + (end_y_offset - start_y_offset) \
                                * interpolation

                        # Advance countdown time.  When countdown is complete, update the game
                        # status with results of the completed command.
                        this_unit.animation_countdown -= time_delta
                        if this_unit.animation_countdown < 0:
                            this_unit.animation_countdown = 0
                            this_unit.animating = False
                            if game_cmd.cmd == "ATTACK":
                                game_dict["logger"].info( \
                                    f"ELIM {game_cmd.e_unit.get_name()} destroyed!")
                                game_cmd.e_unit.hex = (-99, -99)
                                game_cmd.e_unit.status = "destroyed"

                        animating = True
                    else:
                        x_offset, y_offset = get_hex_offset(this_unit.hex, game_dict)

                    draw.rect(screen, player_unit_color[player.idx], \
                        (x_offset + game_dict['unit_x_offset'], \
                        y_offset + game_dict['unit_y_offset'], \
                        game_dict['unit_width'], game_dict['unit_width']))
    return animating
