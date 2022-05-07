""" cmd """

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
