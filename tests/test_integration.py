import os
import re
import sqlite3
import sys
import tkinter as tk

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import crud
import employee, suppliers, categories, products, sales

messages = []
for mod in (crud,):
    mod.messagebox.showerror = lambda title, msg: messages.append(('error', title, msg))
    mod.messagebox.showinfo = lambda title, msg: messages.append(('info', title, msg))
    mod.messagebox.askyesno = lambda title, msg: True

root = tk.Tk()
root.withdraw()


def db():
    conn = sqlite3.connect(os.path.join(ROOT, 'inventory_system.db'))
    conn.row_factory = sqlite3.Row
    return conn


conn = db()
conn.execute("DELETE FROM sales WHERE sale_id IN (400, 401)")
conn.execute("DELETE FROM products WHERE product_id IN (300, 301)")
conn.execute("DELETE FROM suppliers WHERE supplier_id=100")
conn.execute("DELETE FROM categories WHERE category_id=200")
conn.commit()

# --- Employees ---
employee.employee_form(root)
root.update()
c0 = employee.get_count()
employee.add_employee(500, 'Test Emp', 'emp@x.com', '0500000001', '01/01/1990', 'Male', '1,000', 'Addr', 'Admin', 'pw')
assert employee.get_count() == c0 + 1
row = conn.execute('SELECT dob, salary, password FROM employee_data WHERE empid=500').fetchone()
assert row['dob'] == '1990-01-01', row['dob']                    # ISO date
assert row['salary'] == 1000.0, row['salary']                    # REAL number
assert row['password'] != 'pw' and re.fullmatch(r'[0-9a-f]{64}', row['password']), row['password']  # hashed
hash_before = row['password']
employee.update_employee(500, 'Test Emp', 'emp@x.com', '0500000001', '01/01/1990', 'Male', '1,200', 'Addr', 'Admin', '')
row = conn.execute('SELECT salary, password FROM employee_data WHERE empid=500').fetchone()
assert row['salary'] == 1200.0 and row['password'] == hash_before, (row['salary'], row['password'])  # blank pw keeps hash
employee.delete_employee(500)
assert employee.get_count() == c0
print('employee CRUD + hashing: OK')

# --- Suppliers ---
suppliers.supplier_form(root)
root.update()
c0 = suppliers.get_count()
suppliers.add_supplier(100, 'Acme Supplies', 'John Doe', 'acme@x.com', '0200000000', 'Kumasi')
assert suppliers.get_count() == c0 + 1
suppliers.update_supplier(100, 'Acme Supplies Ltd', 'Jane Doe', 'acme@x.com', '0200000001', 'Kumasi')
suppliers.search_supplier('Name', 'Acme')
root.update()
assert len(suppliers.supplier_treeview.get_children()) == 1
suppliers.delete_supplier(100)
assert suppliers.get_count() == c0
# update with unknown id must fail (rowcount check)
before = len(messages)
ok = suppliers.update_supplier(9999, 'X', 'X', 'x@x.com', '0200000000', 'X')
assert ok is False and any(m[0] == 'error' and 'No record found' in m[2] for m in messages[before:])
print('supplier CRUD + rowcount guard: OK')

# --- Categories ---
categories.category_form(root)
root.update()
c0 = categories.get_count()
categories.add_category(200, 'Electronics', 'Electronic items')
assert categories.get_count() == c0 + 1
categories.update_category(200, 'Electronics Pro', 'Electronic items')
categories.delete_category(200)
assert categories.get_count() == c0
print('category CRUD: OK')

