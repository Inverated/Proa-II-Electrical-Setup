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
IGNORE_ERROR = True

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
    
    errors = []
    # Battery Array
    battery_array = data['battery_setup']
    battery_choice = battery_array['choice']
    battery_config = battery_array[battery_choice]
    battery_array = Battery_Array(circuit, components, **battery_config)
    res = battery_array.create_battery_array(log=ENABLE_LOGGING)
    errors.append(res) if res else None
    
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
            res = mppt.setup_mppt(mppt_index, solar_array, battery_array, log=ENABLE_LOGGING)
            errors.append(res) if res else None
            mppt_index += 1
            
    
    POWER_TO = battery_array.get_terminal()
    circuit.V("total_mppt_output", "power_source", POWER_TO, GROUNDING_RESISTANCE)
        
    # Load/Motor
    motor = Load(circuit, components, **data['load_setup']) 
    res = motor.setup_load(battery_array, throttle=1, log=ENABLE_LOGGING)
    errors.append(res) if res else None
    
    # Load Balancer
    load_balancer = Load_Balancer(circuit, components)
    res = load_balancer.balance_loads(battery_array)
    errors.append(res) if res else None
    
    #display_components(components)
    #display_netlist(circuit)
    has_error = len(errors) > 0
    if has_error:
        print(f"\n{BARF}Errors Detected During Circuit Setup:{BARE}")
        for error in errors:
            print(f"\t{error}")
        print()
            
    if not has_error or IGNORE_ERROR:
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

        mppt_result = {"voltage": {}, "current": {}}
        battery_result = {"voltage": {}, "current": {}}
        solar_result = {"voltage": {}, "current": {}}
        panel_result = {"voltage": {}, "current": {}}
        load_result = {"voltage": {}, "current": {}}
        
        # Node voltages
        for node_name, node in analysis.nodes.items():
            if "measured" in node_name:
                continue
            if "mppt" in node_name:
                voltage = float(node.as_ndarray()[0])
                mppt_result["voltage"][node_name] = voltage
            elif "battery" in node_name:
                voltage = float(node.as_ndarray()[0])
                battery_result["voltage"][node_name] = voltage
            elif "solar_array" in node_name:
                voltage = float(node.as_ndarray()[0])
                solar_result["voltage"][node_name] = voltage
            elif "panel" in node_name:
                voltage = float(node.as_ndarray()[0])
                panel_result["voltage"][node_name] = voltage
            elif "load" in node_name:
                voltage = float(node.as_ndarray()[0])
                load_result["voltage"][node_name] = voltage
            else:
                print(f"Node {node_name}: {float(node.as_ndarray()[0]):.2f} V")

        # Branch currents
        for branch_name, branch in analysis.branches.items():
            if branch_name.startswith("v"):
                branch_name = branch_name[1:]  #Remove 'v' prefix
                
            if "measured" in branch_name:
                continue
            if "mppt" in branch_name:
                current = float(branch.as_ndarray()[0])
                mppt_result["current"][branch_name] = current
            elif "battery" in branch_name:
                current = float(branch.as_ndarray()[0])
                battery_result["current"][branch_name] = current
            elif "solar_array" in branch_name:
                current = float(branch.as_ndarray()[0])
                solar_result["current"][branch_name] = current
            elif "panel" in branch_name:
                current = float(branch.as_ndarray()[0])
                panel_result["current"][branch_name] = current
            elif "load" in branch_name:
                current = float(branch.as_ndarray()[0])
                load_result["current"][branch_name] = current
            else:
                print(f"Branch {branch_name}: {float(branch.as_ndarray()[0]):.2f} A")
        
        print("\nSolar Array Results:")
        for key, values in solar_result.items():   
            print(f"  {key.capitalize()}:")
            for name, val in values.items():
                print(f"    {name}: {val:.2f}")   
        print("\nMPPT Results:")
        for key, values in mppt_result.items():
            print(f"  {key.capitalize()}:")
            for name, val in values.items():
                print(f"    {name}: {val:.2f}")
        print("\nBattery Results:")
        for key, values in battery_result.items():
            print(f"  {key.capitalize()}:")
            for name, val in values.items():
                print(f"    {name}: {val:.2f}")
        print("\nLoad Results:")
        for key, values in load_result.items():   
            print(f"  {key.capitalize()}:")
            for name, val in values.items():
                print(f"    {name}: {val:.2f}")
        '''print("\nPanel Results:")
        for key, values in panel_result.items():   
            print(f"  {key.capitalize()}:")
            for name, val in values.items():
                print(f"    {name}: {val:.2f}")'''

    except Exception as e:
        print("An error occurred during simulation:")
        print(e)
            
build_circuit_from_json(PATH)