""" time/performance settings """
from time import sleep

def sleap_waiting_for_other_thread(): # pylint: disable=C0116
    sleep(0.1)
def sleap_waiting_for_user(): # pylint: disable=C0116
    sleep(0.1)
def sleap_post_game_phase(): # pylint: disable=C0116
    sleep(0.0) #2.0)
def sleap_post_game_turn(): # pylint: disable=C0116
    sleep(0.1) # A small cushion gives display thread time to check victory conditions
def get_mv_animation_base_duration(): # pylint: disable=C0116
    return 0.25
def get_attack_animation_duration(): # pylint: disable=C0116
    return 0.75
