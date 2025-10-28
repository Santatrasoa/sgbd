"""
MY SGBD - Système de Gestion de Base de Données Personnel
Version 2.0 - Synchronisée et Améliorée

Partie 1/5 : Imports, Configuration et Fonctions Helper
"""

import os
import readline
import json
import hashlib
import re
from pathlib import Path

# Import depuis le package db
from db.db_main import Db
from utils import load_config

# ============================================================================
# CONFIGURATION
# ============================================================================
config = load_config()
DB_PATH = config.get("db_path", ".database")
DEFAULT_PROMPT = config.get("default_prompt", "m¥⇒")
SEPARATOR = config.get("separator_char", "—")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def hash_password(password):
    """
    Hash un mot de passe avec SHA-256
    
    Args:
        password: Mot de passe en clair
        
    Returns:
        str: Hash SHA-256 du mot de passe
    """
    return hashlib.sha256(password.encode()).hexdigest()


def check_permission(db, operation, database_name, table_name=None):
    """
    Vérifie si l'utilisateur actuel a la permission pour une opération
    
    Args:
        db: Instance de la base de données
        operation: Type d'opération (READ, INSERT, DELETE, UPDATE, DROP, SELECT, ALL)
        database_name: Nom de la base de données
        table_name: Nom de la table (optionnel)
    
    Returns:
        bool: True si autorisé, False sinon
    """
    current_username = db.current_user.get("username")
    role = db.current_user.get("role")
    
    # Les admins ont tous les droits
    if role == "admin":
        return True
    
    # Vérification au niveau table (si spécifié)
    if table_name:
        if (db.permManager.has_table_permission(database_name, table_name, current_username, "ALL") or
            db.permManager.has_table_permission(database_name, table_name, current_username, operation)):
            return True
    
    # Vérification au niveau base de données
    if (db.permManager.has_db_permission(database_name, current_username, "ALL") or
        db.permManager.has_db_permission(database_name, current_username, operation)):
        return True
    
    return False


def validate_table_name(name):
    """
    Valide le nom d'une table selon les règles SQL
    
    Args:
        name: Nom de la table à valider
        
    Returns:
        tuple: (bool, str) - (valide?, message d'erreur si invalide)
    """
    if not name:
        return False, "Le nom de table ne peut pas être vide"
    
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        return False, "Le nom doit commencer par une lettre ou _ et contenir uniquement des lettres, chiffres et _"
    
    if len(name) > 64:
        return False, "Le nom de table ne peut pas dépasser 64 caractères"
    
    return True, ""


def split_top_level_commas(s):
    """
    Split une chaîne par virgules en ignorant celles dans les crochets
    Utilisé pour parser les définitions de colonnes avec contraintes
    
    Args:
        s: Chaîne à découper
        
    Returns:
        list: Liste des fragments séparés par virgules (hors crochets)
        
    Example:
        "col1:string[not_null,unique], col2:number" 
        -> ["col1:string[not_null,unique]", "col2:number"]
    """
    parts = []
    cur = []
    depth = 0
    
    for ch in s:
        if ch == '[':
            depth += 1
            cur.append(ch)
        elif ch == ']':
            depth = max(depth - 1, 0)
            cur.append(ch)
        elif ch == ',' and depth == 0:
            fragment = ''.join(cur).strip()
            if fragment:
                parts.append(fragment)
            cur = []
        else:
            cur.append(ch)
    
    # Ajouter le dernier fragment
    last = ''.join(cur).strip()
    if last:
        parts.append(last)
    
    return parts


def parse_where_clause(where_clause, all_rows):
    """
    Parse et applique une clause WHERE avec support des opérateurs multiples
    
    Supporte les opérateurs: =, !=, >, <, >=, <=, LIKE
    
    Args:
        where_clause: Clause WHERE sans le mot-clé WHERE
        all_rows: Liste de dictionnaires représentant les lignes
        
    Returns:
        list: Liste filtrée des lignes correspondant à la condition
        
    Examples:
        parse_where_clause("age > 18", rows)
        parse_where_clause("nom LIKE %Jean%", rows)
        parse_where_clause("status = active", rows)
    """
    where_clause = where_clause.strip()
    
    # Détection de l'opérateur (ordre important pour >= et <=)
    operators = ['>=', '<=', '!=', '=', '>', '<', ' LIKE ', ' like ']
    operator = None
    
    for op in operators:
        if op in where_clause:
            operator = op.strip()
            break
    
    if not operator:
        print("❌ Opérateur non reconnu dans WHERE")
        print("Opérateurs supportés: =, !=, >, <, >=, <=, LIKE")
        return []
    
    try:
        # Découper la clause WHERE
        parts = where_clause.split(operator, 1)
        if len(parts) != 2:
            print("❌ Syntaxe WHERE invalide")
            return []
        
        left = parts[0].strip()  # Nom de la colonne
        right = parts[1].strip().strip("'").strip('"')  # Valeur de comparaison
        
        filtered_rows = []
        
        for row in all_rows:
            value = str(row.get(left, ""))
            
            # Appliquer l'opérateur
            if operator == '=':
                if value == right:
                    filtered_rows.append(row)
                    
            elif operator == '!=':
                if value != right:
                    filtered_rows.append(row)
                    
            elif operator == '>':
                try:
                    # Essayer comparaison numérique
                    if float(value) > float(right):
                        filtered_rows.append(row)
                except ValueError:
                    # Comparaison alphabétique
                    if value > right:
                        filtered_rows.append(row)
                        
            elif operator == '<':
                try:
                    if float(value) < float(right):
                        filtered_rows.append(row)
                except ValueError:
                    if value < right:
                        filtered_rows.append(row)
                        
            elif operator == '>=':
                try:
                    if float(value) >= float(right):
                        filtered_rows.append(row)
                except ValueError:
                    if value >= right:
                        filtered_rows.append(row)
                        
            elif operator == '<=':
                try:
                    if float(value) <= float(right):
                        filtered_rows.append(row)
                except ValueError:
                    if value <= right:
                        filtered_rows.append(row)
                        
            elif operator.upper() == 'LIKE':
                # Conversion du pattern SQL LIKE en regex Python
                # % = 0 ou plusieurs caractères
                # _ = exactement 1 caractère
                pattern = right.replace('%', '.*').replace('_', '.')
                if re.search(pattern, value, re.IGNORECASE):
                    filtered_rows.append(row)
        
        return filtered_rows
        
    except Exception as e:
        print(f"❌ Erreur dans la clause WHERE: {e}")
        return []

