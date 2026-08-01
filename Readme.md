# Inventory Management System

## Overview
A Tkinter desktop application for managing employees, suppliers, categories, products, and sales, with automatic stock tracking. Built with Python and an embedded SQLite database (experimental MySQL support via PyMySQL).

## Features
- **Dashboard**: Responsive home screen with live totals and quick navigation.
- **CRUD + Search**: Full create, read, update, delete, search, and CSV export for every module.
- **Sales tracking**: Automatic unit-price prefill and total calculation; stock is deducted on sale, restored on delete, and re-deducted on update. Insufficient stock is rejected.
- **Multi-item sales**: The **Multi-Item Sale** screen (a cart on the Sales page) records several different products on a single invoice. Every line shares one invoice number (`INV-00001`…), stock is checked and deducted atomically across the whole order, and the credit-limit check applies to the order total.
- **Sales workflow**: Every sale gets an auto-generated invoice number (`INV-00001`…), a Cash/Credit payment mode, and a printable receipt (text or PDF). Receipts group all lines under the invoice. Sales that have returns cannot be deleted until the returns are removed.
- **Returns**: Record product returns against a sale — stock is restored, a return entry is stored (with the original invoice number and customer), and the ledger records the movement. Returnable quantity is enforced, and returns can be updated or deleted. On a multi-item invoice, each line is listed individually (`INV-00003 — Laptop (qty 2)`), so you return exactly the line you need.
- **Purchasing / restock**: Record purchases from suppliers to receive stock (auto `PO-` invoice numbers, unit cost with auto-total, Cash/Credit payment, free-form note). A **Reorder & Purchase** picker lists every product at or below its reorder level, suggests how much to buy (enough to reach twice the reorder level) with an estimated cost, and can create purchase records for the selected products in one click.
- **Customers & credit tracking**: A dedicated Customers screen (name, phone, email, address, credit limit) with live outstanding balances. Credit sales are linked to a customer (select an existing one, or type a new name and the sale auto-creates the customer on credit). Credit sales are checked against the customer's credit limit when one is set (a limit of `0`/blank means unlimited). Returns and recorded payments reduce the outstanding balance; each customer has a running credit ledger (credit sales / returns / payments) and the Reports menu shows an **Outstanding Customer Credit** report. Cash sales with a typed-in name remain free-text.
- **Products**: Selling and cost price per product, current quantity, and an optional reorder level — low-stock alerts use the product's reorder level when set, otherwise a global fallback threshold.
- **Data integrity**: Foreign keys enforced (`PRAGMA foreign_keys=ON`), UNIQUE constraints on category/product names, CHECK constraints on prices/quantities.
- **Stock movement ledger**: Every quantity change is logged with a signed delta, reason, sale reference, timestamp, and the user who made it — initial stock, adjustments, sales, sale updates/deletions, returns, and purchases. Viewable and exportable from the Reports menu.
- **Security**: Employee passwords are hashed with PBKDF2-SHA256 (600,000 iterations) using a random per-user salt, never stored as plaintext. Hashes stored by older versions are verified transparently and re-hashed on the user's next successful login.
- **Login & roles**: The app starts at a login screen. Admin accounts can access every module; Employee accounts can only record sales.
- **Hardening**: Accounts lock for 5 minutes after 5 failed logins (the lockout is persisted in the database, so it survives restarts); errors are logged to `app.log` (rotating); only one app instance can run at a time; the database is backed up automatically (startup if none in 24h, then every 6h into `backups/`). Backups use SQLite's online backup API, so they are consistent even mid-write.
- **Auto-generated IDs**: Record IDs for employees, customers, suppliers, categories, products, sales, purchases, and returns are generated automatically — the Add dialog shows the next ID (read-only) before you save, mirroring the invoice-number behaviour.
- **Reports**: Low-stock report (with a live count on the dashboard, honoring per-product reorder levels), sales report over any date range with total revenue (invoice number and payment mode included), printable receipts (text or PDF), a stock-movements ledger, stock valuation, and sales analytics (top sellers, sales by employee, profit by product/category).
- **Charts**: The dashboard's **Charts** screen plots revenue by day and the top products by revenue (matplotlib). If matplotlib is not installed the app shows a friendly install hint instead.
- **Multi-database**: SQLite by default; experimental support for MySQL by editing `config.ini`.

