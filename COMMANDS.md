# SGBD Commands

This file lists the available REPL commands implemented in the project.

## Session & Authentication

- `switch_to <username> [password=...] ;` — Switch user (password will be prompted if not provided)
- `exit ;` — Exit the program
- `clear ;` — Clear the console

## Databases

- `create_db <name> ;` — Create a database
- `use_db <name> ;` — Select a database (requires USAGE permission)
- `leave_db ;` — Leave the current database
- `drop_db <name> ;` — Drop a database (confirmation required)
- `list_database ;` — List databases
- `stats_db ;` — Show database statistics for the selected database

## Tables / Schema

- `create_table <name>(col:type[constraints], ...);` — Create a table
  - Example: `create_table users(id:number[primary_key], name:string[not_null]);`
- `add_into_table <table>(col=value, ...);` — Insert a row
  - Example: `add_into_table users(id=1, name='Alice');`
- `list_table ;` — List tables in current database
- `describe_table <table> ;` — Show columns, types, constraints, row count
- `drop_table <table> ;` — Drop a table (confirmation required)

## ALTER TABLE

- `alter_table <table> ADD COLUMN col:type[constraints];` — Add a column
- `alter_table <table> DROP COLUMN <col>;` — Drop a column
- `alter_table <table> RENAME COLUMN <old> TO <new>;` — Rename a column
- `alter_table <table> MODIFY COLUMN <col>:<type>[...];` — Modify a column
- `alter_table <table> RENAME TO <new_name>;` — Rename the table

## Query operations

- `select <cols> from <table> [where <cond>];` — Read rows (supports `*` or column list)
- `update <table> set col=val [, ...] [where <cond>];` — Update rows
- `delete from <table> [where <cond>];` — Delete rows

## Users & Permissions

- `create_user <username> [role=user|admin];` — Create user (password prompted)
- `list_user ;` — List users
- `drop_user <username> ;` — Drop a user (confirmation required)
- `grant <perm[,perm,...]> on <table|db.table|*> to <user> ;` — Grant permissions
  - Example: `grant SELECT on users to alice;`
- `revoke <perm> on <table|db.table|*> from <user> ;` — Revoke permissions
- `show_grants <user>` or `show_grants <db> <user>` — Show grants for a user

## Notes

- Commands are terminated with `;` (multi-line input supported until `;`).
- Table files live in `<db>/<table>.enc` and are encrypted.
- Permission checks use `db.permManager` and `db.current_user["role"]`.
- Types and constraints are configured in `config.json` (`allowed_data_types`, `allowed_constraints`).
