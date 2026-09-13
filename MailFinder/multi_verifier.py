import re
import sys
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

def is_valid_syntax(email):
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))

def run_comprehensive_scan(email):
    print(w + lines)
    print(f"{space}{b}[*]{w} Scanning target: {y}{email}{w}")
    print(w + lines)

    if not is_valid_syntax(email):
        print(f"{space}{r}[!] Invalid Email Syntax!{w}")
        return

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

    print(w + "\n" + lines)
    print(f"{space}{G} SCAN COMPLETE {w} All available validation engines finished.")
    print(w + lines + "\n")
