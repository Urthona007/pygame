""" Battalion Main """
import pygame
from hexl import get_hex_coords_from_direction #pylint: disable=E0401
import unit
from hexl import draw_hexs
from hexl import directions
from threading import Thread
from time import sleep
from random import randrange

def active_phases(game_dict):
    for phase in game_dict["game_phases"]:
        if not phase[1]:
            return True

def reset_phases(game_dict):
    for i in range(len(game_dict["game_phases"])):
        game_dict["game_phases"][i] = (game_dict["game_phases"][i][0], False)

def evaluate_combat(active_phase):
    return

def ai_circle(battalion, unit, game_dict):
    newx, newy = get_hex_coords_from_direction(directions[game_dict["game_turn"]%6], unit.x, unit.y, game_dict)
    return(f"{unit.name}: MV ({unit.x}, {unit.y}) -> ({newx}, {newy})")


from hexl import directions
import numpy as np
import queue
def ai_evacuate(battalion, unit, game_dict):
    return_str = []
    level = 0

    # Create hexnode list counting away from the evacuation hex.
    # Nodes are in form ((x,y), level)
    hexmap = np.full((game_dict["map_width"], game_dict["map_height"]), 99)
    hexmap[game_dict["evacuation_hex"][0]][game_dict["evacuation_hex"][1]] = 0

    hexnode_queue = queue.Queue()
    hexnode_queue.put(game_dict["evacuation_hex"])
    while not hexnode_queue.empty():
        hex = hexnode_queue.get()
        for direct in directions:
            adjx, adjy = get_hex_coords_from_direction(direct, hex[0], hex[1], game_dict)
            if adjx is not None and adjy is not None and hexmap[adjx][adjy] == 99:
                hexmap[adjx][adjy] = hexmap[hex[0]][hex[1]]+1
                hexnode_queue.put((adjx, adjy))

    if hexmap[unit.x][unit.y] == 0:
        return(f"{unit.name}: EVACUATE")
    else:
        candidate_list = []
        for direct in directions:
            adjx, adjy = get_hex_coords_from_direction(direct, unit.x, unit.y, game_dict)
            if adjx is not None and adjy is not None and hexmap[adjx][adjy] < hexmap[unit.x][unit.y]:
                candidate_list.append((adjx, adjy))
        assert len(candidate_list)
        next_hex = candidate_list[randrange(len(candidate_list))]
        return(f"{unit.name}: MV ({unit.x}, {unit.y}) -> ({next_hex[0]}, {next_hex[1]})")

def process_command(unit, command):
    print('\t' + command)
    two_strings = command.split(":")
    if two_strings[1].find("EVACUATE") != -1:
         unit.status = "off_board"
    elif two_strings[1].find("MV") != -1:
        move_strings = two_strings[1].split()
        assert "MV" == move_strings[0]
        start_hex = eval(move_strings[1]+move_strings[2])
        assert "->" == move_strings[3]
        end_hex = eval(move_strings[4]+move_strings[5])
        unit.x = end_hex[0]
        unit.y = end_hex[1]

def execute_phase(game_dict, active_phase):
    if "combat" in active_phase:
        evaluate_combat(active_phase)
    else:
        for player in game_dict["players"]:
            for battalion in player.battalion:
                if battalion.name in active_phase:
                    if battalion.strategy == "Evacuate":
                        for unit in battalion.units:
                            command = ai_evacuate(battalion, unit, game_dict)
                            process_command(unit, command)
                    else:
                        for unit in battalion.units:
                            command = ai_circle(battalion, unit, game_dict)
                            process_command(unit, command)
                    game_dict["update_screen"] = True

def next_phase(game_dict):
    candidate_phases = []
    phase_list = game_dict["game_phases"]
    for phase in phase_list:
        if not phase[1]:
            candidate_phases.append(phase)
    active_phase = candidate_phases[randrange(len(candidate_phases))]
    print(f"Executing {active_phase[0]}")
    execute_phase(game_dict, active_phase[0])
    for i in range(len(phase_list)):
        if phase_list[i][0] == active_phase[0]:
            phase_list[i] = (active_phase[0], True)
    sleep(1)

