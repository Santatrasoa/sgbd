import os
import json

class PermissionManager:
    def __init__(self):
        self.perm_folder = ".database/.permissions"
        os.makedirs(self.perm_folder, exist_ok=True)

    def get_permission_file(self, db_name):
        path = f".database/{db_name}/.permissions.json"
        if not os.path.exists(path):
            with open(path, "w") as f:
                json.dump({}, f, indent=4)
        return path

    def grant(self, db_name, table, username, permission):
        path = self.get_permission_file(db_name)
        with open(path, "r") as f:
            perms = json.load(f)

        perms.setdefault(username, {"databases": [], "tables": {}})
        if table == "*":
            perms[username]["databases"].append(permission.upper())
        else:
            perms[username]["tables"].setdefault(table, [])
            if permission.upper() not in perms[username]["tables"][table]:
                perms[username]["tables"][table].append(permission.upper())

        with open(path, "w") as f:
            json.dump(perms, f, indent=4)
        print(f"granted {permission} on {db_name}.{table} to {username}")

    def revoke(self, db_name, table, username, permission):
        path = self.get_permission_file(db_name)
        with open(path, "r") as f:
            perms = json.load(f)

        if username in perms:
            if table == "*":
                if permission.upper() in perms[username].get("databases", []):
                    perms[username]["databases"].remove(permission.upper())
            else:
                if permission.upper() in perms[username].get("tables", {}).get(table, []):
                    perms[username]["tables"][table].remove(permission.upper())
            with open(path, "w") as f:
                json.dump(perms, f, indent=4)
            print(f"revoked {permission} on {db_name}.{table} from {username}")
        else:
            print("user or permission not found")

    def show_grants(self, db_name, username):
        path = self.get_permission_file(db_name)
        with open(path, "r") as f:
            perms = json.load(f)

        if username not in perms:
            print(f"user {username} has no permissions on {db_name}")
            return

        user_perm = perms[username]
        print(f"—" * 50)
        print(f"Permissions for user \033[32m{username}\033[0m on database \033[34m{db_name}\033[0m")
        print(f"—" * 50)

        for t, perms_list in user_perm.get("tables", {}).items():
            print(f"Table: {t} -> {', '.join(perms_list)}")

        if "databases" in user_perm and user_perm["databases"]:
            print(f"Database level -> {', '.join(user_perm['databases'])}")

        print(f"—" * 50)
