from components.battery_array import Battery_Array
from components.solar_panel_array import Solar_Array
from configurations.constants import GROUNDING_RESISTANCE, WIRE_RESISTANCE, BARF, BARE

class MPPT:
    def __init__(self, circuit, components, max_output_current, efficiency):
        self.MPPT_MAX_OUTPUT_CURRENT = max_output_current
        self.MPPT_OUTPUT_BUFFER_VOLTAGE = 5
        self.MPPT_EFFICIENCY = efficiency
        self.circuit = circuit
        self.components = components
    
    def setup_mppt(self, array_number, solar_array: Solar_Array, battery_array: Battery_Array, log=False):
        MPPT_INPUT_VOLTAGE = solar_array.get_total_voltage()
        MPPT_INPUT_CURRENT = solar_array.get_total_current()
        MPPT_MAX_INPUT_POWER = MPPT_INPUT_VOLTAGE * MPPT_INPUT_CURRENT
        MPPT_INPUT_RESISTANCE = MPPT_INPUT_VOLTAGE / MPPT_INPUT_CURRENT
        
        MPPT_OUTPUT_VOLTAGE = battery_array.get_total_voltage() + self.MPPT_OUTPUT_BUFFER_VOLTAGE
        MPPT_OUTPUT_POWER = MPPT_MAX_INPUT_POWER * self.MPPT_EFFICIENCY
        MPPT_OUTPUT_CURRENT = MPPT_OUTPUT_POWER / MPPT_OUTPUT_VOLTAGE

        self.circuit.R(f"{array_number}_mppt_input_load", 
                 f"{array_number}_solar_array_output_measured", self.circuit.gnd, 
                 MPPT_INPUT_RESISTANCE)

        # Regulate output current to calculated amount
        self.circuit.raw_spice += f"""B{array_number}_mppt_i_reg 0 {array_number}_mppt_out I = min({self.MPPT_MAX_OUTPUT_CURRENT}, {MPPT_OUTPUT_CURRENT})\n"""
        
        self.circuit.V(f"{array_number}_mppt_output_current", f"{array_number}_mppt_out", f"{array_number}_mppt_output_measured", GROUNDING_RESISTANCE)
        # Connect MPPT output to DC bus
        self.circuit.R(f"{array_number}_mppt_out_wire", f"{array_number}_mppt_output_measured", "power_source", WIRE_RESISTANCE)
        #dc_bus is shared positive node for battery and load

        self.components["mppt"].append(f"{array_number}_mppt_i_reg")
        self.components["wire"].append(f"{array_number}_mppt_out_wire")

        if log:
            print(self.__str__(array_number, MPPT_INPUT_VOLTAGE, MPPT_OUTPUT_VOLTAGE, MPPT_MAX_INPUT_POWER, MPPT_OUTPUT_POWER, MPPT_OUTPUT_CURRENT))
            
            
    def __str__(self, array_number, MPPT_INPUT_VOLTAGE, MPPT_OUTPUT_VOLTAGE, MPPT_MAX_INPUT_POWER, MPPT_OUTPUT_POWER, MPPT_OUTPUT_CURRENT):
        return f"""
{BARF}MPPT Setup {array_number + 1}{BARE}
Input Voltage: {MPPT_INPUT_VOLTAGE} V
Output Voltage: {MPPT_OUTPUT_VOLTAGE} V
Max Power: {MPPT_MAX_INPUT_POWER} W
Output Power: {MPPT_OUTPUT_POWER:.2f} W
Output Current: {MPPT_OUTPUT_CURRENT:.2f} A
"""