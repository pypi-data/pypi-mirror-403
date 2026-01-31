import uuid

from .framework import FlutObject, Widget


def _get_engine():
    """Get the current FlutterEngine instance."""
    from flut._flut import _engine

    return _engine


class KeyEventResult:
    """Result of handling a key event, matching Flutter's KeyEventResult."""

    handled = "handled"  # Event was handled, don't propagate
    ignored = "ignored"  # Event was not handled, propagate to other handlers
    skipRemainingHandlers = (
        "skipRemainingHandlers"  # Skip remaining handlers but don't mark as handled
    )


class LogicalKeyboardKey:
    """Logical keyboard keys, matching Flutter's LogicalKeyboardKey."""

    enter = "Enter"
    escape = "Escape"
    backspace = "Backspace"
    tab = "Tab"
    space = " "
    arrowUp = "Arrow Up"
    arrowDown = "Arrow Down"
    arrowLeft = "Arrow Left"
    arrowRight = "Arrow Right"


class KeyEvent:
    """Represents a keyboard event from Flutter."""

    def __init__(self, data: dict):
        self.key = data.get("key", "")
        self.is_key_down = data.get("isKeyDown", False)
        self.is_shift_pressed = data.get("isShiftPressed", False)
        self.is_control_pressed = data.get("isControlPressed", False)
        self.is_alt_pressed = data.get("isAltPressed", False)
        self.is_meta_pressed = data.get("isMetaPressed", False)


class FocusNode(FlutObject):
    """A node in the focus tree that can receive keyboard events.

    Matches Flutter's FocusNode. Can be passed to TextField.focusNode.
    The onKeyEvent callback receives KeyEvent and should return KeyEventResult.

    Example:
        def handle_key(event):
            if event.key == LogicalKeyboardKey.enter and not event.is_shift_pressed:
                on_submit()
                return KeyEventResult.handled
            return KeyEventResult.ignored

        focus_node = FocusNode(onKeyEvent=handle_key)
        TextField(focusNode=focus_node, ...)
    """

    def __init__(self, onKeyEvent=None):
        super().__init__()
        self.onKeyEvent = onKeyEvent

    def _register(self):
        """Register focus node so Dart can invoke key events."""
        _get_engine().focus_node_registry[self._flut_id] = self

    def to_json(self):
        return {
            "id": self._flut_id,
            "hasOnKeyEvent": self.onKeyEvent is not None,
        }


class FlutTextEditingController(FlutObject):
    """Flut's controller for TextField that holds and manages text state.

    Values sync from Dart to Python only when an action is triggered.
    This is the standard controller - use TextEditingController if you
    need real-time reads outside action callbacks.
    """

    def __init__(self, text=""):
        super().__init__()
        self._flut_text = text

    @property
    def text(self):
        return self._flut_text

    @text.setter
    def text(self, value):
        self._flut_text = value

    def clear(self):
        self._flut_text = ""

    def _register(self):
        """Register controller so Dart can sync values back."""
        _get_engine().controller_registry[self._flut_id] = self

    def to_json(self):
        return {
            "id": self._flut_id,
            "text": self._flut_text,
        }


