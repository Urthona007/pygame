""" Code for running pytest on the battalion's hexmap code. """
from datetime import datetime
from time import sleep
from battalion.game_ai import create_hexmap
from battalion.hexl import get_hex_offset, hex_legal
from main import battalion_main
# import pytest nuke this??

###@pytest.mark.parametrize('run_test_n_times', range(2))

def hexmap_test_threaded_function(game_dict, max_turns):
    """ This is the function that starts the hexmap test thread.  This thread is run in parallel
        to the main (display) thread. """
    game_dict["logger"].info("In hexmap_test_threaded_func")
    while game_dict["game_running"]:
        sleep(0.1)
        if game_dict["display_hexmap"] == None:
            game_dict["display_hexmap"] = create_hexmap([game_dict["evacuation_hex"],], game_dict, limit=99)
            game_dict["update_screen_req"] += 1


def test_hexmap():
    """ Open a log, run a random game, inspect the results."""
    logname = datetime.now().strftime("battalion_test_hexmap_%Y%m%d_%H%M%S_log.txt")
    from_test_hexmap_game_dict = {}
    battalion_main(logname, hexmap_test_threaded_function, (from_test_hexmap_game_dict, 13), \
        from_test_hexmap_game_dict, randomize=False)
