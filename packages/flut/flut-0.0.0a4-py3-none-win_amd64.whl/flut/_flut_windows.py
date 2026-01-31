import ctypes
from ctypes import wintypes
import os
import json
import collections
import asyncio

from ._flut_native import FlutNative


# =============================================================================
# Windows Asyncio Integration via IOCP
# =============================================================================

# Win32 constants
WAIT_OBJECT_0 = 0x00000000
WAIT_TIMEOUT = 0x00000102
WAIT_FAILED = 0xFFFFFFFF
INFINITE = 0xFFFFFFFF
QS_ALLINPUT = 0x04FF
MWMO_ALERTABLE = 0x0002
MWMO_INPUTAVAILABLE = 0x0004
PM_REMOVE = 0x0001
PM_NOREMOVE = 0x0000


class ProactorWakeEvent:
    """
    Bridges asyncio's wake mechanism to a Win32 Event for MsgWait.

    When work is scheduled, the loop calls _write_to_self().
    We hook that to also signal a Win32 Event that MsgWaitForMultipleObjectsEx can wait on.
    """

    def __init__(self):
        self._event = None
        self._loop = None
        self._original_write_to_self = None

    def setup(self, loop: asyncio.AbstractEventLoop):
        """Hook loop's _write_to_self to signal our event."""
        self._loop = loop

        # Create auto-reset event
        kernel32 = ctypes.windll.kernel32
        self._event = kernel32.CreateEventW(None, False, False, None)
        if not self._event:
            raise RuntimeError("Failed to create Win32 event")

        # Hook loop's _write_to_self (not proactor's - proactor doesn't have it)
        self._original_write_to_self = loop._write_to_self
        event = self._event

        def hooked_write_to_self():
            self._original_write_to_self()
            kernel32.SetEvent(event)

        loop._write_to_self = hooked_write_to_self

        return self._event

    def cleanup(self):
        """Restore original and close event."""
        if self._loop and self._original_write_to_self:
            self._loop._write_to_self = self._original_write_to_self

        if self._event:
            ctypes.windll.kernel32.CloseHandle(self._event)
            self._event = None


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PATH_FLUT = os.path.join(
    ROOT_DIR,
    ".flutter",
    "build",
    "windows",
    "x64",
    "runner",
    "Release",
)
PATH_FLUT_ASSETS = os.path.join(PATH_FLUT, "data", "flutter_assets")
PATH_FLUT_ICU = os.path.join(PATH_FLUT, "data", "icudtl.dat")
PATH_FLUT_AOT = os.path.join(PATH_FLUT, "data", "app.so")
PATH_FLUT_WINDOWS_DLL = os.path.join(PATH_FLUT, "flutter_windows.dll")


class FlutterDesktopEngineProperties(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("assets_path", ctypes.c_wchar_p),
        ("icu_data_path", ctypes.c_wchar_p),
        ("aot_library_path", ctypes.c_wchar_p),
        ("dart_entrypoint", ctypes.c_char_p),
        ("dart_entrypoint_argc", ctypes.c_int),
        ("dart_entrypoint_argv", ctypes.POINTER(ctypes.c_char_p)),
        ("gpu_preference", ctypes.c_int),
        ("ui_thread_policy", ctypes.c_int),
    ]


FlutterDesktopBinaryReply = ctypes.CFUNCTYPE(
    None, ctypes.POINTER(ctypes.c_uint8), ctypes.c_size_t, ctypes.c_void_p
)


class FlutterDesktopMessage(ctypes.Structure):
    _fields_ = [
        ("struct_size", ctypes.c_size_t),
        ("channel", ctypes.c_char_p),
        ("message", ctypes.POINTER(ctypes.c_uint8)),
        ("message_size", ctypes.c_size_t),
        ("response_handle", ctypes.c_void_p),
    ]


FlutterDesktopMessageCallback = ctypes.CFUNCTYPE(
    None, ctypes.POINTER(FlutterDesktopMessage), ctypes.c_void_p
)


