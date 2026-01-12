import skip
import pathlib

schematic_path = pathlib.Path.joinpath(pathlib.Path.cwd(), r'KiCad\Roti_Proa_II_Electrical\power_management_schematics\power_management_schematics.kicad_sch')

schem = skip.Schematic(schematic_path)




schem.write(schematic_path)

