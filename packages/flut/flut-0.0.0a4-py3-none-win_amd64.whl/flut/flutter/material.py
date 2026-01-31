from .widgets import Widget


def _get_engine():
    """Get the current FlutterEngine instance."""
    from flut._flut import _engine

    return _engine


class Colors:
    deepPurple = 0xFF673AB7
    green = 0xFF4CAF50
    amber = 0xFFFFC107
    blue = 0xFF2196F3
    white = 0xFFFFFFFF
    black = 0xFF000000
    red = 0xFFF44336
    grey = 0xFF9E9E9E
    grey400 = 0xFFBDBDBD
    grey500 = 0xFF9E9E9E
    grey600 = 0xFF757575
    blueGrey = 0xFF607D8B
    transparent = 0x00000000


class ColorScheme:
    def __init__(self, seedColor=None, inversePrimary=None):
        self.seedColor = seedColor
        self.inversePrimary = inversePrimary

    @staticmethod
    def fromSeed(seedColor):
        return ColorScheme(seedColor=seedColor)

    def to_json(self):
        return {"seedColor": self.seedColor}


class TextTheme:
    def __init__(self, headlineMedium=None):
        self.headlineMedium = headlineMedium


class _ThemeColorRef:
    def __init__(self, name: str):
        self.name = name

    def to_json(self):
        # Protocol value: Dart resolves this using Theme.of(context).colorScheme.<name>
        return {"ref": f"theme.colorScheme.{self.name}"}


class _ThemeTextStyleRef:
    def __init__(self, name: str):
        self.name = name

    def to_json(self):
        # Protocol value: Dart resolves this using Theme.of(context).textTheme.<name>
        return {"ref": f"theme.textTheme.{self.name}"}


class ThemeData:
    def __init__(self, colorScheme=None, useMaterial3=True):
        self.colorScheme = colorScheme
        self.useMaterial3 = useMaterial3
        # Keep a real-looking API surface: Theme.of(context).textTheme.headlineMedium
        # This resolves on the Dart side using the actual Flutter Theme.
        self.textTheme = TextTheme(headlineMedium=_ThemeTextStyleRef("headlineMedium"))

    def to_json(self):
        return {
            "colorScheme": self.colorScheme.to_json() if self.colorScheme else None,
            "useMaterial3": self.useMaterial3,
        }


class Theme:
    @staticmethod
    def of(context):
        # Dart owns the real BuildContext/Theme. If Dart provides a minimal context
        # snapshot (via FFI request payload), prefer those real-time values.
        inverse_primary = None
        try:
            inverse_primary = (
                (context or {})
                .get("theme", {})
                .get("colorScheme", {})
                .get("inversePrimary")
            )
        except Exception:
            inverse_primary = None

        scheme = ColorScheme()
        scheme.inversePrimary = (
            inverse_primary
            if isinstance(inverse_primary, int)
            else _ThemeColorRef("inversePrimary")
        )
        return ThemeData(colorScheme=scheme)


class MaterialApp(Widget):
    def __init__(self, home=None, title="Flutter Python", theme=None):
        super().__init__()
        self.home = home
        self.title = title
        self.theme = theme

    def to_json(self):
        return {
            "type": "MaterialApp",
            "title": self.title,
            "theme": self.theme.to_json() if self.theme else None,
            "home": self.home.to_json() if self.home else None,
        }


class Scaffold(Widget):
    def __init__(self, body=None, appBar=None, floatingActionButton=None):
        super().__init__()
        self.body = body
        self.appBar = appBar
        self.floatingActionButton = floatingActionButton

    def to_json(self):
        return {
            "type": "Scaffold",
            "body": self.body.to_json() if self.body else None,
            "appBar": self.appBar.to_json() if self.appBar else None,
            "floatingActionButton": (
                self.floatingActionButton.to_json()
                if self.floatingActionButton
                else None
            ),
        }


class AppBar(Widget):
    def __init__(self, title=None, backgroundColor=None):
        super().__init__()
        self.title = title
        self.backgroundColor = backgroundColor

    def to_json(self):
        background = self.backgroundColor
        if hasattr(background, "to_json"):
            background = background.to_json()
        return {
            "type": "AppBar",
            "title": self.title.to_json() if self.title else None,
            "backgroundColor": background,
        }


class FloatingActionButton(Widget):
    def __init__(self, child=None, onPressed=None, tooltip=None):
        super().__init__()
        self.child = child
        self.onPressed = onPressed
        self.tooltip = tooltip

    def to_json(self):
        action_id = None
        if self.onPressed:
            action_id = _get_engine().register_action(self._flut_id, 0, self.onPressed)
        return {
            "type": "FloatingActionButton",
            "child": self.child.to_json() if self.child else None,
            "tooltip": self.tooltip,
            "onPressedId": action_id,
        }


class Icons:
    # These codepoints must match Flutter's actual Icons.* codepoints
    # See https://api.flutter.dev/flutter/material/Icons-class.html
    send = 0xE571
    arrow_upward = 0xE0A0
    add = 0xE047
    refresh = 0xE4FC
    schedule = 0xEBCC  # timer/clock icon
    speed = 0xE01B  # speedometer icon


class ElevatedButton(Widget):
    def __init__(self, child, onPressed=None):
        super().__init__()
        self.child = child
        self.onPressed = onPressed

    def to_json(self):
        onPressedId = None
        if self.onPressed:
            onPressedId = _get_engine().register_action(
                self._flut_id, 0, self.onPressed
            )

        return {
            "type": "ElevatedButton",
            "child": self.child.to_json() if self.child else None,
            "onPressedId": onPressedId,
        }
