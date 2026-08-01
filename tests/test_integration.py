import os
import re
import tkinter as tk

import testbase

import crud
import movements
import employee, suppliers, categories, products, sales, purchases, customers
import reports

messages = []
for mod in (crud,):
    mod.messagebox.showerror = lambda title, msg: messages.append(('error', title, msg))
    mod.messagebox.showinfo = lambda title, msg: messages.append(('info', title, msg))
    mod.messagebox.askyesno = lambda title, msg: True

root = tk.Tk()
root.withdraw()


def db():
    return testbase.conn()


conn = db()

movements.set_current_user({'empid': 1, 'name': 'Hollali Kelvin'})

# --- Employees ---
employee.employee_form(root)
root.update()
c0 = employee.get_count()
employee.add_employee(500, 'Test Emp', 'emp@x.com', '0500000001', '01/01/1990', 'Male', '1,000', 'Addr', 'Admin', 'pw')
assert employee.get_count() == c0 + 1
row = conn.execute('SELECT dob, salary, password FROM employee_data WHERE empid=500').fetchone()
assert row['dob'] == '1990-01-01', row['dob']                    # ISO date
assert row['salary'] == 1000.0, row['salary']                    # REAL number
assert row['password'] != 'pw' and re.fullmatch(
    r'pbkdf2_sha256\$\d+\$[0-9a-f]{32}\$[0-9a-f]{64}', row['password']), row['password']  # salted hash
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
# cost price + reorder level persist through the form data path
products.update_record({'product_id': 300, 'name': 'Laptop', 'category_id': 200, 'supplier_id': 100,
                        'price': '2,500', 'cost_price': '1,500', 'quantity': '10',
                        'reorder_level': '12', 'description': 'Gaming laptop'})
row = conn.execute('SELECT cost_price, reorder_level FROM products WHERE product_id=300').fetchone()
assert tuple(row) == (1500.0, 12), tuple(row)
assert any(r['product'] == 'Laptop' for r in reports.low_stock_rows(5)), 'reorder level must win'
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
# analytics powered by the ledger
top = reports._top_sellers()
assert top[0]['product'] == 'Laptop Pro' and top[0]['units_sold'] == 3 and top[0]['revenue'] == 9000.0, top
prof = reports._profit_by_product()
assert prof[0]['profit'] == 4500.0, prof                        # (3000 - 1500) * 3
assert reports.stock_valuation_rows()[0]['value'] == 15000.0    # qty 5 * price 3000
emp = reports._sales_by_employee()
assert emp[0]['employee'] == 'Hollali Kelvin' and emp[0]['units_sold'] == 3, emp
print('analytics (top sellers / profit / valuation / by employee): OK')
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

# --- stock movement ledger ---
moves = conn.execute(
    'SELECT product_id, quantity_delta, reason, reference_id, created_by '
    'FROM stock_movements ORDER BY movement_id').fetchall()
assert [m['reason'] for m in moves] == ['initial', 'adjustment', 'sale', 'sale_update', 'sale_delete'], moves
assert [m['quantity_delta'] for m in moves] == [10, -2, -3, 1, 2], moves
assert all(m['product_id'] == 300 for m in moves)
assert all(m['created_by'] == 1 for m in moves)
assert moves[2]['reference_id'] == 400 and moves[3]['reference_id'] == 400
print('stock movement ledger (initial/adjust/sale/update/delete): OK')

# --- invoice numbers, payment mode, and returns ---
sales.add_sale(402, 'Laptop Pro', '4', '3,000', '12,000.00', '31/07/2026', 'Jane')
qty = conn.execute('SELECT quantity FROM products WHERE product_id=300').fetchone()[0]
assert qty == 4, qty
row = conn.execute('SELECT invoice_number, payment_mode FROM sales WHERE sale_id=402').fetchone()
assert row['payment_mode'] == 'Cash', tuple(row)                    # default payment mode
assert re.fullmatch(r'INV-\d{5}', row['invoice_number'] or ''), tuple(row)  # auto invoice number
assert reports.sales_report_rows('2026-01-01', '2099-12-31')[0]['payment_mode'] == 'Cash'
receipt = reports.receipt_text(402)
assert 'Invoice:' in receipt and 'Payment:' in receipt and row['invoice_number'] in receipt, receipt
# a return restores stock and is recorded
before = len(messages)
ok = sales.add_return(402, 2, '01/08/2026')
assert ok is True, messages[before:]
qty = conn.execute('SELECT quantity FROM products WHERE product_id=300').fetchone()[0]
assert qty == 6, qty
rrow = conn.execute('SELECT return_id, sale_id, quantity, unit_price, total, customer, '
                    'invoice_number FROM returns WHERE sale_id=402').fetchone()
