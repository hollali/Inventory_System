import crud
import movements
from app_log import logger
from database import (commit, execute, format_money, is_integrity_error, money_from_cents,
                      next_invoice_number, query, query_one, rollback)

PURCHASES_SPEC = {
    'table': 'purchases',
    'pk': 'purchase_id',
    'pk_label': 'Purchase Id',
    'title': 'Purchases',
    'frame_global': 'purchases_frame',
    'table_columns': ['purchase_id', 'invoice_number', 'supplier_id', 'product_id', 'quantity',
                      'unit_cost', 'total', 'purchase_date', 'payment_mode', 'note'],
    'columns': [
        ('purchase_id', 'Purchase Id', 100), ('invoice_number', 'Invoice', 110),
        ('supplier', 'Supplier', 200), ('product', 'Product', 200),
        ('quantity', 'Quantity', 90), ('unit_cost', 'Unit Cost', 110),
        ('total', 'Total', 110), ('purchase_date', 'Purchase Date', 120),
        ('payment_mode', 'Payment', 100),
    ],
    'search': [('Id', 'p.purchase_id'), ('Invoice', 'p.invoice_number'),
               ('Supplier', 's.name'), ('Product', 'pr.name')],
    'unique_msg': 'Purchase ID must be unique',
    'no_selection_msg': 'Please select a purchase to delete',
    'delete_confirm': 'Are you sure you want to delete this purchase? Stock will be deducted.',
    'msg_insert': 'Purchase recorded and stock received',
    'msg_update': 'Purchase updated successfully',
    'msg_delete': 'Purchase deleted and stock deducted',
    'fields': [
        {'key': 'purchase_id', 'label': 'Purchase Id', 'kind': 'entry', 'pos': (0, 0),
         'store': 'int', 'auto': True},
        {'key': 'supplier_id', 'label': 'Supplier', 'kind': 'source', 'pos': (0, 2),
         'source': ('suppliers', 'supplier_id', 'name'), 'placeholder': 'Select Supplier',
         'display_key': 'supplier', 'required': True, 'msg': 'Please select a supplier'},
        {'key': 'invoice_no', 'label': 'Invoice No.', 'kind': 'label', 'pos': (0, 4),
         'label_text': ''},
        {'key': 'product_id', 'label': 'Product', 'kind': 'source', 'pos': (1, 0),
         'source': ('products', 'product_id', 'name'), 'placeholder': 'Select Product',
         'display_key': 'product', 'required': True, 'msg': 'Please select a product'},
        {'key': 'available', 'label': '', 'kind': 'label', 'pos': (1, 2),
         'label_text': 'Available: -'},
        {'key': 'unit_cost', 'label': 'Unit Cost', 'kind': 'entry', 'pos': (1, 4),
         'required': True, 'validate': 'number',
         'msg': 'Unit cost must be a number', 'store': 'float', 'format': 'money'},
        {'key': 'quantity', 'label': 'Quantity', 'kind': 'entry', 'pos': (2, 0),
         'required': True, 'validate': 'positive_int',
         'msg': 'Quantity must be a positive whole number', 'store': 'int', 'format': 'int'},
        {'key': 'total', 'label': 'Total', 'kind': 'entry', 'pos': (2, 2), 'required': True,
         'validate': 'number', 'msg': 'Total must be a number', 'store': 'float',
         'format': 'money', 'readonly': True},
        {'key': 'payment_mode', 'label': 'Payment', 'kind': 'combobox', 'pos': (2, 4),
         'options': ['Cash', 'Credit'], 'default': 'Cash'},
        {'key': 'purchase_date', 'label': 'Purchase Date', 'kind': 'date', 'pos': (3, 0),
         'required': True, 'store': 'date', 'default_today': True},
        {'key': 'note', 'label': 'Note', 'kind': 'text', 'pos': (3, 2), 'colspan': 2},
    ],
}


def rows(where=None, params=()):
    sql = ('SELECT p.purchase_id, p.invoice_number, s.name AS supplier, pr.name AS product, '
           'p.quantity, p.unit_cost, p.total, p.purchase_date, p.payment_mode, p.note '
           'FROM purchases p '
           'LEFT JOIN suppliers s ON s.supplier_id = p.supplier_id '
           'LEFT JOIN products pr ON pr.product_id = p.product_id')
    if where:
        sql += f' WHERE {where}'
    return [dict(row) for row in query(sql, params)]


