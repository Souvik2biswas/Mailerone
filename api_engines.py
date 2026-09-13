import re
import random
import hashlib
import requests
import dns.resolver
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
