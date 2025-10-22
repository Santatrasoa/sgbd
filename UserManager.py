import json, os, datetime

class UserManager:
    def __init__(self):
        self.user_file_path = ".database/.users/users.json"
        os.makedirs(".database/.users", exist_ok=True)
        if not os.path.exists(self.user_file_path):
            with open(self.user_file_path, "w") as f:
                json.dump({"users": []}, f, indent=4)

    def create_user(self, username, password, role="user"):
        with open(self.user_file_path, "r") as f:
            data = json.load(f)

        for u in data["users"]:
            if u["username"] == username:
                print("user already exists")
                return

        new_user = {
            "username": username,
            "password": password,
            "role": role,
            "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        data["users"].append(new_user)
        with open(self.user_file_path, "w") as f:
            json.dump(data, f, indent=4)
        print(f"user {username} created")

    def list_users(self):
        with open(self.user_file_path, "r") as f:
            data = json.load(f)

        users = data.get("users", [])
        if not users:
            print("no users found")
            return

        max_len = max(len(u["username"]) for u in users)
        print("—" * (max_len + 30))
        print("   list of users")
        print("—" * (max_len + 30))
        print(f"{'Username':<{max_len}} | Role | Created_at")
        print("—" * (max_len + 30))
        for u in users:
            print(f"{u['username']:<{max_len}} | {u['role']} | {u['created_at']}")
        print("—" * (max_len + 30))

    def drop_user(self, username):
        with open(self.user_file_path, "r") as f:
            data = json.load(f)

        new_users = [u for u in data["users"] if u["username"] != username]
        if len(new_users) == len(data["users"]):
            print("user not found")
            return

        data["users"] = new_users
        with open(self.user_file_path, "w") as f:
            json.dump(data, f, indent=4)
        print(f"user {username} removed")

    def use_user(self, username, password):
        with open(self.user_file_path, "r") as f:
            data = json.load(f)
        for u in data["users"]:
            if u["username"] == username and u["password"] == password:
                print(f"user '{username}' logged in")
                return u
        print("invalid username or password")
        return None
def show_help():
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