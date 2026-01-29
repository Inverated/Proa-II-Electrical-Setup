import json


def start_voyage(circuit_config_loc: str, voyage_config_loc: str, ngspice_available: bool):
    with open(voyage_config_loc, 'r') as f:
        data = json.load(f)
        
    voyage_info = data['voyage_info']
    initial_soc = data['initial_battery_soc']
    segments = data['segments']
    
    print(json.dumps(segments, indent=4) )
    
    
    
    
    
    
    
    
    
    
    
    
    
    None
    
def real_time_digital_simulation(circuit_config_loc: str, ngspice_available: bool):
    None