from components.battery_array import Battery_Array
from configurations.constants import BARE, BARF, GROUNDING_RESISTANCE, RAWSPICE_ITERATIONS


class Load:
    def __init__(self, circuit, components, total_power, nominal_voltage):
        self.MOTOR_VOLTAGE = nominal_voltage
        self.MOTOR_TOTAL_POWER = total_power
        self.components = components
        self.circuit = circuit
        
    def setup_load(self, battery_array: Battery_Array, throttle: float = 1.0, log = False):
        MOTOR_POWER_DEMAND = self.MOTOR_TOTAL_POWER * throttle if throttle > 0.0 else GROUNDING_RESISTANCE
        
        BATTERY_MAX_DISCHARGE_CURRENT = battery_array.get_discharge_limit()
        MOTOR_CURRENT_DEMAND = MOTOR_POWER_DEMAND / battery_array.get_total_voltage()
        MOTOR_RESISTANCE = self.MOTOR_VOLTAGE / MOTOR_CURRENT_DEMAND

        POWER_SOURCE = battery_array.get_terminal()
        POWER_SOURCE_ID = battery_array.get_terminal_id()
        
        self.circuit.V("motor_load_source", POWER_SOURCE, "motor_load_negative", GROUNDING_RESISTANCE)
        #self.circuit.R("motor_load", "motor_load_negative", self.circuit.gnd, MOTOR_RESISTANCE)
        self.circuit.raw_spice += f"Bmotor_load motor_load_negative 0 I = I(V{POWER_SOURCE_ID})<-{BATTERY_MAX_DISCHARGE_CURRENT} ? {MOTOR_CURRENT_DEMAND}+(I(V{POWER_SOURCE_ID})+{BATTERY_MAX_DISCHARGE_CURRENT})*{RAWSPICE_ITERATIONS} : {MOTOR_CURRENT_DEMAND}\n"
        
        self.components["load"].append(f"motor_load_{len(self.components['load'])}")

        if log:
            print(self.__str__(MOTOR_POWER_DEMAND, MOTOR_CURRENT_DEMAND, MOTOR_RESISTANCE))
            
            
    def __str__(self, MOTOR_POWER_DEMAND=None, MOTOR_CURRENT_DEMAND=None, MOTOR_RESISTANCE=None):
        return f"""
{BARF}Load Setup (Before balancing){BARE}
Motor Power Demand: {MOTOR_POWER_DEMAND} W
Motor Current Demand: {MOTOR_CURRENT_DEMAND:.2f} A
Motor Resistance: {MOTOR_RESISTANCE:.2f} Ohm
"""