GROUNDING_RESISTANCE    = 1e-6
WIRE_RESISTANCE         = 0.01
BARF                    = "=" * 50 + "\n"
BARE                    = "\n" + "=" * 50
EPSILON = 1e-4

MPPT_BATTERY_VOLTAGE_BUFFER     = 2.0
VOLTAGE_MISMATCH_TOLERANCE      = 5.0
POWER_MISMATCH_TOLERANCE_PERCENTAGE = 1.0

# Use dictt(re.findall(...)) to decode arr1_s2_p4_... to {'arr': 1, 's': 2, 'p': 4}
ARRAY_DECODER_PATTERN = r'(arr|s|p)(\d+)(?=_|\s|$)'
