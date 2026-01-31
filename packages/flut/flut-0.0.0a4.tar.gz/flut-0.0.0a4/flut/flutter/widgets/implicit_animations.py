from .framework import Widget


class AnimatedOpacity(Widget):
    def __init__(self, opacity=1.0, duration=300, child=None):
        """
        opacity: float, 0.0 to 1.0
        duration: int, milliseconds
        child: Widget
        """
        self.opacity = opacity
        self.duration = duration
        self.child = child

    def to_json(self):
        return {
            "type": "AnimatedOpacity",
            "opacity": self.opacity,
            "duration": self.duration,
            "child": self.child.to_json() if self.child else None,
        }
