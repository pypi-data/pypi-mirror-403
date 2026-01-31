import ctypes
import ctypes.util
import os
import json
import collections
import asyncio
from ctypes import (
    c_void_p,
    c_char_p,
    c_int,
    c_int16,
    c_int32,
    c_int64,
    c_size_t,
    CFUNCTYPE,
    c_double,
    c_bool,
    c_uint64,
    c_uint32,
    c_long,
)

from ._flut_native import FlutNative

# ssize_t is signed size_t (c_long on macOS 64-bit)
c_ssize_t = c_long

# Predefine all paths relative to the package directory
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PATH_FLUT = os.path.join(
    ROOT_DIR,
    ".flutter",
    "build",
    "macos",
    "Build",
    "Products",
    "Release",
    "flut.app",
)
PATH_FLUT_FRAMEWORKS = os.path.join(PATH_FLUT, "Contents", "Frameworks")
PATH_FLUT_ASSETS = os.path.join(
    PATH_FLUT_FRAMEWORKS, "App.framework", "Resources", "flutter_assets"
)
PATH_FLUTTER_FRAMEWORK = os.path.join(PATH_FLUT_FRAMEWORKS, "FlutterMacOS.framework")
PATH_FLUTTER_DYLIB = os.path.join(PATH_FLUTTER_FRAMEWORK, "FlutterMacOS")
PATH_APP_FRAMEWORK = os.path.join(PATH_FLUT_FRAMEWORKS, "App.framework")

# =============================================================================
# Objective-C Runtime via ctypes
# =============================================================================

# Load Objective-C runtime
_objc_lib = ctypes.util.find_library("objc")
if not _objc_lib:
    raise ImportError("Could not find Objective-C runtime library")
libobjc = ctypes.CDLL(_objc_lib)

# objc_getClass
libobjc.objc_getClass.argtypes = [c_char_p]
libobjc.objc_getClass.restype = c_void_p

# sel_registerName
libobjc.sel_registerName.argtypes = [c_char_p]
libobjc.sel_registerName.restype = c_void_p

# objc_msgSend - we'll cast it for different signatures
objc_msgSend = libobjc.objc_msgSend

# class_addMethod
libobjc.class_addMethod.argtypes = [c_void_p, c_void_p, c_void_p, c_char_p]
libobjc.class_addMethod.restype = c_bool

# objc_allocateClassPair
libobjc.objc_allocateClassPair.argtypes = [c_void_p, c_char_p, c_size_t]
libobjc.objc_allocateClassPair.restype = c_void_p

# objc_registerClassPair
libobjc.objc_registerClassPair.argtypes = [c_void_p]
libobjc.objc_registerClassPair.restype = None


def objc_class(name):
    """Get an Objective-C class by name."""
    return libobjc.objc_getClass(name.encode("utf-8"))


def sel(name):
    """Get a selector by name."""
    return libobjc.sel_registerName(name.encode("utf-8"))


def msg(obj, selector, *args, restype=c_void_p, argtypes=None):
    """Send a message to an Objective-C object."""
    if argtypes is None:
        argtypes = [c_void_p, c_void_p] + [c_void_p] * len(args)

    send = ctypes.cast(objc_msgSend, ctypes.CFUNCTYPE(restype, *argtypes))
    return send(obj, sel(selector), *args)


# IMP type for method implementations - returns void for this delegate
IMP_VOID = ctypes.CFUNCTYPE(None, c_void_p, c_void_p, c_void_p)

# Global reference to keep the delegate callback alive
_window_delegate_callback = None
_window_delegate_class = None


