from skidl import *

def import_libraries_for_kicad5():
    # Set up search paths for KiCad5 libraries
    # Explicitly add the KiCad5 symbol and footprint paths
    if 'C:\\Program Files\\KiCad\\share\\kicad\\library' not in lib_search_paths[KICAD5]:
        lib_search_paths[KICAD5].append('C:\\Program Files\\KiCad\\share\\kicad\\library')
        print("Added KiCad5 symbol path to lib_search_paths.")

    if 'C:\\Program Files\\KiCad\\share\\kicad\\modules' not in footprint_search_paths[KICAD5]:
        footprint_search_paths[KICAD5].append('C:\\Program Files\\KiCad\\share\\kicad\\modules')
        print("Added KiCad5 footprint path to footprint_search_paths.")

# Generate schematics only for KICAD5
import_libraries_for_kicad5()
set_default_tool(KICAD5)

# Generate schematics only for KICAD9
#set_default_tool(KICAD9)

def solar_3_parallel(vplus, gnd):


    cells = []
    for _ in range(3):
        cell = Part('Device', 'Solar_Cell', value='Solar')
        cell['+'] += vplus
        cell['-'] += gnd
        cells.append(cell)

    return cells, vplus, gnd
        
VPLUS = Net('VPLUS')
GND   = Net('GND')

# Instantiate subcircuit
solar_3_parallel(VPLUS, GND)

# --- Generate schematic + netlist ---
generate_netlist()
generate_schematic()