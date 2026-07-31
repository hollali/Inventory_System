import crud
from database import commit, execute, is_integrity_error, query, query_one, rollback
from products import get_product_details
import reports

SALES_SPEC = {
    'table': 'sales',
    'pk': 'sale_id',
    'pk_label': 'Sale Id',
    'title': 'Sales Details',
    'frame_global': 'sale_frame',
    'table_columns': ['sale_id', 'product_id', 'quantity', 'unit_price', 'total',
                      'sale_date', 'customer'],
    'columns': [
        ('sale_id', 'Sale Id', 90), ('product', 'Product', 220), ('quantity', 'Quantity', 90),
        ('unit_price', 'Unit Price', 120), ('total', 'Total', 120),
        ('sale_date', 'Sale Date', 130), ('customer', 'Customer', 220),
    ],
    'search': [('Id', 's.sale_id'), ('Product', 'p.name'), ('Customer', 's.customer')],
    'unique_msg': 'Sale ID must be unique',
    'no_selection_msg': 'Please select a sale to delete',
    'delete_confirm': 'Are you sure you want to delete this sale? Stock will be restored.',
    'msg_insert': 'Sale recorded successfully',
    'msg_update': 'Sale updated successfully',
    'msg_delete': 'Sale deleted and stock restored',
    'fields': [
        {'key': 'sale_id', 'label': 'Sale Id', 'kind': 'entry', 'pos': (0, 0), 'required': True,
         'validate': 'positive_int', 'msg': 'Sale ID must be a whole number', 'store': 'int'},
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
        {'key': 'customer', 'label': 'Customer', 'kind': 'entry', 'pos': (2, 2), 'required': True},
    ],
}


def rows(where=None, params=()):
    sql = ('SELECT s.sale_id, p.name AS product, s.quantity, s.unit_price, s.total, '
           's.sale_date, s.customer '
           'FROM sales s LEFT JOIN products p ON p.product_id = s.product_id')
    if where:
        sql += f' WHERE {where}'
    return [dict(row) for row in query(sql, params)]


def add_record(data):
    cleaned = crud.validate_data(SALES_SPEC, data, 'add')
    if cleaned is None:
        return False
    cleaned['total'] = round(cleaned['quantity'] * cleaned['unit_price'], 2)
    try:
        stock_row = query_one('SELECT quantity AS n FROM products WHERE product_id = ?',
                              (cleaned['product_id'],))
        stock = stock_row['n'] if stock_row and stock_row['n'] is not None else 0
        if cleaned['quantity'] > stock:
            crud.messagebox.showerror('Error', f'Insufficient stock available (in stock: {stock})')
            return False
        execute('INSERT INTO sales (sale_id, product_id, quantity, unit_price, total, '
                'sale_date, customer) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (cleaned['sale_id'], cleaned['product_id'], cleaned['quantity'],
                 cleaned['unit_price'], cleaned['total'], cleaned['sale_date'],
                 cleaned['customer']))
        execute('UPDATE products SET quantity = quantity - ? WHERE product_id = ?',
                (cleaned['quantity'], cleaned['product_id']))
        commit()
        return True
    except Exception as exc:
        rollback()
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
    try:
        old = query_one('SELECT product_id, quantity FROM sales WHERE sale_id = ?',
                        (cleaned['sale_id'],))
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
        execute('UPDATE products SET quantity = quantity - ? WHERE product_id = ?',
                (cleaned['quantity'], cleaned['product_id']))
        execute('UPDATE sales SET product_id = ?, quantity = ?, unit_price = ?, total = ?, '
                'sale_date = ?, customer = ? WHERE sale_id = ?',
                (cleaned['product_id'], cleaned['quantity'], cleaned['unit_price'],
                 cleaned['total'], cleaned['sale_date'], cleaned['customer'],
                 cleaned['sale_id']))
        commit()
        return True
    except Exception as exc:
        rollback()
        if is_integrity_error(exc):
            crud.messagebox.showerror('Error', 'Sale ID must be unique')
        else:
            crud.messagebox.showerror('Error', f'Database error: {exc}')
        return False


def delete_record(sale_id):
    try:
        row = query_one('SELECT product_id, quantity FROM sales WHERE sale_id = ?', (sale_id,))
        if row and row['product_id'] is not None:
            execute('UPDATE products SET quantity = quantity + ? WHERE product_id = ?',
                    (row['quantity'], row['product_id']))
        execute('DELETE FROM sales WHERE sale_id = ?', (sale_id,))
        commit()
        return True
    except Exception as exc:
        rollback()
        crud.messagebox.showerror('Error', f'Database error: {exc}')
        return False


def add_sale(sale_id, product, quantity, unit_price, total, sale_date, customer):
    return add_record({
        'sale_id': sale_id,
        'product_id': crud.lookup_id('products', 'product_id', 'name', product),
        'quantity': quantity, 'unit_price': unit_price, 'total': total,
        'sale_date': sale_date, 'customer': customer})


def update_sale(sale_id, product, quantity, unit_price, total, sale_date, customer,
                old_product, old_quantity):
    return update_record({
        'sale_id': sale_id,
        'product_id': crud.lookup_id('products', 'product_id', 'name', product),
        'quantity': quantity, 'unit_price': unit_price, 'total': total,
        'sale_date': sale_date, 'customer': customer})


def delete_sale(sale_id, product, quantity):
    return delete_record(sale_id)


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


def get_total_revenue():
    return sum(row['total'] or 0 for row in query('SELECT total FROM sales'))


def export_sale_csv():
    records = [tuple(row[key] for key in ('sale_id', 'product', 'quantity', 'unit_price',
                                          'total', 'sale_date', 'customer')) for row in rows()]
    from layout import export_to_csv
    export_to_csv(None, ('Sale Id', 'Product', 'Quantity', 'Unit Price', 'Total',
                         'Sale Date', 'Customer'), records, 'sales.csv')


def _decorate(detail_frame, widgets):
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


def _on_clear(widgets):
    widgets['available'].config(text='Available: -')


SALES_SPEC['decorate'] = _decorate
SALES_SPEC['on_clear'] = _on_clear

sale_treeview = None
sale_frame = None


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
        'extra_buttons': [('Receipt', show_receipt, 'Print a receipt for the selected sale')],
    }, on_close=on_close)
    return sale_frame
