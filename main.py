import os, readline
from pathlib import Path
import db  # ton fichier db.py doit contenir Db, UserManager, PermissionManager déjà définis

# -----------------------------
# Initialisation
# -----------------------------
db = db.Db()
useDatabase = ""
isDbUse = False
current_user = {"username": "root", "role": "admin"}
userUsingDb = f"user:\033[32m{current_user['username']}\033[0m"
promptContainte = f"[{userUsingDb}]\nm¥⇒ "

print("Welcome to my. We hope that you enjoy using our database")

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

    # Gérer multi-lignes
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
        dbName = cmd[16:].strip() if cmd_line.startswith("create_database") else cmd[9:].strip()
        db.create_DB(dbName)

    elif cmd_line.startswith("use_database") or cmd_line.startswith("use_db"):
        useDatabase = cmd[12:].strip() if cmd_line.startswith("use_database") else cmd[6:].strip()
        dirs = db.list_database(".database/")
        if useDatabase in dirs:
            print(f"database '{useDatabase}' used")
            promptContainte = f"[{userUsingDb} & db:\033[34m{useDatabase}\033[0m]\nm¥⇒ "
            isDbUse = True
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
        promptContainte = f"[{userUsingDb}]\n¥⇒ "

    elif cmd_line.startswith("list_database") or cmd_line.startswith("list_db"):
        db.show_databases()

    # -----------------------------
    # TABLES
    # -----------------------------
    elif cmd_line.startswith("create_table"):
        if isDbUse:
            try:
                if "(" in cmd and ")" in cmd:
                    name = cmd.split(" ")[1].split("(")[0]
                    data = cmd.split('(')[1].replace(')', "").split(',')
                    attr = {}
                    constr = {}
                    flags = False
                    allType = ["Date", "Year", "Time", "Datetime", "Bool", "Number", "Float", "String", "Text", "Bit"]
                    constraints = ["Not_null", "Unique", "Primary_key", "Foreign_key", "Check", "Default", "Auto_increment"]
                    for val in data:
                        parts = val.strip().split(":")
                        col = parts[0].strip()
                        t = parts[1].split('[')[0].capitalize().strip()
                        if t not in allType:
                            flags = True
                        attr[col] = t
                        if "[" in parts[1]:
                            constr[col] = parts[1].split('[')[1].replace(']', '').strip()
                        else:
                            constr[col] = "no constraint"
                    table_def = {"caracteristique": attr, "constraint": constr, "data": []}
                    db.create_Table(useDatabase, name, table_def)
                else:
                    print("!!! syntaxe error !!!")
            except Exception as e:
                print("error:", e)
        else:
            print("no database used")

    elif cmd_line.startswith("add_into_table"):
        if isDbUse:
            try:
                getData = cmd.split(" ")[1:]
                getData = " ".join(getData).strip().split("(")
                table_name = getData[0].strip()
                values = getData[1].replace(")", "").split(",")
                pathToFile = f".database/{useDatabase}/{table_name}.json"
                db.analyse_data(pathToFile, values)
            except Exception:
                print("syntaxe error")
        else:
            print("no database selected")

    elif cmd_line.startswith("drop_table"):
        if isDbUse:
            tableToRemove = cmd[10:].strip()
            db.drop_table(useDatabase, tableToRemove)

    elif cmd_line.startswith("list_table"):
        if isDbUse:
            path = f".database/{useDatabase}"
            tables = db.list_table(path)
            l = max([len(t) for t in tables] + [10])
            print("—" * (l*2))
            print(f"{'list table in ' + useDatabase:^{l*2}}")
            print("—" * (l*2))
            for t in tables:
                print(f"{t.split('.')[0]:^{l*2}}")
            print("—" * (l*2))
        else:
            print("no database selected")

    elif cmd_line.startswith("describe_table"):
        if isDbUse:
            table_name = cmd[15:].strip()
            pathToFile = f".database/{useDatabase}/{table_name}.json"
            db.describe_table(pathToFile)
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
            print("syntax error, use: use_user <username> password=<pwd>;")

    elif cmd_line.startswith("grant"):
        parts = cmd.split(" ")
        permission = parts[1]
        on_index = parts.index("on")
        to_index = parts.index("to")
        target = parts[on_index + 1]
        username = parts[to_index + 1]
        db.permManager.grant(useDatabase, target, username, permission)

    elif cmd_line.startswith("revoke"):
        parts = cmd.split(" ")
        permission = parts[1]
        on_index = parts.index("on")
        from_index = parts.index("from")
        target = parts[on_index + 1]
        username = parts[from_index + 1]
        db.permManager.revoke(useDatabase, target, username, permission)

    elif cmd_line.startswith("show_grants"):
        username = cmd.split(" ")[1]
        db.permManager.show_grants(useDatabase, username)

    elif cmd_line.startswith("help"):
        db.show_help()


    else:
        print("commande not found")


