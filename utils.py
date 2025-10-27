import os, json, hashlib
from datetime import datetime

def log_action(action):
    os.makedirs(".database/.logs", exist_ok=True)
    log_file = ".database/.logs/actions.log"
    with open(log_file, "a") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : {action}\n")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_config():
    if os.path.exists("config.json"):
        with open("config.json") as f:
            return json.load(f)
    return {}


def getAllType(_path):
    if os.path.exists(_path):
        with open(_path, 'r', encoding='utf-8') as f:
            
            return