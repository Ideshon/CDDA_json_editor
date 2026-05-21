from __future__ import annotations

import importlib
import unittest


class TestPackageEntrypoint(unittest.TestCase):
    def test_main_module_is_importable_as_a_package_entrypoint(self) -> None:
        try:
            importlib.import_module("PyQt5")
        except ImportError:
            self.skipTest("PyQt5 is not installed in this Python environment")

        module = importlib.import_module("CDDA_editor.main")

        self.assertTrue(callable(module.main))


if __name__ == "__main__":
    unittest.main()
