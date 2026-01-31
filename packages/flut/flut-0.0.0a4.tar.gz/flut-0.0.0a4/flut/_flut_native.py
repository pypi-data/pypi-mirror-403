from abc import ABC, abstractmethod


class FlutNative(ABC):
    """Abstract base class for platform-specific FFI operations."""

    @abstractmethod
    def initialize(self):
        """Load native libraries."""
        pass

    @abstractmethod
    def run(self, method_call_handler, assets_path: str, width: int, height: int):
        """Run the Flutter engine with window and message loop.
        
        Args:
            method_call_handler: Callable that handles method calls from Dart.
            assets_path: Path to flutter_assets.
            width: Window width.
            height: Window height.
        """
        pass

    @abstractmethod
    def setup_call_dart(self, callback_addr):
        """Set up FFI callback for synchronous Python → Dart calls.
        
        Returns a callable: (call_type: str, data: dict) -> dict | None
        """
        pass

    @abstractmethod
    def setup_notify_dart(self, callback_addr):
        """Set up FFI callback for async notifications to Dart.
        
        Returns a callable: (data_bytes: bytes) -> None
        """
        pass

    @abstractmethod
    def shutdown(self):
        """Clean up native resources."""
        pass

    @staticmethod
    def get_default_assets_path() -> str:
        """Return the default path to flutter_assets for this platform."""
        raise NotImplementedError

