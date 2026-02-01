from copy import deepcopy
import json
from sweep_graph_generation import generate_graph
from pyspice_simulator import begin_simulation
from circuit_constructor import build_circuit_from_json
from configurations.constants import *
from configurations.simulation_config import *

def start_voyage(circuit_config_loc: str, voyage_config_loc: str, save_path: str, ngspice_available: bool):
    with open(voyage_config_loc, 'r') as f:
        data = json.load(f)
        
    voyage_info = data['voyage_info']
    current_soc = data['initial_battery_soc']
    segments = data['segments']
    
    with open(circuit_config_loc, 'r') as f:
        circuit_data = json.load(f)
        

    battery_choice = circuit_data['battery_setup']['choice']
    battery_setup_info = circuit_data['battery_setup'][battery_choice]
    battery_capacity = battery_setup_info['capacity_ah'] * battery_setup_info['battery_in_parallel']
    battery_min_voltage = battery_setup_info['min_voltage']
    battery_max_voltage = battery_setup_info['max_voltage']
    
    current_capacity_Amin = (current_soc / 100) * battery_capacity * 60
    time_range_min = [0]
    results = []
    battery_capacity_list = [current_capacity_Amin]
    
    for segment_idx in range(len(segments)):
        segment = segments[segment_idx]
        
        duration_minutes = segment['duration_minutes']
        throttle_setting = segment['throttle']
        panel_power_setting = segment['solar_power']
        
        modifications = {}

        modifications['battery_voltage'] = estimate_battery_voltage(current_soc, battery_min_voltage, battery_max_voltage)
        modifications['panel_power_setting'] = panel_power_setting
        modifications['throttle_setting'] = throttle_setting

        if current_capacity_Amin <= 0:
            modifications['max_discharge_current'] = 0
        
        circuit, component_object, errors = build_circuit_from_json(circuit_config_loc=circuit_config_loc, modifications=modifications)
        analysis, result = begin_simulation(circuit, component_object, errors, ngspice_available)

        #if result[battery discharge] * voyage time > current capacity, 
        # calculate how huch time to reach 0, remainding time of the segment modify to 0 discharge
        discharge_current_Ah = -result["summary"]["data"][0]["current"]["total_battery_input_current"]
        # use summary res
        
        if current_capacity_Amin - (discharge_current_Ah * 60 * duration_minutes) <= 0: 
            minues_to_empty = (current_capacity_Amin / (discharge_current_Ah * 60))
            segments[segment_idx]["duration_minutes"] -= minues_to_empty
            
            current_capacity_Amin = 0
            current_soc = 0
            
            results.append(result)
            time_range_min.append(time_range_min[-1] + minues_to_empty)
            segment_idx -= 1
        else:
            current_capacity_Amin -= discharge_current_Ah * 60 * duration_minutes
            current_soc = (current_capacity_Amin / (battery_capacity * 60)) / 100
            
            results.append(result)
            time_range_min.append(time_range_min[-1] + duration_minutes)

        battery_capacity_list.append(min(battery_capacity, current_capacity_Amin))
    
    print(len(results))     #missing one. Add a blank result at start?
    print(len(time_range_min))
    print(len(battery_capacity_list))
    generate_graph(results=results, x_axis=time_range_min[:-1], x_label="Time (minutes)",
                   voltage_display_choice=['battery_result', 'load_result'],
                   current_display_choice=['battery_result', 'load_result'],
                   power_display_choice=['panel_result', 'load_result'],
                   battery_capacity=battery_capacity_list[:-1],
                   display_graph=False,
                   save_path=save_path)

    
     
    
    
    
    
    
    
    
    None
    
def real_time_digital_simulation(circuit_config_loc: str, ngspice_available: bool):
    None
    
def estimate_battery_voltage(soc, min_voltage, max_voltage):
    """Simple linear estimation"""
    return min_voltage + (max_voltage - min_voltage) * soc