class TextEditingController(FlutObject):
    """Controller that can call Dart for the current text value.

    Unlike FlutTextEditingController (which syncs only on actions), this controller
    CAN make an FFI call to Dart when you read the `text` property.

    However, during action callbacks (which run on a background thread), the
    controller uses its synced `_flut_text` value instead of calling Dart, because
    the Dart callback (isolateLocal) cannot be called from other threads.

    The action payload includes all controller values, which are synced to `_flut_text`
    before the callback runs. This ensures the callback has fresh values without
    needing to call Dart.

    Trade-offs:
    - Pro: Fresh value from Dart when called from main thread
    - Pro: Works correctly in action callbacks (uses synced value)
    - Con: FFI call overhead on `.text` access from main thread
    - Con: Requires Dart callback to be registered for main thread calls

    Use this when you need timer-based auto-save or similar patterns.
    For most cases, prefer the regular FlutTextEditingController.
    """

    def __init__(self, text=""):
        super().__init__()
        self._flut_text = text  # Synced value from action payload

    @property
    def text(self):
        """Get the current text value.

        Returns the synced value from the most recent action payload.
        This is safe to call from any thread.

        Note: If you need real-time calls to Dart (outside of action callbacks),
        this will attempt an FFI call but falls back to the synced value.
        """
        # Try to call Dart for real-time value (only works on main thread)
        engine = _get_engine()
        if engine:
            result = engine.call_dart("get_controller_text", {"id": self._flut_id})
            if result is not None and "text" in result:
                return result["text"]
        # Use synced value (always available, safe from any thread)
        return self._flut_text

    @text.setter
    def text(self, value):
        """Set text - this will be sent to Dart on next build."""
        self._flut_text = value

    def clear(self):
        self._flut_text = ""

    def _register(self):
        """Register controller so Dart can sync values back."""
        _get_engine().controller_registry[self._flut_id] = self

    def to_json(self):
        return {
            "id": self._flut_id,
            "text": self._flut_text,
        }


class MainAxisAlignment:
    center = "center"
    start = "start"
    end = "end"
    spaceBetween = "spaceBetween"
    spaceAround = "spaceAround"
    spaceEvenly = "spaceEvenly"


class CrossAxisAlignment:
    center = "center"
    start = "start"
    end = "end"
    stretch = "stretch"
    baseline = "baseline"


class ScrollMode:
    auto = "auto"
    always = "always"
    hidden = "hidden"
    adaptive = "adaptive"


class FontWeight:
    bold = "bold"
    normal = "normal"
    w100 = "w100"
    w200 = "w200"
    w300 = "w300"
    w400 = "w400"
    w500 = "w500"
    w600 = "w600"
    w700 = "w700"
    w800 = "w800"
    w900 = "w900"


class TextStyle:
    def __init__(
        self,
        fontSize=None,
        fontWeight=None,
        color=None,
        fontFamily=None,
        height=None,
    ):
        self.fontSize = fontSize
        self.fontWeight = fontWeight
        self.color = color
        self.fontFamily = fontFamily
        self.height = height

    def to_json(self):
        return {
            "fontSize": self.fontSize,
            "fontWeight": self.fontWeight,
            "color": self.color,
            "fontFamily": self.fontFamily,
            "height": self.height,
        }


class EdgeInsets:
    def __init__(self, left=0, top=0, right=0, bottom=0):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom

    @staticmethod
    def all(value):
        return EdgeInsets(value, value, value, value)

    @staticmethod
    def symmetric(vertical=0, horizontal=0):
        return EdgeInsets(horizontal, vertical, horizontal, vertical)

    @staticmethod
    def only(left=0, top=0, right=0, bottom=0):
        return EdgeInsets(left, top, right, bottom)

    def to_json(self):
        return {
            "left": self.left,
            "top": self.top,
            "right": self.right,
            "bottom": self.bottom,
        }


class BorderSide:
    def __init__(self, color=0xFF000000, width=1.0):
        self.color = color
        self.width = width

    def to_json(self):
        return {"color": self.color, "width": self.width}


class Border:
    def __init__(self, left=None, top=None, right=None, bottom=None):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom

    @staticmethod
    def all(width=1.0, color=0xFF000000):
        side = BorderSide(color, width)
        return Border(side, side, side, side)

    def to_json(self):
        return {
            "left": self.left.to_json() if self.left else None,
            "top": self.top.to_json() if self.top else None,
            "right": self.right.to_json() if self.right else None,
            "bottom": self.bottom.to_json() if self.bottom else None,
        }


class BorderRadius:
    def __init__(self, topLeft=0, topRight=0, bottomLeft=0, bottomRight=0):
        self.topLeft = topLeft
        self.topRight = topRight
        self.bottomLeft = bottomLeft
        self.bottomRight = bottomRight

    @staticmethod
    def circular(radius):
        return BorderRadius(radius, radius, radius, radius)

    @staticmethod
    def all(radius):
        return BorderRadius.circular(radius)

    def to_json(self):
        return {
            "topLeft": self.topLeft,
            "topRight": self.topRight,
            "bottomLeft": self.bottomLeft,
            "bottomRight": self.bottomRight,
        }


