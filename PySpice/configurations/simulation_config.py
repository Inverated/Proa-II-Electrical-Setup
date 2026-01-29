import os

path = os.getcwd()

CONFIG_FILE             = os.path.join(path, 'pyspice\\configurations\\circuit_setup.json')
SIM_SAVE_PATH           = os.path.join(path, 'pyspice\\result')
SWEEP_SAVE_PATH         = os.path.join(path, 'pyspice\\result')
SWEEP_INTERVAL_COUNT    = 100   # Number of intervals in sweep simulation
SAVE_OUTPUT             = 1     # Save json output for operating point simulations only

IGNORE_ERROR            = 1
START_SIMULATION        = 1
SIMULATION_LOGGING      = 0
SHOW_SWEEP_PLOT         = 1
RAWSPICE_ITERATIONS     = 1e6


# Disable logging for deployed versions
COMPONENT_LOGGING       = 0
SHOW_COMPONENTS         = 0
SHOW_PANELS             = 0
SHOW_NETLIST            = 0
SHOW_ERRORS             = 0
SHOW_WARNINGS           = 0

