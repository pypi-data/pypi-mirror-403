import importlib.util
import os
import unittest


class TestVersionFile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        package_dir = os.path.join(os.path.dirname(__file__), "../../tangogql")
        version_file_path = os.path.join(package_dir, "_version.py")

        if not os.path.exists(version_file_path):
            raise FileNotFoundError(f"Expected _version.py at {version_file_path}")

        # Load the module from the _version.py file
        spec = importlib.util.spec_from_file_location("_version", version_file_path)
        cls.version_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.version_module)

    def test_version_attributes(self):
        self.assertTrue(
            hasattr(self.version_module, "__version__"), "Missing __version__ attribute"
        )
        self.assertTrue(
            hasattr(self.version_module, "version"), "Missing version attribute"
        )
        self.assertTrue(
            hasattr(self.version_module, "__version_tuple__"),
            "Missing __version_tuple__ attribute",
        )
        self.assertTrue(
            hasattr(self.version_module, "version_tuple"),
            "Missing version_tuple attribute",
        )

        self.assertEqual(
            self.version_module.__version__,
            self.version_module.version,
            "__version__ and version should be identical",
        )
        self.assertEqual(
            self.version_module.__version_tuple__,
            self.version_module.version_tuple,
            "__version_tuple__ and version_tuple should be identical",
        )

    def test_version_tuple(self):
        self.assertIsInstance(
            self.version_module.__version_tuple__,
            tuple,
            "version_tuple should be a tuple",
        )
        self.assertTrue(
            all(
                isinstance(part, int | str)
                for part in self.version_module.__version_tuple__
            ),
            "version_tuple should contain only int or str elements",
        )
        self.assertGreaterEqual(
            len(self.version_module.__version_tuple__),
            2,
            "version_tuple should have at least 2 elements",
        )


if __name__ == "__main__":
    unittest.main()
