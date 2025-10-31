# commands/table_commands.py
import os
import re
import json
from utils.helpers import validate_table_name, split_top_level_commas
from db.db_main import Db

def check_permission(db: Db, operation, database_name, table_name=None):
    username = db.current_user.get("username")
    role = db.current_user.get("role")
    if role == "admin":
        return True
    op = operation.upper()
    if table_name:
        try:
            return (db.permManager.has_table_permission(database_name, table_name, username, op) or
                    db.permManager.has_db_permission(database_name, username, op))
        except:
            return False
    try:
        return db.permManager.has_db_permission(database_name, username, op)
    except:
        return False

def handle_table_commands(cmd, cmd_line, db, useDatabase, isDbUse, SEPARATOR):
    if not isDbUse:
        print("No database selected")
        print("Use: use_db <nom_base>;")
        return

    if cmd_line == "create_table":
        try:
            if "(" not in cmd or ")" not in cmd:
                print("Syntax error: parenthèses manquantes")
                print("Usage: create_table nom(col1:type[contraintes], ...);")
                return
            name = cmd.split(" ")[1].split("(")[0].strip()
            is_valid, error_msg = validate_table_name(name)
            if not is_valid:
                print(f"Invalid table name: {error_msg}")
                return
            if not check_permission(db, "ALL", useDatabase, name):
                print(f"Permission denied to create table '{name}' (user: {db.current_user['username']})")
                return
            inside = cmd[cmd.find("(") + 1: cmd.rfind(")")].strip()
            columns = split_top_level_commas(inside)
            allType = ["date", "year", "time", "datetime", "bool", "number", "float", "string", "text", "bit"]
            constraints_allowed = {
                "not_null": "Not_null", "unique": "Unique", "primary_key": "Primary_key",
                "foreign_key": "Foreign_key", "check": "Check", "default": "Default",
                "auto_increment": "Auto_increment"
            }
            attr = {}
            constr = {}
            has_error = False
            for val in columns:
                val = val.strip()
                if not val: continue
                if ":" not in val:
                    print(f"Syntax error in '{val}' — expected format: name:type[constraint,...]")
                    has_error = True
                    break
                parts = val.split(":", 1)
                col = parts[0].strip()
                type_and_constraints = parts[1].strip()
                if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col):
                    print(f"Invalid column name: '{col}'")
                    has_error = True
                    break
                if "[" in type_and_constraints and "]" in type_and_constraints:
                    type_part = type_and_constraints.split("[", 1)[0].strip()
                    constraint_part = type_and_constraints[
                        type_and_constraints.find("[") + 1:type_and_constraints.rfind("]")
                    ].strip()
                    raw_constraints = [c.strip() for c in constraint_part.split(",") if c.strip()]
                else:
                    type_part = type_and_constraints.strip()
                    raw_constraints = []
                t = type_part.lower()
                if t not in allType:
                    print(f"Unknown type '{type_part}' for column '{col}'")
                    print(f"Available types: {', '.join(allType)}")
                    has_error = True
                    break
                normalized_constraints = []
                invalid_constraints = []
                for rc in raw_constraints:
                    key = rc.lower().replace(" ", "_").replace("-", "_")
                    if key in constraints_allowed:
                        normalized_constraints.append(constraints_allowed[key])
                    else:
                        invalid_constraints.append(rc)
                if invalid_constraints:
                    print(f"Unknown constraints for '{col}': {', '.join(invalid_constraints)}")
                    print(f"Available constraints: {', '.join(constraints_allowed.keys())}")
                    has_error = True
                    break
                attr[col] = type_part.capitalize() if t != "number" else "Number"
                constr[col] = normalized_constraints if normalized_constraints else ["no constraint"]
            if has_error:
                print("Creation cancelled due to detected errors.")
                return
            table_def = {"caracteristique": attr, "constraint": constr, "data": []}
            db.create_Table(useDatabase, name, table_def)
        except Exception as e:
            print(f"Error creating table: {e}")
            import traceback
            traceback.print_exc()

    elif cmd_line == "add_into_table":
        try:
            getData = " ".join(cmd.split(" ")[1:]).strip().split("(")
            table_name = getData[0].strip()
            values_str = getData[1].replace(")", "").strip()
            values = [v.strip() for v in values_str.split(",")]
            pathToFile = f"{db.dbPath}/{useDatabase}/{table_name}.json"
            if not check_permission(db, "INSERT", useDatabase, table_name):
                print(f"Permission denied to insert into '{table_name}' (user: {db.current_user['username']})")
                return
            db.analyse_data(pathToFile, values)
        except IndexError:
            print("Syntax error")
            print("Usage: add_into_table nom_table(col1=val1, col2=val2, ...);")

    elif cmd_line == "drop_table":
        tableToRemove = cmd[10:].strip()
        if not check_permission(db, "DROP", useDatabase, tableToRemove):
            print(f"Permission denied to drop '{tableToRemove}' (user: {db.current_user['username']})")
            return
        confirm = input(f"Delete table '{tableToRemove}'? (yes/no): ").strip().lower()
        if confirm in ["oui", "yes", "y"]:
            db.drop_table(useDatabase, tableToRemove)
        else:
            print("Operation cancelled")

    elif cmd_line == "list_table":
        current_username = db.current_user.get("username")
        role = db.current_user.get("role")
        if role != "admin" and not db.permManager.user_has_any_permission(useDatabase, current_username):
            print(f"Permission denied to read table in'{useDatabase}' (User: {current_username})")
            return
        path = f"{db.dbPath}/{useDatabase}"
        tables = db.list_table(path)
        if len(tables) == 0:
            print("No tables found in this database")
        else:
            l = max([len(t.replace('.json', '')) for t in tables] + [15])
            print(SEPARATOR * (l + 4))
            print(f"{'In the table ' + useDatabase.upper():^{l + 4}}")
            print(SEPARATOR * (l + 4))
            for t in sorted(tables):
                table_name = t.replace('.json', '')
                print(f" {table_name:<{l}}")
            print(SEPARATOR * (l + 4))
            print(f"Total: {len(tables)} table{'s' if len(tables) > 1 else ''}")

    elif cmd_line == "describe_table":
        table_name = cmd[15:].strip()
        if not check_permission(db, "SELECT", useDatabase, table_name):
            print(f"Permission denied to describe '{table_name}' (user: {db.current_user['username']})")
            return
        pathToFile = f"{db.dbPath}/{useDatabase}/{table_name}.json"
        db.describe_table(pathToFile)
