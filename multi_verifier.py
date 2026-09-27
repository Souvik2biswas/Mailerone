import re
import sys
from api_engines import (
    DNSInspectorEngine,
    DisifyEngine,
    DisposableBlocklistEngine,
    OSINTEngine,
    ApolloEngine,
    HunterEngine,
    AbstractAPIEngine,
    ZeroBounceEngine,
    DebounceEngine,
    MailboxlayerEngine,
    EmailRepEngine
)

r = "\033[31m"
g = "\033[32m"
y = "\033[33m"
b = "\033[34m"
p = "\033[35m"
w = "\033[0m"

W = f"{w}\033[1;47m"
R = f"{w}\033[1;41m"
G = f"{w}\033[1;42m"
Y = f"{w}\033[1;43m"
B = f"{w}\033[1;44m"

space = "    "
lines = space + "-" * 75

ROLE_PREFIXES = {
    "admin", "administrator", "support", "info", "sales", "contact", "help",
    "billing", "office", "jobs", "careers", "hr", "marketing", "press", "media",
    "enquiries", "team", "service", "hello", "mail", "webmaster", "postmaster",
    "hostmaster", "abuse", "security", "privacy", "compliance", "legal", "finance",
    "accounting", "dev", "developer", "engineering", "ops", "operations",
    "feedback", "general", "inquiry", "orders", "tech"
}

COMMON_FREE_DOMAINS = {
    "gmail.com", "googlemail.com", "yahoo.com", "ymail.com", "rocketmail.com",
    "hotmail.com", "outlook.com", "live.com", "msn.com", "icloud.com", "me.com",
    "mac.com", "aol.com", "aim.com", "proton.me", "protonmail.com", "zoho.com",
    "mail.com", "gmx.com", "gmx.net", "yandex.ru", "yandex.com", "mail.ru",
    "bk.ru", "inbox.ru", "list.ru", "tutanota.com", "fastmail.com", "naver.com",
    "daum.net", "qq.com", "163.com", "126.com", "sina.com"
}

def is_valid_syntax(email):
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))

