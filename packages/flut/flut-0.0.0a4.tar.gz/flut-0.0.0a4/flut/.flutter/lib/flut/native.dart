import 'dart:async';
import 'dart:convert';
import 'dart:ffi' as ffi;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:ffi/ffi.dart';

// When Dart calls Python, used by invokeNativeSync
typedef _NativePythonFunction = ffi.Pointer<Utf8> Function(ffi.Pointer<Utf8>);

// When Python calls Dart, used for callbacks
typedef _NativePythonToDartFunction = ffi.Pointer<Utf8> Function(ffi.Pointer<Utf8>);

// When Python notifies Dart of set state
typedef _NativeSetStateFunction = ffi.Void Function(ffi.Pointer<Utf8>);

/// Interface for states that need to receive updates from Python
abstract class FlutState {
  void updateFromPython(Map<String, dynamic>? newSubtree);
}

abstract class FlutNative {
  Map<String, FlutState> get stateRegistry;
  Map<String, TextEditingController> get controllerRegistry;
  Map<String, FocusNode> get focusNodeRegistry;

  dynamic invokeNativeSync(String type, Map<String, dynamic> data);
  void invokeNativeNoWaitSync(String type, Map<String, dynamic> data);
  Future<dynamic> invokeNativeAsync(String type, Map<String, dynamic> data);

  void triggerAction(String actionId, Map<String, dynamic> extraData);

  TextEditingController getOrCreateController(
    String id,
    String? controllerText,
  );
  Map<String, String> getControllerValues();
  FocusNode getOrCreateFocusNode(
    String id,
    bool hasOnKeyEvent,
    BuildContext context,
  );
  Map<String, dynamic> captureContextSnapshot(BuildContext context);

  void dispose();
}

class FlutFfiNative implements FlutNative {
  static FlutFfiNative? _instance;

  final int nativeCallbackAddr;

  // Global registries
  @override
  final Map<String, FlutState> stateRegistry = {};
  @override
  final Map<String, TextEditingController> controllerRegistry = {};
  @override
  final Map<String, FocusNode> focusNodeRegistry = {};

  // FFI Resources
  ffi.NativeCallable<_NativePythonToDartFunction>? _dartCallCallable;
  ffi.NativeCallable<_NativeSetStateFunction>? _setStateCallable;
  ffi.Pointer<Utf8>? _callResponseBuffer;

  FlutFfiNative(this.nativeCallbackAddr) {
    if (_instance != null) {
      throw Exception("FlutFfiNative already initialized");
    }
    _instance = this;
    _registerDartCallbackWithPython();
  }

  @override
  void dispose() {
    _instance = null;
    if (_callResponseBuffer != null) {
      calloc.free(_callResponseBuffer!);
      _callResponseBuffer = null;
    }
    _dartCallCallable?.close();
    _setStateCallable?.close();
  }

  // ===========================================================================
  // FFI Invocation
  // ===========================================================================

  @override
  dynamic invokeNativeSync(String type, Map<String, dynamic> data) {
    final req = jsonEncode({"type": type, "data": data});
    final reqPtr = req.toNativeUtf8();

    try {
      final ptr = ffi.Pointer<ffi.NativeFunction<_NativePythonFunction>>.fromAddress(
        nativeCallbackAddr,
      );
      final function = ptr.asFunction<_NativePythonFunction>();
      final resPtr = function(reqPtr);

      if (resPtr == ffi.nullptr) return null;

      final resJson = resPtr.toDartString();
      return jsonDecode(resJson);
    } finally {
      calloc.free(reqPtr);
    }
  }

  /// Invoke the native callback without synchronous dependency on result.
  /// Fire-and-forget: does NOT return a result.
  @override
  void invokeNativeNoWaitSync(String type, Map<String, dynamic> data) {
    Future<dynamic>(() {
      try {
        invokeNativeSync(type, data);
      } catch (e, st) {
        debugPrint('Error in invokeNativeNoWaitSync($type): $e');
        assert(() {
          debugPrint(st.toString());
          return true;
        }());
      }
    });
  }

  /// Invoke the native callback asynchronously and return the result.
  /// Dart UI doesn't block, but Python processes on main thread where call_dart works.
  @override
  Future<dynamic> invokeNativeAsync(String type, Map<String, dynamic> data) {
    return Future<dynamic>(() {
      try {
        return invokeNativeSync(type, data);
      } catch (e, st) {
        debugPrint('Error in invokeNativeAsync($type): $e');
        assert(() {
          debugPrint(st.toString());
          return true;
        }());
        return null;
      }
    });
  }

  // ===========================================================================
  // Action Triggering
  // ===========================================================================

  /// Trigger an action to be processed on Python's main thread.
  /// Uses invokeNativeAsync so Dart UI doesn't block, but Python processes
  /// synchronously on its main thread where call_dart works.
  @override
  void triggerAction(String actionId, Map<String, dynamic> extraData) {
    final actionData = {
      'id': actionId,
      'controllers': getControllerValues(),
      ...extraData,
    };
    // Dart doesn't block, Python processes on main thread
    invokeNativeAsync('action', actionData);
  }

  // ===========================================================================
  // Controller & Focus Logic
  // ===========================================================================

  /// Get all controller values to send with actions
  @override
  Map<String, String> getControllerValues() {
    final values = <String, String>{};
    for (final entry in controllerRegistry.entries) {
      values[entry.key] = entry.value.text;
    }
    return values;
  }

