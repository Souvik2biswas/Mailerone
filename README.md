# 📧 Mailerone

<p align="center">
  <strong>Comprehensive Email Finding, Multi-API Deliverability Verification & OSINT Suite</strong>
</p>

<p align="center">
  <a href="https://souvik2biswas.github.io/Mailerone/"><img src="https://img.shields.io/badge/Live_Web_Demo-Online-brightgreen?style=for-the-badge&logo=googlechrome&logoColor=white" alt="Live Web Demo"></a>
  <a href="https://github.com/Souvik2biswas/Mailerone"><img src="https://img.shields.io/badge/Version-2.3-blue?style=for-the-badge&logo=python" alt="Version 2.3"></a>
  <a href="https://github.com/Souvik2biswas/Mailerone/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue?style=for-the-badge" alt="License"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.8%2B-yellow?style=for-the-badge&logo=python" alt="Python 3.8+"></a>
  <a href="https://github.com/Souvik2biswas/Mailerone/stargazers"><img src="https://img.shields.io/github/stars/Souvik2biswas/Mailerone?style=for-the-badge&color=orange" alt="GitHub Stars"></a>
  <a href="https://github.com/Souvik2biswas/Mailerone/issues"><img src="https://img.shields.io/github/issues/Souvik2biswas/Mailerone?style=for-the-badge&color=red" alt="GitHub Issues"></a>
</p>

<p align="center">
  🌐 <strong>Try the Live Interactive Webpage &amp; Playground:</strong> <a href="https://souvik2biswas.github.io/Mailerone/"><strong>https://souvik2biswas.github.io/Mailerone/</strong></a>
</p>

---

## 🚀 Overview

**Mailerone** is an advanced, all-in-one email intelligence, lead generation, and OSINT toolkit designed for security researchers, penetration testers, OSINT investigators, recruiters, and sales engineers. It combines DNS protocol checks, SMTP server handshakes, disposable domain detection, **B2B email finding engines (Apollo.io, ContactOut, SalesQL, SignalHire, FinalScout, Name2Email, Hunter)**, and integrations with industry-leading verification engines into a unified, interactive terminal dashboard.

---

## ✨ Features

- **💼 B2B Email Finders & Lead Enrichment Suite**
  - **All-in-One Multi-Finder Pipeline**: Query Apollo.io, Hunter.io, ContactOut, SalesQL, SignalHire, FinalScout, and Name2Email simultaneously.
  - **Apollo.io B2B Intelligence**: High-accuracy lead finding, person enrichment, and corporate email discovery via Name + Domain / LinkedIn Profile with multi-key failover and live credit checking.
  - **Name2Email / Name2Mail Smart Permutator**: Generates 34 business email patterns with parallel multi-threaded DNS and MX verification.
  - **ContactOut Integration**: Search corporate/personal emails and phone numbers via Name + Company/Domain or LinkedIn Profile URL.
  - **SalesQL Integration**: Extract verified B2B emails, phone numbers, and professional headlines.
  - **SignalHire Integration**: Real-time candidate contact lookup by prospect name and organization.
  - **FinalScout Integration**: Business email extraction with confidence scoring and LinkedIn URL lookup.
  - **Hunter.io Suite**: Single verification, confidence scoring, and Name+Domain email finder.

- **🌐 Domain & DNS Inspector**
  - Instant discovery of active MX (Mail Exchange) records.
  - Verification of **SPF** (Sender Policy Framework) & **DMARC** security policies.
  - Real-time cross-referencing against an extensive blocklist of **8,800+ disposable / burner email domains**.
  - Whitelist and free provider detection via Disify API.

- **⚡ Multi-Engine Deliverability Scan (All-in-One)**
  - Comprehensive deliverability analysis aggregating DNS, SMTP handshake, Disify, Hunter.io, AbstractAPI, ZeroBounce, Debounce, and Mailboxlayer.
  - Calculated **Deliverability Score (0–100%)** with clear status indicators: `DELIVERABLE`, `RISKY`, or `UNDELIVERABLE`.

- **🔍 Webmail Address Matrix Across 75+ Global Providers**
  - Generates candidate addresses across 75+ global webmail & regional ESPs (Google Workspace, Yahoo, Microsoft, Apple, Proton, Yandex, Mail.ru, QQ, Naver, etc.) with real-time MX infrastructure checks and interactive deep mailbox deliverability scans.

