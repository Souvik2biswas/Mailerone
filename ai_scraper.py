import re
import json
import html
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from config_manager import get_api_keys, get_api_key

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Common unwanted file extensions matching email-like strings (e.g. icon@2x.png)
FORBIDDEN_EXTENSIONS = {
    "png", "jpg", "jpeg", "gif", "svg", "webp", "ico", "bmp", "tif", "tiff",
    "css", "js", "woff", "woff2", "ttf", "eot", "otf", "mp4", "webm", "mp3",
    "wav", "pdf", "zip", "gz", "tar", "exe", "dmg", "bin", "apk"
}

# Dummy placeholder domains that shouldn't be counted as legitimate leads
PLACEHOLDER_DOMAINS = {
    "example.com", "example.org", "example.net", "domain.com", "yourcompany.com",
    "email.com", "test.com", "sample.com", "placeholder.com", "sentry.io",
    "wixpress.com", "bootstrap.com", "wordpress.org", "mysite.com", "temp.com",
    "mycompany.com", "company.com", "yoursite.com", "client.com"
}

# Role-based prefixes for departmental email classification
ROLE_EMAIL_PREFIXES = {
    "support", "sales", "info", "contact", "press", "media", "billing",
    "jobs", "careers", "security", "privacy", "legal", "hello", "team",
    "investors", "partners", "marketing", "help", "inquiries", "inquiry",
    "hr", "accounting", "compliance", "office", "admin", "operations",
    "general", "feedback", "service", "customer", "customercare", "pr"
}

# Executive / leadership title keywords
EXECUTIVE_TITLES = [
    "chief executive officer", "ceo", "chief technology officer", "cto",
    "chief operating officer", "coo", "chief financial officer", "cfo",
    "chief marketing officer", "cmo", "chief product officer", "cpo",
    "founder", "co-founder", "president", "vice president", "vp",
    "managing director", "director", "head of", "partner", "principal",
    "lead", "manager"
]

