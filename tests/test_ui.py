import re
import tkinter as tk

import testbase

import crud
import categories, customers, employee, products, purchases, returns, sales, suppliers
import reports

crud.messagebox.showerror = lambda t, m: print('ERR:', m)
crud.messagebox.showinfo = lambda t, m: print('INFO:', m)
crud.messagebox.askyesno = lambda t, m: True

conn = testbase.conn()

categories.add_category(200, 'Electronics', 'x')
suppliers.add_supplier(100, 'Acme Supplies', 'JD', 'a@b.com', '0200000000', 'Kumasi')
products.add_product(300, 'Laptop', 'Electronics', 'Acme Supplies', '2,500', '10', 'Pro')
employee.add_employee(600, 'UI Test', 'ui@test.com', '0201112222', '15/03/1990', 'Female', '2,000', 'Accra', 'Employee', 'secret')
customers.add_customer(700, 'UI Customer', '0201113333', 'ui@cust.com', 'Kumasi', '2,000')

root = tk.Tk()
root.geometry('+99999+99999')
root.update()


def walk(w, acc):
    acc.append(w)
    for c in w.winfo_children():
        walk(c, acc)
    return acc


def children(win):
    return walk(win, [])


def entries(win):
    return [e for e in children(win) if e.winfo_class() == 'Entry']


def dialogs(win):
    return [w for w in children(win) if w.winfo_class() == 'Toplevel']


def comboboxes(win):
    return [w for w in children(win) if w.winfo_class() == 'TCombobox']


def find_button(win, text):
    for w in children(win):
        if w.winfo_class() == 'Button' and str(w.cget('text')) == text:
            return w
    raise AssertionError(f'no button {text}')


_last_watchdog = None


def run_modal(btn_win, btn_text, probe):
    global _last_watchdog
    result = {}

    def wrapper():
        try:
            probe(result)
        except Exception as exc:
            result['error'] = repr(exc)

    def watchdog():
        for d in dialogs(root):
            d.destroy()

    if _last_watchdog is not None:
        try:
            root.after_cancel(_last_watchdog)
        except Exception:
            pass
    root.after(100, wrapper)
    _last_watchdog = root.after(10000, watchdog)
    find_button(btn_win, btn_text).invoke()
    if 'error' in result:
        raise AssertionError(result['error'])
    return result


# --- employee main screen: treeview shows masked pw, ISO date, salary format ---
employee.employee_form(root)
root.update()
tv = employee.employee_treeview
iid = next(i for i in tv.get_children() if tv.item(i)['values'][0] == 600)
tv.selection_set(iid)
tv.event_generate('<ButtonRelease-1>')
root.update()
vals = tv.item(iid)['values']
assert vals[9] == '********', vals[9]
assert vals[4] == '1990-03-15', vals[4]
assert vals[6] == '2,000.00', vals[6]
assert tv.set(iid, 'number') == '0201112222', tv.set(iid, 'number')


# --- employee update dialog: row prefilled, phone keeps zero, password blank ---
def probe_employee_update(result):
    dlg = dialogs(root)[0]
    dlg_entries = entries(dlg)
    result['employee_entries'] = [e.get() for e in dlg_entries]
    assert dlg_entries[0].get() == '600', dlg_entries[0].get()
    assert any(e.get() == '0201112222' for e in dlg_entries), dlg_entries
    assert any(e.get() == '2,000.00' for e in dlg_entries), dlg_entries
    assert not any(e.get() == 'secret' for e in dlg_entries), dlg_entries
    dlg.destroy()


run_modal(employee.employee_frame, 'Update', probe_employee_update)
print('employee: masked pw, ISO date, salary format, phone zero, modal prefill -> OK')


# --- sales add dialog: product select prefills price + total, Escape cancels ---
sales.sale_form(root)
root.update()


