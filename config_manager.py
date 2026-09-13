import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

DEFAULT_CONFIG = {
    "hunter_api_keys": [
        "5d5015259730682de8b542355525b16ab7026c976a72993d",
        "83e338e3a43cdcc649a1ea49957d2c0223b601bb",
        "36a4ce62890b18e216951bb2cf4b9748129418f8"
    ],
    "abstract_api_key": "",
    "zerobounce_api_key": "",
    "debounce_api_key": "",
    "mailboxlayer_api_key": "",
    "emailrep_api_key": "",
    "github_token": ""
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            # Ensure all keys exist
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

def get_api_key(service_name):
    cfg = load_config()
    return cfg.get(service_name, "")

def set_api_key(service_name, key_value):
    cfg = load_config()
    cfg[service_name] = key_value
    save_config(cfg)
