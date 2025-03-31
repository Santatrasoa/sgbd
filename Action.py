import os, json
from pathlib import Path

class Action :
    def __init__(self, dossier):
        self.dossier = dossier
        self.fichier = ""
        self.chemin_complet = os.path.join(self.dossier, self.fichier)

    def creer_dossier(self, dossier):
        """Créer un dossier s'il n'existe pas."""
        if not os.path.exists(dossier):
            os.makedirs(dossier)
            print(f"Database '{dossier.split('/')[1].strip()}' created.")
        else:
            print(f"Database '{dossier}' already exist.")

    def creer_fichier(self,dossier,nameFile,data):
        fileCreated = os.path.join(dossier, nameFile+".json")
        with open(fileCreated, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
            print(f"Table '{nameFile}' created.")

    def lire_fichier (self):
        """Lire et afficher le contenu du fichier JSON."""
        if os.path.exists(self.chemin_complet):
            with open(self.chemin_complet, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        else:
            print("Le fichier JSON n'existe pas.")
            return None
    
def list_return_dir(path):
    directory = Path(path)
    dirs = [item for item in directory.iterdir() if item.is_dir()]
    return dirs
        
def list_return_file(path):
    directory = Path(path)
    file = [item for item in directory.iterdir() if item.is_file()]
    return file

