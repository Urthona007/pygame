""" game utility functions and class definitions """
from time import sleep
from ast import literal_eval
from random import randrange
from game_ai import evaluate_combat, ai_evacuate, ai_circle

def active_phases(game_dict):
    """ Are there any active phases? """
    for phase in game_dict["game_phases"]:
        if not phase[1]:
            return True
    return False

def reset_phases(game_dict):
    """ reset the state of the game phases each turn to False (ie not performed this turn.  """
    for i in range(len(game_dict["game_phases"])):
        game_dict["game_phases"][i] = (game_dict["game_phases"][i][0], False)

def process_command(unit, command):
    """ Process a text-based unit command from a player."""
    print('\t' + command)
    two_strings = command.split(":")
    if two_strings[1].find("EVACUATE") != -1:
        unit.status = "off_board"
    elif two_strings[1].find("MV") != -1:
        move_strings = two_strings[1].split()
        assert "MV" == move_strings[0]
        start_hex = literal_eval(move_strings[1]+move_strings[2])
        assert "->" == move_strings[3]
        end_hex = literal_eval(move_strings[4]+move_strings[5])
        unit.x = end_hex[0]
        unit.y = end_hex[1]

def execute_phase(game_dict, active_phase):
    """ Basic game operation: Execute the input active phase.  """
    if "combat" in active_phase:
        evaluate_combat(active_phase)
    else:
        for player in game_dict["players"]:
            for battalion in player.battalion:
                if battalion.name in active_phase:
                    if battalion.strategy == "Evacuate":
                        for unit in battalion.units:
                            command = ai_evacuate(unit, game_dict)
                            process_command(unit, command)
                    else:
                        for unit in battalion.units:
                            command = ai_circle(unit, game_dict)
                            process_command(unit, command)
                    game_dict["update_screen"] = True

def next_phase(game_dict):
    """ Basic game operation: Select the next phase randomly and execute it.  """
    candidate_phases = []
    phase_list = game_dict["game_phases"]
    for phase in phase_list:
        if not phase[1]:
            candidate_phases.append(phase)
    active_phase = candidate_phases[randrange(len(candidate_phases))]
    print(f"Executing {active_phase[0]}")
    execute_phase(game_dict, active_phase[0])
    for i in enumerate(phase_list):
        if phase_list[i][0] == active_phase[0]:
            phase_list[i] = (active_phase[0], True)
    sleep(1)

def play_game_threaded_function(game_dict, max_turns):
    """ This is the function that starts the game manager thread.  This thread is run in parallel
        to the main (display) thread. """
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
