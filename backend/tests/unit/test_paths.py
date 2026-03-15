import unittest
from pathlib import Path

from backend.src.config.paths import FRONTEND_DIR, ROOT_DIR


class PathsTest(unittest.TestCase):
    def test_root_dir_points_to_repo_root(self) -> None:
        expected_root = Path(__file__).resolve().parents[3]

        self.assertEqual(expected_root, ROOT_DIR)
        self.assertTrue((ROOT_DIR / "README.md").is_file())
        self.assertTrue((ROOT_DIR / "backend").is_dir())
        self.assertTrue((ROOT_DIR / "docs").is_dir())

    def test_frontend_dir_points_to_frontend_directory(self) -> None:
        self.assertEqual(ROOT_DIR / "frontend", FRONTEND_DIR)
        self.assertTrue((FRONTEND_DIR / "index.html").is_file())


if __name__ == "__main__":
    unittest.main()