"""
MY SGBD - Partie 2/5 : Initialisation et Gestion des Bases de Données

Cette partie contient :
- Initialisation du système
- Boucle principale
- Commandes de gestion des bases de données (CREATE, DROP, USE, LIST, STATS)
"""

# ============================================================================
# INITIALISATION
# ============================================================================

# Créer l'instance de base de données
db = Db(DB_PATH)

# Variables de session
useDatabase = ""
isDbUse = False

# Formater le prompt avec l'utilisateur actuel
userUsingDb = f"user:\033[32m{db.current_user['username']}\033[0m"
promptContainte = f"[{userUsingDb}]\n{DEFAULT_PROMPT} "

# Charger l'historique des commandes si disponible
if os.path.exists(".history"):
    try:
        readline.read_history_file(".history")
    except Exception:
        pass

# Message de bienvenue
print("╔══════════════════════════════════════════════════════════════╗")
print("║          Bienvenue dans MY - Votre SGBD personnel            ║")
print("╚══════════════════════════════════════════════════════════════╝")
print("Tapez 'help' pour voir les commandes disponibles\n")

# ============================================================================
# BOUCLE PRINCIPALE
# ============================================================================

while True:
    print("")
    try:
        cmd = input("my ~ " + promptContainte)
    except KeyboardInterrupt:
        print("\n^C")
        continue
    except EOFError:
        readline.write_history_file(".history")
        print("\n👋 Au revoir ! Merci d'avoir utilisé MY")
        exit()

    # ========================================
    # Commandes système simples
    # ========================================
    
    # Clear : nettoyer l'écran
    if cmd.strip() in ["clear", "clear;"]:
        os.system("clear" if os.name != "nt" else "cls")
        continue
    
    # Exit : quitter le programme
    if cmd.strip() in ["exit", "exit;"]:
        readline.write_history_file(".history")
        print("👋 Au revoir ! Merci d'avoir utilisé MY")
        exit()

    # ========================================
    # Gestion des commandes multi-lignes
    # ========================================
    
    # Continuer à lire jusqu'à trouver un point-virgule
    while not cmd.endswith(";"):
        try:
            next_line = input(" ⇘ ")
        except KeyboardInterrupt:
            print("\n^C")
            break
        except EOFError:
            print("\n👋 Au revoir ! Merci d'avoir utilisé MY")
            readline.write_history_file(".history")
            exit()
        cmd += " " + next_line.strip()

    # Nettoyer la commande
    cmd = cmd.replace(";", "").strip()
    if not cmd:
        continue
    
    # Extraire le mot-clé de la commande
    cmd_line = cmd.split(" ")[0].lower()

    # ============================================================================
    # GESTION DES BASES DE DONNÉES
    # ============================================================================

    # ----------------------------------------
    # CREATE DATABASE : Créer une base
    # ----------------------------------------
    if cmd_line.startswith("create_database") or cmd_line.startswith("create_db"):
        # Extraire le nom de la base
        if cmd_line.startswith("create_database"):
            dbName = cmd[16:].strip()  # Après "create_database "
        else:
            dbName = cmd[9:].strip()   # Après "create_db "
        
        # Appeler la méthode de création
        db.create_DB(dbName)

    # ----------------------------------------
    # USE DATABASE : Sélectionner une base
    # ----------------------------------------
    elif cmd_line.startswith("use_database") or cmd_line.startswith("use_db"):
        # Extraire le nom de la base
        if cmd_line.startswith("use_database"):
            useDatabase = cmd[12:].strip()
        else:
            useDatabase = cmd[6:].strip()
        
        # Vérifier que la base existe
        dirs = db.list_database(DB_PATH)
        
        if useDatabase in dirs:
            # Vérifier les permissions
            if check_permission(db, "USAGE", useDatabase) or check_permission(db, "READ", useDatabase):
                print(f"✓ Base de données '{useDatabase}' sélectionnée")
                # Mettre à jour le prompt
                promptContainte = f"[{userUsingDb} & db:\033[34m{useDatabase}\033[0m]\n{DEFAULT_PROMPT} "
                isDbUse = True
            else:
                current_username = db.current_user.get("username")
                print(f"🚫 Permission refusée pour utiliser '{useDatabase}' (utilisateur: {current_username})")
        else:
            print(f"❌ La base de données '{useDatabase}' n'existe pas")
            print(f"Bases disponibles: {', '.join(dirs) if dirs else 'aucune'}")

    # ----------------------------------------
    # DROP DATABASE : Supprimer une base
    # ----------------------------------------
    elif cmd_line.startswith("drop_database") or cmd_line.startswith("drop_db"):
        # Extraire le nom de la base
        if cmd_line.startswith("drop_database"):
            databaseToRemove = cmd[13:].strip()
        else:
            databaseToRemove = cmd[7:].strip()
        
        # Vérifier si la base n'est pas en cours d'utilisation
        if databaseToRemove == useDatabase:
            print("⚠️ Cette base de données est en cours d'utilisation.")
            print("Utilisez: 'leave_db' ou sélectionnez une autre base")
        else:
            # Demander confirmation
            confirm = input(f"⚠️ Supprimer la base '{databaseToRemove}' ? (oui/non): ").strip().lower()
            if confirm in ["oui", "yes", "y"]:
                db.drop_database(databaseToRemove)
            else:
                print("❌ Opération annulée")

    # ----------------------------------------
    # LEAVE DATABASE : Quitter la base actuelle
    # ----------------------------------------
    elif cmd_line.startswith("leave_db") or cmd_line.startswith("leave_database"):
        if isDbUse:
            print(f"✓ Vous avez quitté la base de données '{useDatabase}'")
            useDatabase = ""
            isDbUse = False
            # Réinitialiser le prompt
            promptContainte = f"[{userUsingDb}]\n{DEFAULT_PROMPT} "
        else:
            print("⚠️ Aucune base de données n'est actuellement sélectionnée")

    # ----------------------------------------
    # LIST DATABASE : Lister les bases
    # ----------------------------------------
    elif cmd_line.startswith("list_database") or cmd_line.startswith("list_db"):
        db.show_databases()

    # ----------------------------------------
    # DATABASE STATS : Statistiques de la base
    # ----------------------------------------
    elif cmd_line.startswith("stats_db") or cmd_line.startswith("database_stats"):
        if isDbUse:
            stats = db.get_statistics(useDatabase)
            print(f"\n📊 Statistiques de '{useDatabase}':")
            print(f"   📋 Tables: {stats['tables']}")
            print(f"   📝 Lignes totales: {stats['total_rows']}")
            print(f"   📑 Colonnes totales: {stats['total_columns']}")
        else:
            print("⚠️ Aucune base de données sélectionnée")
            print("Utilisez: use_db <nom_base>;")

    # else:
    #     # Cette commande sera gérée dans les parties suivantes
    #     # Pour l'instant, on affiche un message temporaire
    #     print(f"⏳ Commande '{cmd_line}' en cours de traitement...")

    #     """
    #     MY SGBD - Partie 3/5 : Gestion des Tables

    #     Cette partie contient :
    #     - CREATE TABLE (avec parsing avancé des colonnes et contraintes)
    #     - DROP TABLE
    #     - LIST TABLE
    #     - DESCRIBE TABLE
    #     - ADD INTO TABLE (insertion de données)
    #     """

