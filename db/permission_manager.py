import json
from pathlib import Path
from typing import Any, List


class PermissionManager:
    """Gestionnaire des permissions pour les bases et tables"""

    def __init__(self, db_path: str = ".database"):
        self.dbPath = Path(db_path)
        self.dbPath.mkdir(exist_ok=True)

    # -----------------------------
    # INIT & OWNER
    # -----------------------------
    def set_owner(self, db_name: str, username: str) -> None:
        """Initialise le fichier de permissions avec un propriétaire."""
        db_folder = self.dbPath / db_name
        db_folder.mkdir(exist_ok=True)

        perm_path = db_folder / "permissions.json"

        data = {
            "owner": username,
            "database_permissions": {},
            "table_permissions": {
                username: {}
            }
        }

        with open(perm_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✓ Owner set to '{username}' for database '{db_name}'")

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

    def is_owner(self, db_name: str, username: str) -> bool:
        """Vérifie si un utilisateur est propriétaire"""
        return self.get_owner(db_name) == username

    # -----------------------------
    # PERMISSION CHECK - CORRIGÉ
    # -----------------------------
    def has_db_permission(self, db_name: str, username: str, required_perm: str = "READ") -> bool:
        """
        Vérifie si un utilisateur a une permission spécifique au niveau DATABASE.
        """
        perm_path = self.dbPath / db_name / "permissions.json"
        if not perm_path.exists():
            return False

        try:
            with open(perm_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Le propriétaire a TOUS les droits
            if data.get("owner") == username:
                return True

            # Vérifier les permissions au niveau base de données
            db_perms = data.get("database_permissions", {})
            user_perms = db_perms.get(username, [])

            # Normaliser les permissions en majuscules
            user_perms = [p.upper() for p in user_perms]
            required_perm = required_perm.upper()

            # ALL donne tous les droits
            if "ALL" in user_perms:
                return True

            return required_perm in user_perms

        except Exception as e:
            print(f"[DEBUG] Error in has_db_permission: {e}")
            return False

    def has_table_permission(self, db_name: str, table_name: str, username: str, required_perm: str) -> bool:
        """
        Vérifie si un utilisateur a une permission spécifique sur une TABLE.
        """
        perm_path = self.dbPath / db_name / "permissions.json"
        if not perm_path.exists():
            return False

        try:
            with open(perm_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Le propriétaire a TOUS les droits
            if data.get("owner") == username:
                return True

            # Vérifier permissions sur la table
            table_perms = data.get("table_permissions", {})
            user_table_perms = table_perms.get(username, {})
            table_perm_list = user_table_perms.get(table_name, [])

            # Normaliser
            table_perm_list = [p.upper() for p in table_perm_list]
            required_perm = required_perm.upper()

            # ALL donne tous les droits
            if "ALL" in table_perm_list:
                return True

            return required_perm in table_perm_list

        except Exception as e:
            print(f"[DEBUG] Error in has_table_permission: {e}")
            return False

    def user_has_any_permission(self, db_name: str, username: str) -> bool:
        """
        Vérifie si un utilisateur a AU MOINS UNE permission sur la base.
        Utilisé pour list_table.
        """
        perm_path = self.dbPath / db_name / "permissions.json"
        if not perm_path.exists():
            return False

        try:
            with open(perm_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Propriétaire = OUI
            if data.get("owner") == username:
                return True

            # Vérifier permissions DB
            db_perms = data.get("database_permissions", {})
            if username in db_perms and db_perms[username]:
                return True

            # Vérifier permissions tables
            table_perms = data.get("table_permissions", {})
            if username in table_perms and table_perms[username]:
                return True

            return False

        except Exception:
            return False

    # -----------------------------
    # GRANT & REVOKE - CORRIGÉ
    # -----------------------------
    def grant(self, db_name: str, table_name: str, username: str, permission: str,
              caller_username: str, caller_role: str) -> bool:
        """
        Accorde une permission sur une table à un utilisateur.
        IMPORTANT: Accorde aussi automatiquement USAGE sur la base.
        """
        db_folder = self.dbPath / db_name
        perm_path = db_folder / "permissions.json"

        if not perm_path.exists():
            print(f"⚠️ Permission file not found for {db_name}, initializing...")
            self.set_owner(db_name, caller_username)

        with open(perm_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Vérifier autorisation du caller
        owner = data.get("owner")
        if caller_role != "admin" and caller_username != owner:
            print(f"❌ Permission denied: only owner ({owner}) or admin can grant.")
            return False

        # Normaliser la permission
        permission = permission.upper()

        # TABLE PERMISSIONS
        table_perms = data.setdefault("table_permissions", {})
        user_perms = table_perms.setdefault(username, {})
        table_perm_list = user_perms.setdefault(table_name, [])

        if permission not in table_perm_list:
            table_perm_list.append(permission)

        # DATABASE PERMISSIONS : donner automatiquement USAGE et READ
        # CRITIQUE: sans ces permissions, l'utilisateur ne peut pas accéder à la base
        db_perms = data.setdefault("database_permissions", {})
        db_user_perms = db_perms.setdefault(username, [])
        
        for auto_perm in ["USAGE", "READ"]:
            if auto_perm not in db_user_perms:
                db_user_perms.append(auto_perm)

        # Sauvegarder
        with open(perm_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✓ Granted {permission} on {db_name}.{table_name} to {username}")
        print(f"  (Auto-granted USAGE and READ on database '{db_name}')")
        return True

    def revoke(self, db_name: str, table_name: str, username: str, permission: str,
               caller_username: str, caller_role: str) -> bool:
        """Révoque une permission sur une table."""
        perm_path = self.dbPath / db_name / "permissions.json"
        if not perm_path.exists():
            print("⚠️ No permissions file found")
            return False

        with open(perm_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        owner = data.get("owner")
        if caller_role != "admin" and caller_username != owner:
            print(f"❌ Permission denied: only owner ({owner}) or admin can revoke.")
            return False

        # Normaliser
        permission = permission.upper()

        table_perms = data.get("table_permissions", {})
        user_perms = table_perms.get(username, {})
        perms_list = user_perms.get(table_name, [])

        # Normaliser la liste existante
        perms_list = [p.upper() for p in perms_list]

        if permission in perms_list:
            perms_list.remove(permission)
            user_perms[table_name] = perms_list
            
            # Nettoyer si vide
            if not perms_list:
                user_perms.pop(table_name, None)
            if not user_perms:
                table_perms.pop(username, None)
            
            print(f"✓ Revoked {permission} from {username} on {db_name}.{table_name}")
        else:
            print(f"⚠️ {username} didn't have {permission} on {table_name}")

        # Sauvegarder
        with open(perm_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return True

    def show_grants(self, db_name: str, username: str) -> None:
        """Affiche toutes les permissions d'un utilisateur sur une base."""
        perm_path = self.dbPath / db_name / "permissions.json"
        
        if not perm_path.exists():
            print(f"⚠️ No permissions file for database '{db_name}'")
            return

        try:
            with open(perm_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            owner = data.get("owner")
            
            print("═" * 60)
            print(f"{'PERMISSIONS FOR ' + username + ' ON ' + db_name:^60}")
            print("═" * 60)

            # Si propriétaire
            if owner == username:
                print(f"👑 {username} is OWNER of this database (ALL PRIVILEGES)")
                print("═" * 60)
                return

            # Permissions au niveau DATABASE
            db_perms = data.get("database_permissions", {})
            user_db_perms = db_perms.get(username, [])
            
            if user_db_perms:
                print(f"\n📦 Database-level permissions:")
                for perm in user_db_perms:
                    print(f"   • {perm}")
            else:
                print(f"\n📦 Database-level permissions: None")

            # Permissions au niveau TABLE
            table_perms = data.get("table_permissions", {})
            user_table_perms = table_perms.get(username, {})
            
            if user_table_perms:
                print(f"\n📋 Table-level permissions:")
                for table, perms in user_table_perms.items():
                    print(f"   {table}:")
                    for perm in perms:
                        print(f"      • {perm}")
            else:
                print(f"\n📋 Table-level permissions: None")

            print("═" * 60)

        except Exception as e:
            print(f"❌ Error reading permissions: {e}")

    # -----------------------------
    # CLEANUP
    # -----------------------------
    def cleanup_database_permissions(self, db_name: str) -> None:
        """Supprime le fichier de permissions associé à une base"""
        perm_path = self.dbPath / db_name / "permissions.json"
        if perm_path.exists():
            perm_path.unlink()
            print(f"✓ Deleted permissions file for {db_name}")

    def cleanup_table_permissions(self, db_name: str, table_name: str) -> None:
        """Supprime les permissions liées à une table supprimée"""
        perm_path = self.dbPath / db_name / "permissions.json"
        if not perm_path.exists():
            return

        try:
            with open(perm_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            table_perms = data.get("table_permissions", {})
            
            # Parcourir tous les utilisateurs
            for user in list(table_perms.keys()):
                user_tables = table_perms[user]
                if table_name in user_tables:
                    del user_tables[table_name]
                    # Si l'utilisateur n'a plus de permissions sur aucune table
                    if not user_tables:
                        del table_perms[user]

            # Sauvegarder
            with open(perm_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"✓ Table '{table_name}' permissions removed from {db_name}")

        except Exception as e:
            print(f"❌ Error cleaning table permissions: {e}")