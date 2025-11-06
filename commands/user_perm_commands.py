# commands/user_perm_commands.py
import getpass
from utils.config_loader import load_config

config = load_config()
ALL_PERMISSION = config.get("permissions", [
    "SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "ALL", "USAGE", "READ"
])

def handle_user_perm_commands(cmd, cmd_line, db, useDatabase, isDbUse, DEFAULT_PROMPT):
    """
    Gère les commandes utilisateurs et permissions
    
    Returns:
        tuple: (userUsingDb, promptContainte, useDatabase, isDbUse) ou None
    """
    
    # ========================================
    # CREATE USER - Avec getpass sécurisé
    # ========================================
    if cmd_line == "create_user":
        try:
            parts = cmd.split()
            if len(parts) < 2:
                print("Username required")
                print("Usage: create_user <username> [role=user|admin];")
                return None

            username = parts[1]
            
            # Vérifier si password= est dans la commande (ancien mode)
            pwd_part = [p for p in parts if p.startswith("password=")]
            role_part = [p for p in parts if p.startswith("role=")]

            # Mode sécurisé : demander le mot de passe avec getpass
            if not pwd_part:
                print(f"Creating user '{username}'")
                password = getpass.getpass("Enter password: ")
                password_confirm = getpass.getpass("Confirm password: ")
                
                if password != password_confirm:
                    print("Passwords do not match")
                    return None
                
                if len(password) < 4:
                    print("Password must be at least 4 characters")
                    return None
            else:
                # Mode ancien (déconseillé)
                password = pwd_part[0].split("=", 1)[1]
                print("⚠️ Warning: Password visible in command. Recommended: create_user <username> [role=x];")

            role = role_part[0].split("=", 1)[1].lower() if role_part else "user"

            if role not in ["user", "admin"]:
                print("Invalid role. Use 'user' or 'admin'")
                return None

            # Créer l'utilisateur (le hash est fait dans userManager)
            db.userManager.create_user(username, password, role)
            print(f"✓ User '{username}' created with role '{role}'")

        except Exception as e:
            print("Usage: create_user <username> [role=user|admin];")
            print("       (password will be requested securely)")
            print(f"Error: {e}")

        return None

    # ========================================
    # LIST USER
    # ========================================
    elif cmd_line == "list_user":
        db.userManager.list_users()
        return None

    # ========================================
    # DROP USER
    # ========================================
    elif cmd_line == "drop_user":
        try:
            parts = cmd.split()
            if len(parts) < 2:
                print("Username required")
                print("Usage: drop_user <username>;")
                return None
            
            username = parts[1]
            
            if username == db.current_user["username"]:
                print("Cannot delete current user")
                print("Switch to another user first")
                return None
            
            confirm = input(f"⚠️ Delete user '{username}'? (yes/no): ").lower()
            if confirm in ["yes", "y", "oui"]:
                db.userManager.drop_user(username)
                print(f"✓ User '{username}' deleted")
            else:
                print("Operation cancelled")
                
        except Exception as e:
            print(f"Error: {e}")

        return None

    # ========================================
    # GRANT - Accorder des permissions (MULTIPLE)
    # ========================================
    elif cmd_line == "grant":
        try:
            parts = cmd.split()
            
            if len(parts) < 5:
                raise ValueError("Incomplete command")
            
            # Trouver les indices des mots-clés
            on_idx = parts.index("on")
            to_idx = parts.index("to")
            
            # Extraire les permissions (tout entre grant et on)
            perm_str = " ".join(parts[1:on_idx])
            target = parts[on_idx + 1]
            username = parts[to_idx + 1]
            
            # Parser les permissions multiples (séparées par des virgules)
            raw_permissions = [p.strip().upper() for p in perm_str.split(",")]
            
            # Valider toutes les permissions
            invalid_perms = [p for p in raw_permissions if p not in ALL_PERMISSION]
            if invalid_perms:
                print(f"Invalid permission(s): {', '.join(invalid_perms)}")
                print(f"Available permissions: {', '.join(ALL_PERMISSION)}")
                return None
            
            # Déterminer la base et la table
            if "." in target:
                db_name, table_name = target.split(".", 1)
            else:
                db_name = useDatabase
                table_name = target
            
            if not db_name:
                print("No database selected and no database qualified")
                print("Use: grant <perm> on <db.table> to <user>;")
                return None
            
            # Accorder chaque permission
            granted_perms = []
            failed_perms = []
            
            for perm in raw_permissions:
                try:
                    success = db.permManager.grant(
                        db_name, table_name, username, perm,
                        db.current_user["username"], 
                        db.current_user["role"]
                    )
                    if success or success is None:  # None = pas de retour explicite
                        granted_perms.append(perm)
                    else:
                        failed_perms.append(perm)
                except Exception as e:
                    print(f"⚠️ Failed to grant {perm}: {e}")
                    failed_perms.append(perm)
            
            # Afficher le résumé
            if granted_perms:
                perm_list = ", ".join(granted_perms)
                print(f"✓ Granted {perm_list} on {db_name}.{table_name} to {username}")
            
            if failed_perms:
                perm_list = ", ".join(failed_perms)
                print(f"Failed to grant: {perm_list}")
            
        except ValueError as e:
            if "not in list" in str(e):
                print("Syntax error: missing 'on' or 'to' keyword")
            print("Usage: grant <permission[,permission,...]> on <table|db.table|*> to <user>;")
            print("Examples:")
            print("  grant SELECT on users to alice;")
            print("  grant SELECT, INSERT, UPDATE on users to alice;")
        except Exception as e:
            print(f"Error: {e}")
            print("Usage: grant <permission[,permission,...]> on <table|db.table|*> to <user>;")

        return None

    # ========================================
    # REVOKE - Révoquer des permissions
    # ========================================
    elif cmd_line == "revoke":
        try:
            parts = cmd.split()
            
            if len(parts) < 5:
                raise ValueError("Incomplete command")
            
            perm = parts[1].upper()
            
            # Vérifier que la permission existe
            if perm not in ALL_PERMISSION:
                print(f"Invalid permission '{perm}'")
                print(f"Available permissions: {', '.join(ALL_PERMISSION)}")
                return None
            
            # Parser la commande
            on_idx = parts.index("on")
            from_idx = parts.index("from")
            target = parts[on_idx + 1]
            username = parts[from_idx + 1]
            
            # Déterminer la base et la table
            if "." in target:
                db_name, table_name = target.split(".", 1)
            else:
                db_name = useDatabase
                table_name = target
            
            if not db_name:
                print("No database selected and no database qualified")
                print("Use: revoke <perm> on <db.table> from <user>;")
                return None
            
            # Révoquer la permission
            db.permManager.revoke(
                db_name, table_name, username, perm,
                db.current_user["username"],
                db.current_user["role"]
            )
            
        except ValueError as e:
            if "not in list" in str(e):
                print("Syntax error: missing 'on' or 'from' keyword")
            print("Usage: revoke <permission> on <table|db.table|*> from <user>;")
            print("Example: revoke SELECT on users from alice;")
        except Exception as e:
            print(f"Error: {e}")
            print("Usage: revoke <permission> on <table|db.table|*> from <user>;")

        return None

    # ========================================
    # SHOW GRANTS - Afficher les permissions
    # ========================================
    elif cmd_line == "show_grants":
        try:
            parts = cmd.split()
            
            if len(parts) == 2:
                # show_grants <user>
                username = parts[1]
                db_name = useDatabase
            elif len(parts) == 3:
                # show_grants <db> <user>
                db_name = parts[1]
                username = parts[2]
            else:
                raise ValueError("Invalid number of arguments")
            
            if not db_name:
                print("No database selected and no database specified")
                print("Use: show_grants <db> <user>;")
                return None
            
            db.permManager.show_grants(db_name, username)
            
        except ValueError:
            print("Syntax error")
            print("Usage: show_grants <user>  OR  show_grants <db> <user>;")
            print("Examples:")
            print("  show_grants alice;")
            print("  show_grants my_db alice;")
        except Exception as e:
            print(f"Error: {e}")

        return None

    # Commande non gérée
    return None