- **🛡️ Multi-API Verifier Engines**
  - **AbstractAPI**: Real-time deliverability, SMTP checks, and catch-all detection.
  - **ZeroBounce**: Status, sub-status, and account validity verification.
  - **DeBounce**: RFC-compliant syntax, DNS verification, and disposable filtering.
  - **Mailboxlayer**: Real-time syntax and SMTP route checking.

- **🕵️ OSINT & Identity Profiler**
  - **Gravatar Integration**: Extract real names, profile usernames, bios, and avatar images.
  - **GitHub Commit Search**: Discover associated GitHub profiles and commits by email address.
  - **EmailRep.io**: Check domain age, reputation, spam history, data breaches, and suspicious activity.

- **🌐 AI-Powered Web Scraper & Contact Harvester**
  - **Multi-Route Crawler**: Concurrently crawls high-value target routes (`/`, `/contact`, `/team`, `/about`, `/leadership`, `/impressum`, `/legal`).
  - **Spambot Email De-obfuscation**: Resolves hidden emails (`name [at] domain [dot] com`, `contact(at)domain`, HTML numeric entities `&#64;`, URL encoding).
  - **Role & Executive Classification**: Automatically categorizes emails into Executive/Personal, Departmental/Role, or External Affiliates.
  - **Phone & Social Media Extraction**: Discovers phone numbers with context labels (`HQ`, `Toll-Free`, `Support`) and maps social profiles (LinkedIn Company & Personal, Twitter/X, GitHub, YouTube, etc.).
  - **Two-Tier AI Engine**: Instant Built-in Local Heuristic NLP Engine (zero external API keys, 100% free) with optional BYOK Generative LLMs (OpenAI GPT-4o, Google Gemini Flash, Groq Llama-3, Anthropic Claude).
  - **Deliverability Handoff & Export**: 1-click handoff to Comprehensive Deliverability Scan and export to `contacts_<domain>.json` / `contacts_<domain>.txt`.

- **🔀 Name-to-Email Permutation Generator**
  - Generate standard business email patterns (`first.last@domain`, `f.last@domain`, `first@domain`, etc.) and export candidates to `result.txt`.

- **⚙️ Interactive API Configuration Manager**
  - Easily update, view, and persist your API keys directly from the terminal.

---

## 📋 Installation

### Prerequisites
- **Python 3.8+** installed on your system.
- **Git** installed.

### 1. Clone the Repository
```bash
git clone https://github.com/Souvik2biswas/Mailerone.git
cd Mailerone
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🏃 Quick Start

### On Windows
Double-click `run.bat` or execute in Command Prompt / PowerShell:
```cmd
run.bat
```
or run directly with Python:
```bash
python Mailerone.py
```

### On Linux / macOS
```bash
python3 Mailerone.py
```

---

## 🕹️ Menu Options

```text
     __   __  _______  ___   ___      _______  ______    _______  __    _  _______ 
    |  |_|  ||   _   ||   | |   |    |       ||    _ |  |       ||  |  | ||       |
    |       ||  |_|  ||   | |   |    |    ___||   | ||  |   _   ||   |_| ||    ___|
    |       ||       ||   | |   |    |   |___ |   |_||_ |  | |  ||       ||   |___ 
    |       ||       ||   | |   |___ |    ___||    __  ||  |_|  ||  _    ||    ___|
    | ||_|| ||   _   ||   | |       ||   |___ |   |  | ||       || | |   ||   |___ 
    |_|   |_||__| |__||___| |_______||_______||___|  |_||_______||_|  |__||_______|
                  .:.:;.. Mailerone v2.1 (Multi-Engine Enhanced) ..;:.:.

    >> Comprehensive Email Finding, Multi-API Deliverability & OSINT Suite

    [1] Domain Inspector (DNS, MX, SPF, DMARC & Burner Check)
    [2] Webmail Address Matrix Across 75+ Global Providers (MX Check & Mailbox Probe)
     |
    [3] Comprehensive Multi-Engine Email Scan (All-in-One Deliverability)
    [4] B2B Email Finders & Lead Enrichment Suite (Apollo, ContactOut, SalesQL, SignalHire, FinalScout, Name2Mail, Hunter)
     |
    [5] AbstractAPI Email Verifier
    [6] Commercial Verifiers (ZeroBounce / Debounce / Mailboxlayer)
    [7] OSINT & Identity Profiler (Gravatar + GitHub + EmailRep)
    [8] AI Web Scraper & Contact Harvester (Emails, Phones, Socials & Team)
    [9] Name-to-Email Permutation Generator (Save to result.txt)
     |
    [10] API Keys, Usage Quotas & Tier Limits Manager
    [0] Exit Mailerone
