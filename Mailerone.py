import os
import re
import sys
import time
import random
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from config_manager import (
    load_config,
    save_config,
    get_api_key,
    get_api_keys,
    set_api_key,
    set_api_keys,
    add_api_key,
    remove_api_key
)
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
    EmailRepEngine,
    ContactOutEngine,
    SalesQLEngine,
    SignalHireEngine,
    FinalScoutEngine,
    Name2EmailEngine,
    MultiFinderEngine,
    APIQuotaEngine,
    AIScraperEngine
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
# 2. Webmail Address Matrix Across 75+ Global Providers
# -------------------------------------------------------------
GLOBAL_ESP_REGISTRY = [
    # Global Webmail Leaders
    ("gmail.com", "Google Workspace / Gmail", "Global"),
    ("yahoo.com", "Yahoo Mail", "Global"),
    ("outlook.com", "Microsoft Outlook", "Global"),
    ("hotmail.com", "Microsoft Hotmail", "Global"),
    ("live.com", "Microsoft Live", "Global"),
    ("icloud.com", "Apple iCloud", "Global"),
    ("aol.com", "AOL Mail", "Global"),
    ("zoho.com", "Zoho Mail", "Global"),
    ("proton.me", "Proton Mail", "Global / Privacy"),
    ("protonmail.com", "Proton Mail (Legacy)", "Global / Privacy"),
    ("mail.com", "Mail.com", "Global"),
    ("gmx.com", "GMX Mail International", "Global"),
    ("gmx.net", "GMX Mail Germany", "Europe"),
    ("web.de", "1&1 WEB.DE", "Europe"),
    ("tuta.com", "Tuta Mail (Tutanota)", "Global / Privacy"),
    ("tutanota.com", "Tutanota Legacy", "Global / Privacy"),
    ("fastmail.com", "Fastmail", "Global / Privacy"),
    ("mailbox.org", "Mailbox.org", "Europe / Privacy"),
    ("posteo.de", "Posteo", "Europe / Privacy"),
    ("runbox.com", "Runbox", "Europe / Privacy"),
    ("startmail.com", "StartMail", "Europe / Privacy"),

    # European Regional Providers
    ("yandex.com", "Yandex Mail Global", "Global / CIS"),
    ("yandex.ru", "Yandex Mail Russia", "Europe / CIS"),
    ("ya.ru", "Yandex Short", "Europe / CIS"),
    ("mail.ru", "VK Mail.ru", "Europe / CIS"),
    ("inbox.ru", "VK Inbox.ru", "Europe / CIS"),
    ("list.ru", "VK List.ru", "Europe / CIS"),
    ("bk.ru", "VK BK.ru", "Europe / CIS"),
    ("rambler.ru", "Rambler Mail", "Europe / CIS"),
    ("orange.fr", "Orange France", "Europe"),
    ("wanadoo.fr", "Wanadoo France", "Europe"),
    ("free.fr", "Free France", "Europe"),
    ("sfr.fr", "SFR France", "Europe"),
    ("laposte.net", "La Poste France", "Europe"),
    ("t-online.de", "Deutsche Telekom", "Europe"),
    ("freenet.de", "Freenet Germany", "Europe"),
    ("arcor.de", "Vodafone Arcor", "Europe"),
    ("libero.it", "Libero Mail Italy", "Europe"),
    ("virgilio.it", "Virgilio Mail Italy", "Europe"),
    ("tim.it", "TIM Telecom Italia", "Europe"),
    ("alice.it", "Alice Italy", "Europe"),
    ("btinternet.com", "BT Internet UK", "Europe"),
    ("virginmedia.com", "Virgin Media UK", "Europe"),
    ("sky.com", "Sky UK", "Europe"),

    # North American Telcos & ISPs
    ("comcast.net", "Xfinity / Comcast", "North America"),
    ("sbcglobal.net", "AT&T / SBCGlobal", "North America"),
    ("att.net", "AT&T Mail", "North America"),
    ("verizon.net", "Verizon Mail", "North America"),
    ("cox.net", "Cox Communications", "North America"),
    ("charter.net", "Spectrum / Charter", "North America"),
    ("bell.net", "Bell Canada", "North America"),
    ("rogers.com", "Rogers Canada", "North America"),
    ("shaw.ca", "Shaw Canada", "North America"),

    # Asia-Pacific Giants
    ("qq.com", "Tencent QQ Mail", "Asia-Pacific"),
    ("163.com", "NetEase 163 Mail", "Asia-Pacific"),
    ("126.com", "NetEase 126 Mail", "Asia-Pacific"),
    ("sina.com", "Sina Weibo Mail", "Asia-Pacific"),
    ("aliyun.com", "Alibaba Aliyun", "Asia-Pacific"),
    ("naver.com", "Naver Mail Korea", "Asia-Pacific"),
    ("daum.net", "Kakao Daum Korea", "Asia-Pacific"),
    ("hanmail.net", "Kakao Hanmail Korea", "Asia-Pacific"),
    ("rediffmail.com", "Rediffmail India", "Asia-Pacific"),
    ("yahoo.co.jp", "Yahoo Japan", "Asia-Pacific"),

    # Professional & Specialty Vanity ESPs
    ("email.com", "Email.com", "Specialty"),
    ("usa.com", "USA.com", "Specialty"),
    ("europe.com", "Europe.com", "Specialty"),
    ("asia.com", "Asia.com", "Specialty"),
    ("engineer.com", "Engineer.com", "Specialty"),
    ("post.com", "Post.com", "Specialty"),
    ("dr.com", "Doctor.com Vanity", "Specialty"),
    ("myself.com", "Myself.com", "Specialty"),
    ("consultant.com", "Consultant.com", "Specialty"),
    ("cheerful.com", "Cheerful.com", "Specialty"),
    ("workmail.com", "WorkMail", "Specialty"),
    ("programmer.net", "Programmer.net", "Specialty"),
    ("techie.com", "Techie.com", "Specialty"),
    ("iname.com", "IName Vanity", "Specialty")
]

