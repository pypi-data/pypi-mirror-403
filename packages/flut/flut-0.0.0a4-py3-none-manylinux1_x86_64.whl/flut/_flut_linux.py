import ctypes
import ctypes.util
import os
import json
import collections
import asyncio
import heapq
from ctypes import c_void_p, c_char_p, c_int, CFUNCTYPE, c_size_t, CDLL, POINTER, c_uint, c_uint64, c_long

from ._flut_native import FlutNative

# ssize_t is signed size_t (c_long on Linux 64-bit)
c_ssize_t = c_long

# =============================================================================
# Paths
# =============================================================================

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Standard "flutter build linux" output structure:
# build/linux/x64/release/bundle/
#   flut (executable)
#   lib/
#     libflutter_linux_gtk.so
#     libapp.so (AOT)
#   data/
#     flutter_assets/
#     icudtl.dat

PATH_FLUT_BUNDLE = os.path.join(
    ROOT_DIR,
    ".flutter",
    "build",
    "linux",
    "x64",
    "release",
    "bundle",
)

PATH_LIB = os.path.join(PATH_FLUT_BUNDLE, "lib")
PATH_DATA = os.path.join(PATH_FLUT_BUNDLE, "data")
PATH_FLUTTER_LIB = os.path.join(PATH_LIB, "libflutter_linux_gtk.so")
PATH_FLUT_ASSETS = os.path.join(PATH_DATA, "flutter_assets")
PATH_FLUT_ICU = os.path.join(PATH_DATA, "icudtl.dat")
PATH_FLUT_AOT = os.path.join(PATH_LIB, "libapp.so")

# =============================================================================
# GTK & GObject & GLib Definitions
# =============================================================================

# Load GTK
_gtk_lib = ctypes.util.find_library("gtk-3")
if not _gtk_lib:
    # Try hardcoded name for common distros if find_library fails
    try:
        gtk = CDLL("libgtk-3.so.0")
    except OSError:
        gtk = None
else:
    gtk = CDLL(_gtk_lib)

# Load GObject
_gobject_lib = ctypes.util.find_library("gobject-2.0")
if not _gobject_lib:
    try:
        gobject = CDLL("libgobject-2.0.so.0")
    except OSError:
        gobject = None
else:
    gobject = CDLL(_gobject_lib)

# Load GLib (for g_unix_fd_add)
_glib_lib = ctypes.util.find_library("glib-2.0")
if not _glib_lib:
    try:
        glib = CDLL("libglib-2.0.so.0")
    except OSError:
        glib = None
else:
    glib = CDLL(_glib_lib)

# Load libc for eventfd
try:
    libc = CDLL("libc.so.6")
except OSError:
    libc = None


# Check if libraries loaded
if not gtk or not gobject:
    print("WARNING: GTK 3 or GObject 2.0 libraries not found. Linux support may fail.")

# GType
GType = c_size_t

# GApplicationFlags
G_APPLICATION_FLAGS_NONE = 0

# GtkWindowType
GTK_WINDOW_TOPLEVEL = 0

# GIOCondition flags
G_IO_IN = 1
G_IO_OUT = 4
G_IO_PRI = 2
G_IO_ERR = 8
G_IO_HUP = 16

# eventfd flags
EFD_NONBLOCK = 0x800
EFD_CLOEXEC = 0x80000

# Callbacks
GCallback = CFUNCTYPE(None, c_void_p, c_void_p)

# GUnixFDSourceFunc: gboolean (*) (gint fd, GIOCondition condition, gpointer user_data)
GUnixFDSourceFunc = CFUNCTYPE(c_int, c_int, c_uint, c_void_p)


# =============================================================================
# GLib-Asyncio Bridge (libuv/Electron pattern)
# =============================================================================
#
# Bridges asyncio to GLib via unified eventfd wake mechanism:
# - _write_to_self hook: writes to eventfd when asyncio schedules callbacks
# - GLib timeout: writes to eventfd when asyncio timer deadline expires
#
# GLib watches eventfd via g_unix_fd_add - single wake authority.
# =============================================================================

GSourceFunc = CFUNCTYPE(c_int, c_void_p)  # gboolean (*)(gpointer)


