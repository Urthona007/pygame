""" game utility functions and class definitions """
import subprocess
from random import randrange
from settings import get_attack_animation_duration, get_mv_animation_base_duration, \
    sleap_post_game_phase, sleap_post_game_turn, sleap_waiting_for_other_thread
from unit import get_player_active_units, get_player_active_units_and_hexes, units_animating
from game_cmd import CombatCmd, GameCmd
from game_ai import ai_capture_city_and_destroy, ai_defend_city_and_delay, ai_evacuate, \
     ai_prevent_evacuation
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
        f.write(f"  {self.idx} {self.get_name()} {len(self.units)} \"{self.strategy}\"\n")
        for u in self.units:
            u.write(f)

    def get_name(self):
        """ return name, with double quotes when necessary. """
        if " " in self.name:
            return f"\"{self.name}\""
        return {self.name}
class Player():
    """ Players can be Human or AI """
    def __init__(self, idx, name):
        self.idx = idx
        self.name = name
        self.battalion = []

    def write(self, f):
        """ Write function. """
        f.write(f"{self.name} {len(self.battalion)}\n")
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
        unit.animation_countdown = unit.animation_duration = \
            get_mv_animation_base_duration() * (len(game_cmd.hexes) - 1)
        unit.animation_cmd = game_cmd
        unit.animating = True
    elif game_cmd.cmd == "ATTACK":
        unit.animation_countdown = unit.animation_duration = \
            get_attack_animation_duration()
        unit.animation_cmd = game_cmd
        unit.animating = True
    elif game_cmd.cmd == "RETREAT":
        # Choose one of the candidates randomly
        candidate_list = []
        for direct in directions:
            adj_hex = get_hex_coords_from_direction(direct, unit.hex, game_dict)
            if adj_hex is not None and \
                not hex_occupied(adj_hex, game_dict) and \
                not hex_next_to_enemies(adj_hex, 1-unit.player_num, game_dict):
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

def process_combat_command(combat_cmd, game_dict):
    if combat_cmd.cmd == "Defender -2 and Defender retreat." or \
    combat_cmd.cmd == "Defender -1 and Defender retreat." or \
    combat_cmd.cmd == "Defender retreat." or \
    combat_cmd.cmd == "Both retreat.":
        for d in combat_cmd.defenders:
            game_cmd = GameCmd(d, None, "RETREAT", [d.hex,])
            process_command(d, game_cmd, game_dict)
    else:
        for a in combat_cmd.attackers:
            game_cmd = GameCmd(a, None, "RETREAT", [a.hex,])
            process_command(a, game_cmd, game_dict)

def recursive_find_combat_group(this_unit, \
    already_discovered_hexes, enemy_hexes, ally_hexes, game_dict):
    for direct in directions:
        adjhex  = get_hex_coords_from_direction(direct, this_unit.hex, game_dict)
        if adjhex and adjhex in enemy_hexes and \
            (adjhex not in already_discovered_hexes):
                already_discovered_hexes.append(adjhex)
                recursive_find_combat_group(hex_occupied(adjhex, game_dict), \
                    already_discovered_hexes, ally_hexes, enemy_hexes, game_dict)

class BattleGroup():
    """ A collection of 2 or more contiguous units in combat. """
    def __init__(self, attackers, defenders):
        self.attackers = attackers
        self.defenders = defenders

    def __str__(self):
        return_str = "Battle Group: "
        for a in self.attackers:
            return_str += f"{a.name} {a.hex} "
        return_str += "vs."
        for d in self.defenders:
            return_str += f"{d.name} {d.hex} "
        return return_str

