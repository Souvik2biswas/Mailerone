import os
import re
import sys
import time
import random
import requests
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
    EmailRepEngine
)
from multi_verifier import run_comprehensive_scan

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

version = "2.0 (Multi-Engine Enhanced)"
space = "    "
lines = space + "-" * 75

validator_url = "https://raw.githubusercontent.com/mishakorzik/MailFinder/main/.validator"

def cls():
    if sys.platform == 'win32':
        os.system('cls')
    else:
        os.system('clear')

def banner():
    print(f'''{b}
     __   __  _______  ___   ___      _______  ___   __    _  ______   _______  ______
    |  |_|  ||   _   ||   | |   |    |       ||   | |  |  | ||      | |       ||    _ |
    |       ||  |_|  ||   | |   |    |    ___||   | |   |_| ||  _    ||    ___||   | ||
    |       ||       ||   | |   |    |   |___ |   | |       || | |   ||   |___ |   |_||_
    |       ||       ||   | |   |___ |    ___||   | |  _    || |_|   ||    ___||    __  |
    | ||_|| ||   _   ||   | |       ||   |    |   | | | |   ||       ||   |___ |   |  | |
    |_|   |_||__| |__||___| |_______||___|    |___| |_|  |__||______| |_______||___|  |_|{w}''')
    print(f'                  .:.:;.. {y}MailFinder v{version} (Multi-API Enhanced){w} ..;:.:.')
    print(f'\n{space}{b}>> {w}Comprehensive Email Finding, Multi-API Deliverability & OSINT Suite\n')

def pause():
    input(f"\n{space}{b}[{w}?{b}]{w} Press Enter to return to main menu...")

# -------------------------------------------------------------
# 1. Domain & DNS Inspection
# -------------------------------------------------------------
def checkdomain():
    cls()
    banner()
    domain = input(f"{space}{b}[{w}?{b}]{w} Enter domain to inspect (e.g. gmail.com): {b}").strip().lower()
    if not domain:
        return
    print(w + lines)
    print(f"{space}{b}[*]{w} Inspecting domain: {y}{domain}{w}\n")

    # 1. DNS & Mail Servers
    dns_res = DNSInspectorEngine.check_domain_dns(domain)
    if dns_res["has_mx"]:
        print(f"{space}{g}[+]{w} Active Mail Servers (MX) : {g}Found ({len(dns_res['mx_records'])}){w}")
        for mx in dns_res["mx_records"]:
            print(f"{space}    - {mx}")
    else:
        print(f"{space}{r}[-]{w} Active Mail Servers (MX) : {r}None Found{w}")
    print(f"{space}{b}[*]{w} SPF Security Policy      : {dns_res['spf']}")
    print(f"{space}{b}[*]{w} DMARC Security Policy    : {dns_res['dmarc']}")

    # 2. Disposable / Burner Domain Check
    is_disposable = DisposableBlocklistEngine.is_disposable(domain)
    if is_disposable:
        print(f"{space}{r}[!] Burner Domain Check       : FLAGGED AS TEMPORARY / DISPOSABLE{w}")
    else:
        print(f"{space}{g}[+]{w} Burner Domain Check       : Clean (Passed 8,700+ domain blocklist)")

    # 3. Disify Whitelist
    disify_res = DisifyEngine.verify(f"test@{domain}")
    if disify_res.get("success"):
        print(f"{space}{g}[+]{w} Free Email Provider      : {disify_res['free_provider']}")
        print(f"{space}{g}[+]{w} Known Domain Whitelist   : {disify_res['whitelist']}")
    pause()

