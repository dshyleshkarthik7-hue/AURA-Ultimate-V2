import unittest
import numpy as np

from train import split_indices


class SessionSplitTests(unittest.TestCase):
    def test_sessions_never_cross_partitions(self):
        labels = []
        groups = []
        for class_id in range(2):
            for session in range(4):
                for frame in range(5):
                    labels.append(class_id)
                    groups.append(f"class{class_id}/session{session}")
        rng = np.random.default_rng(42)
        train, validation, test = split_indices(
            np.asarray(labels), np.asarray(groups), 2, .2, .2, rng
        )
        partitions = [
            {groups[i] for i in part}
            for part in (train, validation, test)
        ]
        self.assertFalse(partitions[0] & partitions[1])
        self.assertFalse(partitions[0] & partitions[2])
        self.assertFalse(partitions[1] & partitions[2])
        for part in (train, validation, test):
            self.assertEqual(set(labels[i] for i in part), {0, 1})

    def test_requires_multiple_sessions_per_class(self):
        labels = np.asarray([0, 0, 1, 1, 1, 1])
        groups = np.asarray(["a/s1", "a/s1", "b/s1", "b/s2", "b/s3", "b/s3"])
        with self.assertRaisesRegex(ValueError, "at least 3"):
            split_indices(labels, groups, 2, .2, .2, np.random.default_rng(1))


if __name__ == "__main__":
    unittest.main()
