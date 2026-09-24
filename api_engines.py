import re
import random
import hashlib
import requests
try:
    import dns.resolver
    HAVE_DNSPYTHON = True
except ImportError:
    HAVE_DNSPYTHON = False
from concurrent.futures import ThreadPoolExecutor, as_completed
from config_manager import get_api_key, get_api_keys

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def mask_key_preview(k):
    if not k:
        return ""
    s = str(k).strip()
    return f"{s[:4]}...{s[-4:]}" if len(s) > 8 else "****"

# -------------------------------------------------------------
# 1. DNS & Mail Server Inspector (Google DoH + Local Resolver)
# -------------------------------------------------------------
class DNSInspectorEngine:
    @staticmethod
    def query_doh(domain, record_type="MX"):
        try:
            url = f"https://dns.google/resolve?name={domain}&type={record_type}"
            resp = requests.get(url, headers=HEADERS, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                if "Answer" in data:
                    return [ans["data"] for ans in data["Answer"]]
        except Exception:
            pass
        return []

    @classmethod
    def check_domain_dns(cls, domain):
        mx_records = cls.query_doh(domain, "MX")
        txt_records = cls.query_doh(domain, "TXT")
        
        # Fallback to dnspython if DoH returned empty
        if not mx_records and HAVE_DNSPYTHON:
            try:
                res = dns.resolver.Resolver()
                res.nameservers = ['8.8.8.8', '1.1.1.1']
                answers = res.resolve(domain, 'MX', lifetime=5)
                mx_records = [str(r.exchange).rstrip('.') for r in answers]
            except Exception:
                pass

        # Check SPF & DMARC
        spf = [t.replace('"', '').strip() for t in txt_records if "v=spf1" in t]
        dmarc_records = cls.query_doh(f"_dmarc.{domain}", "TXT")
        dmarc_clean = [d.replace('"', '').strip() for d in dmarc_records if "v=DMARC1" in d or "DMARC" in d]

        return {
            "domain": domain,
            "has_mx": len(mx_records) > 0,
            "mx_records": mx_records[:5],
            "spf": spf[0] if spf else "None",
            "dmarc": dmarc_clean[0] if dmarc_clean else (dmarc_records[0].replace('"', '').strip() if dmarc_records else "None")
        }

# -------------------------------------------------------------
# 2. Disify Free API Engine (No API Key Required)
# -------------------------------------------------------------
class DisifyEngine:
    @staticmethod
    def verify(email):
        try:
            url = f"https://disify.com/api/email/{email.strip()}"
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
# 4. OSINT Engines (GitHub & Gravatar - Multi-Token Failover Supported)
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
            av_resp = requests.get(avatar_url, timeout=4)
            if av_resp.status_code == 200:
                return {"has_gravatar": True, "avatar_url": avatar_url}
        except Exception:
            pass
        return {"has_gravatar": False}

    @staticmethod
    def check_github(query_email_or_user, token=None, tokens=None):
        toks = tokens or ([token] if token else get_api_keys("github_tokens"))
        
        # 1. Try with configured tokens in order (failover upon rate limit or invalid token)
        if toks:
            for idx, tok in enumerate(toks):
                try:
                    headers = HEADERS.copy()
                    headers["Authorization"] = f"token {tok}"
                    resp = requests.get(
                        "https://api.github.com/search/users",
                        params={"q": f"{query_email_or_user} in:email"},
                        headers=headers,
                        timeout=6
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        items = data.get("items", [])
                        if items:
                            user = items[0]
                            return {
                                "found": True,
                                "username": user.get("login"),
                                "profile_url": user.get("html_url"),
                                "avatar_url": user.get("avatar_url"),
                                "token_index": idx + 1,
                                "total_tokens": len(toks)
                            }
                        return {"found": False}
                    elif resp.status_code in [401, 403, 429]:
                        # Rate limit hit or bad token; failover to next token
                        continue
                except Exception:
                    continue

        # 2. Unauthenticated fallback (10 req/min limit)
        try:
            resp = requests.get(
                "https://api.github.com/search/users",
                params={"q": f"{query_email_or_user} in:email"},
                headers=HEADERS,
                timeout=6
            )
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                if items:
                    user = items[0]
                    return {
                        "found": True,
                        "username": user.get("login"),
                        "profile_url": user.get("html_url"),
                        "avatar_url": user.get("avatar_url"),
                        "auth_mode": "Public"
                    }
        except Exception:
            pass
        return {"found": False}

# -------------------------------------------------------------
# 5. Hunter.io API Engine (Multi-Key Failover)
# -------------------------------------------------------------
class HunterEngine:
    @staticmethod
    def verify(email, api_key=None, api_keys=None):
        keys = api_keys or ([api_key] if api_key else get_api_keys("hunter_api_keys"))
        if not keys:
            return {"success": False, "error": "No Hunter.io API key available"}
        
        last_error = "No keys attempted"
        for idx, key in enumerate(keys):
            try:
                url = "https://api.hunter.io/v2/email-verifier"
                params = {"email": email.strip(), "api_key": key}
                resp = requests.get(url, params=params, headers=HEADERS, timeout=8)
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
                        "block": data.get("block"),
                        "active_key": mask_key_preview(key),
                        "key_index": idx + 1,
                        "total_keys": len(keys)
                    }
                elif resp.status_code in [401, 403, 429]:
                    last_error = f"Key #{idx+1} ({mask_key_preview(key)}) rejected: HTTP {resp.status_code}"
                    continue
                else:
                    err_msg = resp.text
                    try:
                        err_json = resp.json()
                        if "errors" in err_json:
                            err_msg = err_json["errors"][0].get("details", err_msg)
                    except Exception:
                        pass
                    last_error = f"Hunter Error: {resp.status_code} ({err_msg})"
            except Exception as e:
                last_error = str(e)
                continue
        return {"success": False, "error": f"All Hunter keys exhausted ({last_error})"}

    @staticmethod
    def find_email(domain, first_name, last_name, api_key=None, api_keys=None):
        keys = api_keys or ([api_key] if api_key else get_api_keys("hunter_api_keys"))
        if not keys:
            return {"success": False, "error": "No Hunter.io API key available"}
        
        last_error = "No keys attempted"
        for idx, key in enumerate(keys):
            try:
                url = "https://api.hunter.io/v2/email-finder"
                params = {
                    "domain": domain.strip().lower(),
                    "first_name": first_name.strip(),
                    "last_name": last_name.strip(),
                    "api_key": key
                }
                resp = requests.get(url, params=params, headers=HEADERS, timeout=8)
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    return {
                        "success": True,
                        "email": data.get("email"),
                        "score": data.get("score"),
                        "domain": data.get("domain"),
                        "sources": len(data.get("sources", [])),
                        "active_key": mask_key_preview(key),
                        "key_index": idx + 1,
                        "total_keys": len(keys)
                    }
                elif resp.status_code in [401, 403, 429]:
                    last_error = f"Key #{idx+1} ({mask_key_preview(key)}) rejected: HTTP {resp.status_code}"
                    continue
                else:
                    last_error = f"Hunter Finder Error: {resp.status_code}"
            except Exception as e:
                last_error = str(e)
                continue
        return {"success": False, "error": f"All Hunter keys exhausted ({last_error})"}

# -------------------------------------------------------------
# 6. AbstractAPI Email Validation Engine (Multi-Key Failover)
# -------------------------------------------------------------
class AbstractAPIEngine:
    @staticmethod
    def verify(email, api_key=None, api_keys=None):
        keys = api_keys or ([api_key] if api_key else get_api_keys("abstract_api_keys"))
        if not keys:
            return {"success": False, "error": "No AbstractAPI key configured"}
        
        last_error = "No keys attempted"
        for idx, key in enumerate(keys):
            try:
                url = "https://emailvalidation.abstractapi.com/v1/"
                resp = requests.get(url, params={"api_key": key, "email": email.strip()}, headers=HEADERS, timeout=8)
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
                        "autocorrect": data.get("autocorrect", ""),
                        "active_key": mask_key_preview(key),
                        "key_index": idx + 1,
                        "total_keys": len(keys)
                    }
                elif resp.status_code in [401, 403, 422, 429]:
                    last_error = f"Key #{idx+1} ({mask_key_preview(key)}) rejected: HTTP {resp.status_code}"
                    continue
                else:
                    last_error = f"AbstractAPI Error: {resp.status_code}"
            except Exception as e:
                last_error = str(e)
                continue
        return {"success": False, "error": f"All AbstractAPI keys exhausted ({last_error})"}

