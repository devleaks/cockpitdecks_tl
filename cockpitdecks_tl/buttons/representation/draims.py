"""Digital Radio and Audio Integrating Management System

"""

import logging

from cockpitdecks.variable import VariableListener

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


DRAIMS_COLORS = {
    "a": "#FD8008",  # BF521A , amber, dark yellow
    "b": "#2FAFDB",
    "g": "#63E224",
    "m": "#DE50DC",
    "s": "#FFFFFF",  # special characters, not a color
    "w": "#DDDDDD",
    "y": "#EEEE00",
}

DRAIMS_UNIT = "draims-unit"

DRAIMS_DATAREFS = [
    "AirbusFBW/RMP1Freq",
    "AirbusFBW/RMP1StbyFreq",
    "AirbusFBW/RMP2Freq",
    "AirbusFBW/RMP2StbyFreq",
    "AirbusFBW/RMP3/ActiveWindowString",
    "AirbusFBW/RMP3/StandbyWindowString",
    "AirbusFBW/XPDRString",
]


class DRAIMS(VariableListener):

    def __init__(self) -> None:
        VariableListener.__init__(self, name="DRAIMS")
        self.variables = None
        self.datarefs = {}
        self.lines = {}
        self._first = True

    def init(self, simulator):
        for varname in self.get_variables():
            var = simulator.get_variable(name=varname)
            var.add_listener(self)
            self.datarefs[varname] = var
        logger.info(f"DRAIMS requests {len(self.variables)} variables")

    def get_variables(self) -> set:
        if self.variables is not None:
            return self.variables
        variables = set(DRAIMS_DATAREFS)
        self.variables = variables
        return variables

    def completed(self) -> bool:
        return len(self.variables) == len(self.datarefs)

    def variable_changed(self, variable):
        if not variable.has_changed():
            return