class FlutWindowsNative(FlutNative):
    """Windows-specific FFI implementation using flutter_windows.dll."""

    def __init__(self):
        self.engine_dir = PATH_FLUT
        self.dll_path = PATH_FLUT_WINDOWS_DLL
        self.icu_path = PATH_FLUT_ICU

        self.flutter = None
        self.engine = None
        self.view_controller = None
        self._running = False
        self._props = None
        self._wndproc = None
        self._native_callback = None
        self._notify_keepalive = collections.deque(maxlen=100)
        self._last_buffer = None

    def initialize(self):
        if not os.path.exists(self.dll_path):
            raise FileNotFoundError(
                f"flutter_windows.dll not found at: {self.dll_path}"
            )

        try:
            ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

        ctypes.windll.ole32.CoInitialize(None)

        os.add_dll_directory(self.engine_dir)
        self.flutter = ctypes.CDLL(self.dll_path)

        self._setup_api()
        print("Flutter engine loaded!")

    def _setup_api(self):
        f = self.flutter

        if ctypes.sizeof(ctypes.c_void_p) == 8:
            LRESULT = ctypes.c_longlong
        else:
            LRESULT = ctypes.c_long

        f.FlutterDesktopEngineCreate.argtypes = [
            ctypes.POINTER(FlutterDesktopEngineProperties),
        ]
        f.FlutterDesktopEngineCreate.restype = ctypes.c_void_p

        f.FlutterDesktopEngineDestroy.argtypes = [ctypes.c_void_p]
        f.FlutterDesktopEngineDestroy.restype = ctypes.c_bool

        f.FlutterDesktopEngineRun.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        f.FlutterDesktopEngineRun.restype = ctypes.c_bool

        f.FlutterDesktopViewControllerCreate.argtypes = [
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_void_p,
        ]
        f.FlutterDesktopViewControllerCreate.restype = ctypes.c_void_p

        f.FlutterDesktopViewControllerDestroy.argtypes = [ctypes.c_void_p]
        f.FlutterDesktopViewControllerDestroy.restype = None

        f.FlutterDesktopViewControllerGetEngine.argtypes = [ctypes.c_void_p]
        f.FlutterDesktopViewControllerGetEngine.restype = ctypes.c_void_p

        f.FlutterDesktopViewControllerGetView.argtypes = [ctypes.c_void_p]
        f.FlutterDesktopViewControllerGetView.restype = ctypes.c_void_p

        f.FlutterDesktopViewGetHWND.argtypes = [ctypes.c_void_p]
        f.FlutterDesktopViewGetHWND.restype = wintypes.HWND

        f.FlutterDesktopViewControllerHandleTopLevelWindowProc.argtypes = [
            ctypes.c_void_p,
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
            ctypes.POINTER(LRESULT),
        ]
        f.FlutterDesktopViewControllerHandleTopLevelWindowProc.restype = ctypes.c_bool

        f.FlutterDesktopViewControllerForceRedraw.argtypes = [ctypes.c_void_p]
        f.FlutterDesktopViewControllerForceRedraw.restype = None

        f.FlutterDesktopEngineProcessExternalWindowMessage.argtypes = [
            ctypes.c_void_p,
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
            ctypes.POINTER(LRESULT),
        ]
        f.FlutterDesktopEngineProcessExternalWindowMessage.restype = ctypes.c_bool

        try:
            f.FlutterDesktopEngineGetMessenger.argtypes = [ctypes.c_void_p]
            f.FlutterDesktopEngineGetMessenger.restype = ctypes.c_void_p

            f.FlutterDesktopMessengerSetCallback.argtypes = [
                ctypes.c_void_p,
                ctypes.c_char_p,
                FlutterDesktopMessageCallback,
                ctypes.c_void_p,
            ]
            f.FlutterDesktopMessengerSetCallback.restype = None

            f.FlutterDesktopMessengerSendResponse.argtypes = [
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.POINTER(ctypes.c_uint8),
                ctypes.c_size_t,
            ]
            f.FlutterDesktopMessengerSendResponse.restype = None
        except AttributeError:
            print("Warning: Messenger API not found in flutter_windows.dll")

    def setup_call_dart(self, callback_addr):
        DART_CALL_CALLBACK = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_char_p)
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
        DART_NOTIFY_CALLBACK = ctypes.CFUNCTYPE(None, ctypes.c_char_p)
        dart_fn = DART_NOTIFY_CALLBACK(callback_addr)

        def notify_dart_impl(data_bytes):
            try:
                self._notify_keepalive.append(data_bytes)
                dart_fn(data_bytes)
            except Exception as e:
                print(f"Error notifying Dart: {e}")

        return notify_dart_impl

    def _setup_engine(
        self,
        method_call_handler,
        assets_path: str,
        width: int,
        height: int,
        async_mode: bool = False,
    ):
        """
        Shared setup: validates paths, creates engine + view controller, returns HWND.

        Args:
            method_call_handler: Callable that handles method calls from Dart.
            assets_path: Path to flutter_assets.
            width: Window width.
            height: Window height.
            async_mode: If True, prints "(async mode)" in status messages.

        Returns:
            HWND of the Flutter view, or None if setup failed.
        """
        # Validate paths
        if not os.path.exists(assets_path):
            raise FileNotFoundError(f"Assets path not found: {assets_path}")
        if not os.path.exists(self.icu_path):
            raise FileNotFoundError(f"ICU data not found: {self.icu_path}")
        if not os.path.exists(PATH_FLUT_AOT):
            raise FileNotFoundError(f"AOT library not found at: {PATH_FLUT_AOT}")

        # Setup engine properties
        self._props = FlutterDesktopEngineProperties()
        self._props.assets_path = assets_path
        self._props.icu_data_path = self.icu_path
        self._props.aot_library_path = PATH_FLUT_AOT
        self._props.dart_entrypoint = None
        self._props.dart_entrypoint_argc = 0
        self._props.dart_entrypoint_argv = None
        self._props.gpu_preference = 0
        self._props.ui_thread_policy = 1

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

        NativeCallbackType = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_char_p)
        self._native_callback = NativeCallbackType(on_native_callback)

        callback_addr = ctypes.cast(self._native_callback, ctypes.c_void_p).value

        # Setup argv with callback address
        arg1 = f"--native-callback={callback_addr}"
        self._argv_buffers = [arg1.encode("utf-8")]
        self._argv_ptrs = [ctypes.c_char_p(b) for b in self._argv_buffers]
        self._argv_ptrs.append(None)

        ArgvArray = ctypes.c_char_p * len(self._argv_ptrs)
        argv_c = ArgvArray(*self._argv_ptrs)

        self._props.dart_entrypoint_argc = 1
        self._props.dart_entrypoint_argv = ctypes.cast(
            argv_c, ctypes.POINTER(ctypes.c_char_p)
        )

        mode_str = " (async mode)" if async_mode else ""
        print(f"\nStarting Flutter{mode_str}...")
        print(f"  Assets: {assets_path}")
        print(f"  ICU: {self.icu_path}")
        print(f"  Window: {width}x{height}")

        # Create engine
        self.engine = self.flutter.FlutterDesktopEngineCreate(ctypes.byref(self._props))

        if not self.engine:
            print("ERROR: Failed to create Flutter engine!")
            return None

        print(f"  Engine created: {self.engine}")

        # Create view controller
        self.view_controller = self.flutter.FlutterDesktopViewControllerCreate(
            width, height, self.engine
        )

        if not self.view_controller:
            print("ERROR: Failed to create Flutter view controller!")
            self.engine = None
            return None

        # Get HWND
        view = self.flutter.FlutterDesktopViewControllerGetView(self.view_controller)
        hwnd = self.flutter.FlutterDesktopViewGetHWND(view)

        print(f"\nFlutter is running{mode_str}!")
        print(f"  View controller: {self.view_controller}")
        print(f"  Engine: {self.engine}")
        print(f"  HWND: {hwnd}")
        print(f"\nDart's main() -> runApp() has been triggered!")
        print("Close the window to exit.\n")

        return hwnd

    def run(
        self, method_call_handler, assets_path: str, width: int = 800, height: int = 600
    ):
        """Run Flutter with sync message loop (GetMessageW)."""
        hwnd = self._setup_engine(
            method_call_handler, assets_path, width, height, async_mode=False
        )
        if hwnd is None:
            return False

        self._run_message_loop(hwnd, width, height)
        return True

    def _run_message_loop(self, hwnd, width, height):
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        if ctypes.sizeof(ctypes.c_void_p) == 8:
            LRESULT = ctypes.c_longlong
        else:
            LRESULT = ctypes.c_long

        user32.RegisterClassExW.argtypes = [ctypes.c_void_p]
        user32.RegisterClassExW.restype = wintypes.ATOM
        user32.CreateWindowExW.argtypes = [
            wintypes.DWORD,
            wintypes.LPCWSTR,
            wintypes.LPCWSTR,
            wintypes.DWORD,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.HWND,
            wintypes.HMENU,
            wintypes.HINSTANCE,
            wintypes.LPVOID,
        ]
        user32.CreateWindowExW.restype = wintypes.HWND
        user32.SetParent.argtypes = [wintypes.HWND, wintypes.HWND]
        user32.SetParent.restype = wintypes.HWND
        user32.SetWindowLongPtrW.argtypes = [
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_void_p,
        ]
        user32.SetWindowLongPtrW.restype = ctypes.c_void_p
        user32.SetWindowPos.argtypes = [
            wintypes.HWND,
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.UINT,
        ]
        user32.SetWindowPos.restype = wintypes.BOOL
        user32.DefWindowProcW.argtypes = [
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        ]
        user32.DefWindowProcW.restype = LRESULT
        user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
        user32.GetClientRect.restype = wintypes.BOOL

        WNDPROC = ctypes.WINFUNCTYPE(
            LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
        )

        WM_DESTROY = 0x0002
        WM_SIZE = 0x0005
        WM_PAINT = 0x000F
        WM_ACTIVATE = 0x0006
        WM_SETFOCUS = 0x0007
        WS_OVERLAPPEDWINDOW = 0x00CF0000
        WS_VISIBLE = 0x10000000
        WS_CHILD = 0x40000000
        GWL_STYLE = -16
        SW_SHOW = 5
        SWP_NOZORDER = 0x0004
        SWP_SHOWWINDOW = 0x0040
        SWP_FRAMECHANGED = 0x0020

        def _host_wndproc(host_hwnd, msg, wparam, lparam):
            result = LRESULT(0)
            try:
                handled = (
                    self.flutter.FlutterDesktopViewControllerHandleTopLevelWindowProc(
                        self.view_controller,
                        host_hwnd,
                        msg,
                        wparam,
                        lparam,
                        ctypes.byref(result),
                    )
                )
                if handled:
                    return result.value
            except OSError:
                pass

            if msg == WM_SIZE:
                new_w = lparam & 0xFFFF
                new_h = (lparam >> 16) & 0xFFFF
                user32.SetWindowPos(
                    hwnd, None, 0, 0, new_w, new_h, SWP_NOZORDER | SWP_SHOWWINDOW
                )

            if msg == WM_PAINT:
                try:
                    self.flutter.FlutterDesktopViewControllerForceRedraw(
                        self.view_controller
                    )
                except OSError:
                    pass

            if msg == WM_SETFOCUS or msg == WM_ACTIVATE:
                user32.SetFocus(hwnd)

            if msg == WM_DESTROY:
                user32.PostQuitMessage(0)
                return 0

            return user32.DefWindowProcW(host_hwnd, msg, wparam, lparam)

        self._wndproc = WNDPROC(_host_wndproc)

        HCURSOR = getattr(wintypes, "HCURSOR", wintypes.HANDLE)

        class WNDCLASSEX(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.UINT),
                ("style", wintypes.UINT),
                ("lpfnWndProc", WNDPROC),
                ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int),
                ("hInstance", wintypes.HINSTANCE),
                ("hIcon", wintypes.HICON),
                ("hCursor", HCURSOR),
                ("hbrBackground", wintypes.HBRUSH),
                ("lpszMenuName", wintypes.LPCWSTR),
                ("lpszClassName", wintypes.LPCWSTR),
                ("hIconSm", wintypes.HICON),
            ]

        class_name = "FlutterHostWindow"
        h_instance = kernel32.GetModuleHandleW(None)

        wndclass = WNDCLASSEX()
        wndclass.cbSize = ctypes.sizeof(WNDCLASSEX)
        wndclass.style = 0
        wndclass.lpfnWndProc = self._wndproc
        wndclass.cbClsExtra = 0
        wndclass.cbWndExtra = 0
        wndclass.hInstance = h_instance
        wndclass.hIcon = None
        wndclass.hCursor = user32.LoadCursorW(None, 32512)
        wndclass.hbrBackground = None
        wndclass.lpszMenuName = None
        wndclass.lpszClassName = class_name
        wndclass.hIconSm = None

        user32.RegisterClassExW(ctypes.byref(wndclass))

        host_hwnd = user32.CreateWindowExW(
            0,
            class_name,
            "Flut",
            WS_OVERLAPPEDWINDOW | WS_VISIBLE,
            100,
            100,
            width,
            height,
            None,
            None,
            h_instance,
            None,
        )

        if not host_hwnd:
            print("ERROR: Failed to create host window.")
            return False

        client_rect = wintypes.RECT()
        user32.GetClientRect(host_hwnd, ctypes.byref(client_rect))
        client_w = client_rect.right - client_rect.left
        client_h = client_rect.bottom - client_rect.top

        user32.SetParent(hwnd, host_hwnd)
        user32.SetWindowLongPtrW(hwnd, GWL_STYLE, WS_CHILD | WS_VISIBLE)
        user32.SetWindowPos(
            hwnd,
            None,
            0,
            0,
            client_w,
            client_h,
            SWP_NOZORDER | SWP_SHOWWINDOW | SWP_FRAMECHANGED,
        )
        user32.ShowWindow(hwnd, SW_SHOW)
        user32.UpdateWindow(hwnd)

        user32.ShowWindow(host_hwnd, SW_SHOW)
        user32.UpdateWindow(host_hwnd)

        user32.SetFocus(hwnd)

        self.flutter.FlutterDesktopViewControllerForceRedraw(self.view_controller)

        rect = wintypes.RECT()
        user32.GetWindowRect(host_hwnd, ctypes.byref(rect))
        print(
            f"Host Window Rect: {rect.left}, {rect.top} - {rect.right}, {rect.bottom}"
        )
        if not user32.IsWindow(host_hwnd):
            print("ERROR: Host HWND is not a valid window!")

        class MSG(ctypes.Structure):
            _fields_ = [
                ("hwnd", wintypes.HWND),
                ("message", wintypes.UINT),
                ("wParam", wintypes.WPARAM),
                ("lParam", wintypes.LPARAM),
                ("time", wintypes.DWORD),
                ("pt", wintypes.POINT),
                ("lPrivate", wintypes.DWORD),
            ]

        msg = MSG()

        self._running = True
        print("Entering message loop...")

        WM_QUIT = 0x0012

        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

            if msg.message == WM_QUIT:
                break

        return True

    def shutdown(self):
        if self.view_controller:
            self.flutter.FlutterDesktopViewControllerDestroy(self.view_controller)
            self.view_controller = None
            self.engine = None
            print("Flutter shutdown.")
        elif self.engine:
            self.flutter.FlutterDesktopEngineDestroy(self.engine)
            self.engine = None
            print("Flutter engine shutdown.")

    async def run_async(
        self,
        method_call_handler,
        assets_path: str,
        width: int = 800,
        height: int = 600,
        loop: asyncio.AbstractEventLoop = None,
    ):
        """
        Run Flutter with asyncio integration (async).

        Integrates Windows message loop with asyncio's proactor via IOCP.
        Wakes on either Windows messages or asyncio work, then processes both.

        Args:
            method_call_handler: Callable that handles method calls from Dart.
            assets_path: Path to flutter_assets.
            width: Window width.
            height: Window height.
            loop: Asyncio event loop (uses current if not provided).
        """
        hwnd = self._setup_engine(
            method_call_handler, assets_path, width, height, async_mode=True
        )
        if hwnd is None:
            return False

        # Get or use provided asyncio loop
        if loop is None:
            loop = asyncio.get_running_loop()

        await self._run_async_message_loop(hwnd, width, height, loop)
        return True

    async def _run_async_message_loop(
        self, hwnd, width, height, loop: asyncio.AbstractEventLoop
    ):
        """
        Async message loop integrated with asyncio.

        Waits for either Windows messages OR proactor wake event.
        After waking, processes messages and yields to asyncio.
        """
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        if ctypes.sizeof(ctypes.c_void_p) == 8:
            LRESULT = ctypes.c_longlong
        else:
            LRESULT = ctypes.c_long

        # Set up Win32 API types
        user32.RegisterClassExW.argtypes = [ctypes.c_void_p]
        user32.RegisterClassExW.restype = wintypes.ATOM
        user32.CreateWindowExW.argtypes = [
            wintypes.DWORD,
            wintypes.LPCWSTR,
            wintypes.LPCWSTR,
            wintypes.DWORD,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.HWND,
            wintypes.HMENU,
            wintypes.HINSTANCE,
            wintypes.LPVOID,
        ]
        user32.CreateWindowExW.restype = wintypes.HWND
        user32.SetParent.argtypes = [wintypes.HWND, wintypes.HWND]
        user32.SetParent.restype = wintypes.HWND
        user32.SetWindowLongPtrW.argtypes = [
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_void_p,
        ]
        user32.SetWindowLongPtrW.restype = ctypes.c_void_p
        user32.SetWindowPos.argtypes = [
            wintypes.HWND,
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.UINT,
        ]
        user32.SetWindowPos.restype = wintypes.BOOL
        user32.DefWindowProcW.argtypes = [
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        ]
        user32.DefWindowProcW.restype = LRESULT
        user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
        user32.GetClientRect.restype = wintypes.BOOL

        # MsgWaitForMultipleObjectsEx
        user32.MsgWaitForMultipleObjectsEx.argtypes = [
            wintypes.DWORD,  # nCount
            ctypes.POINTER(wintypes.HANDLE),  # pHandles
            wintypes.DWORD,  # dwMilliseconds
            wintypes.DWORD,  # dwWakeMask
            wintypes.DWORD,  # dwFlags
        ]
        user32.MsgWaitForMultipleObjectsEx.restype = wintypes.DWORD

        # PeekMessageW for non-blocking message retrieval
        user32.PeekMessageW.argtypes = [
            ctypes.c_void_p,
            wintypes.HWND,
            wintypes.UINT,
            wintypes.UINT,
            wintypes.UINT,
        ]
        user32.PeekMessageW.restype = wintypes.BOOL

        WNDPROC = ctypes.WINFUNCTYPE(
            LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
        )

        # Window messages
        WM_DESTROY = 0x0002
        WM_SIZE = 0x0005
        WM_PAINT = 0x000F
        WM_ACTIVATE = 0x0006
        WM_SETFOCUS = 0x0007
        WM_QUIT = 0x0012
        WS_OVERLAPPEDWINDOW = 0x00CF0000
        WS_VISIBLE = 0x10000000
        WS_CHILD = 0x40000000
        GWL_STYLE = -16
        SW_SHOW = 5
        SWP_NOZORDER = 0x0004
        SWP_SHOWWINDOW = 0x0040
        SWP_FRAMECHANGED = 0x0020

        # Track if we should quit
        should_quit = False

        def _host_wndproc(host_hwnd, msg, wparam, lparam):
            nonlocal should_quit
            result = LRESULT(0)
            try:
                handled = (
                    self.flutter.FlutterDesktopViewControllerHandleTopLevelWindowProc(
                        self.view_controller,
                        host_hwnd,
                        msg,
                        wparam,
                        lparam,
                        ctypes.byref(result),
                    )
                )
                if handled:
                    return result.value
            except OSError:
                pass

            if msg == WM_SIZE:
                new_w = lparam & 0xFFFF
                new_h = (lparam >> 16) & 0xFFFF
                user32.SetWindowPos(
                    hwnd, None, 0, 0, new_w, new_h, SWP_NOZORDER | SWP_SHOWWINDOW
                )

            if msg == WM_PAINT:
                try:
                    self.flutter.FlutterDesktopViewControllerForceRedraw(
                        self.view_controller
                    )
                except OSError:
                    pass

            if msg == WM_SETFOCUS or msg == WM_ACTIVATE:
                user32.SetFocus(hwnd)

            if msg == WM_DESTROY:
                should_quit = True
                user32.PostQuitMessage(0)
                return 0

            return user32.DefWindowProcW(host_hwnd, msg, wparam, lparam)

        self._wndproc = WNDPROC(_host_wndproc)

        HCURSOR = getattr(wintypes, "HCURSOR", wintypes.HANDLE)

        class WNDCLASSEX(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.UINT),
                ("style", wintypes.UINT),
                ("lpfnWndProc", WNDPROC),
                ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int),
                ("hInstance", wintypes.HINSTANCE),
                ("hIcon", wintypes.HICON),
                ("hCursor", HCURSOR),
                ("hbrBackground", wintypes.HBRUSH),
                ("lpszMenuName", wintypes.LPCWSTR),
                ("lpszClassName", wintypes.LPCWSTR),
                ("hIconSm", wintypes.HICON),
            ]

        class_name = "FlutterHostWindowAsync"
        h_instance = kernel32.GetModuleHandleW(None)

        wndclass = WNDCLASSEX()
        wndclass.cbSize = ctypes.sizeof(WNDCLASSEX)
        wndclass.style = 0
        wndclass.lpfnWndProc = self._wndproc
        wndclass.cbClsExtra = 0
        wndclass.cbWndExtra = 0
        wndclass.hInstance = h_instance
        wndclass.hIcon = None
        wndclass.hCursor = user32.LoadCursorW(None, 32512)
        wndclass.hbrBackground = None
        wndclass.lpszMenuName = None
        wndclass.lpszClassName = class_name
        wndclass.hIconSm = None

        user32.RegisterClassExW(ctypes.byref(wndclass))

        host_hwnd = user32.CreateWindowExW(
            0,
            class_name,
            "Flut (Async)",
            WS_OVERLAPPEDWINDOW | WS_VISIBLE,
            100,
            100,
            width,
            height,
            None,
            None,
            h_instance,
            None,
        )

        if not host_hwnd:
            print("ERROR: Failed to create host window.")
            return False

        client_rect = wintypes.RECT()
        user32.GetClientRect(host_hwnd, ctypes.byref(client_rect))
        client_w = client_rect.right - client_rect.left
        client_h = client_rect.bottom - client_rect.top

        user32.SetParent(hwnd, host_hwnd)
        user32.SetWindowLongPtrW(hwnd, GWL_STYLE, WS_CHILD | WS_VISIBLE)
        user32.SetWindowPos(
            hwnd,
            None,
            0,
            0,
            client_w,
            client_h,
            SWP_NOZORDER | SWP_SHOWWINDOW | SWP_FRAMECHANGED,
        )
        user32.ShowWindow(hwnd, SW_SHOW)
        user32.UpdateWindow(hwnd)

        user32.ShowWindow(host_hwnd, SW_SHOW)
        user32.UpdateWindow(host_hwnd)

        user32.SetFocus(hwnd)

        self.flutter.FlutterDesktopViewControllerForceRedraw(self.view_controller)

        rect = wintypes.RECT()
        user32.GetWindowRect(host_hwnd, ctypes.byref(rect))
        print(
            f"Host Window Rect: {rect.left}, {rect.top} - {rect.right}, {rect.bottom}"
        )

        # Set up wake event that bridges proactor's IOCP to MsgWait
        wake_bridge = ProactorWakeEvent()
        wake_event = wake_bridge.setup(loop)

        print(f"Proactor wake event: {wake_event}")

        class MSG(ctypes.Structure):
            _fields_ = [
                ("hwnd", wintypes.HWND),
                ("message", wintypes.UINT),
                ("wParam", wintypes.WPARAM),
                ("lParam", wintypes.LPARAM),
                ("time", wintypes.DWORD),
                ("pt", wintypes.POINT),
                ("lPrivate", wintypes.DWORD),
            ]

        msg = MSG()
        handles_array = (wintypes.HANDLE * 1)(wake_event)

        self._running = True

        try:
            while not should_quit:
                # Wait for Windows messages OR proactor wake event (IOCP has work)
                result = user32.MsgWaitForMultipleObjectsEx(
                    1,  # one handle
                    handles_array,  # wake event
                    INFINITE,  # no timeout - event wakes us when IOCP has work
                    QS_ALLINPUT,
                    MWMO_INPUTAVAILABLE,
                )

                if result == WAIT_FAILED:
                    error = kernel32.GetLastError()
                    print(f"MsgWaitForMultipleObjectsEx failed: {error}")
                    break

                # Process Windows messages
                while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_REMOVE):
                    if msg.message == WM_QUIT:
                        should_quit = True
                        break
                    user32.TranslateMessage(ctypes.byref(msg))
                    user32.DispatchMessageW(ctypes.byref(msg))

                if should_quit:
                    break

                # Yield to asyncio - let it process callbacks with proper task context
                await asyncio.sleep(0)

        finally:
            wake_bridge.cleanup()

        return True

    @staticmethod
    def get_default_assets_path() -> str:
        return PATH_FLUT_ASSETS