def calculate_deliverability_score(email, dns_res=None, is_burner=False, disify_res=None, api_results=None):
    """
    Calculates a 0-100% weighted Deliverability Score and verdict (DELIVERABLE, RISKY, UNDELIVERABLE)
    based on the Mailerone deliverability rubric:
      - MX Active                 : +40 pts
      - Clean / Not Disposable    : +25 pts
      - SPF Authentication        : +15 pts (or +5 implicit via MX)
      - DMARC Policy Alignment    : +10 pts
      - Non-Role Account          : +5 pts
      - Corporate / Custom Domain : +5 pts
      - Commercial API Adjustments (ZeroBounce, AbstractAPI, Hunter, Debounce, Mailboxlayer, EmailRep)
    """
    if not email or "@" not in email:
        return {
            "email": email or "",
            "score": 0,
            "verdict": "UNDELIVERABLE",
            "risk_level": "CRITICAL (Invalid email syntax)",
            "breakdown": {},
            "api_signals": ["Invalid syntax: Missing or malformed '@' address."]
        }

    username, domain = email.split("@", 1)
    username = username.lower().strip()
    domain = domain.lower().strip()

    dns_res = dns_res or {}
    disify_res = disify_res or {}
    api_results = api_results or {}

    # Signal 1: MX records (+40)
    has_mx = bool(dns_res.get("has_mx"))
    mx_count = len(dns_res.get("mx_records", []))
    if has_mx:
        mx_pts = 40
        mx_detail = f"Active ({mx_count} MX server{'s' if mx_count != 1 else ''} online)"
    else:
        mx_pts = 0
        mx_detail = "No active MX records found (Domain cannot receive email)"

    # Signal 2: Disposable / Burner Check (+25)
    burner_flag = bool(is_burner or disify_res.get("disposable"))
    if burner_flag:
        burner_pts = 0
        burner_detail = "FLAGGED (Known disposable / temporary burner domain)"
    else:
        burner_pts = 25
        burner_detail = "Clean (Domain not in 8,700+ burner blocklist)"

    # Signal 3: SPF Authentication (+15 explicit, +5 implicit via MX)
    spf_str = str(dns_res.get("spf", "None")).strip()
    has_spf = bool(spf_str and spf_str != "None" and "v=spf1" in spf_str)
    if has_spf:
        spf_pts = 15
        spf_detail = "Valid SPF record configured (v=spf1)"
    elif has_mx:
        spf_pts = 5
        spf_detail = "Implicit mail routing via MX (No explicit SPF)"
    else:
        spf_pts = 0
        spf_detail = "None (No SPF policy configured)"

    # Signal 4: DMARC Policy (+10)
    dmarc_str = str(dns_res.get("dmarc", "None")).strip()
    has_dmarc = bool(dmarc_str and dmarc_str != "None" and ("v=DMARC1" in dmarc_str or "DMARC" in dmarc_str))
    if has_dmarc:
        dmarc_pts = 10
        dmarc_detail = "Enforced DMARC record found (v=DMARC1)"
    else:
        dmarc_pts = 0
        dmarc_detail = "Unconfigured / Missing DMARC record"

    # Signal 5: Role Account (+5)
    if disify_res.get("success") and "role_account" in disify_res:
        is_role = bool(disify_res.get("role_account"))
    else:
        is_role = (username in ROLE_PREFIXES)

    if not is_role:
        role_pts = 5
        role_detail = "Personal / Named mailbox handle"
    else:
        role_pts = 0
        role_detail = "Role-based mailbox handle (admin/support/sales)"

    # Signal 6: Corporate Domain (+5)
    if disify_res.get("success") and "free_provider" in disify_res:
        is_free = bool(disify_res.get("free_provider"))
    else:
        is_free = (domain in COMMON_FREE_DOMAINS)

    if not is_free:
        corp_pts = 5
        corp_detail = "Corporate / Custom business domain"
    else:
        corp_pts = 0
        corp_detail = "Free public webmail provider"

    # Base Score calculation
    base_score = mx_pts + burner_pts + spf_pts + dmarc_pts + role_pts + corp_pts
    score = base_score

    # API Verifier Cross-Examination & Mailbox Probing
    api_signals = []
    mailbox_bounced = False
    mailbox_verified = False
    catch_all_detected = False

    # 1. ZeroBounce check
    zb = api_results.get("zerobounce", {})
    if zb.get("success"):
        status = zb.get("status", "").lower()
        if status == "valid":
            mailbox_verified = True
            api_signals.append("ZeroBounce: Verified deliverable mailbox (status: valid)")
        elif status in ["invalid", "spamtrap", "abuse", "do_not_mail"]:
            mailbox_bounced = True
            api_signals.append(f"ZeroBounce: Undeliverable mailbox rejected (status: {status})")
        elif status in ["catch-all", "unknown"]:
            catch_all_detected = True
            api_signals.append(f"ZeroBounce: Server accept-all / catch-all (status: {status})")

    # 2. AbstractAPI check
    abstract = api_results.get("abstract", {})
    if abstract.get("success"):
        deliv = abstract.get("deliverability", "").upper()
        if deliv == "DELIVERABLE":
            mailbox_verified = True
            api_signals.append("AbstractAPI: Recipient deliverability confirmed (DELIVERABLE)")
        elif deliv == "UNDELIVERABLE":
            mailbox_bounced = True
            api_signals.append("AbstractAPI: Recipient mailbox invalid (UNDELIVERABLE)")
        elif deliv == "RISKY" or abstract.get("is_catchall_email"):
            catch_all_detected = True
            api_signals.append("AbstractAPI: Catch-all mailbox or risky delivery (RISKY)")

    # 3. Hunter.io check
    hunter = api_results.get("hunter", {})
    if hunter.get("success"):
        h_res = hunter.get("result", "").lower()
        if h_res == "deliverable":
            mailbox_verified = True
            api_signals.append("Hunter.io: Server mailbox validated (deliverable)")
        elif h_res == "undeliverable":
            mailbox_bounced = True
            api_signals.append("Hunter.io: Server rejected recipient mailbox (undeliverable)")
        elif h_res == "risky":
            catch_all_detected = True
            api_signals.append("Hunter.io: Risky deliverability / catch-all")

    # 4. Debounce check
    deb = api_results.get("debounce", {})
    if deb.get("success"):
        d_res = deb.get("result", "").lower()
        if "safe to send" in d_res:
            mailbox_verified = True
            api_signals.append("Debounce: Mailbox verified (Safe to Send)")
        elif "invalid" in d_res or "bounce" in d_res:
            mailbox_bounced = True
            api_signals.append("Debounce: Mailbox rejected by server (Invalid)")
        elif "accept-all" in d_res or "risky" in d_res:
            catch_all_detected = True
            api_signals.append("Debounce: Server accept-all / risky")

    # 5. Mailboxlayer check
    mbl = api_results.get("mailboxlayer", {})
    if mbl.get("success"):
        if mbl.get("smtp_check") is True:
            mailbox_verified = True
            api_signals.append("Mailboxlayer: Real-time SMTP route confirmed")
        elif mbl.get("smtp_check") is False:
            mailbox_bounced = True
            api_signals.append("Mailboxlayer: Real-time SMTP route failed")

    # 6. EmailRep check
    er = api_results.get("emailrep", {})
    threat_flag = False
    if er.get("success"):
        if er.get("malicious_activity") or er.get("suspicious"):
            threat_flag = True
            api_signals.append("EmailRep: Suspicious or malicious threat telemetry flagged")

    # Apply Overrides & Adjustments
    if not has_mx:
        score = 0
        verdict = "UNDELIVERABLE"
        risk_level = "CRITICAL (Mail servers offline)"
    elif burner_flag:
        score = min(score, 10)
        verdict = "UNDELIVERABLE"
        risk_level = "HIGH (Disposable burner address)"
    elif mailbox_bounced:
        score = min(score, 15)
        verdict = "UNDELIVERABLE"
        risk_level = "HIGH (Mailbox rejected by server)"
    elif threat_flag:
        score = max(5, min(score - 30, 45))
        verdict = "UNDELIVERABLE"
        risk_level = "HIGH (Malicious/Threat activity reported)"
    elif catch_all_detected:
        score = max(50, min(score, 65))
        verdict = "RISKY"
        risk_level = "MEDIUM (Catch-all domain / unverified recipient)"
    elif mailbox_verified:
        score = max(score, 95)
        score = min(100, score)
        verdict = "DELIVERABLE"
        risk_level = "LOW (Mailbox confirmed deliverable)"
    else:
        score = max(5, min(100, score))
        if score >= 80:
            verdict = "DELIVERABLE"
            risk_level = "LOW (High delivery probability)"
        elif score >= 50:
            verdict = "RISKY"
            risk_level = "MEDIUM (Role account or missing DNS auth)"
        else:
            verdict = "UNDELIVERABLE"
            risk_level = "HIGH (Poor deliverability signals)"

    breakdown = {
        "mx": {"points": mx_pts, "max": 40, "detail": mx_detail, "passed": has_mx},
        "disposable": {"points": burner_pts, "max": 25, "detail": burner_detail, "passed": not burner_flag},
        "spf": {"points": spf_pts, "max": 15, "detail": spf_detail, "passed": has_spf},
        "dmarc": {"points": dmarc_pts, "max": 10, "detail": dmarc_detail, "passed": has_dmarc},
        "role": {"points": role_pts, "max": 5, "detail": role_detail, "passed": not is_role},
        "corporate": {"points": corp_pts, "max": 5, "detail": corp_detail, "passed": not is_free},
    }

    return {
        "email": email,
        "score": score,
        "verdict": verdict,
        "risk_level": risk_level,
        "base_score": base_score,
        "breakdown": breakdown,
        "api_signals": api_signals
    }

