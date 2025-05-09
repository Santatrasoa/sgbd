import db
import readline, os

allType = ["Date", "Year", "Time", "Datetime", "Bool", "Number", "Float", "String", "Text", "Bit"]
constraints = ["Not_null", "Unique", "Primary_key", "Foreign_key", "Check", "Default", "Auto_increment"]
db = db.Db()
useDatabase = ""
isDbUse = False
userUsingDb = "user:\033[32mroot\033[0m"
promptContainte = "[" + userUsingDb + "]\nm¥⇒ "

print("Welcome to my. We hope that you enjoy using our database")

readline.read_history_file(".history")

while True:
    print("")
    try:
        cmd = input("my ~ " + promptContainte)

    except KeyboardInterrupt:
        print("\n^C")
        continue

    except EOFError:
        readline.write_history_file(".history")
        print("\nBye! It was my")
        exit()

    if cmd.strip() == "clear" or cmd == "clear;":
        os.system("clear")
        continue

    if cmd.strip() == "exit" or cmd == "exit;":
        readline.write_history_file(".history")
        print("Bye! It was my")
        exit()

    while not cmd.endswith(";"):
        try:
            next_line = input(" ⇘ ")
        except KeyboardInterrupt:
            print("\n^C")
            break
        
        except EOFError:
            print("\nBye! It was my")
            readline.write_history_file(".history")
            exit()
        cmd += next_line.strip()

    cmd = cmd.replace(";", "")
    cmd_line = cmd.split(" ")[0].lower()

    if cmd_line == "clear":
        os.system("clear")
        continue
    if cmd_line == "exit":
        readline.write_history_file(".history")
        print("Bye! It was my")
        exit()

    if cmd_line.startswith("create_database") or cmd_line.startswith("create_db"):
        dbName = ""
        if cmd_line.startswith("create_database"):dbName = cmd[16:].strip()
        else:dbName = cmd[9:].strip()
        db.create_DB(dbName)

    elif cmd_line.startswith("use_database") or cmd_line.startswith("use_db"):
        if cmd_line.startswith("use_database"): useDatabase = cmd[12:].strip()
        else:useDatabase = cmd[6:].strip()
        dirs = db.list_database(".database/")
        if useDatabase in dirs:
            print(f"database '{useDatabase}' used")
            promptContainte = f"[{userUsingDb} & db:\033[34m{useDatabase}\033[0m]\nm¥⇒ "
            isDbUse = True
        else:
            print(f"database {useDatabase} doesn't exist")

    elif cmd_line.startswith("create_table"):
        flags = False
        isConstraintTrue = False
        attribute1 = {}
        getConstraint = {}
        if isDbUse:
            if "(" in cmd and cmd.count('(') == 1 and cmd.count(')') == 1:
                name = cmd.split(" ")[1].split('(')[0]
                cmd = cmd.replace(")", "")
                data = cmd.split('(')[1].split(',')
                attribute = {}
                getType = ""
                if len(cmd.split('(')) == 2 and len(data) > 0:
                    for val in data:
                        values = val.strip().split(':')    
                        getType = ""
                        if "[" in values[1]:
                            constraint = values[1].split('[')[1].replace(']', "").strip()
                            if constraint == "":
                                constraint = "no_constraint"
                            for con in constraints:
                                c = constraint.split(' ')
                                if len(c) > 1:
                                    for i in c:
                                        if i.strip().capitalize() == con.strip().capitalize() or constraint == "no_constraint":
                                            isConstraintTrue = True
                                            break
                                else:
                                    if constraint.strip().capitalize() != con.strip().capitalize() and constraint != "no_constraint":
                                        isConstraintTrue = True
                                        break
                            if isConstraintTrue:
                                getConstraint[values[0]] = constraint
                            getType = values[1].split('[')[0].strip().capitalize()
                        else:
                            getConstraint[values[0]] = "no constraint"
                            getType = values[1].strip().capitalize()

                        attribute[values[0]] = values[1].capitalize()
                        for type in allType:
                            if type.strip() == getType.strip():
                                flags = True
                                break
                    if not flags:
                        print("!!! type error !!!")
                    elif not isConstraintTrue:
                        print("!!! constraint error !!!")

                    else:
                        attribute1["caracteristique"] = attribute
                        attribute1["constraint"] = getConstraint
                        attribute1["data"] = []
                        db.create_Table(useDatabase, name, attribute1)
                else:
                    print("\n\033[31m!!! syntaxe error !!!\033[0m\n")
            else:
                print("\033[31m!!! syntaxe error !!!\033[0m")
        else:
            print("no database used")

    elif cmd_line.startswith("add_into_table"):
        if isDbUse == True:
            getRequests = cmd.split(" ")[1:]
            getRequest=" ".join(getRequests).strip()

            if len(getRequest) == 0: print("syntaxe error")
            else:
                getData = getRequest.split("(")
                path = ".database/" + useDatabase.strip()
                allTable = db.list_table(path)
                isTableExist = False


                for table in allTable:
                    if table.split('.')[0].strip() == getData[0].strip():
                        isTableExist = True

                if isTableExist:
                    if cmd.count("(") > 2 or cmd.count(')') > 2 or cmd.count("(") == 0 or cmd.count(')') == 0: print("syntaxe error")
                    else:
                        getData[1] = getData[1].replace(')', "")
                        verifyData = getData[1].split(',')
                        pathToFile = path+'/'+getData[0].strip()+".json"
                        db.analyse_data(pathToFile,verifyData)
                        pass
        else:
            print("no database selected")

        #db.insert_into("loop", {"mimi": 1})

    elif cmd_line.startswith("drop_database") or cmd_line.startswith("drop_db"):
        databaseToRemove = ""
        if cmd_line.startswith("drop_database "):
            databaseToRemove = cmd[13:].strip()
        else:
            databaseToRemove = cmd[7:].strip()
        if databaseToRemove == useDatabase:
            print("This database is in use.\ntype: \"leave db\" or choose another database and try again")
        else:
            db.drop_database(databaseToRemove)

    elif cmd_line.startswith("leave_db") or cmd_line.startswith("leave_database"):
        useDatabase = ""
        isDbUse = False
        promptContainte = f"[{userUsingDb}]\n¥⇒ "

    elif cmd_line.startswith("drop_table"):
        if isDbUse:
            tableToRemove = cmd[10:].strip()
            db.drop_table(useDatabase, tableToRemove)

    elif cmd_line.startswith("list_database") or cmd_line.startswith("list_db"):
        db.show_databases()

    elif cmd_line.startswith("list_table"):
        if isDbUse:
            path = ".database/" + useDatabase.strip()
            tables = db.list_table(path)
            length = "list table " + useDatabase;
            l=len(length)
            for i in tables:
                if len(i) > l:
                    l = len(i)

            if len(tables) > 0:
                print("—"*((l)*2))
                print(" "*(int(l/2)), "list table in", useDatabase)
                print("—"*((l)*2), sep="")
                
                for i in tables:
                    print(" "*(int(l/2)),i.split('.')[0])
                
                print("—"*((l)*2))

            else:
                print(" empty table :(")
        else:
            print("no database selected")

    elif cmd_line.startswith("describe_table"):
        if isDbUse:
            tableToDescribe = cmd[15:].strip()
            path = ".database/" + useDatabase.strip()
            pathToFile = path+'/'+tableToDescribe.strip()+".json"
            db.describe_table(pathToFile)
        else:
            print("no database selected")

    else:
        print("commande not found")
