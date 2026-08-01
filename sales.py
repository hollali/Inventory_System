import crud
import movements
import customers
from app_log import logger
from database import (commit, execute, is_integrity_error, next_invoice_number, query,
                      query_one, rollback, to_iso_date)
from products import get_product_details
from layout import FIELD_BG, FONT_FAMILY, PRIMARY, button, fs, px, py, scale
from tkinter import *
from tkinter import ttk
from tkcalendar import DateEntry
import reports
from datetime import datetime

SALES_SPEC = {
    'table': 'sales',
    'pk': 'sale_id',
    'pk_label': 'Sale Id',
    'title': 'Sales Details',
    'frame_global': 'sale_frame',
    'table_columns': ['sale_id', 'invoice_number', 'product_id', 'quantity', 'unit_price',
                      'total', 'sale_date', 'customer', 'payment_mode'],
    'columns': [
        ('sale_id', 'Sale Id', 90), ('invoice_number', 'Invoice', 110),
        ('product', 'Product', 200), ('quantity', 'Quantity', 90),
        ('unit_price', 'Unit Price', 110), ('total', 'Total', 110),
        ('sale_date', 'Sale Date', 120), ('customer', 'Customer', 170),
        ('payment_mode', 'Payment', 100),
    ],
    'search': [('Id', 's.sale_id'), ('Invoice', 's.invoice_number'),
               ('Product', 'p.name'), ('Customer', 's.customer')],
    'unique_msg': 'Sale ID must be unique',
    'no_selection_msg': 'Please select a sale to delete',
    'delete_confirm': 'Are you sure you want to delete this sale? Stock will be restored.',
    'delete_guard': ('returns', 'sale_id'),
    'delete_guard_msg': 'Cannot delete: this sale has returns. Delete the returns first.',
    'msg_insert': 'Sale recorded successfully',
    'msg_update': 'Sale updated successfully',
    'msg_delete': 'Sale deleted and stock restored',
    'fields': [
        {'key': 'sale_id', 'label': 'Sale Id', 'kind': 'entry', 'pos': (0, 0), 'required': True,
         'validate': 'positive_int', 'msg': 'Sale ID must be a whole number', 'store': 'int'},
        {'key': 'invoice_no', 'label': 'Invoice No.', 'kind': 'label', 'pos': (3, 0),
         'label_text': ''},
        {'key': 'product_id', 'label': 'Product', 'kind': 'source', 'pos': (0, 2),
         'source': ('products', 'product_id', 'name'), 'placeholder': 'Select Product',
         'display_key': 'product', 'required': True, 'msg': 'Please select a product'},
        {'key': 'available', 'label': '', 'kind': 'label', 'pos': (0, 4),
         'label_text': 'Available: -'},
        {'key': 'quantity', 'label': 'Quantity', 'kind': 'entry', 'pos': (1, 0), 'required': True,
         'validate': 'positive_int', 'msg': 'Quantity must be a positive whole number',
         'store': 'int', 'format': 'int'},
        {'key': 'unit_price', 'label': 'Unit Price', 'kind': 'entry', 'pos': (1, 2),
         'required': True, 'validate': 'number', 'positive': True,
         'msg': 'Unit price must be a positive number', 'store': 'float', 'format': 'money'},
        {'key': 'total', 'label': 'Total', 'kind': 'entry', 'pos': (1, 4), 'required': True,
         'validate': 'number', 'msg': 'Total must be a number', 'store': 'float',
         'format': 'money', 'readonly': True},
        {'key': 'sale_date', 'label': 'Sale Date', 'kind': 'date', 'pos': (2, 0),
         'required': True, 'store': 'date', 'default_today': True},
        {'key': 'customer', 'label': 'Customer', 'kind': 'combobox', 'pos': (2, 2),
         'placeholder': 'Select Customer', 'required': True,
         'msg': 'Please select or type a customer'},
        {'key': 'payment_mode', 'label': 'Payment', 'kind': 'combobox', 'pos': (2, 4),
         'options': ['Cash', 'Credit'], 'default': 'Cash'},
    ],
}


