import re
import random
import hashlib
import requests
import dns.resolver
from concurrent.futures import ThreadPoolExecutor, as_completed
from config_manager import get_api_key

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# -------------------------------------------------------------
# 1. DNS & Mail Server Inspector (Google DoH + Local Resolver)
# -------------------------------------------------------------
class DNSInspectorEngine:
    @staticmethod
    def query_doh(domain, record_type="MX"):
        try:
            url = f"https://dns.google/resolve?name={domain}&type={record_type}"
            resp = requests.get(url, headers=HEADERS, timeout=6).json()
            if "Answer" in resp:
                return [ans["data"] for ans in resp["Answer"]]
        except Exception:
            pass
        return []

    @classmethod
    def check_domain_dns(cls, domain):
        mx_records = cls.query_doh(domain, "MX")
        txt_records = cls.query_doh(domain, "TXT")
        
        # Fallback to dnspython if DoH returned empty
        if not mx_records:
            try:
                res = dns.resolver.Resolver()
                res.nameservers = ['8.8.8.8', '1.1.1.1']
                answers = res.resolve(domain, 'MX', lifetime=5)
                mx_records = [str(r.exchange).rstrip('.') for r in answers]
            except Exception:
                pass

        # Check SPF & DMARC
        spf = [t for t in txt_records if "v=spf1" in t]
        dmarc_records = cls.query_doh(f"_dmarc.{domain}", "TXT")

        return {
            "domain": domain,
            "has_mx": len(mx_records) > 0,
            "mx_records": mx_records[:5],
            "spf": spf[0] if spf else "None",
            "dmarc": dmarc_records[0] if dmarc_records else "None"
        }

