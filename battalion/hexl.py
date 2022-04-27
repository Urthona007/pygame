""" Manage hexs """
from pygame import draw #pylint: disable=E0401

directions = ("N", "NE", "SE", "S", "SW", "NW")
def draw_hexs(screen, game_dict):
    """ draw the hexs """
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
            if game_dict["evacuation_hex"] and game_dict["evacuation_hex"][0] == x \
                and game_dict["evacuation_hex"][1] == y:
                hex_color = (190, 190, 0)
            hex_outline_color = (0, 0, 0)
            draw.polygon(screen, hex_color, hex_poly, 0)
            draw.lines(screen, hex_outline_color, True, hex_poly, 3)

def get_hex_offset(a_hex, game_dict):
    """ get hex offset in screen coordinates """
    y_offset = a_hex[1] * game_dict['map_multiplier'] + game_dict['map_border'][1]
    if a_hex[0]%2:
        y_offset -= game_dict['map_multiplier']/2
    return a_hex[0] * game_dict['map_multiplier'] + game_dict['map_border'][0], y_offset

def hex_legal(x, y, game_dict):
    """ Very basic check that the hex is legal. """
    # pylint: disable=R0916
    if 0 <= x < game_dict["map_width"] and y >= 0 and \
        ((x&2 and y < game_dict["map_height"]) or ((not x&2) and y < game_dict["map_height"]-1)):
        return True
    return False

def get_hex_coords_from_direction(direction, x, y, game_dict): # pylint: disable=R0911,R0912
    """ given a hex and direction, return that hex's address is legal. """
    if direction == "N":
        if hex_legal(x, y-1, game_dict):
            return x, y-1
    elif direction == "S":
        if hex_legal(x, y+1, game_dict):
            return x, y+1
    elif direction == "NE":
        if x%2 and hex_legal(x+1, y-1, game_dict):
            return x+1, y-1
        if not x%2 and hex_legal(x+1, y, game_dict):
            return x+1, y
    elif direction == "SE":
        if x%2 and hex_legal(x+1, y, game_dict):
            return x+1, y
        if not x%2 and hex_legal(x+1, y+1, game_dict):
            return x+1, y+1
    elif direction == "NW":
        if x%2 and hex_legal(x-1, y-1, game_dict):
            return x-1, y-1
        if not x%2 and hex_legal(x-1, y, game_dict):
            return x-1, y
    elif direction == "SW":
        if x%2 and hex_legal(x-1, y, game_dict):
            return x-1, y
        if not x%2 and hex_legal(x-1, y+1, game_dict):
            return x-1, y+1
    return None, None

def hex_occupied(x, y, game_dict):
    """ Return a unit if the hex is occupied, else return none. """
    for player in game_dict["players"]:
        for battalion in player.battalion:
            for unit in battalion.units:
                if unit.x == x and unit.y == y:
                    return unit
    return None

def hex_next_to_enemies(x, y, enemy_player, game_dict):
    """ Search the 6 adjacent hexes to see if an enemy is there.  Return True/False. """
    for direct in directions:
        adjx, adjy = get_hex_coords_from_direction(direct, x, y, game_dict)
        if adjx is not None and adjy is not None:
            eunit = hex_occupied(adjx, adjy, game_dict)
            if eunit and eunit.player == enemy_player:
                return True
    return False
