# Flut

Flutter, but in Python

## Status

This project is in **Technical Preview**.
- APIs are subject to change.
- Not ready for production use.

## Installation

```bash
pip install flut
```

That's it! Windows (x64), macOS (x64, arm64), and Linux (x64) have prebuilt wheels.

You can build from source as well, you will need the Flutter SDK installed.

## Usage

Create a file `app.py`:

```python
from flut import run_app
from flut.flutter.widgets import StatelessWidget, StatefulWidget, State, Text, Center, Column, Icon, MainAxisAlignment
from flut.flutter.material import MaterialApp, Scaffold, AppBar, FloatingActionButton, Icons, ThemeData, ColorScheme, Colors, Theme


class MyApp(StatelessWidget):
    def build(self, context):
        return MaterialApp(
            title="Flut Demo",
            theme=ThemeData(
                colorScheme=ColorScheme.fromSeed(seedColor=Colors.deepPurple),
            ),
            home=MyHomePage(title="Flut Demo Home Page"),
        )


class MyHomePage(StatefulWidget):
    def __init__(self, title):
        super().__init__()
        self.title = title

    def createState(self):
        return _MyHomePageState()


class _MyHomePageState(State[MyHomePage]):
    def initState(self):
        self._counter = 0

    def _incrementCounter(self):
        def _update():
            self._counter += 1

        self.setState(_update)

    def build(self, context):
        return Scaffold(
            appBar=AppBar(
                title=Text(self.widget.title),
                backgroundColor=Theme.of(context).colorScheme.inversePrimary,
            ),
            body=Center(
                child=Column(
                    mainAxisAlignment=MainAxisAlignment.center,
                    children=[
                        Text("You have pushed the button this many times:"),
                        Text(
                            f"{self._counter}",
                            style=Theme.of(context).textTheme.headlineMedium,
                        ),
                    ],
                ),
            ),
            floatingActionButton=FloatingActionButton(
                onPressed=self._incrementCounter,
                tooltip="Increment",
                child=Icon(Icons.add),
            ),
        )


if __name__ == "__main__":
    run_app(MyApp())

```

Run it:

```bash
python app.py
```

For async support:

```python
import asyncio
from flut import run_app_async

# ... your app code ...

if __name__ == "__main__":
    asyncio.run(run_app_async(MyApp()))
```


## License

MIT
