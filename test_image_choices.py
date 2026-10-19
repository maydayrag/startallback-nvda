"""確認空白圖案有名稱，而且不誤認其他清單。"""
import ast
from pathlib import Path, PureWindowsPath
import unittest

source = Path(__file__).parent / "addon/appModules/startallbackcfg.py"
tree = ast.parse(source.read_text(encoding="utf-8"))
scope = {"PureWindowsPath": PureWindowsPath, "_": lambda text: text}
exec(compile(ast.Module(body=[node for node in tree.body
    if isinstance(node, ast.FunctionDef) and node.name == "imageChoiceNames"],
    type_ignores=[]), str(source), "exec"), scope)
names = scope["imageChoiceNames"]

class ImageChoiceTests(unittest.TestCase):
    def test_actual_five_choices(self):
        result = names([""] + ["C:\\StartAllBack\\Orbs\\" + name for name in
            ("clover.svg", "w8logo.svg", "Windows 7.orb", "e1evenorb-pr.png")])
        self.assertEqual(len(result), 5)
        self.assertEqual(result[0], "開始按鈕樣式 1")
        self.assertEqual(result[3], "開始按鈕圖案：Windows 7.orb")

    def test_custom_file_outside_orbs(self):
        self.assertIsNotNone(names(["", "C:\\Orbs\\clover.svg", "D:\\圖案\\自訂.png"]))

    def test_unrelated_or_malformed_lists(self):
        for paths in ([], [""], ["", ""], ["", "Link"],
                      ["", "C:\\Other\\a.png"], ["", "C:\\Orbs\\a.exe"],
                      ["", "C:\\Orbs\\a.png", "relative.png"],
                      ["", "C:\\NotOrbs\\a.png"]):
            with self.subTest(paths=paths):
                self.assertIsNone(names(paths))

if __name__ == "__main__":
    unittest.main()
