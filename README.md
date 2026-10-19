# StartAllBack 無障礙增強

StartAllBack Accessibility Enhancements

[English](README.en.md)

作者：圓臉（roundface）

協助 NVDA 朗讀 StartAllBack 設定中的勾選狀態、顯示方式、開始按鈕圖案，以及 14 個下拉式方塊的功能名稱。

## 安裝

從 [Releases](https://github.com/maydayrag/startallback-nvda/releases) 下載 `StartAllBack-1.0.2.nvda-addon`，以 NVDA 安裝並重新啟動 NVDA。

## 操作方式

進入 StartAllBack 後，依一般方式操作即可，NVDA 會自動朗讀目前選取的項目與狀態。

詳細說明見 [繁體中文操作說明](addon/doc/zh_TW/readme.html)。使用者版不含診斷快捷鍵及資料匯出功能。

## 建置及驗證

使用 Python 3 執行：

```sh
python -m unittest discover -p "test_*.py"
python build.py
```

建置後產生 `StartAllBack-1.0.2.nvda-addon`，並檢查 ZIP 格式、目錄結構及內容一致性。測試使用模擬 NVDA 介面與去識別化的控制項結構，不需要開啟 StartAllBack。

內部附加元件識別名稱保留為 `startAllBackDiagnostics`，以便升級早期版本；使用者版不提供診斷功能。
