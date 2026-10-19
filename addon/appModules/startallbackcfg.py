"""StartAllBack accessibility enhancements by 圓臉 (roundface)."""

import ctypes
import hashlib
from pathlib import Path, PureWindowsPath

import addonHandler
import api
import appModuleHandler
import core
import eventHandler
import watchdog
import winKernel
from logHandler import log
from controlTypes import Role, State
from NVDAObjects.IAccessible import IAccessible
from .startallbackState import decodeSetting, SUPPORTED_SHA256
from NVDAObjects.IAccessible.sysListView32 import (
    LVITEM64, LVIF_PARAM,
    LVM_GETITEMW, LVM_GETITEMTEXTW, LVM_GETITEMCOUNT,
)

addonHandler.initTranslation()


def optionText(key):
    # 使用應用程式自己的選項表，再將常見選項轉成繁體中文。
    labels = {
        "Don't display": _("不顯示"), "Link": _("顯示為連結"),
        "Menu": _("顯示為功能表"), "Items first": _("項目優先"),
        "Folders first": _("資料夾優先"), "No preference": _("無優先順序"),
        "Apps folder": _("應用程式資料夾"), "All Programs": _("所有程式"),
    }
    return labels.get(key, key)


def readMemory(process, address, size):
    # 所有讀取都有長度上限；讀不到完整資料就停止，不回傳猜測值。
    if address <= 0 or not 0 < size <= 4096:
        raise ValueError("Invalid settings memory request")
    buffer = ctypes.create_string_buffer(size)
    transfer(winKernel.readProcessMemory, process, address, buffer)
    return buffer.raw


def readSetting(obj):
    # 每次向清單重新索取此列的物件指標，不長期保存可能失效的位址。
    index = obj.IAccessibleChildID - 1
    if not 0 <= index < 200:
        raise ValueError("Invalid settings row")
    process = obj.processHandle
    item = LVITEM64(mask=LVIF_PARAM, iItem=index)
    remote = winKernel.virtualAllocEx(
        process, None, ctypes.sizeof(item), winKernel.MEM_COMMIT, winKernel.PAGE_READWRITE,
    )
    try:
        transfer(winKernel.writeProcessMemory, process, remote, item)
        if not watchdog.cancellableSendMessage(obj.windowHandle, LVM_GETITEMW, 0, remote):
            raise OSError("Cannot retrieve settings item")
        transfer(winKernel.readProcessMemory, process, remote, item)
        return decodeSetting(lambda address, size: readMemory(process, address, size), item.lParam)
    finally:
        winKernel.virtualFreeEx(process, remote, 0, winKernel.MEM_RELEASE)


def imageChoiceNames(paths):
    # 圖案清單的第二欄存放檔案路徑。必須確認整份清單，避免替其他空白控制項亂取名字。
    if len(paths) < 2 or paths[0] or not any(
        PureWindowsPath(path).parent.name.casefold() == "orbs"
        for path in paths[1:]
    ):
        return None
    if any(not PureWindowsPath(path).is_absolute() or
           PureWindowsPath(path).suffix.lower() not in (".svg", ".orb", ".png", ".bmp")
           for path in paths[1:]):
        return None
    return [_("開始按鈕樣式 1")] + [
        _("開始按鈕圖案：{name}").format(name=PureWindowsPath(path).name)
        for path in paths[1:]
    ]


def readImageChoiceNames(obj):
    # 使用標準清單文字查詢，讀取隱藏欄位；不改動圖案或使用者設定。
    count = watchdog.cancellableSendMessage(obj.windowHandle, LVM_GETITEMCOUNT, 0, 0)
    if not 2 <= count <= 200:
        return None
    process = obj.processHandle
    text = ctypes.create_unicode_buffer(512)
    size = ctypes.sizeof(LVITEM64)
    remote = winKernel.virtualAllocEx(
        process, None, size + ctypes.sizeof(text), winKernel.MEM_COMMIT, winKernel.PAGE_READWRITE,
    )
    try:
        paths = []
        for index in range(count):
            item = LVITEM64(iItem=index, iSubItem=1, pszText=remote + size, cchTextMax=512)
            transfer(winKernel.writeProcessMemory, process, remote, item)
            length = watchdog.cancellableSendMessage(obj.windowHandle, LVM_GETITEMTEXTW, index, remote)
            if not 0 <= length < 511:
                return None
            transfer(winKernel.readProcessMemory, process, remote + size, text)
            paths.append(text.value[:length])
        return imageChoiceNames(paths)
    finally:
        winKernel.virtualFreeEx(process, remote, 0, winKernel.MEM_RELEASE)


class ImageChoiceItem(IAccessible):
    def _get_name(self):
        # 保留程式原有的名稱；只有未命名的圖案才使用檔名。
        original = super().name
        if original:
            return original
        try:
            names = readImageChoiceNames(self)
            index = self.IAccessibleChildID - 1
            if names is not None and 0 <= index < len(names):
                return names[index]
        except Exception:
            log.debugWarning("Cannot read StartAllBack image choice", exc_info=True)
        return original