def validator():
    cls()
    banner()
    user = input(f"{space}{b}[{w}?{b}]{w} Enter username handle to test across providers: {b}").strip().lower()
    if not user:
        return
    # Strip any trailing @domain if user accidentally typed it
    if "@" in user:
        user = user.split("@")[0].strip()
        
    cls()
    banner()
    print(w + lines)
    print(f"{space}{b}[*]{w} Generating webmail candidate matrix for {y}{user}{w} across {len(GLOBAL_ESP_REGISTRY)} global providers...")
    print(f"{space}{b}[*]{w} Resolving mail server (MX) infrastructure in parallel via DNS-over-HTTPS...\n")

    def _probe_provider(item):
        domain, provider_name, region = item
        candidate_email = f"{user}@{domain}"
        mx_records = DNSInspectorEngine.query_doh(domain, "MX")
        has_mx = len(mx_records) > 0
        return {
            "domain": domain,
            "provider": provider_name,
            "region": region,
            "email": candidate_email,
            "has_mx": has_mx,
            "mx_count": len(mx_records)
        }

    t0 = time.time()
    results = []
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = {executor.submit(_probe_provider, item): item for item in GLOBAL_ESP_REGISTRY}
        for fut in as_completed(futures):
            try:
                results.append(fut.result())
            except Exception:
                pass
    t1 = time.time()

    # Sort results by region, then provider name
    results.sort(key=lambda x: (x["region"], x["provider"]))

    # Group and display by region
    current_region = None
    for r_item in results:
        if r_item["region"] != current_region:
            current_region = r_item["region"]
            print(f"\n{space}{p}--- {current_region} Providers ---{w}")
            
        if r_item["has_mx"]:
            status_tag = f"{G} MX-ACTIVE {w}"
            print(f"{space}{status_tag} {g}{r_item['domain']:<18}{w} | {r_item['provider']:<26} -> {y}{r_item['email']}{w}")
        else:
            status_tag = f"{R}  NO-MX   {w}"
            print(f"{space}{status_tag} {d}{r_item['domain']:<18}{w} | {r_item['provider']:<26} -> {d}Mail servers offline{w}")

    active_count = sum(1 for x in results if x["has_mx"])
    print(f"\n" + lines)
    print(f"{space}{G} INFRASTRUCTURE SWEEP COMPLETE {w} {active_count}/{len(results)} Provider Domains Active ({t1-t0:.2f}s)")
    print(w + lines)
    print(f"{space}{y}[!] INFRASTRUCTURE NOTICE:{w}")
    print(f"{space}    [MX-ACTIVE] confirms the mail servers for this provider are online and accepting email.")
    print(f"{space}    It does {r}NOT{w} verify that {y}{user}{w} has registered this specific mailbox on the provider.")
    print(f"{space}    To verify actual recipient mailbox existence, choose a deep scan option below.")
    print(w + lines + "\n")

    while True:
        print(f"{space}{b}[{w}1{b}]{w} ⚡ Run Deep Deliverability Scan on a Candidate Address (SMTP + Multi-API)")
        print(f"{space}{b}[{w}2{b}]{w} 🕵️ Check OSINT Registrations for '{user}' on GitHub & Gravatar")
        print(f"{space}{b}[{w}3{b}]{w} 💾 Export All {len(results)} Generated Addresses to 'result.txt'")
        print(f"{space}{b}[{w}0{b}]{w} Return to Main Menu\n")
        
        sub_choice = input(f"{space}{b}[{w}?{b}]{w} Select action [0-3]: {b}").strip()
        
        if sub_choice == "1":
            target_addr = input(f"{space}{b}[{w}?{b}]{w} Enter candidate email to deep scan (or press Enter for {user}@gmail.com): {b}").strip()
            if not target_addr:
                target_addr = f"{user}@gmail.com"
            print()
            run_comprehensive_scan(target_addr)
            print()
        elif sub_choice == "2":
            print(f"\n{space}{p}--- OSINT Identity Search for Handle: {user} ---{w}")
            gh = OSINTEngine.check_github(user)
            if gh.get("found"):
                print(f"{space}{g}[+]{w} GitHub Account : {G} FOUND {w} (@{gh.get('username')})")
                print(f"{space}    Profile URL    : {gh.get('profile_url')}")
            else:
                print(f"{space}{d}[-]{w} GitHub Account : Not found under exact username")
                
            grav = OSINTEngine.check_gravatar(f"{user}@gmail.com")
            if grav.get("has_gravatar"):
                print(f"{space}{g}[+]{w} Gravatar Link  : {G} FOUND {w} ({grav.get('avatar_url')})")
            else:
                print(f"{space}{d}[-]{w} Gravatar Link  : No public profile on primary address")
            print()
        elif sub_choice == "3":
            try:
                with open("result.txt", "w", encoding="utf-8") as f:
                    f.write(f"# Mailerone Webmail Matrix for handle: {user}\n")
                    f.write(f"# Generated {len(results)} candidate addresses across global ESPs\n\n")
                    for item in results:
                        f.write(f"{item['email']}\n")
                print(f"\n{space}{g}[+]{w} Successfully exported {len(results)} email addresses to {y}result.txt{w}!\n")
            except Exception as e:
                print(f"\n{space}{r}[!] Failed to export result.txt: {e}{w}\n")
        elif sub_choice in ["0", ""]:
            break
        else:
            print(f"{space}{r}Invalid selection.{w}")

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
        print(f"{space}{b}[{w}1{b}]{w} {G} All-in-One Multi-Finder Pipeline {w} (Apollo + Hunter + ContactOut + SalesQL + SignalHire + FinalScout + Name2Email)")
        print(f"{space}{b}[{w}2{b}]{w} Name2Email / Name2Mail (34 Patterns + Parallel DNS/Disify Verifier)")
        print(f"{space}{b}[{w}3{b}]{w} Apollo.io B2B Lead Match & Email Finder (Name + Domain / LinkedIn)")
        print(f"{space}{b}[{w}4{b}]{w} ContactOut B2B Email & Phone Finder (Name + Company / LinkedIn)")
        print(f"{space}{b}[{w}5{b}]{w} SalesQL Lead Enrichment Finder (Name + Domain / LinkedIn)")
        print(f"{space}{b}[{w}6{b}]{w} SignalHire Candidate Search (Name + Company)")
        print(f"{space}{b}[{w}7{b}]{w} FinalScout Corporate Email Finder (Name + Domain / LinkedIn)")
        print(f"{space}{b}[{w}8{b}]{w} Hunter.io Suite (Email Verifier & Name+Domain Finder)")
        print(f"\n{space}{b}[{w}0{b}]{w} Back to Main Menu\n")
        
        choice = input(f"{space}{b}[{w}?{b}]{w} Select option [0-8]: {b}").strip()
        
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
            
        # 3. Apollo.io B2B Lead Match & Email Finder
        elif choice in ["3", "03"]:
            cls()
            banner()
            print(f"{space}{p}--- Apollo.io B2B Lead Match & Email Finder ---{w}\n")
            sub = input(f"{space}{b}[{w}?{b}]{w} Search by (1) Name + Domain or (2) LinkedIn URL? [1/2]: {b}").strip()
            print(w + lines)
            if sub == "2":
                li_url = input(f"{space}{b}[{w}?{b}]{w} Enter LinkedIn Profile URL: {b}").strip()
                res = ApolloEngine.find_by_linkedin(li_url)
            else:
                first = input(f"{space}{b}[{w}?{b}]{w} First Name: {b}").strip()
                last = input(f"{space}{b}[{w}?{b}]{w} Last Name: {b}").strip()
                domain = input(f"{space}{b}[{w}?{b}]{w} Target Domain (e.g. stripe.com): {b}").strip()
                company = input(f"{space}{b}[{w}?{b}]{w} Company Name (optional, press Enter to skip): {b}").strip()
                res = ApolloEngine.find_email(domain, first, last, company=company)
                
            if res.get("success"):
                print(f"{space}{g}[+]{w} Primary Email  : {G} {res.get('primary_email', 'N/A')} {w}")
                if res.get("personal_emails"):
                    print(f"{space}{g}[+]{w} Personal Emails: {', '.join(res.get('personal_emails', []))}")
                if res.get("phone_numbers"):
                    print(f"{space}{g}[+]{w} Phone Numbers  : {', '.join(res.get('phone_numbers', []))}")
                print(f"{space}{g}[+]{w} Status / Score : {res.get('status', 'verified')} (Confidence: {res.get('score', 95)}%)")
                print(f"{space}{g}[+]{w} Job Title      : {res.get('title', 'N/A')}")
                print(f"{space}{g}[+]{w} Company        : {res.get('company', 'N/A')}")
                if res.get("linkedin_url"):
                    print(f"{space}{g}[+]{w} LinkedIn URL   : {res.get('linkedin_url')}")
                if res.get("seniority"):
                    print(f"{space}{g}[+]{w} Seniority      : {res.get('seniority')}")
                loc_parts = [p for p in [res.get('city'), res.get('state'), res.get('country')] if p]
                if loc_parts:
                    print(f"{space}{g}[+]{w} Location       : {', '.join(loc_parts)}")
            else:
                print(f"{space}{r}[!]{w} {res.get('error')}")
                print(f"{space}{y}[*]{w} Configure your Apollo.io API key in Option [9]")
            pause()

        # 4. ContactOut
        elif choice in ["4", "04"]:
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
            
        # 5. SalesQL
        elif choice in ["5", "05"]:
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
            
        # 6. SignalHire
        elif choice in ["6", "06"]:
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
            
        # 7. FinalScout
        elif choice in ["7", "07"]:
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
            
        # 8. Hunter.io Suite
        elif choice in ["8", "08"]:
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
# 8. AI-Powered Web Scraper & Contact Harvester
# -------------------------------------------------------------
def ai_scraper_menu():
    while True:
        cls()
        banner()
        print(f"{space}{p}=== AI Web Scraper & Corporate Contact Harvester ==={w}\n")
        print(f"{space}{d}Automatically crawls target websites, de-cloaks obfuscated emails, extracts{w}")
        print(f"{space}{d}phone numbers, maps social media profiles, and structures leadership with AI.{w}\n")

        target = input(f"{space}{b}[{w}?{b}]{w} Enter Website URL or Domain (e.g. stripe.com) [0=Back]: {b}").strip()
        if not target or target == "0":
            break

        print(f"\n{space}{b}[*]{w} Select Crawling Depth & Strategy:")
        print(f"{space}  [1] Smart Route Discovery (Home, About, Team, Contact, Legal/Impressum) [Recommended]")
        print(f"{space}  [2] Deep Recursive Crawl (Discovers up to 15 internal contact pages)")
        print(f"{space}  [3] Single Landing Page Only")
        depth_ch = input(f"{space}{b}[{w}?{b}]{w} Choice [1-3, default=1]: {b}").strip()
        max_pages = 15 if depth_ch == "2" else (1 if depth_ch == "3" else 8)

        print(f"\n{space}{b}[*]{w} Select AI Intelligence Engine:")
        print(f"{space}  [1] Auto-Detect Best Engine (Uses configured OpenAI/Gemini/Groq/Anthropic, or Local Heuristic)")
        print(f"{space}  [2] Local Smart Heuristic NLP (Built-in, 100% Free, Instant)")
        print(f"{space}  [3] OpenAI (GPT-4o-mini)")
        print(f"{space}  [4] Google Gemini (3.8 Flash / 3.5 Lite)")
        print(f"{space}  [5] Groq (High-Speed LLM)")
        print(f"{space}  [6] Anthropic Claude (3.5 Haiku)")
        ai_ch = input(f"{space}{b}[{w}?{b}]{w} Choice [1-6, default=1]: {b}").strip()
        ai_provider_map = {"1": "auto", "2": "heuristic", "3": "openai", "4": "gemini", "5": "groq", "6": "anthropic"}
        ai_mode = ai_provider_map.get(ai_ch, "auto")

        print(w + lines)
        print(f"{space}{b}[*]{w} Launching AI Web Scraper on: {y}{target}{w}")
        print(f"{space}{b}[*]{w} Crawling key discovery routes (Max: {max_pages} pages)...")

        t0 = time.time()
        dossier = AIScraperEngine.harvest(target, max_pages=max_pages, ai_provider=ai_mode)
        dur = round(time.time() - t0, 2)

        if not dossier.get("success"):
            print(f"\n{space}{r}[!] Harvester Failed:{w} {dossier.get('error')}")
            pause()
            continue

        base_dom = dossier.get("base_domain", target)
        print(f"\n{space}{G} HARVEST COMPLETE {w} ({dur}s | {dossier.get('pages_analyzed', 1)} pages analyzed | Engine: {y}{dossier.get('ai_engine')}{w})")
        print(w + lines)

        # 1. Company Overview
        cname = AIScraperEngine.sanitize_console_text(dossier.get('company_name', 'N/A'))
        summary = AIScraperEngine.sanitize_console_text(dossier.get('summary', 'N/A'))
        industry = AIScraperEngine.sanitize_console_text(dossier.get('industry', 'Unknown'))
        print(f"{space}{p}[1] Company Profile & Intelligence:{w}")
        print(f"{space}    - Entity Name   : {w}{cname}")
        print(f"{space}    - Target Domain : {w}{base_dom}")
        print(f"{space}    - Summary       : {d}{summary}{w}")
        if industry and industry != "Unknown":
            print(f"{space}    - Inferred Ind. : {w}{industry}")
        if dossier.get("headquarters"):
            for hq in dossier["headquarters"]:
                safe_hq = AIScraperEngine.sanitize_console_text(hq)
                print(f"{space}    - Headquarters  : {y}{safe_hq}{w}")

        # 2. Extracted Emails
        emails = dossier.get("emails", [])
        print(f"\n{space}{p}[2] Extracted Emails ({len(emails)} Found):{w}")
        if emails:
            for em in emails:
                cat = em["category"]
                color_tag = g if "Executive" in cat else (b if "Role" in cat else d)
                badge = "[EXEC]" if "Executive" in cat else ("[ROLE]" if "Role" in cat else "[EXT]")
                print(f"{space}    {color_tag}{badge:<7}{w} {em['email']:<32} {d}({em['role_label']}) - src: {em['source']}{w}")
        else:
            print(f"{space}    {d}No direct public emails exposed on crawled pages.{w}")

        # 3. Extracted Phone Numbers
        phones = dossier.get("phones", [])
        print(f"\n{space}{p}[3] Extracted Phone Numbers ({len(phones)} Found):{w}")
        if phones:
            for ph in phones:
                print(f"{space}    {g}[TEL]{w} {ph['number']:<22} {d}({ph.get('label', 'Office')}){w}")
        else:
            print(f"{space}    {d}No phone numbers detected.{w}")

        # 4. Social Accounts
        socials = dossier.get("social_accounts", {})
        total_socials = sum(len(v) for v in socials.values())
        print(f"\n{space}{p}[4] Discovered Social Accounts & Profiles ({total_socials} Found):{w}")
        if socials.get("linkedin_company"):
            for li in socials["linkedin_company"]:
                print(f"{space}    {b}[LinkedIn Company]{w} {li['url']}")
        if socials.get("linkedin_personal"):
            for li in socials["linkedin_personal"]:
                print(f"{space}    {g}[LinkedIn Profile]{w} {li['url']} {d}(@{li['handle']}){w}")
        if socials.get("twitter_x"):
            for tw in socials["twitter_x"]:
                print(f"{space}    {b}[Twitter / X]{w}     {tw['handle']} -> {tw['url']}")
        if socials.get("github"):
            for gh in socials["github"]:
                print(f"{space}    {w}[GitHub]{w}          @{gh['handle']} -> {gh['url']}")
        if socials.get("youtube"):
            for yt in socials["youtube"]:
                print(f"{space}    {r}[YouTube]{w}         {yt['url']}")
        if socials.get("facebook"):
            for fb in socials["facebook"]:
                print(f"{space}    {b}[Facebook]{w}        {fb['url']}")
        if socials.get("instagram"):
            for ig in socials["instagram"]:
                print(f"{space}    {p}[Instagram]{w}       {ig['handle']} -> {ig['url']}")
        if socials.get("discord"):
            for dc in socials["discord"]:
                print(f"{space}    {b}[Discord]{w}         {dc['url']}")
        if socials.get("telegram"):
            for tg in socials["telegram"]:
                print(f"{space}    {b}[Telegram]{w}        {tg['handle']} -> {tg['url']}")
        if total_socials == 0:
            print(f"{space}    {d}No public social profiles linked in page markup.{w}")

        # 5. Detected Team / Leadership
        team = dossier.get("team_leadership", [])
        if team:
            print(f"\n{space}{p}[5] Detected Leadership & Team Members ({len(team)} Identified):{w}")
            for tm in team:
                em_tag = f"<{tm['email']}>" if tm.get("email") else "(No direct email)"
                li_tag = f"| LI: {tm['linkedin']}" if tm.get("linkedin") else ""
                safe_name = AIScraperEngine.sanitize_console_text(tm.get('name', ''))
                safe_title = AIScraperEngine.sanitize_console_text(tm.get('title', ''))
                print(f"{space}    {g}• {safe_name}{w} - {d}{safe_title}{w} {em_tag} {li_tag}")

        # Actions Menu
        print(f"\n{space}{w}--- Actions ---")
        print(f"{space}{b}[{w}1{b}]{w} Export Complete Dossier to contacts_{base_dom}.json")
        print(f"{space}{b}[{w}2{b}]{w} Export Discovered Emails to contacts_{base_dom}.txt")
        print(f"{space}{b}[{w}3{b}]{w} Handoff an Email to Comprehensive Deliverability Scan")
        print(f"{space}{b}[{w}4{b}]{w} Enrich Leadership with Additional B2B APIs (Name2Email / Hunter)")
        print(f"{space}{b}[{w}0{b}]{w} Back / New Scan")
        act = input(f"\n{space}{b}[{w}?{b}]{w} Select Action [0-4]: {b}").strip()

        if act == "1":
            fname = f"contacts_{base_dom}.json"
            try:
                with open(fname, "w", encoding="utf-8") as f:
                    json.dump(dossier, f, indent=4)
                print(f"{space}{g}[✓] Exported full JSON intelligence dossier to: {fname}{w}")
            except Exception as e:
                print(f"{space}{r}[!] Failed to export JSON: {e}{w}")
            pause()
        elif act == "2":
            fname = f"contacts_{base_dom}.txt"
            try:
                with open(fname, "w", encoding="utf-8") as f:
                    for em in emails:
                        f.write(f"{em['email']}\n")
                print(f"{space}{g}[✓] Exported {len(emails)} emails to: {fname}{w}")
            except Exception as e:
                print(f"{space}{r}[!] Failed to export TXT: {e}{w}")
            pause()
        elif act == "3":
            if emails:
                print(f"\n{space}Select email index to scan [1-{len(emails)}]:")
                for i, em in enumerate(emails, 1):
                    print(f"{space}  [{i}] {em['email']}")
                pick = input(f"{space}{b}[{w}?{b}]{w} Index: {b}").strip()
                if pick.isdigit() and 1 <= int(pick) <= len(emails):
                    chosen = emails[int(pick) - 1]["email"]
                    cls()
                    banner()
                    run_comprehensive_scan(chosen)
                    pause()
            else:
                print(f"{space}{y}[!] No emails available for handoff.{w}")
                pause()
        elif act == "4":
            print(f"\n{space}{b}[*]{w} Running B2B Lead Enrichment on detected leadership...")
            AIScraperEngine.enrich_leadership_with_b2b(dossier)
            new_emails = [e for e in dossier.get("emails", []) if "Enriched" in e.get("source", "")]
            if new_emails:
                print(f"{space}{g}[✓] Successfully discovered {len(new_emails)} new email addresses!{w}")
                for ne in new_emails:
                    print(f"{space}    {g}• {ne['email']}{w} ({ne['role_label']}) - {d}{ne['source']}{w}")
                emails = dossier.get("emails", [])
            else:
                print(f"{space}{y}[!] No additional emails could be verified with current B2B endpoints.{w}")
            pause()