  /// Get or create a TextEditingController by ID
  @override
  TextEditingController getOrCreateController(
    String id,
    String? controllerText,
  ) {
    if (!controllerRegistry.containsKey(id)) {
      controllerRegistry[id] = TextEditingController(
        text: controllerText ?? '',
      );
    } else if (controllerText != null &&
        controllerRegistry[id]!.text != controllerText) {
      controllerRegistry[id]!.text = controllerText;
    }
    return controllerRegistry[id]!;
  }

  /// Get or create a FocusNode by ID with optional onKeyEvent callback
  @override
  FocusNode getOrCreateFocusNode(
    String id,
    bool hasOnKeyEvent,
    BuildContext context,
  ) {
    if (!focusNodeRegistry.containsKey(id)) {
      final focusNode = FocusNode();
      if (hasOnKeyEvent) {
        focusNode.onKeyEvent = (node, event) {
          // Only handle key down events
          if (event is! KeyDownEvent) {
            return KeyEventResult.ignored;
          }

          final keyData = {
            'key': event.logicalKey.keyLabel,
            'keyId': event.logicalKey.keyId,
            'isKeyDown': true,
            'isShiftPressed': HardwareKeyboard.instance.isShiftPressed,
            'isControlPressed': HardwareKeyboard.instance.isControlPressed,
            'isAltPressed': HardwareKeyboard.instance.isAltPressed,
            'isMetaPressed': HardwareKeyboard.instance.isMetaPressed,
          };

          final result = triggerKeyEventSync(id, keyData, context);

          switch (result) {
            case 'handled':
              return KeyEventResult.handled;
            case 'skipRemainingHandlers':
              return KeyEventResult.skipRemainingHandlers;
            default:
              return KeyEventResult.ignored;
          }
        };
      }
      focusNodeRegistry[id] = focusNode;
    }
    return focusNodeRegistry[id]!;
  }

  /// Trigger a key event synchronously and get the result
  String triggerKeyEventSync(
    String focusNodeId,
    Map<String, dynamic> keyData,
    BuildContext context,
  ) {
    final payload = {
      'type': 'key_event',
      'focusNodeId': focusNodeId,
      'keyData': keyData,
      'controllers': getControllerValues(),
      'context': captureContextSnapshot(context),
    };

    final result = invokeNativeSync('key_event', payload);
    String keyResult = 'ignored';
    if (result != null) {
      try {
        keyResult = result['result'] ?? 'ignored';
      } catch (e) {
        // ignore
      }
    }

    if (keyResult == 'handled') {
      final focusNode = focusNodeRegistry[focusNodeId];
      if (focusNode != null && focusNode.hasFocus) {
        focusNode.unfocus();
      }
    }

    return keyResult;
  }

  @override
  Map<String, dynamic> captureContextSnapshot(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    return {
      'theme': {
        'useMaterial3': theme.useMaterial3,
        'colorScheme': {'inversePrimary': scheme.inversePrimary.value},
      },
    };
  }

  // ===========================================================================
  // Callbacks
  // ===========================================================================

  void _registerDartCallbackWithPython() {
    _dartCallCallable =
        ffi.NativeCallable<_NativePythonToDartFunction>.isolateLocal(
          _handlePythonCallImpl,
        );

    final callCallbackAddr = _dartCallCallable!.nativeFunction.address;
    invokeNativeSync('register_dart_callback', {
      'callback_addr': callCallbackAddr,
    });

    _setStateCallable =
        ffi.NativeCallable<_NativeSetStateFunction>.listener(
          _onSetState,
        );

    final notifyCallbackAddr = _setStateCallable!.nativeFunction.address;
    invokeNativeSync('register_set_state_callback', {
      'callback_addr': notifyCallbackAddr,
    });
  }

  static ffi.Pointer<Utf8> _handlePythonCallImpl(
    ffi.Pointer<Utf8> requestPtr,
  ) {
    if (_instance == null) {
      return '{"error": "No bridge active"}'.toNativeUtf8();
    }

    final instance = _instance!;

    try {
      final reqJson = requestPtr.toDartString();
      final request = jsonDecode(reqJson) as Map<String, dynamic>;
      final callType = request['type'] as String?;
      final data = request['data'] as Map<String, dynamic>? ?? {};

      Map<String, dynamic>? response;

      if (callType == 'get_controller_text') {
        final controllerId = data['id'] as String?;
        final ctrl = instance.controllerRegistry[controllerId];

        if (controllerId != null && ctrl != null) {
          response = {'text': ctrl.text};
        } else {
          response = {'error': 'Controller not found', 'id': controllerId};
        }
      } else {
        response = {'error': 'Unknown call type', 'type': callType};
      }

      // Buffer management...
      if (instance._callResponseBuffer != null) {
        calloc.free(instance._callResponseBuffer!);
      }

      final responseJson = jsonEncode(response);
      instance._callResponseBuffer = responseJson.toNativeUtf8();
      return instance._callResponseBuffer!;
    } catch (e) {
      debugPrint('Error handling Python call: $e');
      instance._callResponseBuffer = '{"error": "exception"}'.toNativeUtf8();
      return instance._callResponseBuffer!;
    }
  }

  static void _onSetState(ffi.Pointer<Utf8> dataPtr) {
    if (_instance == null) return;

    try {
      final jsonStr = dataPtr.toDartString();
      if (jsonStr.isEmpty) return;

      final id = jsonDecode(jsonStr);
      if (id is String) {
        // Handle single ID (optimized)
        final state = _instance!.stateRegistry[id];
        state?.updateFromPython(null);
      }
    } catch (e) {
      debugPrint('Error handling Python notify: $e');
    }
  }
}
