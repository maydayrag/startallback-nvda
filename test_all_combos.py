"""以實際控制項樹驗證全部 14 個選單，改變值或視窗編號仍應得到相同名稱。"""
import ast
import json
from pathlib import Path
import re
from types import SimpleNamespace as Node
import unittest

root = Path(__file__).parent
source = root / "addon/appModules/startallbackcfg.py"
tree = ast.parse(source.read_text(encoding="utf-8"))
functions = {"taskbarAppearanceName", "panelControls", "enclosingPanel", "comboPurposeName"}
scope = {"Role": Node(PANE=3, WINDOW=1, COMBOBOX=13), "_": lambda text: text}
exec(compile(ast.Module(body=[node for node in tree.body if isinstance(node, ast.FunctionDef)
    and node.name in functions], type_ignores=[]), str(source), "exec"), scope)

class AllComboTests(unittest.TestCase):
    def setUp(self):
        data = json.loads((root / "combo-controls-fixture.json").read_text(encoding="utf-8"))
        self.nodes = {}
        for entry in data:
            xy = re.search(r"left=(-?\d+), top=(-?\d+)", entry["location"])
            self.nodes[entry["id"]] = Node(windowHandle=entry["id"] + 5000,
                windowClassName=entry["windowClassName"], role=entry["role"], name=entry["name"],
                location=Node(left=int(xy[1]), top=int(xy[2])), processID=9, children=[], parent=None)
        for entry in data:
            if entry["parent"] is not None:
                obj = self.nodes[entry["id"]]
                obj.parent = self.nodes[entry["parent"]]
                obj.parent.children.insert(0, obj)

    def test_all_fourteen_labels(self):
        expected = {14:"電源按鈕預設動作",20:"開始功能表圖示大小",21:"視覺樣式",
            31:"工作列飽滿化方式",36:"工作列在螢幕上的位置",38:"分割方式",
            41:"工作圖示置中方式",48:"合併次要工作列按鈕",50:"合併工作列按鈕",
            56:"圖示邊距",57:"圖示大小",58:"視覺樣式",
            65:"次要工作列上的系統匣圖示",66:"系統匣圖示邊距"}
        self.assertEqual(sum(obj.role == 13 for obj in self.nodes.values()), 14)
        for index, label in expected.items():
            with self.subTest(index=index):
                obj = self.nodes[index]
                actual = scope["taskbarAppearanceName"](obj) or scope["comboPurposeName"](obj)
                self.assertEqual(actual, label)

    def test_incomplete_group_does_not_guess(self):
        self.nodes[29].children.remove(self.nodes[47])
        self.assertIsNone(scope["comboPurposeName"](self.nodes[36]))

    def test_unrelated_page_does_not_get_label(self):
        self.nodes[62].windowClassName = "TfrmOther"
        self.assertIsNone(scope["comboPurposeName"](self.nodes[65]))

if __name__ == "__main__":
    unittest.main()
