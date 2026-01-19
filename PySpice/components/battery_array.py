from constants import GROUNDING_RESISTANCE, WIRE_RESISTANCE, BARF, BARE

class Battery_Array:
    def __init__(self, circuit, components, BATTERY_IN_PARALLEL, BATTERY_IN_SERIES, BATTERY_VOLTAGE):
        self.circuit = circuit
        self.BATTERY_IN_PARALLEL = BATTERY_IN_PARALLEL
        self.BATTERY_IN_SERIES = BATTERY_IN_SERIES
        self.BATTERY_VOLTAGE = BATTERY_VOLTAGE
        self.BATTERY_MAX_CHARGE_CURRENT = 100
        self.BATTERY_MAX_DISCHARGE_CURRENT = 50
        self.terminal = None
        self.terminal_id = None
        self.components = components
    
    # Battery types should not be mixed, hence no array_number parameter
    def create_battery_array(self, log=False):
        for p in range(self.BATTERY_IN_PARALLEL):
            battery_row = []
            for s in range(self.BATTERY_IN_SERIES):
                battery_name = f"battery_{p}_{s}"
                battery_row.append(battery_name)
                
                battery_pos = f"{battery_name}_positive"
                battery_neg = f"{battery_name}_negative"
                
                self.circuit.V(battery_name, battery_pos, battery_neg, self.BATTERY_VOLTAGE)
                if s == 0:
                    self.circuit.R(f"{battery_name}_grounding", battery_neg, self.circuit.gnd, GROUNDING_RESISTANCE)
                else:
                    prev_battery_name = f"battery_{p}_{s-1}"
                    self.circuit.R(f"{battery_name}_internal", battery_neg, f"{prev_battery_name}_positive", WIRE_RESISTANCE)
                
            self.components["battery"].append(battery_row)
                        
        for index, row in enumerate(self.components["battery"]):
            battery_row_end = row[-1]
            positive_node = f"{battery_row_end}_positive"
            battery_wire = f"battery_wire_{index}"
            self.circuit.R(battery_wire, positive_node, "battery_input", WIRE_RESISTANCE)  
            self.components["wire"].append(battery_wire)
            
        self.circuit.V("battery_input_current_measurement",
                       "battery_input_measured",
                       "dc_bus",
                       GROUNDING_RESISTANCE)
        
        self.terminal_id = "battery_input_current_measurement"
        self.terminal = "dc_bus"
        
        if log:
            print(self)        

    def get_terminal(self):
        if self.terminal is None:
            raise ValueError("Battery Array terminal not created yet")
        return self.terminal
    
    def get_terminal_id(self):
        if self.terminal_id is None:
            raise ValueError("Battery Array terminal not created yet")
        return self.terminal_id
            
    def get_discharge_limit(self):
        return self.BATTERY_IN_PARALLEL * self.BATTERY_MAX_DISCHARGE_CURRENT
    
    def get_charge_limit(self):
        return self.BATTERY_IN_PARALLEL * self.BATTERY_MAX_CHARGE_CURRENT
    
    def get_total_voltage(self):
        return self.BATTERY_IN_SERIES * self.BATTERY_VOLTAGE   
            
    def __str__(self):
        return f"""
{BARF}Battery Setup{BARE}
Configuration: {self.BATTERY_IN_SERIES} in series, {self.BATTERY_IN_PARALLEL} in parallel
Total Voltage: {self.get_total_voltage()} V
Max Charge Current: {self.get_charge_limit()} A
Max Discharge Current: {self.get_discharge_limit()} A
"""