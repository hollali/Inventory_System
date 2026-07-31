import os
import sqlite3
import sys
import tkinter as tk

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import crud
import categories, employee, products, sales, suppliers

crud.messagebox.showerror = lambda t, m: print('ERR:', m)
crud.messagebox.showinfo = lambda t, m: print('INFO:', m)
crud.messagebox.askyesno = lambda t, m: True

categories.add_category(200, 'Electronics', 'x')
suppliers.add_supplier(100, 'Acme Supplies', 'JD', 'a@b.com', '0200000000', 'Kumasi')
products.add_product(300, 'Laptop', 'Electronics', 'Acme Supplies', '2,500', '10', 'Pro')
employee.add_employee(600, 'UI Test', 'ui@test.com', '0201112222', '15/03/1990', 'Female', '2,000', 'Accra', 'Employee', 'secret')

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


def run_modal(btn_win, btn_text, probe):
    result = {}

    def wrapper():
        try:
            probe(result)
        except Exception as exc:
            result['error'] = repr(exc)

    def watchdog():
        for d in dialogs(root):
            d.destroy()

    root.after(100, wrapper)
    root.after(10000, watchdog)
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
    total = [e for e in dlg_entries if e.cget('state') == 'readonly'][0]
    result['total'] = total.get()
    assert total.get() == '7,500.00', total.get()
    prod.event_generate('<Escape>')
    root.update()
    assert not dialogs(root), 'dialog should be closed by Escape'


run_modal(sales.sale_frame, 'Add', probe_sales_add)
print('sales: modal price prefill + auto-total + Escape cancel -> OK')


# --- cleanup ---
conn = sqlite3.connect(os.path.join(ROOT, 'inventory_system.db'))
conn.execute('DELETE FROM sales WHERE sale_id IN (400, 401)')
conn.execute('DELETE FROM products WHERE product_id=300')
conn.execute('DELETE FROM suppliers WHERE supplier_id=100')
conn.execute('DELETE FROM categories WHERE category_id=200')
conn.execute('DELETE FROM employee_data WHERE empid=600')
conn.commit()
conn.close()
print('ALL UI SMOKE TESTS PASSED')
root.destroy()