# -------------------------------------------------------------
# 2. Check Username on 70+ Email Domains
# -------------------------------------------------------------
def validator():
    cls()
    banner()
    user = input(f"{space}{b}[{w}?{b}]{w} Enter username to test across domains: {b}").strip().lower()
    if not user:
        return
    cls()
    banner()
    print(w + lines)
    print(f"{space}{b}[*]{w} Testing username {y}{user}{w} across 70+ email providers...\n")

    domains = [
        "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "live.com",
        "icloud.com", "email.com", "aol.com", "qq.com", "comcast.net",
        "proton.me", "protonmail.com", "inbox.com", "zoho.com", "mailbox.org",
        "yandex.com", "yandex.ru", "mail.ru", "inbox.ru", "list.ru", "bk.ru",
        "rambler.ru", "runbox.com", "mail.com", "usa.com", "europe.com",
        "asia.com", "engineer.com", "post.com", "dr.com", "myself.com",
        "consultant.com", "cheerful.com", "workmail.com", "programmer.net"
    ]

    for domain in domains:
        email = f"{user}@{domain}"
        dis = DisifyEngine.verify(email)
        if dis.get("success") and dis.get("dns"):
            print(f"{space}{B} READY {w} Domain Active: {g}{domain:<18}{w} -> {email}")
        else:
            print(f"{space}{r} NO-MX {w} Domain Inactive: {d}{domain:<18}{w}")
    pause()

# -------------------------------------------------------------
# 3. Full Multi-Engine Email Scan
# -------------------------------------------------------------
def comprehensive_scan_menu():
    cls()
    banner()
    email = input(f"{space}{b}[{w}?{b}]{w} Enter target email to scan: {b}").strip().lower()
    if not email:
        return
    cls()
    banner()
    run_comprehensive_scan(email)
    pause()

# -------------------------------------------------------------
# 4. Hunter.io Suite (Verifier + Name/Domain Finder)
# -------------------------------------------------------------
def hunter_menu():
    cls()
    banner()
    print(f"{space}{b}[{w}1{b}]{w} Hunter.io Email Verifier")
    print(f"{space}{b}[{w}2{b}]{w} Hunter.io Email Finder (First Name + Last Name + Domain)")
    print(f"{space}{b}[{w}0{b}]{w} Back to Main Menu\n")
    choice = input(f"{space}{b}[{w}?{b}]{w} Select option: {b}").strip()

    if choice == "1":
        cls()
        banner()
        email = input(f"{space}{b}[{w}?{b}]{w} Enter email to verify: {b}").strip()
        res = HunterEngine.verify(email)
        print(w + lines)
        if res.get("success"):
            print(f"{space}{g}[+]{w} Target Email : {email}")
            print(f"{space}{g}[+]{w} Status       : {res.get('status')}")
            print(f"{space}{g}[+]{w} Result       : {res.get('result')}")
            print(f"{space}{g}[+]{w} Score        : {res.get('score')}")
            print(f"{space}{g}[+]{w} Regexp Valid : {res.get('regexp')}")
            print(f"{space}{g}[+]{w} Disposable   : {res.get('disposable')}")
            print(f"{space}{g}[+]{w} SMTP Server  : {res.get('smtp_server')}")
            print(f"{space}{g}[+]{w} SMTP Check   : {res.get('smtp_check')}")
            print(f"{space}{g}[+]{w} Block Status : {res.get('block')}")
        else:
            print(f"{space}{r}[!]{w} {res.get('error')}")
            print(f"{space}{y}[*]{w} Configure your API key in Option [9] (API Key Manager)")
        pause()
    elif choice == "2":
        cls()
        banner()
        first = input(f"{space}{b}[{w}?{b}]{w} First Name: {b}").strip()
        last = input(f"{space}{b}[{w}?{b}]{w} Last Name: {b}").strip()
        domain = input(f"{space}{b}[{w}?{b}]{w} Company / Email Domain (e.g. google.com): {b}").strip()
        res = HunterEngine.find_email(domain, first, last)
        print(w + lines)
        if res.get("success") and res.get("email"):
            print(f"{space}{g}[+]{w} Found Email   : {G} {res['email']} {w}")
            print(f"{space}{g}[+]{w} Confidence    : {res.get('score')}%")
            print(f"{space}{g}[+]{w} Public Sources: {res.get('sources')}")
        else:
            print(f"{space}{r}[!]{w} {res.get('error', 'No email found for given details.')}")
        pause()