```

---

## 📊 API Usage Limits & Tier Guide (Free vs Premium)

Mailerone supports real-time quota inspection and provides a comprehensive breakdown of monthly limits, rate limits, and pricing across all integrated engines:

| Service | Engine Category | Free Tier Allowance | Free Rate Limits | Premium / Paid Tiers | Live Quota Check |
|---|---|---|---|---|:---:|
| **AI Web Scraper & Harvester** | AI Public Intelligence & Scraping | **100% Free & Unlimited** (Built-in Heuristics) | Polite concurrency (8 routes) | **BYOK**: OpenAI / Gemini / Groq / Claude | ✅ Local Heuristics + Multi-LLM |
| **Apollo.io** | B2B Lead Intelligence & Enrichment | **50 Email Credits** / mo (10 Export Credits) | ~60 req/min | **Basic**: 10k credits ($49/mo)<br>**Professional**: 15k credits ($79/mo) | ✅ Yes (Live user profile check & multi-key failover) |
| **Hunter.io** | Lead Finder & Verifier | **25 Searches + 50 Verifications** / mo | 10 req/min | **Starter**: 500 searches ($49/mo)<br>**Growth**: 5k searches ($149/mo) | ✅ Yes (Live searches, verifications & reset date) |
| **ContactOut** | B2B Email & Phone Finder | **40 Work Emails + 5 Direct Phones** / mo | Standard query rate | **Sales Plan**: 500 emails + 50 phones ($49/mo)<br>**Recruiter**: 1k emails ($99/mo) | ✅ Yes (Live Work Emails & Direct Phones balance) |
| **SalesQL** | LinkedIn & Lead Enrichment | **50 Credits** / mo (1 credit = 1 email) | Standard rate | **Starter**: 1,000 credits ($39/mo)<br>**Advanced**: 3,000 credits ($79/mo) | ✅ Yes (Live Monthly Credits & Usage balance) |
| **SignalHire** | Candidate & Prospect Finder | **5 Free Contact Credits** on signup | Per-seat rate | **Lead Plan**: 350–1,000 credits ($49–$99/mo)<br>**Unlimited Email Plan** | ✅ Yes (Live Contact Credits balance) |
| **FinalScout** | LinkedIn & Corporate Finder | **20 Regular Email Credits** / mo | Standard query rate | **Pro**: 500 regular + 100 AI credits ($49/mo)<br>**Enterprise**: 5,000+ credits | ✅ Yes (Live Regular & AI Credits balance) |
| **Name2Email (Name2Mail)** | Smart Permutator & DNS Verifier | **100% Free & Unlimited** (34 patterns) | Zero limits (Runs locally) | **Always Free** (Built directly into Mailerone) | ✅ Always Active |
| **AbstractAPI** | Deliverability Verifier | **100 Verifications** / mo | 1 request / sec | **Starter**: 10k req ($9/mo)<br>**Pro**: 100k req ($49/mo) | ✅ Yes (Headers/Metadata) |
| **ZeroBounce** | Email Hygiene & Scoring | **100 Validations** / mo (Freemium) | Standard batch rate | **Pay-As-You-Go**: $0.008/credit<br>**Monthly**: 2k to 1M+ validations | ✅ Yes (Live remaining credit balance) |
| **DeBounce** | Email Validation API | **100 Free Credits** on signup | Standard rate | **Pay-As-You-Go**: $10 for 5,000 credits (Never expires) | ✅ Yes (Live remaining credit balance) |
| **Mailboxlayer** | Syntax & SMTP Routing | **100 Requests** / mo (HTTP) | 1 request / sec | **Basic**: 5,000 req ($14.99/mo, HTTPS)<br>**Pro**: 50,000 req ($74.99/mo) | ✅ Yes (Key validation) |
| **EmailRep.io** | Threat Intelligence OSINT | **Community**: 25 req/day (no key)<br>**Free Key**: 500 req/day | Daily rolling limit | **Enterprise**: 100k req/mo ($100+/mo) | ✅ Yes (Key mode detection) |
| **GitHub Search API** | OSINT Identity Discovery | **Unauthenticated**: 10 search req/min<br>**With Free Token**: 30 search req/min + 5k core/hr | Per-IP / Token window | **Enterprise API** | ✅ Yes (Live `/rate_limit` endpoint) |
| **Disify & Google DoH** | DNS & Burner Detection | **100% Free Public Services** | ~60 req/min (Disify)<br>Unlimited (Google DoH) | **Completely Free & Open Access** | ✅ Always Active |

> [!TIP]
> You can check your **real-time remaining credit balance and reset dates** directly inside Mailerone by selecting **Option `[10] API Keys, Usage Quotas & Tier Limits Manager` ➔ `[L] Check Real-Time API Quotas`**.

---

## 🔑 API Configuration & On-Device Security

> [!IMPORTANT]
> **Zero Codebase Leakage Guarantee:** All API credentials are saved **strictly on your local device** (in local `config.json`, `.env`, or browser LocalStorage). `config.json`, `.env`, and secret files are explicitly excluded via `.gitignore` and are never committed or pushed to GitHub.

You can use basic domain inspection, burner checks, Name2Email permutations, and username scans without any API keys. For advanced API features, configure keys either:
1. Inside the app via **Option `[9] API Keys Configuration Manager`**,
2. By setting environment variables on your device (e.g. `export HUNTER_API_KEYS="key1,key2"` or `.env`), or
3. By copying `config.example.json` to `config.json` locally on your device:

```bash
cp config.example.json config.json
```

Example local on-device `config.json`:

```json
{
    "apollo_api_keys": [
        "YOUR_APOLLO_API_KEY"
    ],
    "hunter_api_keys": [
        "YOUR_HUNTER_API_KEY"
    ],
    "contactout_api_key": "YOUR_CONTACTOUT_KEY",
    "salesql_api_key": "YOUR_SALESQL_KEY",
    "signalhire_api_key": "YOUR_SIGNALHIRE_KEY",
    "finalscout_api_key": "YOUR_FINALSCOUT_KEY",
    "abstract_api_key": "YOUR_ABSTRACT_KEY",
    "zerobounce_api_key": "YOUR_ZEROBOUNCE_KEY",
    "debounce_api_key": "YOUR_DEBOUNCE_KEY",
    "mailboxlayer_api_key": "YOUR_MAILBOXLAYER_KEY",
    "emailrep_api_key": "YOUR_EMAILREP_KEY",
    "github_token": "YOUR_GITHUB_PERSONAL_ACCESS_TOKEN",
    "openai_api_keys": [
        "YOUR_OPENAI_API_KEY"
    ],
    "gemini_api_keys": [
        "YOUR_GEMINI_API_KEY"
    ],
    "groq_api_keys": [
        "YOUR_GROQ_API_KEY"
    ],
    "anthropic_api_keys": [
        "YOUR_ANTHROPIC_API_KEY"
    ]
}
```

---

## 🧪 Running the Test Suite

Mailerone includes a built-in automated test suite to verify module integrity, pattern generators, and API engine functionality:

```bash
python test_suite.py
```

---

## 📁 Project Structure

```text
Mailerone/
├── .gitignore              # Git ignore configuration
├── .validator              # Validator endpoint reference
├── LICENSE                 # License file
├── README.md               # Documentation & usage guide
├── requirements.txt        # Python dependency manifest
├── run.bat                 # Windows batch launcher
├── Mailerone.py            # Main application entry point & CLI dashboard
├── api_engines.py          # Modular verification & lead finding engines
├── config_manager.py       # Configuration loading and persistence
├── config.json             # API keys and engine configuration
├── mail_validator.py       # Direct SMTP handshake & multi-provider validator
├── multi_verifier.py       # All-in-one comprehensive scanner & score calculator
├── test_suite.py           # Engine verification test suite
└── test_results.json       # Automated test suite run outputs
```

---

## ⚖️ License

This project is licensed under the **Apache License 2.0**. See the [LICENSE](LICENSE) file for full details.

## ⚠️ Disclaimer

This tool is designed for educational purposes, authorized penetration testing, security auditing, and legitimate OSINT/sales research. Ensure you comply with applicable laws and terms of service before querying domains and third-party APIs.