class Text(Widget):
    def __init__(
        self,
        data,
        style=None,
        fontSize=None,
        selectable=False,
        maxLines=None,
        overflow=None,
    ):
        super().__init__()
        self.data = data
        self.style = style
        self.fontSize = fontSize
        self.selectable = selectable
        self.maxLines = maxLines
        self.overflow = overflow

    def to_json(self):
        style = self.style
        if style is None:
            if self.fontSize is None:
                return {
                    "type": "Text",
                    "data": str(self.data),
                    "selectable": self.selectable,
                    "maxLines": self.maxLines,
                    "overflow": self.overflow,
                }
            style = {"fontSize": self.fontSize}
        elif hasattr(style, "to_json"):
            style = style.to_json()
        return {
            "type": "Text",
            "data": str(self.data),
            "style": style,
            "selectable": self.selectable,
            "maxLines": self.maxLines,
            "overflow": self.overflow,
        }


class Center(Widget):
    def __init__(self, child):
        super().__init__()
        self.child = child

    def to_json(self):
        return {"type": "Center", "child": self.child.to_json() if self.child else None}


class Expanded(Widget):
    def __init__(self, child, flex=1):
        super().__init__()
        self.child = child
        self.flex = flex

    def to_json(self):
        return {
            "type": "Expanded",
            "flex": self.flex,
            "child": self.child.to_json() if self.child else None,
        }


class Flexible(Widget):
    def __init__(self, child, flex=1, fit=None):
        super().__init__()
        self.child = child
        self.flex = flex
        self.fit = fit

    def to_json(self):
        return {
            "type": "Flexible",
            "flex": self.flex,
            "fit": self.fit,
            "child": self.child.to_json() if self.child else None,
        }


class SizedBox(Widget):
    def __init__(self, width=None, height=None, child=None):
        super().__init__()
        self.width = width
        self.height = height
        self.child = child

    def to_json(self):
        return {
            "type": "SizedBox",
            "width": self.width,
            "height": self.height,
            "child": self.child.to_json() if self.child else None,
        }


class Container(Widget):
    def __init__(
        self,
        child=None,
        padding=None,
        margin=None,
        color=None,
        width=None,
        height=None,
        decoration=None,
        alignment=None,
    ):
        super().__init__()
        self.child = child
        self.padding = padding
        self.margin = margin
        self.color = color
        self.width = width
        self.height = height
        self.decoration = decoration
        self.alignment = alignment

    def to_json(self):
        return {
            "type": "Container",
            "child": self.child.to_json() if self.child else None,
            "padding": self.padding.to_json() if self.padding else None,
            "margin": self.margin.to_json() if self.margin else None,
            "color": self.color,
            "width": self.width,
            "height": self.height,
            "decoration": self.decoration.to_json() if self.decoration else None,
            "alignment": self.alignment,
        }


class BoxDecoration:
    def __init__(
        self,
        color=None,
        border=None,
        borderRadius=None,
    ):
        self.color = color
        self.border = border
        self.borderRadius = borderRadius

    def to_json(self):
        border_radius = self.borderRadius
        if isinstance(border_radius, (int, float)):
            border_radius = BorderRadius.circular(border_radius)
        return {
            "color": self.color,
            "border": self.border.to_json() if self.border else None,
            "borderRadius": border_radius.to_json() if border_radius else None,
        }


class Column(Widget):
    def __init__(
        self,
        children,
        mainAxisAlignment=None,
        crossAxisAlignment=None,
        spacing=None,
    ):
        super().__init__()
        self.children = children
        self.mainAxisAlignment = mainAxisAlignment
        self.crossAxisAlignment = crossAxisAlignment
        self.spacing = spacing

    def to_json(self):
        return {
            "type": "Column",
            "mainAxisAlignment": self.mainAxisAlignment,
            "crossAxisAlignment": self.crossAxisAlignment,
            "spacing": self.spacing,
            "children": [c.to_json() for c in self.children],
        }


