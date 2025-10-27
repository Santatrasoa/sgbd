import os, json

class PermissionManager:
    """
    Permissions format:
    {
        "alice": {
            "database1": {
                "table1": ["READ", "WRITE"],
                "table2": ["READ"]
            }
        }
    }
    """

    VALID_PERMISSIONS = {"READ", "WRITE", "DELETE", "UPDATE", "ALL"}

    def __init__(self, db_path: str):
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
            perms[username] = {}

    def _ensure_db_entry(self, perms, username, db_name):
        self._ensure_user_entry(perms, username)
        if db_name not in perms[username]:
            perms[username][db_name] = {}

    def grant(self, db_name, table, username, permission, caller_username=None, caller_role=None):
        """Donne une permission à username sur db.table."""
        permission = permission.upper()
        if permission not in self.VALID_PERMISSIONS:
            print(f"⚠️ Invalid permission '{permission}'")
            return

        path = self.get_permission_file(db_name)
        with open(path, "r") as f:
            perms = json.load(f)

        owner = perms.get("__owner__")
        if caller_role != "admin" and caller_username != owner:
            print(f"❌ Permission denied: only owner ({owner}) or admin can grant")
            return

        self._ensure_db_entry(perms, username, db_name)
        if table not in perms[username][db_name]:
            perms[username][db_name][table] = []

        if permission not in perms[username][db_name][table]:
            perms[username][db_name][table].append(permission)

        with open(path, "w") as f:
            json.dump(perms, f, indent=4)
        print(f"✅ Granted {permission} to {username} on {db_name}.{table}")

    def revoke(self, db_name, table, username, permission, caller_username=None, caller_role=None):
        """Retire une permission."""
        permission = permission.upper()
        path = self.get_permission_file(db_name)
        with open(path, "r") as f:
            perms = json.load(f)

        owner = perms.get("__owner__")
        if caller_role != "admin" and caller_username != owner:
            print(f"❌ Permission denied: only owner ({owner}) or admin can revoke")
            return

        if username in perms and db_name in perms[username] and table in perms[username][db_name]:
            if permission in perms[username][db_name][table]:
                perms[username][db_name][table].remove(permission)
        with open(path, "w") as f:
            json.dump(perms, f, indent=4)
        print(f"❌ Revoked {permission} from {username} on {db_name}.{table}")

    def has_permission(self, db_name, table, username, permission):
        path = self.get_permission_file(db_name)
        with open(path, "r") as f:
            perms = json.load(f)
        owner = perms.get("__owner__")
        if username == owner:
            return True
        return username in perms and db_name in perms[username] and permission.upper() in perms[username][db_name].get(table, [])

    def show_grants(self, db_name, username):
        path = self.get_permission_file(db_name)
        with open(path, "r") as f:
            perms = json.load(f)
        if username not in perms:
            print(f"⚠️ User {username} has no permissions on {db_name}")
            return
        user_perm = perms[username]
        print(f"=== Permissions for {username} on {db_name} ===")
        for t, rights in user_perm.get(db_name, {}).items():
            print(f"Table: {t} → {', '.join(rights)}")
