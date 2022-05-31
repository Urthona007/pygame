""" Manage hexmaps """

import queue
from time import sleep
from hexl import get_hex_coords_from_direction, get_hex_offset, hex_legal, hex_next_to_enemies, hex_occupied
from hexl import directions
import numpy as np

def display_hexmap(game_screen, game_dict):
    for x in range(game_dict['map_width']):
        for y in range(game_dict['map_height']):
            if not hex_legal((x,y), game_dict):
                break
            x_offset, y_offset = get_hex_offset((x, y), game_dict)

            # limit to number of font images
            hexval = min(game_dict["font_img_num_limit"]-1, game_dict["display_hexmap"][x][y])
            game_screen.blit(game_dict["font_img_num"][hexval], (x_offset+20, y_offset+40))

def show_hexmap_and_wait_for_continue(hexmap, game_dict):
    game_dict["test_continue"] = False
    game_dict["display_hexmap"] = hexmap
    game_dict["update_screen_req"] += 1
    while not game_dict["test_continue"]:
        sleep(0.1)

def create_hexmap(start_list, game_dict, limit=99, source_unit=None, enforce_zoc=False):
    """ Create a 2D array corresponding to the hexes of integers.  Count away from the start
    list.  """
    # evec hexmap - how far to one or more hexes, ignores units.
    # move hexmap

    hexmap = np.full((game_dict["map_width"], game_dict["map_height"]), 99)
    hexnode_queue = queue.Queue()

    for hx in start_list:
        hexmap[hx[0]][hx[1]] = 0
        hexnode_queue.put(hx)

    depth = 0
    while not hexnode_queue.empty() and depth < limit:
        this_hex = hexnode_queue.get()
        for direct in directions:
            adj_hex = get_hex_coords_from_direction(direct, this_hex, game_dict)
            if adj_hex is not None and \
                (hexmap[adj_hex[0]][adj_hex[1]] == 99):
                # If you don't have to enforce the zoc, this hex is eligible.  Also if it is empty.
                if (not enforce_zoc) or \
                    (hex_occupied(adj_hex, game_dict) is None):
                    hexmap[adj_hex[0]][adj_hex[1]] = hexmap[this_hex[0]][this_hex[1]]+1 # This hex can be reached

                    # But should it seed more hexes.  It should if either we are not enforcing zoc or
                    if (not enforce_zoc) or (not hex_next_to_enemies(adj_hex, 1-source_unit.player, game_dict)): # Enforce zoc.
                        hexnode_queue.put(adj_hex)

    return hexmap