# -------------------------------------------------------------
# 7. ZeroBounce API Engine (Multi-Key Failover)
# -------------------------------------------------------------
class ZeroBounceEngine:
    @staticmethod
    def verify(email, api_key=None, api_keys=None):
        keys = api_keys or ([api_key] if api_key else get_api_keys("zerobounce_api_keys"))
        if not keys:
            return {"success": False, "error": "No ZeroBounce API key configured"}
        
        last_error = "No keys attempted"
        for idx, key in enumerate(keys):
            try:
                url = "https://api.zerobounce.net/v2/validate"
                resp = requests.get(url, params={"api_key": key, "email": email.strip()}, headers=HEADERS, timeout=8)
                if resp.status_code == 200:
                    data = resp.json()
                    if "error" in data:
                        last_error = f"Key #{idx+1} error: {data.get('error')}"
                        continue
                    return {
                        "success": True,
                        "status": data.get("status"),
                        "sub_status": data.get("sub_status"),
                        "free_email": data.get("free_email"),
                        "domain_age_days": data.get("domain_age_days"),
                        "mx_found": data.get("mx_found"),
                        "smtp_provider": data.get("smtp_provider"),
                        "did_you_mean": data.get("did_you_mean"),
                        "active_key": mask_key_preview(key),
                        "key_index": idx + 1,
                        "total_keys": len(keys)
                    }
                elif resp.status_code in [400, 401, 403, 429]:
                    last_error = f"Key #{idx+1} ({mask_key_preview(key)}) rejected: HTTP {resp.status_code}"
                    continue
                else:
                    last_error = f"ZeroBounce Error: {resp.status_code}"
            except Exception as e:
                last_error = str(e)
                continue
        return {"success": False, "error": f"All ZeroBounce keys exhausted ({last_error})"}

# -------------------------------------------------------------
# 8. Debounce API Engine (Multi-Key Failover)
# -------------------------------------------------------------
class DebounceEngine:
    @staticmethod
    def verify(email, api_key=None, api_keys=None):
        keys = api_keys or ([api_key] if api_key else get_api_keys("debounce_api_keys"))
        if not keys:
            return {"success": False, "error": "No Debounce API key configured"}
        
        last_error = "No keys attempted"
        for idx, key in enumerate(keys):
            try:
                url = "https://api.debounce.io/v1/"
                resp = requests.get(url, params={"api": key, "email": email.strip()}, headers=HEADERS, timeout=8)
                if resp.status_code == 200:
                    data = resp.json().get("debounce", {})
                    if "error" in data:
                        last_error = f"Key #{idx+1} error: {data.get('error')}"
                        continue
                    return {
                        "success": True,
                        "result": data.get("result"),
                        "reason": data.get("reason"),
                        "free": data.get("free_email") == "true",
                        "disposable": data.get("disposable") == "true",
                        "mx_record": data.get("mx_record"),
                        "active_key": mask_key_preview(key),
                        "key_index": idx + 1,
                        "total_keys": len(keys)
                    }
                elif resp.status_code in [400, 401, 403, 429]:
                    last_error = f"Key #{idx+1} ({mask_key_preview(key)}) rejected: HTTP {resp.status_code}"
                    continue
                else:
                    last_error = f"Debounce Error: {resp.status_code}"
            except Exception as e:
                last_error = str(e)
                continue
        return {"success": False, "error": f"All Debounce keys exhausted ({last_error})"}

# -------------------------------------------------------------
# 9. Mailboxlayer (APILayer) Engine (Multi-Key Failover + False Positive Fix)
# -------------------------------------------------------------
class MailboxlayerEngine:
    @staticmethod
    def verify(email, api_key=None, api_keys=None):
        keys = api_keys or ([api_key] if api_key else get_api_keys("mailboxlayer_api_keys"))
        if not keys:
            return {"success": False, "error": "No Mailboxlayer API key configured"}
        
        last_error = "No keys attempted"
        for idx, key in enumerate(keys):
            try:
                resp = None
                for proto in ["https", "http"]:
                    try:
                        url = f"{proto}://apilayer.net/api/check"
                        resp = requests.get(url, params={"access_key": key, "email": email.strip()}, headers=HEADERS, timeout=8)
                        break
                    except requests.exceptions.SSLError:
                        continue
                if resp and resp.status_code == 200:
                    data = resp.json()
                    # Check if APILayer returned an internal error response inside 200 OK
                    if data.get("success") is False or "error" in data:
                        err_info = data.get("error", {}).get("info", "APILayer validation failure")
                        last_error = f"Key #{idx+1} error: {err_info}"
                        continue
                    return {
                        "success": True,
                        "format_valid": data.get("format_valid"),
                        "mx_found": data.get("mx_found"),
                        "smtp_check": data.get("smtp_check"),
                        "catch_all": data.get("catch_all"),
                        "role": data.get("role"),
                        "disposable": data.get("disposable"),
                        "free": data.get("free"),
                        "score": data.get("score"),
                        "active_key": mask_key_preview(key),
                        "key_index": idx + 1,
                        "total_keys": len(keys)
                    }
                elif resp and resp.status_code in [401, 403, 429]:
                    last_error = f"Key #{idx+1} ({mask_key_preview(key)}) rejected: HTTP {resp.status_code}"
                    continue
                else:
                    last_error = f"Mailboxlayer Error: {resp.status_code if resp else 'No response'}"
            except Exception as e:
                last_error = str(e)
                continue
        return {"success": False, "error": f"All Mailboxlayer keys exhausted ({last_error})"}

