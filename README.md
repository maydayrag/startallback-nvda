# StartAllBack 清單增強

作者：圓臉（roundface）

協助 NVDA 朗讀 StartAllBack 設定中的勾選狀態、顯示方式、開始按鈕圖案，以及 14 個下拉式方塊的功能名稱。

## 安裝

從 [Releases](https://github.com/maydayrag/startallback-nvda/releases) 下載 `StartAllBack-1.0.nvda-addon`，以 NVDA 安裝並重新啟動 NVDA。

適用於 NVDA 2026.2 和 StartAllBack 3.9.28.5423 x64。此版會核對 StartAllBack 執行檔；其他版本需重新驗證後才能支援。

## 鍵盤操作

- 設定清單：上下鍵選擇項目，空白鍵切換勾選，左右鍵切換選項。
- 同時有勾選和細項的設定：先勾選，再用左右鍵修改細項。
- 下拉式方塊：Tab 或 Shift+Tab 移動，Alt+下鍵展開，上下鍵選擇，Enter 確認。

詳細說明見 [繁體中文操作說明](addon/doc/zh_TW/readme.html)。使用者版不含診斷快捷鍵及資料匯出功能。

## 建置及驗證

使用 Python 3 執行：

```sh
python -m unittest discover -p "test_*.py"
python build.py
```

建置後產生 `StartAllBack-1.0.nvda-addon`，並檢查 ZIP 格式、目錄結構及內容一致性。測試使用模擬 NVDA 介面與去識別化的控制項結構，不需要開啟 StartAllBack。

內部附加元件識別名稱保留為 `startAllBackDiagnostics`，以便升級早期版本；使用者版不提供診斷功能。
