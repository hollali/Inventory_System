from datetime import datetime
from tkinter import *
from tkinter import ttk
from tkcalendar import DateEntry

import crud
import movements
from app_log import logger
from database import (commit, execute, is_integrity_error, query, query_one, rollback, to_iso_date)
from layout import (FONT_FAMILY, PRIMARY, FIELD_BG, ToolTip, button, export_to_csv,
                    fs, is_number, ph, px, pw, py, scale)

CUSTOMERS_SPEC = {
    'table': 'customers',
    'pk': 'customer_id',
    'pk_label': 'Customer Id',
    'title': 'Customer Details',
    'frame_global': 'customers_frame',
    'table_columns': ['customer_id', 'name', 'phone', 'email', 'address',
                      'credit_limit', 'created_at'],
    'columns': [
        ('customer_id', 'Customer Id', 100), ('name', 'Name', 230),
        ('phone', 'Phone', 170), ('email', 'Email', 260),
        ('address', 'Address', 240), ('credit_limit', 'Credit Limit', 120),
        ('balance', 'Balance', 120),
    ],
    'search': [('Id', 'c.customer_id'), ('Name', 'c.name'), ('Phone', 'c.phone')],
    'unique_msg': 'A customer with this name already exists',
    'no_selection_msg': 'Please select a customer',
    'delete_confirm': 'Are you sure you want to delete this customer?',
    'delete_guard': ('credit_payments', 'customer_id'),
    'delete_guard_msg': 'Cannot delete: this customer has credit payments. Record history exists.',
    'msg_insert': 'Customer added successfully',
    'msg_update': 'Customer updated successfully',
    'msg_delete': 'Customer deleted successfully',
    'fields': [
        {'key': 'customer_id', 'label': 'Customer Id', 'kind': 'entry', 'pos': (0, 0),
         'required': True, 'validate': 'positive_int', 'msg': 'Customer ID must be a whole number',
         'store': 'int'},
        {'key': 'name', 'label': 'Name', 'kind': 'entry', 'pos': (0, 2), 'required': True},
        {'key': 'phone', 'label': 'Phone', 'kind': 'entry', 'pos': (0, 4), 'required': True,
         'validate': 'phone', 'msg': 'Please enter a valid phone number'},
        {'key': 'email', 'label': 'Email', 'kind': 'entry', 'pos': (1, 0), 'required': True,
         'validate': 'email', 'msg': 'Please enter a valid email address'},
        {'key': 'address', 'label': 'Address', 'kind': 'text', 'pos': (1, 2), 'rowspan': 2,
         'width': 20, 'height': 2},
        {'key': 'credit_limit', 'label': 'Credit Limit', 'kind': 'entry', 'pos': (1, 4),
         'validate': 'number', 'positive': True, 'msg': 'Credit limit must be a positive number',
         'store': 'float', 'format': 'money', 'placeholder': '0'},
        {'key': 'balance', 'label': 'Balance', 'kind': 'label', 'pos': (2, 4),
         'label_text': '', 'format': 'money'},
    ],
}


def rows(where=None, params=()):
    sql = ('SELECT c.customer_id, c.name, c.phone, c.email, c.address, c.credit_limit, '
           'c.created_at, '
           "COALESCE((SELECT SUM(s.total) FROM sales s WHERE s.customer_id = c.customer_id "
           "AND s.payment_mode = 'Credit'), 0) "
           '- COALESCE((SELECT SUM(r.total) FROM returns r JOIN sales s2 ON s2.sale_id = r.sale_id '
           'WHERE s2.customer_id = c.customer_id), 0) '
           '- COALESCE((SELECT SUM(p.amount) FROM credit_payments p '
           'WHERE p.customer_id = c.customer_id), 0) AS balance '
           'FROM customers c')
    if where:
        sql += f' WHERE {where}'
    return [dict(row) for row in query(sql, params)]