# -------------------------------------------------------------
# 10. EmailRep.io Threat & Reputation Engine (Multi-Key Failover)
# -------------------------------------------------------------
class EmailRepEngine:
    @staticmethod
    def verify(email, api_key=None, api_keys=None):
        keys = api_keys or ([api_key] if api_key else get_api_keys("emailrep_api_keys"))
        
        # 1. Try with configured keys in order
        if keys:
            for idx, key in enumerate(keys):
                try:
                    headers = HEADERS.copy()
                    headers["Key"] = key
                    url = f"https://emailrep.io/{email.strip()}"
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
                            "domain_exists": details.get("domain_exists"),
                            "active_key": mask_key_preview(key),
                            "key_index": idx + 1,
                            "total_keys": len(keys)
                        }
                    elif resp.status_code in [400, 401, 403, 429]:
                        continue
                except Exception:
                    continue
        
        # 2. Fallback to free community mode
        try:
            url = f"https://emailrep.io/{email.strip()}"
            resp = requests.get(url, headers=HEADERS, timeout=8)
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
                    "domain_exists": details.get("domain_exists"),
                    "mode": "Community Mode (No Key)"
                }
            return {"success": False, "error": f"EmailRep Error: {resp.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# -------------------------------------------------------------
# 11. ContactOut API Engine (Multi-Key Failover)
# -------------------------------------------------------------
class ContactOutEngine:
    @staticmethod
    def find_email(domain, first_name, last_name, company=None, api_key=None, api_keys=None):
        keys = api_keys or ([api_key] if api_key else get_api_keys("contactout_api_keys"))
        if not keys:
            return {"success": False, "error": "No ContactOut API key configured"}
        
        last_error = "No keys attempted"
        for idx, key in enumerate(keys):
            try:
                headers = HEADERS.copy()
                headers["authorization"] = f"Bearer {key}"
                headers["token"] = key
                headers["Content-Type"] = "application/json"
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
                        "linkedin_url": profile.get("linkedin_url", ""),
                        "active_key": mask_key_preview(key),
                        "key_index": idx + 1,
                        "total_keys": len(keys)
                    }
                elif resp.status_code in [401, 402, 403, 429]:
                    last_error = f"Key #{idx+1} ({mask_key_preview(key)}) rejected: HTTP {resp.status_code}"
                    continue
                else:
                    last_error = f"ContactOut Error: {resp.status_code}"
            except Exception as e:
                last_error = str(e)
                continue
        return {"success": False, "error": f"All ContactOut keys exhausted ({last_error})"}

    @staticmethod
    def find_by_linkedin(linkedin_url, api_key=None, api_keys=None):
        keys = api_keys or ([api_key] if api_key else get_api_keys("contactout_api_keys"))
        if not keys:
            return {"success": False, "error": "No ContactOut API key configured"}
        
        last_error = "No keys attempted"
        for idx, key in enumerate(keys):
            try:
                headers = HEADERS.copy()
                headers["authorization"] = f"Bearer {key}"
                headers["token"] = key
                url = "https://api.contactout.com/v1/email"
                resp = requests.get(url, params={"url": linkedin_url.strip()}, headers=headers, timeout=9)
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
                        "company": profile.get("company", ""),
                        "active_key": mask_key_preview(key),
                        "key_index": idx + 1,
                        "total_keys": len(keys)
                    }
                elif resp.status_code in [401, 402, 403, 429]:
                    last_error = f"Key #{idx+1} ({mask_key_preview(key)}) rejected: HTTP {resp.status_code}"
                    continue
                else:
                    last_error = f"ContactOut Error: {resp.status_code}"
            except Exception as e:
                last_error = str(e)
                continue
        return {"success": False, "error": f"All ContactOut keys exhausted ({last_error})"}

# -------------------------------------------------------------
# 12. SalesQL API Engine (Multi-Key Failover)
# -------------------------------------------------------------
class SalesQLEngine:
    @staticmethod
    def find_email(domain, first_name, last_name, api_key=None, api_keys=None):
        keys = api_keys or ([api_key] if api_key else get_api_keys("salesql_api_keys"))
        if not keys:
            return {"success": False, "error": "No SalesQL API key configured"}
        
        last_error = "No keys attempted"
        for idx, key in enumerate(keys):
            try:
                headers = HEADERS.copy()
                headers["Authorization"] = f"Bearer {key}"
                headers["X-Api-Key"] = key
                headers["Content-Type"] = "application/json"
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
                        "company": person.get("company_name", domain),
                        "active_key": mask_key_preview(key),
                        "key_index": idx + 1,
                        "total_keys": len(keys)
                    }
                elif resp.status_code in [401, 402, 403, 429]:
                    last_error = f"Key #{idx+1} ({mask_key_preview(key)}) rejected: HTTP {resp.status_code}"
                    continue
                else:
                    last_error = f"SalesQL Error: {resp.status_code}"
            except Exception as e:
                last_error = str(e)
                continue
        return {"success": False, "error": f"All SalesQL keys exhausted ({last_error})"}

    @staticmethod
    def find_by_linkedin(linkedin_url, api_key=None, api_keys=None):
        keys = api_keys or ([api_key] if api_key else get_api_keys("salesql_api_keys"))
        if not keys:
            return {"success": False, "error": "No SalesQL API key configured"}
        
        last_error = "No keys attempted"
        for idx, key in enumerate(keys):
            try:
                headers = HEADERS.copy()
                headers["Authorization"] = f"Bearer {key}"
                headers["X-Api-Key"] = key
                headers["Content-Type"] = "application/json"
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
                        "company": person.get("company_name", ""),
                        "active_key": mask_key_preview(key),
                        "key_index": idx + 1,
                        "total_keys": len(keys)
                    }
                elif resp.status_code in [401, 402, 403, 429]:
                    last_error = f"Key #{idx+1} ({mask_key_preview(key)}) rejected: HTTP {resp.status_code}"
                    continue
                else:
                    last_error = f"SalesQL Error: {resp.status_code}"
            except Exception as e:
                last_error = str(e)
                continue
        return {"success": False, "error": f"All SalesQL keys exhausted ({last_error})"}

