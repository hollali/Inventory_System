import configparser
import hashlib
import os
import re
import shutil
import sqlite3
import time
from datetime import datetime

from app_log import logger

CONFIG_FILE = 'config.ini'
PASSWORD_SALT = 'inventory-system-v1'
PASSWORD_ITERATIONS = 600_000
_HASH_PREFIX = 'pbkdf2_sha256$'
BACKUP_DIR = 'backups'
BACKUP_KEEP = 20

_EMPLOYEE_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS employee_data (
    empid INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    gender VARCHAR(20),
    email VARCHAR(255),
    number VARCHAR(50),
    dob TEXT,
    salary INTEGER,
    address TEXT,
    usertype VARCHAR(50),
    password TEXT,
    failed_attempts INTEGER DEFAULT 0,
    locked_until REAL
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
    price INTEGER CHECK (price >= 0),
    cost_price INTEGER DEFAULT 0 CHECK (cost_price >= 0),
    quantity INTEGER DEFAULT 0 CHECK (quantity >= 0),
    reorder_level INTEGER DEFAULT 0 CHECK (reorder_level >= 0),
    description TEXT,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE SET NULL,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON DELETE SET NULL
)''',
    '''
CREATE TABLE IF NOT EXISTS sales (
    sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price INTEGER NOT NULL CHECK (unit_price >= 0),
    total INTEGER NOT NULL CHECK (total >= 0),
    sale_date TEXT NOT NULL,
    customer TEXT NOT NULL,
    invoice_number TEXT,
    payment_mode TEXT NOT NULL DEFAULT 'Cash',
    customer_id INTEGER,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE RESTRICT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE SET NULL
)''',
    '''
CREATE TABLE IF NOT EXISTS returns (
    return_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id INTEGER,
    product_id INTEGER,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price INTEGER NOT NULL CHECK (unit_price >= 0),
    total INTEGER NOT NULL CHECK (total >= 0),
    return_date TEXT NOT NULL,
    customer TEXT,
    invoice_number TEXT,
    FOREIGN KEY (sale_id) REFERENCES sales(sale_id) ON DELETE SET NULL,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE SET NULL
)''',
    '''
CREATE TABLE IF NOT EXISTS stock_movements (
    movement_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,
    quantity_delta INTEGER NOT NULL,
    reason TEXT NOT NULL,
    reference_id INTEGER,
    created_by INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE SET NULL
)''',
    '''
CREATE TABLE IF NOT EXISTS purchases (
    purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_number TEXT,
    supplier_id INTEGER,
    product_id INTEGER,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_cost INTEGER NOT NULL CHECK (unit_cost >= 0),
    total INTEGER NOT NULL CHECK (total >= 0),
    purchase_date TEXT NOT NULL,
    payment_mode TEXT NOT NULL DEFAULT 'Cash',
    note TEXT,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id) ON DELETE RESTRICT,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE RESTRICT
)''',
    '''
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    credit_limit INTEGER DEFAULT 0 CHECK (credit_limit >= 0),
    created_at TEXT
)''',
    '''
