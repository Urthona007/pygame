""" Code for running pytest on the battalion game. """
from datetime import datetime
import pytest
from battalion.game import play_game_threaded_function
from battalion.main import battalion_main

@pytest.mark.parametrize('run_test_n_times', range(1))
def test_battalion(run_test_n_times): #pylint: disable=W0613 # Allows pytest to run multiple times
    """ Open a log, run a random game, inspect the results."""
    logname = datetime.now().strftime("battalion_%Y%m%d_%H%M%S_log.txt")
    from_test_battalion_dict = {}
    battalion_main(logname, play_game_threaded_function, \
        (from_test_battalion_dict,), from_test_battalion_dict, randomize=True)
    # Open up log file and validate it
    with open(logname, "r", encoding="utf-8") as f:
        # Make sure you can find a line that has turn 1
        found = False
        nextstrs = []
        while not found:
            nextstrs = f.readline().rstrip('n').split()
            assert nextstrs[0] != "" # Should not reach end of file
            if nextstrs[0] == "Turn":
                found = True
        if found:
            batt_keys = ("Turn", "Phase", "MV", "EVACUATE", "ATTACK", "Victory", "ELIM", \
                "RETREAT", "PASS")
            thisline = f.readline()
            nextstrs = thisline.rstrip('n').split()
            while thisline != "":
                print("WCB", thisline)
                prevline = thisline
                prevkey = nextstrs[0]
                assert nextstrs[0] in batt_keys
                thisline = f.readline()
                nextstrs = thisline.rstrip('n').split()
            assert prevkey == "Victory"
            print(prevline)