# -------------------------------------------------------------
# 9. Permutation Name Finder (Generates & Saves to result.txt)
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
            k_count = q.get("total_keys", 1)
            k_act = q.get("active_keys", 1)
            key_tag = f" {d}({k_act}/{k_count} keys active){w}" if k_count > 1 else ""

            if service_name == "Apollo.io":
                print(f"{space}{g}[+] {service_name:<18}{w} : Plan: {y}{q.get('plan_name', 'Standard')}{w} | Account: {q.get('account_email', 'N/A')}{key_tag}")
                print(f"{space}    - Credits Remaining  : {G}{q.get('credits_remaining', 50)}{w} / {q.get('credits_total', 50)} credits/month")
            elif service_name == "Hunter.io":
                print(f"{space}{g}[+] {service_name:<18}{w} : Plan: {y}{q.get('plan_name')}{w} | Account: {q.get('account_email')}{key_tag}")
                print(f"{space}    - Searches Left      : {g}{q.get('searches_remaining')}{w} / {q.get('searches_available')} (Used: {q.get('searches_used')})")
                print(f"{space}    - Verifications Left : {g}{q.get('verifications_remaining')}{w} / {q.get('verifications_available')} (Used: {q.get('verifications_used')})")
                print(f"{space}    - Monthly Reset Date : {q.get('reset_date')}")
            elif service_name == "ContactOut":
                print(f"{space}{g}[+] {service_name:<18}{w} : Plan: {y}{q.get('plan', 'Free Tier')}{w} | Reset: {q.get('reset_date', 'Monthly')}{key_tag}")
                print(f"{space}    - Work Emails Left   : {g}{q.get('work_emails_remaining', 40)}{w} / {q.get('work_emails_total', 40)} per month")
                print(f"{space}    - Direct Phone Left  : {g}{q.get('phone_credits_remaining', 5)}{w} / {q.get('phone_credits_total', 5)} per month")
            elif service_name == "SalesQL":
                print(f"{space}{g}[+] {service_name:<18}{w} : Plan: {y}{q.get('plan', 'Free')}{w} | Reset: {q.get('reset_date', 'Monthly')}{key_tag}")
                print(f"{space}    - Credits Remaining  : {G}{q.get('credits_remaining', 50)}{w} / {q.get('credits_total', 50)} credits/month")
            elif service_name == "SignalHire":
                print(f"{space}{g}[+] {service_name:<18}{w} : Plan: {y}{q.get('plan', 'Free Starter')}{w}{key_tag}")
                print(f"{space}    - Contact Credits    : {G}{q.get('contact_credits_remaining', 5)}{w} / {q.get('contact_credits_total', 5)} available")
            elif service_name == "FinalScout":
                print(f"{space}{g}[+] {service_name:<18}{w} : Plan: {y}{q.get('plan', 'Free')}{w} | Reset: {q.get('reset_date', 'Monthly')}{key_tag}")
                print(f"{space}    - Regular Email Left : {g}{q.get('regular_credits_remaining', 20)}{w} / {q.get('regular_credits_total', 20)} credits")
                print(f"{space}    - AI Email Credits   : {g}{q.get('ai_credits_remaining', 10)}{w} credits")
            elif service_name == "ZeroBounce":
                print(f"{space}{g}[+] {service_name:<18}{w} : Credits Remaining: {G} {q.get('credits_remaining')} {w} validations{key_tag}")
            elif service_name == "DeBounce":
                print(f"{space}{g}[+] {service_name:<18}{w} : Balance Remaining: {G} {q.get('balance')} {w} credits{key_tag}")
            elif service_name == "GitHub API":
                print(f"{space}{g}[+] {service_name:<18}{w} : Mode: {y}{q.get('auth_mode')}{w}{key_tag}")
                print(f"{space}    - Search Rate Limit  : {g}{q.get('search_remaining')}{w} / {q.get('search_limit')} requests remaining")
                print(f"{space}    - Core Rate Limit    : {g}{q.get('core_remaining')}{w} / {q.get('core_limit')} requests remaining")
            else:
                status_text = q.get("status", "Active")
                print(f"{space}{g}[+] {service_name:<18}{w} : {g}{status_text}{w}{key_tag}")

            # Show multi-key breakdown if more than 1 key
            if "keys_breakdown" in q and len(q["keys_breakdown"]) > 1:
                for b_item in q["keys_breakdown"]:
                    key_id = b_item.get("key", b_item.get("token", "****"))
                    st = b_item.get("status", "N/A")
                    print(f"{space}      • Key [{key_id}]: {st}")
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
        if len(val) == 1:
            first = str(val[0]).strip()
            return f"{first[:4]}...{first[-4:]}" if len(first) > 8 else "****"
        previews = [f"{str(k)[:4]}...{str(k)[-4:]}" if len(str(k)) > 8 else "****" for k in val[:2]]
        extra = f" +{len(val)-2} more" if len(val) > 2 else ""
        return f"{', '.join(previews)}{extra} ({len(val)} keys)"
    s = str(val).strip()
    if len(s) > 8:
        return f"{s[:4]}...{s[-4:]}"
    return "****"

