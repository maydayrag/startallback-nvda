"""驗證外觀標籤依控制項結構配對，不因可變視窗編號或順序而貼錯。"""
import ast
from pathlib import Path
from types import SimpleNamespace as Node
import unittest

source = Path(__file__).parent / "addon/appModules/startallbackcfg.py"
tree = ast.parse(source.read_text(encoding="utf-8"))
roles = Node(PANE="pane", COMBOBOX="combo", WINDOW="window")
scope = {"Role": roles, "_": lambda text: text}
exec(compile(ast.Module(body=[node for node in tree.body if isinstance(node, ast.FunctionDef)
    and node.name == "taskbarAppearanceName"], type_ignores=[]), str(source), "exec"), scope)
label = scope["taskbarAppearanceName"]

class TaskbarLabelTests(unittest.TestCase):
    def setUp(self):
        self.form = Node(windowClassName="TfrmTaskbar", processID=1)
        self.panel = Node(windowClassName="TPanel", role="pane", processID=1,
            windowHandle=70, parent=self.form, children=[])
        self.combos = [Node(windowClassName="TComboBox", role="combo", processID=1,
            windowHandle=100+i, parent=self.panel, children=[], location=Node(left=x, top=20))
            for i, x in enumerate((78, 291, 428))]
        self.panel.children = list(reversed(self.combos))

    def test_order_uses_layout_not_child_enumeration(self):
        self.assertEqual([label(obj) for obj in self.combos], ["視覺樣式", "圖示大小", "圖示邊距"])
        self.assertEqual(label(self.panel), "工作列外觀設定")

    def test_window_wrappers(self):
        wrapper = Node(windowClassName="TPanel", role="window", processID=1,
            parent=self.panel, children=self.panel.children)
        self.panel.children = [wrapper]
        for obj in self.combos:
            obj.parent = wrapper
        self.assertEqual(label(self.combos[1]), "圖示大小")

    def test_other_page_rejected(self):
        self.form.windowClassName = "TfrmStartMenu"
        self.form.parent = None
        self.assertIsNone(label(self.panel))

    def test_missing_or_misaligned_controls_rejected(self):
        self.combos[1].location.top = 40
        self.assertIsNone(label(self.panel))
        self.panel.children.pop()
        self.assertIsNone(label(self.panel))

if __name__ == "__main__":
    unittest.main()
