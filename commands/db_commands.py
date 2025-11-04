# commands/db_commands.py
from db.db_main import Db

def handle_db_commands(cmd, cmd_line, db: Db, userUsingDb, DEFAULT_PROMPT, SEPARATOR):
    global useDatabase, isDbUse, promptContainte

    if cmd_line in ["create_database", "create_db"]:
        name = cmd.split(" ", 1)[1].strip() if " " in cmd else ""
        db.create_DB(name)

    if cmd_line in ["use_database", "use_db"]:
        name = cmd.split(" ", 1)[1].strip()
        dirs = db.list_database()
        if name in dirs:
            if db.permManager.has_db_permission(name, db.current_user["username"], "USAGE"):
                print(f"Database '{name}' selected")
                useDatabase = name
                isDbUse = True
                promptContainte = f"[{userUsingDb} & db:\033[34m{name}\033[0m]\n{DEFAULT_PROMPT} "
                return userUsingDb, promptContainte, useDatabase, isDbUse  # ← RETOURNE TOUT
            else:
                print(f"Permission denied to use database '{name}'")
        else:
            print(f"Database '{name}' does not exist")
        return None, None, None, None

    elif cmd_line in ["leave_db", "leave_database"]:
        # ...
        useDatabase = ""
        isDbUse = False
        promptContainte = f"[{userUsingDb}]\n{DEFAULT_PROMPT} "
        return userUsingDb, promptContainte, useDatabase, isDbUse


    elif cmd_line in ["drop_database", "drop_db"]:
        name = cmd.split(" ", 1)[1].strip()
        if name == useDatabase:
            print("Cannot drop current database")
        else:
            confirm = input(f"Delete '{name}'? (yes/no): ").lower()
            if confirm in ["yes", "y", "oui"]:
                db.drop_database(name)

    elif cmd_line in ["list_database", "list_db"]:
        db.show_databases()

    elif cmd_line in ["stats_db", "database_stats"]:
        if isDbUse:
            stats = db.get_statistics(useDatabase)
            print(f"Tables: {stats['tables']}, Rows: {stats['total_rows']}, Cols: {stats['total_columns']}")

    return None, None