def taskbarAppearanceName(obj):
    # 介面資源已確認這列由左到右的用途；不使用每次開啟都會改變的視窗編號。
    panel = obj
    for unused in range(5):
        if panel is None:
            return None
        if panel.windowClassName == "TPanel" and panel.role == Role.PANE:
            break
        panel = panel.parent
    else:
        return None
    ancestor = panel
    for unused in range(12):
        if ancestor is None or ancestor.processID != obj.processID:
            return None
        if ancestor.windowClassName == "TfrmTaskbar":
            break
        ancestor = ancestor.parent
    else:
        return None
    # MSAA 有時會在控制項外多包一層 WINDOW；只穿過這種包裝，不深入其他窗格。
    pending = [(child, 0) for child in panel.children[:20]]
    combos = {}
    while pending:
        child, depth = pending.pop()
        if child.role == Role.COMBOBOX and child.windowClassName == "TComboBox":
            combos[child.windowHandle] = child
        elif child.role == Role.WINDOW and depth < 2:
            pending.extend((nested, depth + 1) for nested in child.children[:20])
    if len(combos) != 3:
        return None
    ordered = sorted(combos.values(), key=lambda child: child.location.left)
    if len({child.location.left for child in ordered}) != 3 or len(
        {child.location.top for child in ordered}
    ) != 1:
        return None
    if obj.windowHandle == panel.windowHandle and obj.role == Role.PANE:
        return _("工作列外觀設定")
    labels = (_("視覺樣式"), _("圖示大小"), _("圖示邊距"))
    for child, label in zip(ordered, labels):
        if obj.role == Role.COMBOBOX and obj.windowHandle == child.windowHandle:
            return label
    return None


def panelControls(panel):
    # 穿過 MSAA 的視窗包裝，取得同一列的控制項；不混入下一層設定窗格。
    pending = [(child, 0) for child in panel.children[:30]]
    result = {}
    while pending:
        child, depth = pending.pop()
        if child.role == Role.WINDOW and depth < 2:
            pending.extend((nested, depth + 1) for nested in child.children[:30])
        else:
            result[(child.windowHandle, child.role)] = child
    return list(result.values())


def enclosingPanel(obj):
    for unused in range(6):
        if obj is None:
            return None
        if obj.windowClassName == "TPanel" and obj.role == Role.PANE:
            return obj
        obj = obj.parent
    return None


def comboPurposeName(obj):
    # 標籤依三頁的 DFM 資源及完整診斷樹核對；保留原生值和鍵盤操作。
    if obj.role != Role.COMBOBOX:
        return None
    panel = enclosingPanel(obj.parent)
    if panel is None:
        return None
    ancestor = panel
    for unused in range(16):
        if ancestor is None or ancestor.processID != obj.processID:
            return None
        page = ancestor.windowClassName
        if page in ("TfrmStartMenu", "TfrmTaskbar", "TfrmTray"):
            break
        ancestor = ancestor.parent
    else:
        return None
    controls = panelControls(panel)
    combos = sorted((child for child in controls if child.role == Role.COMBOBOX
        and child.windowClassName == "TComboBox"), key=lambda child: child.location.left)
    indices = [i for i, child in enumerate(combos) if child.windowHandle == obj.windowHandle]
    if len(indices) != 1:
        return None
    index = indices[0]
    classes = [child.windowClassName for child in controls]
    checks = [child for child in controls if child.windowClassName == "TCheckBox"]
    if page == "TfrmStartMenu":
        if len(combos) == 2 and "TEdit" in classes and "TUpDown" in classes:
            return (_("視覺樣式"), _("開始功能表圖示大小"))[index]
        if len(combos) == 1 and classes.count("TButton") == 1:
            return _("電源按鈕預設動作")
    elif page == "TfrmTray":
        if len(combos) == 2 and len(checks) == 1:
            return (_("次要工作列上的系統匣圖示"), _("系統匣圖示邊距"))[index]
    elif page == "TfrmTaskbar" and len(combos) == 1:
        if len(checks) == 1 and checks[0].name:
            # 這三列各自有對應的核取方塊，可直接採用程式已翻譯的功能名稱。
            return _("{feature}方式").format(feature=checks[0].name)
        if checks:
            return None
        group = enclosingPanel(panel.parent)
        if group is None:
            return None
        rows = []
        for child in panelControls(group):
            if child.windowClassName != "TPanel" or child.role != Role.PANE:
                continue
            content = panelControls(child)
            if (sum(item.windowClassName == "TComboBox" and item.role == Role.COMBOBOX
                    for item in content) == 1
                    and not any(item.windowClassName == "TCheckBox" for item in content)):
                rows.append(child)
        # 只有完整辨識出位置、主工作列合併、次要工作列合併三列時才套用。
        if len(rows) == 3 and len({row.location.top for row in rows}) == 3:
            rows.sort(key=lambda row: row.location.top)
            labels = (_("工作列在螢幕上的位置"), _("合併工作列按鈕"), _("合併次要工作列按鈕"))
            for row, label in zip(rows, labels):
                if row.windowHandle == panel.windowHandle:
                    return label
    return None


