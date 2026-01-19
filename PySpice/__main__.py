import json

from PySpice.Spice.Netlist import Circuit
#from PySpice.Unit import *
from PySpice.Spice.NgSpice.Shared import NgSpiceShared
from configurations.constants import BARF, BARE, GROUNDING_RESISTANCE
from components.load_balancer import Load_Balancer
from components.load import Load
from components.battery_array import Battery_Array
from components.mppt import MPPT
from components.solar_panel_array import Solar_Array

PATH = 'pyspice/configurations/circuit_setup.json'
NGSPICE_AVAILABLE = True
ENABLE_LOGGING = False

try:
    NgSpiceShared.new_instance()
except Exception as e:
    NGSPICE_AVAILABLE = False
    print("Follow steps indicated in readme.md to install NgSpice.")

circuit = Circuit("Ideal Simulation Circuit")
components = {
    "panel": [],
    "battery": [],
    "load": [],
    "wire": [],
    "mppt": []
}

def build_circuit_from_json(file_path: str):
    with open(file_path, 'r') as f:
        data = json.load(f)

    # Battery Array
    battery_array = data['battery_setup']
    battery_choice = battery_array['choice']
    battery_config = battery_array[battery_choice]
    battery_array = Battery_Array(circuit, components, **battery_config)
    battery_array.create_battery_array(log=ENABLE_LOGGING)
    
    # MPPT Array
    mppt_array = data['mppt_panel_setup']
    mppt_index = 0
    for key in mppt_array.keys():
        if not key.startswith("config_"):
            continue 
        config = mppt_array[key]
        for _ in range(config['count']):
            solar_array = Solar_Array(circuit, components, **config['panel_info'])
            mppt = MPPT(circuit, components, **config['mppt_info'])
            
            solar_array.create_panels(mppt_index, log=ENABLE_LOGGING)
            mppt.setup_mppt(mppt_index, solar_array, battery_array, log=ENABLE_LOGGING)
            mppt_index += 1
    
    POWER_TO = battery_array.get_terminal()
    circuit.V("total_mppt_output", "power_source", POWER_TO, GROUNDING_RESISTANCE)
        
    # Load/Motor
    motor = Load(circuit, components, **data['load_setup']) 
    motor.setup_load(battery_array, throttle=1, log=ENABLE_LOGGING)
    
    # Load Balancer
    load_balancer = Load_Balancer(circuit, components)
    load_balancer.balance_loads(battery_array)
    
    #display_components(components)
    #display_netlist(circuit)
    begin_simulation()


def display_components(components):
    print("\nComponents in Circuit:")
    for comp_type, comp_list in components.items():
        print(f"{comp_type.capitalize()}: {len(comp_list)}")
        for comp in comp_list:
            print(f"  - {comp}")

def display_netlist(circuit):
    print("\nCircuit Netlist:")
    print(circuit)

def begin_simulation():
    if not NGSPICE_AVAILABLE:
        print("NgSpice is not available. Simulation cannot proceed.")
        return
    try:
        simulator = circuit.simulator(temperature=25, nominal_temperature=25)
        analysis = simulator.operating_point()

        print(f"{BARF}Simulation Results:{BARE}")

        # Node voltages
        for node_name, node in analysis.nodes.items():
            voltage = float(node.as_ndarray()[0])
            print(f"Node {node_name}: {voltage:.3f} V")

        # Branch currents
        for branch_name, branch in analysis.branches.items():
            current = float(branch.as_ndarray()[0])
            print(f"Branch {branch_name}: {current:.3f} A")

    except Exception as e:
        print("An error occurred during simulation:")
        print(e)
            
build_circuit_from_json(PATH)