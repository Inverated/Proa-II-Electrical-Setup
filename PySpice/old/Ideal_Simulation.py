from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
from PySpice.Spice.NgSpice.Shared import NgSpiceShared

NGSPICE_AVAILABLE = True

try:
    NgSpiceShared.new_instance()
except Exception as e:
    NGSPICE_AVAILABLE = False
    print("Follow steps indicated in readme.md to install NgSpice.")

'''
============================================================
Parameters
============================================================
'''
# General
GROUNDING_RESISTANCE = 1e-6
WIRE_RESISTANCE = 0.01
BARF = "="*50 + "\n"
BARE = "\n" +"="*50
RAWSPICE_ITERATIONS = 1e6
MPPT_PANEL_ARRAY_COUNT = 1

# Solar panel
PANEL_POWER = 455
PANEL_VOLTAGE = 40
PANEL_CURRENT = PANEL_POWER / PANEL_VOLTAGE
PANEL_INTERNAL_R = PANEL_VOLTAGE / PANEL_CURRENT

PANEL_IN_SERIES = 2
PANEL_IN_PARALLEL = 3
PANEL_ARRAY_TOTAL_VOLTAGE = PANEL_IN_SERIES * PANEL_VOLTAGE
PANEL_ARRAY_TOTAL_CURRENT = PANEL_IN_PARALLEL * PANEL_CURRENT
PANEL_ARRAY_TOTAL_POWER = PANEL_ARRAY_TOTAL_VOLTAGE * PANEL_ARRAY_TOTAL_CURRENT

# Battery
BATTERY_VOLTAGE = 25.9
BATTERY_IN_SERIES = 2
BATTERY_IN_PARALLEL = 1
BATTERY_CAPACITY_AH = 50
BATTERY_MAX_CHARGE_CURRENT = 100
BATTERY_MAX_DISCHARGE_CURRENT = 50
BATTERY_TOTAL_VOLTAGE = BATTERY_IN_SERIES * BATTERY_VOLTAGE

# Load
MOTOR_TOTAL_POWER = 4000
MOTOR_VOLTAGE = 48
MOTOR_CURRENT = MOTOR_TOTAL_POWER / MOTOR_VOLTAGE

MOTOR_CONTROLLER = 0.9
MOTOR_POWER_DEMAND = MOTOR_TOTAL_POWER * MOTOR_CONTROLLER if MOTOR_CONTROLLER > 0.0 else GROUNDING_RESISTANCE
MOTOR_CURRENT_DEMAND = MOTOR_POWER_DEMAND / BATTERY_TOTAL_VOLTAGE
MOTOR_RESISTANCE = MOTOR_VOLTAGE / MOTOR_CURRENT_DEMAND

# MPPT
MPPT_MAX_OUTPUT_CURRENT = 45
MPPT_INPUT_VOLTAGE = PANEL_ARRAY_TOTAL_VOLTAGE
MPPT_MAX_INPUT_POWER = PANEL_ARRAY_TOTAL_POWER
MPPT_OUTPUT_BUFFER_VOLTAGE = 5
MPPT_OUTPUT_VOLTAGE = BATTERY_TOTAL_VOLTAGE + MPPT_OUTPUT_BUFFER_VOLTAGE
MPPT_EFFICIENCY = 0.95
MPPT_OUTPUT_POWER = MPPT_MAX_INPUT_POWER * MPPT_EFFICIENCY
MPPT_OUTPUT_CURRENT = MPPT_OUTPUT_POWER / MPPT_OUTPUT_VOLTAGE

# 2 Limitation: MPPT output current & battery charge current
MPPT_INPUT_CURRENT = MPPT_OUTPUT_POWER / PANEL_ARRAY_TOTAL_VOLTAGE
MPPT_INPUT_RESISTANCE = MPPT_INPUT_VOLTAGE / MPPT_INPUT_CURRENT



