# StartAllBack Accessibility Enhancements

[繁體中文](README.zh_TW.md)

Author: roundface

Helps NVDA announce checkbox states, display options, Start button images, and labels for 14 combo boxes in StartAllBack settings.

## Installation

Download `StartAllBack-1.0.4.nvda-addon` from [Releases](https://github.com/maydayrag/startallback-nvda/releases), install it with NVDA, and restart NVDA.

## Usage

If an earlier version is installed under the identifier `startAllBackDiagnostics`, remove it in NVDA's Add-on Store before installing this version. The new identifier is `startallback`.

Open StartAllBack and use it as usual. NVDA will automatically announce the currently selected item and its state.

## Keyboard commands

- Tab / Shift+Tab: Move to the next / previous control.
- Settings list: Up/Down Arrow selects an item, Space toggles its checkbox, and Left/Right Arrow changes its option.
- Settings with both a checkbox and additional options: Press Space to enable the setting, then use Left/Right Arrow to change its option.
- Combo boxes: Alt+Down Arrow expands the list, Up/Down Arrow selects an option, and Enter confirms it.

These commands do not require the NVDA key. After you change a setting, NVDA automatically announces its new state.

See the [English user guide](addon/doc/en/readme.html). The user release does not include diagnostic shortcuts or data export features.
