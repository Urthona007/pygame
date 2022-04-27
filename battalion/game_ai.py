""" Functions for AI """
from game_cmd import GameCmd
from random import randrange
import queue
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
            adjx, adjy = get_hex_coords_from_direction(direct, this_hex[0], this_hex[1], game_dict)
            if adjx is not None and adjy is not None and hexmap[adjx][adjy] == 99:
                hexmap[adjx][adjy] = hexmap[this_hex[0]][this_hex[1]]+1
                hexnode_queue.put((adjx, adjy))

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
            unit_list.append((e_unit.x, e_unit.y))
    enemy_hexmap = create_hexmap(unit_list, game_dict)

    enemy_hexmap = evac_hexmap + enemy_hexmap

    # Choose one of the candidates randomly
    candidate_list = []
    highval = 199
    for direct in directions:
        adjx, adjy = get_hex_coords_from_direction(direct, unit.x, unit.y, game_dict)
        if adjx is not None and adjy is not None and \
            not hex_occupied(adjx, adjy, game_dict):
            if enemy_hexmap[adjx][adjy] < highval:
                candidate_list = [(adjx, adjy),]
                highval = enemy_hexmap[adjx][adjy]
            elif enemy_hexmap[adjx][adjy] == highval:
                if evac_hexmap[adjx][adjy] > \
                    evac_hexmap[candidate_list[0][0]][candidate_list[0][1]]:
                    candidate_list = [(adjx, adjy),]
                elif evac_hexmap[adjx][adjy] == \
                    evac_hexmap[candidate_list[0][0]][candidate_list[0][1]]:
                    candidate_list.append((adjx, adjy))

    if len(candidate_list) == 0:
        return GameCmd(unit, None, "PASS", None)
    next_hex = candidate_list[randrange(len(candidate_list))]
    return(GameCmd(unit, None, "MV", [(unit.x, unit.y), next_hex]))

def ai_evacuate(unit, game_dict):
    """ return CMD string for unit using strategy EVACUATE. """

    # Create a hexmap with the evacuation hex as its origin.
    hexmap = create_hexmap([(game_dict["evacuation_hex"][0], game_dict["evacuation_hex"][1]), ], \
        game_dict)

    if hexmap[unit.x][unit.y] == 0:
        return GameCmd(unit, None, "EVACUATE", None)

    # Choose one of the candidates randomly
    candidate_list = []
    for direct in directions:
        adjx, adjy = get_hex_coords_from_direction(direct, unit.x, unit.y, game_dict)
        if adjx is not None and adjy is not None and \
            hexmap[adjx][adjy] < hexmap[unit.x][unit.y] and \
            not hex_occupied(adjx, adjy, game_dict):
            candidate_list.append((adjx, adjy))
    if len(candidate_list) == 0:
        return GameCmd(unit, None, "PASS", None)
    next_hex = candidate_list[randrange(len(candidate_list))]
    return(GameCmd(unit, None, "MV", [(unit.x, unit.y), next_hex]))
