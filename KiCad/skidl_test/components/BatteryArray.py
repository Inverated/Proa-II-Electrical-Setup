from skidl import *

class BatteryParallel(SubCircuit):
    def __init__(self, vplus_net, gnd_net, *args, **kwargs):
        self.initialize(*args, **kwargs)

        # Internal nets
        VPLUS = Net("VPLUS")
        GND   = Net("GND")

        # Two batteries in parallel
        b1 = Part("Device", "Battery", value="9V")
        b2 = Part("Device", "Battery", value="9V")
        b1.footprint = "BatteryHolder_Keystone_2468_2xAAA"  # adjust based on KiCad 5 footprint library
        b2.footprint = "BatteryHolder_Keystone_2468_2xAAA"

        VPLUS & b1["+"] & b2["+"]  
        GND & b1["-"] & b2["-"]

        # Connect internal nets to top-level nets
        VPLUS += vplus_net
        GND   += gnd_net

        # Create hierarchical pins for top sheet
        self.create_pins("VPLUS", connections=VPLUS)
        self.create_pins("GND", connections=GND)

        self.finalize()