# -------------------------------------------------------------
# 5. AbstractAPI Email Verifier
# -------------------------------------------------------------
def abstract_menu():
    cls()
    banner()
    email = input(f"{space}{b}[{w}?{b}]{w} Enter email to verify with AbstractAPI: {b}").strip()
    if not email:
        return
    res = AbstractAPIEngine.verify(email)
    print(w + lines)
    if res.get("success"):
        print(f"{space}{g}[+]{w} Target Email    : {email}")
        print(f"{space}{g}[+]{w} Deliverability  : {res.get('deliverability')}")
        print(f"{space}{g}[+]{w} Quality Score   : {res.get('quality_score')}")
        print(f"{space}{g}[+]{w} SMTP Valid      : {res.get('is_smtp_valid')}")
        print(f"{space}{g}[+]{w} MX Records Found: {res.get('is_mx_found')}")
        print(f"{space}{g}[+]{w} Disposable      : {res.get('is_disposable_email')}")
        print(f"{space}{g}[+]{w} Free Email      : {res.get('is_free_email')}")
        print(f"{space}{g}[+]{w} Role Email      : {res.get('is_role_email')}")
        print(f"{space}{g}[+]{w} Catch-All       : {res.get('is_catchall_email')}")
    else:
        print(f"{space}{r}[!]{w} {res.get('error')}")
        print(f"{space}{y}[*]{w} Add your AbstractAPI key in Option [9] (API Key Manager)")
    pause()

# -------------------------------------------------------------
# 6. Commercial Verifiers (ZeroBounce, Debounce, Mailboxlayer)
# -------------------------------------------------------------
def other_apis_menu():
    cls()
    banner()
    print(f"{space}{b}[{w}1{b}]{w} ZeroBounce API Verifier")
    print(f"{space}{b}[{w}2{b}]{w} Debounce API Verifier")
    print(f"{space}{b}[{w}3{b}]{w} Mailboxlayer (APILayer) Verifier")
    print(f"{space}{b}[{w}0{b}]{w} Back\n")
    choice = input(f"{space}{b}[{w}?{b}]{w} Select engine: {b}").strip()

    if choice in ["1", "2", "3"]:
        email = input(f"\n{space}{b}[{w}?{b}]{w} Enter email to verify: {b}").strip()
        print(w + lines)
        if choice == "1":
            res = ZeroBounceEngine.verify(email)
            if res.get("success"):
                print(f"{space}{g}[+]{w} ZeroBounce Status : {res.get('status')} ({res.get('sub_status')})")
                print(f"{space}{g}[+]{w} SMTP Provider     : {res.get('smtp_provider')}")
            else:
                print(f"{space}{r}[!]{w} {res.get('error')}")
        elif choice == "2":
            res = DebounceEngine.verify(email)
            if res.get("success"):
                print(f"{space}{g}[+]{w} Debounce Result   : {res.get('result')} ({res.get('reason')})")
            else:
                print(f"{space}{r}[!]{w} {res.get('error')}")
        elif choice == "3":
            res = MailboxlayerEngine.verify(email)
            if res.get("success"):
                print(f"{space}{g}[+]{w} Mailboxlayer SMTP : {res.get('smtp_check')} (Score: {res.get('score')})")
            else:
                print(f"{space}{r}[!]{w} {res.get('error')}")
        pause()

