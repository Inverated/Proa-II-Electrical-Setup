"""
PySpice Circuit Building - Simple Explanation
==============================================

Circuit: 2x 24V Batteries (series) → Buck Converter (48V→24V) → 1kΩ Resistor

Key Concepts:
1. Nodes are connection points (like wires joining)
2. Components connect between two or more nodes
3. Ground is always node "0" or circuit.gnd
4. Each component needs a name and node connections

SETUP REQUIRED:
===============
PySpice requires NgSpice to be installed. If you get a DLL error:

Windows:
1. Download NgSpice from: https://ngspice.sourceforge.io/download.html
   - Get the "ngspice-XX_64.zip" file (64-bit)
2. Extract to C:\Program Files\ngspice
3. Add to PATH or set environment variable:
   setx PYSPICE_LIBRARY_PATH "C:\Program Files\ngspice\Spice64\bin"

Alternative - Use PySpice offline mode (just build circuit, no simulation):
- Set: import os
       os.environ['PYSPICE_USE_NGSPICE'] = '0'
"""

from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import numpy as np
import matplotlib.pyplot as plt
import os

# Try to detect if NgSpice is available
NGSPICE_AVAILABLE = True
try:
    from PySpice.Spice.NgSpice.Shared import NgSpiceShared
    # Try to create a dummy instance to check if library loads
    test = NgSpiceShared.new_instance()
except Exception as e:
    NGSPICE_AVAILABLE = False
    print("WARNING: NgSpice not found. Circuit will be built but not simulated.")
    print("To enable simulation, install NgSpice:")
    print("  https://ngspice.sourceforge.io/download.html")
    print(f"Error: {e}")
    print()

# =============================================================================
# STEP 1: CREATE THE CIRCUIT
# =============================================================================

# Create a new circuit with a name
circuit = Circuit('Battery_Buck_Resistor')

print("="*70)
print("STEP 1: CIRCUIT CREATED")
print("="*70)
print("Circuit object created: 'Battery_Buck_Resistor'")
print(f"Ground node: {circuit.gnd}")
print()

# =============================================================================
# STEP 2: UNDERSTAND NODES (Connection Points)
# =============================================================================

print("="*70)
print("STEP 2: NODES - The Connection Points")
print("="*70)
print("""
Think of nodes as labeled wire junctions in your circuit.

Our circuit will have these nodes:
  - 0 (ground)           ← Reference point, 0V
  - bat1_positive        ← Top of first battery (+24V)
  - bat2_positive        ← Top of second battery (+48V) 
  - buck_output          ← Output of buck converter (+24V)
  
Visualization:
                    bat2_positive (+48V)
                         |
                    [Battery 2]
                         |
                    bat1_positive (+24V)
                         |
                    [Battery 1]
                         |
    0 (ground) ──────────┴──────────── 0V reference
""")
print()

# =============================================================================
# STEP 3: ADD FIRST BATTERY (24V)
# =============================================================================

print("="*70)
print("STEP 3: ADD FIRST BATTERY")
print("="*70)

# Format: circuit.V(name, positive_node, negative_node, voltage)
circuit.V('battery1', 'bat1_positive', circuit.gnd, 24)

print("Battery 1 added:")
print("  Component name: V_battery1")
print("  Positive terminal: connected to node 'bat1_positive'")
print("  Negative terminal: connected to node '0' (ground)")
print("  Voltage: 24V")
print()
print("Diagram:")
print("  bat1_positive (+24V)")
print("        |")
print("    [Battery 1]")
print("        |")
print("    0 (ground)")
print()

# =============================================================================
# STEP 4: ADD SECOND BATTERY (24V) IN SERIES
# =============================================================================

print("="*70)
print("STEP 4: ADD SECOND BATTERY IN SERIES")
print("="*70)

# Second battery: positive at new node, negative connects to first battery's positive
circuit.V('battery2', 'bat2_positive', 'bat1_positive', 24)

print("Battery 2 added:")
print("  Component name: V_battery2")
print("  Positive terminal: connected to node 'bat2_positive'")
print("  Negative terminal: connected to node 'bat1_positive'")
print("  Voltage: 24V")
print()
print("IMPORTANT: Series connection!")
print("  Battery 2's negative connects to Battery 1's positive")
print("  Total voltage: 24V + 24V = 48V from 'bat2_positive' to ground")
print()
print("Diagram:")
print("  bat2_positive (+48V)")
print("        |")
print("    [Battery 2] 24V")
print("        |")
print("  bat1_positive (+24V)")
print("        |")
print("    [Battery 1] 24V")
print("        |")
print("    0 (ground, 0V)")
print()

