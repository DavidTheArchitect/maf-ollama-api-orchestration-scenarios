import ast
import json
import unittest
from pathlib import Path

from release_room.scenarios import SCENARIOS


class NotebookCompanionTests(unittest.TestCase):
    def test_each_scenario_notebook_compiles(self):
        project_root = Path(__file__).resolve().parents[1]
        notebooks = sorted((project_root / "notebooks").glob("*.ipynb"))
        self.assertEqual(len(notebooks), len(SCENARIOS))

        seen: set[str] = set()
        for path in notebooks:
            with self.subTest(notebook=path.name):
                data = json.loads(path.read_text(encoding="utf-8"))
                source_text = "\n".join("".join(cell.get("source", [])) for cell in data.get("cells", []))
                scenario_ids = [scenario.id for scenario in SCENARIOS if scenario.id in source_text]
                self.assertEqual(len(scenario_ids), 1)
                seen.add(scenario_ids[0])
                self.assertIn("release_room.notebook_helpers", source_text)
                self.assertIn("Pattern Anatomy", source_text)

                for index, cell in enumerate(data.get("cells", [])):
                    self.assertIsNone(cell.get("execution_count"))
                    self.assertFalse(cell.get("outputs"))
                    if cell.get("cell_type") == "code":
                        source = "".join(cell.get("source", []))
                        compile(source, f"{path}#cell{index}", "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)

        self.assertEqual(seen, {scenario.id for scenario in SCENARIOS})


if __name__ == "__main__":
    unittest.main()