class GLibAsyncBridge:
    """Bridges asyncio to GLib main loop."""
    
    def __init__(self):
        self._loop = None
        self._eventfd = -1
        self._fd_source_id = 0
        self._timer_source_id = 0
        self._next_deadline = float('inf')
        # prevent GC
        self._fd_callback = None
        self._timer_callback = None
        self._original_write_to_self = None
    
    def setup(self, loop: asyncio.AbstractEventLoop):
        """Create eventfd, hook _write_to_self, register with GLib."""
        self._loop = loop
        
        if not libc:
            raise RuntimeError("libc not available")
        if not glib:
            raise RuntimeError("glib not available")
        
        # Create eventfd
        libc.eventfd.argtypes = [c_uint, c_int]
        libc.eventfd.restype = c_int
        self._eventfd = libc.eventfd(0, EFD_NONBLOCK | EFD_CLOEXEC)
        if self._eventfd < 0:
            raise RuntimeError("Failed to create eventfd")
        
        libc.write.argtypes = [c_int, c_void_p, c_size_t]
        libc.write.restype = c_ssize_t
        libc.read.argtypes = [c_int, c_void_p, c_size_t]
        libc.read.restype = c_ssize_t
        
        eventfd = self._eventfd
        bridge = self
        
        # Hook _write_to_self to also signal eventfd
        self._original_write_to_self = loop._write_to_self
        original_write = self._original_write_to_self
        
        def hooked_write_to_self():
            original_write()
            buf = ctypes.c_uint64(1)
            libc.write(eventfd, ctypes.byref(buf), 8)
        
        loop._write_to_self = hooked_write_to_self
        
        # Register eventfd with GLib
        def fd_callback(fd, condition, user_data):
            buf = ctypes.c_uint64(0)
            libc.read(fd, ctypes.byref(buf), 8)  # drain
            return 1  # keep source
        
        self._fd_callback = GUnixFDSourceFunc(fd_callback)
        glib.g_unix_fd_add.argtypes = [c_int, c_uint, GUnixFDSourceFunc, c_void_p]
        glib.g_unix_fd_add.restype = c_uint
        self._fd_source_id = glib.g_unix_fd_add(self._eventfd, G_IO_IN, self._fd_callback, None)
        
        # Timer callback: writes to eventfd on expiry, removes itself
        def timer_callback(user_data):
            buf = ctypes.c_uint64(1)
            libc.write(eventfd, ctypes.byref(buf), 8)
            bridge._timer_source_id = 0
            bridge._next_deadline = float('inf')
            return 0  # remove source
        
        self._timer_callback = GSourceFunc(timer_callback)
        return self._eventfd
    
    def schedule_next_timer(self):
        """Schedule GLib timeout for next asyncio timer deadline. Call after drain."""
        self._next_deadline = float('inf')
        
        # Cancel existing timer
        if self._timer_source_id > 0:
            glib.g_source_remove.argtypes = [c_uint]
            glib.g_source_remove.restype = c_int
            glib.g_source_remove(self._timer_source_id)
            self._timer_source_id = 0
        
        # Find earliest non-cancelled timer
        if not self._loop._scheduled:
            return
        
        for handle in self._loop._scheduled:
            if not handle._cancelled:
                when = handle._when
                break
        else:
            return
        
        # Schedule GLib timer
        delay_ms = max(1, int((when - self._loop.time()) * 1000))
        glib.g_timeout_add.argtypes = [c_uint, GSourceFunc, c_void_p]
        glib.g_timeout_add.restype = c_uint
        self._timer_source_id = glib.g_timeout_add(delay_ms, self._timer_callback, None)
        self._next_deadline = when
    
    def cleanup(self):
        """Restore hooks, remove GLib sources, close eventfd."""
        if self._loop and self._original_write_to_self:
            self._loop._write_to_self = self._original_write_to_self
        
        glib.g_source_remove.argtypes = [c_uint]
        glib.g_source_remove.restype = c_int
        if self._timer_source_id > 0:
            glib.g_source_remove(self._timer_source_id)
        if self._fd_source_id > 0:
            glib.g_source_remove(self._fd_source_id)
        
        if self._eventfd >= 0:
            libc.close.argtypes = [c_int]
            libc.close.restype = c_int
            libc.close(self._eventfd)
            self._eventfd = -1


# =============================================================================
# Flutter Engine Wrapper using libflutter_linux_gtk.so
# =============================================================================

