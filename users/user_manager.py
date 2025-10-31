# users/user_manager.py
import json
import os
from utils.helpers import hash_password

class UserManager:
    def __init__(self, db_path):
        self.file = os.path.join(db_path, "users.json")
        self._load()

    def _load(self):
        if os.path.exists(self.file):
            with open(self.file, "r") as f:
                self.users = json.load(f)
        else:
            self.users = {}

    def _save(self):
        with open(self.file, "w") as f:
            json.dump(self.users, f, indent=2)

    def create_user(self, name, pwd, role="user"):
        hashed = hash_password(pwd)
        if name in self.users:
            print(f"User '{name}' exists")
            return
        self.users[name] = {"password": hashed, "role": role}
        self._save()
        print(f"User '{name}' created with role '{role}'")

    def switch_user_to(self, name, pwd):
        hashed = hash_password(pwd)
        user = self.users.get(name)
        if user and user["password"] == hashed:
            return {"username": name, "role": user["role"]}
        return None

    def drop_user(self, name):
        if name not in self.users:
            print(f"User '{name}' not found")
            return
        del self.users[name]
        self._save()
        print(f"User '{name}' deleted")

    def list_users(self):
        if not self.users:
            print("No users")
            return
        for u, d in self.users.items():
            print(f"  - {u} ({d['role']})")
