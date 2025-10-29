import os
import shutil
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from .user_manager import UserManager
from .permission_manager import PermissionManager


class Db:
    """Classe principale pour la gestion de base de données"""
    
    def __init__(self, db_path: str = ".database"):
        self.dbName = ""
        self.dbPath = db_path
        self.userManager = UserManager(self.dbPath)
        self.permManager = PermissionManager(self.dbPath)
        self.current_user = {"username": "root", "role": "admin"}
        
        # Créer le dossier de base de données s'il n'existe pas
        Path(self.dbPath).mkdir(exist_ok=True)

    # -----------------------------
    # DATABASE
    # -----------------------------
    def create_DB(self, dbName: str) -> bool:
        """
        Crée une nouvelle base de données
        
        Args:
            dbName: Nom de la base de données
            
        Returns:
            bool: True si créée avec succès, False sinon
        """
        if not dbName or not dbName.strip():
            print("❌ Database name cannot be empty")
            return False
        
        path = Path(f"{self.dbPath}/{dbName}")
        
        if path.exists():
            print(f"❌ Database '{dbName}' already exists")
            return False
        
        try:
            path.mkdir(parents=True, exist_ok=False)
            
            # Définir le créateur comme propriétaire avec tous les droits
            username = self.current_user["username"]
            self.permManager.set_owner(dbName, username)
            self.permManager.grant(
                dbName, "*", username, "ALL",
                caller_username=username,
                caller_role=self.current_user.get("role")
            )
            
            print(f"✓ Database '{dbName}' created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la création de la base de données: {e}")
            return False

    def list_database(self, path: str) -> List[str]:
        """
        Liste toutes les bases de données disponibles
        
        Args:
            path: Chemin du répertoire contenant les bases de données
            
        Returns:
            List[str]: Liste des noms de bases de données
        """
        directory = Path(path)
        
        if not directory.exists():
            return []
        
        return [
            item.name for item in directory.iterdir()
            if item.is_dir() and not item.name.startswith(".")
        ]

    def drop_database(self, databaseName: str) -> bool:
        """
        Supprime une base de données
        
        Args:
            databaseName: Nom de la base de données à supprimer
            
        Returns:
            bool: True si supprimée, False sinon
        """
        if not databaseName or not databaseName.strip():
            print("❌ Database name cannot be empty")
            return False
        
        path = Path(f"{self.dbPath}/{databaseName}")
        
        if not path.exists():
            print(f"❌ Database '{databaseName}' does not exist")
            return False
        
        if not path.is_dir():
            print(f"❌ '{databaseName}' is not a valid database")
            return False
        
        try:
            shutil.rmtree(path)
            
            # Cleanup associated permissions
            self.permManager.cleanup_database_permissions(databaseName)
            
            print(f"✓ Database '{databaseName}' removed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la suppression: {e}")
            return False

    def show_databases(self) -> None:
        """Affiche toutes les bases de données disponibles"""
        allDirs = self.list_database(self.dbPath)
        
        if not allDirs:
            print("📂 No databases found")
            return
        
        # Calculer la largeur pour l'affichage
        max_len = max([len(d) for d in allDirs] + [15])
        separator = "—" * (max_len + 4)
        
        print(separator)
        print(f"{'BASES DE DONNÉES':^{max_len + 4}}")
        print(separator)
        
        for db_name in sorted(allDirs):
            # Vérifier si l'utilisateur est propriétaire
            is_owner = self.permManager.get_owner(db_name)
            owner_mark = " 👑" if is_owner else ""
            print(f" {db_name:<{max_len}}{owner_mark}")
        
        print(separator)
        print(f"Total: {len(allDirs)} database{'s' if len(allDirs) > 1 else ''}")

    # -----------------------------
    # TABLES
    # -----------------------------
    def list_table(self, path: str) -> List[str]:
        """
        Liste toutes les tables dans une base de données
        
        Args:
            path: Chemin du répertoire de la base de données
            
        Returns:
            List[str]: Liste des noms de fichiers de tables
        """
        directory = Path(path)
        
        if not directory.exists():
            return []
        
        return [
            item.name for item in directory.iterdir()
            if item.is_file() and item.suffix == '.json' and not item.name.startswith(".")
        ]

    def create_Table(self, dbName: str, name: str, attribute: Dict[str, Any]) -> bool:
        """
        Crée une nouvelle table
        
        Args:
            dbName: Nom de la base de données
            name: Nom de la table
            attribute: Définition de la table (caractéristiques, contraintes, données)
            
        Returns:
            bool: True si créée avec succès, False sinon
        """
        if not name or not name.strip():
            print("❌ Table name cannot be empty")
            return False
        
        path = Path(f"{self.dbPath}/{dbName}/{name}.json")
        
        if path.exists():
            print(f"❌ Table '{name}' already exists")
            return False
        
        try:
            # Valider la structure de l'attribut
            if "caracteristique" not in attribute:
                print("❌ Table definition must include 'caracteristique'")
                return False
            
            # Initialize data if missing
            if "data" not in attribute:
                attribute["data"] = []
            
            # Sauvegarder la table
            with open(path, "w", encoding="utf-8") as f:
                json.dump(attribute, f, indent=2, ensure_ascii=False)
            
            # Grant ALL permissions to the creator
            username = self.current_user["username"]
            self.permManager.grant(
                dbName, name, username, "ALL",
                caller_username=username,
                caller_role=self.current_user.get("role")
            )
            print(f"✓ Table '{name}' created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error creating table: {e}")
            # Nettoyer en cas d'erreur
            if path.exists():
                path.unlink()
            return False

    def drop_table(self, dbName: str, tableName: str) -> bool:
        """
        Supprime une table
        
        Args:
            dbName: Nom de la base de données
            tableName: Nom de la table à supprimer
            
        Returns:
            bool: True si supprimée, False sinon
        """
        if not tableName or not tableName.strip():
            print("❌ Table name cannot be empty")
            return False
        
        path = Path(f"{self.dbPath}/{dbName}/{tableName}.json")
        
        if not path.exists():
            print(f"❌ Table '{tableName}' does not exist")
            return False
        
        try:
            path.unlink()
            
            # Cleanup table permissions
            self.permManager.cleanup_table_permissions(dbName, tableName)
            
            print(f"✓ Table '{tableName}' removed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la suppression: {e}")
            return False

    def analyse_data(self, path: str, data: List[str]) -> bool:
        """
        Ajoute des données dans une table
        
        Args:
            path: Chemin vers le fichier de la table
            data: Liste des valeurs à insérer (format: col=value)
            
        Returns:
            bool: True si ajoutées avec succès, False sinon
        """
        if not os.path.exists(path):
            print("❌ Table does not exist")
            return False
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = json.load(f)
            
            caracteristiques = content.get("caracteristique", {})
            # Normalize constraint tokens to lowercase for robust comparisons
            raw_constraints = content.get("constraint", {})
            constraints = {col: [c.lower() for c in (vals if isinstance(vals, list) else [vals])] for col, vals in raw_constraints.items()}
            
            if not caracteristiques:
                print("❌ Table has no defined columns")
                return False
            
            addedData = {}
            
            # Parser les données
            for i, item in enumerate(data):
                item = item.strip()
                
                if "=" not in item:
                    print(f"❌ Erreur de syntaxe dans '{item}' (format attendu: col=value)")
                    return False
                
                try:
                    col, value = item.split("=", 1)
                    col = col.strip()
                    value = value.strip().strip("'").strip('"')
                    
                    # Vérifier que la colonne existe
                    if col not in caracteristiques:
                        print(f"❌ La colonne '{col}' n'existe pas dans la table")
                        print(f"Colonnes disponibles: {', '.join(caracteristiques.keys())}")
                        return False
                    
                    addedData[col] = value
                    
                except ValueError:
                    print(f"❌ Erreur lors du parsing de '{item}'")
                    return False
            
            # Check NOT NULL constraints (case-insensitive)
            for col, constraint_list in constraints.items():
                if 'not_null' in constraint_list and col not in addedData:
                    print(f"❌ Column '{col}' cannot be NULL (NOT NULL constraint)")
                    return False
            
            # Check UNIQUE constraints
            existing_data = content.get("data", [])
            for col, constraint_list in constraints.items():
                if 'unique' in constraint_list and col in addedData:
                    for row in existing_data:
                        if row.get(col) == addedData[col]:
                            print(f"❌ UNIQUE constraint violation on column '{col}'")
                            return False
            
            # Append the new row
            content["data"].append(addedData)
            
            # Sauvegarder
            with open(path, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Data added successfully")
            return True
            
        except json.JSONDecodeError:
            print("❌ Corrupted JSON file")
            return False
        except Exception as e:
            print(f"❌ Error inserting data: {e}")
            return False

    def describe_table(self, path: str) -> bool:
        """
        Affiche la description d'une table
        
        Args:
            path: Chemin vers le fichier de la table
            
        Returns:
            bool: True si affichée, False sinon
        """
        if not os.path.exists(path):
            print("❌ Table does not exist")
            return False
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = json.load(f)
            
            caracteristiques = content.get("caracteristique", {})
            raw_constraints = content.get("constraint", {})
            constraints = {col: [c.lower() for c in (vals if isinstance(vals, list) else [vals])] for col, vals in raw_constraints.items()}
            data_count = len(content.get("data", []))
            
            if not caracteristiques:
                print("⚠️ Table has no defined columns")
                return True
            
            # Calculer les largeurs
            max_col_len = max([len(k) for k in caracteristiques.keys()] + [10])
            max_type_len = max([len(str(v)) for v in caracteristiques.values()] + [10])
            
            # En-tête
            separator = "—" * (max_col_len + max_type_len + 40)
            table_name = Path(path).stem
            
            print(separator)
            print(f"{'TABLE: ' + table_name.upper():^{len(separator)}}")
            print(separator)
            print(f"{'Column':<{max_col_len}} | {'Type':<{max_type_len}} | Constraints")
            print(separator)
            
            # Afficher chaque colonne
            for col, col_type in caracteristiques.items():
                constraint_list = constraints.get(col, ["no constraint"])
                
                # Format constraints for display (capitalize tokens)
                if isinstance(constraint_list, list):
                    if "no constraint" in constraint_list:
                        constraint_str = "None"
                    else:
                        constraint_str = ", ".join([c.upper() if len(c) <= 6 else c for c in constraint_list])
                else:
                    constraint_str = str(constraint_list)
                
                print(f"{col:<{max_col_len}} | {col_type:<{max_type_len}} | {constraint_str}")
            
            print(separator)
            print(f"Total: {len(caracteristiques)} column{'s' if len(caracteristiques) > 1 else ''}, {data_count} row{'s' if data_count > 1 else ''}")
            print(separator)
            
            return True
            
        except json.JSONDecodeError:
            print("❌ Fichier JSON corrompu")
            return False
        except Exception as e:
            print(f"❌ Erreur lors de la lecture: {e}")
            return False

    def table_exists(self, dbName: str, tableName: str) -> bool:
        """Vérifie si une table existe"""
        path = Path(f"{self.dbPath}/{dbName}/{tableName}.json")
        return path.exists()

    def get_table_info(self, dbName: str, tableName: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les informations d'une table
        
        Returns:
            Dict contenant les informations ou None si erreur
        """
        path = Path(f"{self.dbPath}/{dbName}/{tableName}.json")
        
        if not path.exists():
            return None
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    # -----------------------------
    # HELP
    # -----------------------------
    def show_help(self) -> None:
        """Affiche l'aide des commandes disponibles"""
        help_text = """
        ╔══════════════════════════════════════════════════════════════╗
        ║               COMMANDES DISPONIBLES - MY SGBD                ║
        ╚══════════════════════════════════════════════════════════════╝

        📦 BASES DE DONNÉES
        create_database <nom>              Créer une nouvelle base de données
        create_db <nom>                    Alias pour create_database
        drop_database <nom>                Supprimer une base de données
        drop_db <nom>                      Alias pour drop_database
        use_database <nom>                 Sélectionner une base de données
        use_db <nom>                       Alias pour use_database
        leave_database                     Quitter la base actuelle
        leave_db                           Alias pour leave_database
        list_database                      Lister toutes les bases
        list_db                            Alias pour list_database
        stats_db                           Statistiques de la base active
        database_stats                     Alias pour stats_db

        📋 TABLES
        create_table <nom>(col:type[constraint], ...)
                                            Créer une nouvelle table
        add_into_table <table>(col=val, ...)
                                            Insérer des données
        drop_table <nom>                   Supprimer une table
        list_table                         Lister les tables de la BD active
        describe_table <nom>               Décrire la structure d'une table

        🔍 REQUÊTES
        select <cols> from <table> [where <condition>]
                                            Interroger les données
        update <table> set col=val [where <condition>]
                                            Modifier des données
        delete from <table> [where <condition>]
                                            Supprimer des données

        👤 UTILISATEURS
        create_user <nom> password=<pwd> [role=<role>]
                                            Créer un utilisateur (role: user|admin)
        list_user                          Lister les utilisateurs
        drop_user <nom>                    Supprimer un utilisateur
        switch_user_to <nom> password=<pwd>
                                            Changer d'utilisateur

        🔐 PERMISSIONS
        grant <perm> on <table|db.*|*> to <user>
                                            Accorder une permission
        revoke <perm> on <table|db.*|*> from <user>
                                            Révoquer une permission
        show_grants <user>                 Afficher les permissions d'un user
        show_grants <db> <user>            Afficher les permissions sur une DB

        ⚙️  SYSTÈME
        help                               Afficher cette aide
        list_commands                      Alias pour help
        commands                           Alias pour help
        clear                              Nettoyer l'écran
        exit                               Quitter le SGBD

        📖 TYPES DE DONNÉES
        date, year, time, datetime, bool, number, float, string, text, bit

        🔒 CONTRAINTES
        not_null, unique, primary_key, foreign_key, check, default, 
        auto_increment

        🔑 PERMISSIONS DISPONIBLES
        SELECT, INSERT, UPDATE, DELETE, DROP, ALL, USAGE

        🔎 OPÉRATEURS WHERE
        =, !=, >, <, >=, <=, LIKE (avec % et _ comme wildcards)

        💡 EXEMPLES
        # Gestion des bases
        create_database ma_db;
        use_db ma_db;
        stats_db;
        
        # Création de table
        create_table users(
            id:number[primary_key,auto_increment],
            nom:string[not_null,unique],
            age:number,
            email:string
        );
        
        # Insertion de données
        add_into_table users(id=1, nom=Alice, age=25, email=alice@test.com);
        add_into_table users(id=2, nom=Bob, age=30);
        
        # Requêtes SELECT
        select * from users;
        select nom, age from users;
        select * from users where age > 25;
        select * from users where nom LIKE %Ali%;
        
        # Mise à jour
        update users set age=26 where nom=Alice;
        update users set email=bob@test.com where id=2;
        
        # Suppression
        delete from users where age < 18;
        
        # Gestion des utilisateurs
        create_user alice password=secret123 role=user;
        switch_user_to alice password=secret123;
        
        # Gestion des permissions
        grant SELECT on users to alice;
        grant ALL on ma_db.* to bob;
        revoke DELETE on users from alice;
        show_grants alice;

        📝 NOTES
        • Toutes les commandes se terminent par un point-virgule (;)
        • Les commandes multi-lignes sont supportées
        • Les noms de colonnes/tables : [a-zA-Z_][a-zA-Z0-9_]*
        • Les mots de passe sont hashés avec SHA-256
        • L'utilisateur 'root' est admin par défaut
        • Les admins ont tous les droits sur toutes les bases

        ════════════════════════════════════════════════════════════════
        """
        print(help_text)
    # -----------------------------
    # UTILITAIRES
    # -----------------------------
    def get_statistics(self, dbName: str) -> Dict[str, Any]:
        """
        Récupère des statistiques sur une base de données
        
        Returns:
            Dict avec les statistiques
        """
        stats = {
            "database": dbName,
            "tables": 0,
            "total_rows": 0,
            "total_columns": 0
        }
        
        path = Path(f"{self.dbPath}/{dbName}")
        
        if not path.exists():
            return stats
        
        tables = self.list_table(str(path))
        stats["tables"] = len(tables)
        
        for table_file in tables:
            table_path = path / table_file
            try:
                with open(table_path, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    stats["total_rows"] += len(content.get("data", []))
                    stats["total_columns"] += len(content.get("caracteristique", {}))
            except Exception:
                continue
        
        return stats