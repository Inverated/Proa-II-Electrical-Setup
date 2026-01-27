import math
import schemdraw
import schemdraw.elements as elm
from configurations.constants import COMPONENT_DISTANCE

class ElementArray:
    def draw(self, drawing: schemdraw.Drawing, element: schemdraw.elements.Element, series: int, parallel: int, terminateDist: float = 2, isRight: bool = True):
        batteries = []
        upperWire = []
        lowerWire = []
        batteryID = 1
        
        series = max(1, series)
        parallel = max(1, parallel)
        
        for i in range(parallel):
            batteryRow = []
            for j in range(series):
                battery = element().down().label(f'B{batteryID}\n12V')
                batteryID += 1
                batteryRow.append(battery)
            
            fst = batteryRow[0]
            lst = batteryRow[-1]
            batteries.append(batteryRow)
            
            if i == 0:
                drawing.add(fst)
                for index in range(1, len(batteryRow)):
                    batt = batteryRow[index]
                    drawing.add(elm.Line().down().at(batteryRow[index-1].end).length(max(0, COMPONENT_DISTANCE-2)))
                    drawing.add(batt)
            else:
                drawing.add(batteryRow[0].at(upperWire[-1].end))
                for index in range(1, len(batteryRow)):
                    drawing.add(elm.Line().down().at(batteryRow[index-1].end).length(max(0, COMPONENT_DISTANCE-2)))
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
            top_terminal = elm.Line().right().at(topExt.end) if isRight else elm.Line().left().at(topExt.end)
            drawing.add(top_terminal)
            bottExt = elm.Line().up().at(lowerWire[-1].end).length(gap/2 - terminateDist/2)
            drawing.add(bottExt)
            bottom_terminal = elm.Line().right().at(bottExt.end) if isRight else elm.Line().left().at(bottExt.end)
            drawing.add(bottom_terminal)
            
        elif gap < terminateDist:
            topExt = elm.Line().up().at(upperWire[-1].end).length(terminateDist/2 - gap/2)
            drawing.add(topExt)
            top_terminal = elm.Line().right().at(topExt.end) if isRight else elm.Line().left().at(topExt.end)
            drawing.add(top_terminal)
            bottExt = elm.Line().down().at(lowerWire[-1].end).length(terminateDist/2 - gap/2)
            drawing.add(bottExt)
            bottom_terminal = elm.Line().right().at(bottExt.end) if isRight else elm.Line().left().at(bottExt.end)
            drawing.add(bottom_terminal)
        
        else:
            topExt = upperWire[-1]
            top_terminal = topExt
            bottExt = lowerWire[-1]
            bottom_terminal = bottExt
            
        return drawing, (top_terminal, bottom_terminal)