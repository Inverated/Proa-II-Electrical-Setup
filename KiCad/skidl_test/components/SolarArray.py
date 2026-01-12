from skidl import *

@SubCircuit
def solar_3_parallel(vplus, gnd):
    """
    Three solar cells connected in parallel.
    vplus : positive output net
    gnd   : negative output net
    """

    for i in range(3):
        cell = Part(
            'Device',
            'Solar_Cell',
            value='Solar',
            footprint='Solar_Cell:SolarCell_Example'  # replace with real footprint
        )

        cell['+'] += vplus
        cell['-'] += gnd
