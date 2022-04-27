""" cmd """

class GameCmd():
    def __init__(self, unit, e_unit, cmd, hexs):
        self.unit = unit
        self.e_unit = e_unit
        self.cmd = cmd
        self.hexs = hexs

    def __str__(self):
        if self.cmd == "ATTACK" or self.cmd == "MV":
            return(f"{self.unit.name}: {self.cmd} {self.hexs}")
        else:
            return(f"{self.unit.name}: {self.cmd}")