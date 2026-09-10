import unittest
from unittest.mock import patch, MagicMock
from shohoj_macro.core.nst_controller import NSTController

class TestNSTController(unittest.TestCase):
    
    def test_init_defaults(self):
        nst = NSTController()
        self.assertIn("localhost:8848", nst.base_url)
        
    def test_launch_api_exact_match(self):
        nst = NSTController(api_key="test_key", local_url="http://localhost:8848")
        
        mock_search_resp = MagicMock()
        mock_search_resp.ok = True
        mock_search_resp.status_code = 200
        mock_search_resp.json.return_value = {
            "data": {
                "docs": [
                    {"profileId": "id_101", "name": "user2@test.com", "email": "user2@test.com"},
                    {"profileId": "id_102", "name": "user1@test.com", "email": "user1@test.com"}
                ]
            }
        }
        
        mock_connect_resp = MagicMock()
        mock_connect_resp.ok = True
        mock_connect_resp.status_code = 200
        mock_connect_resp.json.return_value = {
            "data": {
                "webSocketDebuggerUrl": "ws://127.0.0.1:9222/devtools/browser/abc"
            }
        }

        def mock_get_side_effect(url, *args, **kwargs):
            if "profiles" in url:
                return mock_search_resp
            return mock_connect_resp

        with patch("requests.get", side_effect=mock_get_side_effect):
            ws_url = nst.prepare_and_launch("user1@test.com")
            self.assertEqual(ws_url, "ws://127.0.0.1:9222/devtools/browser/abc")
            self.assertEqual(nst.last_launched_profile_id, "id_102")

    def test_stop_profile(self):
        nst = NSTController(api_key="test_key")
        nst.last_launched_profile_id = "prof_999"
        
        mock_resp = MagicMock()
        mock_resp.ok = True
        
        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = nst.stop_profile()
            self.assertTrue(result)
            self.assertIsNone(nst.last_launched_profile_id)

if __name__ == "__main__":
    unittest.main()