def add_record(data):
    cleaned = crud.validate_data(CUSTOMERS_SPEC, data, 'add')
    if cleaned is None:
        return False
    if not cleaned.get('credit_limit'):
        cleaned['credit_limit'] = None
    cleaned['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return crud.insert_row(CUSTOMERS_SPEC, cleaned)


def update_record(data):
    cleaned = crud.validate_data(CUSTOMERS_SPEC, data, 'update')
    if cleaned is None:
        return False
    if not cleaned.get('credit_limit'):
        cleaned['credit_limit'] = None
    return crud.update_row(CUSTOMERS_SPEC, cleaned)


def delete_record(customer_id):
    linked = query_one('SELECT COUNT(*) AS n FROM sales WHERE customer_id = ?', (customer_id,))
    if linked and linked['n']:
        crud.messagebox.showerror(
            'Error', 'Cannot delete: sales are linked to this customer.')
        return False
    try:
        execute('DELETE FROM customers WHERE customer_id = ?', (customer_id,))
        commit()
        return True
    except Exception as exc:
        rollback()
        logger.exception('DELETE failed on customers')
        if is_integrity_error(exc):
            crud.messagebox.showerror(
                'Error', 'Cannot delete: this customer has credit payments. Record history exists.')
        else:
            crud.messagebox.showerror('Error', f'Database error: {exc}')
        return False


def add_customer(customer_id, name, phone, email, address, credit_limit):
    return add_record({'customer_id': customer_id, 'name': name, 'phone': phone,
                       'email': email, 'address': address,
                       'credit_limit': credit_limit})


def update_customer(customer_id, name, phone, email, address, credit_limit):
    return update_record({'customer_id': customer_id, 'name': name, 'phone': phone,
                          'email': email, 'address': address,
                          'credit_limit': credit_limit})


def delete_customer(customer_id):
    return delete_record(customer_id)


def search_customer(option, search_value):
    if option == 'Search By':
        crud.messagebox.showerror('Error', 'Please select a search option')
        return
    if search_value == '':
        crud.messagebox.showerror('Error', 'Search field is required')
        return
    column = dict(CUSTOMERS_SPEC['search']).get(option)
    if not column:
        crud.messagebox.showerror('Error', 'Please select a valid search option')
        return
    result = rows(where=f'{column} LIKE ?', params=(f'%{search_value}%',))
    crud.render_rows(CUSTOMERS_SPEC['treeview'], CUSTOMERS_SPEC, result)
    if not result:
        crud.messagebox.showinfo('No Records', 'No matching records found')


def get_count():
    return crud.count_rows(CUSTOMERS_SPEC)


def get_customer_names():
    return [row['name'] for row in query('SELECT name FROM customers ORDER BY name')]


def lookup_customer_id(name):
    return crud.lookup_id('customers', 'customer_id', 'name', name)


def find_customer_id(name):
    row = query_one('SELECT customer_id FROM customers WHERE lower(name) = lower(?) LIMIT 1',
                    (str(name).strip(),))
    return row['customer_id'] if row else None


def get_customer_name(customer_id):
    row = query_one('SELECT name FROM customers WHERE customer_id = ?', (customer_id,))
    return row['name'] if row else None


def get_balance(customer_id):
    row = query_one(
        "SELECT COALESCE(SUM(s.total), 0) "
        "- COALESCE((SELECT SUM(r.total) FROM returns r JOIN sales s2 ON s2.sale_id = r.sale_id "
        "WHERE s2.customer_id = ?), 0) "
        "- COALESCE((SELECT SUM(amount) FROM credit_payments WHERE customer_id = ?), 0) AS balance "
        "FROM sales s WHERE s.customer_id = ? AND s.payment_mode = 'Credit'",
        (customer_id, customer_id, customer_id))
    return round(row['balance'], 2) if row else 0.0


def customer_balances_rows():
    return [dict(row) for row in query(
        "SELECT c.customer_id, c.name, c.phone, c.credit_limit, "
        "COALESCE((SELECT SUM(s.total) FROM sales s WHERE s.customer_id = c.customer_id "
        "AND s.payment_mode = 'Credit'), 0) "
        "- COALESCE((SELECT SUM(r.total) FROM returns r JOIN sales s2 ON s2.sale_id = r.sale_id "
        "WHERE s2.customer_id = c.customer_id), 0) "
        "- COALESCE((SELECT SUM(p.amount) FROM credit_payments p "
        "WHERE p.customer_id = c.customer_id), 0) AS balance "
        "FROM customers c WHERE "
        "EXISTS (SELECT 1 FROM sales s WHERE s.customer_id = c.customer_id "
        "AND s.payment_mode = 'Credit') "
        "OR EXISTS (SELECT 1 FROM credit_payments p WHERE p.customer_id = c.customer_id) "
        "ORDER BY balance DESC, c.name")]


def customer_ledger_rows(customer_id):
    entries = [dict(row) for row in query(
        "SELECT s.sale_date AS dt, 'Credit Sale' AS kind, s.invoice_number AS ref, "
        's.total AS amount FROM sales s '
        "WHERE s.customer_id = ? AND s.payment_mode = 'Credit' "
        'UNION ALL '
        "SELECT r.return_date, 'Return', r.invoice_number, -r.total FROM returns r "
        'JOIN sales s2 ON s2.sale_id = r.sale_id WHERE s2.customer_id = ? '
        'UNION ALL '
        "SELECT p.payment_date, 'Payment', 'PAY-' || p.payment_id, -p.amount "
        'FROM credit_payments p WHERE p.customer_id = ? '
        'ORDER BY dt, kind', (customer_id, customer_id, customer_id))]
    running = 0
    for entry in entries:
        running += entry['amount'] or 0
        entry['balance'] = round(running, 2)
    return entries


def add_payment(customer_id, amount, payment_date, note=None):
    payment_date = to_iso_date(payment_date)
    if not customer_id or amount is None or not payment_date:
        crud.messagebox.showerror('Error', 'Customer, amount and payment date are required')
        return False
    try:
        customer = query_one('SELECT customer_id FROM customers WHERE customer_id = ?',
                             (customer_id,))
        if customer is None:
            crud.messagebox.showerror('Error', 'Selected customer not found')
            return False
        created_by = None
        if isinstance(movements.current_user, dict):
            created_by = movements.current_user.get('empid')
        execute('INSERT INTO credit_payments (customer_id, amount, payment_date, note, '
                'created_by, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                (customer_id, amount, payment_date, note, created_by,
                 datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        commit()
        return True
    except Exception as exc:
        rollback()
        logger.exception('add_payment failed')
        crud.messagebox.showerror('Error', f'Database error: {exc}')
        return False


def delete_payment(payment_id):
    try:
        execute('DELETE FROM credit_payments WHERE payment_id = ?', (payment_id,))
        commit()
        return True
    except Exception as exc:
        rollback()
        logger.exception('delete_payment failed')
        crud.messagebox.showerror('Error', f'Database error: {exc}')
        return False


def export_customer_csv():
    records = [tuple(row[key] for key in ('customer_id', 'name', 'phone', 'email', 'address',
                                          'credit_limit', 'balance')) for row in rows()]
    export_to_csv(None, ('Customer Id', 'Name', 'Phone', 'Email', 'Address',
                         'Credit Limit', 'Balance'), records, 'customers.csv')


def _decorate(detail_frame, widgets, mode):
    if mode == 'update':
        customer_id = CUSTOMERS_SPEC.get('selected')
        widgets['balance'].config(text=f'Balance: {get_balance(customer_id):,.2f}')


CUSTOMERS_SPEC['decorate'] = _decorate

customers_treeview = None
customers_frame = None


def _center_payment_dialog(dialog, window, width, height, SX, SY):
    dialog.update_idletasks()
    x = window.winfo_rootx() + max((window.winfo_width() - px(SX, width)) // 2, 0)
    y = window.winfo_rooty() + max((window.winfo_height() - py(SY, height)) // 2, 0)
    dialog.geometry(f'{px(SX, width)}x{py(SY, height)}+{x}+{y}')


def show_payment_dialog(window, customer_id):
    customer = query_one('SELECT name FROM customers WHERE customer_id = ?', (customer_id,))
    if customer is None:
        crud.messagebox.showerror('Error', 'Please select a customer first')
        return None
    SX, SY = scale(window)
    dialog = Toplevel(window)
    dialog.title('Record Payment')
    dialog.configure(bg='white')
    dialog.resizable(False, False)
    dialog.transient(window)
    dialog.grab_set()
    dialog.protocol('WM_DELETE_WINDOW', dialog.destroy)

    body = Frame(dialog, bg='white')
    body.pack(padx=px(SX, 30), pady=py(SY, 20))

    Label(body, text=f'Customer: {customer["name"]}',
          font=(FONT_FAMILY, fs(SY, 13), 'bold'), bg='white').grid(
        row=0, column=0, columnspan=2, sticky='w', pady=py(SY, 4))
    Label(body, text=f'Outstanding balance: {get_balance(customer_id):,.2f}',
          font=(FONT_FAMILY, fs(SY, 12)), bg='white', fg='#666666').grid(
        row=1, column=0, columnspan=2, sticky='w', pady=py(SY, 4))

    Label(body, text='Amount:', font=(FONT_FAMILY, fs(SY, 13), 'bold'), bg='white').grid(
        row=2, column=0, sticky='w', padx=(px(SX, 10), px(SX, 10)), pady=py(SY, 8))
    amount_entry = Entry(body, font=(FONT_FAMILY, fs(SY, 13), 'bold'), bg=FIELD_BG)
    amount_entry.grid(row=2, column=1, pady=py(SY, 8))

    Label(body, text='Date:', font=(FONT_FAMILY, fs(SY, 13), 'bold'), bg='white').grid(
        row=3, column=0, sticky='w', padx=(px(SX, 10), px(SX, 10)), pady=py(SY, 8))
    date_entry = DateEntry(body, width=14, font=(FONT_FAMILY, fs(SY, 13)),
                           state='readonly', date_pattern='yyyy-mm-dd', bg='white')
    date_entry.set_date(datetime.now())
    date_entry.grid(row=3, column=1, pady=py(SY, 8))

    Label(body, text='Note:', font=(FONT_FAMILY, fs(SY, 13), 'bold'), bg='white').grid(
        row=4, column=0, sticky='w', padx=(px(SX, 10), px(SX, 10)), pady=py(SY, 8))
    note_entry = Entry(body, font=(FONT_FAMILY, fs(SY, 13), 'bold'), bg=FIELD_BG, width=20)
    note_entry.grid(row=4, column=1, pady=py(SY, 8))

    result = {'saved': False}

    def do_save():
        value = amount_entry.get().strip()
        if not is_number(value, positive=True):
            crud.messagebox.showerror('Error', 'Amount must be a positive number')
            return
        if add_payment(customer_id, float(value.replace(',', '')), date_entry.get(),
                       note_entry.get().strip() or None):
            result['saved'] = True
            dialog.destroy()

    controls = Frame(body, bg='white')
    controls.grid(row=5, column=0, columnspan=2, pady=py(SY, 10))
    button(controls, 'Save', font_size=fs(SY, 12), command=do_save).pack(side=LEFT, padx=px(SX, 12))
    button(controls, 'Cancel', font_size=fs(SY, 12), command=dialog.destroy).pack(side=LEFT, padx=px(SX, 12))

    dialog.bind('<Escape>', lambda e: dialog.destroy())
    amount_entry.focus_set()
    _center_payment_dialog(dialog, window, 400, 300, SX, SY)
    dialog.wait_window()
    return True if result['saved'] else None


def show_customer_ledger(window, customer_id):
    customer = query_one('SELECT name FROM customers WHERE customer_id = ?', (customer_id,))
    if customer is None:
        crud.messagebox.showerror('Error', 'Please select a customer first')
        return None
    SX, SY = scale(window)
    dialog = Toplevel(window)
    dialog.title(f'Ledger - {customer["name"]}')
    dialog.configure(bg='white')
    dialog.transient(window)
    dialog.grab_set()
    dialog.protocol('WM_DELETE_WINDOW', dialog.destroy)

    Label(dialog, text=f'Credit Ledger - {customer["name"]}',
          font=(FONT_FAMILY, fs(SY, 16), 'bold'), bg=PRIMARY, fg='white').pack(fill=X)

    style = ttk.Style()
    style.theme_use('clam')
    style.configure('Treeview', background='white', foreground='black',
                    rowheight=max(25, py(SY, 25)), fieldbackground='white',
                    bordercolor='gray', borderwidth=1, relief='solid')
    style.configure('Treeview.Heading', font=(FONT_FAMILY, fs(SY, 11), 'bold'),
                    background='#f2f2f2', bordercolor='#d0d0d0', borderwidth=1, relief='solid')
    style.map('Treeview', background=[('selected', '#cce5ff')])

    tree_frame = Frame(dialog, bg='white')
    vertical_scrollbar = Scrollbar(tree_frame, orient=VERTICAL)
    tree = ttk.Treeview(tree_frame, columns=('date', 'kind', 'reference', 'amount', 'balance'),
                        show='headings', yscrollcommand=vertical_scrollbar.set)
    vertical_scrollbar.config(command=tree.yview)
    vertical_scrollbar.pack(side=RIGHT, fill=Y)
    tree.pack(fill=BOTH, expand=True)
    for column_id, label, width in (('date', 'Date', 110), ('kind', 'Type', 100),
                                    ('reference', 'Reference', 120),
                                    ('amount', 'Amount', 120), ('balance', 'Balance', 120)):
        tree.heading(column_id, text=label)
        tree.column(column_id, width=px(SX, width), anchor=CENTER)
    tree_frame.pack(fill=BOTH, expand=True, padx=px(SX, 20), pady=py(SY, 5))

    summary_label = Label(dialog, bg='white', font=(FONT_FAMILY, fs(SY, 13), 'bold'))
    summary_label.pack(pady=py(SY, 5))

    def refresh():
        entries = customer_ledger_rows(customer_id)
        tree.delete(*tree.get_children())
        for entry in entries:
            tree.insert('', END, values=(entry['dt'], entry['kind'], entry['ref'],
                                         f'{entry["amount"]:,.2f}', f'{entry["balance"]:,.2f}'))
        summary_label.config(
            text=f'{len(entries)} entry(s) | Outstanding balance: {get_balance(customer_id):,.2f}')

    def export():
        entries = customer_ledger_rows(customer_id)
        export_to_csv(dialog, ('Date', 'Type', 'Reference', 'Amount', 'Running Balance'),
                      [(e['dt'], e['kind'], e['ref'], e['amount'], e['balance'])
                       for e in entries], f'ledger_customer_{customer_id}.csv')

    controls = Frame(dialog, bg='white')
    controls.pack(pady=py(SY, 10))
    button(controls, 'Refresh', font_size=fs(SY, 11), command=refresh).pack(side=LEFT, padx=px(SX, 10))
    button(controls, 'Export CSV', font_size=fs(SY, 11), command=export).pack(side=LEFT, padx=px(SX, 10))
    button(controls, 'Close', font_size=fs(SY, 11), command=dialog.destroy).pack(side=LEFT, padx=px(SX, 10))

    dialog.bind('<Escape>', lambda e: dialog.destroy())
    refresh()
    _center_payment_dialog(dialog, window, 700, 480, SX, SY)
    return dialog


def customers_form(window, on_close=None):
    global customers_treeview, customers_frame

    def record_payment():
        customer_id = CUSTOMERS_SPEC.get('selected')
        if customer_id is None:
            crud.messagebox.showerror('Error', 'Please select a customer to record a payment')
            return
        if show_payment_dialog(window, customer_id):
            render_customers()

    def view_ledger():
        customer_id = CUSTOMERS_SPEC.get('selected')
        if customer_id is None:
            crud.messagebox.showerror('Error', 'Please select a customer to view its ledger')
            return
        show_customer_ledger(window, customer_id)

    def render_customers():
        crud.render_rows(customers_treeview, CUSTOMERS_SPEC, rows())

    customers_frame, customers_treeview = crud.build_form(window, CUSTOMERS_SPEC, {
        'rows': rows,
        'add': add_record,
        'update': update_record,
        'delete': delete_record,
        'search': search_customer,
        'count': get_count,
        'export_csv': export_customer_csv,
        'extra_buttons': [
            ('Record Payment', record_payment,
             'Record a payment against this customer\'s outstanding credit'),
            ('View Ledger', view_ledger,
             'Show credit sales, returns and payments for this customer'),
        ],
    }, on_close=on_close)
    return customers_frame
