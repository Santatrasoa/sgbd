import os
import getpass
from pathlib import Path
from utils.config_loader import load_config
from utils.crypto import CryptoManager
from db.db_main import Db

try:
    import readline
except ImportError:
    try:
        import pyreadline as readline
    except ImportError:
        print("Warning: readline module not fully available. Command history will be limited.")
        class DummyReadline:
            def get_current_history_length(self): return 0
            def remove_history_item(self, index): pass
            def read_history_file(self, filename): pass
            def write_history_file(self, filename): pass
        readline = DummyReadline()

from commands.db_commands import handle_db_commands
from commands.user_perm_commands import handle_user_perm_commands
from commands.table_commands import handle_alter_table, handle_table_commands
from commands.query_commands import handle_query_commands


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

# === HISTORIQUE PAR UTILISATEUR (SÉCURISÉ) ===
def get_history_file(username: str) -> Path:
    return HISTORY_DIR / f".history_{username}"

def clear_readline_history():
    """Vide l'historique en mémoire de readline"""
    # Vérifie si l'objet readline n'est pas l'objet Dummy
    if hasattr(readline, 'get_current_history_length'):
        while readline.get_current_history_length():
            readline.remove_history_item(0)

def load_user_history(username: str):
    clear_readline_history()
    hist_file = get_history_file(username)
    # Vérifie si l'objet readline n'est pas l'objet Dummy
    if hasattr(readline, 'read_history_file'):
        if hist_file.exists():
            try:
                readline.read_history_file(str(hist_file))
            except Exception as e:
                print(f"Could not load history for {username}: {e}")

def save_user_history(username: str):
    hist_file = get_history_file(username)
    # Vérifie si l'objet readline n'est pas l'objet Dummy
    if hasattr(readline, 'write_history_file'):
        try:
            readline.write_history_file(str(hist_file))
        except Exception as e:
            print(f"Could not save history for {username}: {e}")

# === PROMPT DYNAMIQUE ===
def get_prompt():
    user_part = f"user:\033[32m{current_user}\033[0m"
    db_part = f" & db:\033[34m{useDatabase}\033[0m" if isDbUse else ""
    # Le prompt d'entrée est maintenant séparé du décorateur statique
    return f"[{user_part}{db_part}]\n{DEFAULT_PROMPT} "

# === AUTHENTIFICATION AU DÉMARRAGE ===
def login():
    """Demande les identifiants au démarrage"""
    
    max_attempts = 3 # Nombre d'essais standard
    attempts = 0
    
    while attempts < max_attempts:
        try:
            username = input("Username: ").strip()
            
            if not username:
                print("Username cannot be empty\n")
                attempts += 1
                continue # Correction: 'continue' au lieu de 'continues'
            
            password = getpass.getpass("Password: ")
            
            user = db.userManager.switch_to(username, password)
            
            if user:
                print("╔══════════════════════════════════════════════════════════════╗")
                print("║                    Welcome to my_diaries                     ║")
                print("╚══════════════════════════════════════════════════════════════╝")
                print()
                print("Type 'help' to see available commands\n")
                return user
            else:
                attempts += 1
                remaining = max_attempts - attempts
                if remaining > 0:
                    print(f"Invalid credentials. {remaining} attempt(s) remaining\n")
                else:
                    break 
                    
        except KeyboardInterrupt:
            print("\n\nLogin cancelled. Exiting...")
            exit(0)
        except EOFError:
            print("\n\nLogin cancelled. Exiting...")
            exit(0)
    
    print("Authentication failed. Exiting...")
    exit(1)

logged_user = login()
current_user = logged_user["username"]

useDatabase = ""
isDbUse = False

load_user_history(current_user)

while True:
    try:
        # Le prompt statique est maintenant intégré dans get_prompt()
        cmd = input(get_prompt())
    except KeyboardInterrupt:
        print("\n^C")
        continue
    except EOFError:
        save_user_history(current_user)
        clear_readline_history()
        print("\nBye! Thanks for using my_diaries")
        exit()

    # --- Nettoyage de l'écran avant le parsing de commande ---
    if cmd.strip() in ["clear", "clear;"]:
        # Pour Windows: 'cls', pour Unix-like: 'clear'
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

    cmd = cmd.strip()
    if not cmd.endswith(";"):
        continue
    cmd = cmd[:-1].strip()
    if not cmd:
        continue

    cmd_line = cmd.split(" ", 1)[0].lower() if " " in cmd else cmd.lower()
    print(cmd_line)
    result = None

    # Redondance pour 'clear' et 'exit' au cas où l'utilisateur les tape sans point-virgule
    if cmd_line.strip() == "clear":
        os.system("clear" if os.name != "nt" else "cls")
        continue
    if cmd_line.strip() == "exit":
        save_user_history(current_user)
        clear_readline_history()
        print("Bye! Thanks for using my_diaries")
        exit()

    if cmd_line == "switch_to":
        try:
            parts = cmd.split()
            if len(parts) < 2:
                print("Username required")
                print("Usage: switch_to <username>;")
                continue
            
            username = parts[1]
            
            pwd_part = [p for p in parts if p.startswith("password=")]
            
            if not pwd_part:
                password = getpass.getpass("Password: ")
            else:
                password = pwd_part[0].split("=", 1)[1]
                print("Warning: Password visible in command history!")
            
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
    # Le résultat de handle_db_commands contient l'état de la base de données actuelle
    if result is not None and len(result) >= 4:
        # On extrait useDatabase et isDbUse du résultat de la commande
        _, _, useDatabase, isDbUse = result