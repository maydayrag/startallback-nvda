"""將明確列出的使用者版檔案封裝成 NVDA 附加元件，並驗證最終成品。"""
import ast
from pathlib import Path
import zipfile

root = Path(__file__).resolve().parent
names = ("manifest.ini", "appModules/startallbackcfg.py", "appModules/startallbackState.py", "doc/zh_TW/readme.html")
files = {name: (root / "addon" / name).read_bytes() for name in names}
for name, data in files.items():
    if name.endswith(".py"):
        ast.parse(data.decode("utf-8"))
module = files["appModules/startallbackcfg.py"].decode("utf-8")
assert all(item not in module for item in ("script_captureList", "captureControlTree", "NVDA+shift+f12"))
archive = root / "StartAllBack-1.0.zip"
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as package:
    for name, data in files.items():
        package.writestr(name, data)
output = archive.with_suffix(".nvda-addon")
archive.replace(output)
assert output.read_bytes()[:4] == b"PK\x03\x04"
with zipfile.ZipFile(output) as package:
    assert package.testzip() is None
    assert set(package.namelist()) == set(files)
    assert 'version = "1.0"' in package.read("manifest.ini").decode("utf-8")
    for name, data in files.items():
        assert package.read(name) == data
print(f"Verified {output}")