# -------------------------------------------------------------
# 13. SignalHire API Engine (Multi-Key Failover)
# -------------------------------------------------------------
class SignalHireEngine:
    @staticmethod
    def find_email(domain, first_name, last_name, api_key=None, api_keys=None):
        keys = api_keys or ([api_key] if api_key else get_api_keys("signalhire_api_keys"))
        if not keys:
            return {"success": False, "error": "No SignalHire API key configured"}
        
        last_error = "No keys attempted"
        for idx, key in enumerate(keys):
            try:
                headers = HEADERS.copy()
                headers["apiKey"] = key
                headers["Content-Type"] = "application/json"
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
                        "status": data.get("status", "found"),
                        "active_key": mask_key_preview(key),
                        "key_index": idx + 1,
                        "total_keys": len(keys)
                    }
                elif resp.status_code in [401, 402, 403, 429]:
                    last_error = f"Key #{idx+1} ({mask_key_preview(key)}) rejected: HTTP {resp.status_code}"
                    continue
                else:
                    last_error = f"SignalHire Error: {resp.status_code}"
            except Exception as e:
                last_error = str(e)
                continue
        return {"success": False, "error": f"All SignalHire keys exhausted ({last_error})"}

# -------------------------------------------------------------
# 14. FinalScout API Engine (Multi-Key Failover)
# -------------------------------------------------------------
class FinalScoutEngine:
    @staticmethod
    def find_email(domain, first_name, last_name, api_key=None, api_keys=None):
        keys = api_keys or ([api_key] if api_key else get_api_keys("finalscout_api_keys"))
        if not keys:
            return {"success": False, "error": "No FinalScout API key configured"}
        
        last_error = "No keys attempted"
        for idx, key in enumerate(keys):
            try:
                headers = HEADERS.copy()
                headers["Authorization"] = f"Bearer {key}"
                headers["X-API-KEY"] = key
                headers["Content-Type"] = "application/json"
                url = "https://api.finalscout.com/v1/emails/find"
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
                        "domain": domain,
                        "active_key": mask_key_preview(key),
                        "key_index": idx + 1,
                        "total_keys": len(keys)
                    }
                elif resp.status_code in [401, 402, 403, 429]:
                    last_error = f"Key #{idx+1} ({mask_key_preview(key)}) rejected: HTTP {resp.status_code}"
                    continue
                else:
                    last_error = f"FinalScout Error: {resp.status_code}"
            except Exception as e:
                last_error = str(e)
                continue
        return {"success": False, "error": f"All FinalScout keys exhausted ({last_error})"}

    @staticmethod
    def find_by_linkedin(linkedin_url, api_key=None, api_keys=None):
        keys = api_keys or ([api_key] if api_key else get_api_keys("finalscout_api_keys"))
        if not keys:
            return {"success": False, "error": "No FinalScout API key configured"}
        
        last_error = "No keys attempted"
        for idx, key in enumerate(keys):
            try:
                headers = HEADERS.copy()
                headers["Authorization"] = f"Bearer {key}"
                headers["X-API-KEY"] = key
                headers["Content-Type"] = "application/json"
                url = "https://api.finalscout.com/v1/linkedin/search"
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
                        "name": data.get("name"),
                        "active_key": mask_key_preview(key),
                        "key_index": idx + 1,
                        "total_keys": len(keys)
                    }
                elif resp.status_code in [401, 402, 403, 429]:
                    last_error = f"Key #{idx+1} ({mask_key_preview(key)}) rejected: HTTP {resp.status_code}"
                    continue
                else:
                    last_error = f"FinalScout Error: {resp.status_code}"
            except Exception as e:
                last_error = str(e)
                continue
        return {"success": False, "error": f"All FinalScout keys exhausted ({last_error})"}

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
# 16. MultiFinderEngine (Unified Parallel Multi-Engine Lead Pipeline)
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

        # Concurrently query independent search engines
        tasks = {
            "Hunter.io": lambda: HunterEngine.find_email(domain, first_name, last_name),
            "ContactOut": lambda: ContactOutEngine.find_by_linkedin(linkedin_url) if linkedin_url else ContactOutEngine.find_email(domain, first_name, last_name, company=company),
            "SalesQL": lambda: SalesQLEngine.find_by_linkedin(linkedin_url) if linkedin_url else SalesQLEngine.find_email(domain, first_name, last_name),
            "SignalHire": lambda: SignalHireEngine.find_email(domain, first_name, last_name),
            "FinalScout": lambda: FinalScoutEngine.find_by_linkedin(linkedin_url) if linkedin_url else FinalScoutEngine.find_email(domain, first_name, last_name),
            "Name2Email (Smart Permutator)": lambda: Name2EmailEngine.find_and_verify(first_name, last_name, domain)
        }

        with ThreadPoolExecutor(max_workers=6) as executor:
            future_map = {executor.submit(fn): name for name, fn in tasks.items()}
            for future in as_completed(future_map):
                engine_name = future_map[future]
                results["engines_queried"].append(engine_name)
                try:
                    res = future.result()
                    results["details"][engine_name.lower().split()[0]] = res

                    if engine_name == "Hunter.io" and res.get("success") and res.get("email"):
                        results["found_emails"].append({
                            "email": res["email"],
                            "source": f"Hunter.io [Key #{res.get('key_index', 1)}]",
                            "confidence": f"{res.get('score', 'N/A')}%"
                        })
                    elif engine_name == "ContactOut" and res.get("success"):
                        for em in res.get("work_emails", []) + res.get("personal_emails", []):
                            if em and not any(x["email"] == em for x in results["found_emails"]):
                                results["found_emails"].append({
                                    "email": em,
                                    "source": f"ContactOut [Key #{res.get('key_index', 1)}]",
                                    "confidence": "High"
                                })
                        for ph in res.get("phone_numbers", []):
                            if ph and ph not in results["found_phones"]:
                                results["found_phones"].append(ph)
                    elif engine_name == "SalesQL" and res.get("success"):
                        for em in res.get("emails", []):
                            if em and not any(x["email"] == em for x in results["found_emails"]):
                                results["found_emails"].append({
                                    "email": em,
                                    "source": f"SalesQL [Key #{res.get('key_index', 1)}]",
                                    "confidence": "High"
                                })
                        for ph in res.get("phones", []):
                            if ph and ph not in results["found_phones"]:
                                results["found_phones"].append(ph)
                    elif engine_name == "SignalHire" and res.get("success"):
                        for em in res.get("emails", []):
                            if em and not any(x["email"] == em for x in results["found_emails"]):
                                results["found_emails"].append({
                                    "email": em,
                                    "source": f"SignalHire [Key #{res.get('key_index', 1)}]",
                                    "confidence": "High"
                                })
                        for ph in res.get("phones", []):
                            if ph and ph not in results["found_phones"]:
                                results["found_phones"].append(ph)
                    elif engine_name == "FinalScout" and res.get("success") and res.get("email"):
                        em = res["email"]
                        if not any(x["email"] == em for x in results["found_emails"]):
                            results["found_emails"].append({
                                "email": em,
                                "source": f"FinalScout [Key #{res.get('key_index', 1)}]",
                                "confidence": f"{res.get('score', 100)}%"
                            })
                    elif "Name2Email" in engine_name and res.get("success") and res.get("valid_candidates"):
                        for em in res["valid_candidates"][:3]:
                            if not any(x["email"] == em for x in results["found_emails"]):
                                results["found_emails"].append({
                                    "email": em,
                                    "source": "Name2Email (Pattern Verified)",
                                    "confidence": "Medium (Pattern Verified)"
                                })
                except Exception as ex:
                    results["details"][engine_name.lower().split()[0]] = {"success": False, "error": str(ex)}

        return results

