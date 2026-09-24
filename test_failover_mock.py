#!/usr/bin/env python3
"""
Unit test suite verifying multiple API keys configuration, sequential failover,
and backward-compatible fallbacks across all Mailerone engines.
"""
import unittest
from unittest.mock import patch, MagicMock
from config_manager import (
    get_api_keys, set_api_keys, add_api_key, remove_api_key,
    get_api_key, set_api_key, normalize_keys
)
from api_engines import (
    HunterEngine, ContactOutEngine, SalesQLEngine, SignalHireEngine,
    FinalScoutEngine, AbstractAPIEngine, ZeroBounceEngine, DebounceEngine,
    MailboxlayerEngine, EmailRepEngine, OSINTEngine, APIQuotaEngine
)

class TestMultiKeyFailover(unittest.TestCase):

    def setUp(self):
        from config_manager import load_config
        self.orig_config = load_config()

    def tearDown(self):
        from config_manager import save_config
        save_config(self.orig_config)

    def test_config_manager_multi_key_crud(self):
        # 1. Normalize comma-separated and list inputs
        self.assertEqual(normalize_keys("key1, key2,  key3 "), ["key1", "key2", "key3"])
        self.assertEqual(normalize_keys(["k1", "", "  k2  "]), ["k1", "k2"])

        # 2. Set multiple keys on a test platform
        set_api_keys("test_mock_platform", ["mock_alpha", "mock_beta"])
        keys = get_api_keys("test_mock_platform")
        self.assertEqual(keys, ["mock_alpha", "mock_beta"])

        # 3. Add a single key
        add_api_key("test_mock_platform", "mock_gamma")
        self.assertEqual(get_api_keys("test_mock_platform"), ["mock_alpha", "mock_beta", "mock_gamma"])

        # 4. Remove a key
        remove_api_key("test_mock_platform", "mock_beta")
        self.assertEqual(get_api_keys("test_mock_platform"), ["mock_alpha", "mock_gamma"])

        # 5. Backwards compatibility: get_api_key returns first key, set_api_key sets list of one
        self.assertEqual(get_api_key("test_mock_platform"), "mock_alpha")
        set_api_key("test_mock_platform", "mock_solo")
        self.assertEqual(get_api_keys("test_mock_platform"), ["mock_solo"])

    @patch("requests.get")
    def test_hunter_engine_failover(self, mock_get):
        # Key 1 returns 401 Unauthorized, Key 2 returns 200 OK
        resp_401 = MagicMock(status_code=401, text="Unauthorized")
        resp_200 = MagicMock(status_code=200)
        resp_200.json.return_value = {
            "data": {
                "status": "valid",
                "result": "deliverable",
                "score": 98,
                "disposable": False,
                "mx_records": True,
                "smtp_check": True
            }
        }
        mock_get.side_effect = [resp_401, resp_200]

        res = HunterEngine.verify("alex@company.com", api_keys=["key_bad", "key_good"])
        self.assertTrue(res["success"])
        self.assertEqual(res["result"], "deliverable")
        self.assertEqual(res["key_index"], 2)
        self.assertEqual(res["total_keys"], 2)
        self.assertEqual(mock_get.call_count, 2)

    @patch("requests.post")
    def test_contactout_engine_failover(self, mock_post):
        # Key 1 returns 429 Too Many Requests, Key 2 returns 200 OK with email candidate
        resp_429 = MagicMock(status_code=429, text="Rate limit exceeded")
        resp_200 = MagicMock(status_code=200)
        resp_200.json.return_value = {
            "profile": {
                "work_emails": ["tim@apple.com"]
            }
        }
        mock_post.side_effect = [resp_429, resp_200]

        res = ContactOutEngine.find_email("apple.com", "Tim", "Cook", api_keys=["co_key1", "co_key2"])
        self.assertTrue(res["success"])
        self.assertEqual(res["primary_email"], "tim@apple.com")
        self.assertEqual(res["key_index"], 2)
        self.assertEqual(mock_post.call_count, 2)

    @patch("requests.get")
    def test_zerobounce_engine_failover(self, mock_get):
        # Key 1 returns 402 Payment Required / Credits Expired, Key 2 returns 200
        resp_402 = MagicMock(status_code=402, text="No credits remaining")
        resp_200 = MagicMock(status_code=200)
        resp_200.json.return_value = {
            "status": "valid",
            "sub_status": "",
            "free_email": False,
            "mx_found": "true",
            "smtp_provider": "google"
        }
        mock_get.side_effect = [resp_402, resp_200]

        res = ZeroBounceEngine.verify("user@domain.com", api_keys=["zb_empty", "zb_active"])
        self.assertTrue(res["success"])
        self.assertEqual(res["key_index"], 2)
        self.assertEqual(mock_get.call_count, 2)

    @patch("requests.get")
    def test_mailboxlayer_false_positive_rejection(self, mock_get):
        # APILayer returns 200 OK with success=False payload on bad/expired key
        resp_bad_json = MagicMock(status_code=200)
        resp_bad_json.json.return_value = {
            "success": False,
            "error": {"code": 101, "type": "invalid_access_key"}
        }
        resp_good = MagicMock(status_code=200)
        resp_good.json.return_value = {
            "format_valid": True,
            "mx_found": True,
            "smtp_check": True,
            "score": 0.95
        }
        mock_get.side_effect = [resp_bad_json, resp_good]

        res = MailboxlayerEngine.verify("user@corp.com", api_keys=["bad_mbl", "good_mbl"])
        self.assertTrue(res["success"])
        self.assertEqual(res["key_index"], 2)
        self.assertEqual(mock_get.call_count, 2)

    @patch("requests.get")
    def test_osint_github_multi_token_failover(self, mock_get):
        # Token 1 401, Token 2 200
        resp_401 = MagicMock(status_code=401)
        resp_200 = MagicMock(status_code=200)
        resp_200.json.return_value = {
            "total_count": 1,
            "items": [{"login": "octocat", "html_url": "https://github.com/octocat"}]
        }
        mock_get.side_effect = [resp_401, resp_200]

        res = OSINTEngine.check_github("octocat@github.com", tokens=["token_revoked", "token_valid"])
        self.assertTrue(res["found"])
        self.assertEqual(res["username"], "octocat")
        self.assertEqual(res["token_index"], 2)

    @patch("requests.get")
    def test_api_quota_engine_multi_key_aggregation(self, mock_get):
        # ZeroBounce balance check across 2 keys: key 1 has 50 credits, key 2 has 120 credits
        resp_k1 = MagicMock(status_code=200)
        resp_k1.json.return_value = {"Credits": "50"}
        resp_k2 = MagicMock(status_code=200)
        resp_k2.json.return_value = {"Credits": "120"}
        mock_get.side_effect = [resp_k1, resp_k2]

        zb_entry = APIQuotaEngine.check_zerobounce_quota(api_keys=["zb1", "zb2"])
        self.assertIsNotNone(zb_entry)
        self.assertEqual(zb_entry["credits_remaining"], 170)
        self.assertEqual(zb_entry["total_keys"], 2)
        self.assertEqual(len(zb_entry["keys_breakdown"]), 2)

if __name__ == "__main__":
    unittest.main()