def probe_sales_add(result):
    dlg = dialogs(root)[0]
    prod = [c for c in comboboxes(dlg) if c.get() == 'Select Product'][0]
    prod.set('Laptop')
    prod.event_generate('<<ComboboxSelected>>')
    root.update()
    dlg_entries = entries(dlg)
    assert any(e.get() == '2,500.00' for e in dlg_entries), dlg_entries
    qty = [e for e in dlg_entries if e.grid_info().get('row') == 1
           and e.grid_info().get('column') == 1][0]
    qty.delete(0, 'end')
    qty.insert(0, '3')
    qty.focus_force()
    root.update()
    qty.event_generate('<KeyRelease>', when='now')
    root.update()
    total = [e for e in dlg_entries if e.grid_info().get('row') == 1
             and e.grid_info().get('column') == 5][0]
    result['total'] = total.get()
    assert total.get() == '7,500.00', total.get()
    assert any(c.get() == 'Cash' for c in comboboxes(dlg)), 'payment mode must default to Cash'
    previews = [str(w.cget('text')) for w in children(dlg) if w.winfo_class() == 'Label'
                and str(w.cget('text')).startswith('INV-')]
    assert previews and re.fullmatch(r'INV-\d{5}', previews[0]), previews
    cust_cb = [c for c in comboboxes(dlg) if c.get() == 'Select Customer']
    assert cust_cb, 'customer combobox should exist'
    cust_cb = cust_cb[0]
    assert 'UI Customer' in list(cust_cb.cget('values')), 'customer names must be listed'
    assert 'readonly' not in cust_cb.state(), 'customer field must be editable'
    prod.event_generate('<Escape>')
    root.update()
    assert not dialogs(root), 'dialog should be closed by Escape'


run_modal(sales.sale_frame, 'Add', probe_sales_add)
print('sales: modal price prefill + auto-total + payment default + invoice preview + customer source + Escape -> OK')


# --- stock movements report shows the initial-stock movement ---
moves = reports.stock_movements_rows('2026-01-01', '2099-12-31')
assert len(moves) == 1 and moves[0]['quantity_delta'] == 10 and moves[0]['reason'] == 'initial', moves
dlg = reports.show_stock_movements(root)
root.update()
print('stock movements report renders -> OK')
dlg.destroy()
root.update()


# --- reorder level + new reports ---
products.update_record({'product_id': 300, 'name': 'Laptop', 'category_id': 200,
                        'supplier_id': 100, 'price': '2,500', 'cost_price': '1,500',
                        'quantity': '10', 'reorder_level': '12', 'description': 'Pro'})
assert any(r['product'] == 'Laptop' for r in reports.low_stock_rows(5))
sales.add_sale(400, 'Laptop', '2', '2,500', '5,000.00', '01/08/2026', 'JD')
assert reports._top_sellers()[0]['units_sold'] == 2
assert reports._profit_by_product()[0]['profit'] == 2000.0
assert reports.stock_valuation_rows()[0]['value'] == 20000.0   # 8 * 2500
dlg = reports.show_stock_valuation(root)
root.update()
dlg.destroy()
dlg = reports.show_sales_analytics(root)
root.update()
dlg.destroy()
root.update()
print('reorder level + valuation/analytics reports render -> OK')


# --- returns form: sale source lists invoice numbers, selection shows returnable + customer ---
sales.add_sale(401, 'Laptop', '1', '2,500', '2,500.00', '01/08/2026', 'JD')
returns.return_form(root)
root.update()


def probe_return_add(result):
    dlg = dialogs(root)[0]
    sale_cb = [c for c in comboboxes(dlg) if c.get() == 'Select Sale']
    assert sale_cb, 'sale source combobox should exist'
    sale_cb = sale_cb[0]
    values = list(sale_cb.cget('values'))
    assert values and all(str(v).startswith('INV-') for v in values), values
    sale_cb.set(values[-1])
    sale_cb.event_generate('<<ComboboxSelected>>')
    root.update()
    labels = [str(w.cget('text')) for w in children(dlg) if w.winfo_class() == 'Label']
    assert any(t.startswith('Returnable:') for t in labels), labels
    assert any(t == 'JD' for t in labels), labels
    dlg.destroy()


run_modal(returns.return_frame, 'Add', probe_return_add)
print('returns: invoice-number sale source + returnable/customer prefill -> OK')
sales.delete_sale(401, 'Laptop', '1')


# --- purchases form + add dialog (sources, payment default, invoice preview) ---
purchases.purchase_form(root)
root.update()


