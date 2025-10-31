# commands/query_commands.py
import os
import json
from utils.helpers import parse_where_clause

def handle_query_commands(cmd, cmd_line, db, useDatabase, isDbUse, SEPARATOR):
    if not isDbUse:
        print("No database selected")
        print("Use: use_db <nom_base>;")
        return

    # === SELECT ===
    if cmd_line == "select":
        getRequests = " ".join(cmd.split(" ")[1:]).strip()
        if not getRequests:
            print("Syntax error")
            print("Usage: select <columns> from <table> [where <condition>];")
            return

        parts = getRequests.split()
        if len(parts) < 3 or parts[1].lower() != "from":
            print("Syntax error: missing FROM")
            return

        columns_part = parts[0]
        table_name = parts[2]
        where_clause = None
        if "where" in [p.lower() for p in parts]:
            where_index = [p.lower() for p in parts].index("where")
            if len(parts) > where_index + 1:
                where_clause = " ".join(parts[where_index + 1:])

        # Vérification permission
        if not db.permManager.has_table_permission(useDatabase, table_name, db.current_user["username"], "SELECT"):
            print(f"Permission denied to read '{table_name}'")
            return

        # Lecture chiffrée
        path = db._get_table_path(useDatabase, table_name)
        if not path.exists():
            print(f"Table '{table_name}' does not exist")
            return

        try:
            content = db.crypto.decrypt(path.read_bytes())
            all_rows = content.get("data", [])
            all_columns = list(content.get("caracteristique", {}).keys())

            # Normalisation
            normalized_rows = []
            for row in all_rows:
                clean_row = {k.strip(): str(v).strip().strip('"') for k, v in row.items()}
                normalized_rows.append(clean_row)
            all_rows = normalized_rows

            # Colonnes
            if columns_part == "*":
                selected_columns = all_columns
            else:
                selected_columns = [c.strip() for c in columns_part.split(",")]
                invalid_cols = [c for c in selected_columns if c not in all_columns]
                if invalid_cols:
                    print(f"Unknown columns: {', '.join(invalid_cols)}")
                    print(f"Available: {', '.join(all_columns)}")
                    return

            # WHERE
            filtered_rows = all_rows
            if where_clause:
                filtered_rows = parse_where_clause(where_clause, all_rows)

            if not filtered_rows:
                print("No data found")
                return

            # Affichage
            col_widths = {
                col: max(len(col), max(len(str(row.get(col, ""))) for row in filtered_rows))
                for col in selected_columns
            }
            total_width = sum(col_widths.values()) + len(selected_columns) * 3 + 1
            print(SEPARATOR * total_width)
            print(" | ".join(col.ljust(col_widths[col]) for col in selected_columns))
            print(SEPARATOR * total_width)
            for row in filtered_rows:
                print(" | ".join(str(row.get(col, "")).ljust(col_widths[col]) for col in selected_columns))
            print(SEPARATOR * total_width)
            print(f"({len(filtered_rows)} row{'s' if len(filtered_rows) > 1 else ''} returned)")
            print(SEPARATOR * total_width)

        except Exception as e:
            print(f"Error reading table: {e}")

    # === UPDATE ===
    elif cmd_line == "update":
        try:
            parts = cmd.split()
            if len(parts) < 4 or parts[2].lower() != "set":
                raise ValueError("Syntaxe invalide")
            table_name = parts[1]

            if not db.permManager.has_table_permission(useDatabase, table_name, db.current_user["username"], "UPDATE"):
                print(f"Permission denied for updating '{table_name}'")
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
                assignments[col.strip()] = val.strip().strip("'\"")

            path = db._get_table_path(useDatabase, table_name)
            if not path.exists():
                print(f"Table '{table_name}' does not exist")
                return

            content = db.crypto.decrypt(path.read_bytes())
            all_rows = content.get("data", [])
            normalized_rows = [{k.strip(): str(v).strip().strip('"') for k, v in row.items()} for row in all_rows]

            if where_clause:
                rows_to_update = parse_where_clause(where_clause, normalized_rows)
            else:
                confirm = input(f"Update all rows in '{table_name}'? (yes/no): ").lower()
                if confirm not in ["yes", "y", "oui"]:
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
            path.write_bytes(db.crypto.encrypt(content))
            print(f"{updated_count} row{'s' if updated_count > 1 else ''} updated")

        except ValueError as e:
            print(f"Syntax error: {e}")
            print("Usage: update <table> set col=val [where ...];")
        except Exception as e:
            print(f"Error: {e}")

    # === DELETE ===
    elif cmd_line == "delete":
        try:
            parts = cmd.split()
            if len(parts) < 3 or parts[1].lower() != "from":
                raise ValueError("Syntaxe invalide")
            table_name = parts[2]

            if not db.permManager.has_table_permission(useDatabase, table_name, db.current_user["username"], "DELETE"):
                print(f"Permission denied for deleting from '{table_name}'")
                return

            where_clause = None
            if "where" in [p.lower() for p in parts]:
                where_index = [p.lower() for p in parts].index("where")
                if len(parts) > where_index + 1:
                    where_clause = " ".join(parts[where_index + 1:])
                else:
                    raise ValueError("WHERE condition missing")
            else:
                confirm = input(f"Delete all rows from '{table_name}'? (yes/no): ").lower()
                if confirm not in ["yes", "y", "oui"]:
                    print("Operation aborted")
                    return

            path = db._get_table_path(useDatabase, table_name)
            if not path.exists():
                print(f"Table '{table_name}' does not exist")
                return

            content = db.crypto.decrypt(path.read_bytes())
            all_rows = content.get("data", [])
            normalized_rows = [{k.strip(): str(v).strip().strip('"') for k, v in row.items()} for row in all_rows]

            if where_clause:
                rows_to_delete = parse_where_clause(where_clause, normalized_rows)
                remaining_rows = [row for row in normalized_rows if row not in rows_to_delete]
            else:
                rows_to_delete = normalized_rows
                remaining_rows = []

            content["data"] = remaining_rows
            path.write_bytes(db.crypto.encrypt(content))
            print(f"{len(rows_to_delete)} row{'s' if len(rows_to_delete) > 1 else ''} deleted")

        except ValueError as e:
            print(f"Syntax error: {e}")
            print("Usage: delete from <table> [where ...];")
        except Exception as e:
            print(f"Error: {e}")