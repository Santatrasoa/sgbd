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

# commands/table_commands.py - Ajouter cette fonction

def handle_alter_table(cmd, db, useDatabase, config):
    """
    Gère la commande ALTER TABLE
    
    Syntaxes supportées:
    - ALTER TABLE nom ADD COLUMN col:type[contraintes];
    - ALTER TABLE nom DROP COLUMN col;
    - ALTER TABLE nom RENAME COLUMN old_col TO new_col;
    - ALTER TABLE nom MODIFY COLUMN col:new_type[contraintes];
    - ALTER TABLE nom RENAME TO new_name;
    """
    import json
    import re
    from pathlib import Path
    
    DB_PATH = config.get("db_path", ".database")
    
    try:
        # Parser la commande
        parts = cmd.split()
        if len(parts) < 4:
            raise ValueError("Incomplete ALTER TABLE command")
        
        table_name = parts[2]  # ALTER TABLE <nom>
        action = parts[3].upper()  # ADD, DROP, RENAME, MODIFY
        
        # Chemin vers le fichier de la table
        table_path = Path(f"{DB_PATH}/{useDatabase}/{table_name}.json")
        
        if not table_path.exists():
            print(f"Table '{table_name}' does not exist")
            return
        
        # Vérifier les permissions
        current_username = db.current_user.get("username")
        role = db.current_user.get("role")
        
        # ALTER TABLE nécessite la permission ALL ou une permission spéciale
        if role != "admin":
            has_perm = db.permManager.has_table_permission(
                useDatabase, table_name, current_username, "ALL"
            )
            if not has_perm:
                print(f"🚫 Permission denied to alter table '{table_name}' (user: {current_username})")
                return
        
        # Charger la table
        with open(table_path, "r", encoding="utf-8") as f:
            table_data = json.load(f)
        
        caracteristiques = table_data.get("caracteristique", {})
        constraints = table_data.get("constraint", {})
        data = table_data.get("data", [])
        
        # ==========================================
        # ADD COLUMN : Ajouter une colonne
        # ==========================================
        if action == "ADD" and len(parts) > 4 and parts[4].upper() == "COLUMN":
            # ALTER TABLE users ADD COLUMN email:string[not_null];
            column_def = " ".join(parts[5:])
            
            if ":" not in column_def:
                print("Syntax error: expected format col:type[constraints]")
                print("Example: ALTER TABLE users ADD COLUMN email:string[not_null];")
                return
            
            # Parser la définition de colonne
            col_parts = column_def.split(":", 1)
            col_name = col_parts[0].strip()
            type_and_constraints = col_parts[1].strip()
            
            # Valider le nom de colonne
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col_name):
                print(f"Invalid column name: '{col_name}'")
                return
            
            # Vérifier que la colonne n'existe pas déjà
            if col_name in caracteristiques:
                print(f"Column '{col_name}' already exists")
                return
            
            # Extraire type et contraintes
            if "[" in type_and_constraints and "]" in type_and_constraints:
                type_part = type_and_constraints.split("[", 1)[0].strip()
                constraint_part = type_and_constraints[
                    type_and_constraints.find("[") + 1:type_and_constraints.rfind("]")
                ].strip()
                raw_constraints = [c.strip() for c in constraint_part.split(",") if c.strip()]
            else:
                type_part = type_and_constraints.strip()
                raw_constraints = []
            
            # Valider le type
            all_types = ["date", "year", "time", "datetime", "bool", "number", "float", "string", "text", "bit"]
            if type_part.lower() not in all_types:
                print(f"Unknown type '{type_part}'")
                print(f"Available types: {', '.join(all_types)}")
                return
            
            # Normaliser les contraintes
            constraints_allowed = {
                "not_null": "Not_null",
                "unique": "Unique",
                "primary_key": "Primary_key",
                "foreign_key": "Foreign_key",
                "check": "Check",
                "default": "Default",
                "auto_increment": "Auto_increment"
            }
            
            normalized_constraints = []
            for rc in raw_constraints:
                key = rc.lower().replace(" ", "_").replace("-", "_")
                if key in constraints_allowed:
                    normalized_constraints.append(constraints_allowed[key])
                else:
                    print(f"⚠️ Unknown constraint: {rc}")
            
            # Ajouter la colonne
            caracteristiques[col_name] = type_part.capitalize() if type_part.lower() != "number" else "Number"
            constraints[col_name] = normalized_constraints if normalized_constraints else ["no constraint"]
            
            # Ajouter une valeur par défaut NULL pour toutes les lignes existantes
            for row in data:
                row[col_name] = None
            
            print(f"✓ Column '{col_name}' added to table '{table_name}'")
        
        # ==========================================
        # DROP COLUMN : Supprimer une colonne
        # ==========================================
        elif action == "DROP" and len(parts) > 4 and parts[4].upper() == "COLUMN":
            # ALTER TABLE users DROP COLUMN email;
            col_name = parts[5] if len(parts) > 5 else ""
            
            if not col_name:
                print("Column name required")
                print("Example: ALTER TABLE users DROP COLUMN email;")
                return
            
            if col_name not in caracteristiques:
                print(f"Column '{col_name}' does not exist")
                return
            
            # Vérifier si c'est une clé primaire
            col_constraints = constraints.get(col_name, [])
            if "Primary_key" in col_constraints or "primary_key" in [c.lower() for c in col_constraints]:
                confirm = input(f"⚠️ '{col_name}' is a PRIMARY KEY. Continue? (yes/no): ").lower()
                if confirm not in ["yes", "y"]:
                    print("Operation cancelled")
                    return
            
            # Supprimer la colonne
            del caracteristiques[col_name]
            if col_name in constraints:
                del constraints[col_name]
            
            # Supprimer la colonne de toutes les lignes
            for row in data:
                if col_name in row:
                    del row[col_name]
            
            print(f"✓ Column '{col_name}' dropped from table '{table_name}'")
        
        # ==========================================
        # RENAME COLUMN : Renommer une colonne
        # ==========================================
        elif action == "RENAME" and len(parts) > 4 and parts[4].upper() == "COLUMN":
            # ALTER TABLE users RENAME COLUMN old_name TO new_name;
            if len(parts) < 7 or parts[6].upper() != "TO":
                print("Syntax error")
                print("Example: ALTER TABLE users RENAME COLUMN old_name TO new_name;")
                return
            
            old_name = parts[5]
            new_name = parts[7]
            
            if old_name not in caracteristiques:
                print(f"Column '{old_name}' does not exist")
                return
            
            if new_name in caracteristiques:
                print(f"Column '{new_name}' already exists")
                return
            
            # Valider le nouveau nom
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', new_name):
                print(f"Invalid column name: '{new_name}'")
                return
            
            # Renommer dans caracteristiques
            caracteristiques[new_name] = caracteristiques.pop(old_name)
            
            # Renommer dans constraints
            if old_name in constraints:
                constraints[new_name] = constraints.pop(old_name)
            
            # Renommer dans les données
            for row in data:
                if old_name in row:
                    row[new_name] = row.pop(old_name)
            
            print(f"✓ Column '{old_name}' renamed to '{new_name}'")
        
        # ==========================================
        # MODIFY COLUMN : Modifier le type d'une colonne
        # ==========================================
        elif action == "MODIFY" and len(parts) > 4 and parts[4].upper() == "COLUMN":
            # ALTER TABLE users MODIFY COLUMN age:number[not_null];
            column_def = " ".join(parts[5:])
            
            if ":" not in column_def:
                print("Syntax error: expected format col:new_type[constraints]")
                print("Example: ALTER TABLE users MODIFY COLUMN age:number[not_null];")
                return
            
            # Parser la définition
            col_parts = column_def.split(":", 1)
            col_name = col_parts[0].strip()
            type_and_constraints = col_parts[1].strip()
            
            if col_name not in caracteristiques:
                print(f"Column '{col_name}' does not exist")
                return
            
            # Extraire type et contraintes
            if "[" in type_and_constraints and "]" in type_and_constraints:
                type_part = type_and_constraints.split("[", 1)[0].strip()
                constraint_part = type_and_constraints[
                    type_and_constraints.find("[") + 1:type_and_constraints.rfind("]")
                ].strip()
                raw_constraints = [c.strip() for c in constraint_part.split(",") if c.strip()]
            else:
                type_part = type_and_constraints.strip()
                raw_constraints = []
            
            # Valider le type
            all_types = ["date", "year", "time", "datetime", "bool", "number", "float", "string", "text", "bit"]
            if type_part.lower() not in all_types:
                print(f"Unknown type '{type_part}'")
                return
            
            # Normaliser les contraintes
            constraints_allowed = {
                "not_null": "Not_null",
                "unique": "Unique",
                "primary_key": "Primary_key",
                "foreign_key": "Foreign_key",
                "check": "Check",
                "default": "Default",
                "auto_increment": "Auto_increment"
            }
            
            normalized_constraints = []
            for rc in raw_constraints:
                key = rc.lower().replace(" ", "_").replace("-", "_")
                if key in constraints_allowed:
                    normalized_constraints.append(constraints_allowed[key])
            
            # Avertissement sur le changement de type
            old_type = caracteristiques[col_name]
            if old_type.lower() != type_part.lower():
                print(f"⚠️ Warning: Changing type from {old_type} to {type_part}")
                print("   Existing data may become incompatible")
                confirm = input("Continue? (yes/no): ").lower()
                if confirm not in ["yes", "y"]:
                    print("Operation cancelled")
                    return
            
            # Modifier le type et les contraintes
            caracteristiques[col_name] = type_part.capitalize() if type_part.lower() != "number" else "Number"
            constraints[col_name] = normalized_constraints if normalized_constraints else ["no constraint"]
            
            print(f"✓ Column '{col_name}' modified")
        
        # ==========================================
        # RENAME TO : Renommer la table
        # ==========================================
        elif action == "RENAME" and len(parts) > 4 and parts[4].upper() == "TO":
            # ALTER TABLE users RENAME TO customers;
            new_table_name = parts[5]
            
            # Valider le nouveau nom
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', new_table_name):
                print(f"Invalid table name: '{new_table_name}'")
                return
            
            new_table_path = Path(f"{DB_PATH}/{useDatabase}/{new_table_name}.json")
            if new_table_path.exists():
                print(f"Table '{new_table_name}' already exists")
                return
            
            # Sauvegarder avec le nouveau nom
            table_data["caracteristique"] = caracteristiques
            table_data["constraint"] = constraints
            table_data["data"] = data
            
            with open(new_table_path, "w", encoding="utf-8") as f:
                json.dump(table_data, f, indent=2, ensure_ascii=False)
            
            # Supprimer l'ancien fichier
            table_path.unlink()
            
            # Mettre à jour les permissions (copier les permissions de l'ancienne table)
            # Note: cela nécessiterait d'étendre permission_manager
            
            print(f"✓ Table '{table_name}' renamed to '{new_table_name}'")
            return  # Pas besoin de sauvegarder car on a déjà écrit le nouveau fichier
        
        else:
            print("Unknown ALTER TABLE action")
            print("Supported actions:")
            print("  ALTER TABLE <name> ADD COLUMN <col:type[constraints]>;")
            print("  ALTER TABLE <name> DROP COLUMN <col>;")
            print("  ALTER TABLE <name> RENAME COLUMN <old> TO <new>;")
            print("  ALTER TABLE <name> MODIFY COLUMN <col:type[constraints]>;")
            print("  ALTER TABLE <name> RENAME TO <new_name>;")
            return
        
        # Sauvegarder les modifications (sauf pour RENAME TO qui sauvegarde séparément)
        table_data["caracteristique"] = caracteristiques
        table_data["constraint"] = constraints
        table_data["data"] = data
        
        with open(table_path, "w", encoding="utf-8") as f:
            json.dump(table_data, f, indent=2, ensure_ascii=False)
        
    except ValueError as e:
        print(f"Syntax error: {e}")
        print("Usage: ALTER TABLE <name> <action> ...;")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()