def rows(where=None, params=()):
    sql = ('SELECT s.sale_id, s.invoice_number, p.name AS product, s.quantity, s.unit_price, '
           's.total, s.sale_date, s.customer, s.payment_mode '
           'FROM sales s LEFT JOIN products p ON p.product_id = s.product_id')
    if where:
        sql += f' WHERE {where}'
    return [dict(row) for row in query(sql, params)]


def _resolve_customer(name, payment_mode):
    name = (name or '').strip()
    if not name:
        return None
    customer_id = customers.find_customer_id(name)
    if customer_id is not None:
        return customer_id
    if payment_mode == 'Credit':
        cursor = execute('INSERT INTO customers (name, created_at) VALUES (?, ?)',
                         (name, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        return cursor.lastrowid
    return None


def _credit_within_limit(customer_id, new_total, old_total, payment_mode,
                         old_payment_mode=None, old_customer_id=None):
    if payment_mode != 'Credit' or not customer_id:
        return True
    limit_row = query_one('SELECT credit_limit FROM customers WHERE customer_id = ?',
                          (customer_id,))
    limit = limit_row['credit_limit'] if limit_row and limit_row['credit_limit'] is not None else 0
    if limit <= 0:
        return True
    old_contrib = (old_total or 0) if (old_payment_mode == 'Credit'
                                       and old_customer_id == customer_id) else 0
    projected = customers.get_balance(customer_id) - old_contrib + (new_total or 0)
    if projected > limit + 0.005:
        crud.messagebox.showerror(
            'Error',
            f'Credit limit exceeded: new balance {projected:,.2f} would exceed '
            f'the limit of {limit:,.2f}')
        return False
    return True


def add_record(data):
    cleaned = crud.validate_data(SALES_SPEC, data, 'add')
    if cleaned is None:
        return False
    cleaned['total'] = round(cleaned['quantity'] * cleaned['unit_price'], 2)
    cleaned['invoice_number'] = next_invoice_number('INV', 'sales')
    cleaned['customer_id'] = _resolve_customer(cleaned.get('customer'),
                                               cleaned.get('payment_mode') or 'Cash')
    try:
        stock_row = query_one('SELECT quantity AS n FROM products WHERE product_id = ?',
                              (cleaned['product_id'],))
        stock = stock_row['n'] if stock_row and stock_row['n'] is not None else 0
        if cleaned['quantity'] > stock:
            crud.messagebox.showerror('Error', f'Insufficient stock available (in stock: {stock})')
            return False
        if not _credit_within_limit(cleaned.get('customer_id'), cleaned['total'], None,
                                    cleaned.get('payment_mode') or 'Cash'):
            rollback()
            return False
        execute('INSERT INTO sales (sale_id, invoice_number, product_id, quantity, unit_price, '
                'total, sale_date, customer, payment_mode, customer_id) '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (cleaned['sale_id'], cleaned['invoice_number'], cleaned['product_id'],
                 cleaned['quantity'], cleaned['unit_price'], cleaned['total'],
                 cleaned['sale_date'], cleaned['customer'],
                 cleaned.get('payment_mode') or 'Cash', cleaned['customer_id']))
        execute('UPDATE products SET quantity = quantity - ? WHERE product_id = ?',
                (cleaned['quantity'], cleaned['product_id']))
        movements.log_movement(cleaned['product_id'], -cleaned['quantity'], 'sale',
                               reference_id=cleaned['sale_id'])
        commit()
        return True
    except Exception as exc:
        rollback()
        logger.exception('add_record failed on sales')
        if is_integrity_error(exc):
            crud.messagebox.showerror('Error', 'Sale ID must be unique')
        else:
            crud.messagebox.showerror('Error', f'Database error: {exc}')
        return False


def update_record(data):
    cleaned = crud.validate_data(SALES_SPEC, data, 'update')
    if cleaned is None:
        return False
    cleaned['total'] = round(cleaned['quantity'] * cleaned['unit_price'], 2)
    cleaned['customer_id'] = _resolve_customer(cleaned.get('customer'),
                                               cleaned.get('payment_mode') or 'Cash')
    try:
        old = query_one('SELECT product_id, quantity, total, customer_id, payment_mode '
                        'FROM sales WHERE sale_id = ?', (cleaned['sale_id'],))
        if old is None:
            crud.messagebox.showerror('Error', f"No record found with that {SALES_SPEC['pk_label']}")
            return False
        if old['product_id'] is not None:
            execute('UPDATE products SET quantity = quantity + ? WHERE product_id = ?',
                    (old['quantity'], old['product_id']))
        stock_row = query_one('SELECT quantity AS n FROM products WHERE product_id = ?',
                              (cleaned['product_id'],))
        stock = stock_row['n'] if stock_row and stock_row['n'] is not None else 0
        if cleaned['quantity'] > stock:
            rollback()
            crud.messagebox.showerror('Error', f'Insufficient stock available (in stock: {stock})')
            return False
        if not _credit_within_limit(cleaned.get('customer_id'), cleaned['total'],
                                    old.get('total'), cleaned.get('payment_mode') or 'Cash',
                                    old.get('payment_mode'), old.get('customer_id')):
            rollback()
            return False
        execute('UPDATE products SET quantity = quantity - ? WHERE product_id = ?',
                (cleaned['quantity'], cleaned['product_id']))
        execute('UPDATE sales SET product_id = ?, quantity = ?, unit_price = ?, total = ?, '
                'sale_date = ?, customer = ?, payment_mode = ?, customer_id = ? WHERE sale_id = ?',
                (cleaned['product_id'], cleaned['quantity'], cleaned['unit_price'],
                 cleaned['total'], cleaned['sale_date'], cleaned['customer'],
                 cleaned.get('payment_mode') or 'Cash', cleaned['customer_id'],
                 cleaned['sale_id']))
        if old['product_id'] is not None and old['product_id'] != cleaned['product_id']:
            movements.log_movement(old['product_id'], old['quantity'], 'sale_update',
                                   reference_id=cleaned['sale_id'])
        movements.log_movement(cleaned['product_id'],
                               old['quantity'] - cleaned['quantity'] if
                               old['product_id'] == cleaned['product_id'] else -cleaned['quantity'],
                               'sale_update', reference_id=cleaned['sale_id'])
        commit()
        return True
    except Exception as exc:
        rollback()
        logger.exception('update_record failed on sales')
        if is_integrity_error(exc):
            crud.messagebox.showerror('Error', 'Sale ID must be unique')
        else:
            crud.messagebox.showerror('Error', f'Database error: {exc}')
        return False


def delete_record(sale_id):
    try:
        linked = query_one('SELECT COUNT(*) AS n FROM returns WHERE sale_id = ?', (sale_id,))
        if linked and linked['n']:
            crud.messagebox.showerror(
                'Error', 'Cannot delete: this sale has returns. Delete the returns first.')
            return False
        row = query_one('SELECT product_id, quantity FROM sales WHERE sale_id = ?', (sale_id,))
        if row and row['product_id'] is not None:
            execute('UPDATE products SET quantity = quantity + ? WHERE product_id = ?',
                    (row['quantity'], row['product_id']))
            movements.log_movement(row['product_id'], row['quantity'], 'sale_delete',
                                   reference_id=sale_id)
        execute('DELETE FROM sales WHERE sale_id = ?', (sale_id,))
        commit()
        return True
    except Exception as exc:
        rollback()
        logger.exception('delete_record failed on sales')
        crud.messagebox.showerror('Error', f'Database error: {exc}')
        return False


def add_sale(sale_id, product, quantity, unit_price, total, sale_date, customer,
             customer_id=None, payment_mode='Cash'):
    return add_record({
        'sale_id': sale_id,
        'product_id': crud.lookup_id('products', 'product_id', 'name', product),
        'quantity': quantity, 'unit_price': unit_price, 'total': total,
        'sale_date': sale_date, 'customer': customer,
        'customer_id': customer_id, 'payment_mode': payment_mode})


def add_order(lines, sale_date, customer, payment_mode='Cash', customer_id=None,
              invoice_number=None):
    """Record a multi-line sale where every line shares one invoice number.

    `lines` is a list of dicts with 'product_id' (or 'product' name),
    'quantity' and 'unit_price'. Stock is deducted atomically for all lines;
    on any failure everything is rolled back. Returns the invoice number on
    success, None on failure.
    """
    if not lines:
        crud.messagebox.showerror('Error', 'Add at least one item to the sale')
        return None
    sale_date = to_iso_date(sale_date)
    if not sale_date:
        crud.messagebox.showerror('Error', 'Sale Date is required')
        return None
    payment_mode = payment_mode or 'Cash'
    invoice = invoice_number or next_invoice_number('INV', 'sales')
    customer_id = _resolve_customer(customer, payment_mode)

    prepared = []
    for line in lines:
        product_id = line.get('product_id')
        if product_id is None:
            product_id = crud.lookup_id('products', 'product_id', 'name', line.get('product'))
        if product_id is None:
            crud.messagebox.showerror('Error', 'Please select a product for every line')
            return None
        try:
            quantity = int(str(line.get('quantity')).strip())
            unit_price = float(str(line.get('unit_price')).strip().replace(',', ''))
        except (TypeError, ValueError):
            crud.messagebox.showerror('Error', 'Every line needs a quantity and a unit price')
            return None
        if quantity <= 0 or unit_price < 0:
            crud.messagebox.showerror(
                'Error', 'Quantity must be a positive whole number and price cannot be negative')
            return None
        prepared.append((product_id, quantity, unit_price))

    total = round(sum(quantity * unit_price for _, quantity, unit_price in prepared), 2)
    if not _credit_within_limit(customer_id, total, None, payment_mode):
        return None

    try:
        for product_id, quantity, unit_price in prepared:
            stock_row = query_one('SELECT quantity AS n FROM products WHERE product_id = ?',
                                  (product_id,))
            stock = stock_row['n'] if stock_row and stock_row['n'] is not None else 0
            if quantity > stock:
                crud.messagebox.showerror(
                    'Error', f'Insufficient stock for {quantity} unit(s) (in stock: {stock})')
                return None
        for product_id, quantity, unit_price in prepared:
            line_total = round(quantity * unit_price, 2)
            cursor = execute(
                'INSERT INTO sales (invoice_number, product_id, quantity, unit_price, total, '
                'sale_date, customer, payment_mode, customer_id) '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (invoice, product_id, quantity, unit_price, line_total, sale_date,
                 customer, payment_mode, customer_id))
            new_id = cursor.lastrowid
            execute('UPDATE products SET quantity = quantity - ? WHERE product_id = ?',
                    (quantity, product_id))
            movements.log_movement(product_id, -quantity, 'sale', reference_id=new_id)
        commit()
        return invoice
    except Exception as exc:
        rollback()
        logger.exception('add_order failed')
        crud.messagebox.showerror('Error', f'Database error: {exc}')
        return None


def update_sale(sale_id, product, quantity, unit_price, total, sale_date, customer,
                old_product, old_quantity, customer_id=None, payment_mode=None):
    data = {
        'sale_id': sale_id,
        'product_id': crud.lookup_id('products', 'product_id', 'name', product),
        'quantity': quantity, 'unit_price': unit_price, 'total': total,
        'sale_date': sale_date, 'customer': customer,
        'customer_id': customer_id}
    if payment_mode is not None:
        data['payment_mode'] = payment_mode
    return update_record(data)


def delete_sale(sale_id, product, quantity):
    return delete_record(sale_id)


def returnable_quantity(sale_id):
    sale = query_one('SELECT quantity FROM sales WHERE sale_id = ?', (sale_id,))
    if sale is None:
        return 0
    returned = query_one('SELECT COALESCE(SUM(quantity), 0) AS n FROM returns WHERE sale_id = ?',
                         (sale_id,))
    return max(sale['quantity'] - (returned['n'] if returned else 0), 0)


def record_return(data):
    sale_id = data.get('sale_id')
    quantity = data.get('quantity')
    return_date = to_iso_date(data.get('return_date'))
    if not sale_id or not quantity or not return_date:
        crud.messagebox.showerror('Error', 'All fields are required')
        return False
    try:
        sale = query_one('SELECT sale_id, product_id, quantity, unit_price, customer, '
                         'invoice_number FROM sales WHERE sale_id = ?', (sale_id,))
        if sale is None:
            crud.messagebox.showerror('Error', 'Selected sale not found')
            return False
        remaining = returnable_quantity(sale_id)
        if quantity > remaining:
            crud.messagebox.showerror(
                'Error', f'Only {remaining} unit(s) can be returned for this sale')
            return False
        execute('INSERT INTO returns (sale_id, product_id, quantity, unit_price, total, '
                'return_date, customer, invoice_number) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (sale_id, sale['product_id'], quantity, sale['unit_price'],
                 round(quantity * sale['unit_price'], 2), return_date,
                 sale['customer'], sale['invoice_number']))
        execute('UPDATE products SET quantity = quantity + ? WHERE product_id = ?',
                (quantity, sale['product_id']))
        movements.log_movement(sale['product_id'], quantity, 'return', reference_id=sale_id)
        commit()
        return True
    except Exception as exc:
        rollback()
        logger.exception('record_return failed')
        crud.messagebox.showerror('Error', f'Database error: {exc}')
        return False


def update_return(data):
    return_id = data.get('return_id')
    quantity = data.get('quantity')
    return_date = to_iso_date(data.get('return_date'))
    if not return_id or not quantity or not return_date:
        crud.messagebox.showerror('Error', 'All fields are required')
        return False
    try:
        old = query_one('SELECT sale_id, product_id, quantity FROM returns WHERE return_id = ?',
                        (return_id,))
        if old is None:
            crud.messagebox.showerror('Error', 'Return record not found')
            return False
        returned = query_one(
            'SELECT COALESCE(SUM(quantity), 0) AS n FROM returns '
            'WHERE sale_id = ? AND return_id != ?', (old['sale_id'], return_id))
        remaining = returnable_quantity(old['sale_id']) + old['quantity']
        if quantity > remaining:
            crud.messagebox.showerror(
                'Error', f'Only {remaining} unit(s) can be returned for this sale')
            return False
        execute('UPDATE returns SET quantity = ?, return_date = ? WHERE return_id = ?',
                (quantity, return_date, return_id))
        net = quantity - old['quantity']
        execute('UPDATE products SET quantity = quantity + ? WHERE product_id = ?',
                (net, old['product_id']))
        movements.log_movement(old['product_id'], net, 'return_update',
                               reference_id=old['sale_id'])
        commit()
        return True
    except Exception as exc:
        rollback()
        logger.exception('update_return failed')
        crud.messagebox.showerror('Error', f'Database error: {exc}')
        return False


def delete_return(return_id):
    try:
        row = query_one('SELECT sale_id, product_id, quantity FROM returns WHERE return_id = ?',
                        (return_id,))
        if row is None:
            crud.messagebox.showerror('Error', 'Return record not found')
            return False
        execute('UPDATE products SET quantity = quantity - ? WHERE product_id = ?',
                (row['quantity'], row['product_id']))
        execute('DELETE FROM returns WHERE return_id = ?', (return_id,))
        movements.log_movement(row['product_id'], -row['quantity'], 'return_delete',
                               reference_id=row['sale_id'])
        commit()
        return True
    except Exception as exc:
        rollback()
        logger.exception('delete_return failed')
        crud.messagebox.showerror('Error', f'Database error: {exc}')
        return False


def add_return(sale_id, quantity, return_date):
    return record_return({'sale_id': sale_id, 'quantity': quantity,
                          'return_date': return_date})


def search_sale(option, search_value):
    if option == 'Search By':
        crud.messagebox.showerror('Error', 'Please select a search option')
        return
    if search_value == '':
        crud.messagebox.showerror('Error', 'Search field is required')
        return
    column = dict(SALES_SPEC['search']).get(option)
    if not column:
        crud.messagebox.showerror('Error', 'Please select a valid search option')
        return
    result = rows(where=f'{column} LIKE ?', params=(f'%{search_value}%',))
    crud.render_rows(SALES_SPEC['treeview'], SALES_SPEC, result)
    if not result:
        crud.messagebox.showinfo('No Records', 'No matching records found')


def get_count():
    return crud.count_rows(SALES_SPEC)


def get_order_count():
    row = query_one("SELECT COUNT(DISTINCT invoice_number) AS n FROM sales "
                    "WHERE invoice_number IS NOT NULL AND TRIM(invoice_number) != ''")
    return row['n'] if row else 0


def get_total_revenue():
    return sum(row['total'] or 0 for row in query('SELECT total FROM sales'))


def export_sale_csv():
    records = [tuple(row[key] for key in ('sale_id', 'invoice_number', 'product', 'quantity',
                                          'unit_price', 'total', 'sale_date', 'customer',
                                          'payment_mode')) for row in rows()]
    from layout import export_to_csv
    export_to_csv(None, ('Sale Id', 'Invoice', 'Product', 'Quantity', 'Unit Price', 'Total',
                         'Sale Date', 'Customer', 'Payment'), records, 'sales.csv')


def _decorate(detail_frame, widgets, mode):
    widgets['customer'].config(values=customers.get_customer_names())
    widgets['customer'].config(state='normal')

    def calculate_total(*args):
        try:
            quantity = int(widgets['quantity'].get().strip())
            price = float(widgets['unit_price'].get().strip().replace(',', ''))
            crud.set_widget(widgets['total'], f'{quantity * price:,.2f}')
        except (ValueError, TypeError):
            crud.set_widget(widgets['total'], '')

    def on_product_select(event):
        name = widgets['product_id'].get()
        if name == 'Select Product':
            return
        details = get_product_details(name)
        if details:
            price, stock = details
            crud.set_widget(widgets['unit_price'], f'{price:,.2f}')
            widgets['available'].config(text=f'Available: {stock}')
            calculate_total()

    widgets['product_id'].bind('<<ComboboxSelected>>', on_product_select)
    widgets['quantity'].bind('<KeyRelease>', calculate_total)
    widgets['unit_price'].bind('<KeyRelease>', calculate_total)

    if mode == 'add':
        widgets['invoice_no'].config(text=next_invoice_number('INV', 'sales'))


def _on_clear(widgets):
    widgets['available'].config(text='Available: -')


SALES_SPEC['decorate'] = _decorate
SALES_SPEC['on_clear'] = _on_clear

sale_treeview = None
sale_frame = None


def show_multi_item_dialog(window):
    SX, SY = scale(window)
    dialog = Toplevel(window)
    dialog.title('Multi-Item Sale')
    dialog.configure(bg='white')
    dialog.resizable(False, False)
    dialog.transient(window)
    dialog.grab_set()
    dialog.protocol('WM_DELETE_WINDOW', dialog.destroy)

    Label(dialog, text='Multi-Item Sale (one invoice)', font=(FONT_FAMILY, fs(SY, 16), 'bold'),
          bg=PRIMARY, fg='white').pack(fill=X)

    top = Frame(dialog, bg='white')
    top.pack(pady=py(SY, 8))
    Label(top, text='Invoice:', font=(FONT_FAMILY, fs(SY, 13), 'bold'),
          bg='white').pack(side=LEFT)
    invoice_label = Label(top, text=next_invoice_number('INV', 'sales'),
                          font=(FONT_FAMILY, fs(SY, 13), 'bold'), bg='white', fg=PRIMARY)
    invoice_label.pack(side=LEFT, padx=px(SX, 8))

    builder = Frame(dialog, bg='white')
    builder.pack(pady=py(SY, 4))
    Label(builder, text='Product', font=(FONT_FAMILY, fs(SY, 12), 'bold'),
          bg='white').grid(row=0, column=0)
    Label(builder, text='Qty', font=(FONT_FAMILY, fs(SY, 12), 'bold'),
          bg='white').grid(row=0, column=2)
    Label(builder, text='Unit Price', font=(FONT_FAMILY, fs(SY, 12), 'bold'),
          bg='white').grid(row=0, column=4)

    product_cb = ttk.Combobox(builder, state='readonly', width=24,
                              font=(FONT_FAMILY, fs(SY, 12)),
                              values=[opt[1] for opt in
                                      crud.fetch_options('products', 'product_id', 'name')])
    product_cb.grid(row=1, column=0, padx=px(SX, 6), pady=py(SY, 4))
    qty_entry = Entry(builder, font=(FONT_FAMILY, fs(SY, 12)), bg=FIELD_BG, width=8)
    qty_entry.insert(0, '1')
    qty_entry.grid(row=1, column=2, padx=px(SX, 6), pady=py(SY, 4))
    price_entry = Entry(builder, font=(FONT_FAMILY, fs(SY, 12)), bg=FIELD_BG, width=12)
    price_entry.grid(row=1, column=4, padx=px(SX, 6), pady=py(SY, 4))
    available_label = Label(builder, text='Available: -', font=(FONT_FAMILY, fs(SY, 11)),
                            bg='white', fg='#666666')
    available_label.grid(row=1, column=6, padx=px(SX, 6))

    def on_product_select(event):
        name = product_cb.get()
        if not name:
            return
        details = get_product_details(name)
        if details:
            price, stock = details
            price_entry.delete(0, END)
            price_entry.insert(0, f'{price:,.2f}')
            available_label.config(text=f'Available: {stock}')

    product_cb.bind('<<ComboboxSelected>>', on_product_select)

    cart = []
    columns = ('product', 'quantity', 'unit_price', 'total')
    tree = ttk.Treeview(dialog, columns=columns, show='headings', height=6)
    for col in columns:
        tree.heading(col, text=col.replace('_', ' ').title())
        tree.column(col, width=px(SX, 140), anchor='center')
    tree.pack(padx=px(SX, 20), pady=py(SY, 4), fill=X)

    total_label = Label(dialog, text='Order Total: 0.00',
                        font=(FONT_FAMILY, fs(SY, 14), 'bold'), bg='white', fg=PRIMARY)
    total_label.pack(pady=py(SY, 4))

    def refresh_total():
        total_label.config(
            text=f'Order Total: {sum(float(r["total"]) for r in cart):,.2f}')

    def add_line():
        name = product_cb.get()
        if not name:
            crud.messagebox.showerror('Error', 'Select a product')
            return
        try:
            qty = int(qty_entry.get().strip())
            price = float(price_entry.get().strip().replace(',', ''))
        except ValueError:
            crud.messagebox.showerror('Error', 'Quantity and unit price must be numbers')
            return
        if qty <= 0 or price < 0:
            crud.messagebox.showerror(
                'Error', 'Quantity must be a positive whole number and price cannot be negative')
            return
        product_id = crud.lookup_id('products', 'product_id', 'name', name)
        line_total = round(qty * price, 2)
        cart.append({'product': name, 'product_id': product_id, 'quantity': qty,
                     'unit_price': price, 'total': line_total})
        tree.insert('', END, values=(name, qty, f'{price:,.2f}', f'{line_total:,.2f}'))
        refresh_total()

    def remove_line():
        selection = tree.selection()
        if not selection:
            crud.messagebox.showerror('Error', 'Select a line to remove')
            return
        index = tree.index(selection[0])
        tree.delete(selection[0])
        del cart[index]
        refresh_total()

    meta = Frame(dialog, bg='white')
    meta.pack(pady=py(SY, 6))
    Label(meta, text='Sale Date:', font=(FONT_FAMILY, fs(SY, 12), 'bold'),
          bg='white').grid(row=0, column=0, padx=px(SX, 4))
    sale_date_entry = DateEntry(meta, width=12, font=(FONT_FAMILY, fs(SY, 12)),
                                state='readonly', date_pattern='yyyy-mm-dd', bg='white')
    sale_date_entry.set_date(datetime.now())
    sale_date_entry.grid(row=0, column=1, padx=px(SX, 4))
    Label(meta, text='Customer:', font=(FONT_FAMILY, fs(SY, 12), 'bold'),
          bg='white').grid(row=0, column=2, padx=px(SX, 4))
    customer_cb = ttk.Combobox(meta, width=18, font=(FONT_FAMILY, fs(SY, 12)),
                               values=customers.get_customer_names())
    customer_cb.set('Select Customer')
    customer_cb.grid(row=0, column=3, padx=px(SX, 4))
    Label(meta, text='Payment:', font=(FONT_FAMILY, fs(SY, 12), 'bold'),
          bg='white').grid(row=0, column=4, padx=px(SX, 4))
    payment_cb = ttk.Combobox(meta, width=8, font=(FONT_FAMILY, fs(SY, 12)),
                              state='readonly', values=['Cash', 'Credit'])
    payment_cb.set('Cash')
    payment_cb.grid(row=0, column=5, padx=px(SX, 4))

    def save():
        if not cart:
            crud.messagebox.showerror('Error', 'Add at least one item to the sale')
            return
        customer = customer_cb.get().strip()
        if not customer or customer == 'Select Customer':
            crud.messagebox.showerror('Error', 'Please type or select a customer')
            return
        invoice = add_order(cart, sale_date_entry.get(), customer,
                            payment_cb.get(), invoice_number=invoice_label.cget('text'))
        if invoice:
            dialog.destroy()
            crud.messagebox.showinfo('Success', f'Sale recorded (invoice {invoice})')
            crud.render_rows(sale_treeview, SALES_SPEC, rows())

    controls = Frame(dialog, bg='white')
    controls.pack(pady=py(SY, 10))
    button(controls, 'Add Line', font_size=fs(SY, 12), command=add_line).pack(
        side=LEFT, padx=px(SX, 8))
    button(controls, 'Remove Line', font_size=fs(SY, 12), command=remove_line).pack(
        side=LEFT, padx=px(SX, 8))
    button(controls, 'Save Sale', font_size=fs(SY, 12), command=save).pack(
        side=LEFT, padx=px(SX, 8))
    button(controls, 'Cancel', font_size=fs(SY, 12), command=dialog.destroy).pack(
        side=LEFT, padx=px(SX, 8))
    dialog.bind('<Escape>', lambda e: dialog.destroy())
    return dialog


def sale_form(window, on_close=None):
    global sale_treeview, sale_frame

    def show_receipt():
        sale_id = SALES_SPEC.get('selected')
        if sale_id is None:
            crud.messagebox.showerror('Error', 'Please select a sale to view its receipt')
            return
        reports.show_receipt(window, sale_id)

    sale_frame, sale_treeview = crud.build_form(window, SALES_SPEC, {
        'rows': rows,
        'add': add_record,
        'update': update_record,
        'delete': delete_record,
        'search': search_sale,
        'count': get_count,
        'export_csv': export_sale_csv,
        'extra_buttons': [('Receipt', show_receipt, 'Print a receipt for the selected sale'),
                          ('Multi-Item Sale', lambda: show_multi_item_dialog(window),
                           'Record a sale with multiple products on one invoice')],
    }, on_close=on_close)
    return sale_frame
