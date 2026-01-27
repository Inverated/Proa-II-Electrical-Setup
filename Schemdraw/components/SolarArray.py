import math
import schemdraw
import schemdraw.elements as elm
from configurations.constants import COMPONENT_DISTANCE

class SolarArray:
    def __init__(self, series: int, parallel: int):
        self.series = series
        self.parallel = parallel

    def draw(self, drawing: schemdraw.Drawing, terminateDist: float = 2, isRight: bool = True):
        batteries = []
        upperWire = []
        lowerWire = []
        
        batteryID = 1
        for i in range(self.parallel):        
            batteryRow = []
            for j in range(self.series):
                battery = elm.Solar().down().label(f'B{batteryID}\n12V')
                batteryID += 1
                batteryRow.append(battery)
            
            fst = batteryRow[0]
            lst = batteryRow[-1]
            batteries.append(batteryRow)
            
            if i == 0:
                for batt in batteryRow:
                    drawing.add(batt)
            else:
                drawing.add(batteryRow[0].at(upperWire[-1].end))
                for index in range(1, len(batteryRow)):
                    drawing.add(batteryRow[index])
                
            upper = elm.Line().right().at(fst.start).length(COMPONENT_DISTANCE) if isRight else elm.Line().left().at(fst.start).length(COMPONENT_DISTANCE)
            lower = elm.Line().right().at(lst.end).length(COMPONENT_DISTANCE) if isRight else elm.Line().left().at(lst.end).length(COMPONENT_DISTANCE)
            drawing.add(upper)
            drawing.add(lower)
            upperWire.append(upper)
            lowerWire.append(lower)
                
        gap = math.dist(lowerWire[-1].end, upperWire[-1].end)
        
        if gap > terminateDist:
            topExt = elm.Line().down().at(upperWire[-1].end).length(gap/2 - terminateDist/2)
            drawing.add(topExt)
            drawing.add(elm.Line().right().at(topExt.end) if isRight else elm.Line().left().at(topExt.end))
            bottExt = elm.Line().up().at(lowerWire[-1].end).length(gap/2 - terminateDist/2)
            drawing.add(bottExt)
            drawing.add(elm.Line().right().at(bottExt.end) if isRight else elm.Line().left().at(bottExt.end))
            
        elif gap < terminateDist:
            topExt = elm.Line().up().at(upperWire[-1].end).length(terminateDist/2 - gap/2)
            drawing.add(topExt)
            drawing.add(elm.Line().right().at(topExt.end) if isRight else elm.Line().left().at(topExt.end))
            bottExt = elm.Line().down().at(lowerWire[-1].end).length(terminateDist/2 - gap/2)
            drawing.add(bottExt)
            drawing.add(elm.Line().right().at(bottExt.end) if isRight else elm.Line().left().at(bottExt.end))
        
        else:
            topExt = upperWire[-1]
            bottExt = lowerWire[-1]
            
        return drawing, (topExt, bottExt)