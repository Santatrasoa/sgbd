import os, shutil, json
from pathlib import Path
from .user_manager import UserManager
from .permission_manager import PermissionManager

class Db:
    def __init__(self):
        self.dbName = ""
        self.dbPath = ".database"
        self.userManager = UserManager(self.dbPath)
        self.permManager = PermissionManager(self.dbPath)
        self.current_user = {"username": "root", "role": "admin"}

    def create_DB(self, dbName):
        path = f".database/{dbName}"
        if Path(path).exists():
            print("database already exists")
        else:
            os.makedirs(path)
            print(f"database {dbName} created")
            # when creating a DB, set the creator as owner and give them ALL
            self.permManager.set_owner(dbName, self.current_user["username"])
            self.permManager.grant(dbName, "*", self.current_user["username"], "ALL", caller_username=self.current_user.get("username"), caller_role=self.current_user.get("role"))

    def list_database(self, path):
        directory = Path(path)
        return [item.name for item in directory.iterdir() if item.is_dir() and not item.name.startswith(".")]

    def drop_database(self, databaseName):
        path = Path(f".database/{databaseName}")
        if path.exists() and path.is_dir():
            shutil.rmtree(path)
            print(f"database {databaseName} removed")
        else:
            print("Database does not exist")

    def show_databases(self):
        allDirs = self.list_database(".database/")
        if allDirs:
            l = max([len(d) for d in allDirs] + [8])
            print("—" * (l*2))
            print(f"{'database':^{l*2}}")
            print("—" * (l*2))
            for i in allDirs:
                print(f"{i:^{l*2}}")
            print("—" * (l*2))
        else:
            print("empty :(")

    # -----------------------------
    # TABLES
    # -----------------------------
    def list_table(self, path):
        directory = Path(path)
        return [item.name for item in directory.iterdir() if item.is_file() and not item.name.startswith(".")]

    def create_Table(self, dbName, name ,attribute):
        path = Path(f".database/{dbName}/{name}.json")
        if path.exists():
            print(f"Table {name} already exists")
        else:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(attribute, f, indent=4)
            # table creator becomes owner at table-level by granting ALL to them
            # owner for database remains the same; permission manager treats db owner specially
            self.permManager.grant(dbName, name, self.current_user["username"], "ALL", caller_username=self.current_user.get("username"), caller_role=self.current_user.get("role"))
            print(f"Table {name} created")

    def drop_table(self, dbName, tableName):
        path = Path(f".database/{dbName}/{tableName}.json")
        if path.exists():
            path.unlink()
            print(f"table {tableName} removed")
        else:
            print(f"table {tableName} does not exist")

    def analyse_data(self, path, data):
        if not os.path.exists(path):
            print("Table does not exist")
            return
        with open(path, "r", encoding="utf-8") as f:
            content = json.load(f)
        addedData = {}
        for i, key in enumerate(content["caracteristique"]):
            try:
                k, v = data[i].split("=")
                addedData[k.strip()] = v.strip()
            except:
                print("Syntax Error")
                return
        content["data"].append(addedData)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=4)
        print("Data added")

    def describe_table(self, path):
        if not os.path.exists(path):
            print("Table does not exist")
            return
        with open(path, "r", encoding="utf-8") as f:
            content = json.load(f)
        max_len = max(len(k) for k in content["caracteristique"])
        print("—" * (max_len*2))
        print(f"{'Table description':^{max_len*2}}")
        print("—" * (max_len*2))
        for k, v in content["caracteristique"].items():
            constraint = content.get("constraint", {}).get(k, "None")
            print(f"{k:<{max_len}} : {v} | Constraint: {constraint}")
        print("—" * (max_len*2))

    # -----------------------------
    # HELP
    # -----------------------------
    def show_help(self):
        print("—" * 60)
        print(f"{'COMMANDES DISPONIBLES':^60}")
        print("—" * 60)
        print("\n# DATABASE")
        print(" create_database <name>       : Créer une nouvelle base de données")
        print(" create_db <name>             : Alias pour create_database")
        print(" drop_database <name>         : Supprimer une base de données")
        print(" drop_db <name>               : Alias pour drop_database")
        print(" use_database <name>          : Utiliser une base de données")
        print(" use_db <name>                : Alias pour use_database")
        print(" leave_database               : Quitter la base de données actuelle")
        print(" leave_db                     : Alias pour leave_database")
        print(" list_database                : Lister toutes les bases de données")
        print(" list_db                      : Alias pour list_database")

        print("\n# TABLES")
        print(" create_table <name>(col:type[constraint], ...) : Créer une table")
        print(" add_into_table <table>(col=value, ...)         : Ajouter des données")
        print(" drop_table <name>                             : Supprimer une table")
        print(" list_table                                    : Lister les tables de la BD utilisée")
        print(" describe_table <table>                        : Décrire la table et ses colonnes")

        print("\n# UTILISATEURS")
        print(" create_user <name> password=<pwd> [role=<role>] : Créer un utilisateur")
        print(" list_user                                        : Lister tous les utilisateurs")
        print(" drop_user <name>                                 : Supprimer un utilisateur")
        print(" use_user <name> password=<pwd>                  : Se connecter comme utilisateur")

        print("\n# PERMISSIONS")
        print(" grant <permission> on <table|*> to <user>      : Donner un droit")
        print(" revoke <permission> on <table|*> from <user>   : Retirer un droit")
        print(" show_grants <user>                              : Montrer les droits d'un utilisateur")

        print("\n# AUTRES")
        print(" clear                                           : Nettoyer l'écran")
        print(" exit                                            : Quitter le SGBD")
        print("—" * 60)
