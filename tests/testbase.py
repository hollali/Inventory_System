import atexit
import os
import shutil
import sqlite3
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

TEMP_DIR = tempfile.mkdtemp(prefix='inventory_test_')
DB_PATH = os.path.join(TEMP_DIR, 'inventory_system.db')
os.environ['INVENTORY_DB_FILE'] = DB_PATH


def _cleanup():
    try:
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
    finally:
        os.environ.pop('INVENTORY_DB_FILE', None)


atexit.register(_cleanup)

import app_log
app_log.setup_logging()

from database import commit, connect_database, execute, hash_password

import crud
crud.messagebox.showerror = lambda title, msg: print('ERR:', msg)
crud.messagebox.showinfo = lambda title, msg: print('INFO:', msg)
crud.messagebox.askyesno = lambda title, msg: True

import movements
import employee, suppliers, categories, products, sales, purchases, customers, returns
import login
import reports


def conn():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def seed_users():
    connect_database()
    for empid, name, usertype, password in (
            (1, 'Hollali Kelvin', 'Admin', 'admin123'),
            (2, 'Ama Addai', 'Employee', 'pw')):
        execute(
            'INSERT OR REPLACE INTO employee_data '
            '(empid, name, gender, email, number, dob, salary, address, usertype, password) '
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (empid, name, '', '', '', '', 0, '', usertype, hash_password(password)))
    commit()


seed_users()
