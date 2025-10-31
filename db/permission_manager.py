# db/permission_manager.py
from pathlib import Path

class PermissionManager:
    def __init__(self, db_path: str, crypto):
        self.dbPath = Path(db_path)
        self.crypto = crypto
        self.dbPath.mkdir(exist_ok=True)

    def _get_perm_path(self, db_name: str) -> Path:
        return self.dbPath / db_name / "permissions.enc"

    def _load(self, db_name: str) -> dict:
        path = self._get_perm_path(db_name)
        if not path.exists():
            return {}
        return self.crypto.decrypt(path.read_bytes())

    def _save(self, db_name: str, data: dict):
        path = self._get_perm_path(db_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.crypto.encrypt(data))

    def set_owner(self, db_name: str, username: str) -> None:
        data = {
            "owner": username,
            "database_permissions": {username: ["ALL"]},
            "table_permissions": {username: {}}
        }
        self._save(db_name, data)

    def get_owner(self, db_name: str) -> str:
        data = self._load(db_name)
        return data.get("owner")

    def has_db_permission(self, db_name: str, username: str, required_perm: str) -> bool:
        data = self._load(db_name)
        if data.get("owner") == username:
            return True
        perms = data.get("database_permissions", {}).get(username, [])
        perms = [p.upper() for p in perms]
        return "ALL" in perms or required_perm.upper() in perms

    def has_table_permission(self, db_name: str, table_name: str, username: str, required_perm: str) -> bool:
        data = self._load(db_name)
        if data.get("owner") == username:
            return True
        user_perms = data.get("table_permissions", {}).get(username, {})
        perms = user_perms.get(table_name, [])
        perms = [p.upper() for p in perms]
        return "ALL" in perms or required_perm.upper() in perms

    def grant(self, db_name: str, table_name: str, username: str, permission: str,
              caller_username: str, caller_role: str) -> bool:
        data = self._load(db_name)
        owner = data.get("owner")
        if caller_role != "admin" and caller_username != owner:
            print("Permission denied: only owner or admin can grant")
            return False
        permission = permission.upper()
        table_perms = data.setdefault("table_permissions", {})
        user_perms = table_perms.setdefault(username, {})
        perms_list = user_perms.setdefault(table_name, [])
        if permission not in perms_list:
            perms_list.append(permission)
        db_perms = data.setdefault("database_permissions", {})
        db_user_perms = db_perms.setdefault(username, [])
        for p in ["USAGE", "READ"]:
            if p not in db_user_perms:
                db_user_perms.append(p)
        self._save(db_name, data)
        print(f"Granted {permission} on {db_name}.{table_name} to {username}")
        return True

    def revoke(self, db_name: str, table_name: str, username: str, permission: str,
               caller_username: str, caller_role: str) -> bool:
        data = self._load(db_name)
        owner = data.get("owner")
        if caller_role != "admin" and caller_username != owner:
            print("Permission denied")
            return False
        permission = permission.upper()
        table_perms = data.get("table_permissions", {})
        if username in table_perms and table_name in table_perms[username]:
            perms = [p.upper() for p in table_perms[username][table_name]]
            if permission in perms:
                perms.remove(permission)
                table_perms[username][table_name] = perms
                if not perms:
                    del table_perms[username][table_name]
                if not table_perms[username]:
                    del table_perms[username]
                print(f"Revoked {permission} from {username} on {table_name}")
            else:
                print(f"No {permission} to revoke")
        else:
            print("No permission found")
        self._save(db_name, data)
        return True

    def show_grants(self, db_name: str, username: str) -> None:
        data = self._load(db_name)
        owner = data.get("owner")
        print("═" * 60)
        print(f" PERMISSIONS FOR {username} ON {db_name} ".center(60, " "))
        print("═" * 60)
        if owner == username:
            print(" OWNER (ALL PRIVILEGES)")
        else:
            db_perms = data.get("database_permissions", {}).get(username, [])
            if db_perms:
                print(f" Database: {', '.join(db_perms)}")
            table_perms = data.get("table_permissions", {}).get(username, {})
            if table_perms:
                for t, perms in table_perms.items():
                    print(f" {t}: {', '.join(perms)}")
            if not db_perms and not table_perms:
                print(" No permissions")
        print("═" * 60)

    def cleanup_database_permissions(self, db_name: str):
        perm_path = self._get_perm_path(db_name)
        if perm_path.exists():
            perm_path.unlink()

    def cleanup_table_permissions(self, db_name: str, table_name: str):
        data = self._load(db_name)
        changed = False
        for user in list(data.get("table_permissions", {})):
            if table_name in data["table_permissions"][user]:
                del data["table_permissions"][user][table_name]
                changed = True
                if not data["table_permissions"][user]:
                    del data["table_permissions"][user]
        if changed:
            self._save(db_name, data)