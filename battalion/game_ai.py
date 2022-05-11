""" Functions for AI """
from random import randrange
import queue
from game_cmd import GameCmd
from hexl import get_hex_coords_from_direction, hex_occupied #pylint: disable=E0401
from hexl import directions
import numpy as np

def create_hexmap(start_list, game_dict):
    """ Create a 2D array corresponding to the hexes of integers.  Count away from the start
    list.  """
    hexmap = np.full((game_dict["map_width"], game_dict["map_height"]), 99)
    hexnode_queue = queue.Queue()

    for hx in start_list:
        hexmap[hx[0]][hx[1]] = 0
        hexnode_queue.put(hx)

    while not hexnode_queue.empty():
        this_hex = hexnode_queue.get()
        for direct in directions:
            adj_hex = get_hex_coords_from_direction(direct, this_hex, game_dict)
            if adj_hex is not None and (hexmap[adj_hex[0]][adj_hex[1]] == 99):
                hexmap[adj_hex[0]][adj_hex[1]] = hexmap[this_hex[0]][this_hex[1]]+1
                hexnode_queue.put(adj_hex)

    return hexmap

def ai_circle(unit, game_dict):
    """ Return CMD string for unit using strategy CIRCLE. """
    newx, newy = get_hex_coords_from_direction( \
        directions[game_dict["game_turn"]%6], unit.x, unit.y, game_dict)
    if not hex_occupied(newx, newy, game_dict):
        return(GameCmd(unit, None, "MV", [(unit.x, unit.y), (newx, newy)]))
    return GameCmd(unit, None, "PASS", None)

def ai_prevent_evacuation(unit, game_dict):
    """ Hunt units while guarding the evacuation point.  """
    evac_hexmap = create_hexmap([ \
        (game_dict["evacuation_hex"][0], game_dict["evacuation_hex"][1]), ], game_dict)

    unit_list = []
    e_player = 1 - unit.player
    for battalion in game_dict["players"][e_player].battalion:
        for e_unit in battalion.units:
            unit_list.append(e_unit.hex)
    enemy_hexmap = create_hexmap(unit_list, game_dict)

    enemy_hexmap = evac_hexmap + enemy_hexmap

    # Choose one of the candidates randomly
    candidate_list = []
    highval = 199
    for direct in directions:
        adj_hex = get_hex_coords_from_direction(direct, unit.hex, game_dict)
        if adj_hex is not None and \
            not hex_occupied(adj_hex, game_dict):
            if enemy_hexmap[adj_hex[0]][adj_hex[1]] < highval:
                candidate_list = [adj_hex,]
                highval = enemy_hexmap[adj_hex[0]][adj_hex[1]]
            elif enemy_hexmap[adj_hex[0]][adj_hex[1]] == highval:
                if evac_hexmap[adj_hex[0]][adj_hex[1]] > \
                    evac_hexmap[candidate_list[0][0]][candidate_list[0][1]]:
                    candidate_list = [adj_hex,]
                elif evac_hexmap[adj_hex[0]][adj_hex[1]] == \
                    evac_hexmap[candidate_list[0][0]][candidate_list[0][1]]:
                    candidate_list.append(adj_hex)

    if len(candidate_list) == 0:
        return GameCmd(unit, None, "PASS", None)
    next_hex = candidate_list[randrange(len(candidate_list))]
    return GameCmd(unit, None, "MV", [unit.hex, next_hex])

def ai_evacuate(unit, game_dict):
    """ return CMD string for unit using strategy EVACUATE. """

    # Create a hexmap with the evacuation hex as its origin.
    hexmap = create_hexmap([(game_dict["evacuation_hex"][0], game_dict["evacuation_hex"][1]), ], \
        game_dict)

    if hexmap[unit.hex[0]][unit.hex[1]] == 0:
        return GameCmd(unit, None, "EVACUATE", None)

    # Choose one of the candidates randomly
    candidate_list = []
    for direct in directions:
        adj_hex = get_hex_coords_from_direction(direct, unit.hex, game_dict)
        if adj_hex is not None and \
            hexmap[adj_hex[0]][adj_hex[1]] < hexmap[unit.hex[0]][unit.hex[1]] and \
            not hex_occupied(adj_hex, game_dict):
            candidate_list.append(adj_hex)
    if len(candidate_list) == 0:
        return GameCmd(unit, None, "PASS", None)
    next_hex = candidate_list[randrange(len(candidate_list))]
    return GameCmd(unit, None, "MV", [unit.hex, next_hex])
