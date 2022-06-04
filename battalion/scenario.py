from game import Battalion, Player
from hexl import get_random_edge_hex, get_random_hex
from unit import Unit

def create_hounds_scenario(game_dict, logname, randomize):

    # Define the two players' victory conditions
    def hound_player_0_victory_condition(game_dict):
        """ Player 0 "Hound" Scenario Hound victory conditions """
        for battalion in game_dict["players"][1].battalion:
            for unit in battalion.units:
                if unit.status in ("active", "off_board"):
                    return None
        game_dict["game_running"] = False
        game_dict["logger"].info("Victory Red \"All Blu forces eliminated!\"")
        return "Victory Red: All Blu forces eliminated!"

    def hound_player_1_victory_condition(game_dict):
        """ Player 1 "Rabbit" Scenario Hound victory conditions """
        if game_dict["game_turn"] == 10:
            game_dict["game_running"] = False
            game_dict["logger"].info("Victory Blu \"Turn 10 Blufor still alive.\"")
            return "Victory Blu: Turn 10 Blufor still alive."
        for battalion in game_dict["players"][1].battalion:
            for unit in battalion.units:
                if unit.status != "off_board":
                    return None
        game_dict["game_running"] = False
        game_dict["logger"].info("Victory Blu \"All Blu forces evacuated!\"")
        return "Victory Blu: All Blu forces evacuated!"

    game_dict["victory_condition"] = (hound_player_0_victory_condition, hound_player_1_victory_condition)
    game_dict["evacuation_hex"] = (0,2)
    if randomize:
        game_dict["evacuation_hex"] = get_random_edge_hex(game_dict)
        exclude_hexlist = [game_dict["evacuation_hex"],]
    game_dict["bears_den"] = None
    game_dict['map_width'] = 11
    game_dict['map_height'] = 8
    game_dict['map_multiplier'] = 47
    with open (logname, mode='w', encoding="utf-8") as f:
        f.write(f"{game_dict.__str__()}\n")
    game_dict["players"] = (Player(0, "Red"), Player(1, "Blu"))
    game_dict["players"][0].battalion.append(Battalion(0, "Rommel"))
    game_dict["players"][0].battalion[0].strategy = "Prevent Evacuation"

    start_hex = (6, 4)
    if randomize:
        start_hex = get_random_hex(game_dict, exclude_hexlist)
        exclude_hexlist.append(start_hex)
    game_dict["players"][0].battalion[0].units.append( \
        Unit(unit_type="infantry", name="1st Company", strength=2, movement_allowance=2, \
            starting_hex=start_hex, player=0))

    start_hex = (2, 1)
    if randomize:
        start_hex = get_random_hex(game_dict, exclude_hexlist)
        exclude_hexlist.append(start_hex)
    game_dict["players"][0].battalion[0].units.append( \
        Unit(unit_type="infantry", name="2nd Company", strength=2, movement_allowance=2, \
            starting_hex=start_hex, player=0))
    game_dict["players"][1].battalion.append(Battalion(0, "DeGaulle"))
    game_dict["players"][1].battalion[0].strategy = "Evacuate"

    start_hex = (0, 5)
    if randomize:
        start_hex = get_random_hex(game_dict, exclude_hexlist)
        exclude_hexlist.append(start_hex)
    game_dict["players"][1].battalion[0].units.append( \
        Unit(unit_type="militia", name="Colonel Hogan", strength=1, \
            movement_allowance=1, starting_hex=start_hex, player=1))
    start_hex = (6,0)
    if randomize:
        start_hex = get_random_hex(game_dict, exclude_hexlist)
        exclude_hexlist.append(start_hex)
    game_dict["players"][1].battalion[0].units.append( \
        Unit(unit_type="militia", name="Louie LeBeau", strength=1, \
            movement_allowance=1, starting_hex=start_hex, player=1))

