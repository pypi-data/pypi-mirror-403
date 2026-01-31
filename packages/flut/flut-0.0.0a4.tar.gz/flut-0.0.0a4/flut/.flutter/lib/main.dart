import 'package:flutter/material.dart';
import 'flut/native.dart';

late final FlutNative flutNative;

void main(List<String> args) {
  int? nativeCallbackAddr;
  for (final arg in args) {
    if (arg.startsWith('--native-callback=')) {
      nativeCallbackAddr = int.tryParse(
        arg.substring('--native-callback='.length),
      );
    }
  }

  flutNative = FlutFfiNative(nativeCallbackAddr ?? 0);

  runApp(const RootPythonWidget());
}

// =============================================================================
// Root Widget - Fetches initial tree from Python
// =============================================================================

class RootPythonWidget extends StatefulWidget {
  const RootPythonWidget({super.key});

  @override
  State<RootPythonWidget> createState() => _RootPythonWidgetState();
}

class _RootPythonWidgetState extends State<RootPythonWidget> {
  Map<String, dynamic>? _rootData;
  String? _error;

  @override
  void initState() {
    super.initState();
    _fetchInitialTree();
  }

  void _fetchInitialTree() {
    try {
      _rootData = flutNative.invokeNativeSync("widget_build", {});
    } catch (e) {
      _error = e.toString();
    }
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    if (_error != null) {
      return MaterialApp(
        home: Scaffold(
          body: Center(
            child: Text(
              "Error: $_error",
              style: const TextStyle(color: Colors.red),
            ),
          ),
        ),
      );
    }
    if (_rootData == null) {
      return const MaterialApp(
        home: Scaffold(body: Center(child: CircularProgressIndicator())),
      );
    }
    return buildWidgetFromJson(_rootData!);
  }
}

// =============================================================================
// PythonProxyWidget - Dart-side proxy that maintains Element tree persistence
// =============================================================================

class PythonProxyWidget extends StatefulWidget {
  final String pythonId;
  final String className;
  final bool isStateful;

  const PythonProxyWidget({
    required this.pythonId,
    required this.className,
    required this.isStateful,
    super.key,
  });

  @override
  State<PythonProxyWidget> createState() => _PythonProxyState();
}

class _PythonProxyState extends State<PythonProxyWidget> implements FlutState {
  Map<String, dynamic>? _cachedSubtree;
  bool _needsBuild = true;

  @override
  void initState() {
    super.initState();
    // Register this State in the global registry so we can find it by ID
    flutNative.stateRegistry[widget.pythonId] = this;
  }

  @override
  void dispose() {
    // Unregister when disposed
    flutNative.stateRegistry.remove(widget.pythonId);
    super.dispose();
  }

