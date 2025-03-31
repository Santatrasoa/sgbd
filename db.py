import Action
from pathlib import Path
import os, shutil, json
from datetime import datetime

class Db :
    def __init__(self):
        self.dbName = ""

    def create_DB(self, dbName):
        action = Action.Action(self.dbName)
        dirs = self.list_database(".database/")
        if dbName in dirs:
            print("database already exist")
        else:
            action.creer_dossier(".database/"+dbName)
    
    def create_Table(self, dbName, name ,attribute):
        #action = Action.Action(".database/"+self.dbName)
        files = self.list_table(".database/"+dbName.strip())
        isTableFound = False
        for i in files:
            if name.strip() == i.split(".")[0].strip():
                    isTableFound = True
                    break
        if isTableFound == False:
            action = Action.Action(".database/"+self.dbName.strip())
            action.creer_fichier(".database/"+dbName, name, attribute)
        
        else:
            print(f"Table {name} already exist")

    def list_database(self,path):
        directory = Path(path)
        dirs = [item.name for item in directory.iterdir() if item.is_dir()]
        return dirs
    
    def list_table(self, tableName):
        directory = Path(tableName)
        dirs = [item.name for item in directory.iterdir() if item.is_file()]
        return dirs

    def insert_into(self, table, data):
        
        pass

    def select_into(self, table, colomn):
        print("I work")

    def drop_database(self, databaseName):
        try:
            directory = Path(".database/"+databaseName)
            if directory.exists and directory.is_dir():
                shutil.rmtree(directory)
                print(f"database {databaseName} removed")
            else:
                print("Database does not exist")
        except Exception as e:
            print(f"can not remove this database ",e)

    def drop_table(self, dbName, tableName):
        a = ".database/"+dbName.strip()+"/"+tableName.strip()+".json"
        file_path = Path(a)
        if file_path.exists() and file_path.is_file():
            file_path.unlink()  # Removes the file
            print(f"table {tableName} removed")
        else:
            print(f"table {tableName} does not exist")

    def show_databases(self):
        allDirs = self.list_database(".database/")
        l = 9
        for i in allDirs:
            if l < len(i):
                l = len(i)

        if (len(allDirs) > 0):
            print("", "—"*((l)*2), sep="")
            print(" "*(int(l/2)),"database")
            print("—"*(l*2),)

            for i in allDirs:
                print(" "*(int(l/2)),i)
            print("—"*(l*2), "",sep="")
        else:
            print("empty :(")

    def analyse_data(self, path, data):
        contentTable = {}
        addedData = {}
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                contentTable = json.load(f)
        
        typeOfData = list(contentTable["caracteristique"].values())
        nameOfData = list(contentTable["caracteristique"].keys())

        if len(data) == len(typeOfData):
            isSecondPartExist = True
            verifyType = True
            allDataThemeSame = True

            for i in range(len(data)):
                tmpData = data[i].split("=")
                
                # Vérification de la présence du '=' dans les données
                if len(tmpData) != 2 or tmpData[1] == "":
                    isSecondPartExist = False
                    break

                if nameOfData[i].strip() == tmpData[0].strip():
                    # Validation selon le type de données
                    if typeOfData[i] == "Number" and not tmpData[1].isdigit():
                        verifyType = False
                        break
                    elif typeOfData[i] == "Float":
                        try:
                            float(tmpData[1])  # Vérification si c'est un float
                        except ValueError:
                            verifyType = False
                            break
                    elif typeOfData[i] == "Year" and (not tmpData[1].isdigit() or len(tmpData[1]) != 4):
                        verifyType = False
                        break
                    elif typeOfData[i] == "Bool" and tmpData[1] not in ["True", "False"]:
                        verifyType = False
                        break
                    elif typeOfData[i] == "Date":
                        try:
                            datetime.strptime(tmpData[1], "%Y/%m/%d")  # Date au format YYYY/MM/DD
                        except ValueError:
                            verifyType = False
                            break
                    elif typeOfData[i] == "Datetime":
                        try:
                            datetime.strptime(tmpData[1], "%Y/%m/%d %H:%M:%S")  # Datetime au format YYYY/MM/DD HH:MM:SS
                        except ValueError:
                            verifyType = False
                            break
                    elif typeOfData[i] == "Time":
                        try:
                            datetime.strptime(tmpData[1], "%H:%M:%S")  # Heure au format HH:MM:SS
                        except ValueError:
                            verifyType = False
                            break
                    elif typeOfData[i] == "String" and not tmpData[1]:  # String (non vide)
                        verifyType = False
                        break
                    elif typeOfData[i] == "Text" and not tmpData[1]:  # Text (non vide, peut être long)
                        verifyType = False
                        break
                    elif typeOfData[i] == "Bit" and tmpData[1] not in ["0", "1"]:
                        verifyType = False
                        break

                    # Ajouter les données validées
                    addedData[tmpData[0]] = tmpData[1]
                else:
                    allDataThemeSame = False
                    break

            if not allDataThemeSame or not isSecondPartExist or not verifyType:
                print(allDataThemeSame)
                print(isSecondPartExist)
                print(verifyType)
                print("Syntaxe error")
            else:
                contentTable["data"].append(addedData)
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(contentTable, f, indent=4)
                print("Data added")
                pass
        else:
            print("Syntax Error")
