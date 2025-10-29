"""
Commandes de gestion des bases de données
"""

from utils import check_permission


def handle_database_commands(cmd, cmd_line, session):
    """
    Gère toutes les commandes relatives aux bases de données
    
    Args:
        cmd: Commande complète
        cmd_line: Premier mot de la commande
        session: Dictionnaire de session
    """
    db = session['db']
    DB_PATH = session['DB_PATH']
    
    # CREATE DATABASE / CREATE_DB
    if cmd_line in ["create_database", "create_db"]:
        if cmd_line == "create_database":
            dbName = cmd[16:].strip()
        else:
            dbName = cmd[9:].strip()
        
        db.create_DB(dbName)
    
    # USE DATABASE / USE_DB
    elif cmd_line in ["use_database", "use_db"]:
        if cmd_line == "use_database":
            useDatabase = cmd[12:].strip()
        else:
            useDatabase = cmd[6:].strip()
        
        dirs = db.list_database(DB_PATH)
        
        if useDatabase in dirs:
            if check_permission(db, "USAGE", useDatabase) or check_permission(db, "READ", useDatabase):
                print(f"✓ Database '{useDatabase}' selected")
                session['useDatabase'] = useDatabase
                session['isDbUse'] = True
            else:
                current_username = db.current_user.get("username")
                print(f"❌ Permission denied to use '{useDatabase}' (user: {current_username})")
        else:
            print(f"❌ Database '{useDatabase}' does not exist")
            print(f"Available databases: {', '.join(dirs) if dirs else 'none'}")
    
    # DROP DATABASE / DROP_DB
    elif cmd_line in ["drop_database", "drop_db"]:
        if cmd_line == "drop_database":
            databaseToRemove = cmd[13:].strip()
        else:
            databaseToRemove = cmd[7:].strip()
        
        if databaseToRemove == session['useDatabase']:
            print("❌ This database is currently in use.")
            print("Use: 'leave_db' or select another database")
        else:
            confirm = input(f"⚠️  Delete database '{databaseToRemove}'? (yes/no): ").strip().lower()
            if confirm in ["oui", "yes", "y"]:
                db.drop_database(databaseToRemove)
            else:
                print("Operation cancelled")
    
    # LEAVE DATABASE / LEAVE_DB
    elif cmd_line in ["leave_db", "leave_database"]:
        if session['isDbUse']:
            print(f"✓ You left database '{session['useDatabase']}'")
            session['useDatabase'] = ""
            session['isDbUse'] = False
        else:
            print("ℹ️  No database currently selected")
    
    # LIST DATABASE / LIST_DB
    elif cmd_line in ["list_database", "list_db"]:
        db.show_databases()
    
    # STATS_DB / DATABASE_STATS
    elif cmd_line in ["stats_db", "database_stats"]:
        if session['isDbUse']:
            stats = db.get_statistics(session['useDatabase'])
            print(f"\n📊 Statistics for '{session['useDatabase']}':")
            print(f"    Tables: {stats['tables']}")
            print(f"    Total rows: {stats['total_rows']}")
            print(f"    Total columns: {stats['total_columns']}")
        else:
            print("❌ No database selected")
            print("Use: use_db <database_name>;")