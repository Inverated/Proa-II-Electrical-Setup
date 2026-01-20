import json

# from PySpice.Unit import *
from PySpice.Spice.Netlist import Circuit
from PySpice.Spice.NgSpice.Shared import NgSpiceShared
from parse_result import parse_simulation_result
from configurations.constants import BARF, BARE, GROUNDING_RESISTANCE
from components.load_balancer import Load_Balancer
from components.load import Load
from components.battery_array import Battery_Array
from components.mppt import MPPT
from components.solar_panel_array import Solar_Array

CONFIG_PATH = 'pyspice/configurations/circuit_setup.json'
SAVE_FILE = 'pyspice/result/simulation_results.json'
COMPONENT_LOGGING = 0
SHOW_COMPONENTS = 0
SHOW_NETLIST = 0
IGNORE_ERROR = 1
START_SIMULATION = 1
SIMULATION_LOGGING = 1


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
    res = battery_array.create_battery_array(log=COMPONENT_LOGGING)
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

            solar_array.create_panels(mppt_index, log=COMPONENT_LOGGING)
            res = mppt.setup_mppt(mppt_index, solar_array,
                                  battery_array, log=COMPONENT_LOGGING)
            errors.append(res) if res else None
            mppt_index += 1

    POWER_FROM = mppt.get_terminal()
    POWER_TO = battery_array.get_terminal()
    
    circuit.V("total_mppt_output_current", POWER_FROM, POWER_TO, GROUNDING_RESISTANCE)

    # Load/Motor
    for index, key in enumerate(data["load_setup"].keys()):
        if key == "description":
            continue
        load_name = key + f"_load_{index}"
        motor = Load(circuit, components, load_name=load_name, **data['load_setup'][key])
        res = motor.setup_load(battery_array, log=COMPONENT_LOGGING)
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
            begin_simulation(errors)
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


def begin_simulation(errors=[]):
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
    
    summary = {
        "keyword": "total",
        "array_count": 0,
        "data": [],
    }
    
    error = {
        "keyword": "error",
        "array_count": len(errors),
        "data": errors,
    }
    
    warning = {
        "keyword": "warning",
        "array_count": 0,
        "data": [],
    }
    
    result = {
        "error": error,
        "warning": warning,
        "summary": summary,
        "mppt_result": mppt_result,
        "battery_result": battery_result,
        "solar_result": solar_result,
        "panel_result": panel_result,
        "load_result": load_result,
    }
    
    if not NGSPICE_AVAILABLE:
        err = "NgSpice is not available. Simulation cannot proceed."
        print(err)
        result["error"]["data"].append(err)
        save_to_file(result)
        return
    
    try:
        simulator = circuit.simulator(temperature=25, nominal_temperature=25)
        analysis = simulator.operating_point()
    except Exception as _:
        print("An error occurred during simulation:")
        result["error"]["data"].append("Error has occured during simulation. Check console for details.")
        save_to_file(result)
        return

    parse_simulation_result(analysis, result, struc, SIMULATION_LOGGING)
    
    save_to_file(result)
    
    return None


def save_to_file(result):
    json_result = json.dumps(result, indent=4)
    
    with open(SAVE_FILE, 'w') as f:
        f.write(json_result)
        print(f"\n{BARF}Simulation results saved to {SAVE_FILE}{BARE}")

if __name__ == "__main__":
    build_circuit_from_json(CONFIG_PATH)