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
# Solar panel
PANEL_POWER = 455
PANEL_VOLTAGE = 40
PANEL_CURRENT = PANEL_POWER / PANEL_VOLTAGE

PANEL_IN_SERIES = 2
PANEL_IN_PARALLEL = 3
PANEL_ARRAY_TOTAL_VOLTAGE = PANEL_IN_SERIES * PANEL_VOLTAGE
PANEL_ARRAY_TOTAL_CURRENT = PANEL_IN_PARALLEL * PANEL_CURRENT
PANEL_ARRAY_TOTAL_POWER = PANEL_ARRAY_TOTAL_VOLTAGE * PANEL_ARRAY_TOTAL_CURRENT
PANEL_ARRAY_INTERNAL_RESISTANCE = PANEL_ARRAY_TOTAL_VOLTAGE / PANEL_ARRAY_TOTAL_CURRENT

# Battery
BATTERY_VOLTAGE = 24
BATTERY_IN_SERIES = 2
BATTERY_IN_PARALLEL = 2
BATTERY_CAPACITY_AH = 50
BATTERY_TOTAL_VOLTAGE = BATTERY_IN_SERIES * BATTERY_VOLTAGE

# Load
MOTOR_TOTAL_POWER = 4000
MOTOR_VOLTAGE = 48
MOTOR_CURRENT = MOTOR_TOTAL_POWER / MOTOR_VOLTAGE

MOTOR_CONTROLLER = 0.6
MOTOR_POWER_DEMAND = MOTOR_TOTAL_POWER * MOTOR_CONTROLLER
MOTOR_CURRENT_DEMAND = MOTOR_POWER_DEMAND / MOTOR_VOLTAGE
MOTOR_RESISTANCE = MOTOR_VOLTAGE / MOTOR_CURRENT_DEMAND

# MPPT
MPPT_INPUT_VOLTAGE = PANEL_ARRAY_TOTAL_VOLTAGE
MPPT_OUTPUT_VOLTAGE = BATTERY_TOTAL_VOLTAGE
MPPT_MAX_POWER = PANEL_ARRAY_TOTAL_POWER
MPPT_EFFICIENCY = 0.95
MPPT_OUTPUT_POWER = MPPT_MAX_POWER * MPPT_EFFICIENCY
MPPT_OUTPUT_CURRENT = MPPT_OUTPUT_POWER / MPPT_OUTPUT_VOLTAGE
MPPT_INPUT_CURRENT = MPPT_OUTPUT_POWER / PANEL_ARRAY_TOTAL_VOLTAGE

# Power Array
MPPT_PANEL_ARRAY_COUNT = 2

BARF = "="*50 + "\n"
BARE = "\n" +"="*50

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
                
                if s == 0: # First in series connect to gnd
                    circuit.I(panel_name, circuit.gnd, f"{panel_name}_positive", PANEL_CURRENT)
                    # Current is pushed out of the panel, into the circuit
                    # circuit.I(name, node_from, node_to, I)
                    # node_from is where current comes from
                else:
                    prev_panel_name = f"{arr_no}_panel_{p}_{s-1}"
                    circuit.I(panel_name, f"{prev_panel_name}_positive", f"{panel_name}_positive", PANEL_CURRENT)

            components["panel"].append(panel_row)
        
        for index, row in enumerate(components["panel"]):
            solar_row_end = row[-1]
            positive_node = f"{solar_row_end}_positive"
            panel_wire = f"{arr_no}_panel_wire_{index}"
            circuit.R(panel_wire, positive_node, "solar_array_output", 0.01)
            components["wire"].append(panel_wire)
            # Small resistance to model wiring losses
        
        total_panel_internal_resistance = PANEL_ARRAY_INTERNAL_RESISTANCE
        circuit.R(f"{arr_no}_panel_internal_resistance", "solar_array_output", circuit.gnd, total_panel_internal_resistance)
        
        print(f"""
{BARF}Solar Array Setup {arr_no + 1}{BARE}
Configuration: {PANEL_IN_SERIES} in series, {PANEL_IN_PARALLEL} in parallel
Total Voltage: {PANEL_ARRAY_TOTAL_VOLTAGE} V
Total Current: {PANEL_ARRAY_TOTAL_CURRENT} A
Total Power: {PANEL_ARRAY_TOTAL_POWER} W
Internal Resistance: {PANEL_ARRAY_INTERNAL_RESISTANCE:.2f} Ohm
            """)
        
        #MPPT
        circuit.I(f"{arr_no}_mppt_output", circuit.gnd, f"{arr_no}_mppt_output_positive", MPPT_OUTPUT_CURRENT)

        # Tie MPPT output directly to battery bus
        last_battery_in_first_row = f"battery_{BATTERY_IN_PARALLEL-1}_{BATTERY_IN_SERIES-1}"
        circuit.R(f"{arr_no}_mppt_bus_link", f"{arr_no}_mppt_output_positive", f"{last_battery_in_first_row}_positive", 0.01)

        print(f"""
{BARF}MPPT Setup {arr_no + 1}{BARE}
Input Voltage: {MPPT_INPUT_VOLTAGE} V
Output Voltage: {MPPT_OUTPUT_VOLTAGE} V
Max Power: {MPPT_MAX_POWER} W
Output Power: {MPPT_OUTPUT_POWER:.2f} W
Output Current: {MPPT_OUTPUT_CURRENT:.2f} A
    """)

    
    # Battery
    for p in range(BATTERY_IN_PARALLEL):
        battery_row = []
        for s in range(BATTERY_IN_SERIES):
            battery_name = f"battery_{p}_{s}"
            battery_row.append(battery_name)
            
            if s == 0:
                circuit.V(battery_name, f"{battery_name}_positive", circuit.gnd, BATTERY_VOLTAGE)
                circuit.R(f"{battery_name}_internal_resistance", f"{battery_name}_positive", f"{battery_name}_negative", 0.01)
            else:
                circuit.V(battery_name, f"{battery_name}_positive", f"battery_{p}_{s-1}_negative", BATTERY_VOLTAGE)
                circuit.R(f"{battery_name}_internal_resistance", f"{battery_name}_positive", f"{battery_name}_negative", 0.01)
            components["battery"].append(battery_row)
        
    for index, row in enumerate(components["battery"]):
        battery_row_end = row[-1]
        positive_node = f"{battery_row_end}_positive"
        battery_wire = f"battery_wire_{index}"
        circuit.R(battery_wire, positive_node, "mppt_output_positive", 0.01)  
        components["wire"].append(battery_wire)
        # Connect battery array to MPPT output with small resistance

    print(f"""
{BARF}Battery Setup{BARE}
Configuration: {BATTERY_IN_SERIES} in series, {BATTERY_IN_PARALLEL} in parallel
Total Voltage: {BATTERY_TOTAL_VOLTAGE} V
          """)    
    
    
    # Load
    circuit.R("motor_load", "mppt_output_positive", circuit.gnd, MOTOR_RESISTANCE)
    components["load"].append("motor_load")
    
    print(f"""
{BARF}Load Setup{BARE}
Motor Power Demand: {MOTOR_POWER_DEMAND} W
Motor Current Demand: {MOTOR_CURRENT_DEMAND:.2f} A
Motor Resistance: {MOTOR_RESISTANCE:.2f} Ohm
          """)
    
    
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
