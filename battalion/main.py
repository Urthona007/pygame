""" Battalion Main """
from threading import Thread, Lock
from time import sleep
import logging
from game import Player, Battalion, play_game_threaded_function, reset_phases
from unit import Unit, draw_units
from hexl import draw_hexs, get_random_edge_hex, get_random_hex
import pygame_gui
import pygame

def draw_map(screen, a_game_dict):
    """ Draw game map. """
    draw_hexs(screen, a_game_dict)

class MyFormatter(logging.Formatter):
    """ Logging formatter subclass that formats log msgs differently based on msg level """

    err_fmt  = "ERROR: %(msg)s"
    warn_fmt = "WARNING: %(msg)s"
    dbg_fmt  = "DBG: %(module)s: %(lineno)d: %(msg)s"
    info_fmt = "%(msg)s"

    def __init__(self):
        super().__init__(fmt="%(levelno)d: %(msg)s", datefmt=None, style='%')

    def format(self, record):
        """ Based on the msg level, format log msgs differently. """
        format_orig = self._style._fmt # pylint: disable=W0212

        # Replace the original format with one customized by logging level
        if record.levelno == logging.DEBUG:
            self._style._fmt = MyFormatter.dbg_fmt # pylint: disable=W0212
        elif record.levelno == logging.INFO:
            self._style._fmt = MyFormatter.info_fmt # pylint: disable=W0212
        elif record.levelno == logging.ERROR:
            self._style._fmt = MyFormatter.err_fmt # pylint: disable=W0212
        elif record.levelno == logging.WARN:
            self._style._fmt = MyFormatter.warn_fmt # pylint: disable=W0212

        # Call the original formatter class to do the grunt work
        result = logging.Formatter.format(self, record)

        # Restore the original format configured by the user
        self._style._fmt = format_orig # pylint: disable=W0212

        return result

def create_game_logger(game_dict, logname, screen_only = False):
    """ Log messages to the screen and also to a log file. """
    logging.captureWarnings(True)
    game_dict["logger"] = logging.getLogger(__name__)
    game_dict["logger"].setLevel(logging.DEBUG)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    game_dict["logger"].addHandler(ch)

    if not screen_only:
        # Create log file handler and set level to debug
        fh = logging.FileHandler(logname) #, mode='w')
        fh.setLevel(logging.DEBUG)
        fmt = MyFormatter()
        fh.setFormatter(fmt)
        # fh.setFormatter(logging.Formatter('%(levelname)s:%(message)s'))
        game_dict["logger"].addHandler(fh)

def close_game_logger(game_dict):
    """ Close game logger."""
    handlers = game_dict["logger"].handlers[:]
    for handler in handlers:
        game_dict["logger"].removeHandler(handler)
        handler.close()

def game_setup(game_dict):
    """ Perform initializations common to both Playback and Main."""
    # init pygame
    pygame.init() #pylint: disable=E1101

    # 3) Initialize derived game parameters.
    # Add in all movement phases based on how many battalions are specified.
    for player in game_dict["players"]:
        for battalion in player.battalion:
            game_dict["game_phases"].append((f"{battalion.name}", False))
    reset_phases(game_dict)

    # Initialize the gui.
    game_dict["update_gui"] = False
    gui_manager = pygame_gui.UIManager((game_dict['display_width'], game_dict['display_height']), \
        enable_live_theme_updates=False) # Note: enable live theme updates doesn't seem to work
                                         # and I instead do it manually
    gui_manager.get_theme().load_theme('battalion/phase_theme.json')
    game_dict["turn_label"] = pygame_gui.elements.UILabel(relative_rect=pygame.Rect((2, 2), \
        (98, 20)), text='Turn 1', manager=gui_manager)

    pygame_gui.elements.UILabel(relative_rect=pygame.Rect((2,30), (98, 20)),
                                            text = "Phases:",
                                            manager=gui_manager)
    phase_labels = []
    for idx, phas in enumerate(game_dict["game_phases"]):
        phase_labels.append(pygame_gui.elements.UILabel(relative_rect=pygame.Rect((2, 52+22*idx), \
            (98, 20)), text=phas[0], manager=gui_manager, \
            object_id=pygame_gui.core.ObjectID(class_id='@batt_phase_labels', \
                object_id=f"#phase_{idx}")))
    clock = pygame.time.Clock()

    pygame.display.set_caption(game_dict['name']) # NOTE: this is not working.  I don't know why.
    game_screen = pygame.display.set_mode((game_dict['display_width'], game_dict['display_height']))

    return clock, gui_manager, game_screen, phase_labels

