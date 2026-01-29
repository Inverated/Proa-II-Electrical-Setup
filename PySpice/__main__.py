from pyspice_simulator import begin_simulation
from result_saver import save_to_file
from configurations.constants import *
from circuit_constructor import build_circuit_from_json
from PySpice.Spice.NgSpice.Shared import NgSpiceShared
from sweep_graph_generation import generate_graph


# 0: operating_point / 1:sweep throttle / 2: sweep panel power / 3: Voyage mode / 4: RTDS mode
SIMULATION_TYPE     = 1

ngspice_available = True

try:
    NgSpiceShared.new_instance()
except Exception as e:
    ngspice_available = False
    print("Follow steps indicated in readme.md to install NgSpice.")


if __name__ == "__main__":
    if SIMULATION_TYPE == 0:
        circuit, component_object, errors = build_circuit_from_json(CONFIG_FILE)
        analysis, result = begin_simulation(circuit, component_object, errors)

    else:
        if SIMULATION_TYPE == 1:
            throttle_range = [i/SWEEP_INTERVAL_COUNT for i in range(0, SWEEP_INTERVAL_COUNT+1, 1)]
            results = []
            for throttle in throttle_range:
                if SIMULATION_LOGGING:
                    print(f"\n{BARF}Starting Simulation with Throttle Setting: {throttle*100:.2f}%{BARE}")
                circuit, component_object, errors = build_circuit_from_json(CONFIG_FILE, throttle)
                analysis, result = begin_simulation(circuit, component_object, errors, ngspice_available)
                results.append(result)
            
            generate_graph(results, throttle_range, x_label="Throttle Input (%)",
                    voltage_display_choice=['mppt_result', 'load_result'],
                    current_display_choice=['mppt_result', 'solar_result', 'load_result', 'battery_result'],
                    power_display_choice=['load_result', 'battery_result'],
                    display_graph=SHOW_SWEEP_PLOT,
                    save_path=SWEEP_SAVE_PATH if SAVE_OUTPUT else None)
        elif SIMULATION_TYPE == 2:
            panel_power_range = [i/SWEEP_INTERVAL_COUNT for i in range(SWEEP_INTERVAL_COUNT, 0, -1)]
            results = []
            for panel_power in panel_power_range:
                if SIMULATION_LOGGING:
                    print(f"\n{BARF}Starting Simulation with Panel Power Setting: {panel_power*100:.2f}%{BARE}")
                circuit, component_object, errors = build_circuit_from_json(CONFIG_FILE, panel_power_setting=panel_power)
                analysis, result = begin_simulation(circuit, component_object, errors, ngspice_available)
                
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
                    save_path=SWEEP_SAVE_PATH if SAVE_OUTPUT else None)

    if START_SIMULATION and SAVE_OUTPUT:
        save_to_file(result)
        
        
