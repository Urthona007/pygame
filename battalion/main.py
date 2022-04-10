""" Battalion Main """
import pygame

def get_hex_offset(x, y):
    y_offset = y * game_dict['map_multiplier'] + game_dict['map_border']
    if x%2:
        y_offset -= game_dict['map_multiplier']/2
    return x * game_dict['map_multiplier'] + game_dict['map_border'], y_offset

def draw_hexs(screen):
    HEXAGON = ((0.0, 0.0),(0.333, -0.5), (1.0, -0.5), (1.333, 0.0), (1.0, 0.5), (0.333, 0.5))
    print(HEXAGON)
    for x in range(game_dict['map_width']):
        for y in range(game_dict['map_height']):
            if not x%2 and y == game_dict['map_height']-1: # Legal?
                break
            x_offset, y_offset = get_hex_offset(x, y)
            hex_poly = []
            for coordinate in HEXAGON:
                hex_poly.append(( \
                    x_offset + coordinate[0]*game_dict['map_multiplier'], \
                    y_offset + game_dict['map_multiplier']+coordinate[1]*game_dict['map_multiplier']))
            HEX_COLOR = (0, 100, 0)
            HEX_OUTLINE_COLOR = (0, 0, 0)
            rect = pygame.draw.polygon(screen, HEX_COLOR, hex_poly, 0)
            rect = pygame.draw.lines(screen, HEX_OUTLINE_COLOR, True, hex_poly, 3)


def draw_map(screen):
    draw_hexs(screen)

def draw_units(screen):
    for player in units:
        for unit in player:
            x_offset, y_offset = get_hex_offset(unit.x, unit.y)
            rect = pygame.draw.rect(screen, (0, 240, 240), \
                (x_offset + game_dict['unit_x_offset'], y_offset + game_dict['unit_y_offset'], \
                 game_dict['unit_width'], game_dict['unit_width']))

class unit():
    def __init__(self, type, strength, x, y, player):
        self.type = type
        self.strength = strength
        self.x = x
        self.y = y
        self.player = player # warning, chance of info in 2 places.


pygame.init()
game_dict = {'name': 'Battalion', 'display_width' : 640, 'display_height' : 480, \
    'bkg_color': (50, 50, 50), 'map_width': 11, 'map_height': 8, 'map_multiplier': 50, \
    'map_border' : 8, 'unit_width': 32, 'unit_x_offset': 18, 'unit_y_offset': 34}
units = ([], [])
units[0].append(unit("infantry", 1, 4, 2, 0))
units[1].append(unit("infantry", 1, 7, 7, 1))

pygame.display.set_caption(game_dict['name'])
game_running = True
screen = pygame.display.set_mode((game_dict['display_width'], game_dict['display_height']))

update_screen = True
while game_running:
    for event in pygame.event.get():
        # print(event)
        if event.type == pygame.QUIT:
            game_running = False
    if update_screen:
        screen.fill(game_dict['bkg_color'])
        draw_map(screen)
        draw_units(screen)
        pygame.display.update()
        update_screen = False
pygame.quit()