def add_record(data):
    cleaned = crud.validate_data(PURCHASES_SPEC, data, 'add')
    if cleaned is None:
        return False
    cleaned['total'] = cleaned['quantity'] * cleaned['unit_cost']
    cleaned['invoice_number'] = next_invoice_number('PO', 'purchases')
    if cleaned['unit_cost'] < 0:
        crud.messagebox.showerror('Error', 'Unit cost must be a positive number')
        return False
    try:
        product = query_one('SELECT product_id FROM products WHERE product_id = ?',
                            (cleaned['product_id'],))
        if product is None:
            crud.messagebox.showerror('Error', 'Selected product not found')
            return False
        execute('INSERT INTO purchases (purchase_id, invoice_number, supplier_id, product_id, '
                'quantity, unit_cost, total, purchase_date, payment_mode, note) '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (cleaned.get('purchase_id'), cleaned['invoice_number'], cleaned['supplier_id'],
                 cleaned['product_id'], cleaned['quantity'], cleaned['unit_cost'],
                 cleaned['total'], cleaned['purchase_date'],
                 cleaned.get('payment_mode') or 'Cash', cleaned.get('note')))
        execute('UPDATE products SET quantity = quantity + ? WHERE product_id = ?',
                (cleaned['quantity'], cleaned['product_id']))
        movements.log_movement(cleaned['product_id'], cleaned['quantity'], 'purchase',
                               reference_id=cleaned.get('purchase_id'))
        commit()
        return True
    except Exception as exc:
        rollback()
        logger.exception('add_record failed on purchases')
        if is_integrity_error(exc):
            crud.messagebox.showerror('Error', 'Purchase ID must be unique')
        else:
            crud.messagebox.showerror('Error', f'Database error: {exc}')
        return False


def update_record(data):
    cleaned = crud.validate_data(PURCHASES_SPEC, data, 'update')
    if cleaned is None:
        return False
    cleaned['total'] = cleaned['quantity'] * cleaned['unit_cost']
    if cleaned['unit_cost'] < 0:
        crud.messagebox.showerror('Error', 'Unit cost must be a positive number')
        return False
    try:
        purchase_id = cleaned.get('purchase_id')
        old = query_one('SELECT product_id, quantity FROM purchases WHERE purchase_id = ?',
                        (purchase_id,))
        if old is None:
            crud.messagebox.showerror(
                'Error', f"No record found with that {PURCHASES_SPEC['pk_label']}")
            return False
        if old['product_id'] is not None:
            execute('UPDATE products SET quantity = quantity - ? WHERE product_id = ?',
                    (old['quantity'], old['product_id']))
        execute('UPDATE products SET quantity = quantity + ? WHERE product_id = ?',
                (cleaned['quantity'], cleaned['product_id']))
        execute('UPDATE purchases SET supplier_id = ?, product_id = ?, quantity = ?, '
                'unit_cost = ?, total = ?, purchase_date = ?, payment_mode = ?, note = ? '
                'WHERE purchase_id = ?',
                (cleaned['supplier_id'], cleaned['product_id'], cleaned['quantity'],
                 cleaned['unit_cost'], cleaned['total'], cleaned['purchase_date'],
                 cleaned.get('payment_mode') or 'Cash', cleaned.get('note'), purchase_id))
        if old['product_id'] is not None and old['product_id'] != cleaned['product_id']:
            movements.log_movement(old['product_id'], -old['quantity'], 'purchase_update',
                                   reference_id=purchase_id)
        net = (cleaned['quantity'] - old['quantity'] if
               old['product_id'] == cleaned['product_id'] else cleaned['quantity'])
        movements.log_movement(cleaned['product_id'], net, 'purchase_update',
                               reference_id=purchase_id)
        commit()
        return True
    except Exception as exc:
        rollback()
        logger.exception('update_record failed on purchases')
        crud.messagebox.showerror('Error', f'Database error: {exc}')
        return False


def delete_record(purchase_id):
    try:
        row = query_one('SELECT product_id, quantity FROM purchases WHERE purchase_id = ?',
                        (purchase_id,))
        if row is None:
            crud.messagebox.showerror('Error', 'Purchase record not found')
            return False
        if row['product_id'] is not None:
            execute('UPDATE products SET quantity = quantity - ? WHERE product_id = ?',
                    (row['quantity'], row['product_id']))
            movements.log_movement(row['product_id'], -row['quantity'], 'purchase_delete',
                                   reference_id=purchase_id)
        execute('DELETE FROM purchases WHERE purchase_id = ?', (purchase_id,))
        commit()
        return True
    except Exception as exc:
        rollback()
        logger.exception('delete_record failed on purchases')
        crud.messagebox.showerror('Error', f'Database error: {exc}')
        return False


def create_purchase(product_id, quantity, unit_cost, supplier_id, purchase_date, note='Reorder'):
    return add_record({
        'supplier_id': supplier_id,
        'product_id': product_id,
        'quantity': quantity, 'unit_cost': unit_cost,
        'total': quantity * unit_cost,
        'purchase_date': purchase_date, 'note': note})


