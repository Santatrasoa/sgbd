# main.py
import os
import readline
from utils.config_loader import load_config
from utils.crypto import CryptoManager
from db.db_main import Db
from commands import *

config = load_config()
DB_PATH = config["db_path"]
DEFAULT_PROMPT = config["default_prompt"]
SEPARATOR = config["separator_char"]
USER = config["default_admin"]["username"]

# === MOT DE PASSE PAR DÉFAUT ===
DEFAULT_MASTER_PASSWORD = "mon_mot_de_passe_secret_2025"
crypto = CryptoManager(DEFAULT_MASTER_PASSWORD)


db = Db(DB_PATH, crypto=crypto)
useDatabase = ""
isDbUse = False
userUsingDb = f"user:\033[32m{db.current_user['username']}\033[0m"
promptContainte = f"[{userUsingDb}]\n{DEFAULT_PROMPT} "

if os.path.exists(".history"):
    try: readline.read_history_file(".history")
    except: pass

print("╔══════════════════════════════════════════════════════════════╗")
print("║     Welcome to MY - Your personal DBMS                       ║")
print("╚══════════════════════════════════════════════════════════════╝")
print("Type 'help'\n")
print(USER)

while True:
    print("")
    try:
        cmd = input("my ~ " + promptContainte)
    except KeyboardInterrupt:
        print("\n^C")
        continue
    except EOFError:
        readline.write_history_file(".history")
        print("\nIt was my ...Bye!")
        exit()

    if cmd.strip() in ["clear", "clear;"]:
        os.system("clear" if os.name != "nt" else "cls")
        continue
    if cmd.strip() in ["exit", "exit;"]:
        readline.write_history_file(".history")
        print("\nIt was my ...Bye!")
        exit()

    while not cmd.endswith(";"):
        try:
            cmd += " " + input(" ⇘ ").strip()
        except: break
    cmd = cmd.replace(";", "").strip()
    if not cmd: continue
    cmd_line = cmd.split(" ")[0].lower()


    result = None, None

    if cmd_line.startswith(("create_db", "use_db", "drop_db", "leave_db", "list_db", "stats_db")):
        result = handle_db_commands(cmd, cmd_line, db, userUsingDb, DEFAULT_PROMPT, SEPARATOR)

    elif cmd_line in ["create_table", "add_into_table", "drop_table", "list_table", "describe_table"]:
        if not isDbUse:
            print("No database selected")
            continue
        handle_table_commands(cmd, cmd_line, db, useDatabase, isDbUse, SEPARATOR, config)

    elif cmd_line in ["select", "update", "delete"]:
        if not isDbUse:
            print("No database selected")
            continue
        handle_query_commands(cmd, cmd_line, db, useDatabase, isDbUse, SEPARATOR)

    elif cmd_line in ["create_user", "list_user", "drop_user", "switch_user_to", "grant", "revoke", "show_grants"]:
        result = handle_user_perm_commands(cmd, cmd_line, db, useDatabase, isDbUse, DEFAULT_PROMPT)

    elif cmd_line in ["help", "list_commands"]:
        db.show_help()

    else:
        print(f"Unknown command: {cmd_line}")

    if result is not None and result[0] is not None:
        userUsingDb, promptContainte = result[0], result[1]
        globals()['userUsingDb'] = userUsingDb
        globals()['promptContainte'] = promptContainte

        # Si c'est une commande DB → 4 valeurs
        if len(result) == 4:
            useDatabase, isDbUse = result[2], result[3]
            globals()['useDatabase'] = useDatabase
            globals()['isDbUse'] = isDbUse