def create_window_delegate_class():
    """Create a custom NSWindowDelegate class that terminates app on window close."""
    global _window_delegate_class, _window_delegate_callback

    if _window_delegate_class is not None:
        return _window_delegate_class

    # Create a new class inheriting from NSObject
    NSObject = objc_class("NSObject")
    _window_delegate_class = libobjc.objc_allocateClassPair(
        NSObject, b"FlutWindowDelegate", 0
    )

    if not _window_delegate_class:
        print("ERROR: Failed to create delegate class")
        return None

    # Define the windowWillClose: method
    def window_will_close(self_ptr, cmd_ptr, notification_ptr):
        # Get NSApplication and call terminate:
        NSApplication = libobjc.objc_getClass(b"NSApplication")
        shared_app_sel = libobjc.sel_registerName(b"sharedApplication")
        terminate_sel = libobjc.sel_registerName(b"terminate:")

        # Get shared application
        get_app = ctypes.cast(
            objc_msgSend, ctypes.CFUNCTYPE(c_void_p, c_void_p, c_void_p)
        )
        app = get_app(NSApplication, shared_app_sel)

        # Call terminate:
        terminate = ctypes.cast(
            objc_msgSend, ctypes.CFUNCTYPE(None, c_void_p, c_void_p, c_void_p)
        )
        terminate(app, terminate_sel, None)

    # Keep reference to prevent GC
    _window_delegate_callback = IMP_VOID(window_will_close)

    # Add the method to the class
    # "v@:@" means: void return, self, _cmd, object argument
    libobjc.class_addMethod(
        _window_delegate_class,
        sel("windowWillClose:"),
        _window_delegate_callback,
        b"v@:@",
    )

    # Register the class
    libobjc.objc_registerClassPair(_window_delegate_class)

    return _window_delegate_class


# CGRect structure for macOS
class CGPoint(ctypes.Structure):
    _fields_ = [("x", c_double), ("y", c_double)]


class CGSize(ctypes.Structure):
    _fields_ = [("width", c_double), ("height", c_double)]


class CGRect(ctypes.Structure):
    _fields_ = [("origin", CGPoint), ("size", CGSize)]


def NSMakeRect(x, y, w, h):
    return CGRect(CGPoint(x, y), CGSize(w, h))


# =============================================================================
# CoreFoundation for CFRunLoop integration
# =============================================================================

# Load CoreFoundation
_cf_lib = ctypes.util.find_library("CoreFoundation")
if _cf_lib:
    CoreFoundation = ctypes.CDLL(_cf_lib)
else:
    CoreFoundation = None

# Load libc for pipe/read/write
try:
    libc = ctypes.CDLL("libc.dylib")
except OSError:
    libc = None

# CFRunLoop constants
# Use kCFRunLoopCommonModes for timer registration so timers fire during
# modal operations (window dragging, menu tracking)
kCFRunLoopCommonModes = (
    c_void_p.in_dll(CoreFoundation, "kCFRunLoopCommonModes") if CoreFoundation else None
)

# CFFileDescriptor callback type
# void (*CFFileDescriptorCallBack)(CFFileDescriptorRef f, CFOptionFlags callBackTypes, void *info)
CFFileDescriptorCallBack = CFUNCTYPE(None, c_void_p, c_uint32, c_void_p)

# CFOptionFlags for CFFileDescriptor
kCFFileDescriptorReadCallBack = 1 << 0

# CFRunLoopTimer callback
# void (*CFRunLoopTimerCallBack)(CFRunLoopTimerRef timer, void *info)
CFRunLoopTimerCallBack = CFUNCTYPE(None, c_void_p, c_void_p)


