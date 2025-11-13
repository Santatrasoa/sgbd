# main.py
import os
import readline
import getpass  # ← AJOUT IMPORTANT
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
HISTORY_DIR_PATH = config.get("history_dir", ".history_dir")

# === CRÉATION DU DOSSIER HISTORY SI MANQUANT ===
HISTORY_DIR = Path(HISTORY_DIR_PATH)
HISTORY_DIR.mkdir(exist_ok=True)

# === CHIFFREMENT ===
DEFAULT_MASTER_PASSWORD = "mit_misa_password_123!!!"
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
    clear_readline_history()
    hist_file = get_history_file(username)
    if hist_file.exists():
        try:
            readline.read_history_file(str(hist_file))
        except Exception as e:
            print(f"⚠️ Could not load history for {username}: {e}")

def save_user_history(username: str):
    hist_file = get_history_file(username)
    try:
        readline.write_history_file(str(hist_file))
    except Exception as e:
        print(f"⚠️ Could not save history for {username}: {e}")

# Charge l'historique de root au démarrage
load_user_history("root")

# === PROMPT DYNAMIQUE ===
def get_prompt():
    user_part = f"user:\033[32m{current_user}\033[0m"
    db_part = f" & db:\033[34m{useDatabase}\033[0m" if isDbUse else ""
    return f"[{user_part}{db_part}]\n{DEFAULT_PROMPT} "

# === BIENVENUE ===
print("╔══════════════════════════════════════════════════════════════╗")
print("║                    Welcome to my_diaries                     ║")
print("╚══════════════════════════════════════════════════════════════╝")
print("Type 'help' to see available commands\n")

# === BOUCLE PRINCIPALE ===
while True:
    print("")
    try:
        cmd = input("my_diaries ~ " + get_prompt())
    except KeyboardInterrupt:
        print("\n^C")
        continue
    except EOFError:
        save_user_history(current_user)
        clear_readline_history()
        print("\nBye! Thanks for using my_diaries")
        exit()

    # === COMMANDES SYSTÈME SIMPLES (sans ;) ===
    if cmd.strip() in ["clear", "clear;"]:
        os.system("clear" if os.name != "nt" else "cls")
        continue

    if cmd.strip() in ["exit", "exit;"]:
        save_user_history(current_user)
        clear_readline_history()
        print("Bye! Thanks for using my_diaries")
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
            print("\nBye! Thanks for using my_diaries")
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

    if cmd_line == "switch_to":
        try:
            parts = cmd.split()
            if len(parts) < 2:
                print("Username required")
                print("Usage: switch_to <username>;")
                continue
            
            username = parts[1]
            
            # Vérifier si password= est dans la commande (ancien mode)
            pwd_part = [p for p in parts if p.startswith("password=")]
            
            if not pwd_part:
                password = getpass.getpass("Password: ")
            else:
                password = pwd_part[0].split("=", 1)[1]
                print("⚠️ Warning: Password visible in command history!")
            
            # Tenter la connexion
            new_user = db.userManager.switch_to(username, password)
            
            if new_user:
                save_user_history(current_user)
                
                clear_readline_history()
                
                current_user = username
                db.current_user = new_user
                
                load_user_history(current_user)
                
                print(f"✓ Switched to user '{current_user}'")
            else:
                print("Invalid username or password")
                
        except Exception as e:
            print(f"Error: {e}")
            print("Usage: switch_to <username>;")
        
        continue
    elif cmd_line == "alter_table":
        if not isDbUse:
            print("No database selected")
            print("Use: use_db <database_name>;")
            continue
        
        # Importer et appeler la fonction
        from commands.table_commands import handle_alter_table
        handle_alter_table(cmd, db, useDatabase, config)
        continue

    # === COMMANDES DB ===
    if cmd_line in ["create_db", "create_database", "use_database", "use_db", "drop_db", "list_database","list_db", "stats_db", "leave_db"]:
        result = handle_db_commands(cmd, cmd_line, db, get_prompt(), DEFAULT_PROMPT, SEPARATOR)

    # === COMMANDES TABLE ===
    elif cmd_line in ["create_table", "add_into_table", "list_table", "describe_table", "drop_table"]:
        if not isDbUse:
            print("No database selected")
            print("Use: use_db <database_name>;")
            continue
        handle_table_commands(cmd, cmd_line, db, useDatabase, isDbUse, SEPARATOR, config)

    # === REQUÊTES SQL ===
    elif cmd_line in ["select", "update", "delete"]:
        if not isDbUse:
            print("No database selected")
            print("Use: use_db <database_name>;")
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
        print(f"Unknown command: '{cmd_line}'")
        print("Type 'help' for available commands")
        continue

    # === MISE À JOUR PROMPT ===
    if result is not None and len(result) >= 4:
        _, _, useDatabase, isDbUse = result