assert tuple(rrow) == (rrow['return_id'], 402, 2, 3000.0, 6000.0, 'Jane', row['invoice_number']), tuple(rrow)
# over-return rejected
before = len(messages)
ok = sales.add_return(402, 3, '01/08/2026')
assert ok is False and any(m[0] == 'error' and 'can be returned' in m[2] for m in messages[before:])
qty = conn.execute('SELECT quantity FROM products WHERE product_id=300').fetchone()[0]
assert qty == 6, qty
# return update adjusts stock; delete return restores the deduction
sales.update_return({'return_id': rrow['return_id'], 'quantity': 1, 'return_date': '02/08/2026'})
qty = conn.execute('SELECT quantity FROM products WHERE product_id=300').fetchone()[0]
assert qty == 5, qty
sales.delete_return(rrow['return_id'])
qty = conn.execute('SELECT quantity FROM products WHERE product_id=300').fetchone()[0]
assert qty == 4, qty
# deleting a sale that has returns is blocked
sales.add_return(402, 1, '03/08/2026')
before = len(messages)
ok = sales.delete_sale(402, 'Laptop Pro', '4')
assert ok is False and any(m[0] == 'error' and 'returns' in m[2] for m in messages[before:])
qty = conn.execute('SELECT quantity FROM products WHERE product_id=300').fetchone()[0]
assert qty == 5, qty
sales.delete_return(conn.execute('SELECT MAX(return_id) AS m FROM returns').fetchone()['m'])
sales.delete_sale(402, 'Laptop Pro', '4')
qty = conn.execute('SELECT quantity FROM products WHERE product_id=300').fetchone()[0]
assert qty == 8, qty
print('invoice numbers + payment mode + returns (restock/guard/update/delete): OK')

# --- PDF receipt writer produces a valid PDF file ---
import tempfile
with tempfile.TemporaryDirectory() as tmp:
    pdf_path = os.path.join(tmp, 'receipt.pdf')
    reports.write_pdf_receipt(pdf_path, reports.receipt_text(400) or 'receipt')
    with open(pdf_path, 'rb') as f:
        head = f.read(8)
    assert head == b'%PDF-1.4' and os.path.getsize(pdf_path) > 200, (head, os.path.getsize(pdf_path))
print('PDF receipt writer -> OK')

# --- purchases: receive stock, update, reorder suggestions, ledger ---
purchases.purchase_form(root)
root.update()
c0 = purchases.get_count()
purchases.add_purchase(700, 'Acme Supplies', 'Laptop Pro', '5', '1,500', '7,500.00',
                       '02/08/2026')
assert purchases.get_count() == c0 + 1
qty = conn.execute('SELECT quantity FROM products WHERE product_id=300').fetchone()[0]
assert qty == 13, qty
prow = conn.execute('SELECT invoice_number, supplier_id, product_id, total, payment_mode '
                    'FROM purchases WHERE purchase_id=700').fetchone()
assert re.fullmatch(r'PO-\d{5}', prow['invoice_number']), prow['invoice_number']
assert tuple(prow) == (prow['invoice_number'], 100, 300, 7500.0, 'Cash'), tuple(prow)
# update: 5 -> 3 same product -> stock 11
purchases.update_purchase(700, 'Acme Supplies', 'Laptop Pro', '3', '1,500', '4,500.00',
                          '02/08/2026', 'Laptop Pro', '5')
qty = conn.execute('SELECT quantity FROM products WHERE product_id=300').fetchone()[0]
assert qty == 11, qty
# reorder picker suggests restock (reorder 12, qty 11 -> 2*12-11 = 13)
row = next(r for r in reports.reorder_rows(5) if r['product_id'] == 300)
assert row['suggested_qty'] == 13 and row['suggested_cost'] == 19500.0, row
# create a purchase through the picker helper (auto purchase_id + invoice)
before = len(messages)
ok = purchases.create_purchase(300, 13, 1500.0, 100, '03/08/2026')
assert ok is True, messages[before:]
qty = conn.execute('SELECT quantity FROM products WHERE product_id=300').fetchone()[0]
assert qty == 24, qty
reasons = [m['reason'] for m in conn.execute(
    "SELECT reason FROM stock_movements WHERE reason LIKE 'purchase%' "
    'ORDER BY movement_id').fetchall()]
