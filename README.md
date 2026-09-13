# 📧 Mailerone


<p align="center">
  <strong>Comprehensive Email Finding, Multi-API Deliverability Verification & OSINT Suite</strong>
</p>

<p align="center">
  <a href="https://github.com/Souvik2biswas/Mailerone"><img src="https://img.shields.io/badge/Version-2.0-blue?style=for-the-badge&logo=python" alt="Version 2.0"></a>
  <a href="https://github.com/Souvik2biswas/Mailerone/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-GPL--3.0-green?style=for-the-badge" alt="License"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.8%2B-yellow?style=for-the-badge&logo=python" alt="Python 3.8+"></a>
  <a href="https://github.com/Souvik2biswas/Mailerone/stargazers"><img src="https://img.shields.io/github/stars/Souvik2biswas/Mailerone?style=for-the-badge&color=orange" alt="GitHub Stars"></a>
  <a href="https://github.com/Souvik2biswas/Mailerone/issues"><img src="https://img.shields.io/github/issues/Souvik2biswas/Mailerone?style=for-the-badge&color=red" alt="GitHub Issues"></a>
</p>

---

## 🚀 Overview

**Mailerone** is an advanced, all-in-one email intelligence and OSINT toolkit designed for security researchers, penetration testers, OSINT investigators, and sales engineers. It combines DNS protocol checks, SMTP server handshakes, disposable domain detection, and integrations with industry-leading verification engines into a unified, interactive terminal dashboard.

---

## ✨ Features

- **🌐 Domain & DNS Inspector**
  - Instant discovery of active MX (Mail Exchange) records.
  - Verification of **SPF** (Sender Policy Framework) & **DMARC** security policies.
  - Real-time cross-referencing against an extensive blocklist of **8,700+ disposable / burner email domains**.
  - Whitelist and free provider detection via Disify API.

- **⚡ Multi-Engine Deliverability Scan (All-in-One)**
  - Comprehensive deliverability analysis aggregating DNS, SMTP handshake, Disify, Hunter.io, AbstractAPI, ZeroBounce, Debounce, and Mailboxlayer.
  - Calculated **Deliverability Score (0–100%)** with clear status indicators: `DELIVERABLE`, `RISKY`, or `UNDELIVERABLE`.

- **🔍 Username Search Across 70+ Email Providers**
  - Check existence of target usernames across 70+ popular mail services (Gmail, Yahoo, Outlook, ProtonMail, Mail.ru, Yandex, iCloud, Zoho, etc.).

- **🎯 Hunter.io Email Verification & Finder**
  - Single email verification and confidence scoring.
  - Find corporate email addresses from **First Name + Last Name + Company Domain**.

- **🛡️ Multi-API Verifier Engines**
  - **AbstractAPI**: Real-time deliverability, SMTP checks, and catch-all detection.
  - **ZeroBounce**: Status, sub-status, and account validity verification.
  - **DeBounce**: RFC-compliant syntax, DNS verification, and disposable filtering.
  - **Mailboxlayer**: Real-time syntax and SMTP route checking.

- **🕵️ OSINT & Identity Profiler**
  - **Gravatar Integration**: Extract real names, profile usernames, bios, and avatar images.
  - **GitHub Commit Search**: Discover associated GitHub profiles and commits by email address.
  - **EmailRep.io**: Check domain age, reputation, spam history, data breaches, and suspicious activity.

- **🔀 Name-to-Email Permutation Generator**
  - Generate standard business email patterns (`first.last@domain`, `f.last@domain`, `first@domain`, etc.) and verify deliverability.

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
                  .:.:;.. Mailerone v2.0 (Multi-API Enhanced) ..;:.:.

    >> Comprehensive Email Finding, Multi-API Deliverability & OSINT Suite

    [1] Domain Inspector (DNS, MX, SPF, DMARC & Burner Check)
    [2] Check Username across 70+ Email Domains
     |
    [3] Comprehensive Multi-Engine Email Scan (All-in-One)
     |
    [4] Hunter.io Suite (Email Verifier & Name+Domain Finder)
    [5] AbstractAPI Email Verifier
    [6] ZeroBounce / Debounce / Mailboxlayer Verifiers
    [7] OSINT & Identity Profiler (Gravatar + GitHub + EmailRep)
    [8] Search Email via Full Name (Permutation Generator)
     |
    [9] API Keys Configuration Manager
    [0] Exit Mailerone
```

---

## 🔑 API Configuration

You can use basic domain inspection, burner checks, and username scans without any API keys. For advanced API features, configure keys either:
1. Inside the app via **Option `[9] API Keys Configuration Manager`**, or
2. By editing `config.json`:

```json
{
    "hunter_api_keys": [
        "YOUR_HUNTER_API_KEY"
    ],
    "abstract_api_key": "YOUR_ABSTRACT_KEY",
    "zerobounce_api_key": "YOUR_ZEROBOUNCE_KEY",
    "debounce_api_key": "YOUR_DEBOUNCE_KEY",
    "mailboxlayer_api_key": "YOUR_MAILBOXLAYER_KEY",
    "emailrep_api_key": "YOUR_EMAILREP_KEY",
    "github_token": "YOUR_GITHUB_PERSONAL_ACCESS_TOKEN"
}
```

---

## 🧪 Running the Test Suite

Mailerone includes a built-in automated test suite to verify module integrity and API engine functionality:

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
├── api_engines.py          # Modular verification engines (DNS, Hunter, Abstract, etc.)
├── config_manager.py       # Configuration loading and persistence
├── config.json             # API keys and engine configuration
├── mail_validator.py       # Direct SMTP handshake & multi-provider validator
├── multi_verifier.py       # All-in-one comprehensive scanner & score calculator
├── test_suite.py           # Engine verification test suite
└── test_results.json       # Automated test suite run outputs
```

---

## ⚖️ License

This project is licensed under the **GNU General Public License v3.0**. See the [LICENSE](LICENSE) file for full details.

## ⚠️ Disclaimer

This tool is designed for educational purposes, authorized penetration testing, security auditing, and legitimate OSINT research. Ensure you comply with applicable laws and terms of service before querying domains and third-party APIs.