# StartAllBack Accessibility Enhancements

[繁體中文](README.md)

Author: roundface

Helps NVDA announce checkbox states, display options, Start button images, and labels for 14 combo boxes in StartAllBack settings.

## Installation

Download `StartAllBack-1.0.2.nvda-addon` from [Releases](https://github.com/maydayrag/startallback-nvda/releases), install it with NVDA, and restart NVDA.

## Usage

Open StartAllBack and use it as usual. NVDA will automatically announce the currently selected item and its state.

See the [English user guide](addon/doc/en/readme.html). The user release does not include diagnostic shortcuts or data export features.

## Building and verification

Run with Python 3:

```sh
python -m unittest discover -p "test_*.py"
python build.py
```

The build produces `StartAllBack-1.0.2.nvda-addon` and verifies the ZIP format, package structure, and file contents. Tests use simulated NVDA interfaces and a de-identified control tree; StartAllBack does not need to be running.

The internal add-on identifier remains `startAllBackDiagnostics` to support upgrades from earlier versions. The user release contains no diagnostic functionality.
