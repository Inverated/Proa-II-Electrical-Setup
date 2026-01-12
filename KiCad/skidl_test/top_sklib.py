from collections import defaultdict
from skidl import Pin, Part, Alias, SchLib, SKIDL, TEMPLATE

from skidl.pin import pin_types

SKIDL_lib_version = '0.0.1'

top = SchLib(tool=SKIDL).add_parts(*[
        Part(**{ 'name':'Battery', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'Battery'}), 'ref_prefix':'BT', 'fplist':[], 'footprint':'Battery_SMD:Battery_9V', 'keywords':'batt voltage-source cell', 'description':'Multiple-cell battery', 'datasheet':'~', 'pins':[
            Pin(num='1',name='+',func=pin_types.PASSIVE,unit=1),
            Pin(num='2',name='-',func=pin_types.PASSIVE,unit=1)] })])