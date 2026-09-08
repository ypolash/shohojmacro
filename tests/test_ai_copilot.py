import unittest
from unittest.mock import MagicMock
from shohoj_macro.core.events import MacroEvent, EventType, ErrorPolicy
from shohoj_macro.ai.captcha_solver import ReCaptchaSolver

class TestAICoPilot(unittest.TestCase):
    def test_macro_event_from_dict_unknown_keys(self):
        """Verify MacroEvent.from_dict ignores unrecognized keys without crashing."""
        raw_dict = {
            "event_type": "cdp_physical_input",
            "selector": "button#submit",
            "text": "Click",
            "unknown_extra_field": "some_value",
            "ai_meta": {"model": "gpt-4"}
        }
        event = MacroEvent.from_dict(raw_dict)
        self.assertEqual(event.event_type, EventType.CDP_PHYSICAL_INPUT)
        self.assertEqual(event.selector, "button#submit")
        self.assertEqual(event.text, "Click")

    def test_recaptcha_solver_init(self):
        """Verify ReCaptchaSolver initializes without error when cdp bridge has no stored page."""
        mock_cdp = MagicMock()
        mock_cdp.is_alive.return_value = False
        mock_ai = MagicMock()
        
        solver = ReCaptchaSolver(mock_cdp, mock_ai)
        result = solver.solve()
        self.assertFalse(result)

    def test_json_repair_parsing(self):
        """Verify AITrainingWizard._parse_and_repair_json handles malformed quotes in selectors."""
        from shohoj_macro.gui.ai_training_wizard import AITrainingWizard
        malformed_raw = '''
        [
          {
            "action": "type",
            "selector": "input[name="mobile"]",
            "text": "{{Mobile}}",
            "description": "Type mobile"
          },
          {
            "action": "select",
            "selector": "select[name="ethnicity"]",
            "text": "1st option",
            "description": "Select ethnicity"
          }
        ]
        '''
        wizard_mock = MagicMock()
        steps = AITrainingWizard._parse_and_repair_json(wizard_mock, malformed_raw)
        self.assertEqual(len(steps), 2)
        self.assertEqual(steps[0]["action"], "type")
        self.assertIn("mobile", steps[0]["selector"])

if __name__ == "__main__":
    unittest.main()
