""" game utility functions and class definitions """
import subprocess
from random import randrange
from settings import get_attack_animation_duration, get_mv_animation_base_duration, \
    sleap_post_game_phase, sleap_post_game_turn, sleap_waiting_for_other_thread
from unit import units_animating
from game_cmd import GameCmd
from game_ai import ai_evacuate, ai_prevent_evacuation
from hexl import directions, hex_next_to_enemies
from hexl import get_hex_coords_from_direction, hex_occupied #pylint: disable=E0401

class Battalion():
    """ Battalions consist of one or more units.  Battalions have unique movmement phases.  """
    def __init__(self, idx, name):
        self.idx = idx
        self.name = name
        self.units = []
        self.strategy = "uninitialized"

    def write(self, f):
        """ write function. """
        f.write(f"  {self.idx} {self.name} {self.strategy}\n")
        for u in self.units:
            u.write(f)

class Player():
    """ Players can be Human or AI """
    def __init__(self, idx, name):
        self.idx = idx
        self.name = name
        self.battalion = []

    def write(self, f):
        """ Write function. """
        f.write(f"{self.name}\n")
        for bat in self.battalion:
            bat.write(f)

def sanity_check(game_dict):
    """ Check for bad game state."""
    unit_list = []
    hex_list = []
    for player in game_dict["players"]:
        for battalion in player.battalion:
            for this_unit in battalion.units:
                if this_unit.status == "active":
                    unit_list.append(this_unit)
                    hex_list.append(this_unit.hex)
    if len(hex_list) != len(set(hex_list)):
        game_dict["logger"].error("Duplicate hexes {unit_list} {hex_list}")

def active_phases(game_dict):
    """ Are there any active phases? """
    for phase in game_dict["game_phases"]:
        if not phase[1]:
            return True
    return False

def update_phase_gui(game_dict, active_phase):
    """ Write a tmp file, then copy as actual theme. """
    with open("battalion/phase_theme_tmp.json", "w", encoding="utf-8") as f:
        bright_green = "#00EE00"
        dull_green = "#55955e"
        bright_yellow = "#ffff80"
        f.write("{\n    \"@batt_phase_labels\":\n    {\n")
        f.write("        \"colours\":\n        {\n")
        f.write("            \"dark_bg\": \"#25292e\"\n        }\n    }")
        for idx, phase in enumerate(game_dict["game_phases"]):
            f.write(",\n\n")
            f.write(f"    \"#phase_{idx}\":\n")
            f.write("    {\n        \"colours\":\n")
            f.write("        {\n            \"normal_text\": \"")
            if phase == active_phase:
                f.write(f"{bright_yellow}")
            elif phase[1]:
                f.write(f"{dull_green}")
            else:
                f.write(f"{bright_green}")
            f.write("\"\n        }\n    }")
        f.write("\n}\n")

    game_dict["theme_lock"].acquire()
    subprocess.call('mv battalion/phase_theme_tmp.json battalion/phase_theme.json', shell=True)
    game_dict["theme_lock"].release()

    game_dict["update_gui"] = True

def reset_phases(game_dict):
    """ reset the state of the game phases each turn to False (ie not performed this turn.  """
    for i in range(len(game_dict["game_phases"])):
        game_dict["game_phases"][i] = (game_dict["game_phases"][i][0], False)
    update_phase_gui(game_dict, "no active phase")


def process_command(unit, game_cmd, game_dict):
    """ Process a text-based unit command from a player."""
    game_dict["logger"].info(f"    {game_cmd}")
    game_cmd.validate(game_dict)
    if game_cmd.cmd == "EVACUATE":
        unit.status = "off_board"
    elif game_cmd.cmd == "PASS":
        pass
    elif game_cmd.cmd == "MV":
        unit.hex = game_cmd.hexs[-1]
        unit.animation_countdown = unit.animation_duration = get_mv_animation_base_duration() * (len(game_cmd.hexs) - 1)
        unit.animation_cmd = game_cmd
        unit.animating = True
    elif game_cmd.cmd == "ATTACK":
        unit.animation_countdown = unit.animation_duration = get_attack_animation_duration()
        unit.animation_cmd = game_cmd
        unit.animating = True
    elif game_cmd.cmd == "RETREAT":
        # Choose one of the candidates randomly
        candidate_list = []
        for direct in directions:
            adj_hex = get_hex_coords_from_direction(direct, unit.hex, game_dict)
            if adj_hex is not None and \
                not hex_occupied(adj_hex, game_dict) and \
                not hex_next_to_enemies(adj_hex, 1-unit.player, game_dict):
                candidate_list.append(adj_hex)
        if len(candidate_list) == 0:
            # Nowhere to retreat. TODO, handle nowhere to retreat better.
            game_dict["logger"].info( \
                f"      ELIM {unit.get_name()} has nowhere to retreat and is destroyed!")
            unit.hex = (-99, -99)
            unit.status = "destroyed"
        else:
            retreat_hex = candidate_list[randrange(len(candidate_list))]
            derived_cmd = GameCmd(unit, None, "MV", [unit.hex, retreat_hex])
            process_command(unit, derived_cmd, game_dict)

    game_dict["update_screen_req"] += 1


