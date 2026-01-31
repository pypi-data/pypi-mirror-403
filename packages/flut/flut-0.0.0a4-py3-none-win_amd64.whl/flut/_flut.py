import os
import sys
import json
import asyncio


# The single global engine instance - all other modules only need this
_engine = None


def get_engine():
    """Get the current FlutterEngine instance."""
    return _engine


class FlutterEngine:
    """Flutter Engine built on top of FlutNative."""

    def __init__(self, native, root_widget):
        global _engine
        
        self._native = native
        self._root_widget = root_widget
        self._dart_call_fn = None
        self._notify_set_state_fn = None
        self._action_context = None
        self._event_loop = None  # Stored when running in async mode

        # Registries - all owned by the engine
        self.action_registry = {}       # Maps action IDs → Python callbacks
        self.state_registry = {}        # Maps widget IDs → State objects
        self.controller_registry = {}   # Maps controller IDs → Controller instances
        self.focus_node_registry = {}   # Maps focus node IDs → FocusNode instances

        # Set global engine reference
        _engine = self

    def call_dart(self, call_type, data):
        """Call Dart synchronously. Returns response dict or None.
        
        Safe to call from any action callback since all actions now run on
        the UI thread (main thread).
        """
        if self._dart_call_fn is None:
            return None
        
        return self._dart_call_fn(call_type, data)

    def _setup_dart_call_callback(self, callback_addr):
        """Set up FFI callback for calling Dart via native layer."""
        self._dart_call_fn = self._native.setup_call_dart(callback_addr)

    def _setup_set_state_notification(self, callback_addr):
        """Set up FFI callback for notifying Dart via native layer."""
        self._notify_set_state_fn = self._native.setup_notify_dart(callback_addr)

    def notify_set_state(self, state_id):
        """Send set state notification to Dart."""
        if self._notify_set_state_fn is not None:
            try:
                ids_json = json.dumps(state_id)
                self._notify_set_state_fn(ids_json.encode("utf-8"))
            except Exception as e:
                print(f"Error notifying Dart: {e}")

    def register_action(self, widget_id, slot: int, callback) -> str:
        """Register an action callback that Dart can invoke.
        
        Args:
            widget_id: The widget's _flut_id (stable across rebuilds)
            slot: Action slot number (e.g., 0=tap, 1=panStart, 2=panUpdate)
            callback: The Python callback to invoke
        
        Returns:
            The action ID (currently string, future: int)
        """
        action_id = f"{widget_id}:{slot}"
        self.action_registry[action_id] = callback
        return action_id

    def confirm_action(self, action_id: str):
        """Confirm an action was executed, removing it from the registry."""
        self.action_registry.pop(action_id, None)

    def initialize(self):
        self._native.initialize()

    def run(self, assets_path, width, height):
        self._native.run(self._handle_method_call, assets_path, width, height)

    async def run_async(self, assets_path, width, height, loop=None):
        self._event_loop = loop or asyncio.get_running_loop()
        await self._native.run_async(
            self._handle_method_call, assets_path, width, height, self._event_loop
        )

    def shutdown(self):
        self._native.shutdown()

    def _process_single_action(self, action_data):
        """Process a single action event from Dart."""
        action_id = action_data.get("id")
        self._action_context = action_data.get("context") or None

        flut_controllers = action_data.get("controllers")
        if flut_controllers:
            for ctrl_id, ctrl_text in flut_controllers.items():
                ctrl = self.controller_registry.get(ctrl_id)
                if ctrl and hasattr(ctrl, "_flut_text"):
                    ctrl._flut_text = ctrl_text

        if action_id in self.action_registry:
            cb = self.action_registry[action_id]
            value = action_data.get("value")
            
            # Prepare arguments
            if value is not None:
                args = (value,)
            elif action_data.get("globalPosition") is not None:
                details = {
                    "globalPosition": action_data.get("globalPosition"),
                    "localPosition": action_data.get("localPosition"),
                    "windowWidth": action_data.get("windowWidth"),
                    "windowHeight": action_data.get("windowHeight"),
                }
                delta = action_data.get("delta")
                if delta is not None:
                    details["delta"] = delta
                args = (details,)
            else:
                args = ()
            
            # Run callback
            # Note: We don't auto-delete actions because repeatable events like
            # onPanUpdate fire multiple times. Cleanup is handled when widgets
            # rebuild and register new actions (old IDs become orphaned but the
            # memory impact is minimal for typical apps).
            if asyncio.iscoroutinefunction(cb):
                # Async callback - schedule on stored event loop
                if self._event_loop is not None:
                    self._event_loop.create_task(cb(*args))
                else:
                    print(f"Warning: async callback for {action_id} ignored (no event loop - use run_app_async)")
            else:
                cb(*args)
        else:
            print(f"No callback found for {action_id}")

        self._action_context = None

    def _handle_method_call(self, request_json):
        """
        Generic handler for method calls from Dart.
        request_json is a dict like {"type": "...", "data": ...}
        Returns JSON bytes or None.
        """
        try:
            req_type = request_json.get("type")
            data = request_json.get("data") or {}

            if req_type == "widget_build":
                # Build a widget by ID
                from flut.flutter.widgets.framework import FlutBuildContext
                widget_id = data.get("id")
                context_data = data.get("context") or {}
                context = FlutBuildContext(context_data)
                
                # If id is None, return root widget (initial tree request)
                if widget_id is None:
                    if self._root_widget is not None:
                        resp = self._root_widget.to_json()
                        return json.dumps(resp).encode("utf-8")
                    print("Warning: No root widget set")
                    return json.dumps(None).encode("utf-8")
                
                # If id is provided, look up in state_registry
                obj = self.state_registry.get(widget_id)
                if obj is not None:
                    # State or StatelessWidget - call build()
                    if hasattr(obj, "_flut_last_build_context"):
                        obj._flut_last_build_context = context
                    built = obj.build(context)
                    subtree_json = built.to_json() if built else None
                    return json.dumps(subtree_json).encode("utf-8")
                
                # ID provided but not found - warning and return empty
                print(f"Warning: Widget '{widget_id}' not found in state_registry")
                return json.dumps(None).encode("utf-8")

            elif req_type == "register_dart_callback":
                # Dart is registering its callback address for Python to call
                callback_addr = data.get("callback_addr")
                if callback_addr:
                    self._setup_dart_call_callback(callback_addr)
                    return json.dumps({"success": True}).encode("utf-8")
                return json.dumps({"error": "No callback_addr"}).encode("utf-8")

            elif req_type == "register_set_state_callback":
                # Dart is registering its notification callback address
                callback_addr = data.get("callback_addr")
                if callback_addr:
                    self._setup_set_state_notification(callback_addr)
                    return json.dumps({"success": True}).encode("utf-8")
                return json.dumps({"error": "No callback_addr"}).encode("utf-8")

            elif req_type == "key_event":
                # Synchronous key event handling for FocusNode.onKeyEvent
                from flut.flutter.widgets.basic import KeyEvent
                focus_node_id = data.get("focusNodeId")
                key_data = data.get("keyData", {})
                self._action_context = data.get("context") or None

                # Sync controllers
                flut_controllers = data.get("controllers")
                if flut_controllers:
                    for ctrl_id, ctrl_text in flut_controllers.items():
                        ctrl = self.controller_registry.get(ctrl_id)
                        if ctrl and hasattr(ctrl, "_flut_text"):
                            ctrl._flut_text = ctrl_text

                # Find the FocusNode and call its onKeyEvent
                result = "ignored"
                focus_node = self.focus_node_registry.get(focus_node_id)
                if focus_node and focus_node.onKeyEvent:
                    key_event = KeyEvent(key_data)
                    result = focus_node.onKeyEvent(key_event) or "ignored"

                self._action_context = None
                return json.dumps({"result": result}).encode("utf-8")

            elif req_type == "action":
                # Direct action processing on main thread
                # All actions now use this path (no more event queue)
                self._process_single_action(data)
                return json.dumps({"status": "ok"}).encode("utf-8")

        except Exception as e:
            import traceback

            traceback.print_exc()
            print(f"Error handling method call: {e}")
            return None


