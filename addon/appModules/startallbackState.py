"""Verified StartAllBack 3.9.28.5423 x64 settings layout.

Only reads via an injected reader. Does not send input or change settings.
See LAYOUT.txt for executable offsets and drawing/keyboard-handler evidence.
"""
import struct

SUPPORTED_SHA256 = "a3a991e6d2e3da056eb4dbfcb5c560f78ae8511e4c44835ea03003f29cc64eca"
ITEM_SIZE = 0xA0


def decodeSetting(read, address):
    # 先確認物件的實際類型和大小，避免套用到一般資料夾清單。
    raw = read(address, ITEM_SIZE)
    vmt = struct.unpack_from("<Q", raw)[0]
    classNameAddress, size = struct.unpack("<QQ", read(vmt - 0x70, 16))
    if size != ITEM_SIZE or read(classNameAddress, 18) != b"\x11TSettingsListItem":
        raise ValueError("Not a verified TSettingsListItem")
    current = struct.unpack_from("<i", raw, 0x40)[0]
    radioOnly = bool(struct.unpack_from("<Q", raw, 0x58)[0])
    onValue, offValue = struct.unpack_from("<ii", raw, 0x84)
    optionAddress = struct.unpack_from("<Q", raw, 0x90)[0]
    checked = None if radioOnly else current != offValue
    options = []
    selected = None
    if optionAddress:
        entries, count, shortcut = struct.unpack("<Qii", read(optionAddress, 16))
        if not 1 <= count <= 32 or not 0 <= shortcut < count:
            raise ValueError("Invalid settings option table")
        indices = (0, shortcut) if shortcut else range(count)
        table = read(entries, count * 16)
        for index in indices:
            number, labelAddress = struct.unpack_from("<qQ", table, index * 16)
            length = struct.unpack("<i", read(labelAddress - 4, 4))[0]
            if not 1 <= length <= 128:
                raise ValueError("Invalid option label length")
            label = read(labelAddress, length * 2).decode("utf-16-le")
            if "\0" in label:
                raise ValueError("Invalid option label")
            options.append((number, label))
            if number == current:
                selected = label
        if checked is not False and selected is None:
            raise ValueError("Current value has no matching visible option")
    elif radioOnly or current not in (onValue, offValue):
        raise ValueError("Unrecognized checkbox value")
    # 未勾選的複合項目會隱藏右側選項；朗讀也應反映這個狀態。
    if checked is False:
        selected = None
    return {"checked": checked, "option": selected, "rawValue": current, "options": options}
