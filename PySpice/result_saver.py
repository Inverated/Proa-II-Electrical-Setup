import json
import os

from configurations.constants import BARE, BARF
from configurations.simulation_config import SIM_SAVE_PATH, SAVE_OUTPUT

def save_to_file(result):
    json_result = json.dumps(result, indent=4)
    save_path = os.path.join(SIM_SAVE_PATH, 'simulation_results.json')
    with open(save_path, 'w') as f:
        f.write(json_result)
        print(f"\n{BARF}Simulation results saved to {save_path}{BARE}")