# --- Products (needs categories & suppliers present) ---
categories.add_category(200, 'Electronics', 'Electronic items')
suppliers.add_supplier(100, 'Acme Supplies', 'John Doe', 'acme@x.com', '0200000000', 'Kumasi')
products.product_form(root)
root.update()
c0 = products.get_count()
products.add_product(300, 'Laptop', 'Electronics', 'Acme Supplies', '2,500', '10', 'Gaming laptop')
assert products.get_count() == c0 + 1
qty = conn.execute('SELECT quantity FROM products WHERE product_id=300').fetchone()[0]
assert qty == 10, qty                                               # INTEGER not TEXT
assert products.get_product_details('Laptop') == (2500.0, 10)
products.update_product(300, 'Laptop Pro', 'Electronics', 'Acme Supplies', '3,000', '8', 'Pro laptop')
row = conn.execute('SELECT name, price, quantity FROM products WHERE product_id=300').fetchone()
assert tuple(row) == ('Laptop Pro', 3000.0, 8), tuple(row)
products.search_product('Name', 'Laptop')
root.update()
assert len(products.product_treeview.get_children()) == 1
# duplicate product name must be rejected (UNIQUE)
before = len(messages)
ok = products.add_product(301, 'Laptop Pro', 'Electronics', 'Acme Supplies', '5', '1', 'dup')
assert ok is False and products.get_count() == c0 + 1
print('product CRUD + unique name: OK')

# --- Sales with stock tracking ---
sales.sale_form(root)
root.update()
c0 = sales.get_count()
sales.add_sale(400, 'Laptop Pro', '3', '3,000', '9,000.00', '31/07/2026', 'John Doe')
assert sales.get_count() == c0 + 1
qty = conn.execute('SELECT quantity FROM products WHERE product_id=300').fetchone()[0]
assert qty == 5, qty
row = conn.execute('SELECT sale_date, product_id, total FROM sales WHERE sale_id=400').fetchone()
assert row['sale_date'] == '2026-07-31' and row['product_id'] == 300, tuple(row)   # ISO date + FK by id
assert row['total'] == 9000.0, row['total']                       # total recomputed server-side
# insufficient stock rejected
sales.add_sale(401, 'Laptop Pro', '10', '3,000', '30,000.00', '31/07/2026', 'Jane')
qty = conn.execute('SELECT quantity FROM products WHERE product_id=300').fetchone()[0]
assert qty == 5, qty
assert sales.get_count() == c0 + 1
# update: restore 3 then deduct 2 -> 6
sales.update_sale(400, 'Laptop Pro', '2', '3,000', '6,000.00', '31/07/2026', 'John', 'Laptop Pro', '3')
qty = conn.execute('SELECT quantity FROM products WHERE product_id=300').fetchone()[0]
assert qty == 6, qty
# FK RESTRICT: cannot delete a product that has sales
before = len(messages)
ok = products.delete_product(300)
assert ok is False and any(m[0] == 'error' and 'referenced' in m[2] for m in messages[before:])
# delete sale -> restore 2 -> 8
sales.delete_sale(400, 'Laptop Pro', '2')
qty = conn.execute('SELECT quantity FROM products WHERE product_id=300').fetchone()[0]
assert qty == 8, qty
assert sales.get_count() == c0
sales.search_sale('Product', 'Laptop')
root.update()
assert len(sales.sale_treeview.get_children()) == 0
print('sales CRUD + stock tracking + FK RESTRICT: OK')

# --- delete_guard: category with linked product cannot be deleted ---
products.add_product(301, 'Mouse', 'Electronics', 'Acme Supplies', '50', '5', 'Peripheral')
before = len(messages)
ok = categories.delete_category(200)
assert ok is False and any(m[0] == 'error' and 'linked' in m[2] for m in messages[before:])
ok = suppliers.delete_supplier(100)
assert ok is False
print('delete_guard (category/supplier with linked products): OK')

# --- cleanup test data ---
conn.execute('DELETE FROM products WHERE product_id IN (300, 301)')
conn.execute('DELETE FROM suppliers WHERE supplier_id=100')
conn.execute('DELETE FROM categories WHERE category_id=200')
conn.commit()
conn.close()

print('counts:', employee.get_count(), suppliers.get_count(), categories.get_count(),
      products.get_count(), sales.get_count())

# --- form smoke test ---
products.product_form(root)
root.update()
print('ALL INTEGRATION TESTS PASSED')
root.destroy()
