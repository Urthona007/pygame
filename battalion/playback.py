""" Playback main """
import ast
import shlex
from threading import Lock, Thread
from time import sleep
from game import Player, Battalion, reset_phases, update_phase_gui
from unit import Unit, draw_units, get_unit_by_name
from main import create_game_logger, draw_map, game_setup
import pygame


def playback_threaded_function(game_dict, f):
    """ This is the function that starts the playback manager thread.  This thread is run in
        parallel to the main (display) thread. """
    first_time = True
    while game_dict["game_running"]:
        if game_dict["key_request"] == "automatic" or game_dict["key_request"] == "next phase" or \
            game_dict["key_request"] == "next turn" or first_time:
            first_time = False
            if game_dict["key_request"] == "automatic":
                sleep(1)
            log_string = f.readline().rstrip('\n')
            if log_string == "":
                if game_dict["key_request"] == "automatic":
                    game_dict["game_running"] = False
                    print("End of log reached.  Ending game.")
                else:
                    print("End of log reached.  Cannot go further forward.")
                    game_dict["key_request"] = ""
            else:
                sstring = shlex.split(log_string)
                print(sstring)
                if sstring[0] == "Turn":
                    game_dict["game_turn"] = int(sstring[1])
                    reset_phases(game_dict)
                    game_dict["update_gui"] = True
                elif sstring[0] == "Phase":
                    active_phase = (sstring[1], False)
                    update_phase_gui(game_dict, active_phase)
                    for i, phase in enumerate(game_dict["game_phases"]):
                        if phase[0] == active_phase[0]:
                            game_dict["game_phases"][i] = (active_phase[0], True)
                elif sstring[0] == "MV":
                    # Converting string to list
                    mv_hexes = ast.literal_eval(sstring[2])
                    mv_unit = get_unit_by_name(sstring[1], game_dict)
                    mv_unit.hex = mv_hexes[-1]
                    game_dict["update_screen_req"] += 1
            if game_dict["key_request"] == "next phase" or \
                (game_dict["key_request"] == "next turn" and sstring[0] == "Turn"):
                game_dict["key_request"] = ""

def playback_main(logname):
    """ Main playback function."""
    # The entire playback is performed with the logfile open
    with open(logname, 'r', encoding="utf-8") as f:
        # 1) Read in the header and setup basic information
        game_dict = ast.literal_eval(f.readline().rstrip('n')) # read in static first line

        game_dict["players"] = (Player(0, "Red"), Player(1, "Blu"))
        for i in range(0,2):
            nextstrs = shlex.split(f.readline().rstrip('n'))
            num_battalions = int(nextstrs[1])
            for b in range(num_battalions):
                nextstrs = shlex.split(f.readline().rstrip('n'))
                game_dict["players"][i].battalion.append(Battalion(int(nextstrs[0]), nextstrs[1]))
                num_units = int(nextstrs[2])
                game_dict["players"][i].battalion[0].strategy = " ".join(nextstrs[3:])
                for u in range(num_units):
                    unitstr = shlex.split(f.readline().rstrip('n'))
                    unitstr[5] += unitstr[6]
                    unitstr.pop()
                    game_dict["players"][i].battalion[0].units.append( \
                        Unit(unit_type=unitstr[0], name=unitstr[1], attack=int(unitstr[2]), \
                            strength=int(unitstr[3]), movement_allowance=int(unitstr[4]), \
                            starting_hex=ast.literal_eval(unitstr[5]), player_num=i))
            # print(game_diunit_type=ct["players"name=][i].battalion[0].units[0])

        # 2) Setup the game very similar to the main game
        # create logger
        create_game_logger(game_dict, logname, True)
        game_dict["theme_lock"] = Lock()
        clock, gui_manager, game_screen, phase_labels = game_setup(game_dict)

        # 3) OK!  Let's get the game loops started!
        #
        # Note that this program uses two threads.  This is the main (display) thread.  Any display
        # graphs or gui changes should be effected in this thread.  The first time through it
        # launches the game manager thread.  Both threads use game_dict to communicate information
        # back and forth between the threads.  Any game_dict variable should only be written by one
        # of the two threads.
        first_time = True
        gamemaster_thread = None
        game_dict["game_running"] = True
        game_dict["update_screen_req"] = 1
        game_dict["update_screen"] = 0
        game_dict["key_request"] = ""

        # Main game (playback in this case) loop.  Keep looping until user kills the playback.
        while game_dict["game_running"]:

            time_delta = clock.tick(60)/1000.0

            # Get user mouse and keyboard events
            for e in pygame.event.get():
                # print(event)
                #pylint: disable=E1101
                if e.type == pygame.QUIT:
                    game_dict["logger"].warn("GAME ABORTED BY USER.")
                    game_dict["game_running"] = False
                if e.type == pygame.KEYDOWN :
                    if e.key == pygame.K_p:
                        game_dict["key_request"] = "next phase"
                    elif e.key == pygame.K_o:
                        game_dict["key_request"] = "prev phase"
                    elif e.key == pygame.K_t:
                        game_dict["key_request"] = "next turn"
                    elif e.key == pygame.K_r:
                        game_dict["key_request"] = "prev turn"
                    elif e.key == pygame.K_a:
                        if game_dict["key_request"] == "automatic":
                            game_dict["key_request"] = ""
                        else:
                            game_dict["key_request"] = "automatic"
                    elif e.key == pygame.K_q:
                        game_dict["game_running"] = False
                gui_manager.process_events(e)

            # Redraw the screen as necessary
            if game_dict["update_screen_req"] > game_dict["update_screen"] or \
                gui_manager.get_theme().check_need_to_reload() or game_dict["update_gui"]:
                # Redraw screen
                if game_dict["update_screen_req"] > game_dict["update_screen"]:
                    game_dict["update_screen"] += 1
                game_screen.fill(game_dict['bkg_color'])
                draw_map(game_screen, game_dict)
                animating = draw_units(game_screen, game_dict, time_delta)
                if animating:
                    game_dict["update_screen_req"] += 1

                # Redraw game turn and phase labels
                game_dict["theme_lock"].acquire()
                this_turn = game_dict["game_turn"]
                game_dict["turn_label"].set_text(f"Turn {this_turn}")
                for lb in phase_labels:
                    lb.rebuild_from_changed_theme_data()
                game_dict["update_gui"] = False
                gui_manager.update(time_delta)
                gui_manager.draw_ui(game_screen)
                game_dict["theme_lock"].release()

                # Update Dispay overall
                pygame.display.update()

                # If this is the first time through the loop, launch the playback manager thread.
                if first_time:
                    first_time = False
                    if __name__ == "__main__":
                        sleep(1)
                        gamemaster_thread = Thread( \
                            target = playback_threaded_function, args = (game_dict,f))
                        gamemaster_thread.start()

    # We're exiting, and the gamemaster thread should be exiting too...
    if gamemaster_thread:
        gamemaster_thread.join()

    # Cleanup
    pygame.quit() #pylint: disable=E1101

if __name__ == '__main__':
    playback_main("battalion_log.txt")
