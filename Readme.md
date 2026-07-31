# Inventory Management System

## Overview
A Tkinter desktop application for managing employees, suppliers, categories, products, and sales, with automatic stock tracking. Built with Python and an embedded SQLite database (MySQL supported via PyMySQL).

## Features
- **Dashboard**: Responsive home screen with live totals and quick navigation.
- **CRUD + Search**: Full create, read, update, delete, search, and CSV export for every module.
- **Sales tracking**: Automatic unit-price prefill and total calculation; stock is deducted on sale, restored on delete, and re-deducted on update. Insufficient stock is rejected.
- **Data integrity**: Foreign keys enforced (`PRAGMA foreign_keys=ON`), UNIQUE constraints on category/product names, CHECK constraints on prices/quantities.
- **Security**: Employee passwords are hashed with PBKDF2-SHA256 (100,000 iterations); stored as 64-char hex, never plaintext.
- **Login & roles**: The app starts at a login screen. Admin accounts can access every module; Employee accounts can only record sales.
- **Reports**: Low-stock report (with a live count on the dashboard), sales report over any date range with total revenue, and printable receipts for individual sales.
- **Multi-database**: SQLite by default; switch to MySQL by editing `config.ini`.

## Requirements
- Python 3.11+ (system `python3` on some distros is 3.13+/3.14; the app is tested on 3.11)
- Tk (usually ships with Python)
- Python libraries (see `requirements.txt`):
  - `tkcalendar`
  - `pymysql` (only needed when `engine = mysql` in `config.ini`)

## Installation

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   On Debian/Ubuntu (PEP 668 externally-managed environments):
   ```bash
   pip install --break-system-packages -r requirements.txt
   ```

2. **Run the Application**
   ```bash
   python3.11 dashbord.py
   ```

3. **First Login**
   Existing employee accounts were migrated from the original plaintext database, so their original passwords are unknown. Set a known password for an admin (or any employee) before logging in:
   ```bash
   python3 reset_password.py 1            # prompts for the new password
   # or non-interactively:
   python3 reset_password.py 1 mypassword
   ```
   Log in with the employee id and the password you set. Accounts with `usertype = Admin` see all modules; accounts with `usertype = Employee` can only record sales. Admins can also change any employee's password from the Employees screen.

   > For development/testing only, the migrated admin account (`empid 1`) is pre-set to the password `admin123`. Change it before real use (see `reset_password.py`).

## Configuration
Edit `config.ini` to select the database engine.

```ini
[database]
engine = sqlite    # 'sqlite' or 'mysql'
db_file = inventory_system.db
host = localhost
user = yourusername
password = yourpassword
database = inventory_db
```

- **SQLite** (default): The database file is created and migrated automatically on first run. If a pre-existing database has no schema, it is migrated to the current schema automatically.
- **MySQL**: Create the database and tables first using the schema from `database.py` (the app does not auto-create MySQL tables), then set `engine = mysql` with valid credentials. MySQL is not tested as thoroughly as SQLite.

## Modules
- **Employees**: Manage employee records, masked password field, hashed password storage, ISO-date date-of-birth.
- **Suppliers**: Manage supplier records.
- **Categories**: Manage product categories.
- **Products**: Manage products linked to categories and suppliers.
- **Sales**: Record sales with automatic total calculation and stock tracking. A receipt can be printed and saved for any sale.
- **Reports**: Low-stock report, sales report over a date range, and sales receipts (from the Reports menu).

## Testing
Run the test suites directly (they exercise the UI and the SQLite database in place):
```bash
python3.11 tests/test_integration.py
python3.11 tests/test_ui.py
python3.11 tests/test_login.py
```
The suites are green under Python 3.11 and 3.14. `test_login.py` expects the `admin123` password from the development setup and the migrated admin account (`empid 1`).

## Packaging
Build a standalone executable with PyInstaller:
- **Linux**: `./build.sh` (or `bash build.sh`)
- **Windows**: `build.bat`

The scripts bundle `images/` and `config.ini` into a one-file, windowed executable (`dist/InventorySystem`). `layout.resource_path` resolves bundled resources whether frozen or running from source.

## Data Migration
Existing databases created by the original version (TEXT columns, `dd/mm/yyyy` dates, plaintext passwords) are migrated automatically on first run:
- `employee_data` is rebuilt with typed columns; salaries parsed to REAL, dates converted to ISO format, passwords hashed. A backup is kept as `employee_data_old`.
- Products/sales tables are only dropped and recreated when empty; a database with existing product/sales data is left untouched and the app raises an error so nothing is lost.

## Project Layout
- `dashbord.py` — main entry point (starts at the login screen) and dashboard UI.
- `database.py` — connection management, schema, migrations, password hashing.
- `crud.py` — shared form/CRUD/search/export framework.
- `login.py` — authentication and login screen.
- `reset_password.py` — command-line helper to set an employee's password.
- `employee.py`, `suppliers.py`, `categories.py`, `products.py`, `sales.py` — per-module screens.
- `reports.py` — low-stock/sales reports and receipts.
- `layout.py` — theming, scaling, validators, tooltips, CSV export, resource-path resolution.
- `config.ini` — database configuration.
- `tests/` — integration, UI smoke, and login test suites.

## License
This project is licensed under the MIT License.
