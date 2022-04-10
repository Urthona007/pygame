""" Manage hexs """
from pygame import draw #pylint: disable=E0401

def draw_hexs(screen, game_dict):
    """ draw the hexs """
    hexagon = ((0.0, 0.0),(0.333, -0.5), (1.0, -0.5), (1.333, 0.0), (1.0, 0.5), (0.333, 0.5))
    for x in range(game_dict['map_width']):
        for y in range(game_dict['map_height']):
            if not x%2 and y == game_dict['map_height']-1: # Legal?
                break
            x_offset, y_offset = get_hex_offset(x, y, game_dict)
            hex_poly = []
            for coordinate in hexagon:
                hex_poly.append(( \
                    x_offset + coordinate[0]*game_dict['map_multiplier'], \
                    y_offset + game_dict['map_multiplier'] + \
                    coordinate[1]*game_dict['map_multiplier']))
            hex_color = (0, 100, 0)
            hex_outline_color = (0, 0, 0)
            draw.polygon(screen, hex_color, hex_poly, 0)
            draw.lines(screen, hex_outline_color, True, hex_poly, 3)

def get_hex_offset(x, y, game_dict):
    """ get hex offset in screen coordinates """
    y_offset = y * game_dict['map_multiplier'] + game_dict['map_border']
    if x%2:
        y_offset -= game_dict['map_multiplier']/2
    return x * game_dict['map_multiplier'] + game_dict['map_border'], y_offset
