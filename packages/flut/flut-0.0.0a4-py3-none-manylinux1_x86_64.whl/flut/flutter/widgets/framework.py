from typing import Generic, Optional, TypeVar
from flut._flut_runtime import generate_flut_id
        

def _get_engine():
    """Get the current FlutterEngine instance."""
    from flut._flut import _engine
    return _engine


# =============================================================================
# BuildContext - Abstract interface for accessing theme, media query, etc.
# =============================================================================

class BuildContext:
    """Abstract BuildContext interface matching Flutter's BuildContext.
    
    In Flutter, BuildContext provides access to:
    - Theme.of(context)
    - MediaQuery.of(context)
    - Navigator.of(context)
    - Other inherited widgets
    
    This is the interface that widgets use. The actual implementation
    is FlutBuildContext which holds the captured context data from Dart.
    """
    
    def get(self, key, default=None):
        """Get a value from the context by key."""
        raise NotImplementedError


class FlutBuildContext(BuildContext):
    """Flut's implementation of BuildContext.
    
    This holds the context snapshot captured from Dart during builds.
    The context is a dict containing theme, colorScheme, etc.
    """
    
    def __init__(self, data: dict = None):
        self._data = data or {}
    
    def get(self, key, default=None):
        """Get a value from the context by key."""
        return self._data.get(key, default)
    
    @property
    def theme(self):
        """Access theme data."""
        return self._data.get("theme", {})
    
    @property
    def raw(self):
        """Access the raw context dict for backward compatibility."""
        return self._data
    
    def __getitem__(self, key):
        return self._data[key]
    
    def __contains__(self, key):
        return key in self._data


class FlutObject:
    """Base class for all flut objects."""

    def __init__(self):
        self._flut_id = generate_flut_id()

class Widget(FlutObject):
    """Base class for all widgets. Widgets are immutable configurations."""

    def __init__(self):
        super().__init__()

    def to_json(self):
        raise NotImplementedError


class StatelessWidget(Widget):
    """A widget that does not have mutable state."""
    
    def __init__(self, key=None):
        super().__init__()
    
    def build(self, context):
        raise NotImplementedError

    def to_json(self):
        # Register ourselves so Dart can call build_widget later
        _get_engine().state_registry[self._flut_id] = self
        return {
            "type": "PythonStatelessWidget",
            "id": self._flut_id,
            "className": self.__class__.__name__,
        }


TWidget = TypeVar("TWidget", bound="StatefulWidget")


class State(Generic[TWidget]):
    """Mutable state for a StatefulWidget. Lives in state_registry by ID."""
    
    def __init__(self):
        self._flut_widget: Optional[TWidget] = None
        self._flut_id: Optional[str] = None
        self._flut_last_build_context: BuildContext = FlutBuildContext({})

    @property
    def widget(self) -> TWidget:
        return self._flut_widget

    @property
    def context(self) -> BuildContext:
        return self._flut_last_build_context

    def initState(self):
        pass

    def build(self, context: BuildContext):
        raise NotImplementedError

    def setState(self, fn):
        """Update state and queue update for Dart."""
        if fn:
            fn()
        
        # Notify Dart that this widget needs to rebuild
        engine = _get_engine()
        if engine:
            engine.notify_set_state(self._flut_id)


class StatefulWidget(Widget):
    """A widget that has mutable state managed by Dart's Element tree."""
    
    def __init__(self, key=None):
        super().__init__()
        self._flut_state = None

    def createState(self):
        raise NotImplementedError

    def to_json(self):
        # Create state if needed and register it
        if self._flut_state is None:
            self._flut_state = self.createState()
            self._flut_state._flut_widget = self
            self._flut_state._flut_id = self._flut_id
            self._flut_state.initState()
        
        # Register the State object globally so Dart can find it
        _get_engine().state_registry[self._flut_id] = self._flut_state
        
        return {
            "type": "PythonStatefulWidget",
            "id": self._flut_id,
            "className": self.__class__.__name__,
        }
