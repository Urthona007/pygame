""" Battalion Main """
from threading import Thread
from time import sleep
from game import Player, Battalion, play_game_threaded_function
from unit import Unit, draw_units
from hexl import draw_hexs
import pygame

def draw_map(screen, a_game_dict):
    """ Draw game map. """
    draw_hexs(screen, a_game_dict)

def main():
    """ Start the main code """
    pygame.init()

    # Right now we only have one scenario, Hounds.  Initialize the scenario here.
    scenario = "Hounds" # pylint: disable-msg=C0103
    if scenario == "Hounds":
        game_dict = {'name': 'Battalion', 'display_width' : 640, 'display_height' : 480, \
            'bkg_color': (50, 50, 50), 'map_width': 11, 'map_height': 8, 'map_multiplier': 50, \
            'map_border' : 8, 'unit_width': 32, 'unit_x_offset': 18, 'unit_y_offset': 34, \
            "game_turn": 1, \
            "game_phases":[("Red Combat", False), ("Blu Combat", False)], "game_running": True, \
            "evacuation_hex": (0,4)}

        def player_0_victory_condition(game_dict):
            """ Player 0 Scenario Hound victory conditions """
            for battalion in game_dict["players"][1].battalion:
                for unit in battalion.units:
                    if unit.status in ("active", "off_board"):
                        return None
            game_dict["game_running"] = False
            print("Red Victory, all Blu forces eliminated!")
            return "Red Victory, all Blu forces eliminated!"

        def player_1_victory_condition(game_dict):
            """ Player 1 Scenario Hound victory conditions """
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
        game_dict["players"][0].battalion[0].units.append( \
            Unit("infantry", "1st Company", 2, 4, 4, 0))
        game_dict["players"][1].battalion.append(Battalion(0, "DeGaulle"))
        game_dict["players"][1].battalion[0].strategy = "Evacuate"
        game_dict["players"][1].battalion[0].units.append( \
            Unit("militia", "Resistance Fighters", 1, 7, 5, 1))

    # Add in all movement phases based on how many battalions are specified.
    for player in game_dict["players"]:
        for battalion in player.battalion:
            game_dict["game_phases"].append((f"{battalion.name} Movement", False))

    pygame.display.set_caption(game_dict['name']) # NOTE: this is not working.  I don't know why.

    game_dict["game_running"] = True
    game_screen = pygame.display.set_mode((game_dict['display_width'], game_dict['display_height']))
    game_dict["update_screen"] = True

    # OK!  Let's get the game loops started!  This loop is the main (display) loop.  Note that the
    # first time through it will launch the game manager thread.  Both threads use game_dict to
    # communicate information back and forth between the threads.
    first_time = True
    gamemaster_thread = None

    # Keep looping until someone wins or the game is no longer running
    while (not player_0_victory_condition(game_dict)) and \
        (not player_1_victory_condition(game_dict)) \
        and game_dict["game_running"]:

        # Get user mouse and keyboard events
        for e in pygame.event.get():
            # print(event)
            if e.type == pygame.QUIT:
                print("GAME ABORTED BY USER.")
                game_dict["game_running"] = False

        # Redraw the screen as necessary
        if game_dict["update_screen"]:
            game_screen.fill(game_dict['bkg_color'])
            draw_map(game_screen, game_dict)
            draw_units(game_screen, game_dict)
            pygame.display.update()
            game_dict["update_screen"] = False
            # If this is the first time through the loop, launch the game manager thread.
            if first_time:
                first_time = False
                if __name__ == "__main__":
                    sleep(1)
                    gamemaster_thread = Thread( \
                        target = play_game_threaded_function, args = (game_dict, 10))
                    gamemaster_thread.start()
                    #    thread.join()
                    #    print("thread finished...exiting")

    # We're exiting, and the gamemaster thread should be exiting too...
    if gamemaster_thread:
        gamemaster_thread.join()

    # Cleanup
    pygame.quit()

if __name__ == '__main__':
    main()
