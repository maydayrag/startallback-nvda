"""Check real layout rules with bounded synthetic memory, including failure cases."""
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parent / "addon/appModules"))
from startallbackState import decodeSetting


class Memory:
    def __init__(self, current=1, radio=True, on=1, off=0, labels=None, shortcut=0):
        self.data = bytearray(0x10000)
        self.put(0x1000, "Q", 0x2000)
        self.put(0x2000 - 0x70, "QQ", 0x3000, 0xA0)
        self.data[0x3000:0x3012] = b"\x11TSettingsListItem"
        self.put(0x1040, "i", current)
        self.put(0x1058, "Q", 0x9999 if radio else 0)
        self.put(0x1084, "ii", on, off)
        if labels is not None:
            self.put(0x1090, "Q", 0x4000)
            self.put(0x4000, "Qii", 0x5000, len(labels), shortcut)
            for index, (value, label) in enumerate(labels):
                address = 0x6000 + index * 0x200
                self.put(0x5000 + index * 16, "qQ", value, address)
                self.put(address - 4, "i", len(label))
                encoded = label.encode("utf-16-le")
                self.data[address:address + len(encoded)] = encoded

    def put(self, address, fmt, *values):
        struct.pack_into("<" + fmt, self.data, address, *values)

    def read(self, address, size):
        if address <= 0 or address + size > len(self.data):
            raise OSError("Invalid address")
        return bytes(self.data[address:address + size])

    def decode(self):
        return decodeSetting(self.read, 0x1000)


RADIOS = [(0, "Don't display"), (1, "Link"), (2, "Menu")]


class StateTests(unittest.TestCase):
    def test_each_radio_state(self):
        for number, label in RADIOS:
            with self.subTest(number=number):
                result = Memory(current=number, labels=RADIOS).decode()
                self.assertIsNone(result["checked"])
                self.assertEqual(result["option"], label)

    def test_menu_only_options(self):
        result = Memory(current=2, labels=RADIOS, shortcut=2).decode()
        self.assertEqual(result["options"], [RADIOS[0], RADIOS[2]])

    def test_hidden_option_is_not_reported(self):
        with self.assertRaises(ValueError):
            Memory(current=1, labels=RADIOS, shortcut=2).decode()

    def test_regular_checkboxes(self):
        for number in (0, 1):
            self.assertEqual(Memory(current=number, radio=False).decode()["checked"], bool(number))

    def test_inverted_checkbox(self):
        result = Memory(current=0, radio=False, on=0, off=1).decode()
        self.assertTrue(result["checked"])

    def test_non_boolean_checkbox(self):
        result = Memory(current=2, radio=False, on=2, off=0).decode()
        self.assertTrue(result["checked"])

    def test_unchecked_compound_hides_options(self):
        result = Memory(current=10, radio=False, on=1, off=10,
                        labels=[(0, "Items first"), (1, "Folders first"), (2, "No preference")]).decode()
        self.assertFalse(result["checked"])
        self.assertIsNone(result["option"])

    def test_checked_compound_value(self):
        result = Memory(current=0, radio=False, on=1, off=10,
                        labels=[(0, "Items first"), (1, "Folders first"), (2, "No preference")]).decode()
        self.assertTrue(result["checked"])
        self.assertEqual(result["option"], "Items first")

    def test_unknown_value_is_never_unchecked(self):
        with self.assertRaises(ValueError):
            Memory(current=99, radio=False).decode()

    def test_unknown_class_rejected(self):
        memory = Memory(current=1, radio=False)
        memory.data[0x3001] = ord("X")
        with self.assertRaises(ValueError):
            memory.decode()

    def test_changed_object_size_rejected(self):
        memory = Memory(current=1, radio=False)
        memory.put(0x2000 - 0x68, "Q", 0xB0)
        with self.assertRaises(ValueError):
            memory.decode()

    def test_unbounded_option_count_rejected(self):
        memory = Memory(labels=RADIOS)
        memory.put(0x4008, "i", 100000)
        with self.assertRaises(ValueError):
            memory.decode()

    def test_unbounded_string_rejected(self):
        memory = Memory(labels=RADIOS)
        memory.put(0x6000 - 4, "i", 100000)
        with self.assertRaises(ValueError):
            memory.decode()

    def test_expired_pointer_rejected(self):
        memory = Memory(labels=RADIOS)
        memory.put(0x1090, "Q", 0x100000)
        with self.assertRaises(OSError):
            memory.decode()


if __name__ == "__main__":
    unittest.main()
