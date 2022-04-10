""" Battalion Main """
import pygame #pylint: disable=E0401
import unit
from hexl import draw_hexs

def draw_map(screen, a_game_dict):
    """ Draw game map. """
    draw_hexs(screen, a_game_dict)

pygame.init()
game_dict = {'name': 'Battalion', 'display_width' : 640, 'display_height' : 480, \
    'bkg_color': (50, 50, 50), 'map_width': 11, 'map_height': 8, 'map_multiplier': 50, \
    'map_border' : 8, 'unit_width': 32, 'unit_x_offset': 18, 'unit_y_offset': 34}
units = ([], [])
units[0].append(unit.Unit("infantry", 1, 4, 2, 0))
units[1].append(unit.Unit("infantry", 1, 7, 7, 1))

pygame.display.set_caption(game_dict['name']) # NOTE: this is not working.
game_running = True
batt_screen = pygame.display.set_mode((game_dict['display_width'], game_dict['display_height']))

update_screen = True
while game_running:
    for event in pygame.event.get():
        # print(event)
        if event.type == pygame.QUIT:
            game_running = False
    if update_screen:
        batt_screen.fill(game_dict['bkg_color'])
        draw_map(batt_screen, game_dict)
        unit.draw_units(batt_screen, units, game_dict)
        pygame.display.update()
        update_screen = False
pygame.quit()