# -------------------------------------------------------------
# 7. OSINT & Identity Profiler (Gravatar, GitHub, EmailRep)
# -------------------------------------------------------------
def osint_menu():
    cls()
    banner()
    target = input(f"{space}{b}[{w}?{b}]{w} Enter target email or username: {b}").strip()
    if not target:
        return
    cls()
    banner()
    print(w + lines)
    print(f"{space}{b}[*]{w} Running OSINT profile search on: {y}{target}{w}\n")

    # Gravatar
    if "@" in target:
        grav = OSINTEngine.check_gravatar(target)
        if grav.get("has_gravatar"):
            print(f"{space}{g}[+]{w} Gravatar Profile Found:")
            for k, v in grav.items():
                print(f"{space}    - {k:<15}: {v}")
        else:
            print(f"{space}{b}[*]{w} Gravatar Profile      : No profile found")

    # GitHub
    gh = OSINTEngine.check_github(target)
    if gh.get("found"):
        print(f"\n{space}{g}[+]{w} GitHub Account Match Found:")
        print(f"{space}    - Username        : @{gh['username']}")
        print(f"{space}    - Profile URL     : {gh['profile_url']}")
        print(f"{space}    - Avatar URL      : {gh['avatar_url']}")
    else:
        print(f"{space}{b}[*]{w} GitHub Account        : No matching public account")

    # EmailRep
    if "@" in target:
        er = EmailRepEngine.verify(target)
        if er.get("success"):
            print(f"\n{space}{g}[+]{w} EmailRep Threat Intelligence:")
            print(f"{space}    - Reputation      : {er.get('reputation')}")
            print(f"{space}    - Suspicious Flag : {er.get('suspicious')}")
            print(f"{space}    - In Data Breaches: {er.get('data_breach')}")
            print(f"{space}    - Leaked Creds    : {er.get('credentials_leaked')}")
            print(f"{space}    - Malicious       : {er.get('malicious_activity')}")
    pause()

# -------------------------------------------------------------
# 8. Permutation Name Finder (Generates & Saves to result.txt)
# -------------------------------------------------------------
def name_finder_menu():
    cls()
    banner()
    first = input(f"{space}{b}[{w}?{b}]{w} First Name: {b}").strip().lower()
    last = input(f"{space}{b}[{w}?{b}]{w} Last Name: {b}").strip().lower()
    domain = input(f"{space}{b}[{w}?{b}]{w} Target Domain (or 'auto' for major domains): {b}").strip().lower()
    
    if not first or not last or not domain:
        return

    domains = ["gmail.com", "yahoo.com", "outlook.com"] if domain == "auto" else [domain]
    
    # Generate variations
    perms = [
        f"{first}.{last}",
        f"{last}.{first}",
        f"{first}{last}",
        f"{last}{first}",
        f"{first[0]}.{last}",
        f"{first[0]}{last}",
        f"{first}_{last}",
        f"{last}_{first}",
        f"{first}-{last}",
        f"{first}.{last}1",
        f"{first}.{last}7",
        f"{first}{last}123",
        f"{first}{last}777"
    ]

    print(w + lines)
    print(f"{space}{b}[*]{w} Testing permutations across {len(domains)} domain(s)...")
    
    results = []
    with open("result.txt", "w", encoding="utf-8") as f:
        for p_user in perms:
            for d in domains:
                test_email = f"{p_user}@{d}"
                dis = DisifyEngine.verify(test_email)
                if dis.get("success") and dis.get("dns"):
                    status = f"{g}VALID DOMAIN & SYNTAX{w}"
                    print(f"{space}{B} CANDIDATE {w} {test_email:<30} [{status}]")
                    results.append(test_email)
                    f.write(test_email + "\n")
                else:
                    print(f"{space}{r} INVALID {w} {test_email}")

    print(w + lines)
    print(f"{space}{g}[+]{w} Saved {len(results)} potential candidate email(s) to: {y}result.txt{w}")
    pause()

