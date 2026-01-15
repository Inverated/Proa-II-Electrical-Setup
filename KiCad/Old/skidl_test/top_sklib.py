from collections import defaultdict
from skidl import Pin, Part, Alias, SchLib, SKIDL, TEMPLATE

from skidl.pin import pin_types

SKIDL_lib_version = '0.0.1'

top = SchLib(tool=SKIDL).add_parts(*[
        Part(**{ 'name':'Solar_Cell', 'dest':TEMPLATE, 'tool':SKIDL, 'aliases':Alias({'Solar_Cell'}), 'ref_prefix':'SC', 'fplist':[], 'footprint':None, 'keywords':'solar cell', 'description':'Single solar cell', 'datasheet':'~', 'pins':[
            Pin(num='1',name='+',func=pin_types.PASSIVE,unit=1),
            Pin(num='2',name='-',func=pin_types.PASSIVE,unit=1)] })])