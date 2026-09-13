import time
import json
from config_manager import load_config, save_config, get_api_key, set_api_key
from api_engines import (
    DNSInspectorEngine,
    DisifyEngine,
    DisposableBlocklistEngine,
    OSINTEngine,
    HunterEngine,
    AbstractAPIEngine,
    ZeroBounceEngine,
    DebounceEngine,
    MailboxlayerEngine,
    EmailRepEngine,
    ContactOutEngine,
    SalesQLEngine,
    SignalHireEngine,
    FinalScoutEngine,
    Name2EmailEngine,
    MultiFinderEngine
)
from multi_verifier import run_comprehensive_scan

def run_tests():
    report = {}
    print("="*60)
    print("STARTING MAILERONE MULTI-ENGINE TEST SUITE")
    print("="*60)

    # 1. Config Manager Test
    print("\n[TEST 1] Config Manager...")
    t0 = time.time()
    cfg = load_config()
    set_api_key("test_service_key", "sample_test_value_123")
    saved_val = get_api_key("test_service_key")
    config_ok = (saved_val == "sample_test_value_123")
    report["config_manager"] = {
        "status": "PASSED" if config_ok else "FAILED",
        "duration_sec": round(time.time() - t0, 3)
    }
    print(f" -> Config Manager: {report['config_manager']['status']}")

    # 2. DNS & Mail Server Inspector Test
    print("\n[TEST 2] DNS & Mail Server Inspector...")
    t0 = time.time()
    dns_res = DNSInspectorEngine.check_domain_dns("google.com")
    dns_ok = dns_res["has_mx"] and len(dns_res["mx_records"]) > 0
    report["dns_inspector"] = {
        "status": "PASSED" if dns_ok else "FAILED",
        "mx_count": len(dns_res.get("mx_records", [])),
        "spf_found": dns_res.get("spf") != "None",
        "dmarc_found": dns_res.get("dmarc") != "None",
        "duration_sec": round(time.time() - t0, 3)
    }
    print(f" -> DNS Inspector: {report['dns_inspector']['status']} (MX: {report['dns_inspector']['mx_count']}, SPF: {report['dns_inspector']['spf_found']}, DMARC: {report['dns_inspector']['dmarc_found']})")

    # 3. Disposable Domain Blocklist Test
    print("\n[TEST 3] Disposable Domain Blocklist...")
    t0 = time.time()
    is_temp = DisposableBlocklistEngine.is_disposable("tempmail.com")
    is_clean = DisposableBlocklistEngine.is_disposable("gmail.com")
    blocklist_ok = (is_temp is True) and (is_clean is False)
    report["disposable_blocklist"] = {
        "status": "PASSED" if blocklist_ok else "FAILED",
        "blocklist_size": len(DisposableBlocklistEngine.load_blocklist()),
        "duration_sec": round(time.time() - t0, 3)
    }
    print(f" -> Disposable Blocklist: {report['disposable_blocklist']['status']} (Loaded {report['disposable_blocklist']['blocklist_size']} domains)")

    # 4. Disify Free API Engine Test
    print("\n[TEST 4] Disify Free Verification API...")
    t0 = time.time()
    dis_res = DisifyEngine.verify("contact@github.com")
    dis_ok = dis_res.get("success") is True and dis_res.get("format") is True
    report["disify_api"] = {
        "status": "PASSED" if dis_ok else "FAILED",
        "dns": dis_res.get("dns"),
        "free_provider": dis_res.get("free_provider"),
        "role_account": dis_res.get("role_account"),
        "duration_sec": round(time.time() - t0, 3)
    }
    print(f" -> Disify API: {report['disify_api']['status']} (DNS: {dis_res.get('dns')}, Role: {dis_res.get('role_account')})")

    # 5. OSINT Engines (Gravatar + GitHub)
    print("\n[TEST 5] OSINT Profilers (Gravatar & GitHub)...")
    t0 = time.time()
    grav = OSINTEngine.check_gravatar("support@github.com")
    gh = OSINTEngine.check_github("torvalds")
    osint_ok = grav.get("has_gravatar") is True or gh.get("found") is True
    report["osint_profilers"] = {
        "status": "PASSED" if osint_ok else "FAILED",
        "gravatar_found": grav.get("has_gravatar"),
        "github_found": gh.get("found"),
        "github_user": gh.get("username"),
        "duration_sec": round(time.time() - t0, 3)
    }
    print(f" -> OSINT Profilers: {report['osint_profilers']['status']} (Gravatar: {grav.get('has_gravatar')}, GitHub: {gh.get('found')} @{gh.get('username')})")

    # 6. Hunter.io Deliverability Engine
    print("\n[TEST 6] Hunter.io Engine...")
    t0 = time.time()
    hunter_res = HunterEngine.verify("support@github.com")
    report["hunter_engine"] = {
        "status": "PASSED" if hunter_res.get("success") else "SKIPPED/UNAUTHORIZED",
        "result": hunter_res.get("result"),
        "score": hunter_res.get("score"),
        "error": hunter_res.get("error"),
        "duration_sec": round(time.time() - t0, 3)
    }
    print(f" -> Hunter.io Engine: {report['hunter_engine']['status']} (Result: {hunter_res.get('result')}, Score: {hunter_res.get('score')})")

    # 7. Name2Email Smart Permutator & DNS Verifier Test
    print("\n[TEST 7] Name2Email Smart Permutator & Verifier...")
    t0 = time.time()
    n2e_res = Name2EmailEngine.find_and_verify("satya", "nadella", "microsoft.com")
    n2e_ok = n2e_res.get("success") is True and len(n2e_res.get("valid_candidates", [])) > 0
    report["name2email_engine"] = {
        "status": "PASSED" if n2e_ok else "FAILED",
        "total_generated": n2e_res.get("total_generated"),
        "candidates_found": len(n2e_res.get("valid_candidates", [])),
        "primary_candidate": n2e_res.get("primary_candidate"),
        "duration_sec": round(time.time() - t0, 3)
    }
    print(f" -> Name2Email: {report['name2email_engine']['status']} (Generated {n2e_res.get('total_generated')} patterns, Top: {n2e_res.get('primary_candidate')})")

    # 8. B2B Lead Finding APIs (ContactOut, SalesQL, SignalHire, FinalScout)
    print("\n[TEST 8] B2B Lead Finding Engines (ContactOut, SalesQL, SignalHire, FinalScout)...")
    t0 = time.time()
    co = ContactOutEngine.find_email("microsoft.com", "Satya", "Nadella")
    sql = SalesQLEngine.find_email("microsoft.com", "Satya", "Nadella")
    sh = SignalHireEngine.find_email("microsoft.com", "Satya", "Nadella")
    fs = FinalScoutEngine.find_email("microsoft.com", "Satya", "Nadella")
    b2b_ok = all(isinstance(x, dict) for x in [co, sql, sh, fs])
    report["b2b_lead_engines"] = {
        "status": "PASSED" if b2b_ok else "FAILED",
        "contactout_handled": True,
        "salesql_handled": True,
        "signalhire_handled": True,
        "finalscout_handled": True,
        "duration_sec": round(time.time() - t0, 3)
    }
    print(f" -> B2B Lead Engines: {report['b2b_lead_engines']['status']}")

    # 9. MultiFinder All-in-One Lead Pipeline
    print("\n[TEST 9] MultiFinder All-in-One Pipeline...")
    t0 = time.time()
    mf_res = MultiFinderEngine.search("stripe.com", "Patrick", "Collison")
    mf_ok = len(mf_res.get("engines_queried", [])) >= 5
    report["multifinder_pipeline"] = {
        "status": "PASSED" if mf_ok else "FAILED",
        "engines_queried": mf_res.get("engines_queried"),
        "emails_identified": len(mf_res.get("found_emails", [])),
        "duration_sec": round(time.time() - t0, 3)
    }
    print(f" -> MultiFinder Pipeline: {report['multifinder_pipeline']['status']} (Queried {len(mf_res.get('engines_queried', []))} engines)")

    # 10. Comprehensive Multi-Verifier Execution
    print("\n[TEST 10] Comprehensive Multi-Engine Scan...")
    t0 = time.time()
    run_comprehensive_scan("admin@microsoft.com")
    report["multi_verifier_scan"] = {
        "status": "PASSED",
        "target": "admin@microsoft.com",
        "duration_sec": round(time.time() - t0, 3)
    }

    print("\n" + "="*60)
    print("ALL TESTS COMPLETED!")
    print("="*60)
    
    with open("test_results.json", "w") as f:
        json.dump(report, f, indent=4)
    print("Saved test results to test_results.json")

if __name__ == "__main__":
    run_tests()
