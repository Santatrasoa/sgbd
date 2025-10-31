# db/perm_manager.py
import json
import os

class PermissionManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.file = os.path.join(db_path, "permissions.json")
        self._load()

    def _load(self):
        if os.path.exists(self.file):
            with open(self.file, "r", encoding="utf-8") as f:
                self.perms = json.load(f)
        else:
            self.perms = {}

    def _save(self):
        with open(self.file, "w", encoding="utf-8") as f:
            json.dump(self.perms, f, indent=2)

    def has_db_permission(self, db, user, op):
        return self.perms.get(db, {}).get(user, {}).get("db", []) and (op in self.perms[db][user]["db"] or "ALL" in self.perms[db][user]["db"])

    def has_table_permission(self, db, table, user, op):
        return self.perms.get(db, {}).get(user, {}).get(table, []) and (op in self.perms[db][user][table] or "ALL" in self.perms[db][user][table])

    def grant(self, db_name, target, username, permission, caller_username, caller_role):
        if caller_role != "admin":
            print("Only admin can grant permissions")
            return
        if db_name not in self.perms:
            self.perms[db_name] = {}
        if username not in self.perms[db_name]:
            self.perms[db_name][username] = {}
        if target not in self.perms[db_name][username]:
            self.perms[db_name][username][target] = []
        if permission not in self.perms[db_name][username][target]:
            self.perms[db_name][username][target].append(permission)
        self._save()

    def revoke(self, db_name, target, username, permission, caller_username, caller_role):
        if caller_role != "admin":
            print("Only admin can revoke")
            return
        if db_name in self.perms and username in self.perms[db_name] and target in self.perms[db_name][username]:
            if permission in self.perms[db_name][username][target]:
                self.perms[db_name][username][target].remove(permission)
                if not self.perms[db_name][username][target]:
                    del self.perms[db_name][username][target]
                self._save()

    def show_grants(self, db_name, username):
        perms = self.perms.get(db_name, {}).get(username, {})
        if not perms:
            print(f"No permissions for '{username}' on '{db_name}'")
        else:
            for target, ops in perms.items():
                print(f"  {', '.join(ops)} on {target}")
