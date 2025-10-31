# commands/user_perm_commands.py
from utils.helpers import hash_password
global userUsingDb, promptContainte

def handle_user_perm_commands(cmd, cmd_line, db, useDatabase, isDbUse, DEFAULT_PROMPT):
    
    if cmd_line == "switch_user_to":
        try:
            parts = cmd.split()
            username = parts[1]
            pwd = [p for p in parts if p.startswith("password=")][0].split("=")[1]
            user = db.userManager.switch_user_to(username, pwd)
            if user:  # user est un dict
                db.current_user = user  # ← CRUCIAL
                userUsingDb = f"user:\033[32m{username}\033[0m"
                promptContainte = (
                    f"[{userUsingDb} & db:\033[34m{useDatabase}\033[0m]\n{DEFAULT_PROMPT} "
                    if isDbUse else f"[{userUsingDb}]\n{DEFAULT_PROMPT} "
                )
                return userUsingDb, promptContainte
        except Exception as e:
            print("Usage: switch_user_to <name> password=<pwd>;")
            print(e)

    elif cmd_line == "list_user":
        db.userManager.list_users()

    elif cmd_line == "drop_user":
        try:
            username = cmd.split(" ", 1)[1].strip()
            if username == db.current_user["username"]:
                print("Cannot delete current user")
                return
            confirm = input(f"Delete user '{username}'? (yes/no): ").lower()
            if confirm in ["yes", "y"]:
                db.userManager.drop_user(username)
        except:
            print("Usage: drop_user <username>;")

    elif cmd_line == "switch_user_to":
        try:
            parts = cmd.split()
            username = parts[1]
            pwd = [p for p in parts if p.startswith("password=")][0].split("=")[1]
            user = db.userManager.switch_user_to(username, pwd)
            if user:
                db.current_user = user
                userUsingDb = f"user:\033[32m{username}\033[0m"
                promptContainte = f"[{userUsingDb} & db:\033[34m{useDatabase}\033[0m]\n{DEFAULT_PROMPT} " if isDbUse else f"[{userUsingDb}]\n{DEFAULT_PROMPT} "
                print(f"Switched to '{username}'")
        except:
            print("Usage: switch_user_to <name> password=<pwd>;")

    elif cmd_line == "grant":
        try:
            parts = cmd.split()
            perm = parts[1].upper()
            on_idx = parts.index("on")
            to_idx = parts.index("to")
            target = parts[on_idx + 1]
            username = parts[to_idx + 1]
            db_name = useDatabase if "." not in target else target.split(".")[0]
            table_name = target.split(".")[1] if "." in target else target
            db.permManager.grant(db_name, table_name, username, perm,
                                 db.current_user["username"], db.current_user["role"])
        except Exception as e:
            print("Usage: grant <perm> on <table|db.*> to <user>;")

    elif cmd_line == "revoke":
        try:
            parts = cmd.split()
            perm = parts[1].upper()
            on_idx = parts.index("on")
            from_idx = parts.index("from")
            target = parts[on_idx + 1]
            username = parts[from_idx + 1]
            db_name = useDatabase if "." not in target else target.split(".")[0]
            table_name = target.split(".")[1] if "." in target else target
            db.permManager.revoke(db_name, table_name, username, perm,
                                  db.current_user["username"], db.current_user["role"])
        except:
            print("Usage: revoke <perm> on <table|db.*> from <user>;")

    elif cmd_line == "show_grants":
        try:
            parts = cmd.split()
            if len(parts) == 2:
                username = parts[1]
                db_name = useDatabase
            else:
                db_name = parts[1]
                username = parts[2]
            db.permManager.show_grants(db_name, username)
        except:
            print("Usage: show_grants <user> or show_grants <db> <user>;")