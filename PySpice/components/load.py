from components.battery_array import Battery_Array
from configurations.constants import BARE, BARF, GROUNDING_RESISTANCE, RAWSPICE_ITERATIONS, VOLTAGE_MISMATCH_TOLERANCE


class Load:
    def __init__(self, circuit, components, load_name, total_power, nominal_voltage, throttle: float = 1.0):
        self.load_name = load_name
        self.throttle = throttle
        self.MOTOR_VOLTAGE = nominal_voltage
        self.MOTOR_TOTAL_POWER = total_power
        self.components = components
        self.circuit = circuit
        self.MOTOR_POWER_DEMAND = None
        
    def setup_load(self, battery_array: Battery_Array, log = False):
        self.MOTOR_POWER_DEMAND = self.MOTOR_TOTAL_POWER * self.throttle if self.throttle > 0.0 else GROUNDING_RESISTANCE
        
        BATTERY_MAX_DISCHARGE_CURRENT = battery_array.get_discharge_limit()
        MOTOR_CURRENT_DEMAND = self.MOTOR_POWER_DEMAND / battery_array.get_total_voltage()
        MOTOR_RESISTANCE = self.MOTOR_VOLTAGE / MOTOR_CURRENT_DEMAND

        POWER_SOURCE = battery_array.get_terminal()
        POWER_SOURCE_ID = battery_array.get_terminal_id()
        
        
        self.circuit.V(f"{self.load_name}_source", POWER_SOURCE, f"{self.load_name}_negative", GROUNDING_RESISTANCE)
        #self.circuit.R(f"{self.load_name}", f"{self.load_name}_negative", self.circuit.gnd, MOTOR_RESISTANCE)
        self.circuit.raw_spice += f"B{self.load_name} {self.load_name}_negative 0 I = I(V{POWER_SOURCE_ID})<-{BATTERY_MAX_DISCHARGE_CURRENT} ? {MOTOR_CURRENT_DEMAND}+(I(V{POWER_SOURCE_ID})+{BATTERY_MAX_DISCHARGE_CURRENT})*{RAWSPICE_ITERATIONS} : {MOTOR_CURRENT_DEMAND}\n"
        
        self.components["load"].append(f"{self.load_name}_{len(self.components['load'])}")
        if log:
            print(self.__str__(self.MOTOR_POWER_DEMAND, MOTOR_CURRENT_DEMAND, MOTOR_RESISTANCE))
        
        if abs(battery_array.get_total_voltage() - self.MOTOR_VOLTAGE) > VOLTAGE_MISMATCH_TOLERANCE:
            return f"Mismatch between battery voltage ({battery_array.get_total_voltage()} V) and motor nominal voltage ({self.MOTOR_VOLTAGE} V) exceeds tolerance of {VOLTAGE_MISMATCH_TOLERANCE} V"
        
        return None
            
    def initial_power_demand(self):
        if self.MOTOR_POWER_DEMAND is None:
            return "Load not yet setup."
        return self.MOTOR_POWER_DEMAND
    
    def __str__(self, MOTOR_POWER_DEMAND=None, MOTOR_CURRENT_DEMAND=None, MOTOR_RESISTANCE=None):
        return f"""
{BARF}Load Setup (Before balancing){BARE}
Motor Power Demand: {MOTOR_POWER_DEMAND} W
Motor Current Demand: {MOTOR_CURRENT_DEMAND:.2f} A
Motor Resistance: {MOTOR_RESISTANCE:.2f} Ohm
"""