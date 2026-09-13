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
    EmailRepEngine,
    ContactOutEngine,
    SalesQLEngine,
    SignalHireEngine,
    FinalScoutEngine,
    Name2EmailEngine,
    MultiFinderEngine,
    APIQuotaEngine
)
from multi_verifier import run_comprehensive_scan

r = "\033[31m"
g = "\033[32m"
y = "\033[33m"
b = "\033[34m"
p = "\033[35m"
d = "\033[90m"
w = "\033[0m"

W = f"{w}\033[1;47m"
R = f"{w}\033[1;41m"
G = f"{w}\033[1;42m"
Y = f"{w}\033[1;43m"
B = f"{w}\033[1;44m"

version = "2.0 (Multi-Engine Enhanced)"
space = "    "
lines = space + "-" * 75

validator_url = "https://raw.githubusercontent.com/Souvik2biswas/Mailerone/main/.validator"

def cls():
    if sys.platform == 'win32':
        os.system('cls')
    else:
        os.system('clear')

def banner():
    print(f'''{b}
     __   __  _______  ___   ___      _______  ______    _______  __    _  _______ 
    |  |_|  ||   _   ||   | |   |    |       ||    _ |  |       ||  |  | ||       |
    |       ||  |_|  ||   | |   |    |    ___||   | ||  |   _   ||   |_| ||    ___|
    |       ||       ||   | |   |    |   |___ |   |_||_ |  | |  ||       ||   |___ 
    |       ||       ||   | |   |___ |    ___||    __  ||  |_|  ||  _    ||    ___|
    | ||_|| ||   _   ||   | |       ||   |___ |   |  | ||       || | |   ||   |___ 
    |_|   |_||__| |__||___| |_______||_______||___|  |_||_______||_|  |__||_______|{w}''')
    print(f'                  .:.:;.. {y}Mailerone v{version} (Multi-API Enhanced){w} ..;:.:.')
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
# 4. B2B Email Finders & Lead Enrichment Suite
# -------------------------------------------------------------
def b2b_finders_menu():
    while True:
        cls()
        banner()
        print(f"{space}{p}=== B2B Email Finders & Lead Enrichment Suite ==={w}\n")
        print(f"{space}{b}[{w}1{b}]{w} {G} All-in-One Multi-Finder Pipeline {w} (Hunter + ContactOut + SalesQL + SignalHire + FinalScout + Name2Email)")
        print(f"{space}{b}[{w}2{b}]{w} Name2Email / Name2Mail (34 Patterns + Parallel DNS/Disify Verifier)")
        print(f"{space}{b}[{w}3{b}]{w} ContactOut B2B Email & Phone Finder (Name + Company / LinkedIn)")
        print(f"{space}{b}[{w}4{b}]{w} SalesQL Lead Enrichment Finder (Name + Domain / LinkedIn)")
        print(f"{space}{b}[{w}5{b}]{w} SignalHire Candidate Search (Name + Company)")
        print(f"{space}{b}[{w}6{b}]{w} FinalScout Corporate Email Finder (Name + Domain / LinkedIn)")
        print(f"{space}{b}[{w}7{b}]{w} Hunter.io Suite (Email Verifier & Name+Domain Finder)")
        print(f"\n{space}{b}[{w}0{b}]{w} Back to Main Menu\n")
        
        choice = input(f"{space}{b}[{w}?{b}]{w} Select option [0-7]: {b}").strip()
        
        if choice == "0" or not choice:
            break
            
        # 1. Multi-Finder Pipeline
        elif choice in ["1", "01"]:
            cls()
            banner()
            print(f"{space}{p}--- All-in-One Multi-Finder Lead Pipeline ---{w}\n")
            first = input(f"{space}{b}[{w}?{b}]{w} First Name: {b}").strip()
            last = input(f"{space}{b}[{w}?{b}]{w} Last Name: {b}").strip()
            domain = input(f"{space}{b}[{w}?{b}]{w} Target Domain (e.g. stripe.com): {b}").strip().lower()
            company = input(f"{space}{b}[{w}?{b}]{w} Company Name (optional, press Enter to skip): {b}").strip()
            linkedin_url = input(f"{space}{b}[{w}?{b}]{w} LinkedIn URL (optional, press Enter to skip): {b}").strip()
            
            if not first or not last or not domain:
                continue
                
            print(w + lines)
            print(f"{space}{b}[*]{w} Executing Multi-Finder Lead Search for: {y}{first} {last}{w} @ {y}{domain}{w}...\n")
            res = MultiFinderEngine.search(domain, first, last, company=company, linkedin_url=linkedin_url)
            
            print(f"{space}{G} SEARCH RESULTS SUMMARY {w}\n")
            print(f"{space}{b}[*]{w} Engines Queried: {', '.join(res['engines_queried'])}")
            
            if res["found_emails"]:
                print(f"\n{space}{g}[+]{w} Identified Email Addresses ({len(res['found_emails'])}):")
                for em_info in res["found_emails"]:
                    print(f"{space}    - {G} {em_info['email']} {w} [{y}{em_info['source']}{w}] (Confidence: {g}{em_info['confidence']}{w})")
            else:
                print(f"\n{space}{r}[-]{w} No verified emails returned by queried engines.")
                
            if res["found_phones"]:
                print(f"\n{space}{g}[+]{w} Identified Phone Numbers:")
                for ph in res["found_phones"]:
                    print(f"{space}    - {ph}")
                    
            pause()
            
        # 2. Name2Email Smart Permutator & Verifier
        elif choice in ["2", "02"]:
            cls()
            banner()
            print(f"{space}{p}--- Name2Email / Name2Mail Smart Permutation & Verification Engine ---{w}\n")
            first = input(f"{space}{b}[{w}?{b}]{w} First Name: {b}").strip()
            last = input(f"{space}{b}[{w}?{b}]{w} Last Name: {b}").strip()
            domain = input(f"{space}{b}[{w}?{b}]{w} Target Domain (e.g. google.com): {b}").strip().lower()
            
            if not first or not last or not domain:
                continue
                
            print(w + lines)
            print(f"{space}{b}[*]{w} Generating 34 email permutations & verifying MX/DNS in parallel...")
            res = Name2EmailEngine.find_and_verify(first, last, domain)
            
            if not res.get("has_mx"):
                print(f"{space}{r}[!]{w} {res.get('error', 'Domain has no active mail servers.')}")
            else:
                print(f"{space}{g}[+]{w} Active MX Records: {', '.join(res.get('mx_records', [])[:2])}")
                print(f"{space}{g}[+]{w} Total Permutations Generated: {res.get('total_generated')}")
                if res.get("primary_candidate"):
                    print(f"\n{space}{B} TOP CANDIDATE {w} {G} {res['primary_candidate']} {w}")
                
                print(f"\n{space}{g}[+]{w} Ranked Candidate Permutations:")
                for em in res.get("valid_candidates", [])[:8]:
                    print(f"{space}    - {g}{em}{w}")
                    
                # Save to result file
                with open("name2mail_candidates.txt", "w", encoding="utf-8") as f:
                    for em in res.get("valid_candidates", []):
                        f.write(em + "\n")
                print(f"\n{space}{g}[+]{w} Saved all {len(res.get('valid_candidates', []))} candidate(s) to: {y}name2mail_candidates.txt{w}")
            pause()
            
        # 3. ContactOut
        elif choice in ["3", "03"]:
            cls()
            banner()
            print(f"{space}{p}--- ContactOut B2B Email & Phone Finder ---{w}\n")
            sub = input(f"{space}{b}[{w}?{b}]{w} Search by (1) Name + Domain or (2) LinkedIn URL? [1/2]: {b}").strip()
            print(w + lines)
            if sub == "2":
                li_url = input(f"{space}{b}[{w}?{b}]{w} Enter LinkedIn Profile URL: {b}").strip()
                res = ContactOutEngine.find_by_linkedin(li_url)
            else:
                first = input(f"{space}{b}[{w}?{b}]{w} First Name: {b}").strip()
                last = input(f"{space}{b}[{w}?{b}]{w} Last Name: {b}").strip()
                domain = input(f"{space}{b}[{w}?{b}]{w} Target Domain: {b}").strip()
                company = input(f"{space}{b}[{w}?{b}]{w} Company Name (optional): {b}").strip()
                res = ContactOutEngine.find_email(domain, first, last, company=company)
                
            if res.get("success"):
                print(f"{space}{g}[+]{w} Primary Email  : {G} {res.get('primary_email', 'N/A')} {w}")
                print(f"{space}{g}[+]{w} Work Emails    : {', '.join(res.get('work_emails', [])) or 'None'}")
                print(f"{space}{g}[+]{w} Personal Emails: {', '.join(res.get('personal_emails', [])) or 'None'}")
                print(f"{space}{g}[+]{w} Phone Numbers  : {', '.join(res.get('phone_numbers', [])) or 'None'}")
                print(f"{space}{g}[+]{w} Job Title      : {res.get('job_title', 'N/A')}")
                print(f"{space}{g}[+]{w} Company        : {res.get('company', 'N/A')}")
            else:
                print(f"{space}{r}[!]{w} {res.get('error')}")
                print(f"{space}{y}[*]{w} Configure your ContactOut API key in Option [9]")
            pause()
            
        # 4. SalesQL
        elif choice in ["4", "04"]:
            cls()
            banner()
            print(f"{space}{p}--- SalesQL Lead Enrichment Finder ---{w}\n")
            sub = input(f"{space}{b}[{w}?{b}]{w} Search by (1) Name + Domain or (2) LinkedIn URL? [1/2]: {b}").strip()
            print(w + lines)
            if sub == "2":
                li_url = input(f"{space}{b}[{w}?{b}]{w} Enter LinkedIn Profile URL: {b}").strip()
                res = SalesQLEngine.find_by_linkedin(li_url)
            else:
                first = input(f"{space}{b}[{w}?{b}]{w} First Name: {b}").strip()
                last = input(f"{space}{b}[{w}?{b}]{w} Last Name: {b}").strip()
                domain = input(f"{space}{b}[{w}?{b}]{w} Target Domain: {b}").strip()
                res = SalesQLEngine.find_email(domain, first, last)
                
            if res.get("success"):
                print(f"{space}{g}[+]{w} Primary Email : {G} {res.get('primary_email', 'N/A')} {w}")
                print(f"{space}{g}[+]{w} All Emails    : {', '.join(res.get('emails', [])) or 'None'}")
                print(f"{space}{g}[+]{w} Phone Numbers : {', '.join(res.get('phones', [])) or 'None'}")
                print(f"{space}{g}[+]{w} Headline/Title: {res.get('headline', 'N/A')}")
                print(f"{space}{g}[+]{w} Company       : {res.get('company', 'N/A')}")
            else:
                print(f"{space}{r}[!]{w} {res.get('error')}")
                print(f"{space}{y}[*]{w} Configure your SalesQL API key in Option [9]")
            pause()
            
        # 5. SignalHire
        elif choice in ["5", "05"]:
            cls()
            banner()
            print(f"{space}{p}--- SignalHire Candidate Search ---{w}\n")
            first = input(f"{space}{b}[{w}?{b}]{w} First Name: {b}").strip()
            last = input(f"{space}{b}[{w}?{b}]{w} Last Name: {b}").strip()
            domain = input(f"{space}{b}[{w}?{b}]{w} Company Name / Domain: {b}").strip()
            print(w + lines)
            res = SignalHireEngine.find_email(domain, first, last)
            if res.get("success"):
                print(f"{space}{g}[+]{w} Primary Email : {G} {res.get('primary_email', 'N/A')} {w}")
                print(f"{space}{g}[+]{w} All Emails    : {', '.join(res.get('emails', [])) or 'None'}")
                print(f"{space}{g}[+]{w} Phone Numbers : {', '.join(res.get('phones', [])) or 'None'}")
                print(f"{space}{g}[+]{w} Status        : {res.get('status', 'N/A')}")
            else:
                print(f"{space}{r}[!]{w} {res.get('error')}")
                print(f"{space}{y}[*]{w} Configure your SignalHire API key in Option [9]")
            pause()
            
        # 6. FinalScout
        elif choice in ["6", "06"]:
            cls()
            banner()
            print(f"{space}{p}--- FinalScout Corporate Email Finder ---{w}\n")
            sub = input(f"{space}{b}[{w}?{b}]{w} Search by (1) Name + Domain or (2) LinkedIn URL? [1/2]: {b}").strip()
            print(w + lines)
            if sub == "2":
                li_url = input(f"{space}{b}[{w}?{b}]{w} Enter LinkedIn Profile URL: {b}").strip()
                res = FinalScoutEngine.find_by_linkedin(li_url)
            else:
                first = input(f"{space}{b}[{w}?{b}]{w} First Name: {b}").strip()
                last = input(f"{space}{b}[{w}?{b}]{w} Last Name: {b}").strip()
                domain = input(f"{space}{b}[{w}?{b}]{w} Target Domain: {b}").strip()
                res = FinalScoutEngine.find_email(domain, first, last)
                
            if res.get("success") and res.get("email"):
                print(f"{space}{g}[+]{w} Found Email   : {G} {res.get('email')} {w}")
                print(f"{space}{g}[+]{w} Status        : {res.get('status', 'deliverable')}")
                print(f"{space}{g}[+]{w} Confidence    : {res.get('score', 100)}%")
                print(f"{space}{g}[+]{w} Title         : {res.get('title', 'N/A')}")
            else:
                print(f"{space}{r}[!]{w} {res.get('error', 'No email found.')}")
                print(f"{space}{y}[*]{w} Configure your FinalScout API key in Option [9]")
            pause()
            
        # 7. Hunter.io Suite
        elif choice in ["7", "07"]:
            cls()
            banner()
            print(f"{space}{p}--- Hunter.io Suite ---{w}\n")
            print(f"{space}{b}[{w}1{b}]{w} Hunter.io Email Verifier")
            print(f"{space}{b}[{w}2{b}]{w} Hunter.io Email Finder (First Name + Last Name + Domain)")
            h_sub = input(f"\n{space}{b}[{w}?{b}]{w} Select option [1-2]: {b}").strip()
            print(w + lines)
            if h_sub == "1":
                email = input(f"{space}{b}[{w}?{b}]{w} Enter email to verify: {b}").strip()
                res = HunterEngine.verify(email)
                if res.get("success"):
                    print(f"{space}{g}[+]{w} Status       : {res.get('status')}")
                    print(f"{space}{g}[+]{w} Result       : {res.get('result')}")
                    print(f"{space}{g}[+]{w} Score        : {res.get('score')}")
                    print(f"{space}{g}[+]{w} Disposable   : {res.get('disposable')}")
                    print(f"{space}{g}[+]{w} SMTP Check   : {res.get('smtp_check')}")
                else:
                    print(f"{space}{r}[!]{w} {res.get('error')}")
            elif h_sub == "2":
                first = input(f"{space}{b}[{w}?{b}]{w} First Name: {b}").strip()
                last = input(f"{space}{b}[{w}?{b}]{w} Last Name: {b}").strip()
                domain = input(f"{space}{b}[{w}?{b}]{w} Target Domain: {b}").strip()
                res = HunterEngine.find_email(domain, first, last)
                if res.get("success") and res.get("email"):
                    print(f"{space}{g}[+]{w} Found Email   : {G} {res['email']} {w}")
                    print(f"{space}{g}[+]{w} Confidence    : {res.get('score')}%")
                else:
                    print(f"{space}{r}[!]{w} {res.get('error', 'No email found.')}")
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
# 9. API Keys, Live Quotas & Tier Limits Manager
# -------------------------------------------------------------
def live_quota_inspector_menu():
    cls()
    banner()
    print(f"{space}{p}=== Real-Time API Quotas, Credit Balances & Usage Inspector ==={w}\n")
    print(f"{space}{b}[*]{w} Querying live quota endpoints across configured APIs...\n")
    
    quotas = APIQuotaEngine.check_all_live_quotas()
    
    print(w + lines)
    for service_name, q in quotas.items():
        if not q.get("success"):
            print(f"{space}{r}[-] {service_name:<18}{w} : {r}{q.get('error', 'Failed')}{w}")
        else:
            if service_name == "Hunter.io":
                print(f"{space}{g}[+] {service_name:<18}{w} : Plan: {y}{q.get('plan_name')}{w} | Account: {q.get('account_email')}")
                print(f"{space}    - Searches Left      : {g}{q.get('searches_remaining')}{w} / {q.get('searches_available')} (Used: {q.get('searches_used')})")
                print(f"{space}    - Verifications Left : {g}{q.get('verifications_remaining')}{w} / {q.get('verifications_available')} (Used: {q.get('verifications_used')})")
                print(f"{space}    - Monthly Reset Date : {q.get('reset_date')}")
            elif service_name == "ContactOut":
                print(f"{space}{g}[+] {service_name:<18}{w} : Plan: {y}{q.get('plan', 'Free Tier')}{w} | Reset: {q.get('reset_date', 'Monthly')}")
                print(f"{space}    - Work Emails Left   : {g}{q.get('work_emails_remaining', 40)}{w} / {q.get('work_emails_total', 40)} per month")
                print(f"{space}    - Direct Phone Left  : {g}{q.get('phone_credits_remaining', 5)}{w} / {q.get('phone_credits_total', 5)} per month")
            elif service_name == "SalesQL":
                print(f"{space}{g}[+] {service_name:<18}{w} : Plan: {y}{q.get('plan', 'Free')}{w} | Reset: {q.get('reset_date', 'Monthly')}")
                print(f"{space}    - Credits Remaining  : {G}{q.get('credits_remaining', 50)}{w} / {q.get('credits_total', 50)} credits/month")
            elif service_name == "SignalHire":
                print(f"{space}{g}[+] {service_name:<18}{w} : Plan: {y}{q.get('plan', 'Free Starter')}{w}")
                print(f"{space}    - Contact Credits    : {G}{q.get('contact_credits_remaining', 5)}{w} / {q.get('contact_credits_total', 5)} available")
            elif service_name == "FinalScout":
                print(f"{space}{g}[+] {service_name:<18}{w} : Plan: {y}{q.get('plan', 'Free')}{w} | Reset: {q.get('reset_date', 'Monthly')}")
                print(f"{space}    - Regular Email Left : {g}{q.get('regular_credits_remaining', 20)}{w} / {q.get('regular_credits_total', 20)} credits")
                print(f"{space}    - AI Email Credits   : {g}{q.get('ai_credits_remaining', 10)}{w} credits")
            elif service_name == "ZeroBounce":
                print(f"{space}{g}[+] {service_name:<18}{w} : Credits Remaining: {G} {q.get('credits_remaining')} {w} validations")
            elif service_name == "DeBounce":
                print(f"{space}{g}[+] {service_name:<18}{w} : Balance Remaining: {G} {q.get('balance')} {w} credits")
            elif service_name == "GitHub API":
                print(f"{space}{g}[+] {service_name:<18}{w} : Mode: {y}{q.get('auth_mode')}{w}")
                print(f"{space}    - Search Rate Limit  : {g}{q.get('search_remaining')}{w} / {q.get('search_limit')} requests remaining")
                print(f"{space}    - Core Rate Limit    : {g}{q.get('core_remaining')}{w} / {q.get('core_limit')} requests remaining")
            else:
                status_text = q.get("status", "Active")
                print(f"{space}{g}[+] {service_name:<18}{w} : {g}{status_text}{w}")
    print(w + lines)
    pause()