def evaluate_combat(player_num, game_dict):
    """ Evaluate and execute a combat phase. """
    aggressor = game_dict["players"][player_num]
    defender = game_dict["players"][player_num-1]
    for a_battalion in aggressor.battalion:
        for a_unit in a_battalion.units:
            if a_unit.status == "active":
                for d_battalion in defender.battalion:
                    for d_unit in d_battalion.units:
                        if d_unit.status == "active":
                            for direct in directions:
                                adjhex  = get_hex_coords_from_direction( \
                                    direct, a_unit.hex, game_dict)
                                if adjhex is not None :
                                    if adjhex == d_unit.hex:
                                        # Adjacent unit, this means combat
                                        if a_unit.strength > d_unit.strength:
                                            combat_cmd = GameCmd(a_unit, d_unit, "ATTACK", \
                                                [a_unit.hex, d_unit.hex])
                                        else:
                                            combat_cmd = GameCmd(a_unit, None, "RETREAT", \
                                                [a_unit.hex,])
                                        process_command(a_unit, combat_cmd, game_dict)
                                        while units_animating(game_dict):
                                            sleap_waiting_for_other_thread()

def get_active_phase_idx(active_phase, game_dict):
    """ Get the active phase's index. """
    phase_list = game_dict["game_phases"]
    for idx, phase in enumerate(phase_list):
        if phase[0] == active_phase:
            return idx
    assert False

def execute_phase(game_dict, active_phase):
    """ Basic game operation: Execute the input active phase.  """
    if "Combat" in active_phase:
        combat_words = active_phase.split()
        if "Red" in combat_words[0]:
            evaluate_combat(0, game_dict)
        else:
            evaluate_combat(1, game_dict)

    else:
        for player in game_dict["players"]:
            for battalion in player.battalion:
                if battalion.name in active_phase:
                    if battalion.strategy == "Evacuate":
                        for unit in battalion.units:
                            if unit.status == "active":
                                command = ai_evacuate(unit, game_dict)
                                process_command(unit, command, game_dict)
                                while units_animating(game_dict):
                                    sleap_waiting_for_other_thread()
                    else:
                        for unit in battalion.units:
                            if unit.status == "active":
                                command = ai_prevent_evacuation(unit, game_dict)
                                process_command(unit, command, game_dict)
                                while units_animating(game_dict):
                                    sleap_waiting_for_other_thread()
    #update_phase_gui(game_dict)

def next_phase(game_dict):
    """ Basic game operation: Select the next phase randomly and execute it.  """
    candidate_phases = []
    phase_list = game_dict["game_phases"]
    for phase in phase_list:
        if not phase[1]:
            candidate_phases.append(phase)
    active_phase = candidate_phases[randrange(len(candidate_phases))]
    update_phase_gui(game_dict, active_phase)
    if " " in active_phase[0]: # Surround with quotes if phase is multiple words
        game_dict["logger"].info(f"  Phase \"{active_phase[0]}\"")
    else:
        game_dict["logger"].info(f"  Phase {active_phase[0]}")

    while game_dict["update_gui"]:
        sleap_waiting_for_other_thread()
    execute_phase(game_dict, active_phase[0])
    for i, phase in enumerate(phase_list):
        if phase[0] == active_phase[0]:
            phase_list[i] = (active_phase[0], True)
    sleap_post_game_phase()

def play_game_threaded_function(game_dict):
    """ This is the function that starts the game manager thread.  This thread is run in parallel
        to the main (display) thread. """
    reset_phases(game_dict)
    while game_dict["game_running"]:
        turn = game_dict["game_turn"]
        game_dict["logger"].info(f"Turn {turn}")
        while game_dict["game_running"] and active_phases(game_dict):
            next_phase(game_dict)
        reset_phases(game_dict)
        game_dict["game_turn"] += 1
        sleap_post_game_turn()
    game_dict["game_running"] = False