class Row(Widget):
    def __init__(
        self,
        children,
        mainAxisAlignment=None,
        crossAxisAlignment=None,
        spacing=None,
    ):
        super().__init__()
        self.children = children
        self.mainAxisAlignment = mainAxisAlignment
        self.crossAxisAlignment = crossAxisAlignment
        self.spacing = spacing

    def to_json(self):
        return {
            "type": "Row",
            "mainAxisAlignment": self.mainAxisAlignment,
            "crossAxisAlignment": self.crossAxisAlignment,
            "spacing": self.spacing,
            "children": [c.to_json() for c in self.children],
        }


class Stack(Widget):
    def __init__(self, children):
        super().__init__()
        self.children = children

    def to_json(self):
        return {
            "type": "Stack",
            "children": [c.to_json() for c in self.children],
        }


class Positioned(Widget):
    def __init__(
        self,
        child,
        left=None,
        top=None,
        right=None,
        bottom=None,
        width=None,
        height=None,
    ):
        super().__init__()
        self.child = child
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom
        self.width = width
        self.height = height

    def to_json(self):
        return {
            "type": "Positioned",
            "left": self.left,
            "top": self.top,
            "right": self.right,
            "bottom": self.bottom,
            "width": self.width,
            "height": self.height,
            "child": self.child.to_json() if self.child else None,
        }


class ListView(Widget):
    def __init__(
        self,
        children,
        padding=None,
        spacing=None,
        reverse=False,
    ):
        super().__init__()
        self.children = children
        self.padding = padding
        self.spacing = spacing
        self.reverse = reverse

    def to_json(self):
        return {
            "type": "ListView",
            "padding": self.padding.to_json() if self.padding else None,
            "spacing": self.spacing,
            "reverse": self.reverse,
            "children": [c.to_json() for c in self.children],
        }


class SingleChildScrollView(Widget):
    def __init__(self, child, padding=None, scrollDirection=None):
        super().__init__()
        self.child = child
        self.padding = padding
        self.scrollDirection = scrollDirection

    def to_json(self):
        return {
            "type": "SingleChildScrollView",
            "padding": self.padding.to_json() if self.padding else None,
            "scrollDirection": self.scrollDirection,
            "child": self.child.to_json() if self.child else None,
        }


class TextField(Widget):
    def __init__(
        self,
        controller=None,
        focusNode=None,
        onChanged=None,
        onSubmitted=None,
        readOnly=False,
        maxLines=1,
        minLines=None,
        decoration=None,
        style=None,
    ):
        super().__init__()
        self.controller = controller
        self.focusNode = focusNode
        self.onChanged = onChanged
        self.onSubmitted = onSubmitted
        self.readOnly = readOnly
        self.maxLines = maxLines
        self.minLines = minLines
        self.decoration = decoration
        self.style = style

    def to_json(self):
        engine = _get_engine()
        on_changed_id = None
        on_submitted_id = None
        if self.onChanged:
            on_changed_id = engine.register_action(self._flut_id, 0, self.onChanged)
        if self.onSubmitted:
            on_submitted_id = engine.register_action(self._flut_id, 1, self.onSubmitted)

        # Register controller when TextField is built
        if self.controller:
            self.controller._register()

        # Register focus node when TextField is built
        if self.focusNode:
            self.focusNode._register()

        # Get controller text - works with both FlutTextEditingController and TextEditingController
        controller_text = None
        if self.controller:
            if hasattr(self.controller, "_flut_text"):
                controller_text = self.controller._flut_text
            elif hasattr(self.controller, "_flut_initial_text"):
                controller_text = self.controller._flut_initial_text

        return {
            "type": "TextField",
            "id": self._flut_id,
            "controllerId": self.controller._flut_id if self.controller else None,
            "controllerText": controller_text,
            "focusNode": self.focusNode.to_json() if self.focusNode else None,
            "onChangedId": on_changed_id,
            "onSubmittedId": on_submitted_id,
            "readOnly": self.readOnly,
            "maxLines": self.maxLines,
            "minLines": self.minLines,
            "decoration": self.decoration.to_json() if self.decoration else None,
            "style": self.style.to_json() if self.style else None,
        }