def render_scorecard(score_data):
    """
    Renders a visual terminal scorecard with radial/bar gauge, verdict badge,
    and line-item rubric breakdown.
    """
    email = score_data["email"]
    score = score_data["score"]
    verdict = score_data["verdict"]
    risk_level = score_data["risk_level"]
    breakdown = score_data.get("breakdown", {})
    api_signals = score_data.get("api_signals", [])

    if verdict == "DELIVERABLE":
        v_badge = f"{G} DELIVERABLE {w}"
        score_color = g
    elif verdict == "RISKY":
        v_badge = f"{Y} RISKY {w}"
        score_color = y
    else:
        v_badge = f"{R} UNDELIVERABLE {w}"
        score_color = r

    filled = int(round(score / 5))
    try:
        fill_char = "█"
        empty_char = "░"
        (fill_char + empty_char).encode(sys.stdout.encoding or "utf-8")
        gauge = f"{score_color}{fill_char * filled}{w}{empty_char * (20 - filled)}"
    except Exception:
        gauge = f"{score_color}{'#' * filled}{w}{'-' * (20 - filled)}"

    print(w + "\n" + lines)
    print(f"{space}{W}\033[1;30m COMPREHENSIVE DELIVERABILITY SCORECARD {w}")
    print(w + lines)
    print(f"{space}  Target Email       : {y}{email}{w}")
    print(f"{space}  Deliverability     : {v_badge} (Score: {score_color}{score}/100{w})")
    print(f"{space}  Gauge Meter        : [{gauge}] {score_color}{score}%{w}")
    print(f"{space}  Risk Assessment    : {score_color}{risk_level}{w}")
    print()
    print(f"{space}{p}  --- Weighted Rubric Breakdown ---{w}")

    rubric_labels = [
        ("mx", "Mail Exchange (MX)       ", 40),
        ("disposable", "Clean Hygiene (Non-Burner)", 25),
        ("spf", "SPF Authentication       ", 15),
        ("dmarc", "DMARC Alignment          ", 10),
        ("role", "Mailbox Handle (Non-Role)", 5),
        ("corporate", "Domain Type (Corporate)  ", 5),
    ]

    for key, label, max_pts in rubric_labels:
        item = breakdown.get(key, {})
        pts = item.get("points", 0)
        detail = item.get("detail", "")
        pts_str = f"+{pts:<2} / {max_pts}" if pts > 0 else f" 0  / {max_pts}"
        item_color = g if item.get("passed") else (y if pts > 0 else r)
        print(f"{space}  {item_color}[{pts_str}]{w} {label} : {detail}")

    if api_signals:
        print()
        print(f"{space}{p}  --- Commercial Verifiers & Intelligence ---{w}")
        for sig in api_signals:
            print(f"{space}    - {b}[*]{w} {sig}")

    print(w + lines)
    print(f"{space}{B} SUMMARY {w} Final Verdict: {v_badge} with a deliverability index of {score_color}{score}/100{w}.")
    print(w + lines + "\n")

