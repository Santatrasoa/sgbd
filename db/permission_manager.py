# db/permission_manager.py
import json
from pathlib import Path

class PermissionManager:
    def __init__(self, db_path: str = ".database"):
        self.dbPath = Path(db_path)
        self.dbPath.mkdir(exist_ok=True)

    def set_owner(self, db_name: str, username: str) -> None:
        db_folder = self.dbPath / db_name
        db_folder.mkdir(exist_ok=True)
        perm_path = db_folder / "permissions.json"
        data = {
            "owner": username,
            "database_permissions": {username: ["ALL"]},
            "table_permissions": {username: {}}
        }
        with open(perm_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_owner(self, db_name: str) -> str:
        perm_path = self.dbPath / db_name / "permissions.json"
        if not perm_path.exists():
            return None
        try:
            with open(perm_path, "r", encoding="utf-8") as f:
                return json.load(f).get("owner")
        except:
            return None

    def has_db_permission(self, db_name: str, username: str, required_perm: str) -> bool:
        perm_path = self.dbPath / db_name / "permissions.json"
        if not perm_path.exists():
            return False
        try:
            with open(perm_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("owner") == username:
                return True
            perms = data.get("database_permissions", {}).get(username, [])
            perms = [p.upper() for p in perms]
            return "ALL" in perms or required_perm.upper() in perms
        except:
            return False

    def has_table_permission(self, db_name: str, table_name: str, username: str, required_perm: str) -> bool:
        perm_path = self.dbPath / db_name / "permissions.json"
        if not perm_path.exists():
            return False
        try:
            with open(perm_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("owner") == username:
                return True
            user_perms = data.get("table_permissions", {}).get(username, {})
            perms = user_perms.get(table_name, [])
            perms = [p.upper() for p in perms]
            return "ALL" in perms or required_perm.upper() in perms
        except:
            return False

    def user_has_any_permission(self, db_name: str, username: str) -> bool:
        perm_path = self.dbPath / db_name / "permissions.json"
        if not perm_path.exists():
            return False
        try:
            with open(perm_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("owner") == username:
                return True
            if username in data.get("database_permissions", {}):
                return True
            if username in data.get("table_permissions", {}):
                return any(data["table_permissions"][username].values())
            return False
        except:
            return False

    def grant(self, db_name: str, table_name: str, username: str, permission: str,
              caller_username: str, caller_role: str) -> bool:
        perm_path = self.dbPath / db_name / "permissions.json"
        if not perm_path.exists():
            return False
        try:
            with open(perm_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            owner = data.get("owner")
            if caller_role != "admin" and caller_username != owner:
                print(f"Permission denied: only owner or admin can grant")
                return False

            permission = permission.upper()
            # Table permission
            table_perms = data.setdefault("table_permissions", {})
            user_perms = table_perms.setdefault(username, {})
            perms_list = user_perms.setdefault(table_name, [])
            if permission not in perms_list:
                perms_list.append(permission)

            # Auto-grant USAGE + READ on DB
            db_perms = data.setdefault("database_permissions", {})
            db_user_perms = db_perms.setdefault(username, [])
            for p in ["USAGE", "READ"]:
                if p not in db_user_perms:
                    db_user_perms.append(p)

            with open(perm_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Granted {permission} on {db_name}.{table_name} to {username}")
            return True
        except Exception as e:
            print(f"Error granting permission: {e}")
            return False

    def revoke(self, db_name: str, table_name: str, username: str, permission: str,
               caller_username: str, caller_role: str) -> bool:
        perm_path = self.dbPath / db_name / "permissions.json"
        if not perm_path.exists():
            return False
        try:
            with open(perm_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            owner = data.get("owner")
            if caller_role != "admin" and caller_username != owner:
                print("Permission denied")
                return False

            permission = permission.upper()
            table_perms = data.get("table_permissions", {})
            if username in table_perms and table_name in table_perms[username]:
                perms = table_perms[username][table_name]
                perms = [p.upper() for p in perms]
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
                print(f"No permission found")

            with open(perm_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error revoking: {e}")
            return False

    def show_grants(self, db_name: str, username: str) -> None:
        perm_path = self.dbPath / db_name / "permissions.json"
        if not perm_path.exists():
            print(f"No permissions for database '{db_name}'")
            return
        try:
            with open(perm_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            owner = data.get("owner")
            print("═" * 60)
            print(f" PERMISSIONS FOR {username} ON {db_name} ".center(60, " "))
            print("═" * 60)
            if owner == username:
                print(f" OWNER (ALL PRIVILEGES)")
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
        except Exception as e:
            print(f"Error: {e}")

    def cleanup_database_permissions(self, db_name: str):
        perm_path = self.dbPath / db_name / "permissions.json"
        if perm_path.exists():
            perm_path.unlink()

    def cleanup_table_permissions(self, db_name: str, table_name: str):
        perm_path = self.dbPath / db_name / "permissions.json"
        if not perm_path.exists():
            return
        try:
            with open(perm_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            changed = False
            for user in data.get("table_permissions", {}):
                if table_name in data["table_permissions"][user]:
                    del data["table_permissions"][user][table_name]
                    changed = True
                    if not data["table_permissions"][user]:
                        del data["table_permissions"][user]
            if changed:
                with open(perm_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
        except:
            pass