if __name__ == "__main__" and NGSPICE_AVAILABLE:
    circuit = Circuit("Solar Power System Test")
    
    components = {"panel": [], "battery": [], "load": [], "wire": []}
    
    for arr_no in range(MPPT_PANEL_ARRAY_COUNT):
        
        # Solar Array
        for p in range(PANEL_IN_PARALLEL):
            panel_row = []
            for s in range(PANEL_IN_SERIES):
                panel_name = f"{arr_no}_panel_{p}_{s}"
                panel_row.append(panel_name)
                
                panel_pos = f"{panel_name}_positive"
                panel_neg = f"{panel_name}_negative"
                
                # Current source: neg -> pos
                circuit.I(panel_name, panel_neg, panel_pos, PANEL_CURRENT)
                
                # Ground all panel, else panel can only deliver voltage by a factor of 40 for some reason
                circuit.R(f"{panel_name}_leak_to_gnd", panel_neg, circuit.gnd, GROUNDING_RESISTANCE)

                if s != 0:
                    prev_panel_name = f"{arr_no}_panel_{p}_{s-1}"
                    # Internal resistance
                    circuit.R(f"{panel_name}_internal", panel_neg, f"{prev_panel_name}_positive", PANEL_INTERNAL_R)

            components["panel"].append(panel_row)
        
        for index, row in enumerate(components["panel"]):
            solar_row_end = row[-1]
            positive_node = f"{solar_row_end}_positive"
            panel_wire = f"{arr_no}_panel_wire_{index}"
            circuit.R(panel_wire, positive_node, f"{arr_no}_solar_array_output", WIRE_RESISTANCE)
            components["wire"].append(panel_wire)
            # Small resistance to model wiring losses
        
        print(f"""
{BARF}Solar Array Setup {arr_no + 1}{BARE}
Configuration: {PANEL_IN_SERIES} in series, {PANEL_IN_PARALLEL} in parallel
Total Voltage: {PANEL_ARRAY_TOTAL_VOLTAGE} V
Total Current: {PANEL_ARRAY_TOTAL_CURRENT} A
Total Power: {PANEL_ARRAY_TOTAL_POWER} W
            """)
        
        #MPPT
        circuit.V(f"{arr_no}_solar_array_output_current", f"{arr_no}_solar_array_output", f"{arr_no}_solar_array_output_measured", GROUNDING_RESISTANCE)
        
        circuit.R(f"{arr_no}_mppt_input_load", 
                 f"{arr_no}_solar_array_output_measured", circuit.gnd, 
                 MPPT_INPUT_RESISTANCE)

        # Regulate output current to calculated amount
        circuit.raw_spice += f"""B{arr_no}_mppt_i_reg 0 {arr_no}_mppt_out I = min({MPPT_MAX_OUTPUT_CURRENT}, {MPPT_OUTPUT_CURRENT})\n"""
        

        circuit.V(f"{arr_no}_mppt_output_current", f"{arr_no}_mppt_out", f"{arr_no}_mppt_output_measured", GROUNDING_RESISTANCE)
        # Connect MPPT output to DC bus
        circuit.R(f"{arr_no}_mppt_out_wire", f"{arr_no}_mppt_output_measured", "power_source", WIRE_RESISTANCE)
        #dc_bus is shared positive node for battery and load
        

        print(f"""
{BARF}MPPT Setup {arr_no + 1}{BARE}
Input Voltage: {MPPT_INPUT_VOLTAGE} V
Output Voltage: {MPPT_OUTPUT_VOLTAGE} V
Max Power: {MPPT_MAX_INPUT_POWER} W
Output Power: {MPPT_OUTPUT_POWER:.2f} W
Output Current: {MPPT_OUTPUT_CURRENT:.2f} A
    """)

    circuit.V("total_mppt_output", "power_source", "dc_bus", GROUNDING_RESISTANCE)
    
    # Battery
    for p in range(BATTERY_IN_PARALLEL):
        battery_row = []
        for s in range(BATTERY_IN_SERIES):
            battery_name = f"battery_{p}_{s}"
            battery_row.append(battery_name)
            
            battery_pos = f"{battery_name}_positive"
            battery_neg = f"{battery_name}_negative"
            
            circuit.V(battery_name, battery_pos, battery_neg, BATTERY_VOLTAGE)
            if s == 0:
                circuit.R(f"{battery_name}_grounding", battery_neg, circuit.gnd, GROUNDING_RESISTANCE)
            else:
                prev_battery_name = f"battery_{p}_{s-1}"
                circuit.R(f"{battery_name}_internal", battery_neg, f"{prev_battery_name}_positive", WIRE_RESISTANCE)
            components["battery"].append(battery_row)
            
    circuit.V("battery_input_current", "dc_bus", "battery_input_measured", GROUNDING_RESISTANCE)
    
    for index, row in enumerate(components["battery"]):
        battery_row_end = row[-1]
        positive_node = f"{battery_row_end}_positive"
        battery_wire = f"battery_wire_{index}"
        circuit.R(battery_wire, positive_node, "battery_input_measured", WIRE_RESISTANCE)  
        components["wire"].append(battery_wire)

        
    print(f"""
{BARF}Battery Setup{BARE}
Configuration: {BATTERY_IN_SERIES} in series, {BATTERY_IN_PARALLEL} in parallel
Total Voltage: {BATTERY_TOTAL_VOLTAGE} V
          """)    
    
    #'''
    # Load    
    # Balancing load to limit battery charge current
    # Note: No idea how did this worked. PySpice might have allowed cyclical calculation such that:
    # I(Vbattery_input_current)-{BATTERY_MAX_CHARGE_CURRENT} repeats until it tends to the max charge current 
    circuit.V("balancing_load_current", "dc_bus", "balancing_load_in", GROUNDING_RESISTANCE) 
    circuit.raw_spice += f"Bbalancing_load balancing_load_in 0 I = I(Vbattery_input_current)>{BATTERY_MAX_CHARGE_CURRENT} ? (I(Vbattery_input_current)-{BATTERY_MAX_CHARGE_CURRENT})*{RAWSPICE_ITERATIONS} : 0\n"
    
    circuit.V("motor_load_source", "dc_bus", "motor_load_negative", GROUNDING_RESISTANCE)
    #circuit.R("motor_load", "motor_load_negative", circuit.gnd, MOTOR_RESISTANCE)
    circuit.raw_spice += f"Bmotor_load motor_load_negative 0 I = I(Vbattery_input_current)<-{BATTERY_MAX_DISCHARGE_CURRENT} ? {MOTOR_CURRENT_DEMAND}+(I(Vbattery_input_current)+{BATTERY_MAX_DISCHARGE_CURRENT})*{RAWSPICE_ITERATIONS} : {MOTOR_CURRENT_DEMAND}\n"
    components["load"].append("motor_load")
    
    circuit.V("motor_load_source2", "dc_bus", "motor_load_negative2", GROUNDING_RESISTANCE)
    circuit.raw_spice += f"Bmotor_load2 motor_load_negative2 0 I = I(Vbattery_input_current)<-{BATTERY_MAX_DISCHARGE_CURRENT} ? {MOTOR_CURRENT_DEMAND}+(I(Vbattery_input_current)+{BATTERY_MAX_DISCHARGE_CURRENT})*{RAWSPICE_ITERATIONS} : {MOTOR_CURRENT_DEMAND}\n"
    
    print(f"""
{BARF}Load Setup (Before balancing){BARE}
Motor Power Demand: {MOTOR_POWER_DEMAND} W
Motor Current Demand: {MOTOR_CURRENT_DEMAND:.2f} A
Motor Resistance: {MOTOR_RESISTANCE:.2f} Ohm
          """)
    #'''
    
    
    # Simulation
    print(BARF)
    print("Components in Circuit:")
    for comp_type, comp_list in components.items():
        print(comp_type.capitalize() + ":")
        for each in comp_list:
            print(f"\t{each}")
        
        
    print(f"""
{BARF}Starting Simulation{BARE}
Assuming ideal condition at motor load of {MOTOR_POWER_DEMAND} W ({MOTOR_CONTROLLER*100:.1f}% throttle)
""")
    #print("Circuit Netlist:")
    #print(circuit)
    #print()
    
    try:
        simulator = circuit.simulator(temperature=25, nominal_temperature=25)
        analysis = simulator.operating_point()

        print("Simulation Results:")

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