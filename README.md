# SGBD (simple encrypted DB)

Small educational DBMS that stores encrypted table files on disk and provides a REPL to manage databases, tables, users and permissions.

## Features

- Encrypted table files stored under `<db>/<table>.enc`.
- User and permission management (grant/revoke/show grants).
- Basic SQL-like operations: `select`, `update`, `delete`.
- Schema management: `create_table`, `alter_table`, `describe_table`.
- Command-line REPL with per-user history.

## Quick start

Prerequisites

- Python 3.11+ (the project uses features compatible with 3.11+)
- Install dependencies from `requirements.txt` (if present):

```bash
pip install -r requirements.txt
```

Run the REPL

```bash
python main.py
```

At startup you'll be asked to login. The default admin user is defined in `config/config.json`.

## Commands

A complete list of commands and examples is available in `COMMANDS.md` and via the in-REPL help:

- In REPL: `help;` or `list_commands;`
- See file: `COMMANDS.md`

## Project structure

- `main.py` - application entry point and REPL loop
- `db/` - core DB logic (table handling, user manager, permission manager)
- `commands/` - command handlers that the REPL dispatches to
- `utils/` - helpers, crypto manager, configuration loader
- `config/config.json` - configuration (types, constraints, default admin, paths)

## Notes & Development

- Tables are encrypted with `utils.crypto.CryptoManager`; default master password is set in `main.py` for local dev — replace for production.
- Permission logic lives in `db/permission_manager.py` and is checked by command handlers.

If you want I can also add a small example database and tests to demonstrate the project.