assert reasons == ['purchase', 'purchase_update', 'purchase'], reasons
# delete both purchases -> stock back to 8
purchases.delete_purchase(700)
auto_id = conn.execute('SELECT MAX(purchase_id) AS m FROM purchases').fetchone()['m']
purchases.delete_purchase(auto_id)
qty = conn.execute('SELECT quantity FROM products WHERE product_id=300').fetchone()[0]
assert qty == 8, qty
print('purchases (receive stock / update / reorder suggestions / ledger): OK')

# --- multi-line sale: several products share one invoice ---
products.add_product(302, 'Keyboard', 'Electronics', 'Acme Supplies', '200', '20', 'Peripheral')
qty_laptop = conn.execute('SELECT quantity FROM products WHERE product_id=300').fetchone()[0]
qty_kb = conn.execute('SELECT quantity FROM products WHERE product_id=302').fetchone()[0]
orders_before = sales.get_order_count()
invoice = sales.add_order(
    [{'product_id': 300, 'quantity': 2, 'unit_price': '3,000'},
     {'product_id': 302, 'quantity': 5, 'unit_price': 200}],
    '05/08/2026', 'Jane')
assert invoice and re.fullmatch(r'INV-\d{5}', invoice), invoice
assert sales.get_order_count() == orders_before + 1
lines = conn.execute('SELECT sale_id, product_id, quantity, total, invoice_number '
                     'FROM sales WHERE invoice_number = ? ORDER BY sale_id', (invoice,)).fetchall()
assert len(lines) == 2 and all(r['invoice_number'] == invoice for r in lines), lines
assert conn.execute('SELECT quantity FROM products WHERE product_id=300').fetchone()[0] == qty_laptop - 2
assert conn.execute('SELECT quantity FROM products WHERE product_id=302').fetchone()[0] == qty_kb - 5
# the order total counts once against the credit limit
customers.add_customer(902, 'Bibi Yaw', '0550000002', 'bibi@x.com', 'Accra', '500')
qty_kb2 = conn.execute('SELECT quantity FROM products WHERE product_id=302').fetchone()[0]
before = len(messages)
rejected = sales.add_order([{'product_id': 302, 'quantity': 2, 'unit_price': 200},
                            {'product_id': 302, 'quantity': 1, 'unit_price': 200}],
                           '05/08/2026', 'Bibi Yaw', payment_mode='Credit')
assert rejected is None and any('Credit limit exceeded' in m[2] for m in messages[before:])
assert conn.execute('SELECT quantity FROM products WHERE product_id=302').fetchone()[0] == qty_kb2
# receipt groups all lines of the invoice
receipt = reports.receipt_text(lines[0]['sale_id'])
assert invoice in receipt and 'Jane' in receipt and 'Total:' in receipt, receipt
# a return can target a single line of a multi-line invoice
before = len(messages)
ok = sales.add_return(lines[0]['sale_id'], 1, '06/08/2026')
assert ok is True, messages[before:]
assert conn.execute('SELECT quantity FROM products WHERE product_id=300').fetchone()[0] == qty_laptop - 1
print('multi-line sale (shared invoice / order-level credit / grouped receipt / line return): OK')
# cleanup
sales.delete_return(conn.execute('SELECT MAX(return_id) AS m FROM returns').fetchone()['m'])
for r in lines:
    sales.delete_sale(r['sale_id'], 'Laptop Pro', '2')
products.delete_product(302)
assert conn.execute('SELECT quantity FROM products WHERE product_id=300').fetchone()[0] == qty_laptop

# --- customers: CRUD, credit tracking, payments, ledger, balances report ---
customers.customers_form(root)
root.update()
c0 = customers.get_count()
customers.add_customer(900, 'Alice Mansa', '0550000001', 'alice@x.com', 'Accra', '5,000')
assert customers.get_count() == c0 + 1
row = conn.execute('SELECT credit_limit, created_at FROM customers WHERE customer_id=900').fetchone()
assert row['credit_limit'] == 5000.0 and row['created_at'], tuple(row)   # REAL + created_at stamp
customers.update_customer(900, 'Alice Mansa', '0550000002', 'alice@x.com', 'Accra', '8,000')
assert conn.execute('SELECT credit_limit FROM customers WHERE customer_id=900').fetchone()[0] == 8000.0
# duplicate name rejected (UNIQUE)
before = len(messages)
assert customers.add_customer(901, 'Alice Mansa', '0200000000', 'a@a.com', 'x', '1') is False
assert any('already exists' in m[2] for m in messages[before:])
assert customers.get_balance(900) == 0.0
# credit sale links to the existing customer
sales.add_sale(410, 'Laptop Pro', '2', '3,000', '6,000.00', '04/08/2026', 'Alice Mansa',
               payment_mode='Credit')
