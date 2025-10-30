import json
from pathlib import Path
from typing import Dict, Any


class PermissionManager:
    """Gestionnaire des permissions pour les bases et tables"""

    def __init__(self, db_path: str = ".database"):
        self.dbPath = Path(db_path)
        self.dbPath.mkdir(exist_ok=True)

    # -----------------------------
    # INIT & OWNER
    # -----------------------------
    def set_owner(self, db_name: str, username: str) -> None:
        """
        Initialise le fichier de permissions avec un propriétaire
        et la structure standardisée :
        {
          "owner": "root",
          "database_permissions": {},
          "table_permissions": {
            "root": {}
          }
        }
        """
        perm_path = self.dbPath / db_name / "permissions.json"

        data = {
            "owner": username,
            "database_permissions": {},
            "table_permissions": {
                username: {}
            }
        }

        with open(perm_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"[set_owner] ✅ Owner set to '{username}' for {db_name}")

    def get_owner(self, db_name: str) -> str:
        """Retourne le propriétaire d'une base"""
        perm_path = self.dbPath / db_name / "permissions.json"
        if not perm_path.exists():
            return None
        try:
            with open(perm_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("owner")
        except Exception:
            return None

    # -----------------------------
    # GRANT & REVOKE
    # -----------------------------
    def grant(self, db_name: str, table_name: str, username: str, permission: str,
            caller_username: str, caller_role: str) -> bool:
        """
        Accorde une permission sur une table à un utilisateur.
        Donne aussi automatiquement le droit de lecture ('READ') sur la base
        si l'utilisateur ne l'a pas déjà.
        """
        perm_path = self.dbPath / db_name / "permissions.json"

        # Si le fichier n'existe pas, on initialise
        if not perm_path.exists():
            print(f"⚠️ Permission file not found for {db_name}, initializing...")
            self.set_owner(db_name, caller_username)

        # Lecture du fichier existant
        with open(perm_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # --- Étape 1 : Ajouter le droit sur la table ---
        table_perms = data.setdefault("table_permissions", {})
        user_perms = table_perms.setdefault(username, {})
        table_perms_list = user_perms.setdefault(table_name, [])

        if permission not in table_perms_list:
            table_perms_list.append(permission)
            print(f"✅ Granted {permission} to {username} on table '{table_name}'")

        # --- Étape 2 : Donner automatiquement READ sur la base ---
        db_perms = data.setdefault("database_permissions", {})
        db_user_perms = db_perms.setdefault(username, [])

        if "READ" not in db_user_perms:
            db_user_perms.append("READ")
            print(f"🟢 Automatically granted READ access to {username} on database '{db_name}'")

        # --- Sauvegarde finale ---
        with open(perm_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return True

    def revoke(self, db_name: str, table_name: str, username: str, permission: str) -> bool:
        """Révoque une permission"""
        perm_path = self.dbPath / db_name / "permissions.json"
        if not perm_path.exists():
            print("⚠️ No permissions file found")
            return False

        with open(perm_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        table_perms = data.get("table_permissions", {})
        user_perms = table_perms.get(username, {})
        perms_list = user_perms.get(table_name, [])

        if permission in perms_list:
            perms_list.remove(permission)
            if not perms_list:
                user_perms.pop(table_name, None)
            if not user_perms:
                table_perms.pop(username, None)
        else:
            print(f"⚠️ {username} n’avait pas {permission} sur {table_name}")

        # Sauvegarde
        with open(perm_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"🧹 Revoked {permission} from {username} on {table_name}")
        return True

    # -----------------------------
    # CLEANUP
    # -----------------------------
    def cleanup_database_permissions(self, db_name: str) -> None:
        """Supprime le fichier de permissions associé à une base"""
        perm_path = self.dbPath / db_name / "permissions.json"
        if perm_path.exists():
            perm_path.unlink()
            print(f"[cleanup] Deleted permissions file for {db_name}")

    def cleanup_table_permissions(self, db_name: str, table_name: str) -> None:
        """Supprime les permissions liées à une table supprimée"""
        perm_path = self.dbPath / db_name / "permissions.json"
        if not perm_path.exists():
            return

        with open(perm_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        table_perms = data.get("table_permissions", {})
        for user in list(table_perms.keys()):
            user_tables = table_perms[user]
            if table_name in user_tables:
                del user_tables[table_name]
                if not user_tables:
                    del table_perms[user]

        with open(perm_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"[cleanup] Table '{table_name}' permissions removed from {db_name}")
