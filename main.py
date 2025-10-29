"""
MY SGBD - Système de Gestion de Base de Données Personnel
Version 2.0 - Modularisée

Point d'entrée principal du programme
"""

import os
import readline
from pathlib import Path

from db.db_main import Db
from utils import load_config
from commands.database_commands import handle_database_commands
from commands.table_commands import handle_table_commands
from commands.query_commands import handle_query_commands
from commands.user_commands import handle_user_commands
from commands.permission_commands import handle_permission_commands

# ============================================================================
# CONFIGURATION
# ============================================================================
config = load_config()
DB_PATH = config.get("db_path", ".database")
DEFAULT_PROMPT = config.get("default_prompt", "m¥⇒")
SEPARATOR = config.get("separator_char", "—")

# ============================================================================
# INITIALISATION
# ============================================================================

# Créer l'instance de base de données
db = Db(DB_PATH)

# Variables de session
session = {
    'useDatabase': "",
    'isDbUse': False,
    'db': db,
    'DB_PATH': DB_PATH,
    'SEPARATOR': SEPARATOR
}

# Formater le prompt avec l'utilisateur actuel
def get_prompt():
    """Génère le prompt en fonction de l'état de la session"""
    userUsingDb = f"user:\033[32m{session['db'].current_user['username']}\033[0m"
    if session['isDbUse']:
        return f"[{userUsingDb} & db:\033[34m{session['useDatabase']}\033[0m]\n{DEFAULT_PROMPT} "
    return f"[{userUsingDb}]\n{DEFAULT_PROMPT} "

# Charger l'historique des commandes
if os.path.exists(".history"):
    try:
        readline.read_history_file(".history")
    except Exception:
        pass

# Message de bienvenue
print("╔══════════════════════════════════════════════════════════════╗")
print("║          Welcome to MY - Your personal DBMS                  ║")
print("╚══════════════════════════════════════════════════════════════╝")
print("Type 'help' to see available commands\n")

# ============================================================================
# BOUCLE PRINCIPALE
# ============================================================================

def main():
    """Boucle principale du programme"""
    while True:
        print("")
        try:
            cmd = input("my ~ " + get_prompt())
        except KeyboardInterrupt:
            print("\n^C")
            continue
        except EOFError:
            readline.write_history_file(".history")
            print("\nBye! Thanks for using MY")
            exit()

        # Commandes système simples
        if cmd.strip() in ["clear", "clear;"]:
            os.system("clear" if os.name != "nt" else "cls")
            continue
        
        if cmd.strip() in ["exit", "exit;"]:
            readline.write_history_file(".history")
            print("Bye! Thanks for using MY")
            exit()

        # Gestion des commandes multi-lignes
        while not cmd.endswith(";"):
            try:
                next_line = input(" ⇘ ")
            except KeyboardInterrupt:
                print("\n^C")
                break
            except EOFError:
                print("\nAu revoir ! Merci d'avoir utilisé MY")
                readline.write_history_file(".history")
                exit()
            cmd += " " + next_line.strip()

        # Nettoyer la commande
        cmd = cmd.replace(";", "").strip()
        if not cmd:
            continue
        
        # Extraire le mot-clé de la commande
        cmd_line = cmd.split(" ")[0].lower()

        # Router les commandes vers les bons handlers
        handled = False

        # Commandes de base de données
        if cmd_line in ["create_database", "create_db", "use_database", "use_db", 
                       "drop_database", "drop_db", "leave_database", "leave_db",
                       "list_database", "list_db", "stats_db", "database_stats"]:
            handle_database_commands(cmd, cmd_line, session)
            handled = True

        # Commandes de tables
        elif cmd_line in ["create_table", "add_into_table", "drop_table", 
                         "list_table", "describe_table"]:
            handle_table_commands(cmd, cmd_line, session)
            handled = True

        # Commandes de requêtes
        elif cmd_line in ["select", "update", "delete"]:
            handle_query_commands(cmd, cmd_line, session)
            handled = True

        # Commandes utilisateurs
        elif cmd_line in ["create_user", "list_user", "drop_user", "switch_user_to"]:
            handle_user_commands(cmd, cmd_line, session)
            handled = True

        # Commandes permissions
        elif cmd_line in ["grant", "revoke", "show_grants"]:
            handle_permission_commands(cmd, cmd_line, session)
            handled = True

        # Aide
        elif cmd_line in ["help", "list_commands", "commands"]:
            db.show_help()
            handled = True

        # Commande inconnue
        if not handled:
            print(f"❌ Command '{cmd_line}' not found")
            print("Type 'help' to list all available commands")

if __name__ == "__main__":
    main()