def run_comprehensive_scan(email):
    print(w + lines)
    print(f"{space}{b}[*]{w} Scanning target: {y}{email}{w}")
    print(w + lines)

    if not is_valid_syntax(email):
        print(f"{space}{r}[!] Invalid Email Syntax!{w}")
        return calculate_deliverability_score(email)

    username, domain = email.split("@", 1)

    # 1. DNS & Mail Server Check
    print(f"\n{space}{p}[1] DNS & Mail Server (MX/SPF/DMARC){w}")
    dns_res = DNSInspectorEngine.check_domain_dns(domain)
    if dns_res["has_mx"]:
        print(f"{space}  {g}[+]{w} Active MX Records : {g}Found ({len(dns_res['mx_records'])} servers){w}")
        for mx in dns_res["mx_records"]:
            print(f"{space}      - {mx}")
    else:
        print(f"{space}  {r}[-]{w} Active MX Records : {r}None (Domain cannot receive emails){w}")
    print(f"{space}  {b}[*]{w} SPF Record        : {dns_res['spf']}")
    print(f"{space}  {b}[*]{w} DMARC Record      : {dns_res['dmarc']}")

    # 2. Disposable / Burner Check
    print(f"\n{space}{p}[2] Disposable & Burner Detection{w}")
    is_burner = DisposableBlocklistEngine.is_disposable(domain)
    if is_burner:
        print(f"{space}  {r}[!] Domain Status    : DISPOSABLE / BURNER EMAIL DETECTED!{w}")
    else:
        print(f"{space}  {g}[+]{w} Domain Status    : Clean (Not in 8,700+ burner blocklist)")

    # 3. Disify Free Engine Check
    print(f"\n{space}{p}[3] Disify Verification Engine (Free & Instant){w}")
    disify_res = DisifyEngine.verify(email)
    if disify_res.get("success"):
        print(f"{space}  {g}[+]{w} Format Valid     : {disify_res['format']}")
        print(f"{space}  {g}[+]{w} DNS Active       : {disify_res['dns']}")
        print(f"{space}  {g}[+]{w} Disposable       : {disify_res['disposable']}")
        print(f"{space}  {g}[+]{w} Free Provider    : {disify_res['free_provider']}")
        print(f"{space}  {g}[+]{w} Role Account     : {disify_res['role_account']}")
        print(f"{space}  {g}[+]{w} Whitelisted      : {disify_res['whitelist']}")
    else:
        print(f"{space}  {y}[~]{w} Disify Check     : Skipped ({disify_res.get('error', 'Error')})")

    # 4. OSINT: Gravatar & GitHub
    print(f"\n{space}{p}[4] OSINT Identity & Profile Discovery{w}")
    gravatar = OSINTEngine.check_gravatar(email)
    if gravatar.get("has_gravatar"):
        print(f"{space}  {g}[+]{w} Gravatar Profile : {g}Found!{w}")
        if "display_name" in gravatar:
            print(f"{space}      Display Name  : {gravatar['display_name']}")
        if "location" in gravatar:
            print(f"{space}      Location      : {gravatar['location']}")
        if "avatar_url" in gravatar:
            print(f"{space}      Avatar        : {gravatar['avatar_url']}")
    else:
        print(f"{space}  {b}[*]{w} Gravatar Profile : No public profile found")

    github = OSINTEngine.check_github(email)
    if not github.get("found"):
        github = OSINTEngine.check_github(username)
    if github.get("found"):
        print(f"{space}  {g}[+]{w} GitHub Account   : {g}Found! (@{github['username']}){w}")
        print(f"{space}      Profile       : {github['profile_url']}")
    else:
        print(f"{space}  {b}[*]{w} GitHub Account   : No public account match")

    # 5. Hunter.io Engine
    print(f"\n{space}{p}[5] Hunter.io Deliverability Engine{w}")
    hunter_res = HunterEngine.verify(email)
    if hunter_res.get("success"):
        print(f"{space}  {g}[+]{w} Result           : {hunter_res['result']} (Score: {hunter_res.get('score', 'N/A')})")
        print(f"{space}  {g}[+]{w} SMTP Server Check: {hunter_res['smtp_check']}")
        print(f"{space}  {g}[+]{w} Block Status     : {hunter_res['block']}")
    else:
        print(f"{space}  {y}[~]{w} Hunter.io        : {hunter_res.get('error')}")

    # 6. AbstractAPI Engine
    abstract_res = AbstractAPIEngine.verify(email)
    if abstract_res.get("success"):
        print(f"\n{space}{p}[6] AbstractAPI Verification{w}")
        print(f"{space}  {g}[+]{w} Deliverability   : {abstract_res['deliverability']} (Quality: {abstract_res['quality_score']})")
        print(f"{space}  {g}[+]{w} SMTP Valid       : {abstract_res['is_smtp_valid']}")
        print(f"{space}  {g}[+]{w} Catch-all        : {abstract_res['is_catchall_email']}")

    # 7. ZeroBounce Engine
    zb_res = ZeroBounceEngine.verify(email)
    if zb_res.get("success"):
        print(f"\n{space}{p}[7] ZeroBounce Verification{w}")
        print(f"{space}  {g}[+]{w} Status           : {zb_res['status']} ({zb_res.get('sub_status', '')})")
        print(f"{space}  {g}[+]{w} SMTP Provider    : {zb_res['smtp_provider']}")

    # 8. Debounce Engine
    deb_res = DebounceEngine.verify(email)
    if deb_res.get("success"):
        print(f"\n{space}{p}[8] Debounce Verification{w}")
        print(f"{space}  {g}[+]{w} Result           : {deb_res['result']} ({deb_res.get('reason', '')})")

    # 9. Mailboxlayer Engine
    mbl_res = MailboxlayerEngine.verify(email)
    if mbl_res.get("success"):
        print(f"\n{space}{p}[9] Mailboxlayer Verification{w}")
        print(f"{space}  {g}[+]{w} SMTP Check       : {mbl_res['smtp_check']} (Score: {mbl_res.get('score', 'N/A')})")

    # 10. EmailRep Threat Intelligence
    er_res = EmailRepEngine.verify(email)
    if er_res.get("success"):
        print(f"\n{space}{p}[10] EmailRep Reputation & Threat Intelligence{w}")
        print(f"{space}  {g}[+]{w} Reputation       : {er_res['reputation']}")
        print(f"{space}  {g}[+]{w} Suspicious       : {er_res['suspicious']}")
        print(f"{space}  {g}[+]{w} Leaked in Breach : {er_res['credentials_leaked']}")
        print(f"{space}  {g}[+]{w} Malicious Activity: {er_res['malicious_activity']}")

    # 11. Apollo.io B2B Intelligence & Verification
    apollo_res = ApolloEngine.verify(email)
    if apollo_res.get("success"):
        print(f"\n{space}{p}[11] Apollo.io B2B Intelligence & Verification{w}")
        print(f"{space}  {g}[+]{w} Status           : {apollo_res.get('status')} (Confidence: {apollo_res.get('confidence', 95)}%)")
        if apollo_res.get("name"):
            print(f"{space}  {g}[+]{w} Contact Name     : {apollo_res['name']}")
        if apollo_res.get("title"):
            print(f"{space}  {g}[+]{w} Job Title        : {apollo_res['title']}")
        if apollo_res.get("company"):
            print(f"{space}  {g}[+]{w} Organization     : {apollo_res['company']}")
        if apollo_res.get("linkedin_url"):
            print(f"{space}  {g}[+]{w} LinkedIn Profile : {apollo_res['linkedin_url']}")

    print(w + "\n" + lines)
    print(f"{space}{G} SCAN COMPLETE {w} All available validation engines finished.")
    print(w + lines + "\n")

    api_results = {
        "hunter": hunter_res,
        "abstract": abstract_res,
        "zerobounce": zb_res,
        "debounce": deb_res,
        "mailboxlayer": mbl_res,
        "emailrep": er_res,
        "apollo": apollo_res
    }

    score_data = calculate_deliverability_score(
        email,
        dns_res=dns_res,
        is_burner=is_burner,
        disify_res=disify_res,
        api_results=api_results
    )

    render_scorecard(score_data)
    return score_data
