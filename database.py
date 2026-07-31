import configparser
import hashlib
import os
import shutil
import sqlite3
from datetime import datetime

CONFIG_FILE = 'config.ini'
PASSWORD_SALT = 'inventory-system-v1'

_EMPLOYEE_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS employee_data (
    empid INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    gender VARCHAR(20),
    email VARCHAR(255),
    number VARCHAR(50),
    dob TEXT,
    salary REAL,
    address TEXT,
    usertype VARCHAR(50),
    password TEXT
)'''

_SCHEMA_SQL = [
    _EMPLOYEE_TABLE_SQL,
    '''
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT
)''',
    '''
CREATE TABLE IF NOT EXISTS categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT
)''',
    '''
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE,
    category_id INTEGER,
    supplier_id INTEGER,
    price REAL CHECK (price >= 0),
    quantity INTEGER DEFAULT 0 CHECK (quantity >= 0),
    description TEXT,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE SET NULL,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON DELETE SET NULL
)''',
    '''
CREATE TABLE IF NOT EXISTS sales (
    sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0),
    total REAL NOT NULL CHECK (total >= 0),
    sale_date TEXT NOT NULL,
    customer TEXT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE RESTRICT
)''',
]

_connection = None
_cursor = None
_engine = None
_schema_ready = False


def _read_config():
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), CONFIG_FILE))
    return config


def engine():
    global _engine
    if _engine is None:
        _engine = _read_config().get('database', 'engine', fallback='sqlite').strip().lower()
    return _engine


def _placeholder(sql):
    return sql.replace('?', '%s') if engine() == 'mysql' else sql


def _engine_sql(sql):
    if engine() == 'mysql':
        return sql.replace('INTEGER PRIMARY KEY AUTOINCREMENT',
                           'INT NOT NULL AUTO_INCREMENT PRIMARY KEY') + ' ENGINE=InnoDB'
    return sql


def ensure_tables():
    for statement in _SCHEMA_SQL:
        _cursor.execute(_engine_sql(statement.strip()))
    _connection.commit()


def _parse_number(value):
    try:
        return float(str(value).strip().replace(',', ''))
    except (ValueError, TypeError):
        return None


def to_iso_date(value):
    value = str(value or '').strip()
    parts = value.split('/')
    if len(parts) == 3 and all(p.strip().isdigit() for p in parts):
        day, month, year = (int(p) for p in parts)
        if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100:
            return f'{year:04d}-{month:02d}-{day:02d}'
    return value or None


def _migrate_employee_data():
    _cursor.execute('ALTER TABLE employee_data RENAME TO employee_data_old')
    _cursor.execute(_engine_sql(_EMPLOYEE_TABLE_SQL.strip()))
    rows = _cursor.execute(
        'SELECT empid, name, gender, email, number, dob, salary, address, usertype, password '
        'FROM employee_data_old').fetchall()
    for row in rows:
        _cursor.execute(
            'INSERT INTO employee_data '
            '(empid, name, gender, email, number, dob, salary, address, usertype, password) '
            'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (row['empid'], row['name'], row['gender'], row['email'], row['number'],
             to_iso_date(row['dob']), _parse_number(row['salary']), row['address'],
             row['usertype'], hash_password(row['password'] or '')))
    _cursor.execute('DROP TABLE employee_data_old')


def _backup_database():
    db_file = _read_config().get('database', 'db_file', fallback='inventory_system.db')
    if not os.path.exists(db_file):
        return None
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'{db_file}.backup_{timestamp}'
    shutil.copy2(db_file, backup_file)
    return backup_file


def migrate():
    if engine() != 'sqlite':
        return
    _cursor.execute('PRAGMA user_version')
    version = _cursor.fetchone()
    version = dict(version)['user_version'] if version else 0
    if version >= 1:
        return

    _backup_database()

    _cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='employee_data'")
    if _cursor.fetchone():
        columns = {row['name']: (row['type'] or '').upper()
                   for row in _cursor.execute('PRAGMA table_info(employee_data)')}
        if columns.get('salary') == 'TEXT':
            _migrate_employee_data()

    for table, legacy in (('products', ('category', 'supplier')), ('sales', ('product',))):
        _cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        if not _cursor.fetchone():
            continue
        columns = {row['name'] for row in _cursor.execute(f'PRAGMA table_info({table})')}
        if any(column in columns for column in legacy):
            count = _cursor.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
            if count == 0:
                _cursor.execute(f'DROP TABLE {table}')
            else:
                raise RuntimeError(
                    f'Legacy table "{table}" has {count} rows that cannot be auto-migrated')

    _cursor.execute('PRAGMA user_version = 1')
    _connection.commit()


def _prepare_schema():
    ensure_tables()
    migrate()
    ensure_tables()


def connect_database():
    global _connection, _cursor, _schema_ready
    if _connection is not None:
        return _cursor, _connection
    config = _read_config()

    if engine() == 'mysql':
        try:
            import pymysql
            _connection = pymysql.connect(
                host=config.get('database', 'host', fallback='localhost'),
                user=config.get('database', 'user', fallback='root'),
                password=config.get('database', 'password', fallback=''),
                database=config.get('database', 'database', fallback='inventory_db'),
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
            )
            _cursor = _connection.cursor()
        except Exception as exc:
            raise RuntimeError(f'Could not connect to MySQL: {exc}') from exc
    else:
        db_file = config.get('database', 'db_file', fallback='inventory_system.db')
        try:
            _connection = sqlite3.connect(db_file)
        except Exception as exc:
            raise RuntimeError(f'Could not open database file "{db_file}": {exc}') from exc
        _connection.row_factory = sqlite3.Row
        _connection.execute('PRAGMA foreign_keys = ON')
        _cursor = _connection.cursor()

    if not _schema_ready:
        _prepare_schema()
        _schema_ready = True
    return _cursor, _connection


def execute(sql, params=()):
    connect_database()
    return _cursor.execute(_placeholder(sql), tuple(params))


def query(sql, params=()):
    return [dict(row) for row in execute(sql, params).fetchall()]


def query_one(sql, params=()):
    rows = query(sql, params)
    return rows[0] if rows else None


def commit():
    _connection.commit()


def rollback():
    _connection.rollback()


def hash_password(password):
    return hashlib.pbkdf2_hmac(
        'sha256', str(password).encode('utf-8'), PASSWORD_SALT.encode('utf-8'), 100000).hex()


def verify_password(password, hashed):
    if not hashed:
        return False
    return hash_password(password) == str(hashed)


def is_integrity_error(exc):
    if isinstance(exc, sqlite3.IntegrityError):
        return True
    try:
        from pymysql.err import IntegrityError as MyIntegrityError
        return isinstance(exc, MyIntegrityError)
    except ImportError:
        return False