def create_bears_den_scenario(game_dict, logname, randomize):

    # Define the two players' victory conditions
    def bears_den_player_0_victory_condition(game_dict):
        """ Player 0 "Bear's Den" Scenario Wolf victory conditions """
        # Any units occupying the bears den ?
        for battalion in game_dict["players"][0].battalion:
            for unit in battalion.units:
                if unit.hex == game_dict["bears_den"]:
                    game_dict["game_running"] = False
                    game_dict["logger"].info("Victory Red \"Bear's Den captured!\"")
                    return "Victory Red: Bear's Den captured!"
        # All enemy units eliminated.
        for battalion in game_dict["players"][1].battalion:
            for unit in battalion.units:
                if unit.status in ("active", ):
                    return None
        game_dict["game_running"] = False
        game_dict["logger"].info("Victory Red \"All Blu forces eliminated!\"")
        return "Victory Red: All Blu forces eliminated!"

    def bears_den_player_1_victory_condition(game_dict):
        """ Player 1 "Bear's Den" Scenario Bear victory conditions """
        if game_dict["game_turn"] == 10:
            game_dict["game_running"] = False
            game_dict["logger"].info("Victory Blu \"Turn 10 Blufor still alive and Bear's Den not captured.\"")
            return "Victory Blu: Turn 10 Blufor still alive."
        return None

    game_dict["bears_den"] = (18, 9)
    game_dict["evacuation_hex"] = None
    game_dict['map_width'] = 21
    game_dict['map_height'] = 19
    game_dict['map_multiplier'] = 24
    with open (logname, mode='w', encoding="utf-8") as f:
        f.write(f"{game_dict.__str__()}\n")
    game_dict["victory_condition"] = (bears_den_player_0_victory_condition, bears_den_player_1_victory_condition)
    game_dict["players"] = (Player(0, "Red"), Player(1, "Blu"))

    game_dict["players"][0].battalion.append(Battalion(0, "von Bock"))
    game_dict["players"][0].battalion[0].strategy = "Capture City and Destroy"
    game_dict["players"][0].battalion[0].units.append( \
        Unit(unit_type="panzer", name="1st Panzer", attack=4, strength=2, movement_allowance=3, \
            starting_hex=(0,2), player_num=0))
    game_dict["players"][0].battalion[0].units.append( \
        Unit(unit_type="panzer", name="2nd Panzer", attack=4, strength=2, movement_allowance=3, \
            starting_hex=(0,4), player_num=0))
    game_dict["players"][0].battalion[0].units.append( \
        Unit(unit_type="panzer", name="3rd Panzer", attack=4, strength=2, movement_allowance=3, \
            starting_hex=(0,6), player_num=0))

    game_dict["players"][0].battalion.append(Battalion(0, "von Kluge"))
    game_dict["players"][0].battalion[1].strategy = "Capture City and Destroy"

    game_dict["players"][0].battalion[1].units.append( \
        Unit(unit_type="panzer", name="4th Panzer", attack=4, strength=2, movement_allowance=3, \
            starting_hex=(0,12), player_num=0))
    game_dict["players"][0].battalion[1].units.append( \
        Unit(unit_type="panzer", name="5th Panzer", attack=4, strength=2, movement_allowance=3, \
            starting_hex=(0,14), player_num=0))
    game_dict["players"][0].battalion[1].units.append( \
        Unit(unit_type="panzer", name="6th Panzer", attack=4, strength=2, movement_allowance=3, \
            starting_hex=(0,16), player_num=0))

    game_dict["players"][1].battalion.append(Battalion(1, "Zhukov"))
    game_dict["players"][1].battalion[0].strategy = "Defend City and Delay"
    game_dict["players"][1].battalion[0].units.append( \
        Unit(unit_type="infantry", name="1st Division", attack=2, strength=2, movement_allowance=2, \
            starting_hex=(4,3), player_num=1))
    game_dict["players"][1].battalion[0].units.append( \
        Unit(unit_type="infantry", name="2nd Division", attack=2, strength=2, movement_allowance=2, \
            starting_hex=(4,5), player_num=1))
    game_dict["players"][1].battalion[0].units.append( \
        Unit(unit_type="infantry", name="3rd Division", attack=2, strength=2, movement_allowance=2, \
            starting_hex=(4,7), player_num=1))
    game_dict["players"][1].battalion[0].units.append( \
        Unit(unit_type="infantry", name="Den Guard", attack=2, strength=2, movement_allowance=0, \
            starting_hex=game_dict["bears_den"], player_num=1))

    game_dict["players"][1].battalion.append(Battalion(1, "Timoshenko"))
    game_dict["players"][1].battalion[1].strategy = "Defend City and Delay"
    game_dict["players"][1].battalion[1].units.append( \
        Unit(unit_type="infantry", name="4th Division", attack=2, strength=2, movement_allowance=2, \
            starting_hex=(4,11), player_num=1))
    game_dict["players"][1].battalion[1].units.append( \
        Unit(unit_type="infantry", name="5th Division", attack=2, strength=2, movement_allowance=2, \
            starting_hex=(4,13), player_num=1))
    game_dict["players"][1].battalion[1].units.append( \
        Unit(unit_type="infantry", name="6th Division", attack=2, strength=2, movement_allowance=2, \
            starting_hex=(4,15), player_num=1))
