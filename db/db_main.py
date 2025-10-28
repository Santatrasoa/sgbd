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
            print("❌ Le nom de la base de données ne peut pas être vide")
            return False
        
        path = Path(f"{self.dbPath}/{dbName}")
        
        if path.exists():
            print(f"❌ La base de données '{dbName}' existe déjà")
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
            
            print(f"✓ Base de données '{dbName}' créée avec succès")
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
            print("❌ Le nom de la base de données ne peut pas être vide")
            return False
        
        path = Path(f"{self.dbPath}/{databaseName}")
        
        if not path.exists():
            print(f"❌ La base de données '{databaseName}' n'existe pas")
            return False
        
        if not path.is_dir():
            print(f"❌ '{databaseName}' n'est pas une base de données valide")
            return False
        
        try:
            shutil.rmtree(path)
            
            # Nettoyer les permissions associées
            self.permManager.cleanup_database_permissions(databaseName)
            
            print(f"✓ Base de données '{databaseName}' supprimée avec succès")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la suppression: {e}")
            return False

    def show_databases(self) -> None:
        """Affiche toutes les bases de données disponibles"""
        allDirs = self.list_database(self.dbPath)
        
        if not allDirs:
            print("📂 Aucune base de données trouvée")
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
        print(f"Total: {len(allDirs)} base{'s' if len(allDirs) > 1 else ''} de données")

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
            print("❌ Le nom de la table ne peut pas être vide")
            return False
        
        path = Path(f"{self.dbPath}/{dbName}/{name}.json")
        
        if path.exists():
            print(f"❌ La table '{name}' existe déjà")
            return False
        
        try:
            # Valider la structure de l'attribut
            if "caracteristique" not in attribute:
                print("❌ La définition de la table doit contenir 'caracteristique'")
                return False
            
            # Initialiser les données si absentes
            if "data" not in attribute:
                attribute["data"] = []
            
            # Sauvegarder la table
            with open(path, "w", encoding="utf-8") as f:
                json.dump(attribute, f, indent=2, ensure_ascii=False)
            
            # Accorder tous les droits au créateur
            username = self.current_user["username"]
            self.permManager.grant(
                dbName, name, username, "ALL",
                caller_username=username,
                caller_role=self.current_user.get("role")
            )
            
            print(f"✓ Table '{name}' créée avec succès")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la création de la table: {e}")
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
            print("❌ Le nom de la table ne peut pas être vide")
            return False
        
        path = Path(f"{self.dbPath}/{dbName}/{tableName}.json")
        
        if not path.exists():
            print(f"❌ La table '{tableName}' n'existe pas")
            return False
        
        try:
            path.unlink()
            
            # Nettoyer les permissions de la table
            self.permManager.cleanup_table_permissions(dbName, tableName)
            
            print(f"✓ Table '{tableName}' supprimée avec succès")
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
            print("❌ La table n'existe pas")
            return False
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = json.load(f)
            
            caracteristiques = content.get("caracteristique", {})
            constraints = content.get("constraint", {})
            
            if not caracteristiques:
                print("❌ La table n'a pas de colonnes définies")
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
            
            # Vérifier les colonnes manquantes avec contrainte NOT NULL
            for col, constraint_list in constraints.items():
                if "Not_null" in constraint_list and col not in addedData:
                    print(f"❌ La colonne '{col}' ne peut pas être NULL (contrainte NOT NULL)")
                    return False
            
            # Vérifier les colonnes UNIQUE
            existing_data = content.get("data", [])
            for col, constraint_list in constraints.items():
                if "Unique" in constraint_list and col in addedData:
                    for row in existing_data:
                        if row.get(col) == addedData[col]:
                            print(f"❌ Violation de contrainte UNIQUE sur la colonne '{col}'")
                            return False
            
            # Ajouter les données
            content["data"].append(addedData)
            
            # Sauvegarder
            with open(path, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Données ajoutées avec succès")
            return True
            
        except json.JSONDecodeError:
            print("❌ Fichier JSON corrompu")
            return False
        except Exception as e:
            print(f"❌ Erreur lors de l'ajout des données: {e}")
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
            print("❌ La table n'existe pas")
            return False
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = json.load(f)
            
            caracteristiques = content.get("caracteristique", {})
            constraints = content.get("constraint", {})
            data_count = len(content.get("data", []))
            
            if not caracteristiques:
                print("⚠️ La table n'a pas de colonnes définies")
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
            print(f"{'Colonne':<{max_col_len}} | {'Type':<{max_type_len}} | Contraintes")
            print(separator)
            
            # Afficher chaque colonne
            for col, col_type in caracteristiques.items():
                constraint_list = constraints.get(col, ["Aucune"])
                
                # Formater les contraintes
                if isinstance(constraint_list, list):
                    if "no constraint" in constraint_list:
                        constraint_str = "Aucune"
                    else:
                        constraint_str = ", ".join(constraint_list)
                else:
                    constraint_str = str(constraint_list)
                
                print(f"{col:<{max_col_len}} | {col_type:<{max_type_len}} | {constraint_str}")
            
            print(separator)
            print(f"Total: {len(caracteristiques)} colonne{'s' if len(caracteristiques) > 1 else ''}, {data_count} ligne{'s' if data_count > 1 else ''}")
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

📋 TABLES
  create_table <nom>(col:type[constraint], ...)
                                     Créer une nouvelle table
  add_into_table <table>(col=val, ...)
                                     Insérer des données
  drop_table <nom>                   Supprimer une table
  list_table                         Lister les tables de la BD active
  describe_table <nom>               Décrire la structure d'une table

🔍 REQUÊTES
  select <colonnes> from <table> [where <condition>]
                                     Interroger les données
  update <table> set col=val [where <condition>]
                                     Modifier des données
  delete from <table> [where <condition>]
                                     Supprimer des données

👤 UTILISATEURS
  create_user <nom> password=<pwd> [role=<role>]
                                     Créer un utilisateur
  list_user                          Lister les utilisateurs
  drop_user <nom>                    Supprimer un utilisateur
  switch_user_to <nom> password=<pwd>
                                     Changer d'utilisateur

🔐 PERMISSIONS
  grant <perm> on <table|*> to <user>
                                     Accorder une permission
  revoke <perm> on <table|*> from <user>
                                     Révoquer une permission
  show_grants <user>                 Afficher les permissions

⚙️  SYSTÈME
  help                               Afficher cette aide
  clear                              Nettoyer l'écran
  exit                               Quitter le SGBD

📖 TYPES DE DONNÉES
  date, year, time, datetime, bool, number, float, string, text, bit

🔒 CONTRAINTES
  not_null, unique, primary_key, foreign_key, check, default, auto_increment

🔎 OPÉRATEURS WHERE
  =, !=, >, <, >=, <=, LIKE (avec % et _)

💡 EXEMPLES
  create_database ma_db;
  use_db ma_db;
  create_table users(id:number[primary_key], nom:string[not_null]);
  add_into_table users(id=1, nom=Alice);
  select * from users where nom = Alice;
  update users set nom=Bob where id = 1;
  grant SELECT on users to alice;

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