class InputDecoration:
    def __init__(
        self,
        hintText=None,
        border=None,
        filled=False,
        fillColor=None,
        contentPadding=None,
    ):
        self.hintText = hintText
        self.border = border
        self.filled = filled
        self.fillColor = fillColor
        self.contentPadding = contentPadding

    def to_json(self):
        return {
            "hintText": self.hintText,
            "border": self.border,
            "filled": self.filled,
            "fillColor": self.fillColor,
            "contentPadding": (
                self.contentPadding.to_json() if self.contentPadding else None
            ),
        }


class GestureDetector(Widget):
    def __init__(self, child=None, onTap=None, onPanStart=None, onPanUpdate=None):
        super().__init__()
        self.child = child
        self.onTap = onTap
        self.onPanStart = onPanStart
        self.onPanUpdate = onPanUpdate

    def to_json(self):
        engine = _get_engine()
        on_tap_id = None
        on_pan_start_id = None
        on_pan_update_id = None
        if self.onTap:
            on_tap_id = engine.register_action(self._flut_id, 0, self.onTap)
        if self.onPanStart:
            on_pan_start_id = engine.register_action(self._flut_id, 1, self.onPanStart)
        if self.onPanUpdate:
            on_pan_update_id = engine.register_action(
                self._flut_id, 2, self.onPanUpdate
            )
        return {
            "type": "GestureDetector",
            "onTapId": on_tap_id,
            "onPanStartId": on_pan_start_id,
            "onPanUpdateId": on_pan_update_id,
            "child": self.child.to_json() if self.child else None,
        }


class InkWell(Widget):
    def __init__(self, child=None, onTap=None):
        super().__init__()
        self.child = child
        self.onTap = onTap

    def to_json(self):
        engine = _get_engine()
        on_tap_id = None
        if self.onTap:
            on_tap_id = engine.register_action(self._flut_id, 0, self.onTap)
        return {
            "type": "InkWell",
            "onTapId": on_tap_id,
            "child": self.child.to_json() if self.child else None,
        }


class SystemMouseCursors:
    """Common system mouse cursors."""

    basic = "basic"
    click = "click"
    text = "text"
    resizeLeftRight = "resizeLeftRight"
    resizeUpDown = "resizeUpDown"
    resizeColumn = "resizeColumn"
    resizeRow = "resizeRow"
    grab = "grab"
    grabbing = "grabbing"
    move = "move"
    forbidden = "forbidden"
    wait = "wait"


class MouseRegion(Widget):
    """Widget that tracks mouse events within its bounds."""

    def __init__(self, child=None, cursor=None, onEnter=None, onExit=None):
        super().__init__()
        self.child = child
        self.cursor = cursor
        self.onEnter = onEnter
        self.onExit = onExit

    def to_json(self):
        engine = _get_engine()
        on_enter_id = None
        on_exit_id = None
        if self.onEnter:
            on_enter_id = engine.register_action(self._flut_id, 0, self.onEnter)
        if self.onExit:
            on_exit_id = engine.register_action(self._flut_id, 1, self.onExit)
        return {
            "type": "MouseRegion",
            "cursor": self.cursor,
            "onEnterId": on_enter_id,
            "onExitId": on_exit_id,
            "child": self.child.to_json() if self.child else None,
        }


