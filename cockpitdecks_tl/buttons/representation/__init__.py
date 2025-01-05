# Toliss Airbus specific
from .tl_fma import FMAIcon
from .tl_fcu import FCUIcon

#
# Flight Phases
#
FLIGHT_PHASE_ECAM = [
    "OFF",  # 0
    "ELEC POWER",
    "FIRST ENG STARTED",
    "FIRST ENG TO POWER",
    "80KT",
    "LIFT OFF",
    "1500 FT",
    "800 FT",
    "TOUCHDOWN",
    "80KT",
    "2ND ENG SHUTDOWN",
    "5 MIN AFTER",  # 10
]

FLIGHT_PHASE_QPAC = [
    "OFF",  # 0
    "ELEC POWER",
    "SECOND ENGINE START",
    "FIRST ENG T.O. POWER",
    "70KT",
    "LIFT OFF",
    "LIST OFF + 1 MINUTE OR 400FT",
    "1000FTUP",
    "1000FTDW",
    "400FT",
    "TOUCH DOWN",
    "70KT",
    "FIRST ENG SHUTDOWN",
    "5 MINUTES AFTER SECOND ENG SHUT DOWN",  # 13
]