class FlutLinuxNative(FlutNative):
    """Linux-specific FFI implementation using libflutter_linux_gtk.so."""

    def __init__(self):
        self._running = False
        self.libflutter = None
        self._native_callback = None
        self._last_buffer = None
        self._window = None
        self._notify_keepalive = collections.deque(maxlen=100)
        
    def initialize(self):
        # Load Flutter Engine Library
        if not os.path.exists(PATH_FLUTTER_LIB):
            raise FileNotFoundError(
                f"libflutter_linux_gtk.so not found at: {PATH_FLUTTER_LIB}\n"
                "Please run: cd flut/.flutter && flutter build linux"
            )
        
        self.libflutter = CDLL(PATH_FLUTTER_LIB)
        print("Flutter engine loaded!")
        
        if gtk:
            gtk.gtk_init(None, None)

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

    def _setup_flutter(self, method_call_handler, assets_path: str, width: int, height: int, async_mode: bool = False):
        """
        Shared setup: initializes Flutter, creates project, view, and GTK window.
        
        Args:
            method_call_handler: Callable that handles method calls from Dart.
            assets_path: Path to flutter_assets.
            width: Window width.
            height: Window height.
            async_mode: If True, prints "(async mode)" in status messages.
        
        Returns:
            The GTK window, or None if setup failed.
        """
        if not self.libflutter:
            self.initialize()

        if not os.path.exists(assets_path):
            raise FileNotFoundError(f"Assets path not found: {assets_path}")

        mode_str = " (async mode)" if async_mode else ""
        print(f"\nStarting Flutter{mode_str}...")
        print(f"  Assets: {assets_path}")
        print(f"  Window: {width}x{height}")

        # Create native callback for Dart -> Python calls
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
        
        # Setup Dart Project
        self.libflutter.fl_dart_project_new.restype = c_void_p
        project = self.libflutter.fl_dart_project_new()
        
        self.libflutter.fl_dart_project_set_assets_path.argtypes = [c_void_p, c_char_p]
        self.libflutter.fl_dart_project_set_assets_path(
            project, assets_path.encode("utf-8")
        )
        
        icu_path = PATH_FLUT_ICU
        if os.path.exists(icu_path):
            self.libflutter.fl_dart_project_set_icu_data_path.argtypes = [c_void_p, c_char_p]
            self.libflutter.fl_dart_project_set_icu_data_path(
                project, icu_path.encode("utf-8")
            )

        aot_path = PATH_FLUT_AOT
        if os.path.exists(aot_path):
            try:
                self.libflutter.fl_dart_project_set_aot_library_path.argtypes = [c_void_p, c_char_p]
                self.libflutter.fl_dart_project_set_aot_library_path(
                    project, aot_path.encode("utf-8")
                )
            except AttributeError:
                pass
            
        # Set entrypoint arguments
        arg1 = f"--native-callback={callback_addr}"
        argv = [arg1.encode("utf-8")]
        
        argv_c = (c_char_p * (len(argv) + 1))()
        argv_c[0] = argv[0]
        argv_c[1] = None
        
        self.libflutter.fl_dart_project_set_dart_entrypoint_arguments.argtypes = [c_void_p, POINTER(c_char_p)]
        self.libflutter.fl_dart_project_set_dart_entrypoint_arguments(project, argv_c)
        
        # Create Flutter View
        self.libflutter.fl_view_new.argtypes = [c_void_p]
        self.libflutter.fl_view_new.restype = c_void_p
        fl_view = self.libflutter.fl_view_new(project)
        
        # Create GTK Window
        gtk.gtk_window_new.argtypes = [c_int]
        gtk.gtk_window_new.restype = c_void_p
        window = gtk.gtk_window_new(GTK_WINDOW_TOPLEVEL)
        self._window = window
        
        gtk.gtk_window_set_default_size.argtypes = [c_void_p, c_int, c_int]
        gtk.gtk_window_set_default_size(window, width, height)
        
        title = b"Flut (Async)" if async_mode else b"Flut"
        gtk.gtk_window_set_title.argtypes = [c_void_p, c_char_p]
        gtk.gtk_window_set_title(window, title)
        
        gtk.gtk_container_add.argtypes = [c_void_p, c_void_p]
        gtk.gtk_container_add(window, fl_view)
        
        gtk.gtk_widget_show_all.argtypes = [c_void_p]
        gtk.gtk_widget_show_all(window)
        
        print(f"\nFlutter is running{mode_str}!")
        print("Close the window to exit.\n")
        
        return window

    def run(self, method_call_handler, assets_path: str, width: int = 800, height: int = 600):
        """Run Flutter with sync GTK main loop (gtk_main)."""
        window = self._setup_flutter(method_call_handler, assets_path, width, height, async_mode=False)
        if window is None:
            return False
        
        # Connect destroy signal to quit gtk_main
        def on_destroy(widget, data):
            print("Window destroyed, quitting...")
            gtk.gtk_main_quit()
            
        self._destroy_cb = GCallback(on_destroy)
        
        gobject.g_signal_connect_data.argtypes = [
            c_void_p, c_char_p, GCallback, c_void_p, c_void_p, c_int
        ]
        gobject.g_signal_connect_data(
            window, 
            b"destroy", 
            self._destroy_cb, 
            None, None, 0
        )
        
        self._running = True
        
        # Run GTK Loop (blocking)
        gtk.gtk_main()
        
        return True

    async def run_async(
        self,
        method_call_handler,
        assets_path: str,
        width: int = 800,
        height: int = 600,
        loop: asyncio.AbstractEventLoop = None
    ):
        """
        Run Flutter with asyncio integration (async).
        
        Integrates GTK's GMainLoop with asyncio via eventfd + g_unix_fd_add.
        Wakes on either GTK events or asyncio work, then processes both.
        
        Args:
            method_call_handler: Callable that handles method calls from Dart.
            assets_path: Path to flutter_assets.
            width: Window width.
            height: Window height.
            loop: Asyncio event loop (uses current if not provided).
        """
        window = self._setup_flutter(method_call_handler, assets_path, width, height, async_mode=True)
        if window is None:
            return False

        if loop is None:
            loop = asyncio.get_running_loop()

        await self._run_async_gtk_loop(window, loop)
        return True

    async def _run_async_gtk_loop(self, window, loop: asyncio.AbstractEventLoop):
        """
        Async GTK loop - libuv/Electron pattern:
        1. Drain GTK events  2. Drain asyncio  3. Schedule timer  4. Block
        """
        should_quit = False
        
        def on_destroy(widget, data):
            nonlocal should_quit
            print("Window destroyed, quitting...")
            should_quit = True
            
        self._destroy_cb = GCallback(on_destroy)
        gobject.g_signal_connect_data.argtypes = [c_void_p, c_char_p, GCallback, c_void_p, c_void_p, c_int]
        gobject.g_signal_connect_data(window, b"destroy", self._destroy_cb, None, None, 0)
        
        bridge = GLibAsyncBridge()
        bridge.setup(loop)
        
        self._running = True
        gtk.gtk_events_pending.argtypes = []
        gtk.gtk_events_pending.restype = c_int
        gtk.gtk_main_iteration_do.argtypes = [c_int]
        gtk.gtk_main_iteration_do.restype = c_int
        
        def process_asyncio_timers():
            """Move expired timers to ready queue. Return True if ready has work."""
            now = loop.time()
            while loop._scheduled:
                handle = loop._scheduled[0]
                if handle._cancelled:
                    heapq.heappop(loop._scheduled)
                    handle._scheduled = False
                elif handle._when <= now:
                    heapq.heappop(loop._scheduled)
                    handle._scheduled = False
                    loop._ready.append(handle)
                else:
                    break
            return bool(loop._ready)
        
        def drain_gtk():
            nonlocal should_quit
            while gtk.gtk_events_pending():
                gtk.gtk_main_iteration_do(False)
                if should_quit:
                    return False
            return True
        
        try:
            while not should_quit:
                # 1. Drain GTK
                if not drain_gtk():
                    break
                
                # 2. Drain asyncio (interleaved with GTK to stay responsive)
                while process_asyncio_timers():
                    await asyncio.sleep(0)
                    if not drain_gtk():
                        break
                
                if should_quit:
                    break
                
                # 3. Schedule timer for next asyncio deadline
                bridge.schedule_next_timer()
                
                # 4. Block until event
                gtk.gtk_main_iteration_do(True)
        finally:
            bridge.cleanup()
        
        return True

    def shutdown(self):
        if self._running:
            if gtk:
                gtk.gtk_main_quit()
            self._running = False
            print("Flutter shutdown.")

    @staticmethod
    def get_default_assets_path() -> str:
        return PATH_FLUT_ASSETS