class CocoaAsyncBridge:
    """
    Bridges asyncio to Cocoa/NSApplication via NSEvent posting + CFRunLoopTimer.

    Key insight: nextEventMatchingMask: only returns on NSEvents, not CFRunLoop sources.
    So we must POST an NSEvent when asyncio needs attention.

    - _write_to_self hook: posts NSEvent (wakes nextEvent)
    - CFRunLoopTimer for asyncio timer deadlines: posts NSEvent on expiry

    Single wake authority: NSEvent posted to NSApplication event queue.
    """

    def __init__(self):
        self._loop = None
        self._app = None
        self._runloop = None
        self._timer = None
        self._next_deadline = float("inf")
        # Keep callbacks alive
        self._timer_callback = None
        self._original_write_to_self = None
        # Cached ObjC selectors and functions
        self._post_event_fn = None
        self._post_event_sel = None
        self._other_event_fn = None
        self._other_event_sel = None
        self._NSEvent = None

    def setup(self, loop: asyncio.AbstractEventLoop, app, runloop=None):
        """Hook _write_to_self to post NSEvent, setup timer APIs."""
        self._loop = loop
        self._app = app

        if not CoreFoundation:
            raise RuntimeError("CoreFoundation not available")

        # Cache NSEvent class and message sending
        self._NSEvent = objc_class("NSEvent")

        # NSEventTypeApplicationDefined = 15
        NSEventTypeApplicationDefined = 15

        # otherEventWithType:location:modifierFlags:timestamp:windowNumber:context:subtype:data1:data2:
        self._other_event_fn = ctypes.cast(
            objc_msgSend,
            ctypes.CFUNCTYPE(
                c_void_p,
                c_void_p,
                c_void_p,
                c_uint64,
                CGPoint,
                c_uint64,
                c_double,
                c_int64,
                c_void_p,
                c_int16,
                c_int64,
                c_int64,
            ),
        )
        self._other_event_sel = sel(
            "otherEventWithType:location:modifierFlags:timestamp:windowNumber:context:subtype:data1:data2:"
        )

        # postEvent:atStart:
        self._post_event_fn = ctypes.cast(
            objc_msgSend, ctypes.CFUNCTYPE(None, c_void_p, c_void_p, c_void_p, c_bool)
        )
        self._post_event_sel = sel("postEvent:atStart:")

        bridge = self

        def post_wake_event():
            """Post an NSEventTypeApplicationDefined to wake nextEvent."""
            wake_event = bridge._other_event_fn(
                bridge._NSEvent,
                bridge._other_event_sel,
                NSEventTypeApplicationDefined,
                CGPoint(0, 0),
                0,
                0.0,
                0,
                None,
                0,
                0,
                0,
            )
            if wake_event:
                bridge._post_event_fn(
                    bridge._app, bridge._post_event_sel, wake_event, True
                )

        self._post_wake_event = post_wake_event

        # Hook _write_to_self to post NSEvent (not write to pipe)
        self._original_write_to_self = loop._write_to_self
        original_write = self._original_write_to_self

        def hooked_write_to_self():
            original_write()
            post_wake_event()
            # Force CFRunLoop to stop waiting so nextEventMatchingMask can check event queue
            CoreFoundation.CFRunLoopWakeUp(bridge._runloop)

        loop._write_to_self = hooked_write_to_self

        # Get run loop
        if runloop:
            self._runloop = runloop
        else:
            CoreFoundation.CFRunLoopGetCurrent.argtypes = []
            CoreFoundation.CFRunLoopGetCurrent.restype = c_void_p
            self._runloop = CoreFoundation.CFRunLoopGetCurrent()

        # Setup CFRunLoopTimer APIs
        CoreFoundation.CFRunLoopTimerCreate.argtypes = [
            c_void_p,
            c_double,
            c_double,
            c_uint32,
            c_int32,
            CFRunLoopTimerCallBack,
            c_void_p,
        ]
        CoreFoundation.CFRunLoopTimerCreate.restype = c_void_p
        CoreFoundation.CFRunLoopAddTimer.argtypes = [c_void_p, c_void_p, c_void_p]
        CoreFoundation.CFRunLoopRemoveTimer.argtypes = [c_void_p, c_void_p, c_void_p]
        CoreFoundation.CFAbsoluteTimeGetCurrent.argtypes = []
        CoreFoundation.CFAbsoluteTimeGetCurrent.restype = c_double
        CoreFoundation.CFRelease.argtypes = [c_void_p]
        CoreFoundation.CFRunLoopWakeUp.argtypes = [c_void_p]
        CoreFoundation.CFRunLoopWakeUp.restype = None

        # Timer callback: post NSEvent to wake nextEvent
        def timer_callback(timer, info):
            post_wake_event()
            # Force CFRunLoop to stop waiting so nextEventMatchingMask can check event queue
            CoreFoundation.CFRunLoopWakeUp(bridge._runloop)
            # Timer is one-shot, mark for removal
            if bridge._timer:
                CoreFoundation.CFRunLoopRemoveTimer(
                    bridge._runloop, bridge._timer, kCFRunLoopCommonModes
                )
                CoreFoundation.CFRelease(bridge._timer)
                bridge._timer = None
            bridge._next_deadline = float("inf")

        self._timer_callback = CFRunLoopTimerCallBack(timer_callback)

    def schedule_next_timer(self):
        """Schedule CFRunLoopTimer for next asyncio timer deadline. Call after drain."""
        self._next_deadline = float("inf")

        # Cancel existing timer
        if self._timer:
            CoreFoundation.CFRunLoopRemoveTimer(
                self._runloop, self._timer, kCFRunLoopCommonModes
            )
            CoreFoundation.CFRelease(self._timer)
            self._timer = None

        # Find earliest non-cancelled timer
        scheduled = getattr(self._loop, "_scheduled", [])
        if not scheduled:
            return

        for handle in scheduled:
            if not handle._cancelled:
                when = handle._when
                break
        else:
            return

        # Convert asyncio time to CFAbsoluteTime
        delay_sec = max(0.001, when - self._loop.time())
        fire_time = CoreFoundation.CFAbsoluteTimeGetCurrent() + delay_sec

        # Create one-shot timer (interval=0 means no repeat)
        self._timer = CoreFoundation.CFRunLoopTimerCreate(
            None,  # allocator
            fire_time,  # fire date
            0,  # interval (0 = no repeat)
            0,  # flags
            0,  # order
            self._timer_callback,
            None,  # context
        )

        if self._timer:
            CoreFoundation.CFRunLoopAddTimer(
                self._runloop, self._timer, kCFRunLoopCommonModes
            )
            self._next_deadline = when

    def cleanup(self):
        """Restore hooks, remove timer."""
        if self._loop and self._original_write_to_self:
            self._loop._write_to_self = self._original_write_to_self

        if self._timer and CoreFoundation:
            CoreFoundation.CFRunLoopRemoveTimer(
                self._runloop, self._timer, kCFRunLoopCommonModes
            )
            CoreFoundation.CFRelease(self._timer)
            self._timer = None


