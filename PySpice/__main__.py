from simulation_over_time import real_time_digital_simulation, start_voyage
from simulation_sweeper import sweep_panel_power, sweep_throttle
from circuit_constructor import build_circuit_from_json
from pyspice_simulator import begin_simulation
from result_saver import save_to_file
from configurations.constants import *
from configurations.simulation_config import *
from PySpice.Spice.NgSpice.Shared import NgSpiceShared
import os


# 0: operating_point / 1:sweep throttle / 2: sweep panel power / 3: Voyage mode / 4: RTDS mode
SIMULATION_TYPE         = 3


path = os.getcwd()
CIRCUIT_CONFIG_FILE     = os.path.join(path, 'pyspice\\configurations\\circuit_setup.json')
VOYAGE_CONFIG_FILE      = os.path.join(path, 'pyspice\\configurations\\voyage_setup.json')

SIM_SAVE_PATH           = os.path.join(path, 'pyspice\\result\\operating_point_result')
SWEEP_SAVE_PATH         = os.path.join(path, 'pyspice\\result\\sweep_result')
VOYAGE_RESULT_SAVE_PATH = os.path.join(path, 'pyspice\\result\\voyage_result')

ngspice_available = True

try:
    NgSpiceShared.new_instance()
except Exception as e:
    ngspice_available = False
    print("Follow steps indicated in readme.md to install NgSpice.")


if __name__ == "__main__":
    if SIMULATION_TYPE == 0:
        circuit, component_object, errors = build_circuit_from_json(CIRCUIT_CONFIG_FILE)
        analysis, result = begin_simulation(circuit, component_object, errors, ngspice_available)
        
        if START_SIMULATION and SAVE_OUTPUT:
            save_to_file(result, save_path=SIM_SAVE_PATH)

    elif SIMULATION_TYPE == 1:
        sweep_throttle(circuit_config_loc=CIRCUIT_CONFIG_FILE, save_path=SWEEP_SAVE_PATH, ngspice_available=ngspice_available)
        
    elif SIMULATION_TYPE == 2:
       sweep_panel_power(circuit_config_loc=CIRCUIT_CONFIG_FILE, save_path=SWEEP_SAVE_PATH, ngspice_available=ngspice_available)

    elif SIMULATION_TYPE == 3:
        start_voyage(circuit_config_loc=CIRCUIT_CONFIG_FILE, voyage_config_loc=VOYAGE_CONFIG_FILE, save_path=VOYAGE_RESULT_SAVE_PATH, ngspice_available=ngspice_available)
    elif SIMULATION_TYPE == 4:
        real_time_digital_simulation(circuit_config_loc=CIRCUIT_CONFIG_FILE, ngspice_available=ngspice_available)
    else: 
        print("Invalid SIMULATION_TYPE selected.")
        exit(1)