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

    # commands/table_commands.py
import re
from utils.helpers import validate_table_name, split_top_level_commas

def check_permission(db: Db, operation, database_name, table_name=None):
    username = db.current_user.get("username")
    role = db.current_user.get("role")
    if role == "admin":
        return True
    op = operation.upper()
    if table_name:
        return (db.permManager.has_table_permission(database_name, table_name, username, op) or
                db.permManager.has_db_permission(database_name, username, op))
    return db.permManager.has_db_permission(database_name, username, op)

def handle_table_commands(cmd, cmd_line, db, useDatabase, isDbUse, SEPARATOR, config):
    if not isDbUse:
        print("No database selected")
        print("Use: use_db <nom_base>;")
        return

    # CHARGÉ DEPUIS config.json
    allType = [t.lower() for t in config["allowed_data_types"]]
    constraints_allowed = {k.lower(): v for k, v in config["allowed_constraints"].items()}

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
                print(f"Permission denied to create table '{name}'")
                return

            inside = cmd[cmd.find("(") + 1: cmd.rfind(")")].strip()
            columns = split_top_level_commas(inside)

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
                    print(f"Available types: {', '.join(config['allowed_data_types'])}")
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
                    print(f"Available: {', '.join(config['allowed_constraints'].keys())}")
                    has_error = True
                    break

                # Normalisation du type
                original_type = next((ot for ot in config["allowed_data_types"] if ot.lower() == t), type_part)
                attr[col] = "Number" if t == "number" else original_type.capitalize()
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
        if " " not in cmd:
            print("Usage: add_into_table <table>(col=value, ...);")
            return
        parts = cmd.split(" ", 1)[1].strip()
        if "(" not in parts or ")" not in parts:
            print("Invalid syntax. Use: add_into_table table(col=value, ...);")
            return
        table_part, values_part = parts.split("(", 1)
        table_name = table_part.strip()
        values_str = values_part.rstrip(")").strip()
        if not values_str:
            print("No values provided")
            return
        values = [v.strip() for v in values_str.split(",") if v.strip()]
        if not values:
            print("No valid values")
            return

        # CORRIGÉ : passe db_name, table_name, values
        success = db.analyse_data(useDatabase, table_name, values)
        if success:
            print("Data added successfully")


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

    elif cmd_line in ["list_table", "list_tables"]:
        if not isDbUse:
            print("No database selected")
            return
        tables = db.list_table(useDatabase)  # ← CORRIGÉ
        if not tables:
            print("No tables found")
            return
        max_len = max(len(t) for t in tables)
        sep = SEPARATOR * (max_len + 10)
        print(sep)
        print(f" TABLES IN {useDatabase} ".center(len(sep), " "))
        print(sep)
        for t in sorted(tables):
            print(f" {t}")
        print(sep)
        print(f"Total: {len(tables)} table{'s' if len(tables) > 1 else ''}")
            
    elif cmd_line == "describe_table":
        if " " not in cmd:
            print("Usage: describe_table <name>;")
            return
        table_name = cmd.split(" ", 1)[1].strip()
        if not table_name:
            print("Table name cannot be empty")
            return
        # CORRIGÉ : passe db_name + table_name
        db.describe_table(useDatabase, table_name)