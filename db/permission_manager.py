import os, json
from pathlib import Path


class PermissionManager:

    # Structure JSON recommandée pour le fichier de permissions:
    """
    {
    "owner": "username",
    "database_permissions": {
        "user1": ["READ", "WRITE"],
        "user2": ["ALL"]
    },
    "table_permissions": {
        "user1": {
        "table1": ["SELECT", "INSERT"],
        "table2": ["SELECT"]
        },
        "user2": {
        "table1": ["ALL"]
        }
    }
    }
    """
    VALID_PERMISSIONS = {"READ", "WRITE", "DELETE", "UPDATE", "ALL"}

    def __init__(self, db_path: str):
        self.perm_folder = f"{db_path}/.permissions"
        os.makedirs(self.perm_folder, exist_ok=True)
        self.db_path = db_path


    def get_permission_file(self, db_name):
        path = f"{self.perm_folder}/{db_name}.json"
        if not os.path.exists(path):
            with open(path, "w") as f:
                json.dump({"__owner__": None}, f, indent=4)
        return path

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
# Méthodes à ajouter dans permission_manager.py pour synchronisation complète

    def is_owner(self, db_name: str, username: str) -> bool:
        """
        Vérifie si un utilisateur est propriétaire d'une base de données
        
        Args:
            db_name: Nom de la base de données
            username: Nom de l'utilisateur
            
        Returns:
            bool: True si propriétaire, False sinon
        """
        perm_file = Path(f"{self.db_path}/.permissions/{db_name}_permissions.json")
        
        if not perm_file.exists():
            return False
        
        try:
            with open(perm_file, "r", encoding="utf-8") as f:
                permissions = json.load(f)
            
            return permissions.get("owner") == username
        except Exception:
            return False

    def set_owner(self, db_name: str, username: str) -> bool:
        """
        Définit le propriétaire d'une base de données
        
        Args:
            db_name: Nom de la base de données
            username: Nom de l'utilisateur
            
        Returns:
            bool: True si défini avec succès, False sinon
        """
        perm_dir = Path(f"{self.db_path}/.permissions")
        perm_dir.mkdir(exist_ok=True)
        
        perm_file = perm_dir / f"{db_name}_permissions.json"
        
        try:
            # Charger les permissions existantes ou créer nouvelles
            if perm_file.exists():
                with open(perm_file, "r", encoding="utf-8") as f:
                    permissions = json.load(f)
            else:
                permissions = {
                    "owner": "",
                    "database_permissions": [],
                    "table_permissions": [],
                    "other" : []
                }
            
            # Définir le propriétaire
            permissions["owner"] = username
            permissions["database_permissions"] = ["All"]
            permissions["table_permissions"] = ["ALL"]            
            # Sauvegarder
            with open(perm_file, "w", encoding="utf-8") as f:
                json.dump(permissions, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la définition du propriétaire: {e}")
            return False

    def cleanup_database_permissions(self, db_name: str) -> bool:
        """
        Nettoie toutes les permissions associées à une base de données supprimée
        
        Args:
            db_name: Nom de la base de données
            
        Returns:
            bool: True si nettoyé avec succès, False sinon
        """
        perm_file = Path(f"{self.db_path}/.permissions/{db_name}_permissions.json")
        
        if not perm_file.exists():
            return True  # Rien à nettoyer
        
        try:
            perm_file.unlink()
            print(f"✓ Permissions of '{db_name}' clean")
            return True
        except Exception as e:
            print(f"❌ error occurd when cleaning permission: {e}")
            return False

    def cleanup_table_permissions(self, db_name: str, table_name: str) -> bool:
        """
        Nettoie les permissions d'une table supprimée
        
        Args:
            db_name: Nom de la base de données
            table_name: Nom de la table
            
        Returns:
            bool: True si nettoyé avec succès, False sinon
        """
        perm_file = Path(f"{self.db_path}/.permissions/{db_name}_permissions.json")
        
        if not perm_file.exists():
            return True
        
        try:
            with open(perm_file, "r", encoding="utf-8") as f:
                permissions = json.load(f)
            
            # Nettoyer les permissions de la table
            table_perms = permissions.get("table_permissions", {})
            
            # Supprimer toutes les entrées pour cette table
            users_to_clean = []
            for username, user_table_perms in table_perms.items():
                if table_name in user_table_perms:
                    del user_table_perms[table_name]
                    # Si l'utilisateur n'a plus de permissions, le marquer
                    if not user_table_perms:
                        users_to_clean.append(username)
            
            # Nettoyer les utilisateurs sans permissions
            for username in users_to_clean:
                del table_perms[username]
            
            # Sauvegarder
            with open(perm_file, "w", encoding="utf-8") as f:
                json.dump(permissions, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"❌ Erreur lors du nettoyage des permissions de table: {e}")
            return False

    def user_has_any_permission(self, db_name: str, username: str) -> bool:
        """
        Vérifie si un utilisateur a au moins une permission sur une base de données
        
        Args:
            db_name: Nom de la base de données
            username: Nom de l'utilisateur
            
        Returns:
            bool: True si l'utilisateur a au moins une permission, False sinon
        """
        perm_file = Path(f"{self.db_path}/.permissions/{db_name}_permissions.json")
        
        if not perm_file.exists():
            return False
        
        try:
            with open(perm_file, "r", encoding="utf-8") as f:
                permissions = json.load(f)
            
            # Vérifier si propriétaire
            if permissions.get("owner") == username:
                return True
            
            # Vérifier permissions au niveau base de données
            db_perms = permissions.get("database_permissions", {})
            if username in db_perms and db_perms[username]:
                return True
            
            # Vérifier permissions au niveau tables
            table_perms = permissions.get("table_permissions", {})
            if username in table_perms and table_perms[username]:
                return True
            
            return False
        except Exception:
            return False

    def has_db_permission(self, db_name: str, username: str, permission: str) -> bool:
        """
        Vérifie si un utilisateur a une permission spécifique au niveau base de données
        
        Args:
            db_name: Nom de la base de données
            username: Nom de l'utilisateur
            permission: Permission à vérifier (READ, WRITE, ALL, etc.)
            
        Returns:
            bool: True si l'utilisateur a la permission, False sinon
        """
        perm_file = Path(f"{self.db_path}/.permissions/{db_name}_permissions.json")
        
        if not perm_file.exists():
            return False
        
        try:
            with open(perm_file, "r", encoding="utf-8") as f:
                permissions = json.load(f)
            
            # Propriétaire a tous les droits
            if permissions.get("owner") == username:
                return True
            
            # Vérifier permissions de la base
            db_perms = permissions.get("database_permissions", {})
            user_perms = db_perms.get(username, [])
            
            # ALL inclut toutes les permissions
            if "ALL" in user_perms:
                return True
            
            return permission in user_perms
        except Exception:
            return False

    def has_table_permission(self, db_name: str, table_name: str, username: str, permission: str) -> bool:
        """
        Vérifie si un utilisateur a une permission spécifique sur une table
        
        Args:
            db_name: Nom de la base de données
            table_name: Nom de la table
            username: Nom de l'utilisateur
            permission: Permission à vérifier (SELECT, INSERT, UPDATE, DELETE, ALL, etc.)
            
        Returns:
            bool: True si l'utilisateur a la permission, False sinon
        """
        perm_file = Path(f"{self.db_path}/.permissions/{db_name}_permissions.json")
        
        if not perm_file.exists():
            return False
        
        try:
            with open(perm_file, "r", encoding="utf-8") as f:
                permissions = json.load(f)
            
            # Propriétaire a tous les droits
            if permissions.get("owner") == username:
                return True
            
            # Vérifier permissions de la table
            table_perms = permissions.get("table_permissions", {})
            user_table_perms = table_perms.get(username, {})
            table_perm_list = user_table_perms.get(table_name, [])
            
            # ALL inclut toutes les permissions
            if "ALL" in table_perm_list:
                return True
            
            return permission in table_perm_list
        except Exception:
            return False

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
