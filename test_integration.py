"""Exercise overlay/event behavior using controlled NVDA interface doubles."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

source = Path(__file__).parent / "addon/appModules/startallbackcfg.py"
tree = ast.parse(source.read_text(encoding="utf-8"))
selected = ast.Module(body=[node for node in tree.body if
    isinstance(node, ast.ClassDef) and node.name in ("SettingsItem", "AppModule")
    or isinstance(node, ast.FunctionDef) and node.name == "optionText"], type_ignores=[])

class Accessible:
    states = {"focused", "selectable"}
    value = None
    def invalidateCache(self):
        self.invalidated = True

class ModuleBase:
    def terminate(self):
        self.baseTerminated = True

class Timer:
    stopped = False
    def Stop(self):
        self.stopped = True

class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.events = []
        self.scheduled = []
        self.focus = None
        self.state = {"checked": None, "option": "Link", "rawValue": 1, "options": []}
        def schedule(delay, callback, obj):
            timer = Timer()
            self.scheduled.append((delay, callback, obj, timer))
            return timer
        self.scope = {
            "IAccessible": Accessible, "appModuleHandler": SimpleNamespace(AppModule=ModuleBase),
            "_": lambda text: text, "script": lambda **kw: lambda fn: fn,
            "State": SimpleNamespace(CHECKABLE="checkable", CHECKED="checked"),
            "Role": SimpleNamespace(LISTITEM="item"),
            "readSetting": lambda obj: self.state,
            "api": SimpleNamespace(getFocusObject=lambda: self.focus),
            "core": SimpleNamespace(callLater=schedule),
            "eventHandler": SimpleNamespace(executeEvent=lambda event, obj: self.events.append(event)),
            "log": SimpleNamespace(debugWarning=lambda *a, **kw: None),
        }
        exec(compile(selected, str(source), "exec"), self.scope)
        self.obj = self.scope["SettingsItem"]()
        self.app = self.scope["AppModule"]()
        self.focus = self.obj

    def start(self):
        self.app.event_gainFocus(self.obj, lambda: None)

    def test_checked_and_unchecked_preserve_existing_states(self):
        for checked in (True, False):
            self.state = {"checked": checked, "option": None}
            states = self.obj._get_states()
            self.assertTrue({"focused", "selectable", "checkable"} <= states)
            self.assertEqual("checked" in states, checked)

    def test_radio_value_is_localized_without_checkbox_state(self):
        self.assertEqual(self.obj._get_value(), "顯示為連結")
        self.assertNotIn("checkable", self.obj._get_states())

    def test_native_read_error_keeps_original_behavior(self):
        def fail(obj):
            raise OSError("Gone")
        self.scope["readSetting"] = fail
        self.assertEqual(self.obj._get_states(), Accessible.states)
        self.assertIsNone(self.obj._get_value())

    def test_no_duplicate_announcement_for_unchanged_setting(self):
        self.start()
        self.app.sabCheckChange(self.obj)
        self.assertEqual(self.events, [])

    def test_radio_change_uses_standard_value_event(self):
        self.start()
        self.state = dict(self.state, option="Menu", rawValue=2)
        self.app.sabCheckChange(self.obj)
        self.assertEqual(self.events, ["valueChange"])
        self.assertTrue(self.obj.invalidated)

    def test_checkbox_change_uses_standard_state_event(self):
        self.state = {"checked": False, "option": None}
        self.start()
        self.state = {"checked": True, "option": None}
        self.app.sabCheckChange(self.obj)
        self.assertEqual(self.events, ["stateChange"])

    def test_focus_loss_cancels_pending_timer(self):
        self.start()
        timer = self.scheduled[-1][-1]
        forwarded = []
        self.app.event_loseFocus(self.obj, lambda: forwarded.append(True))
        self.app.sabCheckChange(self.obj)
        self.assertTrue(timer.stopped)
        self.assertEqual(forwarded, [True])
        self.assertEqual(len(self.scheduled), 1)

    def test_unload_stops_and_does_not_reschedule(self):
        self.start()
        timer = self.scheduled[-1][-1]
        self.app.terminate()
        self.app.sabCheckChange(self.obj)
        self.assertTrue(self.app.baseTerminated)
        self.assertTrue(timer.stopped)
        self.assertEqual(len(self.scheduled), 1)

    def test_unverified_build_does_not_get_overlay(self):
        self.obj.windowClassName = "TListView"
        self.obj.role = "item"
        self.obj.IAccessibleChildID = 1
        self.app.sabSupportsLayout = lambda: False
        classes = []
        self.app.chooseNVDAObjectOverlayClasses(self.obj, classes)
        self.assertEqual(classes, [])

    def test_all_valid_setting_rows_get_overlay(self):
        self.obj.windowClassName = "TListView"
        self.obj.role = "item"
        self.app.sabSupportsLayout = lambda: True
        for child in range(1, 31):
            self.obj.IAccessibleChildID = child
            classes = []
            self.app.chooseNVDAObjectOverlayClasses(self.obj, classes)
            self.assertEqual(classes, [type(self.obj)])

if __name__ == "__main__":
    unittest.main()
