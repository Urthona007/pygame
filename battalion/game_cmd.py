""" cmd """

from hexl import hex_next_to_enemies

class CombatCmd():
    def __init__(self, attackers, defenders, attack_strength, defense_strength, cmd):
        self.attackers = attackers
        self.defenders = defenders
        self.attack_strength = attack_strength
        self.defense_strength = defense_strength
        self.cmd = cmd

    def __str__(self):
        return f"{self.attack_strength}/{self.defense_strength} {self.cmd}"

class GameCmd():
    "Holds game command info."
    def __init__(self, unit, e_unit, cmd, hexes):
        self.unit = unit
        self.e_unit = e_unit
        self.cmd = cmd
        self.hexes = hexes

    def __str__(self):
        if self.cmd in ("ATTACK", "MV"):
            return f"{self.cmd} {self.unit.get_name()} \"{self.hexes}\""
        return f"{self.cmd} {self.unit.get_name()}"

    def validate(self, game_dict):
        """ Check that the received command is legal."""
        if self.cmd == "MV":
            # ZOC check
            starting_in_zoc = hex_next_to_enemies(self.hexes[0], 1-self.unit.player_num, game_dict)

            # in route
            for hexx in self.hexes[1:-1]:
                in_zoc = hex_next_to_enemies(hexx, 1-self.unit.player_num, game_dict)
                if in_zoc:
                    game_dict["logger"].error(f"MV ZOC VIOLATION(1): hex {hexx} of cmd {self}")
                    return False

            # final destination
            in_zoc = hex_next_to_enemies(self.hexes[-1], 1-self.unit.player_num, game_dict)
            if in_zoc and starting_in_zoc:
                game_dict["logger"].error(f"MV ZOC VIOLATION(2): hex {self.hexes[-1]} of cmd {self}")
                return False
        return True
