import os, readline, json
from pathlib import Path
from db_main import Db

# -----------------------------
# Initialisation
# -----------------------------
db = Db()
useDatabase = ""
isDbUse = False
userUsingDb = f"user:\033[32m{db.current_user['username']}\033[0m"
promptContainte = f"[{userUsingDb}]\nm¥⇒ "

print("Welcome to my. We hope that you enjoy using our database")

# Historique des commandes
readline.read_history_file(".history") if os.path.exists(".history") else None

# -----------------------------
# Boucle principale
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

    if not cmd.strip():
        continue

    # Gérer multi-lignes
    while not cmd.strip().endswith(";"):
        try:
            next_line = input(" ⇘ ")
        except KeyboardInterrupt:
            print("\n^C")
            break
        except EOFError:
            readline.write_history_file(".history")
            print("\nBye! It was my")
            exit()
        cmd += next_line.strip()

    cmd = cmd.strip().rstrip(";")
    cmd_line = cmd.split(" ")[0].lower()

    # -----------------------------
    # COMMANDES DE BASE
    # -----------------------------
    if cmd_line in ["clear"]:
        os.system("clear")
        continue

    if cmd_line in ["exit"]:
        readline.write_history_file(".history")
        print("Bye! It was my")
        exit()

    # -----------------------------
    # DATABASE
    # -----------------------------
    if cmd_line.startswith("create_database") or cmd_line.startswith("create_db"):
        dbName = cmd.split(" ")[1].strip()
        db.create_DB(dbName)

    elif cmd_line.startswith("use_database") or cmd_line.startswith("use_db"):
        useDatabase = cmd.split(" ")[1].strip()
        dirs = db.list_database(".database/")
        if useDatabase in dirs:
            print(f"database '{useDatabase}' used")
            promptContainte = f"[{userUsingDb} & db:\033[34m{useDatabase}\033[0m]\nm¥⇒ "
            isDbUse = True
        else:
            print(f"database {useDatabase} doesn't exist")

    elif cmd_line.startswith("drop_database") or cmd_line.startswith("drop_db"):
        databaseToRemove = cmd.split(" ")[1].strip()
        if databaseToRemove == useDatabase:
            print("This database is in use.\ntype: \"leave db\" or choose another database")
        else:
            db.drop_database(databaseToRemove)

    elif cmd_line.startswith("leave_db") or cmd_line.startswith("leave_database"):
        useDatabase = ""
        isDbUse = False
        promptContainte = f"[{userUsingDb}]\n¥⇒ "

    elif cmd_line.startswith("list_database") or cmd_line.startswith("list_db"):
        db.show_databases()

    # -----------------------------
    # TABLES
    # -----------------------------
    elif cmd_line.startswith("create_table"):
        if not isDbUse:
            print("no database used")
            continue
        try:
            name = cmd.split(" ")[1].split("(")[0]
            data_str = cmd.split("(", 1)[1].rsplit(")", 1)[0]
            data = [x.strip() for x in data_str.split(",")]

            attr = {}
            constr = {}
            for val in data:
                col, type_part = val.split(":")
                attr[col.strip()] = type_part.split("[")[0].strip()
                if "[" in type_part:
                    constr[col.strip()] = type_part.split("[")[1].replace("]", "").strip()
                else:
                    constr[col.strip()] = "no constraint"

            table_def = {"caracteristique": attr, "constraint": constr, "data": []}
            db.create_Table(useDatabase, name, table_def)
        except Exception as e:
            print("Syntaxe erreur:", e)

    elif cmd_line.startswith("add_into_table"):
        if not isDbUse:
            print("no database selected")
            continue
        try:
            parts = cmd.split(" ", 1)[1]
            table_name = parts.split("(")[0].strip()
            values_str = parts.split("(", 1)[1].rsplit(")", 1)[0]
            values = [x.strip() for x in values_str.split(",")]
            pathToFile = f".database/{useDatabase}/{table_name}.json"
            db.analyse_data(pathToFile, values)
        except Exception:
            print("Syntaxe error")

    elif cmd_line.startswith("drop_table"):
        if not isDbUse:
            print("no database selected")
            continue
        tableToRemove = cmd.split(" ")[1].strip()
        db.drop_table(useDatabase, tableToRemove)

    elif cmd_line.startswith("list_table"):
        if not isDbUse:
            print("no database selected")
            continue
        path = f".database/{useDatabase}"
        tables = db.list_table(path)
        l = max([len(t) for t in tables] + [10])
        print("—" * (l*2))
        print(f"{'list table in ' + useDatabase:^{l*2}}")
        print("—" * (l*2))
        for t in tables:
            print(f"{t.split('.')[0]:^{l*2}}")
        print("—" * (l*2))

    elif cmd_line.startswith("describe_table"):
        if not isDbUse:
            print("no database selected")
            continue
        table_name = cmd.split(" ")[1].strip()
        pathToFile = f".database/{useDatabase}/{table_name}.json"
        db.describe_table(pathToFile)

    # -----------------------------
    # USERS
    # -----------------------------
    elif cmd_line.startswith("create_user"):
        try:
            args = cmd.split(" ")
            name = args[1]
            pwd = [a.split("=")[1] for a in args if a.startswith("password=")][0]
            role_list = [a.split("=")[1] for a in args if a.startswith("role=")]
            role = role_list[0] if role_list else "user"
            db.userManager.create_user(name, pwd, role)
        except IndexError:
            print("Syntaxe error: create_user <name> password=<pwd> [role=<role>]")

    elif cmd_line.startswith("list_user"):
        db.userManager.list_users()

    elif cmd_line.startswith("drop_user"):
        db.userManager.drop_user(cmd.split(" ")[1].strip())

    elif cmd_line.startswith("use_user"):
        try:
            args = cmd.split(" ")
            name = args[1]
            pwd = args[2].split("=")[1]
            user = db.userManager.use_user(name, pwd)
            if user:
                db.current_user = user
                userUsingDb = f"user:\033[32m{name}\033[0m"
                promptContainte = f"[{userUsingDb}]\nm¥⇒ "
        except:
            print("Syntaxe error: use_user <username> password=<pwd>")

    # -----------------------------
    # PERMISSIONS
    # -----------------------------
    elif cmd_line.startswith("grant"):
        try:
            parts = cmd.split(" ")
            permission = parts[1]
            on_index = parts.index("on")
            to_index = parts.index("to")
            target = parts[on_index + 1]
            username = parts[to_index + 1]
            db.permManager.grant(useDatabase, target, username, permission)
        except:
            print("Syntaxe: grant <permission> on <table|*> to <user>")

    elif cmd_line.startswith("revoke"):
        try:
            parts = cmd.split(" ")
            permission = parts[1]
            on_index = parts.index("on")
            from_index = parts.index("from")
            target = parts[on_index + 1]
            username = parts[from_index + 1]
            db.permManager.revoke(useDatabase, target, username, permission)
        except:
            print("Syntaxe: revoke <permission> on <table|*> from <user>")

    elif cmd_line.startswith("show_grants"):
        try:
            username = cmd.split(" ")[1]
            db.permManager.show_grants(useDatabase, username)
        except:
            print("Syntaxe: show_grants <user>")

    elif cmd_line.startswith("help"):
        db.show_help()

    # -----------------------------
    # SELECT
    # -----------------------------
    elif cmd_line.startswith("select"):
        if not isDbUse:
            print("no database selected")
            continue
        # Déjà intégré dans ton code précédent
        try:
            parts = cmd.split(" ", 1)[1]
            from_index = parts.lower().find("from")
            if from_index == -1:
                print("Syntaxe error: select * from <table> [where col=value];")
                continue
            columns_part = parts[:from_index].strip()
            rest = parts[from_index+4:].strip()
            if "where" in rest.lower():
                table_name = rest.lower().split("where")[0].strip()
                where_clause = rest.lower().split("where")[1].strip()
            else:
                table_name = rest.strip()
                where_clause = None
            path = f".database/{useDatabase}/{table_name}.json"
            if not os.path.exists(path):
                print(f"table '{table_name}' does not exist")
                continue
            with open(path, "r", encoding="utf-8") as f:
                content = json.load(f)
            rows = content.get("data", [])
            all_columns = list(content.get("caracteristique", {}).keys())
            # Colonnes sélectionnées
            if columns_part == "*":
                selected_columns = all_columns
            else:
                selected_columns = [c.strip() for c in columns_part.split(",")]
            # WHERE
            if where_clause:
                try:
                    left, right = [x.strip() for x in where_clause.split("=")]
                    rows = [row for row in rows if str(row.get(left, "")).strip('"') == right.strip('"')]
                except:
                    print("Syntaxe WHERE invalide")
                    continue
            if not rows:
                print("No data found")
                continue
            # Affichage
            col_widths = {col: max(len(col), max(len(str(row.get(col, ""))) for row in rows)) for col in selected_columns}
            total_width = sum(col_widths.values()) + 3 * len(selected_columns) + 1
            print("—" * total_width)
            print(" | ".join(col.ljust(col_widths[col]) for col in selected_columns))
            print("—" * total_width)
            for row in rows:
                print(" | ".join(str(row.get(col, "")).strip('"').ljust(col_widths[col]) for col in selected_columns))
            print("—" * total_width)
        except:
            print("Syntaxe error: select * from <table> [where col=value];")

    else:
        print("Unknown command — type 'help' for command list")