def probe_purchase_add(result):
    dlg = dialogs(root)[0]
    assert any(c.get() == 'Cash' for c in comboboxes(dlg)), 'payment mode must default to Cash'
    previews = [str(w.cget('text')) for w in children(dlg) if w.winfo_class() == 'Label'
                and str(w.cget('text')).startswith('PO-')]
    assert previews and re.fullmatch(r'PO-\d{5}', previews[0]), previews
    assert [c for c in comboboxes(dlg) if c.get() == 'Select Supplier'], 'supplier source missing'
    assert [c for c in comboboxes(dlg) if c.get() == 'Select Product'], 'product source missing'
    dlg.destroy()


run_modal(purchases.purchase_frame, 'Add', probe_purchase_add)
print('purchases: supplier/product sources + payment default + invoice preview -> OK')


# --- reorder picker lists the low-stock product (qty 8 <= reorder 12) ---
dlg = reports.show_reorder_picker(root)
root.update()
tree = [w for w in children(dlg) if w.winfo_class() == 'Treeview'][0]
rows_vals = [tree.item(i)['values'] for i in tree.get_children()]
assert rows_vals and rows_vals[0][0] == 'Laptop', rows_vals
dlg.destroy()
root.update()
print('reorder picker lists low-stock products -> OK')


# --- customers: balance column, update balance label, payment dialog, balances report ---
customers.customers_form(root)
root.update()
tv = customers.customers_treeview
iid = next(i for i in tv.get_children() if tv.item(i)['values'][0] == 700)
vals = tv.item(iid)['values']
assert vals[5] == '2,000.00' and vals[6] == '0.00', vals
tv.selection_set(iid)
tv.event_generate('<ButtonRelease-1>')
root.update()


def probe_customer_update(result):
    dlg = dialogs(root)[0]
    labels = [str(w.cget('text')) for w in children(dlg) if w.winfo_class() == 'Label']
    assert any(t == 'Balance: 0.00' for t in labels), labels
    dlg.destroy()


run_modal(customers.customers_frame, 'Update', probe_customer_update)
print('customers: balance column + update dialog balance label -> OK')

# a credit sale for the UI customer so payments reduce a positive balance
sales.add_sale(402, 'Laptop', '1', '700', '700.00', '01/08/2026', 'UI Customer',
               payment_mode='Credit')
assert customers.get_balance(700) == 700.0, customers.get_balance(700)


def probe_payment(result):
    dlg = dialogs(root)[0]
    amt = [e for e in entries(dlg) if e.grid_info().get('row') == 2][0]
    amt.insert(0, '500')
    find_button(dlg, 'Save').invoke()
    root.update()
    result['balance'] = customers.get_balance(700)


result = run_modal(customers.customers_frame, 'Record Payment', probe_payment)
assert result['balance'] == 200.0, result
print('customers: record payment reduces outstanding balance -> OK')

dlg = reports.show_customer_balances(root)
root.update()
bal_tree = [w for w in children(dlg) if w.winfo_class() == 'Treeview'][0]
bal_rows = [bal_tree.item(i)['values'] for i in bal_tree.get_children()]
assert bal_rows and bal_rows[0][0] == 'UI Customer' and bal_rows[0][3] == '200.00', bal_rows
dlg.destroy()
root.update()
print('customer balances report lists credit customers -> OK')


# --- auto-generated ids: add dialog prefills a readonly id and save uses it ---
def probe_customer_add(result):
    dlg = dialogs(root)[0]
    dlg_entries = entries(dlg)
    assert str(dlg_entries[0].cget('state')) == 'readonly', dlg_entries[0].cget('state')
    expected = int(dlg_entries[0].get())
    assert expected > 0, expected
    dlg_entries[1].insert(0, 'Auto ID Customer')
    dlg_entries[2].insert(0, '0201119999')
    dlg_entries[3].insert(0, 'auto@cust.com')
    result['expected'] = expected
    find_button(dlg, 'Save').invoke()


result = run_modal(customers.customers_frame, 'Add', probe_customer_add)
row = conn.execute('SELECT customer_id, name FROM customers WHERE customer_id = ?',
                   (result['expected'],)).fetchone()
assert row is not None and row['name'] == 'Auto ID Customer', (result, row)
print(f'auto-generated customer id {result["expected"]} saved through the form -> OK')


# --- cleanup ---
conn.close()
print('ALL UI SMOKE TESTS PASSED')
root.destroy()
