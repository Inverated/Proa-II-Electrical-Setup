from skidl import *

# Set up library and footprint search paths for KiCad
# setx KICAD_SYMBOL_DIR "C:\Program Files\KiCad\share\kicad\library"
# set KICAD_SYMBOL_DIR="C:\Program Files\KiCad\share\kicad\library"

# setx KISYSMOD "C:\Program Files\KiCad\share\kicad\modules"
# set KISYSMOD="C:\Program Files\KiCad\share\kicad\modules"	

# setx KICAD_FOOTPRINT_DIR "C:\Program Files\KiCad\share\kicad\modules" 
# set KICAD_FOOTPRINT_DIR="C:\Program Files\KiCad\share\kicad\modules" 

# Explicitly add the KiCad5 symbol and footprint paths
if 'C:\\Program Files\\KiCad\\share\\kicad\\library' not in lib_search_paths[KICAD5]:
    lib_search_paths[KICAD5].append('C:\\Program Files\\KiCad\\share\\kicad\\library')
    print("Added KiCad5 symbol path to lib_search_paths.")

if 'C:\\Program Files\\KiCad\\share\\kicad\\modules' not in footprint_search_paths[KICAD5]:
    footprint_search_paths[KICAD5].append('C:\\Program Files\\KiCad\\share\\kicad\\modules')
    print("Added KiCad5 footprint path to footprint_search_paths.")

set_default_tool(KICAD5)

VPLUS_TOP = Net("VPLUS_TOP")
GND_TOP   = Net("GND_TOP")

# --- Subcircuit ---
class BatteryParallel(SubCircuit):
    def __init__(self, vplus_net, gnd_net, *args, **kwargs):
        self.initialize(*args, **kwargs)

        # Internal nets
        VPLUS = Net("VPLUS")
        GND   = Net("GND")

        # Two batteries in parallel
        b1 = Part("Device", "Battery", value="9V")
        b2 = Part("Device", "Battery", value="9V")
        b1.footprint = "Battery_SMD:Battery_9V"  # adjust based on KiCad 5 footprint library
        b2.footprint = "Battery_SMD:Battery_9V"

        VPLUS & b1["+"] & b2["+"]  
        GND & b1["-"] & b2["-"]

        # Connect internal nets to top-level nets
        VPLUS += vplus_net
        GND   += gnd_net

        # Create hierarchical pins for top sheet
        self.create_pins("VPLUS", connections=VPLUS)
        self.create_pins("GND", connections=GND)

        self.finalize()

# --- Instantiate subcircuit ---
bat_parallel = BatteryParallel(VPLUS_TOP, GND_TOP)

# --- Generate schematic + netlist ---
generate_schematic()
generate_netlist()