def add_purchase(purchase_id, supplier, product, quantity, unit_cost, total, purchase_date,
                 payment_mode=None):
    data = {
        'supplier_id': crud.lookup_id('suppliers', 'supplier_id', 'name', supplier),
        'product_id': crud.lookup_id('products', 'product_id', 'name', product),
        'quantity': quantity, 'unit_cost': unit_cost, 'total': total,
        'purchase_date': purchase_date}
    if purchase_id is not None:
        data['purchase_id'] = purchase_id
    if payment_mode:
        data['payment_mode'] = payment_mode
    return add_record(data)


def update_purchase(purchase_id, supplier, product, quantity, unit_cost, total, purchase_date,
                    old_product, old_quantity, payment_mode=None):
    data = {
        'purchase_id': purchase_id,
        'supplier_id': crud.lookup_id('suppliers', 'supplier_id', 'name', supplier),
        'product_id': crud.lookup_id('products', 'product_id', 'name', product),
        'quantity': quantity, 'unit_cost': unit_cost, 'total': total,
        'purchase_date': purchase_date}
    if payment_mode:
        data['payment_mode'] = payment_mode
    return update_record(data)


def delete_purchase(purchase_id):
    return delete_record(purchase_id)


def search_purchase(option, search_value):
    if option == 'Search By':
        crud.messagebox.showerror('Error', 'Please select a search option')
        return
    if search_value == '':
        crud.messagebox.showerror('Error', 'Search field is required')
        return
    column = dict(PURCHASES_SPEC['search']).get(option)
    if not column:
        crud.messagebox.showerror('Error', 'Please select a valid search option')
        return
    result = rows(where=f'{column} LIKE ?', params=(f'%{search_value}%',))
    crud.render_rows(PURCHASES_SPEC['treeview'], PURCHASES_SPEC, result)
    if not result:
        crud.messagebox.showinfo('No Records', 'No matching records found')


def get_count():
    return crud.count_rows(PURCHASES_SPEC)


def get_total_spent():
    return sum(row['total'] or 0 for row in query('SELECT total FROM purchases'))


def export_purchase_csv():
    records = [tuple(row[key] if key not in ('unit_cost', 'total')
                     else money_from_cents(row[key])
                     for key in ('purchase_id', 'invoice_number', 'supplier', 'product',
                                 'quantity', 'unit_cost', 'total', 'purchase_date',
                                 'payment_mode')) for row in rows()]
    from layout import export_to_csv
    export_to_csv(None, ('Purchase Id', 'Invoice', 'Supplier', 'Product', 'Quantity',
                         'Unit Cost', 'Total', 'Purchase Date', 'Payment'), records,
                  'purchases.csv')


def _decorate(detail_frame, widgets, mode):
    def calculate_total(*args):
        try:
            quantity = int(widgets['quantity'].get().strip())
            cost = float(widgets['unit_cost'].get().strip().replace(',', ''))
            crud.set_widget(widgets['total'], f'{quantity * cost:,.2f}')
        except (ValueError, TypeError):
            crud.set_widget(widgets['total'], '')

    def on_product_select(event):
        name = widgets['product_id'].get()
        if name == 'Select Product':
            return
        row = query_one('SELECT quantity, cost_price, price FROM products WHERE name = ?',
                        (name,))
        if row:
            crud.set_widget(widgets['unit_cost'], format_money(row['cost_price'] or 0))
            widgets['available'].config(
                text=f'Available: {row["quantity"]} (price {format_money(row["price"] or 0)})')
            calculate_total()

    widgets['product_id'].bind('<<ComboboxSelected>>', on_product_select)
    widgets['quantity'].bind('<KeyRelease>', calculate_total)
    widgets['unit_cost'].bind('<KeyRelease>', calculate_total)

    if mode == 'add':
        widgets['invoice_no'].config(text=next_invoice_number('PO', 'purchases'))


PURCHASES_SPEC['decorate'] = _decorate

purchase_treeview = None
purchase_frame = None


def purchase_form(window, on_close=None):
    global purchase_treeview, purchase_frame

    def show_reorder_picker():
        import reports
        reports.show_reorder_picker(window)

    purchase_frame, purchase_treeview = crud.build_form(window, PURCHASES_SPEC, {
        'rows': rows,
        'add': add_record,
        'update': update_record,
        'delete': delete_record,
        'search': search_purchase,
        'count': get_count,
        'export_csv': export_purchase_csv,
        'extra_buttons': [('Reorder Picker', show_reorder_picker,
                           'Suggest products to restock and receive them')],
    }, on_close=on_close)
    return purchase_frame
