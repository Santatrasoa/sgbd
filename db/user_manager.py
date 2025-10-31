# db/user_manager.py
from pathlib import Path
from datetime import datetime
from utils.helpers import hash_password

class UserManager:
    def __init__(self, db_path, crypto):
        self.db_path = Path(db_path)
        self.user_file = self.db_path / "users.enc"
        self.crypto = crypto
        self.db_path.mkdir(exist_ok=True)
        self._init_root()

    def _init_root(self):
        if not self.user_file.exists():
            root = {
                "username": "root",
                "password": hash_password("root"),
                "role": "admin",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self._save({"users": [root]})

    def _load(self):
        if not self.user_file.exists():
            return {"users": []}
        return self.crypto.decrypt(self.user_file.read_bytes())

    def _save(self, data):
        self.user_file.write_bytes(self.crypto.encrypt(data))

    def create_user(self, username, password, role="user"):
        data = self._load()
        if any(u["username"] == username for u in data["users"]):
            print(f"User '{username}' already exists")
            return
        new_user = {
            "username": username,
            "password": hash_password(password),
            "role": role,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        data["users"].append(new_user)
        self._save(data)
        print(f"User '{username}' created")

    def list_users(self):
        data = self._load()
        users = data.get("users", [])
        if not users:
            print("No users found")
            return
        max_len = max(len(u["username"]) for u in users)
        sep = "—" * (max_len + 35)
        print(sep)
        print(" LIST OF USERS")
        print(sep)
        print(f"{'Username':<{max_len}} | {'Role':<6} | Created At")
        print(sep)
        for u in users:
            print(f"{u['username']:<{max_len}} | {u['role']:<6} | {u['created_at']}")
        print(sep)

    def drop_user(self, username):
        data = self._load()
        original_count = len(data["users"])
        data["users"] = [u for u in data["users"] if u["username"] != username]
        if len(data["users"]) == original_count:
            print(f"User '{username}' not found")
            return
        self._save(data)
        print(f"User '{username}' removed")

    def switch_user_to(self, username, password):
        data = self._load()
        hashed = hash_password(password)
        for u in data["users"]:
            if u["username"] == username and u["password"] == hashed:
                print(f"Switched to user '{username}'")
                return {"username": username, "role": u["role"]}
        print("Invalid username or password")
        return None