def _get_native_and_assets(assets_path):
    """Get native implementation and resolve assets path for current platform."""
    if os.name == "nt":
        from ._flut_windows import FlutWindowsNative
        native = FlutWindowsNative()
        platform_name = "Flutter via Python - Using flutter_windows.dll"
        build_cmd = "flutter build bundle"
    elif sys.platform == "darwin":
        from ._flut_macos import FlutMacOSNative
        native = FlutMacOSNative()
        platform_name = "Flutter via Python - Using FlutterMacOS.framework"
        build_cmd = "cd flutter && flutter build macos"
    elif sys.platform.startswith("linux"):
        from ._flut_linux import FlutLinuxNative
        native = FlutLinuxNative()
        platform_name = "Flutter via Python - Using libflutter_linux_gtk.so"
        build_cmd = "cd flut/.flutter && flutter build linux"
    else:
        raise NotImplementedError(f"Platform {sys.platform} not supported yet.")

    if assets_path is None:
        assets_path = native.get_default_assets_path()
        if len(sys.argv) > 1:
            assets_path = sys.argv[1]

    if not os.path.exists(assets_path):
        print(f"ERROR: Assets not found at: {assets_path}")
        print()
        print("Build your Flutter app first:")
        print(f"  {build_cmd}")
        return None, None

    print("=" * 60)
    print(platform_name)
    print("=" * 60)
    print()
    print(f"Assets: {assets_path}")
    print()

    return native, assets_path


def run_app(widget, assets_path=None, width=800, height=600):
    """Run the app (sync mode)."""
    native, assets_path = _get_native_and_assets(assets_path)
    if native is None:
        return None

    engine = FlutterEngine(native, widget)
    engine.initialize()

    try:
        engine.run(assets_path, width, height)
    finally:
        engine.shutdown()

    return engine


async def run_app_async(widget, assets_path=None, width=800, height=600):
    """
    Run the app with asyncio integration (Windows, Linux, and macOS).
    
    Integrates platform's UI loop with asyncio:
    - Windows: Win32 messages + IOCP via MsgWaitForMultipleObjectsEx
    - Linux: GTK events + epoll via eventfd + g_unix_fd_add
    - macOS: CFRunLoop + kqueue via pipe + CFFileDescriptor
    
    Single-threaded, event-driven.
    
    Usage:
        async def main():
            # Start background async tasks
            asyncio.create_task(my_background_task())
            
            # Run Flutter app (this drives the event loop)
            await run_app_async(MyWidget())
        
        asyncio.run(main())
    
    Args:
        widget: The root widget for the app.
        assets_path: Path to flutter_assets (auto-detected if None).
        width: Initial window width.
        height: Initial window height.
    
    Returns:
        The FlutterEngine instance after the app closes.
    """
    native, assets_path = _get_native_and_assets(assets_path)
    if native is None:
        return None

    engine = FlutterEngine(native, widget)
    engine.initialize()

    try:
        await engine.run_async(assets_path, width, height)
    finally:
        engine.shutdown()

    return engine