def play_game_threaded_function(game_dict, max_turns):
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
    def __init__(self, idx, name):
        self.idx = idx
        self.name = name
        self.units = []
        self.strategy = "uninitialized"

class Player():
    def __init__(self, idx, name):
        self.idx = idx
        self.name = name
        self.battalion = []

def draw_map(screen, a_game_dict):
    """ Draw game map. """
    draw_hexs(screen, a_game_dict)

pygame.init()
scenario = "Hounds"
if scenario == "Hounds":
    game_dict = {'name': 'Battalion', 'display_width' : 640, 'display_height' : 480, \
        'bkg_color': (50, 50, 50), 'map_width': 11, 'map_height': 8, 'map_multiplier': 50, \
        'map_border' : 8, 'unit_width': 32, 'unit_x_offset': 18, 'unit_y_offset': 34, \
        "game_turn": 1, \
        "game_phases":[("Red Combat", False), ("Blu Combat", False)], "game_running": True, \
        "evacuation_hex": (0,4)}

    def player_0_victory_condition(game_dict):
        for battalion in game_dict["players"][1].battalion:
            for unit in battalion.units:
                if unit.status == "active" or unit.status == "off_board":
                    return None
        game_dict["game_running"] = False
        print("Red Victory, all Blu forces eliminated!")
        return "Red Victory, all Blu forces eliminated!"

    def player_1_victory_condition(game_dict):
        if game_dict["game_turn"] == 10:
            game_dict["game_running"] = False
            print("Blu Victory, Turn 10 Blufor still alive.")
            return "Blu Victory, Turn 10 Blufor still alive."
        for battalion in game_dict["players"][1].battalion:
            for unit in battalion.units:
                if unit.status == "active":
                    return None
                assert unit.status == "off_board"
        game_dict["game_running"] = False
        print("Blu Victory, all Blu forces evacuated!")
        return "Blu Victory, all Blu forces evacuated!"

    game_dict["players"] = (Player(0, "Red"), Player(1, "Blu"))
    game_dict["players"][0].battalion.append(Battalion(0, "Rommel"))
    game_dict["players"][0].battalion[0].strategy = "Seek and Destroy"
    game_dict["players"][0].battalion[0].units.append(unit.Unit("infantry", "1st Company", 2, 4, 2, 0))
    game_dict["players"][0].victory_condition = lambda player1_num_units: len(game_dict["players"][1])
    game_dict["players"][1].battalion.append(Battalion(0, "DeGaulle"))
    game_dict["players"][1].battalion[0].strategy = "Evacuate"
    game_dict["players"][1].battalion[0].units.append(unit.Unit("militia", "Resistance Fighters", 1, 7, 5, 1))

for player in game_dict["players"]:
    for battalion in player.battalion:
        game_dict["game_phases"].append((f"{battalion.name} Movement", False))

pygame.display.set_caption(game_dict['name']) # NOTE: this is not working.

game_dict["game_running"] = True
game_screen = pygame.display.set_mode((game_dict['display_width'], game_dict['display_height']))
game_dict["update_screen"] = True



first_time = True
gamemaster_thread = None
while (not player_0_victory_condition(game_dict)) and (not player_1_victory_condition(game_dict)) and game_dict["game_running"]:
    for event in pygame.event.get():
        # print(event)
        if event.type == pygame.QUIT:
            print("GAME ABORTED BY USER.")
            game_dict["game_running"] = False
    if game_dict["update_screen"]:
        game_screen.fill(game_dict['bkg_color'])
        draw_map(game_screen, game_dict)
        unit.draw_units(game_screen, game_dict)
        pygame.display.update()
        game_dict["update_screen"] = False
        if first_time:
            first_time = False
            if __name__ == "__main__":
                sleep(1)
                gamemaster_thread = Thread(target = play_game_threaded_function, args = (game_dict, 10))
                gamemaster_thread.start()
                #    thread.join()
                #    print("thread finished...exiting")
if gamemaster_thread:
    gamemaster_thread.join()
pygame.quit()