# =============================================================================
# Flutter Engine Wrapper using FlutterMacOS.framework
# =============================================================================


class FlutMacOSNative(FlutNative):
    """macOS-specific FFI implementation using FlutterMacOS.framework."""

    def __init__(self):
        self.flutter_engine = None
        self.flutter_view_controller = None
        self._running = False
        self._native_callback = None
        self._last_buffer = None
        self._window = None
        self._window_delegate = None
        self._notify_keepalive = collections.deque(maxlen=100)

    def initialize(self):
        """Load the Flutter macOS framework via ctypes."""
        if not os.path.exists(PATH_FLUT):
            raise FileNotFoundError(
                f"Flutter app bundle not found at {PATH_FLUT}. Build with: cd flut/.flutter && flutter build macos --no-tree-shake-icons"
            )

        print(f"Loading Flutter from: {PATH_FLUTTER_DYLIB}")

        if not os.path.exists(PATH_FLUTTER_DYLIB):
            raise FileNotFoundError(
                f"FlutterMacOS.framework not found at: {PATH_FLUTTER_DYLIB}"
            )

        # Load frameworks using NSBundle
        NSBundle = objc_class("NSBundle")

        # Load FlutterMacOS.framework
        flutter_path_ns = self._create_nsstring(PATH_FLUTTER_FRAMEWORK)
        flutter_bundle = msg(NSBundle, "bundleWithPath:", flutter_path_ns)
        if flutter_bundle:
            msg(flutter_bundle, "load")

        # Load App.framework
        app_path_ns = self._create_nsstring(PATH_APP_FRAMEWORK)
        app_bundle = msg(NSBundle, "bundleWithPath:", app_path_ns)
        if app_bundle:
            msg(app_bundle, "load")

        print("Flutter framework loaded!")

    def setup_call_dart(self, callback_addr):
        DART_CALL_CALLBACK = CFUNCTYPE(c_void_p, c_char_p)
        dart_fn = DART_CALL_CALLBACK(callback_addr)

        def call_dart_impl(call_type, data):
            try:
                req = json.dumps({"type": call_type, "data": data})
                req_bytes = req.encode("utf-8")
                result_ptr = dart_fn(req_bytes)
                if result_ptr == 0 or result_ptr is None:
                    return None
                result_str = ctypes.string_at(result_ptr).decode("utf-8")
                return json.loads(result_str)
            except Exception as e:
                print(f"Error calling Dart: {e}")
                return None

        return call_dart_impl

    def setup_notify_dart(self, callback_addr):
        DART_NOTIFY_CALLBACK = CFUNCTYPE(None, c_char_p)
        dart_fn = DART_NOTIFY_CALLBACK(callback_addr)

        def notify_dart_impl(data_bytes):
            try:
                self._notify_keepalive.append(data_bytes)
                dart_fn(data_bytes)
            except Exception as e:
                print(f"Error notifying Dart: {e}")

        return notify_dart_impl

    def _create_nsstring(self, s):
        """Create an NSString from a Python string."""
        NSString = objc_class("NSString")
        return msg(NSString, "stringWithUTF8String:", s.encode("utf-8"))

    def _create_nsarray(self, items):
        """Create an NSArray from Python strings."""
        NSMutableArray = objc_class("NSMutableArray")
        arr = msg(NSMutableArray, "array")
        for item in items:
            ns_item = self._create_nsstring(item)
            msg(arr, "addObject:", ns_item)
        return arr

    def _setup_flutter(self, method_call_handler, width: int, height: int):
        """
        Shared setup for both sync and async run methods.
        Creates the Flutter engine, window, and returns the NSApplication instance.
        """

        def on_native_callback(request_ptr):
            try:
                if not request_ptr:
                    return 0
                req_str = ctypes.string_at(request_ptr).decode("utf-8")
                req_json = json.loads(req_str)
                result_bytes = method_call_handler(req_json)
                if result_bytes:
                    self._last_buffer = ctypes.create_string_buffer(result_bytes)
                    return ctypes.addressof(self._last_buffer)
                return 0
            except Exception as e:
                print(f"Error in on_native_callback: {e}")
                return 0

        NativeCallbackType = CFUNCTYPE(c_void_p, c_char_p)
        self._native_callback = NativeCallbackType(on_native_callback)
        callback_addr = ctypes.cast(self._native_callback, c_void_p).value

        # Get Objective-C classes
        NSApplication = objc_class("NSApplication")
        NSWindow = objc_class("NSWindow")
        FlutterDartProject = objc_class("FlutterDartProject")
        FlutterViewController = objc_class("FlutterViewController")

        # Initialize NSApplication
        app = msg(NSApplication, "sharedApplication")

        # Set activation policy to regular (foreground app)
        # NSApplicationActivationPolicyRegular = 0
        set_policy = ctypes.cast(
            objc_msgSend, ctypes.CFUNCTYPE(c_bool, c_void_p, c_void_p, c_int)
        )
        set_policy(app, sel("setActivationPolicy:"), 0)

        # Finish launching the app (required for windows to appear)
        msg(app, "finishLaunching")

        # Create Flutter Dart project
        dart_project = msg(msg(FlutterDartProject, "alloc"), "init")

        # Set dart entrypoint arguments
        dart_args = self._create_nsarray([f"--native-callback={callback_addr}"])
        msg(dart_project, "setDartEntrypointArguments:", dart_args)

        # Create Flutter view controller with project (it will create and run engine internally)
        self.flutter_view_controller = msg(
            msg(FlutterViewController, "alloc"),
            "initWithProject:",
            dart_project,
        )

        if not self.flutter_view_controller:
            raise RuntimeError("Failed to create Flutter view controller")

        # Get the engine from the view controller
        self.flutter_engine = msg(self.flutter_view_controller, "engine")

        print(f"  View controller created: {self.flutter_view_controller}")
        print(f"  Engine: {self.flutter_engine}")

        # Create NSWindow
        # Style mask: titled | closable | miniaturizable | resizable
        style_mask = (1 << 0) | (1 << 1) | (1 << 2) | (1 << 3)  # 15

        # NSWindow initWithContentRect:styleMask:backing:defer:
        # For struct arguments, we need to define the function properly
        init_window = ctypes.cast(
            objc_msgSend,
            ctypes.CFUNCTYPE(
                c_void_p,  # return
                c_void_p,  # self
                c_void_p,  # _cmd
                CGRect,  # contentRect
                c_uint64,  # styleMask
                c_uint64,  # backing
                c_bool,  # defer
            ),
        )

        rect = NSMakeRect(100, 100, width, height)
        self._window = init_window(
            msg(NSWindow, "alloc"),
            sel("initWithContentRect:styleMask:backing:defer:"),
            rect,
            style_mask,
            2,  # NSBackingStoreBuffered
            False,
        )

        if not self._window:
            raise RuntimeError("Failed to create window")

        print(f"  Window created: {self._window}")

        # Create and set window delegate to handle window close
        delegate_class = create_window_delegate_class()
        if delegate_class:
            self._window_delegate = msg(msg(delegate_class, "alloc"), "init")
            msg(self._window, "setDelegate:", self._window_delegate)

        # Prevent window from being released when closed
        set_released = ctypes.cast(
            objc_msgSend, ctypes.CFUNCTYPE(None, c_void_p, c_void_p, c_bool)
        )
        set_released(self._window, sel("setReleasedWhenClosed:"), False)

        # Set window title
        title = self._create_nsstring("Flut")
        msg(self._window, "setTitle:", title)

        # Get the Flutter view from the view controller
        flutter_view = msg(self.flutter_view_controller, "view")
        print(f"  Flutter view: {flutter_view}")

        # Set the Flutter view as the content view of the window
        msg(self._window, "setContentView:", flutter_view)

        # Set the view's frame to match the window's content rect
        set_frame = ctypes.cast(
            objc_msgSend, ctypes.CFUNCTYPE(None, c_void_p, c_void_p, CGRect)
        )
        content_rect = NSMakeRect(0, 0, width, height)
        set_frame(flutter_view, sel("setFrame:"), content_rect)

        # Ensure the view is not hidden
        set_hidden = ctypes.cast(
            objc_msgSend, ctypes.CFUNCTYPE(None, c_void_p, c_void_p, c_bool)
        )
        set_hidden(flutter_view, sel("setHidden:"), False)

        # Force the view to display
        msg(flutter_view, "setNeedsDisplay:", c_void_p(1))
        msg(flutter_view, "display")

        # Center the window on screen
        msg(self._window, "center")

        # Make window key and order front
        msg(self._window, "makeKeyAndOrderFront:", c_void_p(0))

        # Activate application
        activate = ctypes.cast(
            objc_msgSend, ctypes.CFUNCTYPE(None, c_void_p, c_void_p, c_bool)
        )
        activate(app, sel("activateIgnoringOtherApps:"), True)

        print(f"\nFlutter is running!")
        print(f"  View controller: {self.flutter_view_controller}")
        print("Close the window to exit.\n")

        self._running = True

        return app

    def run(
        self, method_call_handler, assets_path: str, width: int = 800, height: int = 600
    ):
        if not os.path.exists(assets_path):
            raise FileNotFoundError(f"Assets path not found: {assets_path}")

        print(f"\nStarting Flutter...")
        print(f"  Assets: {assets_path}")
        print(f"  Window: {width}x{height}")

        app = self._setup_flutter(method_call_handler, width, height)

        # Run the application event loop (blocking)
        msg(app, "run")

        return True

    async def run_async(
        self,
        method_call_handler,
        assets_path: str,
        width: int = 800,
        height: int = 600,
        loop=None,
    ):
        """Async version that integrates with asyncio event loop."""
        if not os.path.exists(assets_path):
            raise FileNotFoundError(f"Assets path not found: {assets_path}")

        print(f"\nStarting Flutter (async)...")
        print(f"  Assets: {assets_path}")
        print(f"  Window: {width}x{height}")

        app = self._setup_flutter(method_call_handler, width, height)

        # Run async event loop - use provided loop or get the running one
        if loop is None:
            loop = asyncio.get_running_loop()
        await self._run_async_runloop(app, loop)

        return True

    async def _run_async_runloop(self, app, loop):
        """
        Async NSApplication event loop integration with asyncio.

        Single blocking wait that wakes on either UI or asyncio events,
        then batch-drains both queues before sleeping again.

        CFRunLoopTimer posts NSEvent on expiry - single wake authority.
        """
        import heapq

        # Get classes
        NSDate = objc_class("NSDate")

        # Load CoreFoundation
        cf = ctypes.CDLL(
            "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
        )
        # kCFRunLoopCommonModes is used by bridge for registering timers (so they fire in all modes)
        # kCFRunLoopDefaultMode is used for nextEvent inMode: (can't run in CommonModes pseudo-mode)
        kCFRunLoopDefaultMode = c_void_p.in_dll(cf, "kCFRunLoopDefaultMode")

        CFRunLoopGetMain = cf.CFRunLoopGetMain
        CFRunLoopGetMain.argtypes = []
        CFRunLoopGetMain.restype = c_void_p

        main_runloop = CFRunLoopGetMain()

        # Setup the async bridge
        # Posts NSEvent when asyncio needs attention (timer expiry or _write_to_self)
        bridge = CocoaAsyncBridge()
        bridge.setup(loop, app, main_runloop)
        print(f"Asyncio bridge: initialized")

        # NSEventMaskAny = NSUIntegerMax
        NSEventMaskAny = 0xFFFFFFFFFFFFFFFF

        # Setup nextEventMatchingMask:untilDate:inMode:dequeue:
        next_event_fn = ctypes.cast(
            objc_msgSend,
            ctypes.CFUNCTYPE(
                c_void_p,
                c_void_p,
                c_void_p,
                c_uint64,
                c_void_p,
                c_void_p,
                c_bool,
            ),
        )
        next_event_sel = sel("nextEventMatchingMask:untilDate:inMode:dequeue:")

        # distantFuture for blocking wait
        distant_future = msg(NSDate, "distantFuture")

        def process_asyncio_timers():
            """Move expired timers to ready queue. Return True if ready has work."""
            now = loop.time()
            scheduled = getattr(loop, "_scheduled", [])
            ready = getattr(loop, "_ready", None)
            if ready is None:
                return False
            while scheduled:
                handle = scheduled[0]
                if handle._cancelled:
                    heapq.heappop(scheduled)
                    handle._scheduled = False
                elif handle._when <= now:
                    heapq.heappop(scheduled)
                    handle._scheduled = False
                    ready.append(handle)
                else:
                    break
            return bool(ready)

        def drain_nsevents():
            """Drain all pending NSEvents (non-blocking)."""
            now_date = msg(NSDate, "date")
            while True:
                event = next_event_fn(
                    app,
                    next_event_sel,
                    NSEventMaskAny,
                    now_date,  # immediate - no wait
                    kCFRunLoopDefaultMode,
                    True,
                )
                if not event:
                    break
                msg(app, "sendEvent:", event)
            msg(app, "updateWindows")

        def has_pending_asyncio_work():
            """Check if asyncio has ready callbacks or due timers."""
            ready = getattr(loop, "_ready", None)
            if ready:
                return True
            scheduled = getattr(loop, "_scheduled", [])
            if scheduled:
                now = loop.time()
                for handle in scheduled:
                    if not handle._cancelled and handle._when <= now:
                        return True
            return False

        try:
            while self._running:
                # 1. Drain NSEvents (includes UI + triggers CFRunLoop sources)
                drain_nsevents()

                # 2. Drain asyncio (interleaved with events to stay responsive)
                while process_asyncio_timers():
                    await asyncio.sleep(0)
                    drain_nsevents()

                if not self._running:
                    break

                # 3. Schedule timer for next asyncio deadline
                bridge.schedule_next_timer()

                # 4. Final drain before blocking - catches any events posted during
                # asyncio drain (e.g., Dart frame callbacks from setState notifications)
                drain_nsevents()

                # 5. Check if more asyncio work appeared during drain - if so, don't block
                if has_pending_asyncio_work():
                    continue

                # 6. Block until event (UI event or timer fires)
                event = next_event_fn(
                    app,
                    next_event_sel,
                    NSEventMaskAny,
                    distant_future,  # block forever
                    kCFRunLoopDefaultMode,
                    True,
                )

                if event:
                    msg(app, "sendEvent:", event)

        finally:
            bridge.cleanup()

    def shutdown(self):
        self._running = False
        if self.flutter_engine:
            msg(self.flutter_engine, "shutDownEngine")
            self.flutter_engine = None
        print("Flutter shutdown.")

    @staticmethod
    def get_default_assets_path() -> str:
        return PATH_FLUT_ASSETS