def identify_battle_groups(player_num, game_dict):
    battle_group_list = []
    a_units, a_hexes = get_player_active_units_and_hexes(game_dict["players"][player_num])
    d_units, d_hexes = get_player_active_units_and_hexes(game_dict["players"][1-player_num])
    already_discovered_hexes = []

    for a_unit in a_units:
        if a_unit.hex not in already_discovered_hexes:
            already_discovered_hexes.append(a_unit.hex)
            num_discovered = len(already_discovered_hexes)
            recursive_find_combat_group(a_unit, \
                already_discovered_hexes, d_hexes, a_hexes,
                game_dict)
            if len(already_discovered_hexes) > num_discovered:
                # Battle group found
                attackers = []
                defenders = []
                for hidx in range(num_discovered-1, len(already_discovered_hexes)):
                    discovered_unit = hex_occupied(already_discovered_hexes[hidx], game_dict)
                    if discovered_unit.player_num == a_unit.player_num:
                        attackers.append(discovered_unit)
                    else:
                        defenders.append(discovered_unit)
                battle_group_list.append(BattleGroup(attackers, defenders))
    return battle_group_list

def combat_result(off_pts, def_pts):
    ratio = off_pts/def_pts
    if ratio >= 4.0:
        return "Defender -2 and Defender retreat."
    elif ratio >= 3.0:
        return "Defender -1 and Defender retreat."
    elif ratio >= 2.5:
        return "Defender retreat."
    elif ratio >= 2.0:
        return "Both retreat."
    else:
        return "Retreat."

def execute_battle_group_combat(battle_group, game_dict):
    attack_power = defense_power = 0
    for a in battle_group.attackers:
        attack_power += a.attack
    for d in battle_group.defenders:
        defense_power += d.strength
    result_str = combat_result(attack_power, defense_power)
    combat_cmd = CombatCmd(battle_group.attackers, battle_group.defenders, attack_power, defense_power, result_str)
    game_dict["logger"].info(f"{combat_cmd}")

    process_combat_command(combat_cmd, game_dict)
    while units_animating(game_dict):
        sleap_waiting_for_other_thread()

def evaluate_combat(player_num, game_dict):
    """ Evaluate and execute a combat phase. """

    # Step One: Identify contiguous battle groups.
    battle_group_list = identify_battle_groups(player_num, game_dict)
    game_dict["logger"].info(f"Num battle groups = {len(battle_group_list)}")
    for bg in battle_group_list:
        game_dict["logger"].info(f"BG: {bg}")

    # Step Two: Execute each battle group
    for battle_group in battle_group_list:
        execute_battle_group_combat(battle_group, game_dict)


#    aggressor = game_dict["players"][player_num]
#    defender = game_dict["players"][player_num-1]
#    for a_battalion in aggressor.battalion:
#        for a_unit in a_battalion.units:
#            if a_unit.status == "active":
#                for d_battalion in defender.battalion:
#                    for d_unit in d_battalion.units:
#                        if d_unit.status == "active":
#                            for direct in directions:
#                                adjhex  = get_hex_coords_from_direction( \
#                                    direct, a_unit.hex, game_dict)
#                                if adjhex is not None :
#                                    if adjhex == d_unit.hex:
                                        # Adjacent unit, this means combat
#                                        if a_unit.strength > d_unit.strength:
#                                            combat_cmd = GameCmd(a_unit, d_unit, "ATTACK", \
#                                                [a_unit.hex, d_unit.hex])
#                                        else:
#                                            combat_cmd = GameCmd(a_unit, None, "RETREAT", \
#                                                [a_unit.hex,])
#                                        process_command(a_unit, combat_cmd, game_dict)
#                                        while units_animating(game_dict):
#                                            sleap_waiting_for_other_thread()

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
                    strategy_dict = {"Evacuate": ai_evacuate, \
                        "Prevent Evacuation": ai_prevent_evacuation,
                        "Capture City and Destroy": ai_capture_city_and_destroy,
                        "Defend City and Delay": ai_defend_city_and_delay
                        }
                    for unit in battalion.units:
                        if unit.status == "active":
                            command = strategy_dict[battalion.strategy](unit, game_dict)
                            process_command(unit, command, game_dict)
                            while units_animating(game_dict) and game_dict["game_running"]:
                                sleap_waiting_for_other_thread()
                            if not game_dict["game_running"]:
                                return
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