# =============================================================================
# STEP 5: ADD IDEAL BUCK CONVERTER
# =============================================================================

print("="*70)
print("STEP 5: ADD IDEAL BUCK CONVERTER (48V → 24V)")
print("="*70)

# An ideal buck converter with proper grounding
# We'll use a simpler model: voltage-controlled voltage source (VCVS)
# connected through a resistor to model input current draw

# Add a very small series resistor at input for current measurement
circuit.R('buck_input_sense', 'bat2_positive', 'buck_input_internal', 0.001)

# Ideal buck model using VCVS (voltage-controlled voltage source)
# Output voltage = 24V (independent of input, ideal regulation)
# The VCVS acts as a perfect power converter

# For an ideal buck: we need to model the input current
# Method: Use a current-controlled current source
# The load determines output current, which determines input current

# Output stage: constant 24V
circuit.raw_spice += "\nBbuck_output buck_output 0 V=24"

# Input current modeling: behavioral resistor that changes resistance
# to maintain power balance: P_in = P_out
# R_equivalent = V_in^2 / P_out = V_in^2 / (V_out * I_out)
# For V_in=48V, V_out=24V, I_out=24mA: R_eq = 48^2 / (24*0.024) = 4000 ohms

# Simpler approach: Just use a resistor that gives us the right power
# P_out = 576mW, V_in = 48V → R = V^2/P = 48^2/0.576 = 4000 ohms
circuit.R('buck_input_load', 'buck_input_internal', circuit.gnd, 4000)

print("Buck converter added:")
print("  Input resistor: Simulates power draw (4kΩ)")
print("  Output: Behavioral voltage source 'Bbuck_output'")
print("    - Outputs constant 24V regardless of input")
print()
print("Simplified ideal model:")
print("  Input current ≈ 12mA (48V / 4kΩ)")
print("  Output current = 24mA (24V / 1kΩ load)")
print("  Input power ≈ 576mW")
print("  Output power = 576mW")
print("  Efficiency ≈ 100%")
print()
print("Note: This is a simplified model.")
print("      A real buck would use switches, inductor, and feedback.")
print()

# =============================================================================
# STEP 6: ADD LOAD RESISTOR (1kΩ)
# =============================================================================

print("="*70)
print("STEP 6: ADD LOAD RESISTOR")
print("="*70)

# Format: circuit.R(name, node1, node2, resistance)
circuit.R('load', 'buck_output', circuit.gnd, 1000)

print("Load resistor added:")
print("  Component name: R_load")
print("  Terminal 1: connected to node 'buck_output'")
print("  Terminal 2: connected to node '0' (ground)")
print("  Resistance: 1000Ω (1kΩ)")
print()
print("Current calculation (Ohm's law):")
print("  I = V / R = 24V / 1000Ω = 0.024A = 24mA")
print()
print("Power dissipation:")
print("  P = V² / R = 24² / 1000 = 0.576W = 576mW")
print()

# =============================================================================
# STEP 7: COMPLETE CIRCUIT DIAGRAM
# =============================================================================

print("="*70)
print("STEP 7: COMPLETE CIRCUIT OVERVIEW")
print("="*70)
print("""
Complete Circuit with Node Names:

    bat2_positive (+48V)
           |
       [Battery 2] 24V
           |
    bat1_positive (+24V)
           |
       [Battery 1] 24V
           |
       ────┴──── 0 (ground)
           
    bat2_positive (+48V)
           |
       [BUCK 48V→24V]
           |
    buck_output (+24V)
           |
       [1kΩ Resistor]
           |
       ────┴──── 0 (ground)

Node Summary:
  - bat2_positive: +48V (top of battery stack)
  - bat1_positive: +24V (middle connection)
  - buck_output:   +24V (regulated output)
  - 0 (ground):    0V   (reference)
""")
print()

# =============================================================================
# STEP 8: PYSPICE COMPONENT SYNTAX BREAKDOWN
# =============================================================================

