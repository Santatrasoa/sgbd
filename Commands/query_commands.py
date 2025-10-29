"""
Commandes de requêtes SQL (SELECT, UPDATE, DELETE)
"""

import os
import json
from utils import check_permission, parse_where_clause


def handle_query_commands(cmd, cmd_line, session):
    """
    Gère les commandes de requêtes SQL
    
    Args:
        cmd: Commande complète
        cmd_line: Premier mot de la commande
        session: Dictionnaire de session
    """
    db = session['db']
    DB_PATH = session['DB_PATH']
    SEPARATOR = session['SEPARATOR']
    useDatabase = session['useDatabase']
    isDbUse = session['isDbUse']
    
    # SELECT
    if cmd_line == "select":
        if not isDbUse:
            print("❌ No database selected")
            print("Use: use_db <database_name>;")
            return
        
        getRequests = " ".join(cmd.split(" ")[1:]).strip()
        
        if len(getRequests) == 0:
            print("❌ Syntax error")
            print("Usage: select <columns> from <table> [where <condition>];")
            return
        
        parts = getRequests.split()
        
        if len(parts) >= 3 and parts[1].lower() == "from":
            columns_part = parts[0]
            table_name = parts[2]
            
            if not check_permission(db, "SELECT", useDatabase, table_name):
                current_username = db.current_user.get("username")
                print(f"❌ Permission denied to read '{table_name}' (user: {current_username})")
                return
            
            where_clause = None
            if "where" in [p.lower() for p in parts]:
                where_index = [p.lower() for p in parts].index("where")
                if len(parts) > where_index + 1:
                    where_clause = " ".join(parts[where_index + 1:])
            
            path = f"{DB_PATH}/{useDatabase}/{table_name}.json"
            
            if not os.path.exists(path):
                print(f"❌ Table '{table_name}' does not exist")
                return
            
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = json.load(f)
                
                all_rows = content.get("data", [])
                all_columns = list(content.get("caracteristique", {}).keys())
                
                normalized_rows = []
                for row in all_rows:
                    clean_row = {}
                    for k, v in row.items():
                        clean_row[k.strip()] = str(v).strip().strip('"')
                    normalized_rows.append(clean_row)
                
                if columns_part == "*":
                    selected_columns = all_columns
                else:
                    selected_columns = [c.strip() for c in columns_part.split(",")]
                    invalid_cols = [c for c in selected_columns if c not in all_columns]
                    if invalid_cols:
                        print(f"❌ Unknown columns: {', '.join(invalid_cols)}")
                        print(f"Available columns: {', '.join(all_columns)}")
                        return
                
                filtered_rows = normalized_rows
                if where_clause:
                    filtered_rows = parse_where_clause(where_clause, normalized_rows)
                
                if len(filtered_rows) == 0:
                    print("📭 No data found")
                else:
                    col_widths = {
                        col: max(len(col), max((len(str(row.get(col, ""))) for row in filtered_rows), default=0))
                        for col in selected_columns
                    }
                    total_width = sum(col_widths.values()) + (len(selected_columns) * 3) + 1
                    
                    print(SEPARATOR * total_width)
                    print(" | ".join(col.ljust(col_widths[col]) for col in selected_columns))
                    print(SEPARATOR * total_width)
                    
                    for row in filtered_rows:
                        print(" | ".join(str(row.get(col, "")).ljust(col_widths[col]) for col in selected_columns))
                    
                    print(SEPARATOR * total_width)
                    print(f"({len(filtered_rows)} row{'s' if len(filtered_rows) > 1 else ''} returned)")
                    
            except json.JSONDecodeError:
                print(f"❌ Error: corrupted JSON file for table '{table_name}'")
            except Exception as e:
                print(f"❌ Error reading table: {e}")
        else:
            print("❌ Syntax error")
            print("Usage: select <columns> from <table> [where <condition>];")
    
    # UPDATE
    elif cmd_line == "update":
        if not isDbUse:
            print("❌ No database selected")
            print("Use: use_db <database_name>;")
            return
        
        try:
            parts = cmd.split()
            
            if len(parts) < 4 or parts[2].lower() != "set":
                raise ValueError("Invalid syntax")
            
            table_name = parts[1]
            
            if not check_permission(db, "UPDATE", useDatabase, table_name):
                current_username = db.current_user.get("username")
                print(f"❌ Permission denied to update '{table_name}' (User: {current_username})")
                return
            
            set_index = [p.lower() for p in parts].index("set")
            where_index = [p.lower() for p in parts].index("where") if "where" in [p.lower() for p in parts] else None
            
            if where_index:
                set_part = " ".join(parts[set_index + 1:where_index])
                where_clause = " ".join(parts[where_index + 1:])
            else:
                set_part = " ".join(parts[set_index + 1:])
                where_clause = None
            
            assignments = {}
            for assign in set_part.split(","):
                if "=" not in assign:
                    raise ValueError(f"Invalid assignment: {assign}")
                col, val = assign.split("=", 1)
                col = col.strip()
                val = val.strip().strip("'").strip('"')
                assignments[col] = val
            
            path = f"{DB_PATH}/{useDatabase}/{table_name}.json"
            if not os.path.exists(path):
                print(f"❌ Table '{table_name}' doesn't exist")
                return
            
            with open(path, "r", encoding="utf-8") as f:
                content = json.load(f)
            
            all_rows = content.get("data", [])
            
            normalized_rows = []
            for row in all_rows:
                clean_row = {}
                for k, v in row.items():
                    clean_row[k.strip()] = str(v).strip().strip('"')
                normalized_rows.append(clean_row)
            
            if where_clause:
                rows_to_update = parse_where_clause(where_clause, normalized_rows)
            else:
                confirm = input(f"⚠️  Update all rows in '{table_name}'? (yes/no): ").strip().lower()
                if confirm not in ["yes", "y"]:
                    print("Operation aborted")
                    return
                rows_to_update = normalized_rows
            
            updated_count = 0
            for row in normalized_rows:
                if row in rows_to_update:
                    for col, val in assignments.items():
                        if col in row:
                            row[col] = val
                    updated_count += 1
            
            content["data"] = normalized_rows
            with open(path, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
            
            print(f"✓ {updated_count} row{'s' if updated_count > 1 else ''} updated")
            
        except ValueError as e:
            print(f"❌ Syntax error: {e}")
            print("Usage: update <table> set col1=val1, col2=val2 [where condition];")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # DELETE
    elif cmd_line == "delete":
        if not isDbUse:
            print("❌ No database selected")
            print("Use: use_db <database_name>;")
            return
        
        try:
            parts = cmd.split()
            
            if len(parts) < 3 or parts[1].lower() != "from":
                raise ValueError("Invalid syntax")
            
            table_name = parts[2]
            
            if not check_permission(db, "DELETE", useDatabase, table_name):
                current_username = db.current_user.get("username")
                print(f"❌ Permission denied to delete from '{table_name}' (User: {current_username})")
                return
            
            where_clause = None
            if "where" in [p.lower() for p in parts]:
                where_index = [p.lower() for p in parts].index("where")
                if len(parts) > where_index + 1:
                    where_clause = " ".join(parts[where_index + 1:])
                else:
                    raise ValueError("WHERE condition missing")
            else:
                confirm = input(f"⚠️  Delete all rows in '{table_name}'? (yes/no): ").strip().lower()
                if confirm not in ["yes", "y"]:
                    print("Operation aborted")
                    return
            
            path = f"{DB_PATH}/{useDatabase}/{table_name}.json"
            if not os.path.exists(path):
                print(f"❌ Table '{table_name}' doesn't exist")
                return
            
            with open(path, "r", encoding="utf-8") as f:
                content = json.load(f)
            
            all_rows = content.get("data", [])
            
            normalized_rows = []
            for row in all_rows:
                clean_row = {}
                for k, v in row.items():
                    clean_row[k.strip()] = str(v).strip().strip('"')
                normalized_rows.append(clean_row)
            
            if where_clause:
                rows_to_delete = parse_where_clause(where_clause, normalized_rows)
                remaining_rows = [row for row in normalized_rows if row not in rows_to_delete]
            else:
                rows_to_delete = normalized_rows
                remaining_rows = []
            
            content["data"] = remaining_rows
            with open(path, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
            
            print(f"✓ {len(rows_to_delete)} row{'s' if len(rows_to_delete) > 1 else ''} deleted")
            
        except ValueError as e:
            print(f"❌ Syntax error: {e}")
            print("Usage: delete from <table> [where condition];")
        except Exception as e:
            print(f"❌ Error: {e}")