import tempfile
import unittest
from pathlib import Path

from backend.src.controllers.frontend_controller import FrontendController


class FrontendControllerTest(unittest.TestCase):
    def test_get_index_serves_html(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "index.html").write_text("<!doctype html><title>tube</title>", encoding="utf-8")

            controller = FrontendController(root)

            response = controller.get_index()

            self.assertEqual(200, response.status_code)
            self.assertEqual("text/html; charset=utf-8", response.headers["Content-Type"])
            self.assertEqual("no-cache", response.headers["Cache-Control"])
            self.assertIn(b"<title>tube</title>", response.body)

    def test_get_asset_blocks_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "index.html").write_text("ok", encoding="utf-8")
            outside_file = root.parent / "outside.txt"
            outside_file.write_text("nope", encoding="utf-8")

            controller = FrontendController(root)

            response = controller.get_asset("../outside.txt")

            self.assertEqual(404, response.status_code)
            self.assertEqual("application/json; charset=utf-8", response.headers["Content-Type"])
            self.assertEqual({"error": "not found"}, response.body)


if __name__ == "__main__":
    unittest.main()