class IconButton(Widget):
    def __init__(
        self,
        icon,
        onPressed=None,
        iconColor=None,
        backgroundColor=None,
        iconSize=24,
        tooltip=None,
        disabled=False,
    ):
        super().__init__()
        self.icon = icon
        self.onPressed = onPressed
        self.iconColor = iconColor
        self.backgroundColor = backgroundColor
        self.iconSize = iconSize
        self.tooltip = tooltip
        self.disabled = disabled

    def to_json(self):
        engine = _get_engine()
        on_pressed_id = None
        if self.onPressed:
            on_pressed_id = engine.register_action(self._flut_id, 0, self.onPressed)
        return {
            "type": "IconButton",
            "icon": self.icon.to_json() if hasattr(self.icon, "to_json") else self.icon,
            "onPressedId": on_pressed_id,
            "iconColor": self.iconColor,
            "backgroundColor": self.backgroundColor,
            "iconSize": self.iconSize,
            "tooltip": self.tooltip,
            "disabled": self.disabled,
        }


class CircularProgressIndicator(Widget):
    def __init__(self, strokeWidth=4.0, color=None):
        super().__init__()
        self.strokeWidth = strokeWidth
        self.color = color

    def to_json(self):
        return {
            "type": "CircularProgressIndicator",
            "strokeWidth": self.strokeWidth,
            "color": self.color,
        }


class Divider(Widget):
    def __init__(self, height=1, thickness=1, color=None):
        super().__init__()
        self.height = height
        self.thickness = thickness
        self.color = color

    def to_json(self):
        return {
            "type": "Divider",
            "height": self.height,
            "thickness": self.thickness,
            "color": self.color,
        }


class Padding(Widget):
    def __init__(self, padding, child):
        super().__init__()
        self.padding = padding
        self.child = child

    def to_json(self):
        return {
            "type": "Padding",
            "padding": self.padding.to_json() if self.padding else None,
            "child": self.child.to_json() if self.child else None,
        }


class Align(Widget):
    def __init__(self, alignment, child):
        super().__init__()
        self.alignment = alignment
        self.child = child

    def to_json(self):
        return {
            "type": "Align",
            "alignment": self.alignment,
            "child": self.child.to_json() if self.child else None,
        }


class Alignment:
    topLeft = "topLeft"
    topCenter = "topCenter"
    topRight = "topRight"
    centerLeft = "centerLeft"
    center = "center"
    centerRight = "centerRight"
    bottomLeft = "bottomLeft"
    bottomCenter = "bottomCenter"
    bottomRight = "bottomRight"


class Icon(Widget):
    def __init__(self, codePoint, color=None, size=None):
        super().__init__()
        self.codePoint = codePoint
        self.color = color
        self.size = size

    def to_json(self):
        return {
            "type": "Icon",
            "codePoint": self.codePoint,
            "color": self.color,
            "size": self.size,
        }


class Visibility(Widget):
    def __init__(self, visible, child):
        super().__init__()
        self.visible = visible
        self.child = child

    def to_json(self):
        return {
            "type": "Visibility",
            "visible": self.visible,
            "child": self.child.to_json() if self.child else None,
        }


class Opacity(Widget):
    def __init__(self, opacity, child):
        super().__init__()
        self.opacity = opacity
        self.child = child

    def to_json(self):
        return {
            "type": "Opacity",
            "opacity": self.opacity,
            "child": self.child.to_json() if self.child else None,
        }


class ClipRRect(Widget):
    def __init__(self, borderRadius, child):
        super().__init__()
        self.borderRadius = borderRadius
        self.child = child

    def to_json(self):
        border_radius = self.borderRadius
        if isinstance(border_radius, (int, float)):
            border_radius = BorderRadius.circular(border_radius)
        return {
            "type": "ClipRRect",
            "borderRadius": border_radius.to_json() if border_radius else None,
            "child": self.child.to_json() if self.child else None,
        }


class Card(Widget):
    def __init__(self, child=None, color=None, elevation=None, margin=None):
        super().__init__()
        self.child = child
        self.color = color
        self.elevation = elevation
        self.margin = margin

    def to_json(self):
        return {
            "type": "Card",
            "child": self.child.to_json() if self.child else None,
            "color": self.color,
            "elevation": self.elevation,
            "margin": self.margin.to_json() if self.margin else None,
        }


class Spacer(Widget):
    def __init__(self, flex=1):
        super().__init__()
        self.flex = flex

    def to_json(self):
        return {"type": "Spacer", "flex": self.flex}