CREATE TABLE IF NOT EXISTS credit_payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    amount INTEGER NOT NULL CHECK (amount >= 0),
    payment_date TEXT NOT NULL,
    note TEXT,
    created_by INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE RESTRICT
)''',
]

MIGRATION_VERSION = 8

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


def money_to_cents(value):
    """Parse a user-entered amount (float or comma-formatted string) into integer cents."""
    if value is None:
        return None
    try:
        return int(round(float(str(value).strip().replace(',', '')) * 100))
    except (ValueError, TypeError):
        return None


def money_from_cents(value):
    """Convert stored integer cents into a float for display/export."""
    if value is None:
        return 0.0
    try:
        return float(value) / 100.0
    except (ValueError, TypeError):
        return 0.0


def format_money(value):
    """Format stored integer cents as a 2-decimal currency string."""
    return f'{money_from_cents(value):,.2f}'


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


def _copy_db_file(src_file, dst_file):
    if engine() == 'sqlite':
        src = _connection if _connection is not None else sqlite3.connect(src_file)
        dst = sqlite3.connect(dst_file)
        try:
            src.backup(dst)
        finally:
            dst.close()
            if src is not _connection:
                src.close()
    else:
        shutil.copy2(src_file, dst_file)


def _backup_database():
    src = db_file_path()
    if not os.path.exists(src):
        return None
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(BACKUP_DIR, f'{os.path.basename(src)}.backup_{timestamp}')
    _copy_db_file(src, backup_file)
    _prune_backups(BACKUP_DIR, os.path.basename(src))
    return backup_file


def db_file_path():
    return os.environ.get('INVENTORY_DB_FILE') or _read_config().get(
        'database', 'db_file', fallback='inventory_system.db')


def _prune_backups(directory, prefix):
    backups = []
    if os.path.isdir(directory):
        backups = [os.path.join(directory, name) for name in os.listdir(directory)
                   if name.startswith(prefix)]
    if len(backups) > BACKUP_KEEP:
        for old in sorted(backups, key=os.path.getmtime)[:-BACKUP_KEEP]:
            try:
                os.remove(old)
            except OSError:
                logger.exception('Failed to remove old backup: %s', old)


def backup_now():
    backup_file = _backup_database()
    if backup_file:
        logger.info('Database backup created: %s', backup_file)
    return backup_file


def backup_if_due(max_age_days=1):
    src = db_file_path()
    if not os.path.exists(src):
        return None
    backups = []
    if os.path.isdir(BACKUP_DIR):
        prefix = os.path.basename(src)
        backups = [os.path.join(BACKUP_DIR, name) for name in os.listdir(BACKUP_DIR)
                   if name.startswith(prefix)]
    if backups:
        newest = max(os.path.getmtime(path) for path in backups)
        if time.time() - newest < max_age_days * 86400:
            return None
    return backup_now()


def migrate():
    if engine() != 'sqlite':
        return
    _cursor.execute('PRAGMA user_version')
    version = _cursor.fetchone()
    version = dict(version)['user_version'] if version else 0
    if version >= MIGRATION_VERSION:
        return

    _backup_database()

    if version < 1:
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

    if version < 3:
        columns = {row['name'] for row in _cursor.execute('PRAGMA table_info(products)')}
        if 'reorder_level' not in columns:
            _cursor.execute('ALTER TABLE products ADD COLUMN reorder_level INTEGER DEFAULT 0')
        if 'cost_price' not in columns:
            _cursor.execute('ALTER TABLE products ADD COLUMN cost_price REAL DEFAULT 0')

    if version < 4:
        columns = {row['name'] for row in _cursor.execute('PRAGMA table_info(sales)')}
        if 'invoice_number' not in columns:
            _cursor.execute('ALTER TABLE sales ADD COLUMN invoice_number TEXT')
        if 'payment_mode' not in columns:
            _cursor.execute("ALTER TABLE sales ADD COLUMN payment_mode TEXT NOT NULL DEFAULT 'Cash'")
        rows = _cursor.execute('SELECT sale_id FROM sales ORDER BY sale_id').fetchall()
        for index, row in enumerate(rows, 1):
            _cursor.execute('UPDATE sales SET invoice_number = ? WHERE sale_id = ?',
                            (f'INV-{index:05d}', row['sale_id']))

    if version < 5:
        columns = {row['name'] for row in _cursor.execute('PRAGMA table_info(purchases)')}
        if 'payment_mode' not in columns:
            _cursor.execute(
                "ALTER TABLE purchases ADD COLUMN payment_mode TEXT NOT NULL DEFAULT 'Cash'")

    if version < 6:
        columns = {row['name'] for row in _cursor.execute('PRAGMA table_info(sales)')}
        if 'customer_id' not in columns:
            _cursor.execute('ALTER TABLE sales ADD COLUMN customer_id INTEGER')
        names = [row['customer'] for row in _cursor.execute(
            "SELECT DISTINCT customer FROM sales WHERE customer IS NOT NULL "
            "AND TRIM(customer) != '' ORDER BY customer")]
        for name in names:
            _cursor.execute('INSERT OR IGNORE INTO customers (name, created_at) VALUES (?, ?)',
                            (name, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            _cursor.execute(
                'UPDATE sales SET customer_id = '
                '(SELECT customer_id FROM customers WHERE name = ?) '
                'WHERE customer = ? AND customer_id IS NULL', (name, name))

    if version < 7:
        columns = {row['name'] for row in _cursor.execute('PRAGMA table_info(employee_data)')}
        if 'failed_attempts' not in columns:
            _cursor.execute('ALTER TABLE employee_data ADD COLUMN failed_attempts INTEGER DEFAULT 0')
        if 'locked_until' not in columns:
            _cursor.execute('ALTER TABLE employee_data ADD COLUMN locked_until REAL')

    if version < 8:
        _money_tables = {
            'sales': ('unit_price', 'total'),
            'purchases': ('unit_cost', 'total'),
            'returns': ('unit_price', 'total'),
            'products': ('price', 'cost_price'),
            'customers': ('credit_limit',),
            'employee_data': ('salary',),
            'credit_payments': ('amount',),
            'stock_movements': (),
        }
        needs_rebuild = False
        for table, money_cols in _money_tables.items():
            columns = {row['name']: (row['type'] or '').upper()
                       for row in _cursor.execute(f'PRAGMA table_info({table})')}
            if any(columns.get(col) != 'INTEGER' for col in money_cols):
                needs_rebuild = True
                break
        if needs_rebuild:
            _cursor.execute('UPDATE returns SET sale_id = NULL WHERE sale_id IS NOT NULL AND NOT EXISTS '
                            '(SELECT 1 FROM sales WHERE sales.sale_id = returns.sale_id)')
            _cursor.execute('UPDATE returns SET product_id = NULL WHERE product_id IS NOT NULL '
                            'AND NOT EXISTS (SELECT 1 FROM products WHERE products.product_id = returns.product_id)')
            _cursor.execute('UPDATE stock_movements SET product_id = NULL WHERE product_id IS NOT NULL '
                            'AND NOT EXISTS (SELECT 1 FROM products '
                            'WHERE products.product_id = stock_movements.product_id)')
            _cursor.execute('UPDATE sales SET customer_id = NULL WHERE customer_id IS NOT NULL '
                            'AND NOT EXISTS (SELECT 1 FROM customers '
                            'WHERE customers.customer_id = sales.customer_id)')
            _connection.commit()
            _cursor.execute('PRAGMA foreign_keys = OFF')
            try:
                _ddl_by_name = {}
                for statement in _SCHEMA_SQL:
                    match = re.search(r'CREATE TABLE IF NOT EXISTS (\w+)', statement)
                    if match:
                        _ddl_by_name[match.group(1)] = statement
                _pk_by_table = {
                    'sales': 'sale_id', 'purchases': 'purchase_id', 'returns': 'return_id',
                    'products': 'product_id', 'customers': 'customer_id',
                    'employee_data': 'empid', 'credit_payments': 'payment_id',
                    'stock_movements': 'movement_id',
                }
                for table, money_cols in _money_tables.items():
                    temp_name = table + '_v8'
                    _cursor.execute(_ddl_by_name[table].replace(
                        f'CREATE TABLE IF NOT EXISTS {table} (', f'CREATE TABLE {temp_name} ('))
                    new_cols = [row['name'] for row in
                                _cursor.execute(f'PRAGMA table_info({temp_name})')]
                    select_cols = ', '.join(
                        ('CASE WHEN {col} IS NULL THEN NULL ELSE CAST(ROUND({col} * 100) AS INTEGER) END'
                         if col in money_cols else col).format(col=col)
                        for col in new_cols)
                    _cursor.execute(
                        f'INSERT INTO {temp_name} ({", ".join(new_cols)}) '
                        f'SELECT {select_cols} FROM {table}')
                    _cursor.execute(f'DROP TABLE {table}')
                    _cursor.execute(f'ALTER TABLE {temp_name} RENAME TO {table}')
                    count = _cursor.execute(f'SELECT COUNT(*) AS n FROM {table}').fetchone()['n']
                    if count:
                        _cursor.execute(
                            f'INSERT OR REPLACE INTO sqlite_sequence(name, seq) VALUES '
                            f'(?, (SELECT MAX({_pk_by_table[table]}) FROM {table}))', (table,))
            finally:
                _cursor.execute('PRAGMA foreign_keys = ON')

    _cursor.execute(f'PRAGMA user_version = {MIGRATION_VERSION}')
    _connection.commit()


_INDEX_SQL = [
    'CREATE INDEX IF NOT EXISTS idx_sales_product ON sales(product_id)',
    'CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales(customer_id)',
    'CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date)',
    'CREATE INDEX IF NOT EXISTS idx_returns_sale ON returns(sale_id)',
    'CREATE INDEX IF NOT EXISTS idx_movements_product ON stock_movements(product_id)',
    'CREATE INDEX IF NOT EXISTS idx_purchases_product ON purchases(product_id)',
    'CREATE INDEX IF NOT EXISTS idx_creditpay_customer ON credit_payments(customer_id)',
]


def _prepare_schema():
    ensure_tables()
    migrate()
    ensure_tables()
    if engine() == 'sqlite':
        for statement in _INDEX_SQL:
            _cursor.execute(statement)
        _connection.commit()


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
            logger.exception('MySQL connection failed')
            raise RuntimeError(f'Could not connect to MySQL: {exc}') from exc
    else:
        db_file = os.environ.get('INVENTORY_DB_FILE') or config.get(
            'database', 'db_file', fallback='inventory_system.db')
        try:
            _connection = sqlite3.connect(db_file)
        except Exception as exc:
            logger.exception('SQLite open failed')
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
    return _hash_password(str(password), os.urandom(16), PASSWORD_ITERATIONS)


def _hash_password(password, salt, iterations):
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations).hex()
    return f'{_HASH_PREFIX}{iterations}${salt.hex()}${digest}'


def verify_password(password, hashed):
    stored = str(hashed or '')
    if not stored:
        return False
    if stored.startswith(_HASH_PREFIX):
        try:
            _, iterations, salt_hex, digest = stored.split('$', 3)
            candidate = hashlib.pbkdf2_hmac(
                'sha256', str(password).encode('utf-8'), bytes.fromhex(salt_hex),
                int(iterations)).hex()
            return candidate == digest
        except (ValueError, TypeError):
            return False
    return hashlib.pbkdf2_hmac(
        'sha256', str(password).encode('utf-8'), PASSWORD_SALT.encode('utf-8'), 100000).hex() == stored


def password_needs_rehash(stored):
    return bool(stored) and not str(stored).startswith(_HASH_PREFIX)


def is_integrity_error(exc):
    if isinstance(exc, sqlite3.IntegrityError):
        return True
    try:
        from pymysql.err import IntegrityError as MyIntegrityError
        return isinstance(exc, MyIntegrityError)
    except ImportError:
        return False


def next_id(table, id_column):
    row = query_one('SELECT seq + 1 AS next FROM sqlite_sequence WHERE name = ?', (table,))
    if row and row['next'] is not None:
        return int(row['next'])
    row = query_one(f'SELECT COALESCE(MAX({id_column}), 0) + 1 AS next FROM {table}')
    return int(row['next']) if row else 1


def next_invoice_number(prefix, table):
    row = query_one(
        f"SELECT COALESCE(MAX(CAST(SUBSTR(invoice_number, INSTR(invoice_number, '-') + 1) "
        f"AS INTEGER)), 0) + 1 AS n FROM {table}")
    return f'{prefix}-{row["n"]:05d}' if row else f'{prefix}-00001'