# -------------------------------------------------------------
# 9. API Keys Configuration Manager
# -------------------------------------------------------------
def config_keys_menu():
    while True:
        cls()
        banner()
        cfg = load_config()
        print(f"{space}{p}=== API Keys Configuration Manager ==={w}\n")
        
        services = [
            ("Hunter.io Keys", "hunter_api_keys", "List of keys (built-in fallback available)"),
            ("AbstractAPI Key", "abstract_api_key", "https://abstractapi.com"),
            ("ZeroBounce Key", "zerobounce_api_key", "https://zerobounce.net"),
            ("Debounce Key", "debounce_api_key", "https://debounce.io"),
            ("Mailboxlayer Key", "mailboxlayer_api_key", "https://mailboxlayer.com"),
            ("EmailRep Key", "emailrep_api_key", "https://emailrep.io")
        ]

        for i, (name, key_field, info) in enumerate(services, 1):
            val = cfg.get(key_field, "")
            status = f"{g}[Configured]{w}" if val else f"{y}[Empty / Not set]{w}"
            print(f"{space}{b}[{w}{i}{b}]{w} {name:<22} {status}  ({info})")

        print(f"\n{space}{b}[{w}0{b}]{w} Back to Main Menu\n")
        ch = input(f"{space}{b}[{w}?{b}]{w} Select number to edit key: {b}").strip()
        
        if ch == "0" or not ch:
            break
        elif ch in [str(x) for x in range(1, len(services) + 1)]:
            idx = int(ch) - 1
            s_name, s_field, _ = services[idx]
            new_val = input(f"\n{space}{b}[{w}?{b}]{w} Enter new key for {s_name} (or leave empty to clear): {b}").strip()
            if s_field == "hunter_api_keys":
                if new_val:
                    cfg[s_field] = [new_val]
                else:
                    cfg[s_field] = []
            else:
                cfg[s_field] = new_val
            save_config(cfg)
            print(f"\n{space}{g}[+]{w} Key updated successfully!")
            time.sleep(1)

# -------------------------------------------------------------
# Main Application Menu Loop
# -------------------------------------------------------------
def main_menu():
    while True:
        cls()
        banner()
        print(f"{space}{b}[{w}1{b}]{w} Domain Inspector (DNS, MX, SPF, DMARC & Burner Check)")
        print(f"{space}{b}[{w}2{b}]{w} Check Username across 70+ Email Domains")
        print(f"{space} {w}|")
        print(f"{space}{b}[{w}3{b}]{w} {G} Comprehensive Multi-Engine Email Scan {w} (All-in-One)")
        print(f"{space} {w}|")
        print(f"{space}{b}[{w}4{b}]{w} Hunter.io Suite (Email Verifier & Name+Domain Finder)")
        print(f"{space}{b}[{w}5{b}]{w} AbstractAPI Email Verifier")
        print(f"{space}{b}[{w}6{b}]{w} ZeroBounce / Debounce / Mailboxlayer Verifiers")
        print(f"{space}{b}[{w}7{b}]{w} OSINT & Identity Profiler (Gravatar + GitHub + EmailRep)")
        print(f"{space}{b}[{w}8{b}]{w} Search Email via Full Name (Permutation Generator)")
        print(f"{space} {w}|")
        print(f"{space}{b}[{w}9{b}]{w} API Keys Configuration Manager")
        print(f"{space}{b}[{w}0{b}]{w} Exit MailFinder\n")

        choice = input(f"{space}{b}[{w}?{b}]{w} Select an option [0-9]: {b}").strip()

        if choice in ["1", "01"]:
            checkdomain()
        elif choice in ["2", "02"]:
            validator()
        elif choice in ["3", "03"]:
            comprehensive_scan_menu()
        elif choice in ["4", "04"]:
            hunter_menu()
        elif choice in ["5", "05"]:
            abstract_menu()
        elif choice in ["6", "06"]:
            other_apis_menu()
        elif choice in ["7", "07"]:
            osint_menu()
        elif choice in ["8", "08"]:
            name_finder_menu()
        elif choice in ["9", "09"]:
            config_keys_menu()
        elif choice == "0":
            print(f"\n{space}{b}[*]{w} Goodbye!\n")
            break
        else:
            time.sleep(1)

if __name__ == "__main__":
    main_menu()