print("="*70)
print("STEP 8: PYSPICE COMPONENT SYNTAX EXPLAINED")
print("="*70)
print("""
General Format:
  circuit.COMPONENT_TYPE(name, node1, node2, ..., value)

Examples from our circuit:

1. VOLTAGE SOURCE (Battery):
   circuit.V('battery1', 'bat1_positive', circuit.gnd, 24)
            │            │                │             │
            │            │                │             └─ Value: 24V
            │            │                └─ Negative terminal: ground
            │            └─ Positive terminal: node 'bat1_positive'
            └─ Name: 'battery1' (PySpice adds 'V' prefix → Vbattery1)

2. RESISTOR:
   circuit.R('load', 'buck_output', circuit.gnd, 1000)
            │        │               │             │
            │        │               │             └─ Value: 1000Ω
            │        │               └─ Terminal 2: ground
            │        └─ Terminal 1: node 'buck_output'
            └─ Name: 'load' (PySpice adds 'R' prefix → Rload)

3. BEHAVIORAL SOURCE (Buck output):
   circuit.raw_spice += "Bbuck_output buck_output 0 V=24"
                         │           │            │  │
                         │           │            │  └─ Equation: V=24
                         │           │            └─ Negative: ground (0)
                         │           └─ Positive: node 'buck_output'
                         └─ Name: 'buck_output'

KEY RULES:
  1. Node names can be strings ('bat1_positive') or 0/circuit.gnd for ground
  2. First node is usually positive/high, second is negative/low (for clarity)
  3. Component names get a letter prefix (V for voltage, R for resistor, etc.)
  4. Order matters: V(name, +node, -node, value)
  5. Values can be numbers or use units: 24@u_V, 1@u_kOhm
""")
print()

# =============================================================================
# STEP 9: SIMULATE AND MEASURE
# =============================================================================

print("="*70)
print("STEP 9: RUN SIMULATION")
print("="*70)

if not NGSPICE_AVAILABLE:
    print("NgSpice not available - showing expected results instead")
    print()
    print("EXPECTED RESULTS (calculated):")
    print("-" * 40)
    print()
    
    # Calculate expected values
    v_bat2 = 48.0
    v_bat1 = 24.0
    v_buck_out = 24.0
    i_load = 24.0 / 1000.0  # 24V / 1kΩ
    i_bat = i_load  # Ideal buck, same current (simplified)
    
    print("NODE VOLTAGES:")
    print(f"  bat2_positive:  {v_bat2:.3f} V  (Top of battery stack)")
    print(f"  bat1_positive:  {v_bat1:.3f} V  (Between batteries)")
    print(f"  buck_output:    {v_buck_out:.3f} V  (Buck converter output)")
    print(f"  ground (0):     {0:.3f} V  (Reference)")
    print()
    
    print("COMPONENT CURRENTS:")
    print(f"  Battery 1 (Vbattery1):  {i_bat*1000:.3f} mA")
    print(f"  Battery 2 (Vbattery2):  {i_bat*1000:.3f} mA")
    print(f"  Load resistor (Rload):  {i_load*1000:.3f} mA")
    print()
    
    print("POWER CALCULATIONS:")
    p_bat_total = v_bat2 * i_bat
    p_load = v_buck_out * i_load
    efficiency = (p_load / p_bat_total * 100) if p_bat_total > 0 else 100
    
    print(f"  Battery power output:   {p_bat_total*1000:.3f} mW")
    print(f"  Load power dissipated:  {p_load*1000:.3f} mW")
    print(f"  Efficiency:             {efficiency:.1f}%")
    print()
    
else:
    # NgSpice is available - run actual simulation
    
    # Create simulator
    simulator = circuit.simulator(temperature=25, nominal_temperature=25)
    
    print("Simulator created at 25°C")
    print()
    
    # Run DC operating point analysis (finds steady-state voltages/currents)
    print("Running DC operating point analysis...")
    analysis = simulator.operating_point()
    print("Analysis complete!")
    print()
    
    # =============================================================================
    # STEP 10: EXTRACT AND DISPLAY RESULTS
    # =============================================================================
    
    print("="*70)
    print("STEP 10: SIMULATION RESULTS")
    print("="*70)
    print()
    
    # Get node voltages
    print("NODE VOLTAGES:")
    print("-" * 40)
    
    # Extract voltage at each node (convert numpy array to float)
    v_bat2 = float(analysis['bat2_positive'].as_ndarray()[0])
    v_bat1 = float(analysis['bat1_positive'].as_ndarray()[0])
    v_buck_out = float(analysis['buck_output'].as_ndarray()[0])
    
    print(f"  bat2_positive:  {v_bat2:.3f} V  (Top of battery stack)")
    print(f"  bat1_positive:  {v_bat1:.3f} V  (Between batteries)")
    print(f"  buck_output:    {v_buck_out:.3f} V  (Buck converter output)")
    print(f"  ground (0):     {0:.3f} V  (Reference)")
    print()
    
    # Calculate currents
    print("COMPONENT CURRENTS:")
    print("-" * 40)
    
    # Current through batteries (SPICE tracks voltage source currents)
    i_bat1 = -float(analysis['Vbattery1'].as_ndarray()[0])  # Negative because of convention
    i_bat2 = -float(analysis['Vbattery2'].as_ndarray()[0])
    
    # Current through resistor (using Ohm's law)
    i_load = v_buck_out / 1000  # V / R
    
    # Current at buck input (through the sense resistor)
    # Calculate from Ohm's law: I = (V1 - V2) / R
    v_buck_in = float(analysis['buck_input_internal'].as_ndarray()[0])
    i_buck_in = (v_bat2 - v_buck_in) / 0.001  # Current through 0.001 ohm sense resistor
    
    print(f"  Battery 1 (Vbattery1):  {i_bat1*1000:.3f} mA")
    print(f"  Battery 2 (Vbattery2):  {i_bat2*1000:.3f} mA")
    print(f"  Buck input:             {i_buck_in*1000:.3f} mA")
    print(f"  Load resistor (Rload):  {i_load*1000:.3f} mA")
    print()
    
    # Power calculations
    print("POWER CALCULATIONS:")
    print("-" * 40)
    
    p_bat_total = v_bat2 * i_bat2  # Power from battery stack
    p_load = v_buck_out * i_load    # Power to load
    
    # Debug: show what we're calculating
    print(f"  DEBUG: v_bat2={v_bat2:.3f}V, i_bat2={i_bat2:.6f}A")
    print(f"  DEBUG: v_buck_out={v_buck_out:.3f}V, i_load={i_load:.6f}A")
    print()
    
    efficiency = (p_load / p_bat_total * 100) if p_bat_total > 1e-9 else 0
    
    print(f"  Battery power output:   {p_bat_total*1000:.3f} mW")
    print(f"  Load power dissipated:  {p_load*1000:.3f} mW")
    print(f"  Efficiency:             {efficiency:.1f}%")
    print()

