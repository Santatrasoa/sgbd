# db/db_main.py
import os
import shutil
import json
from pathlib import Path
from utils.config_loader import load_config
from typing import Dict, List, Any, Optional
from .user_manager import UserManager
from .permission_manager import PermissionManager

config = load_config()

class Db:
    def __init__(self, db_path: str = ".database", crypto=None):
        self.dbPath = Path(db_path)
        self.crypto = crypto
        self.userManager = UserManager(self.dbPath, self.crypto)
        self.permManager = PermissionManager(self.dbPath, self.crypto)
        self.current_user = {
            "username": config["default_admin"]["username"],
            "role": config["default_admin"]["role"]
        }
        self.dbPath.mkdir(exist_ok=True)
        self._migrate_json_to_enc()

    def _migrate_json_to_enc(self):
        for json_file in self.dbPath.rglob("*.json"):
            enc_file = json_file.with_suffix(".enc")
            if not enc_file.exists():
                print(f"Migrating: {json_file} → {enc_file.name}")
                try:
                    data = json.loads(json_file.read_text(encoding="utf-8"))
                    enc_file.write_bytes(self.crypto.encrypt(data))
                    json_file.unlink()
                except Exception as e:
                    print(f"Skip: {e}")

    def _get_table_path(self, db_name: str, table_name: str) -> Path:
        return self.dbPath / db_name / f"{table_name}.enc"

    def create_DB(self, dbName: str) -> bool:
        path = self.dbPath / dbName
        if path.exists():
            print(f"Database '{dbName}' already exists")
            return False
        path.mkdir(parents=True)
        self.permManager.set_owner(dbName, self.current_user["username"])
        print(f"Database '{dbName}' created successfully")
        return True

    def list_database(self):
        return [p.name for p in self.dbPath.iterdir() if p.is_dir()]

    def drop_database(self, databaseName: str) -> bool:
        path = self.dbPath / databaseName
        if not path.exists():
            print(f"Database '{databaseName}' does not exist")
            return False
        shutil.rmtree(path)
        self.permManager.cleanup_database_permissions(databaseName)
        print(f"Database '{databaseName}' removed")
        return True

    def create_Table(self, dbName: str, name: str, attribute: Dict[str, Any]) -> bool:
        path = self._get_table_path(dbName, name)
        if path.exists():
            print(f"Table '{name}' already exists")
            return False
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.crypto.encrypt(attribute))
        self.permManager.grant(dbName, name, self.current_user["username"], "ALL",
                               self.current_user["username"], self.current_user["role"])
        print(f"Table '{name}' created")
        return True

    def list_table(self, db_name: str) -> List[str]:
        """Liste toutes les tables (.enc) dans une base"""
        db_dir = self.dbPath / db_name
        if not db_dir.exists():
            return []
        return [f.stem for f in db_dir.glob("*.enc")]

    def load_table(self, db_name: str, table_name: str) -> dict:
        path = self._get_table_path(db_name, table_name)
        if not path.exists():
            raise FileNotFoundError()
        return self.crypto.decrypt(path.read_bytes())

    def save_table(self, db_name: str, table_name: str, data: dict):
        path = self._get_table_path(db_name, table_name)
        path.write_bytes(self.crypto.encrypt(data))

    def drop_table(self, dbName: str, tableName: str) -> bool:
        path = self._get_table_path(dbName, tableName)
        if not path.exists():
            print(f"Table '{tableName}' does not exist")
            return False
        path.unlink()
        self.permManager.cleanup_table_permissions(dbName, tableName)
        print(f"Table '{tableName}' removed")
        return True

    def analyse_data(self, db_name: str, table_name: str, data: List[str]) -> bool:
        path = self._get_table_path(db_name, table_name)
        if not path.exists():
            print("Table does not exist")
            return False
        try:
            content = self.crypto.decrypt(path.read_bytes())
            caracteristiques = content.get("caracteristique", {})
            constraints = content.get("constraint", {})
            addedData = {}
            for item in data:
                if "=" not in item:
                    print(f"Syntax error in '{item}'")
                    return False
                col, value = item.split("=", 1)
                col, value = col.strip(), value.strip().strip("'\"")
                if col not in caracteristiques:
                    print(f"Column '{col}' does not exist")
                    return False
                addedData[col] = value
            # Validation contraintes...
            content["data"].append(addedData)
            self.save_table(db_name, table_name, content)
            print("Data added")
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False
    def describe_table(self, db_name: str, table_name: str) -> None:  # ← Change en None
        path = self._get_table_path(db_name, table_name)
        if not path.exists():
            print(f"Table '{table_name}' does not exist")
            return

        try:
            content = self.crypto.decrypt(path.read_bytes())
            caracteristiques = content.get("caracteristique", {})
            constraints = content.get("constraint", {})
            data_count = len(content.get("data", []))

            if not caracteristiques:
                print("Table has no defined columns")
                return

            max_col_len = max(len(k) for k in caracteristiques.keys())
            max_type_len = max(len(str(v)) for v in caracteristiques.values())
            sep_len = max_col_len + max_type_len + 40
            separator = "—" * sep_len

            print(separator)
            print(f" TABLE: {table_name.upper()} ".center(sep_len, " "))
            print(separator)
            print(f"{'Column':<{max_col_len}} | {'Type':<{max_type_len}} | Constraints")
            print(separator)

            for col, col_type in caracteristiques.items():
                cons_list = constraints.get(col, ["no constraint"])
                cons_str = "None" if "no constraint" in cons_list else ", ".join([c.upper() for c in cons_list])
                print(f"{col:<{max_col_len}} | {col_type:<{max_type_len}} | {cons_str}")

            print(separator)
            print(f"Total: {len(caracteristiques)} column{'s' if len(caracteristiques) > 1 else ''}, "
                f"{data_count} row{'s' if data_count > 1 else ''}")
            print(separator)

            # self.check_constraints(db_name, table_name, {})  # Exemple d'appel

        except Exception as e:
            print(f"Error: {e}")
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

    def check_constraints(self, db_name: str, table_name: str, new_record: Dict[str, Any]) -> bool:
        """Vérifie les contraintes avant insertion"""
        path = self._get_table_path(db_name, table_name)
        if not path.exists():
            print(f"Table '{table_name}' does not exist")
            return False
        try:
            content = self.crypto.decrypt(path.read_bytes())
            constraints = content.get("constraint", {})
            data = content.get("data", [])

            for col, cons_list in constraints.items():
                print(col, cons_list)
                if col not in new_record:
                    continue
                value = new_record[col]

                for cons in cons_list:
                    if cons == "NOT NULL" and (value is None or value == ""):
                        print(f"Constraint violation: '{col}' cannot be NULL")
                        return False
                    if cons.startswith("UNIQUE"):
                        for record in data:
                            if record.get(col) == value:
                                print(f"Constraint violation: '{col}' must be UNIQUE")
                                return False
                    if cons.startswith("CHECK"):
                        condition = cons[6:-1].strip()  # Extrait la condition entre parenthèses
                        try:
                            if not eval(condition, {}, {col: value}):
                                print(f"Constraint violation: CHECK constraint failed for '{col}'")
                                return False
                        except Exception as e:
                            print(f"Error evaluating CHECK constraint for '{col}': {e}")
                            return False

            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    def show_help(self):
        print("Help...")