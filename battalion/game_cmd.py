""" cmd """

from hexl import hex_next_to_enemies


class GameCmd():
    "Holds game command info."
    def __init__(self, unit, e_unit, cmd, hexs):
        self.unit = unit
        self.e_unit = e_unit
        self.cmd = cmd
        self.hexs = hexs

    def __str__(self):
        if self.cmd in ("ATTACK", "MV"):
            return f"{self.cmd} {self.unit.get_name()} \"{self.hexs}\""
        return f"{self.cmd} {self.unit.get_name()}"

    def validate(self, game_dict):
        """ Check that the received command is legal."""
        if self.cmd == "MV":
            # ZOC check
            starting_in_zoc = hex_next_to_enemies(self.hexs[0], 1-self.unit.player, game_dict)

            # in route
            for hexx in self.hexs[1:-1]:
                in_zoc = hex_next_to_enemies(hexx, 1-self.unit.player, game_dict)
                if in_zoc == starting_in_zoc:
                    game_dict["logger"].error(f"MV ZOC VIOLATION {self}")
                    return False

            # final destination
            in_zoc = hex_next_to_enemies(self.hexs[-1], 1-self.unit.player, game_dict)
            if in_zoc == starting_in_zoc == True:
                game_dict["logger"].error(f"MV ZOC VIOLATION {self}")
                return False
        return True
