import schemdraw
import schemdraw.elements as elm

from Components.SolarArray import SolarArray

drawing = schemdraw.Drawing()
drawing.config(unit=2)  # default .length( units )

drawing, (top,bottom) = SolarArray(series=3, parallel=2).draw(drawing, terminateDist=2, isRight=True)
drawing, (top,bottom) = SolarArray(series=3, parallel=2).draw(drawing, terminateDist=2, isRight=False)

drawing.draw()