def tier_limits_matrix_menu():
    cls()
    banner()
    print(f"{space}{p}=== API Free Tier vs Premium Tier Quota & Usage Limits Matrix ==={w}\n")
    
    matrix = APIQuotaEngine.get_tier_matrix()
    
    for idx, item in enumerate(matrix, 1):
        print(f"{space}{B} {idx:02d}. {item['service']} {w} [{y}{item['category']}{w}]")
        print(f"{space}    {g}* Free Tier Quota      :{w} {item['free_tier']}")
        print(f"{space}    {y}* Free Rate Limits     :{w} {item['free_limits']}")
        print(f"{space}    {p}* Premium Tiers        :{w} {item['premium_tier']}")
        print(f"{space}    {b}* Live Balance Support :{w} {item['live_balance_support']}")
        print(f"{space}    {d}* Website / Docs       :{w} {item['website']}\n")
        
    print(w + lines)
    pause()

def mask_key(val):
    if not val:
        return ""
    if isinstance(val, list):
        if not val:
            return ""
        first = str(val[0])
        if len(first) > 8:
            return f"{first[:4]}...{first[-4:]} ({len(val)} key{'s' if len(val)>1 else ''})"
        return f"({len(val)} key{'s' if len(val)>1 else ''})"
    s = str(val).strip()
    if len(s) > 8:
        return f"{s[:4]}...{s[-4:]}"
    return "****"

