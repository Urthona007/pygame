""" Manage hexes """
from random import randrange
from pygame import draw #pylint: disable=E0401

directions = ("N", "NE", "SE", "S", "SW", "NW")
def draw_hexes(screen, game_dict):
    """ draw the hexes """
    hexagon = ((0.0, 0.0),(0.333, -0.5), (1.0, -0.5), (1.333, 0.0), (1.0, 0.5), (0.333, 0.5))
    for x in range(game_dict['map_width']):
        for y in range(game_dict['map_height']):
            if not x%2 and y == game_dict['map_height']-1: # Legal?
                break
            x_offset, y_offset = get_hex_offset((x, y), game_dict)
            hex_poly = []
            for coordinate in hexagon:
                hex_poly.append(( \
                    x_offset + coordinate[0]*game_dict['map_multiplier'], \
                    y_offset + game_dict['map_multiplier'] + \
                    coordinate[1]*game_dict['map_multiplier']))
            hex_color = (0, 100, 0)
            if game_dict["evacuation_hex"] == (x, y):
                hex_color = (190, 190, 0)
            if game_dict["bears_den"] == (x, y):
                hex_color = (60, 0, 60)
            hex_outline_color = (0, 0, 0)
            draw.polygon(screen, hex_color, hex_poly, 0)
            draw.lines(screen, hex_outline_color, True, hex_poly, 3)

def get_hex_offset(a_hex, game_dict):
    """ get hex offset in screen coordinates """
    y_offset = a_hex[1] * game_dict['map_multiplier'] + game_dict['map_border'][1]
    if a_hex[0]%2:
        y_offset -= game_dict['map_multiplier']/2
    return a_hex[0] * game_dict['map_multiplier'] + game_dict['map_border'][0], y_offset

def hex_legal(hexx, game_dict):
    """ Very basic check that the hex is legal. """
    # pylint: disable=R0916
    if 0 <= hexx[0] < game_dict["map_width"] and hexx[1] >= 0 and \
        ((hexx[0]%2 and hexx[1] < game_dict["map_height"]) or \
        ((not hexx[0]%2) and hexx[1] < game_dict["map_height"]-1)):
        return True
    return False

def get_random_hex(game_dict, exclude_hexlist):
    """ Retrieve a random hex from the map, with option exclude list. """
    found = False
    while not found:
        candidate_hex = (randrange(game_dict["map_width"]), randrange(game_dict["map_height"]))
        found = hex_legal(candidate_hex, game_dict) and candidate_hex not in exclude_hexlist
    return candidate_hex

def get_random_edge_hex(game_dict):
    """ Retrieve a random hex on the edge of the map."""
    found = False
    while not found:
        candidate_hex = (randrange(game_dict["map_width"]), randrange(game_dict["map_height"]))
        if hex_legal(candidate_hex, game_dict):
            if candidate_hex[0] == 0 or candidate_hex[0] == (game_dict["map_width"] - 1) or \
                candidate_hex[1] == 0 or \
                (candidate_hex[0]%2 and candidate_hex[1] == (game_dict["map_height"] - 1)) or \
                ((not candidate_hex[0]%2) and candidate_hex[1] == (game_dict["map_height"]-2)):
                found = True
    return candidate_hex

def get_hex_coords_from_direction(direction, hexx, game_dict): # pylint: disable=R0911,R0912
    """ given a hex and direction, return that hex's address is legal. """
    x = hexx[0]
    y = hexx[1]
    if direction == "N":
        if hex_legal((x, y-1), game_dict):
            return (x, y-1)
    elif direction == "S":
        if hex_legal((x, y+1), game_dict):
            return (x, y+1)
    elif direction == "NE":
        if x%2 and hex_legal((x+1, y-1), game_dict):
            return (x+1, y-1)
        if not x%2 and hex_legal((x+1, y), game_dict):
            return (x+1, y)
    elif direction == "SE":
        if x%2 and hex_legal((x+1, y), game_dict):
            return (x+1, y)
        if not x%2 and hex_legal((x+1, y+1), game_dict):
            return (x+1, y+1)
    elif direction == "NW":
        if x%2 and hex_legal((x-1, y-1), game_dict):
            return (x-1, y-1)
        if not x%2 and hex_legal((x-1, y), game_dict):
            return (x-1, y)
    elif direction == "SW":
        if x%2 and hex_legal((x-1, y), game_dict):
            return (x-1, y)
        if not x%2 and hex_legal((x-1, y+1), game_dict):
            return (x-1, y+1)
    return None

def hex_occupied(hexx, game_dict):
    """ Return a unit if the hex is occupied, else return none. """
    for player in game_dict["players"]:
        for battalion in player.battalion:
            for unit in battalion.units:
                if unit.hex == hexx:
                    return unit
    return None

def hex_next_to_enemies(hexx, enemy_player_num, game_dict):
    """ Search the 6 adjacent hexes to see if an enemy is there.  Return True/False. """
    for direct in directions:
        adj_hex = get_hex_coords_from_direction(direct, hexx, game_dict)
        if adj_hex is not None:
            eunit = hex_occupied(adj_hex, game_dict)
            if eunit and eunit.player_num == enemy_player_num:
                return True
    return False

