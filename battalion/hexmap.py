""" Manage hexmaps """

import queue
from hexl import get_hex_coords_from_direction, get_hex_offset, hex_legal
from hexl import directions
import numpy as np

def display_hexmap(game_screen, game_dict):
    for x in range(game_dict['map_width']):
        for y in range(game_dict['map_height']):
            if not hex_legal((x,y), game_dict):
                break
            x_offset, y_offset = get_hex_offset((x, y), game_dict)
            game_screen.blit(game_dict["font_img_num"][game_dict["display_hexmap"][x][y]], (x_offset+20, y_offset+40))

def create_hexmap(start_list, game_dict, limit=99):
    """ Create a 2D array corresponding to the hexes of integers.  Count away from the start
    list.  """
    # evec hexmap - how far to one or more hexes, ignores units.
    #
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
            if adj_hex is not None and (hexmap[adj_hex[0]][adj_hex[1]] == 99):
                hexmap[adj_hex[0]][adj_hex[1]] = hexmap[this_hex[0]][this_hex[1]]+1
                hexnode_queue.put(adj_hex)

    return hexmap
