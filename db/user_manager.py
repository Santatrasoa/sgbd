import os, json
from datetime import datetime
from utils import hash_password

class UserManager:
    def __init__(self, db_path):
        self.user_file_path = f"{db_path}/.users/users.json"
        os.makedirs(f"{db_path}/.users", exist_ok=True)
        if not os.path.exists(self.user_file_path):
            root_user = {
                "username": "root",
                "password": hash_password("root"),
                "role": "admin",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            with open(self.user_file_path, "w") as f:
                json.dump({"users": [root_user]}, f, indent=4)

    def create_user(self, username, password, role="user"):
        with open(self.user_file_path, "r") as f:
            data = json.load(f)

        for u in data["users"]:
            if u["username"] == username:
                print("user already exists")
                return

        new_user = {
            "username": username,
            "password": hash_password(password),
            "role": role,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
        sep = "—" * (max_len + 30)
        print(sep)
        print("   list of users")
        print(sep)
        print(f"{'Username':<{max_len}} | Role | Created_at")
        print(sep)
        for u in users:
            print(f"{u['username']:<{max_len}} | {u['role']} | {u['created_at']}")
        print(sep)

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

    def switch_user_to(self, username, password):
        with open(self.user_file_path, "r") as f:
            data = json.load(f)
        for u in data["users"]:
            if u["username"] == username and u["password"] == hash_password(password):
                print(f"user '{username}' logged in")
                return u
        print("invalid username or password")
        return None
