# main.py
import os
import readline
from pathlib import Path
from utils.config_loader import load_config
from utils.crypto import CryptoManager
from db.db_main import Db
from commands import *

# === CONFIG ===
config = load_config()
DB_PATH = config["db_path"]
DEFAULT_PROMPT = config["default_prompt"]
SEPARATOR = config["separator_char"]
HISTORY_DIR_PATH = config.get("history_dir", ".history_dir")  # Configurable

# === CRÉATION DU DOSSIER HISTORY SI MANQUANT ===
HISTORY_DIR = Path(HISTORY_DIR_PATH)
HISTORY_DIR.mkdir(exist_ok=True)

# === CHIFFREMENT ===
DEFAULT_MASTER_PASSWORD = "mon_mot_de_passe_secret_2025"
crypto = CryptoManager(DEFAULT_MASTER_PASSWORD)

# === DB ===
db = Db(DB_PATH, crypto=crypto)

# === ÉTAT ===
useDatabase = ""
isDbUse = False
current_user = db.current_user["username"]

# === HISTORIQUE PAR UTILISATEUR (SÉCURISÉ) ===
def get_history_file(username: str) -> Path:
    return HISTORY_DIR / f".history_{username}"

def clear_readline_history():
    """Vide l'historique en mémoire de readline"""
    while readline.get_current_history_length():
        readline.remove_history_item(0)

def load_user_history(username: str):
    clear_readline_history()  # VIDE AVANT CHARGEMENT
    hist_file = get_history_file(username)
    if hist_file.exists():
        try:
            readline.read_history_file(str(hist_file))
        except Exception as e:
            print(f"Warning: Could not load history for {username}: {e}")

def save_user_history(username: str):
    hist_file = get_history_file(username)
    try:
        readline.write_history_file(str(hist_file))
    except Exception as e:
        print(f"Warning: Could not save history for {username}: {e}")

# Charge l'historique de root au démarrage
load_user_history("root")

# === PROMPT DYNAMIQUE ===
def get_prompt():
    user_part = f"user:\033[32m{current_user}\033[0m"
    db_part = f" & db:\033[34m{useDatabase}\033[0m" if isDbUse else ""
    return f"[{user_part}{db_part}]\n{DEFAULT_PROMPT} "

# === BIENVENUE ===
print("╔══════════════════════════════════════════════════════════════╗")
print("║       SGBD SÉCURISÉ – HISTORIQUE ISOLÉ PAR USER – ; OBLIGATOIRE       ║")
print("╚══════════════════════════════════════════════════════════════╝")
print("Tape 'help' pour voir les commandes\n")

# === BOUCLE PRINCIPALE ===
while True:
    print("")
    try:
        cmd = input("my ~ " + get_prompt())
    except KeyboardInterrupt:
        print("\n^C")
        continue
    except EOFError:
        save_user_history(current_user)
        clear_readline_history()
        print("\nBye! Thanks for using MY")
        exit()

    # === COMMANDES SYSTÈME SIMPLES (sans ;) ===
    if cmd.strip() in ["clear", "clear;"]:
        os.system("clear" if os.name != "nt" else "cls")
        continue

    if cmd.strip() in ["exit", "exit;"]:
        save_user_history(current_user)
        clear_readline_history()
        print("Bye! Thanks for using MY")
        exit()

    # === GESTION DES COMMANDES MULTI-LIGNES ===
    while not cmd.strip().endswith(";"):
        try:
            next_line = input(" ⇘ ")
        except KeyboardInterrupt:
            print("\n^C")
            cmd = ""
            break
        except EOFError:
            save_user_history(current_user)
            clear_readline_history()
            print("\nAu revoir ! Merci d'avoir utilisé MY")
            exit()
        cmd += " " + next_line.strip()

    # === NETTOYAGE DE LA COMMANDE ===
    cmd = cmd.strip()
    if not cmd.endswith(";"):
        continue
    cmd = cmd[:-1].strip()
    if not cmd:
        continue

    # === ANALYSE ===
    cmd_line = cmd.split(" ", 1)[0].lower() if " " in cmd else cmd.lower()
    result = None

    # === SWITCH USER (SÉCURISÉ) ===
    if cmd_line == "switch_user_to":
        parts = cmd.split(" ", 2)
        if len(parts) < 3 or "password=" not in parts[2]:
            print("Usage: switch_user_to <user> password=<pass>;")
            continue
        username = parts[1]
        password = parts[2].split("=", 1)[1] if "=" in parts[2] else ""
        new_user = db.userManager.switch_user_to(username, password)
        if new_user:
            # 1. SAUVEGARDE l'actuel
            save_user_history(current_user)
            # 2. VIDE readline
            clear_readline_history()
            # 3. CHANGE d'utilisateur
            current_user = username
            db.current_user = new_user
            # 4. CHARGE le nouvel historique
            load_user_history(current_user)
            print(f"Switched to user '{current_user}'")
        continue

    # === COMMANDES DB ===
    if cmd_line in ["create_db", "use_db", "drop_db", "list_db", "stats_db", "leave_db"]:
        result = handle_db_commands(cmd, cmd_line, db, get_prompt(), DEFAULT_PROMPT, SEPARATOR)

    # === COMMANDES TABLE ===
    elif cmd_line in ["create_table", "add_into_table", "list_table", "describe_table", "drop_table"]:
        if not isDbUse:
            print("No database selected")
            continue
        handle_table_commands(cmd, cmd_line, db, useDatabase, isDbUse, SEPARATOR, config)

    # === REQUÊTES SQL ===
    elif cmd_line in ["select", "update", "delete"]:
        if not isDbUse:
            print("No database selected")
            continue
        handle_query_commands(cmd, cmd_line, db, useDatabase, isDbUse, SEPARATOR)

    # === GESTION UTILISATEURS & PERMISSIONS ===
    elif cmd_line in ["create_user", "list_user", "drop_user", "grant", "revoke", "show_grants"]:
        result = handle_user_perm_commands(cmd, cmd_line, db, useDatabase, isDbUse, DEFAULT_PROMPT)

    # === HELP ===
    elif cmd_line in ["help", "list_commands"]:
        db.show_help()

    # === COMMANDE INCONNUE ===
    else:
        print(f"Unknown command: '{cmd_line}'. Type 'help' for available commands.")
        continue

    # === MISE À JOUR PROMPT (dynamique via get_prompt()) ===
    if result is not None and len(result) >= 4:
        _, _, useDatabase, isDbUse = result