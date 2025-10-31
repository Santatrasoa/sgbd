# commands/user_perm_commands.py
from utils.helpers import hash_password

# Variables globales (modifiées dans main.py)
global userUsingDb, promptContainte

def handle_user_perm_commands(cmd, cmd_line, db, useDatabase, isDbUse, DEFAULT_PROMPT):
    if cmd_line == "create_user":
        try:
            parts = cmd.split()
            if len(parts) < 2:
                raise ValueError("Missing username")

            username = parts[1]
            pwd_part = [p for p in parts if p.startswith("password=")]
            role_part = [p for p in parts if p.startswith("role=")]

            if not pwd_part:
                raise ValueError("Missing password")

            password = pwd_part[0].split("=", 1)[1]
            role = role_part[0].split("=", 1)[1].lower() if role_part else "user"

            if role not in ["user", "admin"]:
                print("Invalid role. Use 'user' or 'admin'")
                return

            db.userManager.create_user(username, password, role)
            print(f"User '{username}' created with role '{role}'")

        except Exception as e:
            print("Usage: create_user <username> password=<pwd> [role=user|admin];")
            if str(e) != "Missing username" and str(e) != "Missing password":
                print(f"Error: {e}")

    elif cmd_line == "list_user":
        db.userManager.list_users()

    elif cmd_line == "drop_user":
        try:
            username = cmd.split(" ", 1)[1].strip()
            if username == db.current_user["username"]:
                print("Cannot delete current user")
                return
            confirm = input(f"Delete user '{username}'? (yes/no): ").lower()
            if confirm in ["yes", "y", "oui"]:
                db.userManager.drop_user(username)
                print(f"User '{username}' deleted")
        except IndexError:
            print("Usage: drop_user <username>;")
        except Exception as e:
            print(f"Error: {e}")

    elif cmd_line == "switch_user_to":
        try:
            parts = cmd.split()
            if len(parts) < 2:
                raise ValueError("Missing username")
            username = parts[1]
            pwd_part = [p for p in parts if p.startswith("password=")]
            if not pwd_part:
                raise ValueError("Missing password")
            pwd = pwd_part[0].split("=", 1)[1]

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
        except Exception as e:
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
        except Exception as e:
            print("Usage: show_grants <user> or show_grants <db> <user>;")

    # Retour par défaut (si aucune modification du prompt)
    return None, None