import pygame.draw

def draw_hexs(screen, game_dict):
    HEXAGON = ((0.0, 0.0),(0.333, -0.5), (1.0, -0.5), (1.333, 0.0), (1.0, 0.5), (0.333, 0.5))
    print(HEXAGON)
    for x in range(game_dict['map_width']):
        for y in range(game_dict['map_height']):
            if not x%2 and y == game_dict['map_height']-1: # Legal?
                break
            x_offset, y_offset = get_hex_offset(x, y, game_dict)
            hex_poly = []
            for coordinate in HEXAGON:
                hex_poly.append(( \
                    x_offset + coordinate[0]*game_dict['map_multiplier'], \
                    y_offset + game_dict['map_multiplier']+coordinate[1]*game_dict['map_multiplier']))
            HEX_COLOR = (0, 100, 0)
            HEX_OUTLINE_COLOR = (0, 0, 0)
            rect = pygame.draw.polygon(screen, HEX_COLOR, hex_poly, 0)
            rect = pygame.draw.lines(screen, HEX_OUTLINE_COLOR, True, hex_poly, 3)

def get_hex_offset(x, y, game_dict):
    y_offset = y * game_dict['map_multiplier'] + game_dict['map_border']
    if x%2:
        y_offset -= game_dict['map_multiplier']/2
    return x * game_dict['map_multiplier'] + game_dict['map_border'], y_offset


