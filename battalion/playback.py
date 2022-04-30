""" Playback main """
import ast
import shlex
from threading import Lock, Thread
from time import sleep

import pygame
from game import Player, Battalion
from unit import Unit, draw_units
from main import draw_map, game_setup

def playback_threaded_function(game_dict):
    """ This is the function that starts the playback manager thread.  This thread is run in parallel
        to the main (display) thread. """
    while game_dict["game_running"]:
        sleep(1)

def main():
    with open("battalion_log.txt", 'r') as f:
        game_dict = ast.literal_eval(f.readline()) # read in static first line

        game_dict["players"] = (Player(0, "Red"), Player(1, "Blu"))
        for i in range(0,2):
            unused_player_name = f.readline()
            nextstrs = f.readline().split()
            game_dict["players"][i].battalion.append(Battalion(int(nextstrs[0]), nextstrs[1]))
            game_dict["players"][i].battalion[0].strategy = " ".join(nextstrs[2:])
            unitstr = shlex.split(f.readline())
            game_dict["players"][i].battalion[0].units.append( \
                    Unit(unitstr[0], unitstr[1], int(unitstr[2]), int(unitstr[3]), int(unitstr[4]), \
                        game_dict["players"][i]))
            print(game_dict["players"][i].battalion[0].units[0])

    clock, gui_manager, game_screen, phase_labels = game_setup(game_dict)
    # OK!  Let's get the game loops started!
    #
    # Note that this program uses two threads.  This is the main (display) thread.  Any display
    # graphs or gui changes should be effected in this thread.  The first time through it launches
    # the game manager thread.  Both threads use game_dict to communicate information back and forth
    # between the threads.  Any game_dict variable should only be written by one of the two threads.
    first_time = True
    gamemaster_thread = None
    game_dict["game_running"] = True
    game_dict["update_screen_req"] = 1
    game_dict["update_screen"] = 0

    game_dict["theme_lock"] = Lock()

    # Main game loop.  Keep looping until someone wins or the game is no longer running
    while game_dict["game_running"]:

        time_delta = clock.tick(60)/1000.0

        # Get user mouse and keyboard events
        for e in pygame.event.get():
            # print(event)
            if e.type == pygame.QUIT:
                game_dict["logger"].warn("GAME ABORTED BY USER.")
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
                        target = playback_threaded_function, args = (game_dict,))
                    gamemaster_thread.start()

    # We're exiting, and the gamemaster thread should be exiting too...
    if gamemaster_thread:
        gamemaster_thread.join()

    # Cleanup
    pygame.quit()

if __name__ == '__main__':
    main()