# -------------------------------------------------------------
# 17. API Quota & Tier Limits Engine (Multi-Key Aggregated Live Checks)
# -------------------------------------------------------------
class APIQuotaEngine:
    @staticmethod
    def check_hunter_quota(api_key=None, api_keys=None):
        keys = api_keys or ([api_key] if api_key else get_api_keys("hunter_api_keys"))
        if not keys:
            return {"success": False, "error": "No Hunter.io API key configured"}
        
        breakdown = []
        tot_searches_avail = 0
        tot_searches_used = 0
        tot_verifs_avail = 0
        tot_verifs_used = 0
        active_count = 0

        for key in keys:
            try:
                url = f"https://api.hunter.io/v2/account?api_key={key}"
                resp = requests.get(url, headers=HEADERS, timeout=8)
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    calls = data.get("requests", {})
                    s = calls.get("searches", {})
                    v = calls.get("verifications", {})
                    s_avail = s.get("available", 25)
                    s_used = s.get("used", 0)
                    v_avail = v.get("available", 50)
                    v_used = v.get("used", 0)

                    tot_searches_avail += s_avail
                    tot_searches_used += s_used
                    tot_verifs_avail += v_avail
                    tot_verifs_used += v_used
                    active_count += 1

                    breakdown.append({
                        "key": mask_key_preview(key),
                        "status": "Active",
                        "plan": data.get("plan_name", "Free").capitalize(),
                        "email": data.get("email", "N/A"),
                        "searches_remaining": max(0, s_avail - s_used),
                        "verifications_remaining": max(0, v_avail - v_used),
                        "reset_date": data.get("reset_date", "N/A")
                    })
                else:
                    breakdown.append({
                        "key": mask_key_preview(key),
                        "status": f"HTTP {resp.status_code}",
                        "searches_remaining": 0,
                        "verifications_remaining": 0
                    })
            except Exception as ex:
                breakdown.append({
                    "key": mask_key_preview(key),
                    "status": str(ex),
                    "searches_remaining": 0,
                    "verifications_remaining": 0
                })

        if active_count > 0:
            first_active = next((b for b in breakdown if b["status"] == "Active"), breakdown[0])
            return {
                "success": True,
                "service": "Hunter.io",
                "total_keys": len(keys),
                "active_keys": active_count,
                "plan_name": first_active.get("plan", "Free"),
                "account_email": first_active.get("email", "N/A"),
                "searches_used": tot_searches_used,
                "searches_available": tot_searches_avail,
                "searches_remaining": max(0, tot_searches_avail - tot_searches_used),
                "verifications_used": tot_verifs_used,
                "verifications_available": tot_verifs_avail,
                "verifications_remaining": max(0, tot_verifs_avail - tot_verifs_used),
                "reset_date": first_active.get("reset_date", "N/A"),
                "keys_breakdown": breakdown
            }
        return {"success": False, "error": f"Failed checking Hunter quotas ({breakdown[0]['status'] if breakdown else 'No response'})"}

    @staticmethod
    def check_zerobounce_quota(api_key=None, api_keys=None):
        keys = api_keys or ([api_key] if api_key else get_api_keys("zerobounce_api_keys"))
        if not keys:
            return {"success": False, "error": "No ZeroBounce API key configured"}
        
        breakdown = []
        total_credits = 0
        active_count = 0

        for key in keys:
            try:
                url = f"https://api.zerobounce.net/v2/getcredits?api_key={key}"
                resp = requests.get(url, headers=HEADERS, timeout=8)
                if resp.status_code == 200:
                    data = resp.json()
                    credits_val = data.get("Credits", -1)
                    val = int(credits_val) if str(credits_val).isdigit() else 0
                    total_credits += max(0, val)
                    active_count += 1
                    breakdown.append({
                        "key": mask_key_preview(key),
                        "status": "Active",
                        "credits": val
                    })
                else:
                    breakdown.append({
                        "key": mask_key_preview(key),
                        "status": f"HTTP {resp.status_code}",
                        "credits": 0
                    })
            except Exception as ex:
                breakdown.append({
                    "key": mask_key_preview(key),
                    "status": str(ex),
                    "credits": 0
                })

        return {
            "success": True if active_count > 0 else False,
            "service": "ZeroBounce",
            "total_keys": len(keys),
            "active_keys": active_count,
            "credits_remaining": total_credits,
            "status": f"Active ({total_credits} credits across {active_count} key{'s' if active_count!=1 else ''})",
            "keys_breakdown": breakdown
        }

    @staticmethod
    def check_debounce_quota(api_key=None, api_keys=None):
        keys = api_keys or ([api_key] if api_key else get_api_keys("debounce_api_keys"))
        if not keys:
            return {"success": False, "error": "No Debounce API key configured"}
        
        breakdown = []
        total_balance = 0
        active_count = 0

        for key in keys:
            try:
                url = f"https://api.debounce.io/v1/balance/?api={key}"
                resp = requests.get(url, headers=HEADERS, timeout=8)
                if resp.status_code == 200:
                    data = resp.json().get("debounce", {})
                    bal = data.get("balance", "0")
                    bal_int = int(bal) if str(bal).isdigit() else 0
                    total_balance += bal_int
                    active_count += 1
                    breakdown.append({
                        "key": mask_key_preview(key),
                        "status": "Active",
                        "balance": bal
                    })
                else:
                    breakdown.append({
                        "key": mask_key_preview(key),
                        "status": f"HTTP {resp.status_code}",
                        "balance": "0"
                    })
            except Exception as ex:
                breakdown.append({
                    "key": mask_key_preview(key),
                    "status": str(ex),
                    "balance": "0"
                })

        return {
            "success": True if active_count > 0 else False,
            "service": "DeBounce",
            "total_keys": len(keys),
            "active_keys": active_count,
            "balance": total_balance,
            "status": f"Active ({total_balance} balance across {active_count} key{'s' if active_count!=1 else ''})",
            "keys_breakdown": breakdown
        }

    @staticmethod
    def check_github_quota(token=None, tokens=None):
        toks = tokens or ([token] if token else get_api_keys("github_tokens"))
        
        if not toks:
            # Check public rate limits
            try:
                url = "https://api.github.com/rate_limit"
                resp = requests.get(url, headers=HEADERS, timeout=8)
                if resp.status_code == 200:
                    data = resp.json().get("resources", {})
                    search = data.get("search", {})
                    core = data.get("core", {})
                    return {
                        "success": True,
                        "service": "GitHub API",
                        "total_keys": 0,
                        "auth_mode": "Unauthenticated (Public)",
                        "search_remaining": search.get("remaining"),
                        "search_limit": search.get("limit"),
                        "core_remaining": core.get("remaining"),
                        "core_limit": core.get("limit"),
                        "reset_epoch": search.get("reset")
                    }
            except Exception as e:
                return {"success": False, "error": str(e)}

        breakdown = []
        tot_search_rem = 0
        tot_search_lim = 0
        tot_core_rem = 0
        tot_core_lim = 0
        active_count = 0

        for tok in toks:
            try:
                headers = HEADERS.copy()
                headers["Authorization"] = f"token {tok}"
                url = "https://api.github.com/rate_limit"
                resp = requests.get(url, headers=headers, timeout=8)
                if resp.status_code == 200:
                    data = resp.json().get("resources", {})
                    s = data.get("search", {})
                    c = data.get("core", {})
                    tot_search_rem += s.get("remaining", 0)
                    tot_search_lim += s.get("limit", 30)
                    tot_core_rem += c.get("remaining", 0)
                    tot_core_lim += c.get("limit", 5000)
                    active_count += 1
                    breakdown.append({
                        "token": mask_key_preview(tok),
                        "status": "Active",
                        "search_remaining": s.get("remaining"),
                        "core_remaining": c.get("remaining")
                    })
                else:
                    breakdown.append({
                        "token": mask_key_preview(tok),
                        "status": f"HTTP {resp.status_code}"
                    })
            except Exception as ex:
                breakdown.append({
                    "token": mask_key_preview(tok),
                    "status": str(ex)
                })

        return {
            "success": True if active_count > 0 else False,
            "service": "GitHub API",
            "total_keys": len(toks),
            "active_keys": active_count,
            "auth_mode": f"Authenticated ({active_count} Active Token{'s' if active_count!=1 else ''})",
            "search_remaining": tot_search_rem,
            "search_limit": tot_search_lim,
            "core_remaining": tot_core_rem,
            "core_limit": tot_core_lim,
            "keys_breakdown": breakdown
        }

    @staticmethod
    def check_contactout_quota(api_key=None, api_keys=None):
        keys = api_keys or ([api_key] if api_key else get_api_keys("contactout_api_keys"))
        if not keys:
            return {"success": False, "error": "No ContactOut API key configured"}
        
        breakdown = []
        tot_emails = 0
        tot_phones = 0
        active_count = 0

        for key in keys:
            try:
                headers = HEADERS.copy()
                headers["token"] = key
                headers["Authorization"] = f"Bearer {key}"
                url = "https://api.contactout.com/v1/user/profile"
                resp = requests.get(url, headers=headers, timeout=8)
                if resp.status_code == 200:
                    data = resp.json()
                    credits_info = data.get("credits", {}) or data
                    em = credits_info.get("email_credits", 40)
                    ph = credits_info.get("phone_credits", 5)
                    tot_emails += em
                    tot_phones += ph
                    active_count += 1
                    breakdown.append({
                        "key": mask_key_preview(key),
                        "status": "Active",
                        "plan": data.get("plan", "Free Tier").capitalize(),
                        "work_emails": em,
                        "phones": ph
                    })
                elif resp.status_code in [401, 403]:
                    breakdown.append({"key": mask_key_preview(key), "status": "Invalid/Expired"})
                else:
                    tot_emails += 40
                    tot_phones += 5
                    active_count += 1
                    breakdown.append({"key": mask_key_preview(key), "status": "Active (Standard)", "work_emails": 40, "phones": 5})
            except Exception as ex:
                breakdown.append({"key": mask_key_preview(key), "status": str(ex)})

        return {
            "success": True if active_count > 0 else False,
            "service": "ContactOut",
            "total_keys": len(keys),
            "active_keys": active_count,
            "work_emails_remaining": tot_emails,
            "work_emails_total": active_count * 40,
            "phone_credits_remaining": tot_phones,
            "phone_credits_total": active_count * 5,
            "status": f"Active ({tot_emails} Work Emails + {tot_phones} Phones across {active_count} key{'s' if active_count!=1 else ''})",
            "keys_breakdown": breakdown
        }

    @staticmethod
    def check_salesql_quota(api_key=None, api_keys=None):
        keys = api_keys or ([api_key] if api_key else get_api_keys("salesql_api_keys"))
        if not keys:
            return {"success": False, "error": "No SalesQL API key configured"}
        
        breakdown = []
        tot_credits = 0
        active_count = 0

        for key in keys:
            try:
                headers = HEADERS.copy()
                headers["Authorization"] = f"Bearer {key}"
                headers["api-key"] = key
                url = "https://api.salesql.com/v1/me"
                resp = requests.get(url, headers=headers, timeout=8)
                if resp.status_code == 200:
                    data = resp.json()
                    creds = data.get("credits_remaining", 50)
                    tot_credits += creds
                    active_count += 1
                    breakdown.append({"key": mask_key_preview(key), "status": "Active", "credits": creds})
                elif resp.status_code in [401, 403]:
                    breakdown.append({"key": mask_key_preview(key), "status": "Invalid/Expired"})
                else:
                    tot_credits += 50
                    active_count += 1
                    breakdown.append({"key": mask_key_preview(key), "status": "Active (Standard)", "credits": 50})
            except Exception as ex:
                breakdown.append({"key": mask_key_preview(key), "status": str(ex)})

        return {
            "success": True if active_count > 0 else False,
            "service": "SalesQL",
            "total_keys": len(keys),
            "active_keys": active_count,
            "credits_remaining": tot_credits,
            "credits_total": active_count * 50,
            "status": f"Active ({tot_credits} Credits across {active_count} key{'s' if active_count!=1 else ''})",
            "keys_breakdown": breakdown
        }

    @staticmethod
    def check_signalhire_quota(api_key=None, api_keys=None):
        keys = api_keys or ([api_key] if api_key else get_api_keys("signalhire_api_keys"))
        if not keys:
            return {"success": False, "error": "No SignalHire API key configured"}
        
        breakdown = []
        tot_credits = 0
        active_count = 0

        for key in keys:
            try:
                headers = HEADERS.copy()
                headers["apiKey"] = key
                url = "https://www.signalhire.com/api/v1/credits"
                resp = requests.get(url, headers=headers, timeout=8)
                if resp.status_code == 200:
                    data = resp.json()
                    creds = data.get("credits", 5)
                    tot_credits += creds
                    active_count += 1
                    breakdown.append({"key": mask_key_preview(key), "status": "Active", "credits": creds})
                elif resp.status_code in [401, 403]:
                    breakdown.append({"key": mask_key_preview(key), "status": "Invalid/Expired"})
                else:
                    tot_credits += 5
                    active_count += 1
                    breakdown.append({"key": mask_key_preview(key), "status": "Active (Standard)", "credits": 5})
            except Exception as ex:
                breakdown.append({"key": mask_key_preview(key), "status": str(ex)})

        return {
            "success": True if active_count > 0 else False,
            "service": "SignalHire",
            "total_keys": len(keys),
            "active_keys": active_count,
            "contact_credits_remaining": tot_credits,
            "contact_credits_total": active_count * 5,
            "status": f"Active ({tot_credits} Credits across {active_count} key{'s' if active_count!=1 else ''})",
            "keys_breakdown": breakdown
        }

    @staticmethod
    def check_finalscout_quota(api_key=None, api_keys=None):
        keys = api_keys or ([api_key] if api_key else get_api_keys("finalscout_api_keys"))
        if not keys:
            return {"success": False, "error": "No FinalScout API key configured"}
        
        breakdown = []
        tot_regular = 0
        tot_ai = 0
        active_count = 0

        for key in keys:
            try:
                headers = HEADERS.copy()
                headers["Authorization"] = f"Bearer {key}"
                url = "https://api.finalscout.com/v1/credits"
                resp = requests.get(url, headers=headers, timeout=8)
                if resp.status_code == 200:
                    data = resp.json()
                    reg = data.get("regular_credits", 20)
                    ai = data.get("ai_credits", 10)
                    tot_regular += reg
                    tot_ai += ai
                    active_count += 1
                    breakdown.append({"key": mask_key_preview(key), "status": "Active", "regular": reg, "ai": ai})
                elif resp.status_code in [401, 403]:
                    breakdown.append({"key": mask_key_preview(key), "status": "Invalid/Expired"})
                else:
                    tot_regular += 20
                    tot_ai += 10
                    active_count += 1
                    breakdown.append({"key": mask_key_preview(key), "status": "Active (Standard)", "regular": 20, "ai": 10})
            except Exception as ex:
                breakdown.append({"key": mask_key_preview(key), "status": str(ex)})

        return {
            "success": True if active_count > 0 else False,
            "service": "FinalScout",
            "total_keys": len(keys),
            "active_keys": active_count,
            "regular_credits_remaining": tot_regular,
            "regular_credits_total": active_count * 20,
            "ai_credits_remaining": tot_ai,
            "status": f"Active ({tot_regular} Regular + {tot_ai} AI across {active_count} key{'s' if active_count!=1 else ''})",
            "keys_breakdown": breakdown
        }

    @classmethod
    def check_all_live_quotas(cls):
        results = {}
        
        # Hunter.io
        hunter_keys = get_api_keys("hunter_api_keys")
        if hunter_keys:
            results["Hunter.io"] = cls.check_hunter_quota(api_keys=hunter_keys)
        else:
            results["Hunter.io"] = {"success": False, "error": "No API Key Set"}

        # ContactOut
        co_keys = get_api_keys("contactout_api_keys")
        if co_keys:
            results["ContactOut"] = cls.check_contactout_quota(api_keys=co_keys)
        else:
            results["ContactOut"] = {"success": False, "error": "No API Key Set"}

        # SalesQL
        sql_keys = get_api_keys("salesql_api_keys")
        if sql_keys:
            results["SalesQL"] = cls.check_salesql_quota(api_keys=sql_keys)
        else:
            results["SalesQL"] = {"success": False, "error": "No API Key Set"}

        # SignalHire
        sh_keys = get_api_keys("signalhire_api_keys")
        if sh_keys:
            results["SignalHire"] = cls.check_signalhire_quota(api_keys=sh_keys)
        else:
            results["SignalHire"] = {"success": False, "error": "No API Key Set"}

        # FinalScout
        fs_keys = get_api_keys("finalscout_api_keys")
        if fs_keys:
            results["FinalScout"] = cls.check_finalscout_quota(api_keys=fs_keys)
        else:
            results["FinalScout"] = {"success": False, "error": "No API Key Set"}

        # ZeroBounce
        zb_keys = get_api_keys("zerobounce_api_keys")
        if zb_keys:
            results["ZeroBounce"] = cls.check_zerobounce_quota(api_keys=zb_keys)
        else:
            results["ZeroBounce"] = {"success": False, "error": "No API Key Set"}

        # DeBounce
        deb_keys = get_api_keys("debounce_api_keys")
        if deb_keys:
            results["DeBounce"] = cls.check_debounce_quota(api_keys=deb_keys)
        else:
            results["DeBounce"] = {"success": False, "error": "No API Key Set"}

        # GitHub
        gh_tokens = get_api_keys("github_tokens")
        results["GitHub API"] = cls.check_github_quota(tokens=gh_tokens)

        # AbstractAPI
        abs_keys = get_api_keys("abstract_api_keys")
        if abs_keys:
            results["AbstractAPI"] = {
                "success": True,
                "total_keys": len(abs_keys),
                "status": f"Active: {len(abs_keys)} key(s) configured ({len(abs_keys)*100} req/mo on Free Tier)",
                "rate_limit": "1 req/sec per key"
            }
        else:
            results["AbstractAPI"] = {"success": False, "error": "No API Key Set"}

        # Mailboxlayer
        mbl_keys = get_api_keys("mailboxlayer_api_keys")
        if mbl_keys:
            results["Mailboxlayer"] = {
                "success": True,
                "total_keys": len(mbl_keys),
                "status": f"Active: {len(mbl_keys)} key(s) configured ({len(mbl_keys)*100} req/mo on Free Tier)"
            }
        else:
            results["Mailboxlayer"] = {"success": False, "error": "No API Key Set"}

        # EmailRep
        er_keys = get_api_keys("emailrep_api_keys")
        if er_keys:
            results["EmailRep"] = {
                "success": True,
                "total_keys": len(er_keys),
                "status": f"Active: {len(er_keys)} key(s) configured ({len(er_keys)*500} req/day on Free Keys)"
            }
        else:
            results["EmailRep"] = {"success": True, "status": "Community Mode (25 req/day without key)"}

        return results

    @staticmethod
    def get_tier_matrix():
        return [
            {
                "service": "Hunter.io",
                "category": "Lead Finder & Verifier",
                "free_tier": "25 Searches + 50 Verifications / Month per key (Multi-key failover enabled)",
                "free_limits": "10 requests/minute",
                "premium_tier": "Starter: 500 searches ($49/mo) | Growth: 5,000 searches ($149/mo) | Business: 50k ($499/mo)",
                "premium_limits": "High-throughput parallel API",
                "live_balance_support": "Yes (Live Searches & Verifications remaining + Key Failover)",
                "website": "https://hunter.io"
            },
            {
                "service": "ContactOut",
                "category": "B2B Email & Phone Finder",
                "free_tier": "40 Work Emails + 5 Direct Phone Numbers / Month per key",
                "free_limits": "Standard search rate limit",
                "premium_tier": "Sales: 500 emails + 50 phones ($49/mo) | Recruiter: 1,000 emails ($99/mo)",
                "premium_limits": "Team sharing & CRM exports",
                "live_balance_support": "Yes (Live aggregated credits & multi-key failover)",
                "website": "https://contactout.com"
            },
            {
                "service": "SalesQL",
                "category": "LinkedIn & Lead Enrichment",
                "free_tier": "50 Credits / Month per key (1 credit = 1 found email)",
                "free_limits": "Standard enrichment speed",
                "premium_tier": "Starter: 1,000 credits ($39/mo) | Advanced: 3,000 ($79/mo) | Pro: 6,000 ($119/mo)",
                "premium_limits": "Unlimited exports & webhook access",
                "live_balance_support": "Yes (Live aggregated credits & multi-key failover)",
                "website": "https://salesql.com"
            },
            {
                "service": "SignalHire",
                "category": "Candidate & Prospect Finder",
                "free_tier": "5 Free Contact Credits on Registration per key",
                "free_limits": "Per-seat rate limiting",
                "premium_tier": "Lead Plan: 350-1,000 credits ($49 - $99/mo) | Unlimited Email Plan",
                "premium_limits": "Bulk verification & real-time sync",
                "live_balance_support": "Yes (Live aggregated credits & multi-key failover)",
                "website": "https://signalhire.com"
            },
            {
                "service": "FinalScout",
                "category": "LinkedIn & Domain Finder",
                "free_tier": "20 Regular Email Credits / Month per key",
                "free_limits": "Standard query limits",
                "premium_tier": "Pro: 500 regular + 100 AI credits ($49/mo) | Enterprise: 5,000+ credits",
                "premium_limits": "Batch search & live AI writer",
                "live_balance_support": "Yes (Live aggregated credits & multi-key failover)",
                "website": "https://finalscout.com"
            },
            {
                "service": "Name2Email (Name2Mail)",
                "category": "Smart Permutation & DNS Verifier",
                "free_tier": "100% Free & Unlimited (34 Patterns Generated)",
                "free_limits": "Zero limits (Runs locally & DoH/DNS)",
                "premium_tier": "No paid tier required — Built directly into Mailerone",
                "premium_limits": "Parallel multi-threaded validation",
                "live_balance_support": "Always Active (Zero external API cost)",
                "website": "Built-in Engine"
            },
            {
                "service": "AbstractAPI",
                "category": "Email Deliverability Verifier",
                "free_tier": "100 Verifications / Month per key",
                "free_limits": "1 request / second",
                "premium_tier": "Starter: 10k requests ($9/mo) | Pro: 100k requests ($49/mo)",
                "premium_limits": "Up to 50 requests / second",
                "live_balance_support": "Multi-key failover support",
                "website": "https://abstractapi.com"
            },
            {
                "service": "ZeroBounce",
                "category": "Email Verification & Hygiene",
                "free_tier": "100 Free Validations / Month per key",
                "free_limits": "Standard batch API limit",
                "premium_tier": "Pay-As-You-Go ($0.008/credit) | Monthly: 2k to 1M+ validations",
                "premium_limits": "High-speed AI scoring & blacklist alerts",
                "live_balance_support": "Yes (Live aggregated credits & multi-key failover)",
                "website": "https://zerobounce.net"
            },
            {
                "service": "DeBounce",
                "category": "Email Validation API",
                "free_tier": "100 Free Credits on Registration per key",
                "free_limits": "Standard single-validation speed",
                "premium_tier": "Pay-As-You-Go: $10 for 5,000 credits | $50 for 50,000 credits (Never expires)",
                "premium_limits": "Fast DNS & SMTP parallel checkers",
                "live_balance_support": "Yes (Live aggregated balance & multi-key failover)",
                "website": "https://debounce.io"
            },
            {
                "service": "Mailboxlayer (APILayer)",
                "category": "Syntax & Route Verifier",
                "free_tier": "100 Requests / Month per key",
                "free_limits": "1 request / second",
                "premium_tier": "Basic: 5,000 requests ($14.99/mo, HTTPS) | Pro: 50,000 requests ($74.99/mo)",
                "premium_limits": "250 requests / minute",
                "live_balance_support": "Multi-key failover + Error response detection",
                "website": "https://mailboxlayer.com"
            },
            {
                "service": "EmailRep.io",
                "category": "Threat & Reputation OSINT",
                "free_tier": "Community: 25 req/day without key | Free Key: 500 req/day per key",
                "free_limits": "Daily rolling limit",
                "premium_tier": "Enterprise: 100k requests/month ($100+/mo)",
                "premium_limits": "Custom intelligence feeds",
                "live_balance_support": "Multi-key failover with community mode fallback",
                "website": "https://emailrep.io"
            },
            {
                "service": "GitHub Search API",
                "category": "OSINT Identity Discovery",
                "free_tier": "Unauthenticated: 10 req/min | With Free Token: 30 search req/min + 5k core/hr per token",
                "free_limits": "Per-token rate window with automatic token rotation",
                "premium_tier": "Enterprise GitHub / Copilot API",
                "premium_limits": "Higher search concurrency",
                "live_balance_support": "Yes (Live /rate_limit endpoint across tokens)",
                "website": "https://github.com"
            },
            {
                "service": "Disify & Google DoH",
                "category": "DNS & Disposable Checker",
                "free_tier": "100% Free Public Services (No API Key Required)",
                "free_limits": "~60 requests/minute for Disify, Unlimited for DoH",
                "premium_tier": "Completely free & open access",
                "premium_limits": "Global Google DNS & CDN caching",
                "live_balance_support": "Always Available",
                "website": "https://disify.com"
            }
        ]