class AIScraperEngine:
    """
    AI-Powered Web Scraper & Contact Harvester:
    - Multi-route smart crawler (Home, About, Team, Contact, Legal/Impressum, Careers)
    - Advanced email de-obfuscation (HTML entities, spambot text patterns, mailto: decoders)
    - Phone number extraction with international normalization and context labeling
    - Social account categorization (LinkedIn Company/Personal, Twitter/X, GitHub, etc.)
    - Physical headquarters and contact form discovery
    - Two-tier AI Engine:
        * Local Semantic Heuristic Engine (zero API key, instant, 100% resilient)
        * Generative LLM Extraction (OpenAI / Gemini / Groq / Anthropic)
    """

    @staticmethod
    def normalize_target_url(target):
        """Clean and normalize a domain or URL to a valid HTTPS URL."""
        if not target:
            return ""
        t = target.strip()
        if not (t.startswith("http://") or t.startswith("https://")):
            t = f"https://{t}"
        parsed = urllib.parse.urlparse(t)
        netloc = parsed.netloc or parsed.path
        netloc = netloc.split("/")[0].strip()
        scheme = parsed.scheme if parsed.scheme in ["http", "https"] else "https"
        return f"{scheme}://{netloc}"

    @staticmethod
    def extract_base_domain(url):
        """Extract apex/base domain from a URL (e.g. https://www.stripe.com -> stripe.com)."""
        parsed = urllib.parse.urlparse(url)
        host = (parsed.netloc or parsed.path).split(":")[0].lower()
        if host.startswith("www."):
            host = host[4:]
        return host

    @classmethod
    def clean_html_to_text(cls, raw_html):
        """Strip scripts, styles, and markup to retrieve clean, readable text."""
        if not raw_html:
            return ""
        # Remove script, style, noscript, svg, and iframe tags
        text = re.sub(r'(?is)<script.*?</script>', ' ', raw_html)
        text = re.sub(r'(?is)<style.*?</style>', ' ', text)
        text = re.sub(r'(?is)<noscript.*?</noscript>', ' ', text)
        text = re.sub(r'(?is)<svg.*?</svg>', ' ', text)
        text = re.sub(r'(?is)<iframe.*?</iframe>', ' ', text)
        # Convert break tags and paragraph ends to newlines
        text = re.sub(r'(?i)<(br|/p|/div|/li|/h[1-6]|/tr)>', '\n', text)
        # Strip all other HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        # Unescape HTML entities
        text = html.unescape(text)
        # Normalize whitespace while preserving line structure
        lines = [re.sub(r'[ \t]+', ' ', l).strip() for l in text.split('\n')]
        return '\n'.join([l for l in lines if l])

    @classmethod
    def extract_json_ld(cls, raw_html):
        """Extract structured JSON-LD data from HTML."""
        json_items = []
        if not raw_html:
            return json_items
        matches = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', raw_html, re.DOTALL | re.IGNORECASE)
        for m in matches:
            try:
                data = json.loads(m.strip())
                if isinstance(data, list):
                    json_items.extend(data)
                elif isinstance(data, dict):
                    if "@graph" in data and isinstance(data["@graph"], list):
                        json_items.extend(data["@graph"])
                    else:
                        json_items.append(data)
            except Exception:
                continue
        return json_items

    @classmethod
    def deobfuscate_text(cls, raw_str):
        """Decode common obfuscation tricks used to hide emails from scrapers."""
        if not raw_str:
            return ""
        s = html.unescape(raw_str)
        s = urllib.parse.unquote(s)
        
        # Replace entity variations
        s = re.sub(r'(?i)&commat;|&#64;|&#x40;', '@', s)
        s = re.sub(r'(?i)&period;|&#46;|&#x2e;', '.', s)
        
        # Replace written patterns: [at], (at), [@], ' at ', ' AT '
        s = re.sub(r'(?i)\s*(?:\[at\]|\(at\)|\[@\]|\bat\b)\s*', '@', s)
        # Replace written patterns: [dot], (dot), [.], ' dot ', ' DOT '
        s = re.sub(r'(?i)\s*(?:\[dot\]|\(dot\)|\[\.\]|\bdot\b)\s*', '.', s)
        return s

    @classmethod
    def extract_emails(cls, raw_html, base_domain=""):
        """
        Extract and de-obfuscate emails from raw HTML.
        Categorizes into Executive/Personal, Departmental/Role, or External.
        """
        discovered = {}
        if not raw_html:
            return []

        # 1. Extract from mailto: links directly
        mailto_matches = re.findall(r'href=["\']mailto:([^"?\'#\s]+)', raw_html, re.IGNORECASE)
        for m in mailto_matches:
            email_clean = cls.deobfuscate_text(m).strip().lower()
            if cls._is_valid_email(email_clean):
                discovered[email_clean] = {
                    "source": "mailto",
                    "context": "Direct mailto: contact link"
                }

        # 2. Deobfuscate raw HTML and full text
        clean_text = cls.clean_html_to_text(raw_html)
        deobf_html = cls.deobfuscate_text(raw_html)
        deobf_text = cls.deobfuscate_text(clean_text)

        # Standard RFC email pattern
        email_pattern = re.compile(r'\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b')
        
        for pool_text, src_name in [(deobf_text, "text"), (deobf_html, "html_markup")]:
            for match in email_pattern.finditer(pool_text):
                email = match.group(0).strip().lower()
                if email.endswith('.'):
                    email = email[:-1]
                if cls._is_valid_email(email) and email not in discovered:
                    # Capture surrounding context snippet (up to 80 chars)
                    start = max(0, match.start() - 40)
                    end = min(len(pool_text), match.end() + 40)
                    ctx = pool_text[start:end].replace('\n', ' ').strip()
                    discovered[email] = {
                        "source": src_name,
                        "context": ctx
                    }

        # 3. Categorize emails
        results = []
        base_dom_lower = base_domain.lower() if base_domain else ""
        
        for email, meta in discovered.items():
            user, domain = email.split("@", 1)
            is_same_domain = (base_dom_lower and (domain == base_dom_lower or domain.endswith("." + base_dom_lower)))
            
            # Check if role-based
            prefix_match = any(user == r or user.startswith(f"{r}.") or user.startswith(f"{r}_") for r in ROLE_EMAIL_PREFIXES)
            
            if not is_same_domain and base_dom_lower:
                category = "External / Vendor"
                role_label = f"External ({domain})"
            elif prefix_match:
                category = "Role / Departmental"
                role_label = user.split(".")[0].split("_")[0].capitalize()
            elif is_same_domain:
                category = "Executive / Personal"
                role_label = "Direct / Employee"
            else:
                category = "Role / Departmental"
                role_label = "General Contact"

            results.append({
                "email": email,
                "username": user,
                "domain": domain,
                "category": category,
                "role_label": role_label,
                "is_primary_domain": is_same_domain,
                "source": meta.get("source", "crawler"),
                "context": meta.get("context", "")
            })

        # Sort: Executive/Personal first, then Role, then External
        priority_map = {"Executive / Personal": 1, "Role / Departmental": 2, "External / Vendor": 3}
        results.sort(key=lambda x: priority_map.get(x["category"], 4))
        return results

    @classmethod
    def _is_valid_email(cls, email):
        """Validate candidate email against RFC syntax and blacklist filters."""
        if not email or "@" not in email or " " in email:
            return False
        parts = email.split("@")
        if len(parts) != 2:
            return False
        user, domain = parts
        if not user or not domain or "." not in domain:
            return False
        if len(email) < 6 or len(email) > 100:
            return False
        # Filter forbidden file extensions and ensure valid alphabetic TLD
        ext = domain.rsplit(".", 1)[-1].lower()
        if ext in FORBIDDEN_EXTENSIONS or not re.match(r'^[a-z]{2,24}$', ext):
            return False
        # Filter dummy placeholder domains
        if domain.lower() in PLACEHOLDER_DOMAINS:
            return False
        # Filter image-like naming (e.g. icon@2x)
        if user.endswith("@2x") or user.endswith("@3x") or "@" in user:
            return False
        return True

    @classmethod
    def extract_phone_numbers(cls, raw_html):
        """Extract phone numbers from tel: links and structured text patterns."""
        phones = {}
        if not raw_html:
            return []

        # 1. Extract from tel: links
        tel_matches = re.findall(r'href=["\']tel:([^"?\'#\s]+)', raw_html, re.IGNORECASE)
        for t in tel_matches:
            cleaned = cls._clean_phone_number(t)
            if cleaned and cleaned not in phones:
                phones[cleaned] = {"number": cleaned, "label": "Direct Call Link", "source": "tel_link"}

        # 2. Extract from JSON-LD schema
        json_lds = cls.extract_json_ld(raw_html)
        for item in json_lds:
            for field in ["telephone", "faxNumber", "contactPoint"]:
                val = item.get(field)
                if isinstance(val, str):
                    c = cls._clean_phone_number(val)
                    if c and c not in phones:
                        phones[c] = {"number": c, "label": "Schema.org Official", "source": "json_ld"}
                elif isinstance(val, list):
                    for sub in val:
                        if isinstance(sub, dict) and "telephone" in sub:
                            c = cls._clean_phone_number(sub["telephone"])
                            if c and c not in phones:
                                phones[c] = {"number": c, "label": sub.get("contactType", "Customer Support"), "source": "json_ld"}

        # 3. Extract from text using international / domestic patterns
        clean_text = cls.clean_html_to_text(raw_html)
        # Look for phone patterns
        phone_regex = re.compile(
            r'(?:(?:Tel|Phone|Call|Toll-Free|Office|HQ|Fax|Contact|Mobile)[:\s]+)?'
            r'(\+?[0-9]{1,4}[-.\s]?(?:\([0-9]{2,5}\)[-.\s]?|[0-9]{2,5}[-.\s]?)'
            r'[0-9]{2,4}[-.\s]?[0-9]{3,5})',
            re.IGNORECASE
        )
        
        for m in phone_regex.finditer(clean_text):
            raw_match = m.group(1).strip()
            # Capture contextual snippet before match
            start = max(0, m.start() - 35)
            ctx = clean_text[start:m.start()].lower()
            
            cleaned = cls._clean_phone_number(raw_match)
            if cleaned and cleaned not in phones:
                # Infer label from context
                label = "General Office"
                if "toll" in ctx or "free" in ctx:
                    label = "Toll-Free Support"
                elif "support" in ctx or "help" in ctx or "care" in ctx:
                    label = "Customer Support"
                elif "sales" in ctx:
                    label = "Sales Line"
                elif "fax" in ctx:
                    label = "Fax Number"
                elif "hq" in ctx or "headquarters" in ctx:
                    label = "Headquarters"
                elif "direct" in ctx or "mobile" in ctx:
                    label = "Direct Line"
                
                phones[cleaned] = {
                    "number": cleaned,
                    "label": label,
                    "source": "text_context"
                }

        return list(phones.values())

    @staticmethod
    def _clean_phone_number(raw_phone):
        """Sanitize phone string, filter out dates, zip codes, and invalid lengths."""
        if not raw_phone:
            return ""
        # Remove common text artifacts
        s = html.unescape(raw_phone).strip()
        s = urllib.parse.unquote(s)
        # Remove leading tel: or callto:
        s = re.sub(r'^(?:tel:|callto:)', '', s, flags=re.IGNORECASE).strip()
        # Normalize newlines and whitespace
        s = re.sub(r'[\r\n\t]+', ' ', s)
        s = re.sub(r'\s+', ' ', s).strip()
        # Keep +, digits, dashes, spaces, parens, dots
        s = re.sub(r'[^\d+().\-\s]', '', s).strip()
        
        # If dots are present, only allow standard dot-separated phone formats (e.g. 800.555.0199)
        if "." in s and not re.match(r'^\+?[0-9]{1,4}(?:\.[0-9]{2,5}){2,4}$', s):
            return ""

        # Count actual digits
        digits = re.sub(r'\D', '', s)
        if len(digits) < 7 or len(digits) > 15:
            return ""
        # Avoid year strings (e.g. 2024-2025)
        if len(digits) == 8 and (s.startswith("201") or s.startswith("202")):
            return ""
        # Avoid repetitive dummy digits
        if len(set(digits)) == 1:
            return ""
        # Avoid dimensions (e.g. 1920x1080)
        return s

    @classmethod
    def extract_social_accounts(cls, raw_html):
        """Discover and categorize social media accounts, company pages, and personal profiles."""
        socials = {
            "linkedin_company": [],
            "linkedin_personal": [],
            "twitter_x": [],
            "github": [],
            "youtube": [],
            "facebook": [],
            "instagram": [],
            "discord": [],
            "telegram": [],
            "tiktok": [],
            "threads": [],
            "medium": []
        }
        if not raw_html:
            return socials

        # Extract all href attributes
        hrefs = re.findall(r'href=["\']([^"\'#\s]+)', raw_html, re.IGNORECASE)
        # Also check JSON-LD sameAs
        for item in cls.extract_json_ld(raw_html):
            same_as = item.get("sameAs", [])
            if isinstance(same_as, str):
                hrefs.append(same_as)
            elif isinstance(same_as, list):
                hrefs.extend([s for s in same_as if isinstance(s, str)])

        seen = set()

        for link in hrefs:
            link = html.unescape(link.strip())
            if not link.startswith("http"):
                continue
            
            clean_url = link.split("?")[0].rstrip("/")
            if clean_url in seen:
                continue

            # 1. LinkedIn
            if "linkedin.com" in clean_url:
                if "/company/" in clean_url or "/school/" in clean_url or "/showcase/" in clean_url:
                    slug = clean_url.split("/company/")[-1].split("/")[0] if "/company/" in clean_url else clean_url.split("/")[-1]
                    socials["linkedin_company"].append({"url": clean_url, "handle": slug, "type": "Company Page"})
                    seen.add(clean_url)
                elif "/in/" in clean_url:
                    slug = clean_url.split("/in/")[-1].split("/")[0]
                    socials["linkedin_personal"].append({"url": clean_url, "handle": slug, "type": "Personal Profile"})
                    seen.add(clean_url)

            # 2. Twitter / X
            elif any(d in clean_url for d in ["twitter.com", "x.com"]):
                # Filter out intent, share, hashtag, search
                if not any(bad in clean_url for bad in ["/share", "/intent", "/search", "/home", "/explore", "/privacy", "/tos"]):
                    handle = clean_url.split("/")[-1].replace("@", "")
                    if handle and handle.lower() not in ["twitter", "x"]:
                        socials["twitter_x"].append({"url": clean_url, "handle": f"@{handle}"})
                        seen.add(clean_url)

            # 3. GitHub
            elif "github.com" in clean_url:
                if not any(bad in clean_url for bad in ["/features", "/pricing", "/explore", "/topics", "/security", "/site", "/about", "/login", "/signup"]):
                    parts = clean_url.split("github.com/")[-1].split("/")
                    handle = parts[0]
                    if handle:
                        socials["github"].append({"url": clean_url, "handle": handle})
                        seen.add(clean_url)

            # 4. YouTube
            elif "youtube.com" in clean_url or "youtu.be" in clean_url:
                handle = clean_url.split("/")[-1]
                socials["youtube"].append({"url": clean_url, "handle": handle})
                seen.add(clean_url)

            # 5. Facebook
            elif "facebook.com" in clean_url and "/sharer" not in clean_url:
                handle = clean_url.split("/")[-1]
                socials["facebook"].append({"url": clean_url, "handle": handle})
                seen.add(clean_url)

            # 6. Instagram
            elif "instagram.com" in clean_url and "/p/" not in clean_url:
                handle = clean_url.split("/")[-1]
                socials["instagram"].append({"url": clean_url, "handle": f"@{handle}"})
                seen.add(clean_url)

            # 7. Discord
            elif "discord.gg" in clean_url or "discord.com/invite" in clean_url:
                invite = clean_url.split("/")[-1]
                socials["discord"].append({"url": clean_url, "invite_code": invite})
                seen.add(clean_url)

            # 8. Telegram
            elif "t.me" in clean_url or "telegram.me" in clean_url:
                handle = clean_url.split("/")[-1]
                socials["telegram"].append({"url": clean_url, "handle": f"@{handle}"})
                seen.add(clean_url)

            # 9. TikTok
            elif "tiktok.com" in clean_url:
                handle = clean_url.split("/")[-1]
                socials["tiktok"].append({"url": clean_url, "handle": handle})
                seen.add(clean_url)

            # 10. Threads
            elif "threads.net" in clean_url:
                handle = clean_url.split("/")[-1]
                socials["threads"].append({"url": clean_url, "handle": handle})
                seen.add(clean_url)

            # 11. Medium
            elif "medium.com" in clean_url:
                handle = clean_url.split("/")[-1]
                socials["medium"].append({"url": clean_url, "handle": handle})
                seen.add(clean_url)

        return socials

    @classmethod
    def extract_headquarters_and_forms(cls, raw_html):
        """Extract headquarters, physical addresses, and contact forms/endpoints."""
        addresses = []
        forms = []

        # 1. From JSON-LD
        for item in cls.extract_json_ld(raw_html):
            addr = item.get("address")
            if isinstance(addr, dict):
                parts = [
                    addr.get("streetAddress", ""),
                    addr.get("addressLocality", ""),
                    addr.get("addressRegion", ""),
                    addr.get("postalCode", ""),
                    addr.get("addressCountry", "")
                ]
                clean_addr = ", ".join([p for p in parts if p])
                if clean_addr and clean_addr not in addresses:
                    addresses.append(clean_addr)
            elif isinstance(addr, str) and addr not in addresses:
                addresses.append(addr)

        # 2. From HTML text
        clean_text = cls.clean_html_to_text(raw_html)
        # Look for street/suite patterns
        addr_match = re.search(
            r'(?:Headquarters|Office|Address|Location|HQ)[:\s]+'
            r'([0-9]{1,5}\s+[A-Za-z0-9\s.,#-]+(?:Suite|Ste|Floor|Fl|Avenue|Ave|Street|St|Road|Rd|Boulevard|Blvd|Way|Dr|Drive)[A-Za-z0-9\s.,#-]+)',
            clean_text,
            re.IGNORECASE
        )
        if addr_match:
            found = addr_match.group(1).strip()
            if len(found) < 120 and found not in addresses:
                addresses.append(found)

        # 3. Contact Form Actions & Calendly/Typeform discovery
        form_actions = re.findall(r'<form[^>]*action=["\']([^"\'#\s]+)', raw_html, re.IGNORECASE)
        for act in form_actions:
            if not act.startswith("javascript:"):
                forms.append({"type": "HTML Form Action", "endpoint": act})

        # Check for embedded calendar / booking widgets
        for widget in ["calendly.com", "hubspot.com", "typeform.com", "tally.so", "fillout.com"]:
            if widget in raw_html:
                m = re.findall(rf'https://[a-zA-Z0-9-.]*{re.escape(widget)}/[^"\'\s<>]+', raw_html)
                for w_url in m:
                    forms.append({"type": f"{widget.split('.')[0].capitalize()} Booking Widget", "endpoint": w_url})

        return {
            "headquarters": addresses,
            "contact_endpoints": forms
        }

    @classmethod
    def discover_crawl_routes(cls, base_url, home_html=""):
        """
        Discover high-value contact routes:
        1. Links dynamically found in home HTML matching contact/team keywords (highest relevance)
        2. Pre-defined standard corporate routes
        """
        discovered_urls = [base_url if base_url.endswith('/') else f"{base_url}/"]
        base_dom = cls.extract_base_domain(base_url)

        # 1. Parse links directly linked from home page first (highest priority)
        if home_html:
            links = re.findall(r'href=["\']([^"\'#\s]+)', home_html, re.IGNORECASE)
            keywords = ["team", "people", "leadership", "contact", "about", "impressum", "touch", "reach", "staff", "management", "support", "press"]
            for l in links:
                if any(k in l.lower() for k in keywords):
                    full = urllib.parse.urljoin(base_url, l)
                    parsed = urllib.parse.urlparse(full)
                    # Stay within same domain
                    if cls.extract_base_domain(full) == base_dom and full not in discovered_urls:
                        # Avoid file downloads
                        ext = parsed.path.split(".")[-1].lower() if "." in parsed.path else ""
                        if ext not in FORBIDDEN_EXTENSIONS:
                            discovered_urls.append(full)

        # 2. Add standard fallback routes
        standard_routes = [
            "/contact",
            "/team",
            "/about",
            "/leadership",
            "/contact-us",
            "/our-team",
            "/about-us",
            "/people",
            "/impressum",
            "/legal",
            "/privacy",
            "/press",
            "/careers"
        ]

        for r in standard_routes:
            full = urllib.parse.urljoin(base_url, r)
            if full not in discovered_urls:
                discovered_urls.append(full)

        return discovered_urls

    @classmethod
    def crawl_site(cls, target, max_pages=8, timeout=7):
        """
        Crawl target website concurrently across high-value routes.
        Returns aggregated HTML and page metadata.
        """
        base_url = cls.normalize_target_url(target)
        if not base_url:
            return {"success": False, "error": "Invalid target URL or domain"}

        base_domain = cls.extract_base_domain(base_url)
        session = requests.Session()
        session.headers.update(HEADERS)

        # 1. Fetch Homepage first to discover custom routes
        home_html = ""
        crawled_pages = {}
        try:
            resp = session.get(base_url, timeout=timeout, allow_redirects=True)
            if resp.status_code == 200:
                home_html = resp.text
                crawled_pages[base_url] = {
                    "url": base_url,
                    "status": 200,
                    "html": home_html
                }
                # Update base_url if redirected
                base_url = f"{urllib.parse.urlparse(resp.url).scheme}://{urllib.parse.urlparse(resp.url).netloc}"
        except requests.exceptions.SSLError:
            # Fallback to HTTP if SSL fails
            if base_url.startswith("https://"):
                base_url = base_url.replace("https://", "http://")
                try:
                    resp = session.get(base_url, timeout=timeout, allow_redirects=True)
                    if resp.status_code == 200:
                        home_html = resp.text
                        crawled_pages[base_url] = {"url": base_url, "status": 200, "html": home_html}
                except Exception:
                    pass
        except Exception:
            pass

        # 2. Discover all candidate routes
        routes = cls.discover_crawl_routes(base_url, home_html)
        target_routes = [r for r in routes if r not in crawled_pages][:max_pages]

        # 3. Concurrently fetch remaining candidate pages
        def fetch_page(url):
            try:
                r = session.get(url, timeout=timeout, allow_redirects=True)
                if r.status_code == 200 and "text/html" in r.headers.get("Content-Type", ""):
                    return url, r.status_code, r.text
            except Exception:
                pass
            return url, 0, ""

        if target_routes:
            with ThreadPoolExecutor(max_workers=min(len(target_routes), 5)) as pool:
                futures = {pool.submit(fetch_page, u): u for u in target_routes}
                for fut in as_completed(futures):
                    url, code, content = fut.result()
                    if code == 200 and content:
                        crawled_pages[url] = {
                            "url": url,
                            "status": code,
                            "html": content
                        }

        if not crawled_pages:
            return {
                "success": False,
                "error": f"Failed to connect to {target} (Host unreachable or SSL/timeout error)"
            }

        return {
            "success": True,
            "base_url": base_url,
            "base_domain": base_domain,
            "pages": crawled_pages
        }

    # -------------------------------------------------------------
    # AI Engine Tier 1: Local Built-in Heuristic NLP Extractor
    # -------------------------------------------------------------
    @classmethod
    def run_local_heuristic_ai(cls, crawled_data):
        """
        Extract and structure contacts, team members, and company dossier
        using local pattern heuristics with ZERO external API keys.
        """
        base_domain = crawled_data.get("base_domain", "")
        pages = crawled_data.get("pages", {})

        all_html = "\n".join([p["html"] for p in pages.values()])
        home_html = pages.get(crawled_data.get("base_url"), {}).get("html", "") or all_html

        # 1. Company Metadata
        title_m = re.search(r'<title[^>]*>(.*?)</title>', home_html, re.IGNORECASE)
        title = html.unescape(title_m.group(1)).strip() if title_m else base_domain.capitalize()
        
        desc_m = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', home_html, re.IGNORECASE)
        if not desc_m:
            desc_m = re.search(r'<meta[^>]*property=["\']og:description["\'][^>]*content=["\']([^"\']+)["\']', home_html, re.IGNORECASE)
        description = html.unescape(desc_m.group(1)).strip() if desc_m else ""

        # 2. Extract Emails, Phones, Socials, Addresses
        emails = cls.extract_emails(all_html, base_domain)
        phones = cls.extract_phone_numbers(all_html)
        socials = cls.extract_social_accounts(all_html)
        hq_forms = cls.extract_headquarters_and_forms(all_html)

        # 3. Detect Team Members & Leadership from Team/About pages
        team_members = cls._detect_team_members(pages, emails, socials)

        return {
            "company_name": title.split(" - ")[0].split(" | ")[0].split(" — ")[0].strip(),
            "title": title,
            "summary": description or f"Online business entity operating on {base_domain}.",
            "base_domain": base_domain,
            "target_url": crawled_data.get("base_url"),
            "pages_analyzed": len(pages),
            "ai_engine": "Local Smart Heuristic NLP (Built-in)",
            "emails": emails,
            "phones": phones,
            "social_accounts": socials,
            "headquarters": hq_forms["headquarters"],
            "contact_endpoints": hq_forms["contact_endpoints"],
            "team_leadership": team_members
        }

    @classmethod
    def _detect_team_members(cls, pages, emails, socials):
        """Heuristically identify leadership team members, titles, and match to contacts."""
        team = []
        seen_names = set()

        # Find team / about pages
        relevant_htmls = []
        for url, p in pages.items():
            if any(k in url.lower() for k in ["team", "about", "leadership", "people", "founder"]):
                relevant_htmls.append(p["html"])

        if not relevant_htmls and pages:
            relevant_htmls = [list(pages.values())[0]["html"]]

        combined_text = "\n".join([cls.clean_html_to_text(h) for h in relevant_htmls])
        lines = [l.strip() for l in combined_text.split("\n") if l.strip()]

        # Scan line-by-line for name + title pairs
        for i in range(len(lines) - 1):
            line_a = lines[i]
            line_b = lines[i + 1]

            # Check if line_a looks like a name (2-3 words, capitalized, no punctuation)
            words = line_a.split()
            if 2 <= len(words) <= 3 and all(w[0].isupper() and w.isalpha() for w in words):
                # Check if line_b contains an executive / leadership title
                if any(t in line_b.lower() for t in EXECUTIVE_TITLES):
                    name = line_a
                    title = line_b
                    if name not in seen_names and len(name) < 35 and len(title) < 50:
                        seen_names.add(name)
                        
                        # Check if any discovered email matches name
                        matched_email = ""
                        first = words[0].lower()
                        last = words[-1].lower()
                        for e in emails:
                            u = e["username"].lower()
                            if first in u or last in u:
                                matched_email = e["email"]
                                break

                        # Check if any personal LinkedIn matches name
                        matched_li = ""
                        for li in socials.get("linkedin_personal", []):
                            h = li["handle"].lower()
                            if first in h or last in h:
                                matched_li = li["url"]
                                break

                        team.append({
                            "name": name,
                            "title": title,
                            "email": matched_email,
                            "linkedin": matched_li
                        })

        return team[:10]  # Cap to top 10 detected leaders

    # -------------------------------------------------------------
    # AI Engine Tier 2: Generative LLM Extraction (OpenAI/Gemini/Groq/Anthropic)
    # -------------------------------------------------------------
    @classmethod
    def run_llm_ai(cls, crawled_data, model_provider="auto"):
        """
        Run generative AI model on scraped text content to extract
        structured intelligence, executives, and verified contact mappings.
        Falls back to local heuristic AI if provider fails or quota exhausted.
        """
        # Always run local heuristic AI first as baseline
        baseline = cls.run_local_heuristic_ai(crawled_data)
        
        # Determine available API key and provider
        provider, api_key = cls._resolve_ai_provider(model_provider)
        if not api_key:
            return baseline  # Seamless fallback

        # Aggregate text summary (max ~8000 chars for optimal speed & token cost)
        pages = crawled_data.get("pages", {})
        condensed_texts = []
        for url, p in pages.items():
            txt = cls.clean_html_to_text(p["html"])
            condensed_texts.append(f"--- PAGE: {url} ---\n{txt[:2500]}")
        combined_prompt_text = "\n\n".join(condensed_texts)[:10000]

        prompt = (
            "You are a master OSINT investigator and corporate contact extraction AI.\n"
            "Analyze the scraped web pages below and return a STRICT JSON object with these exact keys:\n"
            "{\n"
            '  "company_name": "Official company name",\n'
            '  "industry": "Industry or market sector",\n'
            '  "summary": "Concise 2-sentence summary of what this business does",\n'
            '  "executives": [\n'
            '     {"name": "Full Name", "title": "Role/Title", "email": "email or null", "linkedin": "profile url or null"}\n'
            "  ],\n"
            '  "department_contacts": [\n'
            '     {"department": "Support/Sales/Press/etc.", "email": "email address", "phone": "phone or null"}\n'
            "  ],\n"
            '  "phone_numbers": [\n'
            '     {"number": "Phone number", "label": "HQ/Sales/Support"}\n'
            "  ],\n"
            '  "headquarters": "Primary physical address or null",\n'
            '  "social_handles": {"linkedin": "url or null", "twitter": "url or null", "github": "url or null"}\n'
            "}\n\n"
            "RAW WEBSITE CONTENT:\n"
            f"{combined_prompt_text}"
        )

        try:
            llm_result = None
            if provider == "openai" or provider == "groq":
                llm_result = cls._call_openai_compatible(provider, api_key, prompt)
            elif provider == "gemini":
                llm_result = cls._call_gemini(api_key, prompt)
            elif provider == "anthropic":
                llm_result = cls._call_anthropic(api_key, prompt)

            if llm_result:
                # Merge LLM results with baseline
                baseline["company_name"] = llm_result.get("company_name") or baseline["company_name"]
                baseline["summary"] = llm_result.get("summary") or baseline["summary"]
                baseline["industry"] = llm_result.get("industry", "Unknown")
                baseline["ai_engine"] = f"{provider.capitalize()} LLM Engine"

                # Merge executives
                llm_execs = llm_result.get("executives", [])
                if llm_execs:
                    baseline["team_leadership"] = llm_execs

                # Merge any newly discovered emails
                existing_emails = {e["email"] for e in baseline["emails"]}
                for d in llm_result.get("department_contacts", []):
                    em = d.get("email")
                    if em and cls._is_valid_email(em) and em not in existing_emails:
                        baseline["emails"].append({
                            "email": em,
                            "username": em.split("@")[0],
                            "domain": em.split("@")[-1],
                            "category": "Role / Departmental",
                            "role_label": d.get("department", "Department"),
                            "is_primary_domain": True,
                            "source": f"{provider}_ai_inference",
                            "context": f"AI identified as {d.get('department')}"
                        })
                        existing_emails.add(em)
        except Exception:
            # Fall back to baseline on any LLM parsing or network issue
            pass

        return baseline

    @classmethod
    def _resolve_ai_provider(cls, requested):
        """Find the best available AI API key based on user request and local config."""
        req = requested.lower() if requested else "auto"
        
        # Check providers in priority
        providers = [
            ("gemini", ["gemini_api_keys", "gemini_api_key"]),
            ("openai", ["openai_api_keys", "openai_api_key"]),
            ("groq", ["groq_api_keys", "groq_api_key"]),
            ("anthropic", ["anthropic_api_keys", "anthropic_api_key"])
        ]

        if req != "auto":
            # Targeted provider
            for name, key_names in providers:
                if req in name:
                    for kn in key_names:
                        k = get_api_key(kn)
                        if k:
                            return name, k
            return "heuristic", None

        # Auto-detect first configured key
        for name, key_names in providers:
            for kn in key_names:
                k = get_api_key(kn)
                if k:
                    return name, k

        return "heuristic", None

    DEFAULT_AI_MODELS = {
        "openai": "gpt-4o-mini",
        "gemini": "gemini-2.0-flash",
        "groq": "llama-3.3-70b-versatile",
        "anthropic": "claude-3-5-haiku-latest"
    }

    @classmethod
    def _call_openai_compatible(cls, provider, api_key, prompt):
        """Call OpenAI or Groq chat completions endpoint with automatic model resolution and fallback."""
        url = "https://api.openai.com/v1/chat/completions" if provider == "openai" else "https://api.groq.com/openai/v1/chat/completions"
        if provider == "openai":
            model = get_api_key("openai_model") or cls.DEFAULT_AI_MODELS["openai"]
        else:
            model = get_api_key("groq_model") or cls.DEFAULT_AI_MODELS["groq"]

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a contact intelligence extraction AI. Always respond in valid JSON format."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }
        resp = requests.post(url, headers=headers, json=body, timeout=18)
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            return json.loads(content)
        elif resp.status_code in [400, 404] and provider == "groq" and model != "llama-3.1-8b-instant":
            # Fallback to ultra-fast 8B instant if 70B versatile encounters capacity or tier constraints
            fb_body = dict(body)
            fb_body["model"] = "llama-3.1-8b-instant"
            fb_resp = requests.post(url, headers=headers, json=fb_body, timeout=18)
            if fb_resp.status_code == 200:
                content = fb_resp.json()["choices"][0]["message"]["content"]
                return json.loads(content)
        return None

    @classmethod
    def _call_gemini(cls, api_key, prompt):
        """Call Google Gemini REST endpoint (defaulting to gemini-2.0-flash with 1.5-flash fallback)."""
        model = get_api_key("gemini_model") or cls.DEFAULT_AI_MODELS["gemini"]
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        body = {
            "contents": [{
                "parts": [{"text": f"{prompt}\nReturn ONLY pure valid JSON."}]
            }],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.2
            }
        }
        resp = requests.post(url, json=body, timeout=18)
        if resp.status_code == 200:
            text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)
        elif resp.status_code in [400, 404] and model != "gemini-1.5-flash":
            # Graceful fallback to gemini-1.5-flash
            fb_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            fb_resp = requests.post(fb_url, json=body, timeout=18)
            if fb_resp.status_code == 200:
                text = fb_resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
        return None

    @classmethod
    def _call_anthropic(cls, api_key, prompt):
        """Call Anthropic Messages REST endpoint (defaulting to claude-3-5-haiku-latest with snapshot fallback)."""
        url = "https://api.anthropic.com/v1/messages"
        model = get_api_key("anthropic_model") or cls.DEFAULT_AI_MODELS["anthropic"]
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        body = {
            "model": model,
            "max_tokens": 1500,
            "messages": [{"role": "user", "content": f"{prompt}\nRespond with JSON only."}]
        }
        resp = requests.post(url, headers=headers, json=body, timeout=18)
        if resp.status_code == 200:
            txt = resp.json()["content"][0]["text"]
            # Extract json if wrapped in ```json ... ```
            m = re.search(r'\{.*\}', txt, re.DOTALL)
            if m:
                return json.loads(m.group(0))
        elif resp.status_code in [400, 404] and "latest" in model:
            # Fallback to dated snapshot if dynamic latest alias is rejected on legacy API accounts
            fb_body = dict(body)
            fb_body["model"] = "claude-3-5-haiku-20241022"
            fb_resp = requests.post(url, headers=headers, json=fb_body, timeout=18)
            if fb_resp.status_code == 200:
                txt = fb_resp.json()["content"][0]["text"]
                m = re.search(r'\{.*\}', txt, re.DOTALL)
                if m:
                    return json.loads(m.group(0))
        return None

    # -------------------------------------------------------------
    # Main Harvester Public Entry Point
    # -------------------------------------------------------------
    @classmethod
    def harvest(cls, target, max_pages=8, ai_provider="auto"):
        """
        Complete Harvester Pipeline:
        1. Crawls target site across key discovery routes
        2. Executes Obfuscation De-cloaker & Contact Extraction
        3. Structures data with AI (Heuristic or LLM)
        """
        crawl_res = cls.crawl_site(target, max_pages=max_pages)
        if not crawl_res.get("success"):
            return {
                "success": False,
                "error": crawl_res.get("error", "Crawling failed"),
                "target": target
            }

        dossier = cls.run_llm_ai(crawl_res, model_provider=ai_provider)
        dossier["success"] = True
        return dossier
