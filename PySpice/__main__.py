import datetime
import json
import os

from PySpice.Spice.Netlist import Circuit
from PySpice.Spice.NgSpice.Shared import NgSpiceShared
from result_checker import cross_check_result
from parse_result import parse_simulation_result
from configurations.constants import BARF, BARE, GROUNDING_RESISTANCE
from components.load_balancer import Load_Balancer
from components.load import Load
from components.battery_array import Battery_Array
from components.mppt import MPPT
from components.solar_panel_array import Solar_Array

path = os.getcwd()
CONFIG_PATH         = os.path.join(path, 'pyspice/configurations/circuit_setup.json')
SAVE_FILE           = os.path.join(path, 'pyspice/result/simulation_results.json')
SAVE_OUTPUT         = 0

COMPONENT_LOGGING   = 0
SHOW_COMPONENTS     = 0
SHOW_PANELS         = 0
SHOW_NETLIST        = 0

IGNORE_ERROR        = 1
START_SIMULATION    = 1
SIMULATION_LOGGING  = 1

SHOW_ERRORS         = 1
SHOW_WARNINGS       = 1

"================== NgSpice Initialization ================"
NGSPICE_AVAILABLE = True

try:
    NgSpiceShared.new_instance()
except Exception as e:
    NGSPICE_AVAILABLE = False
    print("Follow steps indicated in readme.md to install NgSpice.")


"================== Construct circuit ================="

def build_circuit_from_json(file_path: str):
    circuit = Circuit("Solar_Panel-Mppt-Battery-Motor Circuit Thingy")
    components = {
        "panel": [],
        "battery": [],
        "load": [],
        "wire": [],
        "mppt": []
    }
    
    with open(file_path, 'r') as f:
        input_data = json.load(f)

    component_object = {}
    errors = []
    
    # Battery Array
    battery_array = input_data['battery_setup']
    battery_choice = battery_array['choice']
    battery_config = battery_array[battery_choice]
    battery_array = Battery_Array(circuit, components, **battery_config)
    err = battery_array.create_battery_array(log=COMPONENT_LOGGING)
    
    component_object["battery_array"] = battery_array
    errors.append(err) if err else None

    # MPPT Array
    mppt_array = input_data['mppt_panel_setup']
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
            err = mppt.setup_mppt(mppt_index, solar_array,
                                  battery_array, log=COMPONENT_LOGGING)
            
            errors.append(err) if err else None
            component_object["mppt"] = component_object.get("mppt", []) + [mppt]
            component_object["solar_array"] = component_object.get("solar_array", []) + [solar_array]
            mppt_index += 1

    POWER_FROM = mppt.get_terminal()
    POWER_TO = battery_array.get_terminal()
    
    circuit.V("total_mppt_output_current", POWER_FROM, POWER_TO, GROUNDING_RESISTANCE)

    # Load/Motor
    index = 0
    for key in input_data["load_setup"].keys():
        if key == "description":
            continue
        load_name = f"{index}:{key}_load"
        load = Load(circuit, components, load_name=load_name, **input_data['load_setup'][key])
        err = load.setup_load(battery_array, log=COMPONENT_LOGGING)
        
        component_object["load"] = component_object.get("load", []) + [load]
        errors.append(err) if err else None
        index += 1  
        
    # Load Balancer (One is enough to restrict battery output)
    load_balancer = Load_Balancer(circuit, components)
    err = load_balancer.balance_loads(battery_array)
    
    component_object["load_balancer"] = load_balancer
    errors.append(err) if err else None


    "================== Finish adding components ================="
    if SHOW_COMPONENTS:
        display_components(components)
    if SHOW_NETLIST:
        display_netlist(circuit)

    simulation_started = False
    
    # Errors cannot be ignored for actual run
    has_error = len(errors) > 0
    if not has_error or IGNORE_ERROR:
        if START_SIMULATION:
            simulation_started = True
            meta_data = {"name": circuit.title, "configuration_file": CONFIG_PATH, "date": datetime.datetime.now().isoformat()}
            
            analysis, result, struc = begin_simulation(meta_data, circuit, errors)
            parse_simulation_result(analysis, result, struc, SIMULATION_LOGGING, SHOW_PANELS)
            cross_check_result(component_object, result)
            
            if SAVE_OUTPUT:
                save_to_file(result)
    else:
        if SHOW_ERRORS and START_SIMULATION:
            print(f"{BARF}Simulation Aborted Due to Errors in Circuit Setup.{BARE}")
    
    if has_error and SHOW_ERRORS:
        print(f"\n{BARF}Errors Detected During Circuit Setup:{BARE}")
        for error in errors:
            print(f"\t{error}")
        print()
    
    # Warning are components with limited output but might still work
    if simulation_started and result["warning"]["array_count"] > 0 and SHOW_WARNINGS:
        print(f"\n{BARF}Warnings Detected During Simulation:{BARE}")
        for warning in result["warning"]["data"]:
            print(f"\t{warning}")
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


def begin_simulation(meta_data, circuit, errors=[]):
    struc = '{"array_index": 0, "voltage": {}, "current": {}}'
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
    
    load_balancer = {
        "keyword": "balancing_load",
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
        "info": meta_data,
        "error": error,
        "warning": warning,
        "summary": summary,
        "mppt_result": mppt_result,
        "battery_result": battery_result,
        "solar_result": solar_result,
        "panel_result": panel_result,
        "load_balancer": load_balancer,
        "load_result": load_result,
    }
    
    if not NGSPICE_AVAILABLE:
        err = "NgSpice is not available. Simulation cannot proceed."
        result["error"]["data"].append(err)
        return None, result, struc
    
    try:
        simulator = circuit.simulator(temperature=25, nominal_temperature=25)
        analysis = simulator.operating_point()
    except Exception as _:
        result["error"]["data"].append("Error has occured during simulation. Check console for details.")
        return None, result, struc
    
    print(f"\n{BARF}Simulation Completed Successfully.{BARE}")
    
    return analysis, result, struc


def save_to_file(result):
    json_result = json.dumps(result, indent=4)
    
    with open(SAVE_FILE, 'w') as f:
        f.write(json_result)
        print(f"\n{BARF}Simulation results saved to {SAVE_FILE}{BARE}")

if __name__ == "__main__":
    build_circuit_from_json(CONFIG_PATH)