def config_keys_menu():
    while True:
        cls()
        banner()
        print(f"{space}{p}=== API Keys, Usage Quotas & Multi-Key Failover Manager ==={w}\n")
        print(f"{space}{d}Select an engine [01-16] to add, update, or clear its API keys.{w}")
        print(f"{space}{d}Tip: Enter multiple keys separated by commas for automatic failover.{w}\n")
        
        services = [
            ("Apollo.io Keys", "apollo_api_keys", "https://apollo.io", APIQuotaEngine.check_apollo_quota),
            ("Hunter.io Keys", "hunter_api_keys", "https://hunter.io", APIQuotaEngine.check_hunter_quota),
            ("ContactOut Keys", "contactout_api_keys", "https://contactout.com", APIQuotaEngine.check_contactout_quota),
            ("SalesQL Keys", "salesql_api_keys", "https://salesql.com", APIQuotaEngine.check_salesql_quota),
            ("SignalHire Keys", "signalhire_api_keys", "https://signalhire.com", APIQuotaEngine.check_signalhire_quota),
            ("FinalScout Keys", "finalscout_api_keys", "https://finalscout.com", APIQuotaEngine.check_finalscout_quota),
            ("AbstractAPI Keys", "abstract_api_keys", "https://abstractapi.com", None),
            ("ZeroBounce Keys", "zerobounce_api_keys", "https://zerobounce.net", APIQuotaEngine.check_zerobounce_quota),
            ("Debounce Keys", "debounce_api_keys", "https://debounce.io", APIQuotaEngine.check_debounce_quota),
            ("Mailboxlayer Keys", "mailboxlayer_api_keys", "https://mailboxlayer.com", None),
            ("EmailRep Keys", "emailrep_api_keys", "https://emailrep.io", None),
            ("GitHub Tokens", "github_tokens", "https://github.com/settings/tokens", APIQuotaEngine.check_github_quota),
            ("OpenAI API Keys", "openai_api_keys", "https://platform.openai.com", None),
            ("Gemini API Keys", "gemini_api_keys", "https://aistudio.google.com", None),
            ("Groq API Keys", "groq_api_keys", "https://console.groq.com", None),
            ("Anthropic Keys", "anthropic_api_keys", "https://console.anthropic.com", None)
        ]

        for i, (name, key_field, info, _) in enumerate(services, 1):
            keys = get_api_keys(key_field)
            masked = mask_key(keys)
            count_tag = f"[{len(keys)} key{'s' if len(keys)!=1 else ''}]" if keys else ""
            status = f"{g}[Configured {count_tag}: {masked}]{w}" if keys else f"{y}[Empty / Not set]{w}"
            print(f"{space}{b}[{w}{i:02d}{b}]{w} {name:<18} {status:<34} {d}({info}){w}")

        print(f"\n{space}{G} [L] Check Real-Time API Quotas & Remaining Credit Balances {w}")
        print(f"{space}{B} [T] View Free Tier vs Premium Tier Quota & Usage Limits Matrix {w}")
        print(f"\n{space}{b}[{w}0{b}]{w} Back to Main Menu\n")
        ch = input(f"{space}{b}[{w}?{b}]{w} Select option to manage [1-16, L, T, 0]: {b}").strip().upper()
        
        if ch == "0" or not ch:
            break
        elif ch == "L":
            live_quota_inspector_menu()
        elif ch == "T":
            tier_limits_matrix_menu()
        elif ch in [str(x) for x in range(1, len(services) + 1)] or ch in [f"{x:02d}" for x in range(1, len(services) + 1)]:
            idx = int(ch) - 1
            s_name, s_field, s_url, validator_fn = services[idx]
            current_keys = get_api_keys(s_field)
            
            print(f"\n{space}{w}--- Manage Keys for: {y}{s_name}{w} ---")
            if current_keys:
                print(f"{space}{g}Currently configured ({len(current_keys)} key{'s' if len(current_keys)!=1 else ''}):{w}")
                for k_idx, k_val in enumerate(current_keys, 1):
                    print(f"{space}  [{k_idx}] {mask_key(k_val)}")
            else:
                print(f"{space}{y}Currently configured: None{w}")
            
            print(f"\n{space}{d}Instructions:{w}")
            print(f"{space}{d}- Enter 1 or more keys separated by commas (e.g. key1, key2, key3){w}")
            print(f"{space}{d}- Enter '+key' to append a key without replacing existing keys{w}")
            print(f"{space}{d}- Press ENTER without typing anything to clear all keys for this service{w}")
            
            new_input = input(f"\n{space}{b}[{w}?{b}]{w} Enter key(s): {b}").strip()
            
            if not new_input:
                set_api_keys(s_field, [])
                print(f"\n{space}{y}[!] Cleared all keys for {s_name}.{w}")
            elif new_input.startswith("+"):
                append_val = new_input[1:].strip()
                if append_val:
                    add_api_key(s_field, append_val)
                    updated = get_api_keys(s_field)
                    print(f"\n{space}{g}[+] Appended new key to {s_name}! Total keys: {len(updated)}{w}")
            else:
                set_api_keys(s_field, new_input)
                updated = get_api_keys(s_field)
                print(f"\n{space}{g}[+] Updated {s_name}! Saved {len(updated)} key(s) in config.json!{w}")

            updated_keys = get_api_keys(s_field)
            if updated_keys and validator_fn:
                print(f"{space}{b}[*]{w} Running live balance check across configured keys...")
                try:
                    res = validator_fn(api_keys=updated_keys)
                    if res.get("success"):
                        print(f"{space}{g}[✓] Service Connected!{w} {res.get('status', 'Active connection established.')}")
                        if "credits_remaining" in res:
                            print(f"{space}    - Total Credits: {G}{res['credits_remaining']}{w}")
                        elif "work_emails_remaining" in res:
                            print(f"{space}    - Work Emails  : {G}{res['work_emails_remaining']}{w}")
                    else:
                        print(f"{space}{y}[!] Notice:{w} {res.get('error', 'Keys saved.')}")
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
        print(f"{space}{b}[{w}2{b}]{w} Webmail Address Matrix Across 75+ Global Providers (MX Check & Mailbox Probe)")
        print(f"{space} {w}|")
        print(f"{space}{b}[{w}3{b}]{w} {G} Comprehensive Multi-Engine Email Scan {w} (All-in-One Deliverability)")
        print(f"{space}{b}[{w}4{b}]{w} {B} B2B Email Finders & Lead Enrichment Suite {w} (Apollo, ContactOut, SalesQL, SignalHire, FinalScout, Name2Mail, Hunter)")
        print(f"{space} {w}|")
        print(f"{space}{b}[{w}5{b}]{w} AbstractAPI Email Verifier")
        print(f"{space}{b}[{w}6{b}]{w} Commercial Verifiers (ZeroBounce / Debounce / Mailboxlayer)")
        print(f"{space}{b}[{w}7{b}]{w} OSINT & Identity Profiler (Gravatar + GitHub + EmailRep)")
        print(f"{space}{b}[{w}8{b}]{w} {G} AI Web Scraper & Contact Harvester {w} (Emails, Phones, Socials & Team)")
        print(f"{space}{b}[{w}9{b}]{w} Name-to-Email Permutation Generator (Save to result.txt)")
        print(f"{space} {w}|")
        print(f"{space}{b}[{w}10{b}]{w} API Keys, Usage Quotas & Tier Limits Manager")
        print(f"{space}{b}[{w}0{b}]{w} Exit Mailerone\n")

        choice = input(f"{space}{b}[{w}?{b}]{w} Select an option [0-10]: {b}").strip()

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
            ai_scraper_menu()
        elif choice in ["9", "09"]:
            name_finder_menu()
        elif choice in ["10"]:
            config_keys_menu()
        elif choice == "0":
            print(f"\n{space}{b}[*]{w} Goodbye!\n")
            break
        else:
            time.sleep(1)

if __name__ == "__main__":
    main_menu()
