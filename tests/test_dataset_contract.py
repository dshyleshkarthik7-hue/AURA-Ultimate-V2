import tempfile
import unittest
from pathlib import Path

from aura.data import validate_dataset


class DatasetContractTests(unittest.TestCase):
    def test_contract_rejects_unexpected_label_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for label in ("a", "b", "old"):
                (root / label).mkdir()
            for label in ("a", "b"):
                for i in range(2):
                    (root / label / f"{i}.jpg").write_bytes(b"x")
            with self.assertRaises(ValueError):
                validate_dataset(root, ["a", "b"], 2)

    def test_unknown_directory_is_allowed_but_not_a_class(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for label in ("a", "b", "unknown"):
                (root / label).mkdir()
            for label in ("a", "b"):
                for i in range(2):
                    (root / label / f"{i}.jpg").write_bytes(b"x")
            mapping = validate_dataset(root, ["a", "b"], 2)
            self.assertEqual(set(mapping), {"a", "b"})
            self.assertEqual(len(list((root / "unknown").glob("*.jpg"))), 0)


if __name__ == "__main__":
    unittest.main()
