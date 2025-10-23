import os, json


class PermissionManager:
    """Gère les permissions par base.

    Format du fichier JSON:
      {
        "__owner__": "owner_username",
        "alice": { "databases": [...], "tables": { ... }},
        "bob": { ... }
      }

    Seul le propriétaire (owner) de la base ou un utilisateur de role 'admin'
    doit pouvoir appeler grant/revoke.
    """

    def __init__(self, db_path):
        self.perm_folder = f"{db_path}/.permissions"
        os.makedirs(self.perm_folder, exist_ok=True)

    def get_permission_file(self, db_name):
        path = f"{self.perm_folder}/{db_name}.json"
        if not os.path.exists(path):
            with open(path, "w") as f:
                json.dump({"__owner__": None}, f, indent=4)
        return path

    def set_owner(self, db_name, owner_username):
        path = self.get_permission_file(db_name)
        with open(path, "r") as f:
            perms = json.load(f)
        perms["__owner__"] = owner_username
        with open(path, "w") as f:
            json.dump(perms, f, indent=4)

    def get_owner(self, db_name):
        path = self.get_permission_file(db_name)
        with open(path, "r") as f:
            perms = json.load(f)
        return perms.get("__owner__")

    def _ensure_user_entry(self, perms, username):
        if username not in perms:
            perms[username] = {"databases": [], "tables": {}}

    def grant(self, db_name, table, username, permission, caller_username=None, caller_role=None):
        """Donne une permission à `username` sur db_name.table.

        caller_username/caller_role : utilisateur effectuant l'opération. Si
        caller_role == 'admin' ou caller_username == owner, l'opération est autorisée.
        """
        path = self.get_permission_file(db_name)
        with open(path, "r") as f:
            perms = json.load(f)

        owner = perms.get("__owner__")
        if caller_role != "admin" and caller_username != owner:
            print(f"permission denied: only owner ({owner}) or admin can grant/revoke on {db_name}")
            return

        self._ensure_user_entry(perms, username)
        if table == "*":
            if permission.upper() not in perms[username].get("databases", []):
                perms[username]["databases"].append(permission.upper())
        else:
            perms[username]["tables"].setdefault(table, [])
            if permission.upper() not in perms[username]["tables"][table]:
                perms[username]["tables"][table].append(permission.upper())

        with open(path, "w") as f:
            json.dump(perms, f, indent=4)
        print(f"granted {permission} on {db_name}.{table} to {username}")

    def revoke(self, db_name, table, username, permission, caller_username=None, caller_role=None):
        path = self.get_permission_file(db_name)
        with open(path, "r") as f:
            perms = json.load(f)

        owner = perms.get("__owner__")
        if caller_role != "admin" and caller_username != owner:
            print(f"permission denied: only owner ({owner}) or admin can grant/revoke on {db_name}")
            return

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
        owner = perms.get("__owner__")
        if username not in perms:
            print(f"user {username} has no permissions on {db_name}")
            return
        user_perm = perms[username]
        sep = "" * 50
        print(sep)
        print(f"Permissions for user {username} on database {db_name}")
        print(sep)
        for t, perms_list in user_perm.get("tables", {}).items():
            print(f"Table: {t} -> {', '.join(perms_list)}")
        if "databases" in user_perm and user_perm["databases"]:
            print(f"Database level -> {', '.join(user_perm['databases'])}")
        print(sep)

    def has_db_permission(self, db_name, username, permission):
        path = self.get_permission_file(db_name)
        with open(path, "r") as f:
            perms = json.load(f)
        owner = perms.get("__owner__")
        if username == owner:
            return True
        if username not in perms:
            return False
        return permission.upper() in perms[username].get("databases", [])

    def has_table_permission(self, db_name, table, username, permission):
        path = self.get_permission_file(db_name)
        with open(path, "r") as f:
            perms = json.load(f)
        owner = perms.get("__owner__")
        if username == owner:
            return True
        if username not in perms:
            return False
        return permission.upper() in perms[username].get("tables", {}).get(table, [])

    def user_has_any_permission(self, db_name, username):
        path = self.get_permission_file(db_name)
        with open(path, "r") as f:
            perms = json.load(f)
        owner = perms.get("__owner__")
        if username == owner:
            return True
        if username not in perms:
            return False
        user_perm = perms[username]
        if user_perm.get("databases"):
            if any(user_perm.get("databases")):
                return True
        for tbl_perms in user_perm.get("tables", {}).values():
            if tbl_perms:
                return True
        return False
