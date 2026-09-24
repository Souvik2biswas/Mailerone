import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

CANONICAL_KEY_MAP = {
    "hunter": "hunter_api_keys",
    "hunter_api_key": "hunter_api_keys",
    "hunter_api_keys": "hunter_api_keys",
    "abstract": "abstract_api_keys",
    "abstract_api_key": "abstract_api_keys",
    "abstract_api_keys": "abstract_api_keys",
    "zerobounce": "zerobounce_api_keys",
    "zerobounce_api_key": "zerobounce_api_keys",
    "zerobounce_api_keys": "zerobounce_api_keys",
    "debounce": "debounce_api_keys",
    "debounce_api_key": "debounce_api_keys",
    "debounce_api_keys": "debounce_api_keys",
    "mailboxlayer": "mailboxlayer_api_keys",
    "mailboxlayer_api_key": "mailboxlayer_api_keys",
    "mailboxlayer_api_keys": "mailboxlayer_api_keys",
    "emailrep": "emailrep_api_keys",
    "emailrep_api_key": "emailrep_api_keys",
    "emailrep_api_keys": "emailrep_api_keys",
    "contactout": "contactout_api_keys",
    "contactout_api_key": "contactout_api_keys",
    "contactout_api_keys": "contactout_api_keys",
    "salesql": "salesql_api_keys",
    "salesql_api_key": "salesql_api_keys",
    "salesql_api_keys": "salesql_api_keys",
    "signalhire": "signalhire_api_keys",
    "signalhire_api_key": "signalhire_api_keys",
    "signalhire_api_keys": "signalhire_api_keys",
    "finalscout": "finalscout_api_keys",
    "finalscout_api_key": "finalscout_api_keys",
    "finalscout_api_keys": "finalscout_api_keys",
    "github": "github_tokens",
    "github_token": "github_tokens",
    "github_tokens": "github_tokens",
}

DEFAULT_CONFIG = {
    "hunter_api_keys": [
        "5d5015259730682de8b542355525b16ab7026c976a72993d",
        "83e338e3a43cdcc649a1ea49957d2c0223b601bb",
        "36a4ce62890b18e216951bb2cf4b9748129418f8"
    ],
    "abstract_api_keys": [],
    "zerobounce_api_keys": [],
    "debounce_api_keys": [],
    "mailboxlayer_api_keys": [],
    "emailrep_api_keys": [],
    "contactout_api_keys": [],
    "salesql_api_keys": [],
    "signalhire_api_keys": [],
    "finalscout_api_keys": [],
    "github_tokens": []
}

def normalize_keys(raw_val):
    """Normalize string, list, or comma-separated keys into a list of non-empty strings."""
    if not raw_val:
        return []
    keys = []
    if isinstance(raw_val, list):
        for item in raw_val:
            if isinstance(item, str):
                for part in item.split(","):
                    p = part.strip()
                    if p and p not in keys:
                        keys.append(p)
            elif item:
                s = str(item).strip()
                if s and s not in keys:
                    keys.append(s)
    elif isinstance(raw_val, str):
        for part in raw_val.split(","):
            p = part.strip()
            if p and p not in keys:
                keys.append(p)
    return keys

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            # Ensure all canonical default keys exist
            for k, v in DEFAULT_CONFIG.items():
                if k not in cfg:
                    cfg[k] = v
            return cfg
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def get_api_keys(service_name):
    """Retrieve all configured keys for a service as a list of strings."""
    cfg = load_config()
    canonical = CANONICAL_KEY_MAP.get(service_name, service_name)
    
    # 1. Try canonical plural key
    val = cfg.get(canonical)
    if val:
        keys = normalize_keys(val)
        if keys:
            return keys
            
    # 2. Try raw service_name
    val = cfg.get(service_name)
    if val:
        keys = normalize_keys(val)
        if keys:
            return keys

    # 3. Check singular alias if service ends in _keys or _tokens
    if canonical.endswith("_keys"):
        singular = canonical[:-1]  # e.g. abstract_api_key
        val = cfg.get(singular)
        if val:
            return normalize_keys(val)
    elif canonical.endswith("_tokens"):
        singular = canonical[:-1]  # e.g. github_token
        val = cfg.get(singular)
        if val:
            return normalize_keys(val)

    return []

def get_api_key(service_name):
    """Backwards-compatible single key getter. Returns first available key or empty string."""
    keys = get_api_keys(service_name)
    return keys[0] if keys else ""

def set_api_keys(service_name, key_values):
    """Save multiple keys for a service."""
    cfg = load_config()
    canonical = CANONICAL_KEY_MAP.get(service_name, service_name)
    cleaned = normalize_keys(key_values)
    cfg[canonical] = cleaned
    
    # Also update singular legacy key for backwards compatibility if applicable
    if canonical.endswith("_keys"):
        singular = canonical[:-1]
        cfg[singular] = cleaned[0] if cleaned else ""
    elif canonical.endswith("_tokens"):
        singular = canonical[:-1]
        cfg[singular] = cleaned[0] if cleaned else ""
    elif service_name in cfg and service_name != canonical:
        cfg[service_name] = cleaned[0] if cleaned else ""
        
    save_config(cfg)
    return cleaned

def set_api_key(service_name, key_value):
    """Save single or comma-separated key(s) for a service."""
    return set_api_keys(service_name, key_value)

def add_api_key(service_name, new_key):
    """Add a new key to the service's key list if not already present."""
    keys = get_api_keys(service_name)
    clean_new = normalize_keys(new_key)
    for k in clean_new:
        if k not in keys:
            keys.append(k)
    return set_api_keys(service_name, keys)

def remove_api_key(service_name, key_to_remove):
    """Remove a specific key from the service's key list."""
    keys = get_api_keys(service_name)
    target = key_to_remove.strip()
    keys = [k for k in keys if k != target]
    return set_api_keys(service_name, keys)