  /// Called when we receive an update (triggered by action callback return or notify)
  @override
  void updateFromPython(Map<String, dynamic>? newSubtree) {
    // Use Flutter's native setState to trigger reconciliation
    setState(() {
      if (newSubtree != null) {
        _cachedSubtree = newSubtree;
        _needsBuild = false;
      } else {
        // If no subtree provided, it means we need to fetch it (dirty)
        _needsBuild = true;
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    // If we need to build (first time), ask Python
    if (_needsBuild) {
      try {
        _cachedSubtree = flutNative.invokeNativeSync('widget_build', {
          'id': widget.pythonId,
          'context': flutNative.captureContextSnapshot(context),
        });
        _needsBuild = false;
      } catch (e) {
        return Text('Build error: $e');
      }
    }

    if (_cachedSubtree == null) {
      return const SizedBox.shrink();
    }

    return buildWidgetFromJson(_cachedSubtree!);
  }
}

// =============================================================================
// Theme Builder
// =============================================================================

ThemeData _buildThemeData(Map<String, dynamic>? data) {
  final useMaterial3 = (data?['useMaterial3'] as bool?) ?? true;
  final colorSchemeData = data?['colorScheme'];
  final seedColor = (colorSchemeData is Map)
      ? (colorSchemeData['seedColor'] as int?)
      : null;

  // Match Flutter's default template behavior as closely as possible.
  if (seedColor != null) {
    return ThemeData(
      colorSchemeSeed: Color(seedColor),
      useMaterial3: useMaterial3,
    );
  }

  return ThemeData(useMaterial3: useMaterial3);
}

// =============================================================================
// JSON to Widget Builder
// =============================================================================

Widget buildWidgetFromJson(Map<String, dynamic> data) {
  final type = data['type'];

  // Handle Python proxy widgets - these get their own State in Dart
  if (type == 'PythonStatefulWidget') {
    return PythonProxyWidget(
      key: ValueKey(data['id']), // Key ensures Element tree stability!
      pythonId: data['id'],
      className: data['className'],
      isStateful: true,
    );
  }

  if (type == 'PythonStatelessWidget') {
    return PythonProxyWidget(
      key: ValueKey(data['id']),
      pythonId: data['id'],
      className: data['className'],
      isStateful: false,
    );
  }

  // Handle primitive widgets
  final child = data['child'] != null
      ? buildWidgetFromJson(data['child'])
      : null;

  switch (type) {
    case 'MaterialApp':
      return MaterialApp(
        title: data['title'] ?? 'Flut',
        theme: _buildThemeData(data['theme']),
        home: data['home'] != null ? buildWidgetFromJson(data['home']) : null,
      );
    case 'Scaffold':
      return Scaffold(
        appBar: data['appBar'] != null
            ? buildWidgetFromJson(data['appBar']) as PreferredSizeWidget?
            : null,
        body: data['body'] != null ? buildWidgetFromJson(data['body']) : null,
        floatingActionButton: data['floatingActionButton'] != null
            ? buildWidgetFromJson(data['floatingActionButton'])
            : null,
      );
    case 'AppBar':
      final titleWidget = data['title'] != null
          ? buildWidgetFromJson(data['title'])
          : null;
      final background = data['backgroundColor'];

      if (background is Map && background['ref'] is String) {
        final ref = background['ref'] as String;
        if (ref == 'theme.colorScheme.inversePrimary') {
          return PreferredSize(
            preferredSize: const Size.fromHeight(kToolbarHeight),
            child: Builder(
              builder: (context) => AppBar(
                backgroundColor: Theme.of(context).colorScheme.inversePrimary,
                title: titleWidget,
              ),
            ),
          );
        }
      }

      Color? backgroundColor;
      if (background is int) {
        backgroundColor = Color(background);
      }

      return AppBar(backgroundColor: backgroundColor, title: titleWidget);
    case 'FloatingActionButton':
      return Builder(
        builder: (context) => FloatingActionButton(
          onPressed: () =>
              _triggerActionAsync(data['onPressedId'] ?? '', context),
          child: child,
        ),
      );
    case 'Icon':
      final iconColor = data['color'] != null ? Color(data['color']) : null;
      final iconSize = (data['size'] as num?)?.toDouble();
      final codePoint = (data['codePoint'] as num).toInt();
      return Icon(
        IconData(codePoint, fontFamily: 'MaterialIcons'),
        color: iconColor,
        size: iconSize,
      );
    case 'Text':
      final style = data['style'];
      final textData = data['data']?.toString() ?? '';
      final selectable = data['selectable'] ?? false;
      final maxLines = data['maxLines'] as int?;

      // If style is a theme ref, resolve it honestly using Flutter's Theme.
      if (style is Map && style['ref'] is String) {
        final ref = style['ref'] as String;
        if (ref.startsWith('theme.textTheme.')) {
          final name = ref.substring('theme.textTheme.'.length);
          return Builder(
            builder: (context) {
              final textTheme = Theme.of(context).textTheme;
              final resolved = switch (name) {
                'headlineMedium' => textTheme.headlineMedium,
                'headlineSmall' => textTheme.headlineSmall,
                'titleLarge' => textTheme.titleLarge,
                'bodyLarge' => textTheme.bodyLarge,
                'bodyMedium' => textTheme.bodyMedium,
                _ => null,
              };
              if (selectable) {
                return SelectableText(
                  textData,
                  style: resolved,
                  maxLines: maxLines,
                );
              }
              return Text(textData, style: resolved, maxLines: maxLines);
            },
          );
        }
      }

      // If Python omitted style entirely, allow Flutter to use the ambient
      // DefaultTextStyle/Theme.
      if (style == null) {
        if (selectable) {
          return SelectableText(textData, maxLines: maxLines);
        }
        return Text(textData, maxLines: maxLines);
      }

      final styleMap = (style is Map) ? style : const <String, dynamic>{};
      final parsedStyle = _parseTextStyle(styleMap);
      if (selectable) {
        return SelectableText(textData, style: parsedStyle, maxLines: maxLines);
      }
      return Text(textData, style: parsedStyle, maxLines: maxLines);
    case 'Center':
      return Center(child: child);
    case 'Column':
      final children =
          (data['children'] as List?)
              ?.map((c) => buildWidgetFromJson(c as Map<String, dynamic>))
              .toList() ??
          [];

      return Column(
        mainAxisAlignment: _parseMainAxisAlignment(data['mainAxisAlignment']),
        crossAxisAlignment: _parseCrossAxisAlignment(
          data['crossAxisAlignment'],
        ),
        children: children,
      );
    case 'ElevatedButton':
      return Builder(
        builder: (context) => ElevatedButton(
          onPressed: () =>
              _triggerActionAsync(data['onPressedId'] ?? '', context),
          child: child ?? const Text('Button'),
        ),
      );
    case 'AnimatedOpacity':
      return AnimatedOpacity(
        opacity: (data['opacity'] as num?)?.toDouble() ?? 1.0,
        duration: Duration(
          milliseconds: (data['duration'] as num?)?.toInt() ?? 300,
        ),
        child: child,
      );
    case 'CustomPaint':
      final size = data['size'] ?? [0, 0];
      return CustomPaint(
        size: Size(
          (size[0] as num?)?.toDouble() ?? 0,
          (size[1] as num?)?.toDouble() ?? 0,
        ),
        painter: _JSONPainter(data['painter']),
        child: child,
      );
    case 'Container':
      return _buildContainer(data);
    case 'Row':
      return _buildRow(data);
    case 'Stack':
      return _buildStack(data);
    case 'Positioned':
      return _buildPositioned(data);
    case 'ListView':
      return _buildListView(data);
    case 'SingleChildScrollView':
      return SingleChildScrollView(
        padding: _parseEdgeInsets(data['padding']),
        scrollDirection: data['scrollDirection'] == 'horizontal'
            ? Axis.horizontal
            : Axis.vertical,
        child: child,
      );
    case 'TextField':
      return _buildTextField(data);
    case 'GestureDetector':
      return _buildGestureDetector(data);
    case 'InkWell':
      return _buildInkWell(data);
    case 'MouseRegion':
      return _buildMouseRegion(data);
    case 'IconButton':
      return _buildIconButton(data);
    case 'CircularProgressIndicator':
      return CircularProgressIndicator(
        strokeWidth: (data['strokeWidth'] as num?)?.toDouble() ?? 4.0,
        color: data['color'] != null ? Color(data['color']) : null,
      );
    case 'Divider':
      return Divider(
        height: (data['height'] as num?)?.toDouble() ?? 1,
        thickness: (data['thickness'] as num?)?.toDouble() ?? 1,
        color: data['color'] != null ? Color(data['color']) : null,
      );
    case 'Padding':
      return Padding(
        padding: _parseEdgeInsets(data['padding']) ?? EdgeInsets.zero,
        child: child,
      );
    case 'Align':
      return Align(alignment: _parseAlignment(data['alignment']), child: child);
    case 'Visibility':
      return Visibility(
        visible: data['visible'] ?? true,
        child: child ?? const SizedBox.shrink(),
      );
    case 'Opacity':
      return Opacity(
        opacity: (data['opacity'] as num?)?.toDouble() ?? 1.0,
        child: child,
      );
    case 'ClipRRect':
      return ClipRRect(
        borderRadius: _parseBorderRadius(data['borderRadius']),
        child: child,
      );
    case 'Card':
      return Card(
        color: data['color'] != null ? Color(data['color']) : null,
        elevation: (data['elevation'] as num?)?.toDouble(),
        margin: _parseEdgeInsets(data['margin']),
        child: child,
      );
    case 'Spacer':
      return Spacer(flex: (data['flex'] as num?)?.toInt() ?? 1);
    case 'Expanded':
      return Expanded(
        flex: (data['flex'] as num?)?.toInt() ?? 1,
        child: child ?? const SizedBox.shrink(),
      );
    case 'Flexible':
      return Flexible(
        flex: (data['flex'] as num?)?.toInt() ?? 1,
        fit: data['fit'] == 'tight' ? FlexFit.tight : FlexFit.loose,
        child: child ?? const SizedBox.shrink(),
      );
    case 'SizedBox':
      return SizedBox(
        width: (data['width'] as num?)?.toDouble(),
        height: (data['height'] as num?)?.toDouble(),
        child: child,
      );
    default:
      return Text("Unknown Widget: $type");
  }
}

// =============================================================================
// Widget Builders
// =============================================================================

Widget _buildContainer(Map<String, dynamic> data) {
  final child = data['child'] != null
      ? buildWidgetFromJson(data['child'])
      : null;
  final decoration = _parseBoxDecoration(data['decoration']);

  return Container(
    padding: _parseEdgeInsets(data['padding']),
    margin: _parseEdgeInsets(data['margin']),
    width: (data['width'] as num?)?.toDouble(),
    height: (data['height'] as num?)?.toDouble(),
    color: decoration == null && data['color'] != null
        ? Color(data['color'])
        : null,
    decoration: decoration,
    alignment: _parseAlignmentNullable(data['alignment']),
    child: child,
  );
}

Widget _buildRow(Map<String, dynamic> data) {
  final children =
      (data['children'] as List?)
          ?.map((c) => buildWidgetFromJson(c as Map<String, dynamic>))
          .toList() ??
      [];

  return Row(
    mainAxisAlignment: _parseMainAxisAlignment(data['mainAxisAlignment']),
    crossAxisAlignment: _parseCrossAxisAlignment(data['crossAxisAlignment']),
    children: children,
  );
}

Widget _buildStack(Map<String, dynamic> data) {
  final children =
      (data['children'] as List?)
          ?.map((c) => buildWidgetFromJson(c as Map<String, dynamic>))
          .toList() ??
      [];

  return Stack(children: children);
}

Widget _buildPositioned(Map<String, dynamic> data) {
  final child = data['child'] != null
      ? buildWidgetFromJson(data['child'])
      : null;

  return Positioned(
    left: (data['left'] as num?)?.toDouble(),
    top: (data['top'] as num?)?.toDouble(),
    right: (data['right'] as num?)?.toDouble(),
    bottom: (data['bottom'] as num?)?.toDouble(),
    width: (data['width'] as num?)?.toDouble(),
    height: (data['height'] as num?)?.toDouble(),
    child: child ?? const SizedBox.shrink(),
  );
}

Widget _buildListView(Map<String, dynamic> data) {
  final children =
      (data['children'] as List?)
          ?.map((c) => buildWidgetFromJson(c as Map<String, dynamic>))
          .toList() ??
      [];
  final spacing = (data['spacing'] as num?)?.toDouble() ?? 0;
  final reverse = data['reverse'] as bool? ?? false;

  if (spacing > 0) {
    final spacedChildren = <Widget>[];
    for (int i = 0; i < children.length; i++) {
      spacedChildren.add(children[i]);
      if (i < children.length - 1) {
        spacedChildren.add(SizedBox(height: spacing));
      }
    }
    return ListView(
      padding: _parseEdgeInsets(data['padding']),
      reverse: reverse,
      children: spacedChildren,
    );
  }

  return ListView(
    padding: _parseEdgeInsets(data['padding']),
    reverse: reverse,
    children: children,
  );
}

Widget _buildTextField(Map<String, dynamic> data) {
  final controllerId = data['controllerId'] as String?;
  final controllerText = data['controllerText'] as String?;
  final focusNodeData = data['focusNode'] as Map<String, dynamic>?;

  return Builder(
    builder: (context) {
      // If controller is specified, use it
      TextEditingController? controller;
      if (controllerId != null) {
        controller = flutNative.getOrCreateController(
          controllerId,
          controllerText,
        );
      }

      // If focusNode is specified, use it
      FocusNode? focusNode;
      if (focusNodeData != null) {
        final focusNodeId = focusNodeData['id'] as String;
        final hasOnKeyEvent = focusNodeData['hasOnKeyEvent'] as bool? ?? false;
        focusNode = flutNative.getOrCreateFocusNode(
          focusNodeId,
          hasOnKeyEvent,
          context,
        );
      }

      return TextField(
        key: ValueKey(data['id']),
        controller: controller,
        focusNode: focusNode,
        readOnly: data['readOnly'] ?? false,
        maxLines: data['maxLines'], // null means unlimited (multiline)
        minLines: data['minLines'],
        decoration: _parseInputDecoration(data['decoration']),
        style: _parseTextStyle(data['style']),
        onChanged: data['onChangedId'] != null
            ? (value) => _triggerActionWithValueAsync(
                data['onChangedId'],
                value,
                context,
              )
            : null,
        onSubmitted: data['onSubmittedId'] != null
            ? (value) => _triggerActionWithValueAsync(
                data['onSubmittedId'],
                value,
                context,
              )
            : null,
      );
    },
  );
}

Widget _buildGestureDetector(Map<String, dynamic> data) {
  final child = data['child'] != null
      ? buildWidgetFromJson(data['child'])
      : null;

  return Builder(
    builder: (context) => GestureDetector(
      onTap: data['onTapId'] != null
          ? () => _triggerActionAsync(data['onTapId'], context)
          : null,
      onPanStart: data['onPanStartId'] != null
          ? (details) => _triggerActionWithDragStartDetails(
              data['onPanStartId'],
              details,
              context,
            )
          : null,
      onPanUpdate: data['onPanUpdateId'] != null
          ? (details) => _triggerActionWithDragDetails(
              data['onPanUpdateId'],
              details,
              context,
            )
          : null,
      child: child,
    ),
  );
}

Widget _buildInkWell(Map<String, dynamic> data) {
  final child = data['child'] != null
      ? buildWidgetFromJson(data['child'])
      : null;

  return Builder(
    builder: (context) => InkWell(
      onTap: data['onTapId'] != null
          ? () => _triggerActionAsync(data['onTapId'], context)
          : null,
      child: child,
    ),
  );
}

MouseCursor _parseMouseCursor(String? cursor) {
  switch (cursor) {
    case 'basic':
      return SystemMouseCursors.basic;
    case 'click':
      return SystemMouseCursors.click;
    case 'text':
      return SystemMouseCursors.text;
    case 'resizeLeftRight':
      return SystemMouseCursors.resizeLeftRight;
    case 'resizeUpDown':
      return SystemMouseCursors.resizeUpDown;
    case 'resizeColumn':
      return SystemMouseCursors.resizeColumn;
    case 'resizeRow':
      return SystemMouseCursors.resizeRow;
    case 'grab':
      return SystemMouseCursors.grab;
    case 'grabbing':
      return SystemMouseCursors.grabbing;
    case 'move':
      return SystemMouseCursors.move;
    case 'forbidden':
      return SystemMouseCursors.forbidden;
    case 'wait':
      return SystemMouseCursors.wait;
    default:
      return MouseCursor.defer;
  }
}

Widget _buildMouseRegion(Map<String, dynamic> data) {
  final child = data['child'] != null
      ? buildWidgetFromJson(data['child'])
      : null;
  final cursor = _parseMouseCursor(data['cursor'] as String?);

  return Builder(
    builder: (context) => MouseRegion(
      cursor: cursor,
      onEnter: data['onEnterId'] != null
          ? (_) => _triggerActionAsync(data['onEnterId'], context)
          : null,
      onExit: data['onExitId'] != null
          ? (_) => _triggerActionAsync(data['onExitId'], context)
          : null,
      child: child,
    ),
  );
}

Widget _buildIconButton(Map<String, dynamic> data) {
  final icon = data['icon'];
  Widget iconWidget;

  if (icon is Map<String, dynamic>) {
    iconWidget = buildWidgetFromJson(icon);
  } else {
    iconWidget = const Icon(Icons.error);
  }

  final disabled = data['disabled'] ?? false;
  final iconColor = data['iconColor'] != null ? Color(data['iconColor']) : null;
  final backgroundColor = data['backgroundColor'] != null
      ? Color(data['backgroundColor'])
      : null;

  return Builder(
    builder: (context) => IconButton(
      icon: iconWidget,
      onPressed: disabled || data['onPressedId'] == null
          ? null
          : () => _triggerActionAsync(data['onPressedId'], context),
      color: iconColor,
      iconSize: (data['iconSize'] as num?)?.toDouble() ?? 24,
      tooltip: data['tooltip'],
      style: backgroundColor != null
          ? IconButton.styleFrom(backgroundColor: backgroundColor)
          : null,
    ),
  );
}

// =============================================================================
// Parsing Helpers
// =============================================================================

EdgeInsets? _parseEdgeInsets(dynamic data) {
  if (data == null) return null;
  if (data is Map) {
    return EdgeInsets.only(
      left: (data['left'] as num?)?.toDouble() ?? 0,
      top: (data['top'] as num?)?.toDouble() ?? 0,
      right: (data['right'] as num?)?.toDouble() ?? 0,
      bottom: (data['bottom'] as num?)?.toDouble() ?? 0,
    );
  }
  return null;
}

Border? _parseBorder(dynamic data) {
  if (data == null) return null;
  if (data is Map) {
    BorderSide parseSide(dynamic sideData) {
      if (sideData == null) return BorderSide.none;
      return BorderSide(
        color: sideData['color'] != null
            ? Color(sideData['color'])
            : Colors.black,
        width: (sideData['width'] as num?)?.toDouble() ?? 1.0,
      );
    }

    return Border(
      left: parseSide(data['left']),
      top: parseSide(data['top']),
      right: parseSide(data['right']),
      bottom: parseSide(data['bottom']),
    );
  }
  return null;
}

BorderRadius _parseBorderRadius(dynamic data) {
  if (data == null) return BorderRadius.zero;
  if (data is num) return BorderRadius.circular(data.toDouble());
  if (data is Map) {
    return BorderRadius.only(
      topLeft: Radius.circular((data['topLeft'] as num?)?.toDouble() ?? 0),
      topRight: Radius.circular((data['topRight'] as num?)?.toDouble() ?? 0),
      bottomLeft: Radius.circular(
        (data['bottomLeft'] as num?)?.toDouble() ?? 0,
      ),
      bottomRight: Radius.circular(
        (data['bottomRight'] as num?)?.toDouble() ?? 0,
      ),
    );
  }
  return BorderRadius.zero;
}

BoxDecoration? _parseBoxDecoration(dynamic data) {
  if (data == null) return null;
  if (data is! Map) return null;
  return BoxDecoration(
    color: data['color'] != null ? Color(data['color']) : null,
    border: _parseBorder(data['border']),
    borderRadius: _parseBorderRadius(data['borderRadius']),
  );
}

InputDecoration? _parseInputDecoration(dynamic data) {
  if (data == null) return null;
  if (data is! Map) return null;
  return InputDecoration(
    hintText: data['hintText'],
    border: _parseInputBorder(data['border']),
    filled: data['filled'] ?? false,
    fillColor: data['fillColor'] != null ? Color(data['fillColor']) : null,
    contentPadding: _parseEdgeInsets(data['contentPadding']),
  );
}

InputBorder? _parseInputBorder(dynamic data) {
  if (data == null) return null;
  if (data == 'none') return InputBorder.none;
  return null;
}

Alignment _parseAlignment(dynamic data) {
  if (data == null) return Alignment.center;
  switch (data) {
    case 'topLeft':
      return Alignment.topLeft;
    case 'topCenter':
      return Alignment.topCenter;
    case 'topRight':
      return Alignment.topRight;
    case 'centerLeft':
      return Alignment.centerLeft;
    case 'center':
      return Alignment.center;
    case 'centerRight':
      return Alignment.centerRight;
    case 'bottomLeft':
      return Alignment.bottomLeft;
    case 'bottomCenter':
      return Alignment.bottomCenter;
    case 'bottomRight':
      return Alignment.bottomRight;
    default:
      return Alignment.center;
  }
}

Alignment? _parseAlignmentNullable(dynamic data) {
  if (data == null) return null;
  return _parseAlignment(data);
}

MainAxisAlignment _parseMainAxisAlignment(dynamic raw) {
  if (raw == 'start') return MainAxisAlignment.start;
  if (raw == 'end') return MainAxisAlignment.end;
  if (raw == 'spaceBetween') return MainAxisAlignment.spaceBetween;
  if (raw == 'spaceAround') return MainAxisAlignment.spaceAround;
  if (raw == 'spaceEvenly') return MainAxisAlignment.spaceEvenly;
  return MainAxisAlignment.start;
}

CrossAxisAlignment _parseCrossAxisAlignment(dynamic raw) {
  if (raw == 'start') return CrossAxisAlignment.start;
  if (raw == 'end') return CrossAxisAlignment.end;
  if (raw == 'center') return CrossAxisAlignment.center;
  if (raw == 'stretch') return CrossAxisAlignment.stretch;
  if (raw == 'baseline') return CrossAxisAlignment.baseline;
  return CrossAxisAlignment.center;
}

TextStyle? _parseTextStyle(dynamic data) {
  if (data == null) return null;
  if (data is Map) {
    return TextStyle(
      fontSize: (data['fontSize'] as num?)?.toDouble(),
      fontWeight: _parseFontWeight(data['fontWeight']),
      color: data['color'] != null ? Color(data['color']) : null,
      fontFamily: data['fontFamily'],
      height: (data['height'] as num?)?.toDouble(),
    );
  }
  return null;
}

FontWeight? _parseFontWeight(dynamic data) {
  if (data == null) return null;
  switch (data) {
    case 'bold':
      return FontWeight.bold;
    case 'normal':
      return FontWeight.normal;
    case 'w100':
      return FontWeight.w100;
    case 'w200':
      return FontWeight.w200;
    case 'w300':
      return FontWeight.w300;
    case 'w400':
      return FontWeight.w400;
    case 'w500':
      return FontWeight.w500;
    case 'w600':
      return FontWeight.w600;
    case 'w700':
      return FontWeight.w700;
    case 'w800':
      return FontWeight.w800;
    case 'w900':
      return FontWeight.w900;
    default:
      return null;
  }
}

void _triggerActionWithValueAsync(
  String actionId,
  String value,
  BuildContext? context,
) {
  if (actionId.isEmpty) return;
  flutNative.triggerAction(actionId, {
    'value': value,
    if (context != null) 'context': flutNative.captureContextSnapshot(context),
  });
}

void _triggerActionWithDragDetails(
  String actionId,
  DragUpdateDetails details,
  BuildContext? context,
) {
  if (actionId.isEmpty) return;

  // Get window size from context if available
  double? windowWidth;
  double? windowHeight;
  if (context != null) {
    final size = MediaQuery.of(context).size;
    windowWidth = size.width;
    windowHeight = size.height;
  }

  // DIRECT: Drag updates bypass the queue for performance
  final payload = {
    'id': actionId,
    'controllers': flutNative.getControllerValues(),
    'globalPosition': {
      'x': details.globalPosition.dx,
      'y': details.globalPosition.dy,
    },
    'localPosition': {
      'x': details.localPosition.dx,
      'y': details.localPosition.dy,
    },
    'delta': {'x': details.delta.dx, 'y': details.delta.dy},
    if (windowWidth != null) 'windowWidth': windowWidth,
    if (windowHeight != null) 'windowHeight': windowHeight,
    if (context != null) 'context': flutNative.captureContextSnapshot(context),
  };

  // Use AvoidSync to fire-and-forget (ignoring result), but execute immediately via FFI
  flutNative.invokeNativeNoWaitSync('action', payload);
}

void _triggerActionWithDragStartDetails(
  String actionId,
  DragStartDetails details,
  BuildContext? context,
) {
  if (actionId.isEmpty) return;

  // Get window size from context if available
  double? windowWidth;
  double? windowHeight;
  if (context != null) {
    final size = MediaQuery.of(context).size;
    windowWidth = size.width;
    windowHeight = size.height;
  }

  // DIRECT: Drag start bypasses the queue for performance and ordering with drag update
  final payload = {
    'id': actionId,
    'controllers': flutNative.getControllerValues(),
    'globalPosition': {
      'x': details.globalPosition.dx,
      'y': details.globalPosition.dy,
    },
    'localPosition': {
      'x': details.localPosition.dx,
      'y': details.localPosition.dy,
    },
    if (windowWidth != null) 'windowWidth': windowWidth,
    if (windowHeight != null) 'windowHeight': windowHeight,
    if (context != null) 'context': flutNative.captureContextSnapshot(context),
  };

  // Use AvoidSync to fire-and-forget (ignoring result), but execute immediately via FFI
  flutNative.invokeNativeNoWaitSync('action', payload);
}

void _triggerActionAsync(String actionId, BuildContext? context) {
  if (actionId.isEmpty) return;
  // Use triggerAction: Dart doesn't block, Python processes on main thread
  flutNative.triggerAction(actionId, {
    if (context != null) 'context': flutNative.captureContextSnapshot(context),
  });
}

// =============================================================================
// CustomPainter for canvas drawing
// =============================================================================

class _JSONPainter extends CustomPainter {
  final Map<String, dynamic>? data;
  _JSONPainter(this.data);

  @override
  void paint(Canvas canvas, Size size) {
    if (data == null || data!['commands'] == null) return;

    final commands = data!['commands'] as List;
    for (final cmd in commands) {
      final type = cmd['cmd'];
      final paint = _parsePaint(cmd['paint']);

      if (type == 'drawLine') {
        final p1 = _parseOffset(cmd['p1']);
        final p2 = _parseOffset(cmd['p2']);
        canvas.drawLine(p1, p2, paint);
      } else if (type == 'drawCircle') {
        final c = _parseOffset(cmd['c']);
        final radius = (cmd['radius'] as num).toDouble();
        canvas.drawCircle(c, radius, paint);
      } else if (type == 'drawRect') {
        final r = cmd['rect'] as List;
        final rect = Rect.fromLTWH(
          (r[0] as num).toDouble(),
          (r[1] as num).toDouble(),
          (r[2] as num).toDouble(),
          (r[3] as num).toDouble(),
        );
        canvas.drawRect(rect, paint);
      }
    }
  }

  Offset _parseOffset(dynamic list) {
    final l = list as List;
    return Offset((l[0] as num).toDouble(), (l[1] as num).toDouble());
  }

  Paint _parsePaint(dynamic map) {
    final paint = Paint();
    if (map['color'] != null) paint.color = Color(map['color']);
    if (map['strokeWidth'] != null) {
      paint.strokeWidth = (map['strokeWidth'] as num).toDouble();
    }
    if (map['style'] == 'stroke') {
      paint.style = PaintingStyle.stroke;
    } else {
      paint.style = PaintingStyle.fill;
    }
    return paint;
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
