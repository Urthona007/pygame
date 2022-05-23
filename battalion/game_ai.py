""" Functions for AI """
from random import randrange
import queue
from battalion.hexmap import create_hexmap
from game_cmd import GameCmd
from hexl import get_hex_coords_from_direction, hex_next_to_enemies, hex_occupied #pylint: disable=E0401
from hexl import directions

def get_eligible_to_move_to_hex_list(unit, game_dict):
    """ return a list of eligible hexes and a map, the latter is useful for later path
        generation.  """
    move_map = create_hexmap([unit.hex,], game_dict, limit=unit.movement_allowance, source_unit=unit, enforce_zoc=True)
    hex_list = []
    for x in range(game_dict["map_width"]):
        for y in range(game_dict["map_height"]):
            if move_map[x][y] > 0 and move_map[x][y] <= unit.movement_allowance:
                hex_list.append((x,y))
    return hex_list, move_map

def create_path(start_hex, dest_hex, move_map):
    return [start_hex, dest_hex]

def ai_circle(unit, game_dict):
    """ Return CMD string for unit using strategy CIRCLE. """
    newx, newy = get_hex_coords_from_direction( \
        directions[game_dict["game_turn"]%6], unit.hex, game_dict)
    if not hex_occupied(unit.hex, game_dict):
        return(GameCmd(unit, None, "MV", [unit.hex, (newx, newy)]))
    return GameCmd(unit, None, "PASS", None)

def ai_prevent_evacuation(unit, game_dict):
    """ Hunt units while guarding the evacuation point.  """

    # The evac_hexmap is distance to the evacuation hex
    evac_hexmap = create_hexmap([ \
        (game_dict["evacuation_hex"][0], game_dict["evacuation_hex"][1]), ], game_dict)

    # Create a list of the enemy units
    e_unit_list = []
    e_player = 1 - unit.player
    for battalion in game_dict["players"][e_player].battalion:
        for e_unit in battalion.units:
            e_unit_list.append(e_unit.hex)

    # Create the enemy hexmap: the distance to the enemies
    enemy_hexmap = create_hexmap(e_unit_list, game_dict)

    # Add the two maps together.
    enemy_hexmap = evac_hexmap + enemy_hexmap

    # Is this unit already in the enemy zoc?
    started_in_zoc = hex_next_to_enemies(unit.hex, 1-unit.player, game_dict)
    if started_in_zoc:
        return GameCmd(unit, None, "PASS", None) # Stay engaged

    # Figure out which hex we want to move to.
    candidate_list = []
    highval = 199
    eligible_hex_list, move_map = get_eligible_to_move_to_hex_list(unit, game_dict)
    for eligible_hex in eligible_hex_list:
        if eligible_hex is not None and \
            not hex_occupied(eligible_hex, game_dict) and \
            (not (started_in_zoc and hex_next_to_enemies(eligible_hex, 1-unit.player, game_dict))):
            if enemy_hexmap[eligible_hex[0]][eligible_hex[1]] < highval:
                candidate_list = [eligible_hex,]
                highval = enemy_hexmap[eligible_hex[0]][eligible_hex[1]]
            elif enemy_hexmap[eligible_hex[0]][eligible_hex[1]] == highval:
                if evac_hexmap[eligible_hex[0]][eligible_hex[1]] > \
                    evac_hexmap[candidate_list[0][0]][candidate_list[0][1]]:
                    candidate_list = [eligible_hex,]
                elif evac_hexmap[eligible_hex[0]][eligible_hex[1]] == \
                    evac_hexmap[candidate_list[0][0]][candidate_list[0][1]]:
                    candidate_list.append(eligible_hex)

    if len(candidate_list) == 0:
        return GameCmd(unit, None, "PASS", None)
    dest_hex = candidate_list[randrange(len(candidate_list))]
    path = create_path(unit.hex, dest_hex, move_map)
    return GameCmd(unit, None, "MV", path)

def ai_evacuate(unit, game_dict):
    """ return CMD string for unit using strategy EVACUATE. """

    # Create a hexmap with the evacuation hex as its origin.
    hexmap = create_hexmap([(game_dict["evacuation_hex"][0], game_dict["evacuation_hex"][1]), ], \
        game_dict)

    if hexmap[unit.hex[0]][unit.hex[1]] == 0:
        return GameCmd(unit, None, "EVACUATE", None)

    # Choose one of the candidates randomly
    candidate_list = []
    started_in_zoc = hex_next_to_enemies(unit.hex, 1-unit.player, game_dict)
    if started_in_zoc:
        threshold_val = 998
    else:
        threshold_val = hexmap[unit.hex[0]][unit.hex[1]]
    for direct in directions:
        adj_hex = get_hex_coords_from_direction(direct, unit.hex, game_dict)
        if adj_hex is not None and \
            hexmap[adj_hex[0]][adj_hex[1]] < threshold_val and \
            not hex_occupied(adj_hex, game_dict) and \
            (not (started_in_zoc and hex_next_to_enemies(adj_hex, 1-unit.player, game_dict))):
            candidate_list.append(adj_hex)
    if len(candidate_list) == 0:
        return GameCmd(unit, None, "PASS", None)
    next_hex = candidate_list[randrange(len(candidate_list))]
    return GameCmd(unit, None, "MV", [unit.hex, next_hex])