# ============================================================================
# GESTION DES TABLES
# ============================================================================

    # ----------------------------------------
    # CREATE TABLE : Créer une table
    # ----------------------------------------
    elif cmd_line.startswith("create_table"):
        if not isDbUse:
            print("⚠️ Aucune base de données sélectionnée")
            print("Utilisez: use_db <nom_base>;")
            continue

        try:
            # Vérifier la présence des parenthèses
            if "(" not in cmd or ")" not in cmd:
                print("❌ Erreur de syntaxe: parenthèses manquantes")
                print("Usage: create_table nom(col1:type[contraintes], col2:type, ...);")
                print("Exemple: create_table users(id:number[primary_key], nom:string[not_null]);")
                continue

            # Extraction du nom de la table
            name = cmd.split(" ")[1].split("(")[0].strip()

            # Validation du nom de table
            is_valid, error_msg = validate_table_name(name)
            if not is_valid:
                print(f"❌ Nom de table invalide: {error_msg}")
                continue

            # Vérification des permissions
            if not check_permission(db, "ALL", useDatabase, name):
                current_username = db.current_user.get("username")
                print(f"🚫 Permission refusée pour créer la table '{name}' (utilisateur: {current_username})")
                continue

            # Extraire le contenu entre parenthèses
            inside = cmd[cmd.find("(") + 1: cmd.rfind(")")].strip()
            columns = split_top_level_commas(inside)

            # Types de données autorisés
            allType = ["date", "year", "time", "datetime", "bool", "number", "float", "string", "text", "bit"]

            # Contraintes autorisées
            constraints_allowed = {
                "not_null": "Not_null",
                "unique": "Unique",
                "primary_key": "Primary_key",
                "foreign_key": "Foreign_key",
                "check": "Check",
                "default": "Default",
                "auto_increment": "Auto_increment"
            }

            attr = {}
            constr = {}
            has_error = False

            # Parcourir chaque colonne
            for val in columns:
                val = val.strip()
                if not val:
                    continue

                # Vérifier syntaxe nom:type
                if ":" not in val:
                    print(f"❌ Erreur de syntaxe dans '{val}' — format attendu: nom:type[contrainte,...]")
                    print("Exemple: id:number[primary_key,not_null]")
                    has_error = True
                    break

                # Séparer nom et type+contraintes
                parts = val.split(":", 1)
                col = parts[0].strip()
                type_and_constraints = parts[1].strip()

                # Vérifier nom de colonne
                if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', col):
                    print(f"❌ Nom de colonne invalide: '{col}'")
                    print("Le nom doit commencer par une lettre ou _ et contenir uniquement lettres, chiffres et _")
                    has_error = True
                    break

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

                t = type_part.lower()

                # Vérifier type de donnée
                if t not in allType:
                    print(f"❌ Type inconnu '{type_part}' pour la colonne '{col}'")
                    print(f"Types disponibles: {', '.join(allType)}")
                    has_error = True
                    break

                # Normaliser et valider contraintes
                normalized_constraints = []
                invalid_constraints = []

                for rc in raw_constraints:
                    key = rc.lower().replace(" ", "_").replace("-", "_")
                    if key in constraints_allowed:
                        normalized_constraints.append(constraints_allowed[key])
                    else:
                        invalid_constraints.append(rc)

                # Si contraintes invalides → erreur bloquante
                if invalid_constraints:
                    print(f"⚠️ Contraintes inconnues pour '{col}': {', '.join(invalid_constraints)}")
                    print(f"Contraintes disponibles: {', '.join(constraints_allowed.keys())}")
                    has_error = True
                    break

                # Enregistrer attributs + contraintes
                attr[col] = type_part.capitalize() if t != "number" else "Number"
                constr[col] = normalized_constraints if normalized_constraints else ["no constraint"]

            # Si erreur → on stoppe la création
            if has_error:
                print("❌ Création annulée à cause d’erreurs détectées.")
                continue

            # Créer la table si tout est correct
            table_def = {
                "caracteristique": attr,
                "constraint": constr,
                "data": []
            }

            db.create_Table(useDatabase, name, table_def)

        except Exception as e:
            print(f"🔥 Erreur lors de la création de la table: {e}")
            import traceback
            traceback.print_exc()

    # ----------------------------------------
    # ADD INTO TABLE : Insérer des données
    # ----------------------------------------
    elif cmd_line.startswith("add_into_table"):
        if not isDbUse:
            print("⚠️ Aucune base de données sélectionnée")
            print("Utilisez: use_db <nom_base>;")
            continue
            
        try:
            # Parser la commande: add_into_table nom_table(col1=val1, col2=val2)
            getData = " ".join(cmd.split(" ")[1:]).strip().split("(")
            table_name = getData[0].strip()
            values_str = getData[1].replace(")", "").strip()
            values = [v.strip() for v in values_str.split(",")]
            
            # Chemin vers le fichier de la table
            pathToFile = f"{DB_PATH}/{useDatabase}/{table_name}.json"
            
            # Vérification des permissions
            if not check_permission(db, "INSERT", useDatabase, table_name):
                current_username = db.current_user.get("username")
                print(f"🚫 Permission refusée pour insérer dans '{table_name}' (utilisateur: {current_username})")
                continue
            
            # Appeler la méthode d'analyse et insertion
            db.analyse_data(pathToFile, values)
            
        except IndexError:
            print("❌ Erreur de syntaxe")
            print("Usage: add_into_table nom_table(col1=val1, col2=val2, ...);")
            print("Exemple: add_into_table users(id=1, nom=Alice, age=25);")
        except Exception as e:
            print(f"❌ Erreur: {e}")

    # ----------------------------------------
    # DROP TABLE : Supprimer une table
    # ----------------------------------------
    elif cmd_line.startswith("drop_table"):
        if not isDbUse:
            print("⚠️ Aucune base de données sélectionnée")
            print("Utilisez: use_db <nom_base>;")
            continue
            
        tableToRemove = cmd[10:].strip()
        
        # Vérification des permissions
        if not check_permission(db, "DROP", useDatabase, tableToRemove):
            current_username = db.current_user.get("username")
            print(f"🚫 Permission refusée pour supprimer '{tableToRemove}' (utilisateur: {current_username})")
            continue
        
        # Demander confirmation
        confirm = input(f"⚠️ Supprimer la table '{tableToRemove}' ? (oui/non): ").strip().lower()
        if confirm in ["oui", "yes", "y"]:
            db.drop_table(useDatabase, tableToRemove)
        else:
            print("❌ Opération annulée")

    # ----------------------------------------
    # LIST TABLE : Lister les tables
    # ----------------------------------------
    elif cmd_line.startswith("list_table"):
        if not isDbUse:
            print("⚠️ Aucune base de données sélectionnée")
            print("Utilisez: use_db <nom_base>;")
            continue
            
        current_username = db.current_user.get("username")
        role = db.current_user.get("role")
        
        # Vérifier les permissions
        if role != "admin" and not db.permManager.user_has_any_permission(useDatabase, current_username):
            print(f"🚫 Permission refusée pour lister les tables de '{useDatabase}' (utilisateur: {current_username})")
            continue
        
        # Lister les tables
        path = f"{DB_PATH}/{useDatabase}"
        tables = db.list_table(path)
        
        if len(tables) == 0:
            print("📂 Aucune table trouvée dans cette base de données")
        else:
            # Calculer la largeur pour l'affichage
            l = max([len(t.replace('.json', '')) for t in tables] + [15])
            print(SEPARATOR * (l + 4))
            print(f"{'TABLES DANS ' + useDatabase.upper():^{l + 4}}")
            print(SEPARATOR * (l + 4))
            
            for t in sorted(tables):
                table_name = t.replace('.json', '')
                print(f" {table_name:<{l}}")
            
            print(SEPARATOR * (l + 4))
            print(f"Total: {len(tables)} table{'s' if len(tables) > 1 else ''}")

    # ----------------------------------------
    # DESCRIBE TABLE : Décrire une table
    # ----------------------------------------
    elif cmd_line.startswith("describe_table"):
        if not isDbUse:
            print("⚠️ Aucune base de données sélectionnée")
            print("Utilisez: use_db <nom_base>;")
            continue
            
        table_name = cmd[15:].strip()
        
        # Vérification des permissions
        if not check_permission(db, "SELECT", useDatabase, table_name):
            current_username = db.current_user.get("username")
            print(f"🚫 Permission refusée pour décrire '{table_name}' (utilisateur: {current_username})")
            continue
        
        # Afficher la description
        pathToFile = f"{DB_PATH}/{useDatabase}/{table_name}.json"
        db.describe_table(pathToFile)
        """
        MY SGBD - Partie 4/5 : Requêtes SQL

        Cette partie contient :
        - SELECT (avec WHERE avancé)
        - UPDATE (avec WHERE)
        - DELETE (avec WHERE)
        """

    # ----------------------------------------
    # SELECT : Interroger les données
    # ----------------------------------------
    elif cmd_line.startswith("select"):
        if not isDbUse:
            print("⚠️ Aucune base de données sélectionnée")
            print("Utilisez: use_db <nom_base>;")
            continue
            
        # Extraire la requête (tout après "select")
        getRequests = " ".join(cmd.split(" ")[1:]).strip()
        
        if len(getRequests) == 0:
            print("❌ Erreur de syntaxe")
            print("Usage: select <colonnes> from <table> [where <condition>];")
            print("Exemples:")
            print("  select * from users;")
            print("  select nom, age from users where age > 18;")
            continue
        
        # Parser la requête: select colonnes from table [where condition]
        parts = getRequests.split()
        
        if len(parts) >= 3 and parts[1].lower() == "from":
            columns_part = parts[0]
            table_name = parts[2]
            
            # Vérification des permissions
            if not check_permission(db, "SELECT", useDatabase, table_name):
                current_username = db.current_user.get("username")
                print(f"🚫 Permission refusée pour lire '{table_name}' (utilisateur: {current_username})")
                continue
            
            # Extraire la clause WHERE si présente
            where_clause = None
            if "where" in [p.lower() for p in parts]:
                where_index = [p.lower() for p in parts].index("where")
                if len(parts) > where_index + 1:
                    where_clause = " ".join(parts[where_index + 1:])
                else:
                    print("❌ Erreur de syntaxe après WHERE")
                    continue
            
            # Chemin vers le fichier de la table
            path = f"{DB_PATH}/{useDatabase}/{table_name}.json"
            
            if not os.path.exists(path):
                print(f"❌ La table '{table_name}' n'existe pas")
                continue
            
            try:
                # Charger la table
                with open(path, "r", encoding="utf-8") as f:
                    content = json.load(f)
                
                all_rows = content.get("data", [])
                all_columns = list(content.get("caracteristique", {}).keys())
                
                # Normalisation des données (nettoyer les espaces et guillemets)
                normalized_rows = []
                for row in all_rows:
                    clean_row = {}
                    for k, v in row.items():
                        clean_row[k.strip()] = str(v).strip().strip('"')
                    normalized_rows.append(clean_row)
                
                all_rows = normalized_rows
                
                # Sélection des colonnes
                if columns_part == "*":
                    selected_columns = all_columns
                else:
                    selected_columns = [c.strip() for c in columns_part.split(",")]
                    
                    # Vérifier que les colonnes existent
                    invalid_cols = [c for c in selected_columns if c not in all_columns]
                    if invalid_cols:
                        print(f"❌ Colonnes inconnues: {', '.join(invalid_cols)}")
                        print(f"Colonnes disponibles: {', '.join(all_columns)}")
                        continue
                
                # Application du WHERE
                filtered_rows = all_rows
                if where_clause:
                    filtered_rows = parse_where_clause(where_clause, all_rows)
                
                # Affichage des résultats
                if len(filtered_rows) == 0:
                    print("📭 Aucune donnée trouvée")
                else:
                    # Calculer la largeur de chaque colonne
                    col_widths = {
                        col: max(len(col), max((len(str(row.get(col, ""))) for row in filtered_rows), default=0))
                        for col in selected_columns
                    }
                    total_width = sum(col_widths.values()) + (len(selected_columns) * 3) + 1
                    
                    # Afficher l'en-tête
                    print(SEPARATOR * total_width)
                    print(" | ".join(col.ljust(col_widths[col]) for col in selected_columns))
                    print(SEPARATOR * total_width)
                    
                    # Afficher les lignes
                    for row in filtered_rows:
                        print(" | ".join(str(row.get(col, "")).ljust(col_widths[col]) for col in selected_columns))
                    
                    print(SEPARATOR * total_width)
                    print(f"({len(filtered_rows)} ligne{'s' if len(filtered_rows) > 1 else ''} retournée{'s' if len(filtered_rows) > 1 else ''})")
                    
            except json.JSONDecodeError:
                print(f"❌ Erreur: fichier JSON corrompu pour la table '{table_name}'")
            except Exception as e:
                print(f"❌ Erreur lors de la lecture: {e}")
        else:
            print("❌ Erreur de syntaxe")
            print("Usage: select <colonnes> from <table> [where <condition>];")
            print("Exemples:")
            print("  select * from users;")
            print("  select nom, age from users where age > 18;")
            print("  select * from users where nom LIKE %jean%;")

    # ----------------------------------------
    # UPDATE : Modifier des données
    # ----------------------------------------
    elif cmd_line.startswith("update"):
        if not isDbUse:
            print("⚠️ Aucune base de données sélectionnée")
            print("Utilisez: use_db <nom_base>;")
            continue
        
        try:
            # Parsing: UPDATE table SET col1=val1, col2=val2 WHERE condition
            parts = cmd.split()
            
            if len(parts) < 4 or parts[2].lower() != "set":
                raise ValueError("Syntaxe invalide")
            
            table_name = parts[1]
            
            # Vérification des permissions
            if not check_permission(db, "UPDATE", useDatabase, table_name):
                current_username = db.current_user.get("username")
                print(f"🚫 Permission refusée pour modifier '{table_name}' (utilisateur: {current_username})")
                continue
            
            # Trouver SET et WHERE
            set_index = [p.lower() for p in parts].index("set")
            where_index = [p.lower() for p in parts].index("where") if "where" in [p.lower() for p in parts] else None
            
            # Extraire les assignations
            if where_index:
                set_part = " ".join(parts[set_index + 1:where_index])
                where_clause = " ".join(parts[where_index + 1:])
            else:
                set_part = " ".join(parts[set_index + 1:])
                where_clause = None
            
            # Parser les assignations (col1=val1, col2=val2)
            assignments = {}
            for assign in set_part.split(","):
                if "=" not in assign:
                    raise ValueError(f"Assignation invalide: {assign}")
                col, val = assign.split("=", 1)
                col = col.strip()
                val = val.strip().strip("'").strip('"')
                assignments[col] = val
            
            # Charger la table
            path = f"{DB_PATH}/{useDatabase}/{table_name}.json"
            if not os.path.exists(path):
                print(f"❌ La table '{table_name}' n'existe pas")
                continue
            
            with open(path, "r", encoding="utf-8") as f:
                content = json.load(f)
            
            all_rows = content.get("data", [])
            
            # Normalisation
            normalized_rows = []
            for row in all_rows:
                clean_row = {}
                for k, v in row.items():
                    clean_row[k.strip()] = str(v).strip().strip('"')
                normalized_rows.append(clean_row)
            
            # Appliquer WHERE si présent
            if where_clause:
                rows_to_update = parse_where_clause(where_clause, normalized_rows)
            else:
                # Confirmation pour UPDATE sans WHERE
                confirm = input(f"⚠️ Mettre à jour TOUTES les lignes de '{table_name}'? (oui/non): ").strip().lower()
                if confirm not in ["oui", "yes", "y"]:
                    print("❌ Opération annulée")
                    continue
                rows_to_update = normalized_rows
            
            # Mettre à jour les lignes
            updated_count = 0
            for row in normalized_rows:
                if row in rows_to_update:
                    for col, val in assignments.items():
                        if col in row:
                            row[col] = val
                    updated_count += 1
            
            # Sauvegarder
            content["data"] = normalized_rows
            with open(path, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
            
            print(f"✓ {updated_count} ligne{'s' if updated_count > 1 else ''} mise{'s' if updated_count > 1 else ''} à jour")
            
        except ValueError as e:
            print(f"❌ Erreur de syntaxe: {e}")
            print("Usage: update <table> set col1=val1, col2=val2 [where condition];")
            print("Exemple: update users set age=26 where nom = Alice;")
        except Exception as e:
            print(f"❌ Erreur: {e}")

    # ----------------------------------------
    # DELETE : Supprimer des données
    # ----------------------------------------
    elif cmd_line.startswith("delete"):
        if not isDbUse:
            print("⚠️ Aucune base de données sélectionnée")
            print("Utilisez: use_db <nom_base>;")
            continue
        
        try:
            # Parsing: DELETE FROM table WHERE condition
            parts = cmd.split()
            
            if len(parts) < 3 or parts[1].lower() != "from":
                raise ValueError("Syntaxe invalide")
            
            table_name = parts[2]
            
            # Vérification des permissions
            if not check_permission(db, "DELETE", useDatabase, table_name):
                current_username = db.current_user.get("username")
                print(f"🚫 Permission refusée pour supprimer dans '{table_name}' (utilisateur: {current_username})")
                continue
            
            # WHERE clause
            where_clause = None
            if "where" in [p.lower() for p in parts]:
                where_index = [p.lower() for p in parts].index("where")
                if len(parts) > where_index + 1:
                    where_clause = " ".join(parts[where_index + 1:])
                else:
                    raise ValueError("Condition WHERE manquante")
            else:
                # Confirmation pour DELETE sans WHERE
                confirm = input(f"⚠️ Supprimer TOUTES les lignes de '{table_name}'? (oui/non): ").strip().lower()
                if confirm not in ["oui", "yes", "y"]:
                    print("❌ Opération annulée")
                    continue
            
            # Charger la table
            path = f"{DB_PATH}/{useDatabase}/{table_name}.json"
            if not os.path.exists(path):
                print(f"❌ La table '{table_name}' n'existe pas")
                continue
            
            with open(path, "r", encoding="utf-8") as f:
                content = json.load(f)
            
            all_rows = content.get("data", [])
            
            # Normalisation
            normalized_rows = []
            for row in all_rows:
                clean_row = {}
                for k, v in row.items():
                    clean_row[k.strip()] = str(v).strip().strip('"')
                normalized_rows.append(clean_row)
            
            # Appliquer WHERE
            if where_clause:
                rows_to_delete = parse_where_clause(where_clause, normalized_rows)
                remaining_rows = [row for row in normalized_rows if row not in rows_to_delete]
            else:
                rows_to_delete = normalized_rows
                remaining_rows = []
            
            # Sauvegarder
            content["data"] = remaining_rows
            with open(path, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
            
            print(f"✓ {len(rows_to_delete)} ligne{'s' if len(rows_to_delete) > 1 else ''} supprimée{'s' if len(rows_to_delete) > 1 else ''}")
            
        except ValueError as e:
            print(f"❌ Erreur de syntaxe: {e}")
            print("Usage: delete from <table> [where condition];")
            print("Exemple: delete from users where age < 18;")
        except Exception as e:
            print(f"❌ Erreur: {e}")

            """
            MY SGBD - Partie 5/5 : Utilisateurs, Permissions et Help

            Cette partie contient :
            - Gestion des utilisateurs (CREATE, DROP, SWITCH, LIST)
            - Gestion des permissions (GRANT, REVOKE, SHOW GRANTS)
            - Commande HELP
            - Gestion des commandes inconnues
            """

# ============================================================================
# GESTION DES UTILISATEURS
# ============================================================================

    # ----------------------------------------
    # CREATE USER : Créer un utilisateur
    # ----------------------------------------
    elif cmd_line.startswith("create_user"):
        try:
            args = cmd.split(" ")
            name = args[1]
            password = [a for a in args if a.startswith("password=")]
            role = [a for a in args if a.startswith("role=")]
            
            if not password:
                print("❌ Mot de passe requis")
                print("Usage: create_user nom password=motdepasse [role=user|admin];")
                print("Exemple: create_user alice password=secret123 role=user;")
                continue
            
            pwd = password[0].split("=")[1]
            
            # Hash du mot de passe avec SHA-256
            hashed_pwd = hash_password(pwd)
            
            rl = role[0].split("=")[1] if role else "user"
            
            if rl not in ["user", "admin"]:
                print("❌ Rôle invalide. Utilisez 'user' ou 'admin'")
                continue
            
            # Créer l'utilisateur
            db.userManager.create_user(name, hashed_pwd, rl)
            print(f"✓ Utilisateur '{name}' créé avec le rôle '{rl}'")
            
        except IndexError:
            print("❌ Erreur de syntaxe")
            print("Usage: create_user nom password=motdepasse [role=user|admin];")
            print("Exemple: create_user alice password=secret123 role=user;")
        except Exception as e:
            print(f"❌ Erreur: {e}")

    # ----------------------------------------
    # LIST USER : Lister les utilisateurs
    # ----------------------------------------
    elif cmd_line.startswith("list_user"):
        db.userManager.list_users()

    # ----------------------------------------
    # DROP USER : Supprimer un utilisateur
    # ----------------------------------------
    elif cmd_line.startswith("drop_user"):
        try:
            username = cmd.split(" ")[1]
            
            # Empêcher la suppression de son propre compte
            if username == db.current_user.get("username"):
                print("❌ Vous ne pouvez pas supprimer votre propre compte")
                print("Connectez-vous avec un autre utilisateur pour supprimer ce compte")
                continue
            
            # Demander confirmation
            confirm = input(f"⚠️ Supprimer l'utilisateur '{username}' ? (oui/non): ").strip().lower()
            if confirm in ["oui", "yes", "y"]:
                db.userManager.drop_user(username)
            else:
                print("❌ Opération annulée")
                
        except IndexError:
            print("❌ Nom d'utilisateur requis")
            print("Usage: drop_user nom_utilisateur;")
            print("Exemple: drop_user alice;")

    # ----------------------------------------
    # SWITCH USER : Changer d'utilisateur
    # ----------------------------------------
    elif cmd_line.startswith("switch_user_to"):
        try:
            args = cmd.split(" ")
            name = args[1]
            pwd = args[2].split("=")[1]
            
            # Hash du mot de passe pour comparaison
            hashed_pwd = hash_password(pwd)
            
            # Tenter de se connecter
            user = db.userManager.switch_user_to(name, hashed_pwd)
            
            if user:
                # Mise à jour de l'utilisateur actuel
                db.current_user = user
                userUsingDb = f"user:\033[32m{name}\033[0m"
                
                # Mettre à jour le prompt
                if isDbUse:
                    promptContainte = f"[{userUsingDb} & db:\033[34m{useDatabase}\033[0m]\n{DEFAULT_PROMPT} "
                else:
                    promptContainte = f"[{userUsingDb}]\n{DEFAULT_PROMPT} "
                
                print(f"✓ Connecté en tant que '{name}'")
            else:
                print("❌ Nom d'utilisateur ou mot de passe incorrect")
                
        except (IndexError, ValueError):
            print("❌ Erreur de syntaxe")
            print("Usage: switch_user_to nom_utilisateur password=motdepasse;")
            print("Exemple: switch_user_to alice password=secret123;")

# ============================================================================
# GESTION DES PERMISSIONS
# ============================================================================

    # ----------------------------------------
    # GRANT : Accorder une permission
    # ----------------------------------------
    elif cmd_line.startswith("grant"):
        try:
            parts = cmd.split()
            permission = parts[1].upper()
            on_index = parts.index("on")
            to_index = parts.index("to")
            raw_target = parts[on_index + 1]
            username = parts[to_index + 1]
            
            # Support pour db.table ou db.*
            if "." in raw_target:
                db_name, target = raw_target.split(".", 1)
            else:
                db_name = useDatabase
                target = raw_target
            
            if not db_name:
                print("❌ Aucune base de données sélectionnée et aucune base qualifiée")
                print("Utilisez: grant <perm> on <db.table> to <user>;")
                continue
            
            caller_username = db.current_user.get("username")
            caller_role = db.current_user.get("role")
            
            # Accorder la permission
            db.permManager.grant(db_name, target, username, permission, 
                               caller_username=caller_username, caller_role=caller_role)
            print(f"✓ Permission '{permission}' accordée à '{username}' sur '{raw_target}'")
            
        except (ValueError, IndexError):
            print("❌ Erreur de syntaxe")
            print("Usage: grant <PERMISSION> on <table|db.table|*> to <utilisateur>;")
            print("Permissions: SELECT, INSERT, UPDATE, DELETE, DROP, ALL, USAGE")
            print("Exemples:")
            print("  grant SELECT on users to alice;")
            print("  grant ALL on ma_base.* to bob;")

    # ----------------------------------------
    # REVOKE : Révoquer une permission
    # ----------------------------------------
    elif cmd_line.startswith("revoke"):
        try:
            parts = cmd.split()
            permission = parts[1].upper()
            on_index = parts.index("on")
            from_index = parts.index("from")
            raw_target = parts[on_index + 1]
            username = parts[from_index + 1]
            
            # Support pour db.table ou db.*
            if "." in raw_target:
                db_name, target = raw_target.split(".", 1)
            else:
                db_name = useDatabase
                target = raw_target
            
            if not db_name:
                print("❌ Aucune base de données sélectionnée et aucune base qualifiée")
                print("Utilisez: revoke <perm> on <db.table> from <user>;")
                continue
            
            caller_username = db.current_user.get("username")
            caller_role = db.current_user.get("role")
            
            # Révoquer la permission
            db.permManager.revoke(db_name, target, username, permission, 
                                caller_username=caller_username, caller_role=caller_role)
            print(f"✓ Permission '{permission}' révoquée pour '{username}' sur '{raw_target}'")
            
        except (ValueError, IndexError):
            print("❌ Erreur de syntaxe")
            print("Usage: revoke <PERMISSION> on <table|db.table|*> from <utilisateur>;")
            print("Exemples:")
            print("  revoke SELECT on users from alice;")
            print("  revoke ALL on ma_base.* from bob;")

    # ----------------------------------------
    # SHOW GRANTS : Afficher les permissions
    # ----------------------------------------
    elif cmd_line.startswith("show_grants"):
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
                print("❌ Erreur de syntaxe")
                print("Usage: show_grants <utilisateur>  OU  show_grants <db> <utilisateur>;")
                print("Exemples:")
                print("  show_grants alice;")
                print("  show_grants ma_base alice;")
                continue
            
            if not db_name:
                print("❌ Aucune base de données sélectionnée et aucune base spécifiée")
                continue
            
            # Afficher les permissions
            db.permManager.show_grants(db_name, username)
            
        except Exception as e:
            print(f"❌ Erreur: {e}")

# ============================================================================
# AIDE ET COMMANDES INCONNUES
# ============================================================================

    # ----------------------------------------
    # HELP : Afficher l'aide
    # ----------------------------------------
    elif cmd_line.startswith("help"):
        db.show_help()

    # ----------------------------------------
    # Commande inconnue
    # ----------------------------------------
    else:
        print(f"❌ Commande '{cmd_line}' non reconnue")
        print("Tapez 'help' pour voir les commandes disponibles")

# ============================================================================
# FIN DE LA PARTIE 5/5 - CODE COMPLET
# ============================================================================