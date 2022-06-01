""" Code for running pytest on the battalion's hexmap code. """
from datetime import datetime
from threading import Thread
from time import sleep

import pytest
from game_ai import create_hexmap
from main import battalion_main
from settings import sleap_waiting_for_other_thread, sleap_waiting_for_user

@pytest.fixture(autouse=True, scope="session")
def pytest_configure():
    """ Register these vars as session level global variables."""
    pytest.test_hexmap_game_dict = {"initialized":False,}
    pytest.test_hexmap_display_thread = None

@pytest.fixture(autouse=True, scope="session")
def start_game():
    """ Open a log, run a random game, inspect the results."""
    logname = datetime.now().strftime("battalion_test_hexmap_%Y%m%d_%H%M%S_log.txt")
    pytest.test_hexmap_display_thread = Thread(target=battalion_main, daemon=True, \
        args=(logname, None, None, pytest.test_hexmap_game_dict, False))
    pytest.test_hexmap_display_thread.start()
    while not pytest.test_hexmap_game_dict["initialized"]:
        sleap_waiting_for_other_thread()
    yield pytest.test_hexmap_display_thread
    pytest.test_hexmap_game_dict["game_running"] = False
    while pytest.test_hexmap_display_thread.is_alive():
        sleap_waiting_for_other_thread()

@pytest.mark.parametrize("evac_hex_list, start_list, sz_limit, red_unit_hex, blue_unit_hex, enforce_zoc_val", \
    [ \
        ([(0,3),], [(0,3),], 99, (0,6), (3,3), False), \
        ([(0,3),], [(0,3),], 99, (1,6), (3,4), False), \
        ([(0,3),], [(2,6),], 99, (2,6), (0,4), True) \
    ])
def test_hexmap(evac_hex_list, start_list, sz_limit, red_unit_hex, blue_unit_hex, enforce_zoc_val):
    """ Visual test of hexmap, tester should enter p or f key based on image."""

    # Clear some values, set the evacuation hex, generate a hexmap, and request a screeen update.
    pytest.test_hexmap_game_dict["test_grade"] = "undetermined"
    pytest.test_hexmap_game_dict["test_continue"] = False
    pytest.test_hexmap_game_dict["evacuation_hex"] = evac_hex_list[0]
    pytest.test_hexmap_game_dict["players"][0].battalion[0].units[0].hex = red_unit_hex
    pytest.test_hexmap_game_dict["players"][1].battalion[0].units[0].hex = blue_unit_hex
    pytest.test_hexmap_game_dict["display_hexmap"] = \
        create_hexmap(start_list, pytest.test_hexmap_game_dict, limit=sz_limit, \
            source_unit=pytest.test_hexmap_game_dict["players"][0].battalion[0].units[0], enforce_zoc=enforce_zoc_val)
    pytest.test_hexmap_game_dict["update_screen_req"] += 1

    # Wait for user to pass/fail
    while not pytest.test_hexmap_game_dict["test_continue"]:
        sleap_waiting_for_user
    pytest.test_hexmap_game_dict["test_continue"] = False

    # Process the grade.
    grade = pytest.test_hexmap_game_dict["test_grade"]
    grade_str = f"Expected \"pass\" but got {grade}"
    assert pytest.test_hexmap_game_dict["test_grade"] == "pass", grade_str
    pytest.test_hexmap_game_dict["test_grade"] = "undetermined"
