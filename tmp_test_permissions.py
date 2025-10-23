from db.db_main import Db
import os, shutil
# clean
if os.path.exists('.database'): shutil.rmtree('.database')
# init
d=Db()
# create db as root
print('create db testdb')
d.create_DB('testdb')
# create user alice
print('create user alice')
d.userManager.create_user('alice','pass')
# simulate login as alice
alice = d.userManager.use_user('alice','pass')
print('alice:', alice)
# attempt to use database as alice without any grants
if alice:
    d.current_user = alice
    dirs = d.list_database('.database')
    print('list db:', dirs)
    if 'testdb' in dirs:
        # simulate main's use_database permission check
        current_username = d.current_user.get('username')
        role = d.current_user.get('role')
        if role == 'admin' or d.permManager.has_db_permission('testdb', current_username, 'ALL') or d.permManager.has_db_permission('testdb', current_username, 'USAGE'):
            print("alice can 'use' testdb (permission granted)")
        else:
            print("alice denied to 'use' testdb (permission denied)")
# try to create table as alice
print('alice create table t1')
# check permission for create
if alice:
    current_username = d.current_user.get('username')
    role = d.current_user.get('role')
    if role == 'admin' or d.permManager.has_db_permission('testdb', current_username, 'ALL') or d.permManager.has_table_permission('testdb','t1', current_username, 'ALL'):
        d.create_Table('testdb','t1',{'caracteristique':{},'constraint':{},'data':[]})
        print('table created')
    else:
        print('permission denied to create table')
print('files in testdb:', os.listdir('.database/testdb') if os.path.exists('.database/testdb') else [])
