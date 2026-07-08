import inspect
import unittest
from importlib import import_module
from pathlib import Path

from invocations_scenarios.diagram_helpers import quote_to_cash_flow_diagram
from invocations_scenarios.scenarios import SCENARIOS_BY_ID

PATTERN_TO_LETTER = {
    "sequential": "16a",
    "concurrent": "16b",
    "handoff": "16c",
    "group-chat": "16d",
    "magentic": "16e",
}

CANONICAL_ROLES = {
    "QuoteTriggerAgent",
    "CustomerContextAgent",
    "SkuDiscoveryAgent",
    "ProductFitAgent",
    "PricingTermsAgent",
    "QuoteGenerationAgent",
}

DIAGRAM_MARKERS = (
    "CRM system",
    "Orchestration store: customer context",
    "Orchestration store: product context",
    "Product / SKU system",
    "Pricing / finance / legal system",
    "deallocate wave 1",
    "deallocate wave 2",
    "Final quote package",
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def scenario_ids():
    return [f"scenario-16-quote-to-cash-{pattern}" for pattern in PATTERN_TO_LETTER]


class QuoteToCashScenarioTests(unittest.TestCase):
    def test_all_five_variants_registered(self):
        for sid in scenario_ids():
            with self.subTest(scenario=sid):
                self.assertIn(sid, SCENARIOS_BY_ID)

    def test_each_variant_uses_the_six_canonical_roles(self):
        for sid in scenario_ids():
            scenario = SCENARIOS_BY_ID[sid]
            with self.subTest(scenario=sid):
                names = {agent.name for agent in scenario.agents}
                self.assertEqual(names, CANONICAL_ROLES)

    def test_each_module_exposes_run_sample_and_main(self):
        for sid in scenario_ids():
            module_name = sid.replace("-", "_")
            with self.subTest(scenario=sid):
                module = import_module(f"invocations_scenarios.scenarios.{module_name}")
                self.assertIs(module.SCENARIO, SCENARIOS_BY_ID[sid])
                self.assertTrue(inspect.iscoroutinefunction(module.run_sample))
                source = inspect.getsource(module)
                self.assertIn('if __name__ == "__main__":', source)

    def test_quote_to_cash_diagram_has_business_systems(self):
        for sid in scenario_ids():
            scenario = SCENARIOS_BY_ID[sid]
            with self.subTest(scenario=sid):
                mermaid = quote_to_cash_flow_diagram(scenario).mermaid
                self.assertTrue(mermaid.startswith("flowchart TD"))
                self.assertIn(scenario.id, mermaid)
                self.assertIn(scenario.pattern, mermaid)
                for marker in DIAGRAM_MARKERS:
                    self.assertIn(marker, mermaid)
                for role in CANONICAL_ROLES:
                    self.assertIn(role, mermaid)

    def test_each_variant_has_sample_and_notebook(self):
        for pattern, letter in PATTERN_TO_LETTER.items():
            sid = f"scenario-16-quote-to-cash-{pattern}"
            with self.subTest(scenario=sid):
                sample = PROJECT_ROOT / "samples" / f"{sid}.json"
                self.assertTrue(sample.exists(), sample)
                notebook = PROJECT_ROOT / "notebooks" / f"{letter}-{sid}.ipynb"
                self.assertTrue(notebook.exists(), notebook)


if __name__ == "__main__":
    unittest.main()