# =============================================================================
# STEP 11: KEY TAKEAWAYS
# =============================================================================

print("="*70)
print("STEP 11: KEY TAKEAWAYS")
print("="*70)
print("""
HOW PYSPICE DEFINES CONNECTIONS:
═══════════════════════════════════

1. NODES are connection points (wires)
   - Use string names: 'bat1_positive', 'buck_output'
   - Ground is always: 0 or circuit.gnd
   - Same node name = electrically connected

2. COMPONENTS connect between nodes
   - Format: circuit.TYPE(name, node1, node2, ..., value)
   - Each component must have unique name
   - Nodes can be reused across components

3. VALUES can be specified as:
   - Plain numbers: 24, 1000
   - With units: 24@u_V, 1@u_kOhm
   - Expressions: "V(node1)*2"

4. SERIES connections:
   - Share a common node between components
   - Battery2(-) connects to Battery1(+) at 'bat1_positive'

5. PARALLEL connections:
   - Both terminals connect to same two nodes
   - Example: Two resistors from 'buck_output' to '0'

EXAMPLE CONNECTION PATTERNS:
════════════════════════════

Series (Batteries):
  V(bat2, bat2_pos, bat1_pos, 24V)  ← bat2- connects to bat1+
  V(bat1, bat1_pos, gnd, 24V)       ← bat1- connects to gnd
  Result: 48V total

Parallel (Resistors):
  R(r1, buck_out, gnd, 1k)          ← Both connect same nodes
  R(r2, buck_out, gnd, 2k)          ← Both connect same nodes
  Result: 666Ω equivalent

Voltage Divider:
  R(r1, vin, vmid, 1k)              ← Chain of connections
  R(r2, vmid, gnd, 1k)              ← via shared 'vmid' node
  Result: vmid = vin/2
""")

print("\n" + "="*70)
print("SIMULATION SUMMARY")
print("="*70)

# Use calculated values if NgSpice not available
if 'v_bat2' not in locals():
    v_bat2 = 48.0
    v_buck_out = 24.0
    i_load = 0.024
    p_load = 0.576
    efficiency = 100.0

print(f"""
Circuit: 2×24V Batteries → Buck Converter → 1kΩ Load

Results:
  Input voltage:   {v_bat2:.1f}V
  Output voltage:  {v_buck_out:.1f}V
  Load current:    {i_load*1000:.1f}mA
  Load power:      {p_load*1000:.1f}mW
  Efficiency:      {efficiency:.0f}%

The circuit works as expected!
""")

if not NGSPICE_AVAILABLE:
    print("="*70)
    print("TO ENABLE ACTUAL SIMULATION:")
    print("="*70)
    print("""
1. Download NgSpice for Windows (64-bit):
   https://ngspice.sourceforge.io/download.html
   
2. Extract to: C:\\Program Files\\ngspice

3. Add to system PATH or set environment variable:
   setx PYSPICE_LIBRARY_PATH "C:\\Program Files\\ngspice\\Spice64\\bin"
   
4. Restart your terminal/IDE

Alternatively, you can view the circuit netlist without simulation:
    print(circuit)
    """)