def battalion_main(logname, randomize=False):
    """ Start the main code """
    # Create game_dict which holds all game parameters and global cross-thread data and signals.
    # 1) Initialize general settings first
    game_dict = {'name': 'Battalion', 'display_width' : 640, 'display_height' : 480, \
            'bkg_color': (50, 50, 50), 'map_width': 11, 'map_height': 8, 'map_multiplier': 47, \
            'map_border' : (100, 8), 'unit_width': 32, 'unit_x_offset': 18, 'unit_y_offset': 34, \
            "game_turn": 1, \
            "game_phases":[("Red Combat", False), ("Blu Combat", False)], "game_running": True \
            }

    # 2) Initialize specific parameters.  Right now we only have one scenario, Hounds.
    scenario = "Hounds" # pylint: disable-msg=C0103
    game_dict["scenario"] = scenario
    if scenario == "Hounds":
        # Define the two players' victory conditions
        def player_0_victory_condition(game_dict):
            """ Player 0 "Hound" Scenario Hound victory conditions """
            for battalion in game_dict["players"][1].battalion:
                for unit in battalion.units:
                    if unit.status in ("active", "off_board"):
                        return None
            game_dict["game_running"] = False
            game_dict["logger"].info("Victory Red \"All Blu forces eliminated!\"")
            return "Victory Red: All Blu forces eliminated!"

        def player_1_victory_condition(game_dict):
            """ Player 1 "Rabbit" Scenario Hound victory conditions """
            if game_dict["game_turn"] == 10:
                game_dict["game_running"] = False
                game_dict["logger"].info("Victory Blu \"Turn 10 Blufor still alive.\"")
                return "Victory Blu: Turn 10 Blufor still alive."
            for battalion in game_dict["players"][1].battalion:
                for unit in battalion.units:
                    if unit.status == "active":
                        return None
                    assert unit.status == "off_board"
            game_dict["game_running"] = False
            game_dict["logger"].info("Victory Blu \"All Blu forces evacuated!\"")
            return "Victory Blu: All Blu forces evacuated!"

        game_dict["evacuation_hex"] = (0,2)
        if randomize:
            game_dict["evacuation_hex"] = get_random_edge_hex(game_dict)
        with open (logname, mode='w', encoding="utf-8") as f:
            f.write(f"{game_dict.__str__()}\n")
        game_dict["players"] = (Player(0, "Red"), Player(1, "Blu"))
        game_dict["players"][0].battalion.append(Battalion(0, "Rommel"))
        game_dict["players"][0].battalion[0].strategy = "Seek and Destroy"
        start_hex = (0, 4)
        exclude_hexlist = [game_dict["evacuation_hex"],]
        if randomize:
            start_hex = get_random_hex(game_dict, exclude_hexlist)
            exclude_hexlist.append(start_hex)
        game_dict["players"][0].battalion[0].units.append( \
            Unit("infantry", "1st Company", 2, start_hex, 0))
        game_dict["players"][1].battalion.append(Battalion(0, "DeGaulle"))
        game_dict["players"][1].battalion[0].strategy = "Evacuate"
        start_hex = (0, 5)
        if randomize:
            start_hex = get_random_hex(game_dict, exclude_hexlist)
            exclude_hexlist.append(start_hex)
        game_dict["players"][1].battalion[0].units.append( \
            Unit("militia", "Resistance Fighters", 1, start_hex, 1))

        with open(logname, mode = 'a', encoding="utf-8") as f:
            for player in game_dict["players"]:
                player.write(f)

    # create logger
    create_game_logger(game_dict, logname)
    game_dict["theme_lock"] = Lock()
    # game_dict["theme_lock"].acquire()
    clock, gui_manager, game_screen, phase_labels = game_setup(game_dict)
    # game_dict["theme_lock"].release()

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

    # Main game loop.  Keep looping until someone wins or the game is no longer running
    while (not player_0_victory_condition(game_dict)) and \
        (not player_1_victory_condition(game_dict)) \
        and game_dict["game_running"]:

        time_delta = clock.tick(60)/1000.0

        # Get user mouse and keyboard events
        for e in pygame.event.get():
            # print(event)
            if e.type == pygame.QUIT: #pylint: disable=E1101
                game_dict["logger"].warning("GAME ABORTED BY USER.")
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

            gui_manager.update(time_delta)
            gui_manager.draw_ui(game_screen)
            game_dict["theme_lock"].release()
            game_dict["update_gui"] = False

            # Update Dispay overall
            pygame.display.update()

            # If this is the first time through the loop, launch the game manager thread.
            if first_time:
                first_time = False
                if __name__ in ("__main__", "battalion.main"):
                    sleep(1)
                    gamemaster_thread = Thread( \
                        target = play_game_threaded_function, args = (game_dict, 10))
                    gamemaster_thread.start()

    # We're exiting, and the gamemaster thread should be exiting too...
    if gamemaster_thread:
        gamemaster_thread.join()

    # Cleanup
    close_game_logger(game_dict)

    pygame.quit() #pylint: disable=E1101

if __name__ == '__main__':
    battalion_main("battalion_log.txt", False)
