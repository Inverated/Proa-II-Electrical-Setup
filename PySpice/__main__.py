import json

from PySpice.Spice.Netlist import Circuit
# from PySpice.Unit import *
from PySpice.Spice.NgSpice.Shared import NgSpiceShared
from configurations.constants import BARF, BARE, GROUNDING_RESISTANCE
from components.load_balancer import Load_Balancer
from components.load import Load
from components.battery_array import Battery_Array
from components.mppt import MPPT
from components.solar_panel_array import Solar_Array

PATH = 'pyspice/configurations/circuit_setup.json'
ENABLE_LOGGING = 0
SHOW_COMPONENTS = 0
SHOW_NETLIST = 0
IGNORE_ERROR = 1
START_SIMULATION = 1


NGSPICE_AVAILABLE = True

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
            solar_array = Solar_Array(
                circuit, components, **config['panel_info'])
            mppt = MPPT(circuit, components, **config['mppt_info'])

            solar_array.create_panels(mppt_index, log=ENABLE_LOGGING)
            res = mppt.setup_mppt(mppt_index, solar_array,
                                  battery_array, log=ENABLE_LOGGING)
            errors.append(res) if res else None
            mppt_index += 1

    POWER_FROM = mppt.get_terminal()
    POWER_TO = battery_array.get_terminal()
    
    circuit.V("total_mppt_output_current", POWER_FROM, POWER_TO, GROUNDING_RESISTANCE)

    # Load/Motor
    motor = Load(circuit, components, **data['load_setup'])
    res = motor.setup_load(battery_array, throttle=1, log=ENABLE_LOGGING)
    errors.append(res) if res else None

    # Load Balancer
    load_balancer = Load_Balancer(circuit, components)
    res = load_balancer.balance_loads(battery_array)
    errors.append(res) if res else None

    if SHOW_COMPONENTS:
        display_components(components)
    if SHOW_NETLIST:
        display_netlist(circuit)

    has_error = len(errors) > 0

    if not has_error or IGNORE_ERROR:
        if START_SIMULATION:
            begin_simulation()
    else:
        print(f"{BARF}Simulation Aborted Due to Errors in Circuit Setup.{BARE}")
    
    if has_error:
        print(f"\n{BARF}Errors Detected During Circuit Setup:{BARE}")
        for error in errors:
            print(f"\t{error}")
        print()


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
    except Exception as e:
        print("An error occurred during simulation:")
        print(e)
        return

    print(f"{BARF}Simulation Results:{BARE}")

    struc = '{"voltage": {}, "current": {}}'
    mppt_result = {
        "keyword": "mppt",
        "array_count": 0,
        "data": [],
    }
    solar_result = {
        "keyword": "solar_array",
        "array_count": 0,
        "data": [],
    }
    panel_result = {
        "keyword": "panel",
        "array_count": 0,
        "data": [],
    }
    
    battery_result = {
        "keyword": "battery",
        "array_count": 0,
        "data": [],
    }
    load_result = {
        "keyword": "load",
        "array_count": 0,
        "data": [],
    }
    
    others = {
        "keyword": "total",
        "array_count": 0,
        "data": [],
    }
    
    result = {
        "others": others,
        "mppt_result": mppt_result,
        "battery_result": battery_result,
        "solar_result": solar_result,
        "panel_result": panel_result,
        "load_result": load_result,
    }

    # Node voltages
    for node_name, node in analysis.nodes.items():
        if "measured" in node_name:
            continue
        matched = False
        for dic in result.values():
            if matched:
                break
            if dic["keyword"] in node_name:
                matched = True
                
                prefix = node_name[0:node_name.index("_")]
                if prefix.isdigit():
                    prefix = int(prefix)
                    if prefix > len(dic["data"]):
                        dic["data"].extend(eval(struc) for _ in range(prefix - len(dic["data"]) + 1))
                        dic["array_count"] = len(dic["data"])
                    dic["data"][prefix]["voltage"][node_name.lstrip(f"{prefix}_")] = float(node.as_ndarray()[0])
                else:
                    if len(dic["data"]) == 0:
                        dic["data"].append(eval(struc))
                        dic["array_count"] += 1
                    dic["data"][0]["voltage"][node_name] = float(node.as_ndarray()[0])
        if not matched:
            print(f"Node {node_name}: {float(node.as_ndarray()[0]):.2f} V")

    # Branch currents
    for branch_name, branch in analysis.branches.items():
        if branch_name.startswith("v"):
            branch_name = branch_name[1:]  # Remove 'v' prefix
        
        if "measured" in branch_name:
                continue
        matched = False
        for dic in result.values():
            if matched:
                break
            if dic["keyword"] in branch_name:
                matched = True
                
                prefix = branch_name[0:branch_name.index("_")]
                if prefix.isdigit():
                    prefix = int(prefix)
                    # Add to data list at index i of i_name
                    if prefix > len(dic["data"]):
                        dic["data"].extend(eval(struc) for _ in range(prefix - len(dic["data"]) + 1))
                        dic["array_count"] = len(dic["data"])
                    dic["data"][prefix]["current"][branch_name.lstrip(f"{prefix}_")] = float(branch.as_ndarray()[0])
                else:
                    if len(dic["data"]) == 0:
                        dic["data"].append(eval(struc))
                        dic["array_count"] += 1
                    dic["data"][0]["current"][branch_name] = float(branch.as_ndarray()[0])
        if not matched:
            print(f"Branch {branch_name}: {float(branch.as_ndarray()[0]):.2f} A")

    for key in result.keys():
        if key == "panel_result":
            continue  # Skip panels
        
        count = result[key]['array_count']
        print(f"\n{result[key]['keyword'].capitalize()} Results (Count: {count}):")
        for index, data in enumerate(result[key]['data']):
            print(f"{result[key]['keyword'].capitalize()} {index}:") if count > 1 else None
            
            print("\t"*min(1, count) + "Voltages:")
            for node, voltage in data['voltage'].items():
                print("\t"*min(1, count) + f"\t{node}: {voltage:.2f} V")
            print("\t"*min(1, count) + "Currents:")
            for branch, current in data['current'].items():
                print("\t"*min(1, count) + f"\t{branch}: {current:.2f} A")
        print(BARE)


if __name__ == "__main__":
    build_circuit_from_json(PATH)