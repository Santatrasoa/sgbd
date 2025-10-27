import os
import readline
import json
from pathlib import Path

# Import depuis le package db
from db.db_main import Db
from utils import load_config

# -----------------------------
# CONFIGURATION
# -----------------------------
config = load_config()
DB_PATH = config.get("db_path", ".database")
DEFAULT_PROMPT = config.get("default_prompt", "m¥⇒")
SEPARATOR = config.get("separator_char", "—")

# -----------------------------
# INITIALISATION
# -----------------------------
db = Db(DB_PATH)  # Instance de la classe principale
useDatabase = ""
isDbUse = False
current_user = {"username": "root", "role": "admin"}
userUsingDb = f"user:\033[32m{current_user['username']}\033[0m"
promptContainte = f"[{userUsingDb}]\n{DEFAULT_PROMPT} "

if os.path.exists(".history"):
    readline.read_history_file(".history")

print("Welcome to my. We hope that you enjoy using our database")

# -----------------------------
# BOUCLE PRINCIPALE
# -----------------------------
while True:
    print("")
    try:
        cmd = input("my ~ " + promptContainte)
    except KeyboardInterrupt:
        print("\n^C")
        continue
    except EOFError:
        readline.write_history_file(".history")
        print("\nBye! It was my")
        exit()

    # Clear / Exit simple
    if cmd.strip() in ["clear", "clear;"]:
        os.system("clear")
        continue
    if cmd.strip() in ["exit", "exit;"]:
        readline.write_history_file(".history")
        print("Bye! It was my")
        exit()

    # Multi-lignes
    while not cmd.endswith(";"):
        try:
            next_line = input(" ⇘ ")
        except KeyboardInterrupt:
            print("\n^C")
            break
        except EOFError:
            print("\nBye! It was my")
            readline.write_history_file(".history")
            exit()
        cmd += next_line.strip()

    cmd = cmd.replace(";", "")
    cmd_line = cmd.split(" ")[0].lower()

    # -----------------------------
    # DATABASE
    # -----------------------------
    if cmd_line.startswith("create_database") or cmd_line.startswith("create_db"):
        dbName = cmd[16:].strip() if cmd_line.startswith("create_database") else cmd[9:].strip()
        db.create_DB(dbName)

    elif cmd_line.startswith("use_database") or cmd_line.startswith("use_db"):
        useDatabase = cmd[12:].strip() if cmd_line.startswith("use_database") else cmd[6:].strip()
        dirs = db.list_database(DB_PATH)
        if useDatabase in dirs:
            # check permission: admins/root can always use; otherwise require USAGE or ALL at database level
            current_username = db.current_user.get("username")
            role = db.current_user.get("role")
            if role == "admin" or db.permManager.has_permission(useDatabase, "", current_username, "READ") or db.permManager.has_permission(useDatabase, "",current_username, "USAGE"):
                print(f"database '{useDatabase}' used")
                promptContainte = f"[{userUsingDb} & db:\033[34m{useDatabase}\033[0m]\n{DEFAULT_PROMPT} "
                isDbUse = True
            else:
                print(f"permission denied to use database '{useDatabase}' for user {current_username}")
        else:
            print(f"database {useDatabase} doesn't exist")

    elif cmd_line.startswith("drop_database") or cmd_line.startswith("drop_db"):
        databaseToRemove = cmd[13:].strip() if cmd_line.startswith("drop_database") else cmd[7:].strip()
        if databaseToRemove == useDatabase:
            print("This database is in use.\ntype: \"leave db\" or choose another database")
        else:
            db.drop_database(databaseToRemove)

    elif cmd_line.startswith("leave_db") or cmd_line.startswith("leave_database"):
        useDatabase = ""
        isDbUse = False
        promptContainte = f"[{userUsingDb}]\n{DEFAULT_PROMPT} "

    elif cmd_line.startswith("list_database") or cmd_line.startswith("list_db"):
        db.show_databases()

    # -----------------------------
    # TABLES
    # -----------------------------
    
    elif cmd_line.startswith("create_table"):
        if isDbUse:
            try:
                # Vérifier présence des parenthèses
                if "(" in cmd and ")" in cmd:
                    # Extraction du nom de table (supporte create_table Name(...))
                    name = cmd.split(" ")[1].split("(")[0].strip()

                    # Extraire la portion entre la première '(' et la dernière ')'
                    inside = cmd[cmd.find("(") + 1: cmd.rfind(")")]
                    # retirer un ; final si présent
                    inside = inside.rstrip().rstrip(';').strip()

                    # Fonction utilitaire : split au top-level par ',' en ignorant les ',' dans [...]
                    def split_top_level_commas(s: str):
                        parts = []
                        cur = []
                        depth = 0
                        for ch in s:
                            if ch == '[':
                                depth += 1
                                cur.append(ch)
                            elif ch == ']':
                                depth = max(depth - 1, 0)
                                cur.append(ch)
                            elif ch == ',' and depth == 0:
                                fragment = ''.join(cur).strip()
                                if fragment:
                                    parts.append(fragment)
                                cur = []
                            else:
                                cur.append(ch)
                        last = ''.join(cur).strip()
                        if last:
                            parts.append(last)
                        return parts

                    columns = split_top_level_commas(inside)

                    attr = {}
                    constr = {}

                    # Types et contraintes autorisés (on les utilise en minuscule pour normaliser)
                    allType = ["date", "year", "time", "datetime", "bool", "number", "float", "string", "text", "bit"]
                    constraints_allowed = {
                        "not_null": "Not_null",
                        "unique": "Unique",
                        "primary_key": "Primary_key",
                        "foreign_key": "Foreign_key",
                        "check": "Check",
                        "default": "Default",
                        "auto_increment": "Auto_increment"
                    }

                    # Parcours des définitions de colonnes
                    for val in columns:
                        val = val.strip()
                        if not val:
                            continue

                        # Vérifie la syntaxe nom:type...
                        if ":" not in val:
                            print(f"❌ Syntax error in '{val}' — expected format: name:type[constraint,...]")
                            break

                        parts = val.split(":", 1)
                        col = parts[0].strip()
                        type_and_constraints = parts[1].strip()

                        # Extraire type et contraintes (si présentes)
                        if "[" in type_and_constraints and type_and_constraints.endswith("]"):
                            type_part = type_and_constraints.split("[", 1)[0].strip()
                            constraint_part = type_and_constraints[type_and_constraints.find("[") + 1:-1].strip()
                            # split des contraintes par ',' (ici les virgules sont OK car déjà hors split_top_level_commas)
                            raw_constraints = [c.strip() for c in constraint_part.split(",") if c.strip()]
                        elif "[" in type_and_constraints and "]" in type_and_constraints:
                            # Gestion robuste si plusieurs [ ] mal positionnés
                            type_part = type_and_constraints.split("[", 1)[0].strip()
                            constraint_part = type_and_constraints[type_and_constraints.find("[") + 1:type_and_constraints.rfind("]")].strip()
                            raw_constraints = [c.strip() for c in constraint_part.split(",") if c.strip()]
                        else:
                            type_part = type_and_constraints.strip()
                            raw_constraints = []

                        t = type_part.lower()

                        # Vérifier le type
                        if t not in allType:
                            print(f"❌ Unknown type '{type_part}' for column '{col}'")
                            break

                        # Normaliser et valider contraintes (insensible à la casse/espaces/tirets)
                        normalized_constraints = []
                        invalid_constraints = []
                        for rc in raw_constraints:
                            key = rc.lower().replace(" ", "_").replace("-", "_")
                            if key in constraints_allowed:
                                normalized_constraints.append(constraints_allowed[key])
                            else:
                                invalid_constraints.append(rc)

                        if invalid_constraints:
                            print(f"⚠️ Unknown constraints for '{col}': {invalid_constraints}")
                            # si tu veux stopper à la première contrainte invalide, décommente la ligne suivante:
                            # break

                        # Enregistrer
                        attr[col] = type_part.capitalize() if t != "number" else "Number"
                        constr[col] = normalized_constraints if normalized_constraints else ["no constraint"]
                    else:
                        # Vérification des permissions
                        current_username = db.current_user.get("username")
                        role = db.current_user.get("role")

                        if (
                            role == "admin"
                            or db.permManager.has_db_permission(useDatabase, current_username, "ALL")
                            or db.permManager.has_table_permission(useDatabase, name, current_username, "ALL")
                        ):
                            table_def = {
                                "caracteristique": attr,
                                "constraint": constr,
                                "data": []
                            }
                            db.create_Table(useDatabase, name, table_def)
                        else:
                            print(f"🚫 Permission denied to create table '{name}' in database '{useDatabase}' for user '{current_username}'")
                else:
                    print("❌ Syntax error: missing parentheses")
            except Exception as e:
                print("🔥 Error while creating table:", e)
        else:
            print("⚠️ No database currently in use")

    
    elif cmd_line.startswith("add_into_table"):
        if isDbUse:
            try:
                getData = " ".join(cmd.split(" ")[1:]).strip().split("(")
                table_name = getData[0].strip()
                values = getData[1].replace(")", "").split(",")
                pathToFile = f"{DB_PATH}/{useDatabase}/{table_name}.json"
                # permission check for INSERT / ALL
                current_username = db.current_user.get("username")
                role = db.current_user.get("role")
                if role == "admin" or db.permManager.has_table_permission(useDatabase, table_name, current_username, "ALL") or db.permManager.has_table_permission(useDatabase, table_name, current_username, "INSERT"):
                    db.analyse_data(pathToFile, values)
                else:
                    print(f"permission denied to add into table '{table_name}' for user {current_username}")
            except Exception:
                print("syntaxe error")
        else:
            print("no database selected")

    elif cmd_line.startswith("drop_table"):
        if isDbUse:
            tableToRemove = cmd[10:].strip()
            current_username = db.current_user.get("username")
            role = db.current_user.get("role")
            if role == "admin" or db.permManager.has_table_permission(useDatabase, tableToRemove, current_username, "ALL") or db.permManager.has_table_permission(useDatabase, tableToRemove, current_username, "DROP"):
                db.drop_table(useDatabase, tableToRemove)
            else:
                print(f"permission denied to drop table '{tableToRemove}' for user {current_username}")

    elif cmd_line.startswith("list_table"):
        if isDbUse:
            path = f"{DB_PATH}/{useDatabase}"
            # if user is not admin and has no permission on the DB, deny listing
            current_username = db.current_user.get("username")
            role = db.current_user.get("role")
            if role != "admin" and not db.permManager.user_has_any_permission(useDatabase, current_username):
                print(f"permission denied to list tables in database '{useDatabase}' for user {current_username}")
                continue
            tables = db.list_table(path)
            if len(tables) == 0:
                print("No table found in this database")
            else:
                l = max([len(t) for t in tables] + [10])
                print(SEPARATOR * (l*2))
                print(f"{'list table in ' + useDatabase:^{l*2}}")
                print(SEPARATOR * (l*2))
                for t in tables:
                    print(f"{t.split('.')[0]:^{l*2}}")
                print(SEPARATOR * (l*2))
        else:
            print("no database selected")

    elif cmd_line.startswith("describe_table"):
        if isDbUse:
            table_name = cmd[15:].strip()
            pathToFile = f"{DB_PATH}/{useDatabase}/{table_name}.json"
            current_username = db.current_user.get("username")
            role = db.current_user.get("role")
            if role == "admin" or db.permManager.has_table_permission(useDatabase, table_name, current_username, "ALL") or db.permManager.has_table_permission(useDatabase, table_name, current_username, "SELECT"):
                db.describe_table(pathToFile)
            else:
                print(f"permission denied to describe table '{table_name}' for user {current_username}")
        else:
            print("no database selected")

    # -----------------------------
    # USERS
    # -----------------------------
    elif cmd_line.startswith("create_user"):
        args = cmd.split(" ")
        name = args[1]
        password = [a for a in args if a.startswith("password=")]
        role = [a for a in args if a.startswith("role=")]
        if not password: print("password required"); continue
        pwd = password[0].split("=")[1]
        rl = role[0].split("=")[1] if role else "user"
        db.userManager.create_user(name, pwd, rl)

    elif cmd_line.startswith("list_user"):
        db.userManager.list_users()

    elif cmd_line.startswith("drop_user"):
        db.userManager.drop_user(cmd.split(" ")[1])

    elif cmd_line.startswith("switch_user_to"):
        try:
            args = cmd.split(" ")
            name = args[1]
            pwd = args[2].split("=")[1]
            user = db.userManager.switch_user_to(name, pwd)
            if user:
                db.current_user = user
                userUsingDb = f"user:\033[32m{name}\033[0m"
                promptContainte = f"[{userUsingDb}]\n{DEFAULT_PROMPT} "
        except:
            print("syntax error, use: switch_user_to <username> password=<pwd>;")

    # -----------------------------
    # PERMISSIONS
    # -----------------------------
    elif cmd_line.startswith("grant"):
        try:
            parts = cmd.split()
            permission = parts[1]
            on_index = parts.index("on")
            to_index = parts.index("to")
            raw_target = parts[on_index + 1]
            username = parts[to_index + 1]
        except (ValueError, IndexError):
            print("syntax error for grant: use `grant <PERM> on <table|db.table|*> to <user>`")
            continue

        # allow qualified target: db.table or db.*
        if "." in raw_target:
            db_name, target = raw_target.split(".", 1)
        else:
            db_name = useDatabase
            target = raw_target

        if not db_name:
            print("no database selected and no database qualified in grant target")
            continue

        caller_username = db.current_user.get("username")
        caller_role = db.current_user.get("role")
        db.permManager.grant(db_name, target, username, permission, caller_username=caller_username, caller_role=caller_role)

    elif cmd_line.startswith("revoke"):
        try:
            parts = cmd.split()
            permission = parts[1]
            on_index = parts.index("on")
            from_index = parts.index("from")
            raw_target = parts[on_index + 1]
            username = parts[from_index + 1]
        except (ValueError, IndexError):
            print("syntax error for revoke: use `revoke <PERM> on <table|db.table|*> from <user>`")
            continue

        if "." in raw_target:
            db_name, target = raw_target.split(".", 1)
        else:
            db_name = useDatabase
            target = raw_target

        if not db_name:
            print("no database selected and no database qualified in revoke target")
            continue

        caller_username = db.current_user.get("username")
        caller_role = db.current_user.get("role")
        db.permManager.revoke(db_name, target, username, permission, caller_username=caller_username, caller_role=caller_role)

    elif cmd_line.startswith("show_grants"):
        parts = cmd.split()
        # allow: show_grants <user>   or   show_grants <db> <user>
        if len(parts) == 2:
            username = parts[1]
            db_name = useDatabase
        elif len(parts) == 3:
            db_name = parts[1]
            username = parts[2]
        else:
            print("syntax: show_grants <user>  OR  show_grants <db> <user>")
            continue

        if not db_name:
            print("no database selected and no database specified for show_grants")
            continue

        db.permManager.show_grants(db_name, username)

    # -----------------------------
    # SELECT
    # -----------------------------
    elif cmd_line.startswith("select"):
        if isDbUse:
            getRequests = " ".join(cmd.split(" ")[1:]).strip()
            if len(getRequests) == 0:
                print("syntaxe error")
                continue
            parts = getRequests.split()
            if len(parts) >= 3 and parts[1].lower() == "from":
                columns_part = parts[0]
                table_name = parts[2]
                where_clause = None
                if "where" in [p.lower() for p in parts]:
                    where_index = [p.lower() for p in parts].index("where")
                    if len(parts) > where_index + 1:
                        where_clause = " ".join(parts[where_index + 1:])
                    else:
                        print("syntaxe error after WHERE")
                        continue
                path = f"{DB_PATH}/{useDatabase}/{table_name}.json"
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        content = json.load(f)
                    all_rows = content.get("data", [])
                    all_columns = list(content.get("caracteristique", {}).keys())
                    normalized_rows = []
                    for row in all_rows:
                        clean_row = {}
                        for k, v in row.items():
                            clean_row[k.strip()] = str(v).strip().strip('"')
                        normalized_rows.append(clean_row)
                    all_rows = normalized_rows
                    selected_columns = all_columns if columns_part == "*" else [c.strip() for c in columns_part.split(",")]
                    filtered_rows = all_rows
                    if where_clause:
                        try:
                            left, right = where_clause.split("=")
                            left = left.strip()
                            right = right.strip().strip("'").strip('"')
                            filtered_rows = [row for row in all_rows if str(row.get(left, "")) == right]
                        except ValueError:
                            print("Syntaxe WHERE invalide — use: where col = value")
                            continue
                    if len(filtered_rows) == 0:
                        print("No data found")
                    else:
                        col_widths = {col: max(len(col), max((len(str(row.get(col, ""))) for row in filtered_rows), default=0)) for col in selected_columns}
                        total_width = sum(col_widths.values()) + (len(selected_columns) * 3) + 1
                        print(SEPARATOR * total_width)
                        print(" | ".join(col.ljust(col_widths[col]) for col in selected_columns))
                        print(SEPARATOR * total_width)
                        for row in filtered_rows:
                            print(" | ".join(str(row.get(col, "")).ljust(col_widths[col]) for col in selected_columns))
                        print(SEPARATOR * total_width)
                else:
                    print(f"table '{table_name}' does not exist")
            else:
                print("syntaxe error — use: select * from <table> [where col = value]")
        else:
            print("no database selected")

    # -----------------------------
    # HELP
    # -----------------------------
    elif cmd_line.startswith("help"):
        db.show_help()

    else:
        print("command not found")