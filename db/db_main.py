# db/db_main.py
import os
import shutil
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from .user_manager import UserManager
from .permission_manager import PermissionManager


class Db:
    """Classe principale pour la gestion de base de données"""

    def __init__(self, db_path: str = ".database"):
        self.dbPath = db_path
        self.userManager = UserManager(self.dbPath)
        self.permManager = PermissionManager(self.dbPath)
        self.current_user = {"username": "root", "role": "admin"}
        Path(self.dbPath).mkdir(exist_ok=True)

    # =============================
    # DATABASE
    # =============================

    def create_DB(self, dbName: str) -> bool:
        """Crée une nouvelle base de données"""
        if not dbName or not dbName.strip():
            print("Database name cannot be empty")
            return False
        path = Path(f"{self.dbPath}/{dbName}")
        if path.exists():
            print(f"Database '{dbName}' already exists")
            return False
        try:
            path.mkdir(parents=True, exist_ok=False)
            username = self.current_user["username"]
            self.permManager.set_owner(dbName, username)
            print(f"Database '{dbName}' created successfully")
            return True
        except Exception as e:
            print(f"Error creating database: {e}")
            return False

    def list_database(self, path: str = None) -> List[str]:
        """Liste toutes les bases de données disponibles"""
        directory = Path(path or self.dbPath)
        if not directory.exists():
            return []
        return [
            item.name for item in directory.iterdir()
            if item.is_dir() and not item.name.startswith(".")
        ]

    def drop_database(self, databaseName: str) -> bool:
        """Supprime une base de données"""
        if not databaseName or not databaseName.strip():
            print("Database name cannot be empty")
            return False
        path = Path(f"{self.dbPath}/{databaseName}")
        if not path.exists():
            print(f"Database '{databaseName}' does not exist")
            return False
        try:
            shutil.rmtree(path)
            self.permManager.cleanup_database_permissions(databaseName)
            print(f"Database '{databaseName}' removed successfully")
            return True
        except Exception as e:
            print(f"Error deleting database: {e}")
            return False

    def show_databases(self) -> None:
        """Affiche toutes les bases de données disponibles"""
        allDirs = self.list_database()
        if not allDirs:
            print("No databases found")
            return
        max_len = max([len(d) for d in allDirs] + [15])
        separator = "—" * (max_len + 4)
        print(separator)
        print(f"{'DATABASES':^{max_len + 4}}")
        print(separator)
        for db_name in sorted(allDirs):
            is_owner = self.permManager.get_owner(db_name) == self.current_user["username"]
            owner_mark = " (owner)" if is_owner else ""
            print(f" {db_name:<{max_len}}{owner_mark}")
        print(separator)
        print(f"Total: {len(allDirs)} database{'s' if len(allDirs) > 1 else ''}")

    # =============================
    # TABLES
    # =============================

    def list_table(self, path: str) -> List[str]:
        """Liste toutes les tables dans une base de données"""
        directory = Path(path)
        if not directory.exists():
            return []
        return [
            item.name for item in directory.iterdir()
            if item.is_file() and item.suffix == '.json' and not item.name.startswith(".")
        ]

    def create_Table(self, dbName: str, name: str, attribute: Dict[str, Any]) -> bool:
        """Crée une nouvelle table"""
        if not name or not name.strip():
            print("Table name cannot be empty")
            return False
        path = Path(f"{self.dbPath}/{dbName}/{name}.json")
        if path.exists():
            print(f"Table '{name}' already exists")
            return False
        try:
            if "caracteristique" not in attribute:
                print("Table definition must include 'caracteristique'")
                return False
            if "data" not in attribute:
                attribute["data"] = []
            with open(path, "w", encoding="utf-8") as f:
                json.dump(attribute, f, indent=2, ensure_ascii=False)
            username = self.current_user["username"]
            self.permManager.grant(dbName, name, username, "ALL",
                                   caller_username=username,
                                   caller_role=self.current_user["role"])
            print(f"Table '{name}' created successfully")
            return True
        except Exception as e:
            print(f"Error creating table: {e}")
            if path.exists():
                path.unlink()
            return False

    def drop_table(self, dbName: str, tableName: str) -> bool:
        """Supprime une table"""
        if not tableName or not tableName.strip():
            print("Table name cannot be empty")
            return False
        path = Path(f"{self.dbPath}/{dbName}/{tableName}.json")
        if not path.exists():
            print(f"Table '{tableName}' does not exist")
            return False
        try:
            path.unlink()
            self.permManager.cleanup_table_permissions(dbName, tableName)
            print(f"Table '{tableName}' removed successfully")
            return True
        except Exception as e:
            print(f"Error deleting table: {e}")
            return False

    def analyse_data(self, path: str, data: List[str]) -> bool:
        """Ajoute des données dans une table"""
        if not os.path.exists(path):
            print("Table does not exist")
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = json.load(f)
            caracteristiques = content.get("caracteristique", {})
            raw_constraints = content.get("constraint", {})
            constraints = {
                col: [c.lower() for c in (vals if isinstance(vals, list) else [vals])]
                for col, vals in raw_constraints.items()
            }
            if not caracteristiques:
                print("Table has no defined columns")
                return False

            addedData = {}
            for item in data:
                item = item.strip()
                if "=" not in item:
                    print(f"Syntax error in '{item}' (expected: col=value)")
                    return False
                col, value = item.split("=", 1)
                col = col.strip()
                value = value.strip().strip("'").strip('"')
                if col not in caracteristiques:
                    print(f"Column '{col}' does not exist")
                    print(f"Available: {', '.join(caracteristiques.keys())}")
                    return False
                addedData[col] = value

            # NOT NULL
            for col, cons in constraints.items():
                if 'not_null' in cons and col not in addedData:
                    print(f"Column '{col}' cannot be NULL")
                    return False

            # UNIQUE
            existing = content.get("data", [])
            for col, cons in constraints.items():
                if 'unique' in cons and col in addedData:
                    for row in existing:
                        if row.get(col) == addedData[col]:
                            print(f"UNIQUE constraint violation on '{col}'")
                            return False

            content["data"].append(addedData)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
            print("Data added successfully")
            return True
        except json.JSONDecodeError:
            print("Corrupted JSON file")
            return False
        except Exception as e:
            print(f"Error inserting data: {e}")
            return False

    def describe_table(self, path: str) -> bool:
        """Affiche la description d'une table"""
        if not os.path.exists(path):
            print("Table does not exist")
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = json.load(f)
            caracteristiques = content.get("caracteristique", {})
            raw_constraints = content.get("constraint", {})
            constraints = {
                col: [c.lower() for c in (vals if isinstance(vals, list) else [vals])]
                for col, vals in raw_constraints.items()
            }
            data_count = len(content.get("data", []))
            if not caracteristiques:
                print("Table has no defined columns")
                return True

            max_col_len = max([len(k) for k in caracteristiques.keys()] + [10])
            max_type_len = max([len(str(v)) for v in caracteristiques.values()] + [10])
            separator = "—" * (max_col_len + max_type_len + 40)
            table_name = Path(path).stem
            print(separator)
            print(f"{'TABLE: ' + table_name.upper():^{len(separator)}}")
            print(separator)
            print(f"{'Column':<{max_col_len}} | {'Type':<{max_type_len}} | Constraints")
            print(separator)
            for col, col_type in caracteristiques.items():
                cons_list = constraints.get(col, ["no constraint"])
                if "no constraint" in cons_list:
                    cons_str = "None"
                else:
                    cons_str = ", ".join([c.upper() if len(c) <= 6 else c.capitalize() for c in cons_list])
                print(f"{col:<{max_col_len}} | {col_type:<{max_type_len}} | {cons_str}")
            print(separator)
            print(f"Total: {len(caracteristiques)} column{'s' if len(caracteristiques) > 1 else ''}, "
                  f"{data_count} row{'s' if data_count > 1 else ''}")
            print(separator)
            return True
        except json.JSONDecodeError:
            print("Corrupted JSON file")
            return False
        except Exception as e:
            print(f"Error reading table: {e}")
            return False

    def table_exists(self, dbName: str, tableName: str) -> bool:
        """Vérifie si une table existe"""
        return Path(f"{self.dbPath}/{dbName}/{tableName}.json").exists()

    def get_table_info(self, dbName: str, tableName: str) -> Optional[Dict[str, Any]]:
        """Récupère les infos d'une table"""
        path = Path(f"{self.dbPath}/{dbName}/{tableName}.json")
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    # =============================
    # STATISTIQUES
    # =============================

    def get_statistics(self, dbName: str) -> Dict[str, Any]:
        """Statistiques d'une base de données"""
        stats = {"database": dbName, "tables": 0, "total_rows": 0, "total_columns": 0}
        path = Path(f"{self.dbPath}/{dbName}")
        if not path.exists():
            return stats
        tables = self.list_table(str(path))
        stats["tables"] = len(tables)
        for table_file in tables:
            try:
                with open(path / table_file, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    stats["total_rows"] += len(content.get("data", []))
                    stats["total_columns"] += len(content.get("caracteristique", {}))
            except Exception:
                continue
        return stats

    # =============================
    # HELP
    # =============================

    def show_help(self) -> None:
        """Affiche l'aide complète"""
        help_text = """
╔══════════════════════════════════════════════════════════════╗
║                COMMANDES DISPONIBLES - MY SGBD                ║
╚══════════════════════════════════════════════════════════════╝

BASES DE DONNÉES
  create_database <nom>        → Créer une base
  use_db <nom>                 → Sélectionner
  drop_db <nom>                → Supprimer
  list_db                      → Lister
  stats_db                     → Statistiques

TABLES
  create_table <nom>(col:type[contraintes], ...) → Créer
  add_into_table <t>(c=v, ...) → Insérer
  drop_table <nom>             → Supprimer
  list_table                   → Lister
  describe_table <nom>         → Structure

REQUÊTES
  select * from t [where c=v]  → Lire
  update t set c=v [where...]  → Modifier
  delete from t [where...]     → Supprimer

UTILISATEURS
  create_user n password=p [role=admin|user]
  switch_user_to n password=p
  drop_user n
  list_user

PERMISSIONS
  grant SELECT on table to user
  revoke DELETE on db.* from user
  show_grants user
  show_grants db user

SYSTÈME
  help | list_commands | clear | exit

TYPES : date, number, string, bool, ...
CONTRAINTES : not_null, unique, primary_key, ...
OPÉRATEURS WHERE : =, !=, >, LIKE %abc%, etc.
═══════════════════════════════════════════════════════════════
"""
        print(help_text)
