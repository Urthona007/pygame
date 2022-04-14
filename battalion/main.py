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

def ai_circle(battalion):
    for unit in battalion.units:
        newx, newy = get_hex_coords_from_direction(directions[game_dict["game_turn"]%6], unit.x, unit.y, game_dict)
        unit.x = newx
        unit.y = newy

from hexl import directions
def ai_evacuate(battalion):
    level = 0

    # Create hexnode list counting away from the evacuation hex.
    # Nodes are in form ((x,y), level)
    hexnode_list = [(game_dict["evacuation_hex"], level), ]
    while True:
        level = level + 1
        new_hexnode_list = []
        for hex in hexnode_list:
            if hex[1] == level - 1:
                for direct in directions:
                    adjx, adjy = get_hex_coords_from_direction(direct, hex[0][0], hex[0][1], game_dict)
                    if adjx is not None and adjy is not None:
                        eligible = True
                        for existing_hex in hexnode_list:
                            if existing_hex[0][0] == adjx and existing_hex[0][1] == adjy:
                                eligible = False
                                break
                        if eligible:
                            new_hexnode_list.append(((adjx, adjy), level))
        if len(new_hexnode_list) == 0:
            break
        else:
            for hex in new_hexnode_list:
                hexnode_list.append(hex)

    for unit in battalion.units:
        for hex in hexnode_list:
            if unit.x == hex[0][0] and unit.y == hex[0][1]:
                hexlevel = hex[1]
                if hexlevel == 0:
                    print(f"Evacuating {unit.name}")
                    unit.status = "off_board"
                    break
                else:
                    candidate_list = []
                    for direct in directions:
                        adjx, adjy = get_hex_coords_from_direction(direct, unit.x, unit.y, game_dict)
                        if adjx is not None and adjy is not None:
                            for adjhex in hexnode_list:
                                if adjx == adjhex[0][0] and adjy == adjhex[0][1] and adjhex[1] < hexlevel:
                                    candidate_list.append(adjhex)
                    assert len(candidate_list)
                    next_hexnode = candidate_list[randrange(len(candidate_list))]
                    unit.x = next_hexnode[0][0]
                    unit.y = next_hexnode[0][1]
                    break

def execute_phase(game_dict, active_phase):
    if "combat" in active_phase:
        evaluate_combat(active_phase)
    else:
        for player in game_dict["players"]:
            for battalion in player.battalion:
                if battalion.name in active_phase:
                    if battalion.strategy == "Evacuate":
                        ai_evacuate(battalion)
                    else:
                        ai_circle(battalion)
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
