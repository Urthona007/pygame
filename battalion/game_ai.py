""" Functions for AI """
from random import randrange
from unit import get_player_active_units_and_hexes
from hexmap import create_hexmap
from game_cmd import GameCmd
from hexl import get_hex_coords_from_direction, hex_next_to_enemies, hex_occupied #pylint: disable=E0401
from hexl import directions

def get_eligible_to_move_to_hex_list(unit, game_dict):
    """ return a list of eligible hexes and a map, the latter is useful for later path
        generation.  """
    move_map = create_hexmap([unit.hex,], game_dict, limit=unit.movement_allowance, \
        source_unit=unit, enforce_zoc=True)
    hex_list = []
    for x in range(game_dict["map_width"]):
        for y in range(game_dict["map_height"]):
            if move_map[x][y] > 0 and move_map[x][y] <= unit.movement_allowance:
                hex_list.append((x,y))
    return hex_list, move_map

def create_path(start_hex, dest_hex, move_map, enemy_player, game_dict):
    """ Create a list of hexes that is a legal path for a move."""
    path = [dest_hex]
    while path[0] != start_hex:
        candidate_list = []
        for direct in directions:
            adj_hex = get_hex_coords_from_direction(direct, path[0], game_dict)
            if adj_hex == start_hex:
                path.insert(0, adj_hex)
                return path
            if adj_hex is not None and \
                move_map[adj_hex[0]][adj_hex[1]] < move_map[path[0][0]][path[0][1]] and \
                not hex_occupied(adj_hex, game_dict) and \
                not hex_next_to_enemies(adj_hex, enemy_player, game_dict):
                candidate_list.append(adj_hex)
        assert candidate_list
        next_hex = candidate_list[randrange(len(candidate_list))]
        path.insert(0, next_hex)
    assert False

def ai_circle(unit, game_dict):
    """ Return CMD string for unit using strategy CIRCLE. """
    newx, newy = get_hex_coords_from_direction( \
        directions[game_dict["game_turn"]%6], unit.hex, game_dict)
    if not hex_occupied(unit.hex, game_dict):
        return(GameCmd(unit, None, "MV", [unit.hex, (newx, newy)]))
    return GameCmd(unit, None, "PASS", None)

def ai_prevent_evacuation(unit, game_dict):
    """ Hunt units while guarding the evacuation point.  """
    # Is this unit already in the enemy zoc?
    started_in_zoc = hex_next_to_enemies(unit.hex, 1-unit.player_num, game_dict)
    if started_in_zoc:
        return GameCmd(unit, None, "PASS", None) # Stay engaged

    # The evac_hexmap is distance to the evacuation hex, it ignores blocking units
    evac_hexmap = create_hexmap([ \
        (game_dict["evacuation_hex"][0], game_dict["evacuation_hex"][1]), ], game_dict)

    # Retrieve list of active enemy unit hexes
    e_player_num = 1 - unit.player_num
    unused_e_unit_list, e_unit_hex_list = get_player_active_units_and_hexes(game_dict["players"][e_player_num])

    # Create the enemy hexmap: the distance to the enemies, it ignores blocking units
    enemy_hexmap = create_hexmap(e_unit_hex_list, game_dict)

    # Add the two maps together.  We will then find the hexes with the lowest sum, in
    # theory, a good balance between guarding the evacuation point but also chasing
    # the enemy.
    combined_hexmap = evac_hexmap + enemy_hexmap

    # Create another hexmap that is the hexes that this unit's movement allowance allows
    # it to reach.  This function does that and also returns the eligible hexes in a list.
    # Figure out which hex we want to move to.
    eligible_hex_list, move_map = get_eligible_to_move_to_hex_list(unit, game_dict)

    # Create a candidate list of best hexes to move to.
    candidate_list = []
    highval = 199
    for eligible_hex in eligible_hex_list:
        # We first look for the most favorable (lowest) enemy_hexmap value
        combo_hexval = combined_hexmap[eligible_hex[0]][eligible_hex[1]]
        if combo_hexval < highval:
            candidate_list = [eligible_hex,]
            highval = combo_hexval
        elif combo_hexval == highval:
            # in case of a tie, use the most favorable (lowest) enemy_hexmap value
            # to break the tie.
            enemy_hexval = enemy_hexmap[eligible_hex[0]][eligible_hex[1]]
            current_list_enemy_hexval = enemy_hexmap[candidate_list[0][0]][candidate_list[0][1]]
            if enemy_hexval < current_list_enemy_hexval:
                candidate_list = [eligible_hex,] # This is the sole best candidate
            elif enemy_hexval == current_list_enemy_hexval:
                candidate_list.append(eligible_hex)
            else:
                pass

    # If no candidates, just pass
    if len(candidate_list) == 0:
        return GameCmd(unit, None, "PASS", None)

    # Randomly choose the best candidate to be the destination hex if more than one.
    dest_hex = candidate_list[randrange(len(candidate_list))]
    path = create_path(unit.hex, dest_hex, move_map, 1-unit.player_num, game_dict)
    return GameCmd(unit, None, "MV", path)