assert conn.execute('SELECT customer_id FROM sales WHERE sale_id=410').fetchone()['customer_id'] == 900
assert customers.get_balance(900) == 6000.0
# credit sale to a brand-new name auto-creates the customer and links it
sales.add_sale(411, 'Laptop Pro', '1', '3,000', '3,000.00', '04/08/2026', 'Kofi Boateng',
               payment_mode='Credit')
kofi = conn.execute("SELECT customer_id FROM sales WHERE sale_id=411").fetchone()['customer_id']
assert kofi is not None and customers.get_balance(kofi) == 3000.0, kofi
# cash sale with a new name does NOT create a customer
sales.add_sale(412, 'Laptop Pro', '1', '3,000', '3,000.00', '04/08/2026', 'Walk-in')
assert conn.execute("SELECT customer_id FROM sales WHERE sale_id=412").fetchone()['customer_id'] is None
# a return on the credit sale reduces the outstanding balance
sales.add_return(410, 1, '05/08/2026')
assert customers.get_balance(900) == 3000.0
# a payment reduces the balance and is recorded with ISO date
assert customers.add_payment(900, 2_000.0, '06/08/2026', 'partial payment') is True
assert customers.get_balance(900) == 1000.0
prow = conn.execute('SELECT customer_id, amount, payment_date FROM credit_payments').fetchone()
assert tuple(prow) == (900, 2000.0, '2026-08-06'), tuple(prow)
# balances report only lists customers with credit activity
by_name = {r['name']: r['balance'] for r in customers.customer_balances_rows()}
assert by_name == {'Alice Mansa': 1000.0, 'Kofi Boateng': 3000.0}, by_name
# ledger shows sale/return/payment in date order with running balance
ledger = customers.customer_ledger_rows(900)
assert [e['kind'] for e in ledger] == ['Credit Sale', 'Return', 'Payment'], ledger
assert ledger[-1]['balance'] == 1000.0
# delete guard: customer with sales is blocked
before = len(messages)
assert customers.delete_customer(900) is False and any('sales' in m[2] for m in messages[before:])
# customer balances report renders
dlg = reports.show_customer_balances(root)
root.update()
dlg.destroy()
root.update()
# cleanup this block's data
conn.execute('DELETE FROM returns WHERE sale_id IN (410, 411, 412)')
conn.execute('DELETE FROM credit_payments')
conn.execute('DELETE FROM sales WHERE sale_id IN (410, 411, 412)')
conn.execute('DELETE FROM customers WHERE customer_id IN (900, ?)', (kofi,))
conn.commit()
print('customers (CRUD / credit tracking / payments / ledger / balances): OK')

# --- delete_guard: category with linked product cannot be deleted ---
products.add_product(301, 'Mouse', 'Electronics', 'Acme Supplies', '50', '5', 'Peripheral')
before = len(messages)
ok = categories.delete_category(200)
assert ok is False and any(m[0] == 'error' and 'linked' in m[2] for m in messages[before:])
ok = suppliers.delete_supplier(100)
assert ok is False
print('delete_guard (category/supplier with linked products): OK')

# --- cleanup test data ---
conn.execute('DELETE FROM returns')
conn.execute('DELETE FROM purchases')
conn.execute('DELETE FROM credit_payments')
conn.execute('DELETE FROM stock_movements')
conn.execute('DELETE FROM sales WHERE sale_id IN (400, 401, 402, 410, 411, 412)')
conn.execute('DELETE FROM products WHERE product_id IN (300, 301)')
conn.execute('DELETE FROM suppliers WHERE supplier_id=100')
conn.execute('DELETE FROM categories WHERE category_id=200')
conn.execute('DELETE FROM customers WHERE customer_id IN (900, 901)')
conn.commit()
conn.close()

print('counts:', employee.get_count(), suppliers.get_count(), categories.get_count(),
      products.get_count(), sales.get_count(), customers.get_count())

# --- form smoke test ---
products.product_form(root)
root.update()
print('ALL INTEGRATION TESTS PASSED')
root.destroy()
