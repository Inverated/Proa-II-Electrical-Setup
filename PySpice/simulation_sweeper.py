from sweep_graph_generation import generate_graph
from pyspice_simulator import begin_simulation
from circuit_constructor import build_circuit_from_json
from configurations.constants import *
from configurations.simulation_config import *


def sweep_throttle(circuit_config_loc, save_path, ngspice_available):
    """Sweep the throttle from 0% to 100% in defined intervals and run simulations."""
    
    throttle_range = [i / SWEEP_INTERVAL_COUNT for i in range(0, SWEEP_INTERVAL_COUNT + 1, 1)]
    results = []
    for throttle in throttle_range:
        if SIMULATION_LOGGING:
            print(f"\n{BARF}Starting Simulation with Throttle Setting: {throttle*100:.2f}%{BARE}")
            
        circuit, component_object, errors = build_circuit_from_json(circuit_config_loc, {'throttle_setting': throttle})
        analysis, result = begin_simulation(circuit, component_object, errors, ngspice_available)
        results.append(result)
    
    generate_graph(results, throttle_range, x_label="Throttle Input (%)",
            voltage_display_choice=['mppt_result', 'load_result'],
            current_display_choice=['mppt_result', 'solar_result', 'load_result', 'battery_result'],
            power_display_choice=['load_result', 'battery_result'],
            display_graph=SHOW_SWEEP_PLOT,
            save_path=save_path if SAVE_OUTPUT else None)
    
def sweep_panel_power(circuit_config_loc, save_path, ngspice_available):
    """Sweep the panel power from 100% to 0% in defined intervals and run simulations."""

    panel_power_range = [i / SWEEP_INTERVAL_COUNT for i in range(SWEEP_INTERVAL_COUNT, 0, -1)]
    results = []
    for panel_power in panel_power_range:
        if SIMULATION_LOGGING:
            print(f"\n{BARF}Starting Simulation with Panel Power Setting: {panel_power*100:.2f}%{BARE}")
            
        circuit, component_object, errors = build_circuit_from_json(circuit_config_loc, {'panel_power_setting': panel_power})
        analysis, result = begin_simulation(circuit, component_object, errors, ngspice_available)
        
        # If the simulation fails at a certain panel power, stop the sweep
        if analysis:
            results.append(result)
        else:
            panel_power_range = panel_power_range[:panel_power_range.index(panel_power)]
            break
        
    generate_graph(results, panel_power_range, x_label="Panel Power (%)",
            voltage_display_choice=['mppt_result', 'load_result'],
            current_display_choice=['mppt_result', 'solar_result', 'load_result', 'battery_result'],
            power_display_choice=['load_result', 'battery_result', 'solar_result'],
            display_graph=SHOW_SWEEP_PLOT,
            save_path=save_path if SAVE_OUTPUT else None)