class TaskbarAppearanceControl(IAccessible):
    def _get_name(self):
        # 只補空白名稱，保留選項值、操作方式與程式原本提供的名稱。
        original = super().name
        if original:
            return original
        try:
            return taskbarAppearanceName(self) or comboPurposeName(self) or original
        except Exception:
            log.debugWarning("Cannot label StartAllBack appearance control", exc_info=True)
            return original


class SettingsItem(IAccessible):
    def sabReadSetting(self):
        try:
            return readSetting(self)
        except Exception:
            # 未知資料不能被當作「未勾選」或「不顯示」。保留原本的 NVDA 行為。
            if not getattr(self, "sabReadErrorLogged", False):
                log.debugWarning("Cannot read StartAllBack setting", exc_info=True)
                self.sabReadErrorLogged = True
            return None

    def _get_states(self):
        states = set(super().states)
        setting = self.sabReadSetting()
        if setting is not None and setting["checked"] is not None:
            states.add(State.CHECKABLE)
            states.discard(State.CHECKED)
            if setting["checked"]:
                states.add(State.CHECKED)
        return states

    def _get_value(self):
        setting = self.sabReadSetting()
        if setting is not None and setting["option"] is not None:
            return optionText(setting["option"])
        return super().value












def transfer(function, process, remote, local):
    # 僅使用這次查詢自己配置的暫存區，並確認沒有只讀到一半。
    size = ctypes.sizeof(local)
    transferred = ctypes.c_size_t()
    if not function(process, remote, ctypes.byref(local), size, ctypes.byref(transferred)):
        raise ctypes.WinError()
    if transferred.value != size:
        raise OSError("Incomplete diagnostic buffer transfer")




class AppModule(appModuleHandler.AppModule):
    def sabSupportsLayout(self):
        # 此記憶體配置已針對這個執行檔查證。版本改變時不套用舊偏移量。
        if not hasattr(self, "sabLayoutSupported"):
            self.sabLayoutSupported = False
            try:
                self.sabLayoutSupported = (
                    self.is64BitProcess
                    and hashlib.sha256(Path(self.appPath).read_bytes()).hexdigest() == SUPPORTED_SHA256
                )
            except OSError:
                log.debugWarning("Cannot verify StartAllBack executable", exc_info=True)
            if not self.sabLayoutSupported:
                log.warning("StartAllBack executable has an unverified layout; enhancements disabled")
        return self.sabLayoutSupported

    def chooseNVDAObjectOverlayClasses(self, obj, clsList):
        if (
            isinstance(obj, IAccessible)
            and obj.windowClassName in ("TPanel", "TComboBox")
            and obj.role in (Role.PANE, Role.COMBOBOX)
            and self.sabSupportsLayout()
        ):
            clsList.insert(0, TaskbarAppearanceControl)
        # 依實際設定項目的類型配對，涵蓋每一列，不以名稱或固定序號配對。
        if (
            isinstance(obj, IAccessible)
            and obj.windowClassName == "TListView"
            and obj.role == Role.LISTITEM
            and obj.IAccessibleChildID > 0
            and self.sabSupportsLayout()
        ):
            try:
                readSetting(obj)
            except Exception:
                try:
                    if not obj.name and readImageChoiceNames(obj) is not None:
                        clsList.insert(0, ImageChoiceItem)
                except Exception:
                    log.debugWarning("Cannot identify StartAllBack image list", exc_info=True)
                return
            clsList.insert(0, SettingsItem)

    def sabStopMonitor(self):
        timer = getattr(self, "sabTimer", None)
        self.sabTimer = None
        self.sabMonitoredObject = None
        if timer is not None:
            timer.Stop()

    def event_gainFocus(self, obj, nextHandler):
        self.sabStopMonitor()
        nextHandler()
        if isinstance(obj, SettingsItem):
            self.sabMonitoredObject = obj
            self.sabLastSetting = obj.sabReadSetting()
            self.sabTimer = core.callLater(150, self.sabCheckChange, obj)

    def event_loseFocus(self, obj, nextHandler):
        if getattr(self, "sabMonitoredObject", None) is obj:
            self.sabStopMonitor()
        nextHandler()

    def sabCheckChange(self, obj):
        # 只追蹤目前焦點。滑鼠或鍵盤改變選項時，也能更新語音和點字。
        if (
            getattr(self, "sabTerminated", False)
            or getattr(self, "sabMonitoredObject", None) is not obj
            or api.getFocusObject() is not obj
        ):
            return
        self.sabTimer = None
        current = obj.sabReadSetting()
        previous = self.sabLastSetting
        self.sabLastSetting = current
        if current is not None and previous is not None and current != previous:
            obj.invalidateCache()
            if current["checked"] != previous["checked"]:
                eventHandler.executeEvent("stateChange", obj)
            if current["option"] != previous["option"]:
                eventHandler.executeEvent("valueChange", obj)
        self.sabTimer = core.callLater(150, self.sabCheckChange, obj)

    def terminate(self):
        # 外掛重新載入或程式關閉時，停止計時器，避免舊物件繼續查詢。
        try:
            super().terminate()
        finally:
            self.sabTerminated = True
            self.sabStopMonitor()

