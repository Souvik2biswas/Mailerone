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
    "hunter_api_keys": [],
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

USER_CONFIG_FILE = os.path.expanduser("~/.mailerone/config.json")

def _load_device_env():
    """Load key-value pairs from local device .env without committing to codebase."""
    env_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
        os.path.expanduser("~/.env")
    ]
    for p in env_paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip("'\"")
                            if k and k not in os.environ:
                                os.environ[k] = v
            except Exception:
                pass

_load_device_env()

def load_config():
    # 1. Prefer local project config.json (ignored by git, kept on device)
    target_file = CONFIG_FILE if os.path.exists(CONFIG_FILE) else (USER_CONFIG_FILE if os.path.exists(USER_CONFIG_FILE) else CONFIG_FILE)
    
    if not os.path.exists(target_file):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(target_file, "r", encoding="utf-8") as f:
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
        # Ensure directory exists if saving to user profile
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def get_api_keys(service_name):
    """Retrieve all configured keys for a service as a list of strings from device storage / env."""
    cfg = load_config()
    canonical = CANONICAL_KEY_MAP.get(service_name, service_name)
    keys = []
    
    # 1. Try canonical plural key from local device config
    val = cfg.get(canonical)
    if val:
        keys = normalize_keys(val)
            
    # 2. Try raw service_name
    if not keys:
        val = cfg.get(service_name)
        if val:
            keys = normalize_keys(val)

    # 3. Check singular alias if service ends in _keys or _tokens
    if not keys:
        if canonical.endswith("_keys"):
            singular = canonical[:-1]  # e.g. abstract_api_key
            val = cfg.get(singular)
            if val:
                keys = normalize_keys(val)
        elif canonical.endswith("_tokens"):
            singular = canonical[:-1]  # e.g. github_token
            val = cfg.get(singular)
            if val:
                keys = normalize_keys(val)

    # 4. Check on-device environment variables (e.g. HUNTER_API_KEYS, HUNTER_API_KEY)
    env_candidates = [
        canonical.upper(),
        service_name.upper(),
        f"{canonical.upper()}_KEY",
        f"{canonical.upper()}_KEYS",
        f"{service_name.upper()}_API_KEY",
        f"{service_name.upper()}_API_KEYS",
        f"{service_name.upper()}_KEY",
        f"{service_name.upper()}_TOKEN"
    ]
    for env_var in env_candidates:
        env_val = os.environ.get(env_var)
        if env_val:
            for k in normalize_keys(env_val):
                if k not in keys:
                    keys.append(k)

    return keys

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