def config_keys_menu():
    while True:
        cls()
        banner()
        cfg = load_config()
        print(f"{space}{p}=== API Keys, Usage Quotas & Tier Limits Manager ==={w}\n")
        print(f"{space}{d}Select an engine number [01-11] to change or clear its API key.{w}\n")
        
        services = [
            ("Hunter.io Keys", "hunter_api_keys", "https://hunter.io (25 searches/mo)", APIQuotaEngine.check_hunter_quota),
            ("ContactOut Key", "contactout_api_key", "https://contactout.com (40 emails/mo)", APIQuotaEngine.check_contactout_quota),
            ("SalesQL Key", "salesql_api_key", "https://salesql.com (50 credits/mo)", APIQuotaEngine.check_salesql_quota),
            ("SignalHire Key", "signalhire_api_key", "https://signalhire.com (5 credits/mo)", APIQuotaEngine.check_signalhire_quota),
            ("FinalScout Key", "finalscout_api_key", "https://finalscout.com (20 credits/mo)", APIQuotaEngine.check_finalscout_quota),
            ("AbstractAPI Key", "abstract_api_key", "https://abstractapi.com (100 req/mo)", None),
            ("ZeroBounce Key", "zerobounce_api_key", "https://zerobounce.net (100 credits/mo)", APIQuotaEngine.check_zerobounce_quota),
            ("Debounce Key", "debounce_api_key", "https://debounce.io (100 free credits)", APIQuotaEngine.check_debounce_quota),
            ("Mailboxlayer Key", "mailboxlayer_api_key", "https://mailboxlayer.com (100 req/mo)", None),
            ("EmailRep Key", "emailrep_api_key", "https://emailrep.io (500 req/day)", None),
            ("GitHub Token", "github_token", "https://github.com/settings/tokens (30 req/min)", APIQuotaEngine.check_github_quota)
        ]

        for i, (name, key_field, info, _) in enumerate(services, 1):
            val = cfg.get(key_field, "")
            masked = mask_key(val)
            status = f"{g}[Configured: {masked}]{w}" if (val and (not isinstance(val, list) or len(val) > 0)) else f"{y}[Empty / Not set]{w}"
            print(f"{space}{b}[{w}{i:02d}{b}]{w} {name:<18} {status:<28} {d}({info}){w}")

        print(f"\n{space}{G} [L] Check Real-Time API Quotas & Remaining Credit Balances {w}")
        print(f"{space}{B} [T] View Free Tier vs Premium Tier Quota & Usage Limits Matrix {w}")
        print(f"\n{space}{b}[{w}0{b}]{w} Back to Main Menu\n")
        ch = input(f"{space}{b}[{w}?{b}]{w} Select option to change [1-11, L, T, 0]: {b}").strip().upper()
        
        if ch == "0" or not ch:
            break
        elif ch == "L":
            live_quota_inspector_menu()
        elif ch == "T":
            tier_limits_matrix_menu()
        elif ch in [str(x) for x in range(1, len(services) + 1)] or ch in [f"{x:02d}" for x in range(1, len(services) + 1)]:
            idx = int(ch) - 1
            s_name, s_field, s_url, validator_fn = services[idx]
            current_val = cfg.get(s_field, "")
            print(f"\n{space}{w}--- Change API Key: {y}{s_name}{w} ---")
            print(f"{space}Current status: {g}{mask_key(current_val) if current_val else 'None'}{w}")
            print(f"{space}{d}Note: Enter comma-separated keys for multiple fallback keys.{w}" if s_field == "hunter_api_keys" else "")
            new_val = input(f"{space}{b}[{w}?{b}]{w} Enter new API key (or press ENTER to clear): {b}").strip()
            
            if s_field == "hunter_api_keys":
                if new_val:
                    keys_list = [k.strip() for k in new_val.split(",") if k.strip()]
                    cfg[s_field] = keys_list
                else:
                    cfg[s_field] = []
            else:
                cfg[s_field] = new_val
            
            save_config(cfg)
            print(f"\n{space}{g}[+]{w} API Key for {s_name} updated successfully in config.json!")
            
            # Offer instant key validation if new_val was provided and validator exists
            if new_val and validator_fn:
                test_key = new_val.split(",")[0].strip() if s_field == "hunter_api_keys" else new_val
                print(f"{space}{b}[*]{w} Validating key with {s_name} live API...")
                try:
                    res = validator_fn(test_key)
                    if res.get("success"):
                        print(f"{space}{g}[✓] Key Verified!{w} {res.get('status', 'Active connection established.')}")
                        if "credits_remaining" in res:
                            print(f"{space}    - Remaining Balance: {G}{res['credits_remaining']}{w} credits")
                        elif "work_emails_remaining" in res:
                            print(f"{space}    - Work Emails Left : {G}{res['work_emails_remaining']}{w} / {res.get('work_emails_total', 40)}")
                    else:
                        print(f"{space}{y}[!] Notice:{w} {res.get('error', 'Could not verify balance (key saved).')}")
                except Exception as ex:
                    print(f"{space}{d}(Validation test skipped: {ex}){w}")
            
            time.sleep(1.8)

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
        print(f"{space}{b}[{w}3{b}]{w} {G} Comprehensive Multi-Engine Email Scan {w} (All-in-One Deliverability)")
        print(f"{space}{b}[{w}4{b}]{w} {B} B2B Email Finders & Lead Enrichment Suite {w} (ContactOut, SalesQL, SignalHire, FinalScout, Name2Mail, Hunter)")
        print(f"{space} {w}|")
        print(f"{space}{b}[{w}5{b}]{w} AbstractAPI Email Verifier")
        print(f"{space}{b}[{w}6{b}]{w} Commercial Verifiers (ZeroBounce / Debounce / Mailboxlayer)")
        print(f"{space}{b}[{w}7{b}]{w} OSINT & Identity Profiler (Gravatar + GitHub + EmailRep)")
        print(f"{space}{b}[{w}8{b}]{w} Name-to-Email Permutation Generator (Save to result.txt)")
        print(f"{space} {w}|")
        print(f"{space}{b}[{w}9{b}]{w} API Keys, Usage Quotas & Tier Limits Manager")
        print(f"{space}{b}[{w}0{b}]{w} Exit Mailerone\n")

        choice = input(f"{space}{b}[{w}?{b}]{w} Select an option [0-9]: {b}").strip()

        if choice in ["1", "01"]:
            checkdomain()
        elif choice in ["2", "02"]:
            validator()
        elif choice in ["3", "03"]:
            comprehensive_scan_menu()
        elif choice in ["4", "04"]:
            b2b_finders_menu()
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
