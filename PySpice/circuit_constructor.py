import json

from configurations.constants import *
from PySpice.Spice.Netlist import Circuit
from configurations.constants import GROUNDING_RESISTANCE
from configurations.simulation_config import COMPONENT_LOGGING, SHOW_COMPONENTS, SHOW_NETLIST
from components.load_balancer import Load_Balancer
from components.load import Load
from components.battery_array import Battery_Array
from components.mppt import MPPT
from components.solar_panel_array import Solar_Array


def build_circuit_from_json(file_path: str, throttle_setting = None, panel_power_setting = None):
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
            if panel_power_setting is not None:
                config['panel_info']['power'] *= panel_power_setting
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

    POWER_FROM = mppt.get_terminal() if mppt_index > 0 else None
    POWER_TO = battery_array.get_terminal()
    
    circuit.V("total_mppt_output_current", POWER_FROM, POWER_TO, GROUNDING_RESISTANCE)

    # Load/Motor
    index = 0
    for key in input_data["load_setup"].keys():
        if key == "description":
            continue
        load_name = f"{index}:{key}_load"
        
        if throttle_setting is not None:
            if type(throttle_setting) == list:
                input_data['load_setup'][key]['throttle'] = throttle_setting[index]
            else:
                input_data['load_setup'][key]['throttle'] = throttle_setting
                
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

    if SHOW_COMPONENTS:
        display_components(components)
    if SHOW_NETLIST:
        display_netlist(circuit)

    
    return circuit, component_object, errors


def display_components(components):
    print("\nComponents in Circuit:")
    for comp_type, comp_list in components.items():
        print(f"{comp_type.capitalize()}: {len(comp_list)}")
        for comp in comp_list:
            print(f"  - {comp}")


def display_netlist(circuit):
    print("\nCircuit Netlist:")
    print(circuit)