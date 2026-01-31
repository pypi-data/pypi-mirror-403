from .framework import Widget

class Paint:
    def __init__(self, color=0xFF000000, strokeWidth=1.0, style="fill"):
        self.color = color
        self.strokeWidth = strokeWidth
        self.style = style  # "fill" or "stroke"

    def to_json(self):
        return {
            "color": self.color,
            "strokeWidth": self.strokeWidth,
            "style": self.style,
        }

class CustomPainter:
    def __init__(self):
        self.commands = []

    def drawLine(self, p1, p2, paint):
        """p1, p2 are tuples (x, y)"""
        self.commands.append({
            "cmd": "drawLine",
            "p1": p1,
            "p2": p2,
            "paint": paint.to_json()
        })

    def drawCircle(self, c, radius, paint):
        """c is tuple (x, y)"""
        self.commands.append({
            "cmd": "drawCircle",
            "c": c,
            "radius": radius,
            "paint": paint.to_json()
        })
    
    def drawRect(self, rect, paint):
        """rect is tuple (left, top, width, height)"""
        self.commands.append({
            "cmd": "drawRect",
            "rect": rect,
            "paint": paint.to_json()
        })

    def to_json(self):
        return {"commands": self.commands}

class CustomPaint(Widget):
    def __init__(self, painter=None, child=None, size=(0, 0)):
        # Widget does not have an __init__ that calls super() in this makeshift framework
        # super().__init__(child=child) <- ERROR
        self.child = child 
        self.painter = painter
        self.size = size

    def to_json(self):
        return {
            "type": "CustomPaint",
            "painter": self.painter.to_json() if self.painter else None,
            "child": self.child.to_json() if self.child else None,
            "size": [self.size[0], self.size[1]]
        }