# -------------------------------------------------------------
# 2. Disify Free API Engine (No API Key Required)
# -------------------------------------------------------------
class DisifyEngine:
    @staticmethod
    def verify(email):
        try:
            url = f"https://disify.com/api/email/{email}"
            resp = requests.get(url, headers=HEADERS, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "success": True,
                    "format": data.get("format", False),
                    "domain": data.get("domain", ""),
                    "disposable": data.get("disposable", False),
                    "dns": data.get("dns", False),
                    "whitelist": data.get("whitelist", False),
                    "free_provider": data.get("free", False),
                    "role_account": data.get("role", False),
                    "mx_info": data.get("mx_info", [])
                }
            return {"success": False, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# -------------------------------------------------------------
# 3. Disposable Domain List Engine (Offline + Live Blocklist)
# -------------------------------------------------------------
class DisposableBlocklistEngine:
    _cached_domains = set()

    @classmethod
    def load_blocklist(cls):
        if cls._cached_domains:
            return cls._cached_domains
        # Default common burners
        common = {
            "tempmail.com", "10minutemail.com", "guerrillamail.com", "mailinator.com",
            "throwawaymail.com", "yopmail.com", "sharklasers.com", "getairmail.com",
            "dispostable.com", "mytemp.email", "nada.ltd", "mohmal.com", "trashmail.com"
        }
        cls._cached_domains.update(common)
        try:
            url = "https://raw.githubusercontent.com/disposable-email-domains/disposable-email-domains/master/disposable_email_blocklist.conf"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                for line in resp.text.splitlines():
                    d = line.strip().lower()
                    if d and not d.startswith("#"):
                        cls._cached_domains.add(d)
        except Exception:
            pass
        return cls._cached_domains

    @classmethod
    def is_disposable(cls, domain):
        domains = cls.load_blocklist()
        return domain.lower() in domains

# -------------------------------------------------------------
# 4. OSINT Engines (GitHub & Gravatar - Free, No Key Required)
# -------------------------------------------------------------
class OSINTEngine:
    @staticmethod
    def check_gravatar(email):
        h = hashlib.md5(email.strip().lower().encode("utf-8")).hexdigest()
        url = f"https://www.gravatar.com/{h}.json"
        avatar_url = f"https://www.gravatar.com/avatar/{h}?d=404"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=6)
            if resp.status_code == 200:
                entry = resp.json().get("entry", [{}])[0]
                return {
                    "has_gravatar": True,
                    "display_name": entry.get("displayName", "N/A"),
                    "profile_url": entry.get("profileUrl", ""),
                    "avatar_url": avatar_url,
                    "location": entry.get("currentLocation", "N/A")
                }
            # Check direct avatar
            av_resp = requests.get(avatar_url, timeout=4)
            if av_resp.status_code == 200:
                return {"has_gravatar": True, "avatar_url": avatar_url}
        except Exception:
            pass
        return {"has_gravatar": False}

    @staticmethod
    def check_github(query_email_or_user):
        try:
            url = f"https://api.github.com/search/users?q={query_email_or_user}+in:email"
            resp = requests.get(url, headers=HEADERS, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                if items:
                    user = items[0]
                    return {
                        "found": True,
                        "username": user.get("login"),
                        "profile_url": user.get("html_url"),
                        "avatar_url": user.get("avatar_url")
                    }
        except Exception:
            pass
        return {"found": False}

# -------------------------------------------------------------
# 5. Hunter.io API Engine
# -------------------------------------------------------------
class HunterEngine:
    @staticmethod
    def verify(email, api_key=None):
        if not api_key:
            keys = get_api_key("hunter_api_keys") or []
            api_key = random.choice(keys) if keys else ""
        if not api_key:
            return {"success": False, "error": "No Hunter.io API key available"}
        try:
            url = f"https://api.hunter.io/v2/email-verifier?email={email}&api_key={api_key}"
            resp = requests.get(url, headers=HEADERS, timeout=8)
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                return {
                    "success": True,
                    "status": data.get("status"),
                    "result": data.get("result"),
                    "score": data.get("score"),
                    "regexp": data.get("regexp"),
                    "gibberish": data.get("gibberish"),
                    "disposable": data.get("disposable"),
                    "mx_records": data.get("mx_records"),
                    "smtp_server": data.get("smtp_server"),
                    "smtp_check": data.get("smtp_check"),
                    "block": data.get("block")
                }
            return {"success": False, "error": f"Hunter Error: {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def find_email(domain, first_name, last_name, api_key=None):
        if not api_key:
            keys = get_api_key("hunter_api_keys") or []
            api_key = random.choice(keys) if keys else ""
        if not api_key:
            return {"success": False, "error": "No Hunter.io API key available"}
        try:
            url = f"https://api.hunter.io/v2/email-finder?domain={domain}&first_name={first_name}&last_name={last_name}&api_key={api_key}"
            resp = requests.get(url, headers=HEADERS, timeout=8)
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                return {
                    "success": True,
                    "email": data.get("email"),
                    "score": data.get("score"),
                    "domain": data.get("domain"),
                    "sources": len(data.get("sources", []))
                }
            return {"success": False, "error": f"Hunter Finder Error: {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# -------------------------------------------------------------
# 6. AbstractAPI Email Validation Engine
# -------------------------------------------------------------
class AbstractAPIEngine:
    @staticmethod
    def verify(email, api_key=None):
        if not api_key:
            api_key = get_api_key("abstract_api_key")
        if not api_key:
            return {"success": False, "error": "No AbstractAPI key configured"}
        try:
            url = f"https://emailvalidation.abstractapi.com/v1/?api_key={api_key}&email={email}"
            resp = requests.get(url, headers=HEADERS, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "success": True,
                    "deliverability": data.get("deliverability"),
                    "quality_score": data.get("quality_score"),
                    "is_valid_format": data.get("is_valid_format", {}).get("value"),
                    "is_free_email": data.get("is_free_email", {}).get("value"),
                    "is_disposable_email": data.get("is_disposable_email", {}).get("value"),
                    "is_role_email": data.get("is_role_email", {}).get("value"),
                    "is_catchall_email": data.get("is_catchall_email", {}).get("value"),
                    "is_mx_found": data.get("is_mx_found", {}).get("value"),
                    "is_smtp_valid": data.get("is_smtp_valid", {}).get("value"),
                    "autocorrect": data.get("autocorrect", "")
                }
            return {"success": False, "error": f"AbstractAPI Error: {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# -------------------------------------------------------------
# 7. ZeroBounce API Engine
# -------------------------------------------------------------
class ZeroBounceEngine:
    @staticmethod
    def verify(email, api_key=None):
        if not api_key:
            api_key = get_api_key("zerobounce_api_key")
        if not api_key:
            return {"success": False, "error": "No ZeroBounce API key configured"}
        try:
            url = f"https://api.zerobounce.net/v2/validate?api_key={api_key}&email={email}"
            resp = requests.get(url, headers=HEADERS, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "success": True,
                    "status": data.get("status"),
                    "sub_status": data.get("sub_status"),
                    "free_email": data.get("free_email"),
                    "domain_age_days": data.get("domain_age_days"),
                    "mx_found": data.get("mx_found"),
                    "smtp_provider": data.get("smtp_provider"),
                    "did_you_mean": data.get("did_you_mean")
                }
            return {"success": False, "error": f"ZeroBounce Error: {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# -------------------------------------------------------------
# 8. Debounce API Engine
# -------------------------------------------------------------
class DebounceEngine:
    @staticmethod
    def verify(email, api_key=None):
        if not api_key:
            api_key = get_api_key("debounce_api_key")
        if not api_key:
            return {"success": False, "error": "No Debounce API key configured"}
        try:
            url = f"https://api.debounce.io/v1/?api={api_key}&email={email}"
            resp = requests.get(url, headers=HEADERS, timeout=8)
            if resp.status_code == 200:
                data = resp.json().get("debounce", {})
                return {
                    "success": True,
                    "result": data.get("result"),
                    "reason": data.get("reason"),
                    "free": data.get("free_email") == "true",
                    "disposable": data.get("disposable") == "true",
                    "mx_record": data.get("mx_record")
                }
            return {"success": False, "error": f"Debounce Error: {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# -------------------------------------------------------------
# 9. Mailboxlayer (APILayer) Engine
# -------------------------------------------------------------
class MailboxlayerEngine:
    @staticmethod
    def verify(email, api_key=None):
        if not api_key:
            api_key = get_api_key("mailboxlayer_api_key")
        if not api_key:
            return {"success": False, "error": "No Mailboxlayer API key configured"}
        try:
            url = f"http://apilayer.net/api/check?access_key={api_key}&email={email}"
            resp = requests.get(url, headers=HEADERS, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "success": True,
                    "format_valid": data.get("format_valid"),
                    "mx_found": data.get("mx_found"),
                    "smtp_check": data.get("smtp_check"),
                    "catch_all": data.get("catch_all"),
                    "role": data.get("role"),
                    "disposable": data.get("disposable"),
                    "free": data.get("free"),
                    "score": data.get("score")
                }
            return {"success": False, "error": f"Mailboxlayer Error: {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# -------------------------------------------------------------
# 10. EmailRep.io Threat & Reputation Engine
# -------------------------------------------------------------
class EmailRepEngine:
    @staticmethod
    def verify(email, api_key=None):
        if not api_key:
            api_key = get_api_key("emailrep_api_key")
        headers = HEADERS.copy()
        if api_key:
            headers["Key"] = api_key
        try:
            url = f"https://emailrep.io/{email}"
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                details = data.get("details", {})
                return {
                    "success": True,
                    "reputation": data.get("reputation"),
                    "suspicious": data.get("suspicious"),
                    "references": data.get("references"),
                    "blacklisted": details.get("blacklisted"),
                    "malicious_activity": details.get("malicious_activity"),
                    "credentials_leaked": details.get("credentials_leaked"),
                    "data_breach": details.get("data_breach"),
                    "spam": details.get("spam"),
                    "domain_exists": details.get("domain_exists")
                }
            return {"success": False, "error": f"EmailRep Error: {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# -------------------------------------------------------------
# 11. ContactOut API Engine (B2B Email & Phone Finder)
# -------------------------------------------------------------
class ContactOutEngine:
    @staticmethod
    def find_email(domain, first_name, last_name, company=None, api_key=None):
        if not api_key:
            api_key = get_api_key("contactout_api_key")
        if not api_key:
            return {"success": False, "error": "No ContactOut API key configured"}
        headers = HEADERS.copy()
        headers["authorization"] = f"Bearer {api_key}"
        headers["token"] = api_key
        headers["Content-Type"] = "application/json"
        try:
            url = "https://api.contactout.com/v1/people/search"
            payload = {
                "first_name": first_name.strip(),
                "last_name": last_name.strip(),
                "domain": domain.strip().lower()
            }
            if company:
                payload["company"] = company.strip()
            resp = requests.post(url, headers=headers, json=payload, timeout=9)
            if resp.status_code == 200:
                data = resp.json()
                profile = data.get("profile", {}) or (data.get("data", [{}])[0] if isinstance(data.get("data"), list) and data.get("data") else {})
                work_emails = profile.get("work_emails", []) or profile.get("work_email", [])
                personal_emails = profile.get("personal_emails", []) or profile.get("personal_email", [])
                if isinstance(work_emails, str):
                    work_emails = [work_emails]
                if isinstance(personal_emails, str):
                    personal_emails = [personal_emails]
                phones = profile.get("phones", []) or profile.get("phone_numbers", [])
                if isinstance(phones, str):
                    phones = [phones]
                return {
                    "success": True,
                    "engine": "ContactOut",
                    "work_emails": work_emails,
                    "personal_emails": personal_emails,
                    "primary_email": work_emails[0] if work_emails else (personal_emails[0] if personal_emails else None),
                    "phone_numbers": phones,
                    "job_title": profile.get("job_title", profile.get("title", "")),
                    "company": profile.get("company_name", company or domain),
                    "linkedin_url": profile.get("linkedin_url", "")
                }
            return {"success": False, "error": f"ContactOut Error: {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def find_by_linkedin(linkedin_url, api_key=None):
        if not api_key:
            api_key = get_api_key("contactout_api_key")
        if not api_key:
            return {"success": False, "error": "No ContactOut API key configured"}
        headers = HEADERS.copy()
        headers["authorization"] = f"Bearer {api_key}"
        headers["token"] = api_key
        try:
            url = f"https://api.contactout.com/v1/email?url={linkedin_url}"
            resp = requests.get(url, headers=headers, timeout=9)
            if resp.status_code == 200:
                data = resp.json()
                profile = data.get("profile", {}) or data
                work_emails = profile.get("work_emails", [])
                personal_emails = profile.get("personal_emails", [])
                if isinstance(work_emails, str):
                    work_emails = [work_emails]
                if isinstance(personal_emails, str):
                    personal_emails = [personal_emails]
                return {
                    "success": True,
                    "engine": "ContactOut",
                    "work_emails": work_emails,
                    "personal_emails": personal_emails,
                    "primary_email": work_emails[0] if work_emails else (personal_emails[0] if personal_emails else None),
                    "phone_numbers": profile.get("phones", []),
                    "job_title": profile.get("title", ""),
                    "company": profile.get("company", "")
                }
            return {"success": False, "error": f"ContactOut Error: {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# -------------------------------------------------------------
# 12. SalesQL API Engine (B2B Lead Enrichment)
# -------------------------------------------------------------
class SalesQLEngine:
    @staticmethod
    def find_email(domain, first_name, last_name, api_key=None):
        if not api_key:
            api_key = get_api_key("salesql_api_key")
        if not api_key:
            return {"success": False, "error": "No SalesQL API key configured"}
        headers = HEADERS.copy()
        headers["Authorization"] = f"Bearer {api_key}"
        headers["X-Api-Key"] = api_key
        headers["Content-Type"] = "application/json"
        try:
            url = "https://api.salesql.com/v1/persons/enrich"
            payload = {
                "first_name": first_name.strip(),
                "last_name": last_name.strip(),
                "domain": domain.strip().lower()
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=9)
            if resp.status_code == 200:
                data = resp.json()
                person = data.get("person", {}) or data.get("data", {}) or data
                raw_emails = person.get("emails", [])
                emails_list = []
                for em in raw_emails:
                    if isinstance(em, dict):
                        emails_list.append(em.get("email"))
                    elif isinstance(em, str):
                        emails_list.append(em)
                return {
                    "success": True,
                    "engine": "SalesQL",
                    "emails": emails_list,
                    "primary_email": emails_list[0] if emails_list else person.get("email"),
                    "phones": person.get("phones", []),
                    "headline": person.get("headline", ""),
                    "location": person.get("location", ""),
                    "company": person.get("company_name", domain)
                }
            return {"success": False, "error": f"SalesQL Error: {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def find_by_linkedin(linkedin_url, api_key=None):
        if not api_key:
            api_key = get_api_key("salesql_api_key")
        if not api_key:
            return {"success": False, "error": "No SalesQL API key configured"}
        headers = HEADERS.copy()
        headers["Authorization"] = f"Bearer {api_key}"
        headers["X-Api-Key"] = api_key
        headers["Content-Type"] = "application/json"
        try:
            url = "https://api.salesql.com/v1/persons/enrich"
            payload = {"linkedin_url": linkedin_url.strip()}
            resp = requests.post(url, headers=headers, json=payload, timeout=9)
            if resp.status_code == 200:
                data = resp.json()
                person = data.get("person", {}) or data
                raw_emails = person.get("emails", [])
                emails_list = [em.get("email") if isinstance(em, dict) else em for em in raw_emails]
                return {
                    "success": True,
                    "engine": "SalesQL",
                    "emails": emails_list,
                    "primary_email": emails_list[0] if emails_list else person.get("email"),
                    "headline": person.get("headline", ""),
                    "company": person.get("company_name", "")
                }
            return {"success": False, "error": f"SalesQL Error: {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# -------------------------------------------------------------
# 13. SignalHire API Engine (Candidate & Prospect Email Finder)
# -------------------------------------------------------------
class SignalHireEngine:
    @staticmethod
    def find_email(domain, first_name, last_name, api_key=None):
        if not api_key:
            api_key = get_api_key("signalhire_api_key")
        if not api_key:
            return {"success": False, "error": "No SignalHire API key configured"}
        headers = HEADERS.copy()
        headers["apiKey"] = api_key
        headers["Content-Type"] = "application/json"
        try:
            url = "https://www.signalhire.com/api/v1/candidate/search"
            payload = {
                "name": f"{first_name.strip()} {last_name.strip()}",
                "company": domain.strip().lower(),
                "items": ["email", "phone"]
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=9)
            if resp.status_code in [200, 201]:
                data = resp.json()
                candidate = data.get("candidate", {}) or (data.get("candidates", [{}])[0] if isinstance(data.get("candidates"), list) and data.get("candidates") else {})
                raw_emails = candidate.get("emails", [])
                emails_list = [e.get("value") if isinstance(e, dict) else e for e in raw_emails]
                raw_phones = candidate.get("phones", [])
                phones_list = [p.get("value") if isinstance(p, dict) else p for p in raw_phones]
                return {
                    "success": True,
                    "engine": "SignalHire",
                    "emails": emails_list,
                    "primary_email": emails_list[0] if emails_list else None,
                    "phones": phones_list,
                    "social_profiles": candidate.get("socialProfiles", []),
                    "status": data.get("status", "found")
                }
            return {"success": False, "error": f"SignalHire Error: {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# -------------------------------------------------------------
# 14. FinalScout API Engine (LinkedIn & Corporate Email Finder)
# -------------------------------------------------------------
class FinalScoutEngine:
    @staticmethod
    def find_email(domain, first_name, last_name, api_key=None):
        if not api_key:
            api_key = get_api_key("finalscout_api_key")
        if not api_key:
            return {"success": False, "error": "No FinalScout API key configured"}
        headers = HEADERS.copy()
        headers["Authorization"] = f"Bearer {api_key}"
        headers["X-API-KEY"] = api_key
        headers["Content-Type"] = "application/json"
        try:
            url = "https://finalscout.com/api/v1/emails/find"
            payload = {
                "first_name": first_name.strip(),
                "last_name": last_name.strip(),
                "domain": domain.strip().lower()
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=9)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "success": True,
                    "engine": "FinalScout",
                    "email": data.get("email"),
                    "status": data.get("status", "deliverable"),
                    "score": data.get("score", 100),
                    "title": data.get("title", ""),
                    "domain": domain
                }
            return {"success": False, "error": f"FinalScout Error: {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def find_by_linkedin(linkedin_url, api_key=None):
        if not api_key:
            api_key = get_api_key("finalscout_api_key")
        if not api_key:
            return {"success": False, "error": "No FinalScout API key configured"}
        headers = HEADERS.copy()
        headers["Authorization"] = f"Bearer {api_key}"
        headers["X-API-KEY"] = api_key
        headers["Content-Type"] = "application/json"
        try:
            url = "https://finalscout.com/api/v1/linkedin/search"
            payload = {"url": linkedin_url.strip()}
            resp = requests.post(url, headers=headers, json=payload, timeout=9)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "success": True,
                    "engine": "FinalScout",
                    "email": data.get("email"),
                    "status": data.get("status"),
                    "score": data.get("score"),
                    "name": data.get("name")
                }
            return {"success": False, "error": f"FinalScout Error: {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# -------------------------------------------------------------
# 15. Name2Email (Name2Mail) Smart Permutator & Verification Engine
# -------------------------------------------------------------
class Name2EmailEngine:
    @staticmethod
    def generate_patterns(first_name, last_name, domain):
        clean_first = re.sub(r'[^a-zA-Z0-9]', '', first_name).lower()
        clean_last = re.sub(r'[^a-zA-Z0-9]', '', last_name).lower()
        clean_domain = domain.strip().lower()

        if not clean_first or not clean_last or not clean_domain:
            return []

        f = clean_first[0]
        l = clean_last[0]

        patterns = [
            f"{clean_first}.{clean_last}",
            f"{clean_first}{clean_last}",
            f"{f}.{clean_last}",
            f"{f}{clean_last}",
            f"{clean_first}_{clean_last}",
            f"{f}_{clean_last}",
            f"{clean_first}-{clean_last}",
            f"{f}-{clean_last}",
            f"{clean_first}.{l}",
            f"{clean_first}{l}",
            f"{clean_first}_{l}",
            f"{clean_first}-{l}",
            f"{clean_first}",
            f"{clean_last}",
            f"{clean_last}.{clean_first}",
            f"{clean_last}{clean_first}",
            f"{clean_last}.{f}",
            f"{clean_last}{f}",
            f"{clean_last}_{clean_first}",
            f"{clean_last}_{f}",
            f"{clean_last}-{clean_first}",
            f"{clean_last}-{f}",
            f"{l}.{clean_first}",
            f"{l}{clean_first}",
            f"{l}_{clean_first}",
            f"{l}-{clean_first}",
            f"{f}.{l}",
            f"{f}{l}",
            f"{clean_first}.{clean_last}1",
            f"{clean_first}.{clean_last}2",
            f"{clean_first}{clean_last}1",
            f"{clean_first}{clean_last}123",
            f"{clean_first}{clean_last}777"
        ]

        seen = set()
        unique_emails = []
        for p in patterns:
            em = f"{p}@{clean_domain}"
            if em not in seen:
                seen.add(em)
                unique_emails.append(em)

        return unique_emails

    @classmethod
    def find_and_verify(cls, first_name, last_name, domain, max_threads=6):
        domain = domain.strip().lower()
        dns_info = DNSInspectorEngine.check_domain_dns(domain)
        is_burner = DisposableBlocklistEngine.is_disposable(domain)

        if not dns_info["has_mx"]:
            return {
                "success": False,
                "domain": domain,
                "error": "Target domain does not have active MX mail servers.",
                "has_mx": False,
                "is_disposable": is_burner,
                "valid_candidates": [],
                "all_patterns": []
            }

        patterns = cls.generate_patterns(first_name, last_name, domain)
        candidate_results = []
        valid_candidates = []

        def check_single(email):
            res = DisifyEngine.verify(email)
            is_valid = res.get("success") and res.get("dns") and not res.get("disposable")
            return {
                "email": email,
                "dns_active": res.get("dns", False),
                "format": res.get("format", False),
                "is_free": res.get("free_provider", False),
                "is_valid": is_valid
            }

        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = {executor.submit(check_single, em): em for em in patterns}
            for future in as_completed(futures):
                try:
                    r = future.result()
                    candidate_results.append(r)
                    if r["is_valid"]:
                        valid_candidates.append(r["email"])
                except Exception:
                    pass

        priority_prefixes = [
            f"{first_name.lower()}.{last_name.lower()}@",
            f"{first_name.lower()[0]}{last_name.lower()}@",
            f"{first_name.lower()[0]}.{last_name.lower()}@",
            f"{first_name.lower()}{last_name.lower()}@"
        ]
        
        sorted_valid = []
        for pref in priority_prefixes:
            for v in valid_candidates:
                if v.startswith(pref) and v not in sorted_valid:
                    sorted_valid.append(v)
        for v in valid_candidates:
            if v not in sorted_valid:
                sorted_valid.append(v)

        return {
            "success": True,
            "engine": "Name2Email",
            "domain": domain,
            "has_mx": True,
            "is_disposable": is_burner,
            "mx_records": dns_info["mx_records"],
            "total_generated": len(patterns),
            "valid_candidates": sorted_valid,
            "primary_candidate": sorted_valid[0] if sorted_valid else (patterns[0] if patterns else None),
            "all_candidates": candidate_results
        }

# -------------------------------------------------------------
# 16. MultiFinderEngine (Unified Multi-Engine Lead Finder Pipeline)
# -------------------------------------------------------------
class MultiFinderEngine:
    @staticmethod
    def search(domain, first_name, last_name, company=None, linkedin_url=None):
        results = {
            "query": {
                "first_name": first_name,
                "last_name": last_name,
                "domain": domain,
                "company": company,
                "linkedin_url": linkedin_url
            },
            "engines_queried": [],
            "found_emails": [],
            "found_phones": [],
            "social_profiles": [],
            "details": {}
        }

        # 1. Hunter.io
        h_res = HunterEngine.find_email(domain, first_name, last_name)
        results["engines_queried"].append("Hunter.io")
        results["details"]["hunter"] = h_res
        if h_res.get("success") and h_res.get("email"):
            results["found_emails"].append({
                "email": h_res["email"],
                "source": "Hunter.io",
                "confidence": f"{h_res.get('score', 'N/A')}%"
            })

        # 2. ContactOut
        if linkedin_url:
            co_res = ContactOutEngine.find_by_linkedin(linkedin_url)
        else:
            co_res = ContactOutEngine.find_email(domain, first_name, last_name, company=company)
        results["engines_queried"].append("ContactOut")
        results["details"]["contactout"] = co_res
        if co_res.get("success"):
            for em in co_res.get("work_emails", []) + co_res.get("personal_emails", []):
                if em and not any(x["email"] == em for x in results["found_emails"]):
                    results["found_emails"].append({
                        "email": em,
                        "source": "ContactOut",
                        "confidence": "High"
                    })
            for ph in co_res.get("phone_numbers", []):
                if ph and ph not in results["found_phones"]:
                    results["found_phones"].append(ph)

        # 3. SalesQL
        if linkedin_url:
            sql_res = SalesQLEngine.find_by_linkedin(linkedin_url)
        else:
            sql_res = SalesQLEngine.find_email(domain, first_name, last_name)
        results["engines_queried"].append("SalesQL")
        results["details"]["salesql"] = sql_res
        if sql_res.get("success"):
            for em in sql_res.get("emails", []):
                if em and not any(x["email"] == em for x in results["found_emails"]):
                    results["found_emails"].append({
                        "email": em,
                        "source": "SalesQL",
                        "confidence": "High"
                    })
            for ph in sql_res.get("phones", []):
                if ph and ph not in results["found_phones"]:
                    results["found_phones"].append(ph)

        # 4. SignalHire
        sh_res = SignalHireEngine.find_email(domain, first_name, last_name)
        results["engines_queried"].append("SignalHire")
        results["details"]["signalhire"] = sh_res
        if sh_res.get("success"):
            for em in sh_res.get("emails", []):
                if em and not any(x["email"] == em for x in results["found_emails"]):
                    results["found_emails"].append({
                        "email": em,
                        "source": "SignalHire",
                        "confidence": "High"
                    })
            for ph in sh_res.get("phones", []):
                if ph and ph not in results["found_phones"]:
                    results["found_phones"].append(ph)

        # 5. FinalScout
        if linkedin_url:
            fs_res = FinalScoutEngine.find_by_linkedin(linkedin_url)
        else:
            fs_res = FinalScoutEngine.find_email(domain, first_name, last_name)
        results["engines_queried"].append("FinalScout")
        results["details"]["finalscout"] = fs_res
        if fs_res.get("success") and fs_res.get("email"):
            em = fs_res["email"]
            if not any(x["email"] == em for x in results["found_emails"]):
                results["found_emails"].append({
                    "email": em,
                    "source": "FinalScout",
                    "confidence": f"{fs_res.get('score', 100)}%"
                })

        # 6. Name2Email Smart Permutation Generator & Validator
        n2e_res = Name2EmailEngine.find_and_verify(first_name, last_name, domain)
        results["engines_queried"].append("Name2Email (Smart Permutator)")
        results["details"]["name2email"] = n2e_res
        if n2e_res.get("success") and n2e_res.get("valid_candidates"):
            for em in n2e_res["valid_candidates"][:3]:
                if not any(x["email"] == em for x in results["found_emails"]):
                    results["found_emails"].append({
                        "email": em,
                        "source": "Name2Email (Verified Candidate)",
                        "confidence": "Medium (Pattern Verified)"
                    })

        return results