## Requirements
- Python 3.11+ (system `python3` on some distros is 3.13+/3.14; the app is tested on 3.11)
- Tk (usually ships with Python)
- Python libraries (see `requirements.txt`):
  - `tkcalendar`
  - `pymysql` (only needed when `engine = mysql` in `config.ini`)
  - `matplotlib` (optional — enables the dashboard **Charts** screen)

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
   python3.11 dashboard.py
   ```

3. **First Login**
   Existing employee accounts were migrated from the original plaintext database, so their original passwords are unknown. Set a known password for an admin (or any employee) before logging in:
   ```bash
   python3 reset_password.py 1            # prompts for the new password
   # or non-interactively:
   python3 reset_password.py 1 mypassword
   ```
   Log in with the employee id and the password you set. Accounts with `usertype = Admin` see all modules; accounts with `usertype = Employee` can only record sales. Admins can also change any employee's password from the Employees screen.

   > No default password is shipped. Set one with `reset_password.py` before the first login. The development database checked into test environments may still contain a known dev-only password for `empid 1` — always rotate it for real use.

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
- **MySQL** *(experimental)*: Create the database and tables first using the schema from `database.py` (the app does not auto-create MySQL tables), then set `engine = mysql` with valid credentials. The MySQL backend is not covered by the test suite and may lag behind the SQLite schema — prefer SQLite unless you have a specific need.

## Modules
- **Employees**: Manage employee records, masked password field, hashed password storage, ISO-date date-of-birth.
- **Suppliers**: Manage supplier records.
- **Categories**: Manage product categories.
- **Products**: Manage products linked to categories and suppliers, with cost price and reorder level for profit and low-stock reporting.
- **Sales**: Record sales with automatic total calculation, auto invoice numbers, Cash/Credit payment mode, and stock tracking. Single-item sales go through the standard form; several products on one invoice go through the **Multi-Item Sale** cart. A receipt can be printed (text or PDF) and saved for any sale. The customer field lists existing customers and links credit sales to them.
- **Customers**: Manage customer records (with credit limit), see each customer's outstanding balance, record payments against their credit, and open a running credit ledger. Exported to CSV.
- **Returns**: Record returns against a sale (restores stock), browse/edit/delete them, and export to CSV.
- **Purchases**: Record purchases to receive stock from suppliers, browse/edit/delete them, and export to CSV. The **Reorder & Purchase** picker (from the Purchases screen or Reports) suggests and creates restock purchases.
- **Reports**: Low-stock report, sales report over a date range, stock-movements ledger, outstanding customer credit, and sales receipts (from the Reports menu).

## Testing
Run the test suites directly (they exercise the UI against a throwaway copy of the database):
```bash
python3.11 tests/test_integration.py
python3.11 tests/test_ui.py
python3.11 tests/test_login.py
```
`tests/testbase.py` creates an isolated temporary database (via the `INVENTORY_DB_FILE` env var) and seeds the admin/employee test accounts, so the suites never touch the real `inventory_system.db`. The suites are green under Python 3.11 and 3.14. `test_login.py` expects the dev-only password of the migrated admin account (`empid 1`). GitHub Actions (`.github/workflows/ci.yml`) runs the same suites under Xvfb on Python 3.11 and the system Python.

## Packaging
Build a standalone executable with PyInstaller:
- **Linux**: `./build.sh` (or `bash build.sh`)
- **Windows**: `build.bat`

The scripts bundle `images/` and `config.ini` into a one-file, windowed executable (`dist/InventorySystem`). `layout.resource_path` resolves bundled resources whether frozen or running from source.

## Data Migration
Existing databases created by the original version (TEXT columns, `dd/mm/yyyy` dates, plaintext passwords) are migrated automatically on first run:
- `employee_data` is rebuilt with typed columns; salaries parsed to REAL, dates converted to ISO format, passwords hashed. A backup is kept as `employee_data_old`.
- Products/sales tables are only dropped and recreated when empty; a database with existing product/sales data is left untouched and the app raises an error so nothing is lost.
- Schema version is tracked with `PRAGMA user_version` (currently 7). Upgrades add new columns/tables automatically (e.g. `stock_movements`, product `cost_price` and `reorder_level`, sales `invoice_number`/`payment_mode`, the `returns` and `purchases` tables, the `customers`/`credit_payments` tables, and the persisted login-lockout columns on `employee_data`). When upgrading, existing sales are back-filled into customer records automatically.

## Project Layout
- `dashboard.py` — main entry point (starts at the login screen) and dashboard UI.
- `database.py` — connection management, schema, migrations, password hashing, automated backups.
- `crud.py` — shared form/CRUD/search/export framework.
- `movements.py` — stock-movement ledger recording (current user + signed deltas).
- `login.py` — authentication, login screen, and failed-login lockout.
- `app_log.py` — rotating file logging and exception hooks.
- `reset_password.py` — command-line helper to set an employee's password.
- `employee.py`, `suppliers.py`, `categories.py`, `products.py`, `sales.py` — per-module screens.
- `customers.py` — customers screen (balances, credit payments, per-customer ledger).
- `returns.py` — returns screen (record/browse returns against sales).
- `purchases.py` — purchases screen (receive stock from suppliers) and the reorder picker integration.
- `reports.py` — low-stock/sales reports, reorder picker, receipts (text + PDF), and the matplotlib sales charts (`show_charts`).
- `layout.py` — theming, scaling, validators, tooltips, CSV export, resource-path and single-instance helpers.
- `config.ini` — database configuration.
- `tests/` — integration, UI smoke, and login test suites.

## License
This project is licensed under the MIT License.
