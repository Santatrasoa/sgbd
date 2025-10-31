# utils/helpers.py
import hashlib
import re
import json
import os

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def validate_table_name(name: str):
    if not name or not name.strip():
        return False, "name is empty"
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        return False, "must start with a letter or '_' and contain only letters, digits and '_'"
    return True, ""

def split_top_level_commas(s: str):
    parts = []
    buf = []
    depth = 0
    in_single = in_double = False
    for ch in s:
        if ch == "'" and not in_double:
            in_single = not in_single
            buf.append(ch)
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            buf.append(ch)
            continue
        if in_single or in_double:
            buf.append(ch)
            continue
        if ch == '[': depth += 1
        if ch == ']': depth = max(0, depth - 1)
        if ch == ',' and depth == 0:
            part = ''.join(buf).strip()
            if part: parts.append(part)
            buf = []
            continue
        buf.append(ch)
    last = ''.join(buf).strip()
    if last: parts.append(last)
    return parts

def parse_where_clause(where_clause, all_rows):
    if where_clause is None:
        return all_rows
    where_clause = where_clause.strip()
    if not where_clause:
        return all_rows
    operators = ['>=', '<=', '!=', '=', '>', '<', ' LIKE ', ' like ']
    operator = None
    for op in operators:
        if op in where_clause:
            operator = op.strip()
            split_op = op
            break
    if not operator:
        print("Unrecognized operator in WHERE. Supported: =, !=, >, <, >=, <=, LIKE")
        return []
    try:
        left, right = where_clause.split(split_op, 1)
        left = left.strip()
        right = right.strip().strip("'").strip('"')
        filtered = []
        for row in all_rows:
            value = str(row.get(left, ""))
            if operator == '=':
                if value == right: filtered.append(row)
            elif operator == '!=':
                if value != right: filtered.append(row)
            elif operator == '>':
                try:
                    if float(value) > float(right): filtered.append(row)
                except ValueError:
                    if value > right: filtered.append(row)
            elif operator == '<':
                try:
                    if float(value) < float(right): filtered.append(row)
                except ValueError:
                    if value < right: filtered.append(row)
            elif operator == '>=':
                try:
                    if float(value) >= float(right): filtered.append(row)
                except ValueError:
                    if value >= right: filtered.append(row)
            elif operator == '<=':
                try:
                    if float(value) <= float(right): filtered.append(row)
                except ValueError:
                    if value <= right: filtered.append(row)
            elif operator.upper() == 'LIKE':
                pattern = right.replace('%', '.*').replace('_', '.')
                if re.search(pattern, value, re.IGNORECASE):
                    filtered.append(row)
        return filtered
    except Exception as e:
        print(f"Error parsing WHERE clause: {e}")
        return []
