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
    ApolloEngine, HunterEngine, ContactOutEngine, SalesQLEngine, SignalHireEngine,
    FinalScoutEngine, AbstractAPIEngine, ZeroBounceEngine, DebounceEngine,
    MailboxlayerEngine, EmailRepEngine, OSINTEngine, APIQuotaEngine, AIScraperEngine
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

    @patch("requests.post")
    def test_apollo_engine_failover(self, mock_post):
        # Key 1 returns 401 Unauthorized, Key 2 returns 200 OK with matched person
        resp_401 = MagicMock(status_code=401, text="Unauthorized")
        resp_200 = MagicMock(status_code=200)
        resp_200.json.return_value = {
            "person": {
                "name": "Satya Nadella",
                "email": "satya@microsoft.com",
                "email_status": "verified",
                "title": "Chief Executive Officer",
                "organization": {
                    "name": "Microsoft"
                },
                "phone_numbers": [{"sanitized_number": "+1-425-882-8080"}]
            }
        }
        mock_post.side_effect = [resp_401, resp_200]

        res = ApolloEngine.find_email("microsoft.com", "Satya", "Nadella", api_keys=["apollo_bad", "apollo_good"])
        self.assertTrue(res["success"])
        self.assertEqual(res["primary_email"], "satya@microsoft.com")
        self.assertEqual(res["status"], "verified")
        self.assertEqual(res["company"], "Microsoft")
        self.assertEqual(res["key_index"], 2)
        self.assertEqual(res["total_keys"], 2)
        self.assertEqual(mock_post.call_count, 2)

    @patch("requests.get")
    def test_apollo_quota_engine(self, mock_get):
        # Key 1 returns active profile with 80 credits, Key 2 returns 401
        resp_k1 = MagicMock(status_code=200)
        resp_k1.json.return_value = {
            "user": {"email": "pro@enterprise.com", "name": "Lead Ops"},
            "plan_name": "Professional",
            "credits_remaining": 80
        }
        resp_k2 = MagicMock(status_code=401, text="Invalid API key")
        mock_get.side_effect = [resp_k1, resp_k2]

        res = APIQuotaEngine.check_apollo_quota(api_keys=["k1_valid", "k2_expired"])
        self.assertTrue(res["success"])
        self.assertEqual(res["service"], "Apollo.io")
        self.assertEqual(res["active_keys"], 1)
        self.assertEqual(res["total_keys"], 2)
        self.assertEqual(res["credits_remaining"], 80)
        self.assertEqual(len(res["keys_breakdown"]), 2)

    def test_ai_scraper_obfuscation_and_email_extraction(self):
        sample_markup = (
            "<html><body>"
            "<p>Contact CEO: satya.nadella [at] microsoft [dot] com</p>"
            "<p>Support: <a href='mailto:support@microsoft.com?subject=Help'>support@microsoft.com</a></p>"
            "<p>Billing: billing(at)microsoft.com</p>"
            "<p>De-cloaked entity: info&#64;microsoft&#46;com</p>"
            "<p>Ignore bad files: avatar@2x.png and logo@3x.jpg and test@example.com</p>"
            "<p>External PR: press@reputationwire.com</p>"
            "</body></html>"
        )
        emails = AIScraperEngine.extract_emails(sample_markup, base_domain="microsoft.com")
        extracted_addresses = [e["email"] for e in emails]

        self.assertIn("satya.nadella@microsoft.com", extracted_addresses)
        self.assertIn("support@microsoft.com", extracted_addresses)
        self.assertIn("billing@microsoft.com", extracted_addresses)
        self.assertIn("info@microsoft.com", extracted_addresses)
        self.assertIn("press@reputationwire.com", extracted_addresses)

        # Confirm false positives were rejected
        self.assertNotIn("avatar@2x.png", extracted_addresses)
        self.assertNotIn("test@example.com", extracted_addresses)

        # Confirm role categorization
        categories = {e["email"]: e["category"] for e in emails}
        self.assertEqual(categories["satya.nadella@microsoft.com"], "Executive / Personal")
        self.assertEqual(categories["support@microsoft.com"], "Role / Departmental")
        self.assertEqual(categories["press@reputationwire.com"], "External / Vendor")

    def test_ai_scraper_phone_and_social_extraction(self):
        sample_markup = (
            "<html><body>"
            "<p>Toll-Free Phone: <a href='tel:+18005550199'>+1 (800) 555-0199</a></p>"
            "<p>Support Line: +1-425-882-8080</p>"
            "<a href='https://www.linkedin.com/company/microsoft'>Company LinkedIn</a>"
            "<a href='https://www.linkedin.com/in/satyanadella'>Satya LinkedIn</a>"
            "<a href='https://x.com/satyanadella'>Satya Twitter/X</a>"
            "<a href='https://github.com/microsoft'>Microsoft GitHub</a>"
            "<a href='https://youtube.com/@Microsoft'>YouTube</a>"
            "<footer>Address: One Microsoft Way, Redmond, WA 98052</footer>"
            "</body></html>"
        )
        phones = AIScraperEngine.extract_phone_numbers(sample_markup)
        phone_numbers = [p["number"] for p in phones]
        self.assertTrue(any("800" in p for p in phone_numbers))
        self.assertTrue(any("425" in p for p in phone_numbers))

        socials = AIScraperEngine.extract_social_accounts(sample_markup)
        self.assertEqual(len(socials["linkedin_company"]), 1)
        self.assertEqual(socials["linkedin_company"][0]["handle"], "microsoft")
        self.assertEqual(len(socials["linkedin_personal"]), 1)
        self.assertEqual(socials["linkedin_personal"][0]["handle"], "satyanadella")
        self.assertEqual(len(socials["twitter_x"]), 1)
        self.assertEqual(socials["twitter_x"][0]["handle"], "@satyanadella")
        self.assertEqual(len(socials["github"]), 1)
        self.assertEqual(socials["github"][0]["handle"], "microsoft")
        self.assertEqual(len(socials["youtube"]), 1)

    @patch("requests.Session.get")
    def test_ai_scraper_end_to_end_crawl_and_heuristic_ai(self, mock_session_get):
        home_html = (
            "<html><head><title>Stripe - Financial Infrastructure</title>"
            "<meta name='description' content='Payments infrastructure for the internet.'></head>"
            "<body><a href='/contact'>Contact</a><a href='/team'>Team</a>"
            "<a href='https://www.linkedin.com/company/stripe'>LI</a>"
            "<a href='https://x.com/stripe'>Twitter</a>"
            "<p>General: info@stripe.com</p>"
            "</body></html>"
        )
        team_html = (
            "<html><body>"
            "<h1>Leadership Team</h1>"
            "<p>Patrick Collison</p><p>Chief Executive Officer</p>"
            "<p>Contact: patrick@stripe.com</p>"
            "<p>John Collison</p><p>President</p>"
            "<p>Contact: john@stripe.com</p>"
            "</body></html>"
        )
        contact_html = (
            "<html><body>"
            "<p>Support: support@stripe.com or call +1 (888) 926-2289</p>"
            "<footer>Headquarters: 354 Oyster Point Blvd, South San Francisco, CA 94080</footer>"
            "</body></html>"
        )

        def mock_router(url, *args, **kwargs):
            resp = MagicMock(status_code=200)
            resp.headers = {"Content-Type": "text/html"}
            if "team" in url:
                resp.text = team_html
            elif "contact" in url:
                resp.text = contact_html
            else:
                resp.text = home_html
            resp.url = url
            return resp

        mock_session_get.side_effect = mock_router

        dossier = AIScraperEngine.harvest("stripe.com", max_pages=4, ai_provider="heuristic")
        self.assertTrue(dossier["success"])
        self.assertEqual(dossier["base_domain"], "stripe.com")
        self.assertIn("Stripe", dossier["title"])

        found_emails = [e["email"] for e in dossier["emails"]]
        self.assertIn("info@stripe.com", found_emails)
        self.assertIn("patrick@stripe.com", found_emails)
        self.assertIn("support@stripe.com", found_emails)

        found_phones = [p["number"] for p in dossier["phones"]]
        self.assertTrue(any("888" in p for p in found_phones))

        # Check detected leadership
        team_names = [t["name"] for t in dossier["team_leadership"]]
        self.assertIn("Patrick Collison", team_names)
        self.assertIn("John Collison", team_names)

    @patch("requests.post")
    @patch("requests.Session.get")
    def test_ai_scraper_llm_execution(self, mock_session_get, mock_post):
        mock_resp = MagicMock(status_code=200)
        mock_resp.headers = {"Content-Type": "text/html"}
        mock_resp.text = "<html><head><title>Acme Inc</title></head><body><p>support@acme.com</p></body></html>"
        mock_resp.url = "https://acme.com"
        mock_session_get.return_value = mock_resp

        # Mock OpenAI response
        llm_resp = MagicMock(status_code=200)
        llm_resp.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"company_name": "Acme Global", "industry": "Cloud SaaS", "summary": "Next-gen automation platform", "executives": [{"name": "Jane Doe", "title": "Founder & CEO", "email": "jane@acme.com"}], "department_contacts": [{"department": "Sales", "email": "sales@acme.com"}]}'
                }
            }]
        }
        mock_post.return_value = llm_resp

        with patch("ai_scraper.get_api_key", return_value="sk-test-fake-key"):
            dossier = AIScraperEngine.harvest("acme.com", max_pages=1, ai_provider="openai")
            self.assertTrue(dossier["success"])
            self.assertEqual(dossier["company_name"], "Acme Global")
            self.assertEqual(dossier["industry"], "Cloud SaaS")
            emails = [e["email"] for e in dossier["emails"]]
            self.assertIn("sales@acme.com", emails)
            self.assertIn("support@acme.com", emails)

if __name__ == "__main__":
    unittest.main()
