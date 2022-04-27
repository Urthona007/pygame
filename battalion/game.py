""" game utility functions and class definitions """
from time import sleep
from ast import literal_eval
from random import randrange
from game_cmd import GameCmd
from unit import get_unit_by_name
from game_ai import ai_evacuate, ai_circle, ai_prevent_evacuation
from hexl import directions, hex_next_to_enemies
from hexl import get_hex_coords_from_direction, hex_occupied #pylint: disable=E0401
import json
import shutil

def active_phases(game_dict):
    """ Are there any active phases? """
    for phase in game_dict["game_phases"]:
        if not phase[1]:
            return True
    return False

def update_phase_gui(game_dict, active_phase):
    with open("battalion/phase_theme_tmp.json", "w") as f:
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

    # Extra debug, could be disabled.
    with open("battalion/phase_theme_tmp.json", "rt") as f:
        try:
            theme_dict = json.load(f)
        except json.decoder.JSONDecodeError:
            print("JSON load failure for phase_theme_tmp.json.  Investigate please.")
            exit(-1)
    game_dict["theme_lock"].acquire()
    shutil.copy("battalion/phase_theme_tmp.json", "battalion/phase_theme.json")
    game_dict["theme_lock"].release()

    game_dict["update_gui"] = True

def reset_phases(game_dict):
    """ reset the state of the game phases each turn to False (ie not performed this turn.  """
    for i in range(len(game_dict["game_phases"])):
        game_dict["game_phases"][i] = (game_dict["game_phases"][i][0], False)
    update_phase_gui(game_dict, "no active phase")


def process_command(unit, game_cmd, game_dict):
    """ Process a text-based unit command from a player."""
    print(f"    {game_cmd}")
    if game_cmd.cmd == "EVACUATE":
        unit.status = "off_board"
    elif game_cmd.cmd == "PASS":
        pass
    elif game_cmd.cmd == "MV":
        unit.x = game_cmd.hexs[-1][0]
        unit.y = game_cmd.hexs[-1][1]
        unit.animation_countdown = unit.animation_duration = 1.0
        unit.animation_cmd = game_cmd
        unit.animating = True
    elif game_cmd.cmd == "ATTACK":
        unit.animation_countdown = unit.animation_duration = 1.0
        unit.animation_cmd = game_cmd
        unit.animating = True
    elif game_cmd.cmd == "RETREAT":
        # Choose one of the candidates randomly
        candidate_list = []
        for direct in directions:
            adjx, adjy = get_hex_coords_from_direction(direct, unit.x, unit.y, game_dict)
            if adjx is not None and adjy is not None and \
                not hex_occupied(adjx, adjy, game_dict) and \
                not hex_next_to_enemies(adjx, adjy, 1-unit.player, game_dict):
                candidate_list.append((adjx, adjy))
        if len(candidate_list) == 0:
            # Nowhere to retreat.
            print(f"{unit.name} has nowhere to retreat and is destroyed!")
            unit.x = -1
            unit.y = -1
            unit.status = "destroyed"
        else:
            retreat_hex = candidate_list[randrange(len(candidate_list))]
            derived_cmd = GameCmd(unit, None, "MV", [(unit.x, unit.y), retreat_hex])
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
                                adjx, adjy = get_hex_coords_from_direction( \
                                    direct, a_unit.x, a_unit.y, game_dict)
                                if adjx is not None and adjy is not None:
                                    if adjx == d_unit.x and adjy == d_unit.y:
                                        # Adjacent unit, this means combat
                                        if a_unit.strength > d_unit.strength:
                                            combat_cmd = GameCmd(a_unit, d_unit, "ATTACK", [(a_unit.x, a_unit.y), (d_unit.x, d_unit.y)])
                                        else:
                                            combat_cmd = GameCmd(a_unit, None, "RETREAT", [(a_unit.x, a_unit.y),])
                                        process_command(a_unit, combat_cmd, game_dict)

def get_active_phase_idx(active_phase, game_dict):
    phase_list = game_dict["game_phases"]
    for idx, phase in enumerate(phase_list):
        if phase[0] == active_phase:
            return idx
    assert(True)

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
                            command = ai_evacuate(unit, game_dict)
                            process_command(unit, command, game_dict)
                    else:
                        for unit in battalion.units:
                            command = ai_prevent_evacuation(unit, game_dict)
                            process_command(unit, command, game_dict)

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
    print(f"  Phase {active_phase[0]}")
    execute_phase(game_dict, active_phase[0])
    for i, phase in enumerate(phase_list):
        if phase[0] == active_phase[0]:
            phase_list[i] = (active_phase[0], True)
    sleep(2)

def play_game_threaded_function(game_dict, max_turns):
    """ This is the function that starts the game manager thread.  This thread is run in parallel
        to the main (display) thread. """
    reset_phases(game_dict)
    while game_dict["game_running"]:
        turn = game_dict["game_turn"]
        print(f"Turn {turn}")
        while game_dict["game_running"] and active_phases(game_dict):
            next_phase(game_dict)
        reset_phases(game_dict)
        game_dict["game_turn"] += 1
    if game_dict["game_turn"] == max_turns:
        print(f"\nGAME OVER: MAX TURNS {max_turns} reached.")
    game_dict["game_running"] = False

class Battalion():
    """ Battalions consist of one or more units.  Battalions have unique movmement phases.  """
    def __init__(self, idx, name):
        self.idx = idx
        self.name = name
        self.units = []
        self.strategy = "uninitialized"

class Player():
    """ Players can be Human or AI """
    def __init__(self, idx, name):
        self.idx = idx
        self.name = name
        self.battalion = []