def ai_evacuate(unit, game_dict):
    """ return CMD string for unit using strategy EVACUATE. """

    # Create a hexmap with the evacuation hex as its origin.  Enemy can block this.
    evac_hexmap = create_hexmap( \
        [(game_dict["evacuation_hex"][0], game_dict["evacuation_hex"][1]), ], \
        game_dict, limit=99, source_unit=unit, enforce_zoc=True)

    if evac_hexmap[unit.hex[0]][unit.hex[1]] == 0:
        return GameCmd(unit, None, "EVACUATE", None)

    # Retrieve list of active enemy unit hexes and create a hexmap.
    e_player = 1 - unit.player
    unused_e_unit_list, e_unit_hex_list = get_player_active_units_and_hexes(game_dict["players"][e_player])
    enemy_hexmap = create_hexmap(e_unit_hex_list, game_dict)

    # Create another hexmap that is the hexes that this unit's movement allowance allows
    # it to reach.  This function does that and also returns the eligible hexes in a list.
    # Figure out which hex we want to move to.
    eligible_hex_list, move_map = get_eligible_to_move_to_hex_list(unit, game_dict)

    # Remove any hexes that are adjacent to the enemy
    filtered_eligible_hex_list = []
    for hexx in eligible_hex_list:
        if not hex_next_to_enemies(hexx, 1-unit.player_num, game_dict):
            filtered_eligible_hex_list.append(hexx)

    if not filtered_eligible_hex_list:
        return GameCmd(unit, None, "PASS", None)

    # Create a candidate_list.  We want the lowest evac hex and the highest enemy hex.
    combo_hexmap = evac_hexmap - enemy_hexmap
    #started_in_zoc = hex_next_to_enemies(unit.hex, 1-unit.player, game_dict)
    #if started_in_zoc:
    #    threshold_val = 998
    #else:
    #    threshold_val = hexmap[unit.hex[0]][unit.hex[1]]
    candidate_list = []
    for hexx in filtered_eligible_hex_list:
        if (not candidate_list) or \
            combo_hexmap[hexx[0]][hexx[1]] < \
            combo_hexmap[candidate_list[0][0]][candidate_list[0][1]]:
            candidate_list = [hexx,]
        elif combo_hexmap[hexx[0]][hexx[1]] == \
            combo_hexmap[candidate_list[0][0]][candidate_list[0][1]]:
            candidate_list.append(hexx)

    dest_hex = candidate_list[randrange(len(candidate_list))]
    path = create_path(unit.hex, dest_hex, move_map, 1-unit.player_num, game_dict)
    return GameCmd(unit, None, "MV", path)

def ai_capture_city_and_destroy(unit, game_dict):
    """ return CMD string for unit trying to capture city and destroy enemies."""
        # Is this unit already in the enemy zoc?
    started_in_zoc = hex_next_to_enemies(unit.hex, 1-unit.player_num, game_dict)
    if started_in_zoc:
        return GameCmd(unit, None, "PASS", None) # Stay engaged

    # The evac_hexmap is distance to the evacuation hex, it ignores blocking units
    den_hexmap = create_hexmap( \
        (game_dict["bears_den"], ), game_dict)

    # Retrieve list of active enemy unit hexes
    e_player_num = 1 - unit.player_num
    unused_e_unit_list, e_unit_hex_list = get_player_active_units_and_hexes(game_dict["players"][e_player_num])

    # Create the enemy hexmap: the distance to the enemies, it ignores blocking units
    enemy_hexmap = create_hexmap(e_unit_hex_list, game_dict)

    # Add the two maps together.  We will then find the hexes with the lowest sum, in
    # theory, a good balance between getting near the bears den but also chasing
    # the enemy.
    combined_hexmap = den_hexmap + enemy_hexmap

    # Create another hexmap that is the hexes that this unit's movement allowance allows
    # it to reach.  This function does that and also returns the eligible hexes in a list.
    # Figure out which hex we want to move to.
    eligible_hex_list, move_map = get_eligible_to_move_to_hex_list(unit, game_dict)

    # Create a candidate list of best hexes to move to.
    candidate_list = []
    highval = 199
    for eligible_hex in eligible_hex_list:
        # We first look for the most favorable (lowest) enemy_hexmap value
        combo_hexval = combined_hexmap[eligible_hex[0]][eligible_hex[1]]
        if combo_hexval < highval:
            candidate_list = [eligible_hex,]
            highval = combo_hexval
        elif combo_hexval == highval:
            # in case of a tie, use the most favorable (lowest) den_hexmap value
            # to break the tie.
            den_hexval = den_hexmap[eligible_hex[0]][eligible_hex[1]]
            current_list_den_hexval = den_hexmap[candidate_list[0][0]][candidate_list[0][1]]
            if den_hexval < current_list_den_hexval:
                candidate_list = [eligible_hex,] # This is the sole best candidate
            elif den_hexval == current_list_den_hexval:
                candidate_list.append(eligible_hex)
            else:
                pass

    # If no candidates, just pass
    if len(candidate_list) == 0:
        return GameCmd(unit, None, "PASS", None)

    # Randomly choose the best candidate to be the destination hex if more than one.
    dest_hex = candidate_list[randrange(len(candidate_list))]
    path = create_path(unit.hex, dest_hex, move_map, 1-unit.player_num, game_dict)
    return GameCmd(unit, None, "MV", path)

def ai_defend_city_and_delay(unit, game_dict):
    """ return CMD string for unit defending a city and delaying enemy advances."""
    return GameCmd(unit, None, "PASS", None)
