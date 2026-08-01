import crud
import movements
from database import money_from_cents
from layout import export_to_csv

PRODUCT_SPEC = {
    'table': 'products',
    'pk': 'product_id',
    'pk_label': 'Product Id',
    'title': 'Product Details',
    'frame_global': 'product_frame',
    'table_columns': ['product_id', 'name', 'category_id', 'supplier_id', 'price',
                      'cost_price', 'quantity', 'reorder_level', 'description'],
    'columns': [
        ('product_id', 'Product Id', 100), ('name', 'Name', 220),
        ('category_name', 'Category', 150), ('supplier_name', 'Supplier', 150),
        ('price', 'Price', 110), ('cost_price', 'Cost', 110), ('quantity', 'Quantity', 90),
        ('reorder_level', 'Reorder', 90), ('description', 'Description', 350),
    ],
    'join': ('LEFT JOIN categories ON products.category_id = categories.category_id '
             'LEFT JOIN suppliers ON products.supplier_id = suppliers.supplier_id'),
    'select_columns': ['products.product_id', 'products.name',
                       'categories.name AS category_name', 'suppliers.name AS supplier_name',
                       'products.price', 'products.cost_price',
                       'products.quantity', 'products.reorder_level', 'products.description'],
    'search': [('Id', 'products.product_id'), ('Name', 'products.name'),
               ('Category', 'categories.name')],
    'unique_msg': 'Product ID must be unique',
    'no_selection_msg': 'Please select a product to delete',
    'delete_confirm': 'Are you sure you want to delete this product?',
    'msg_insert': 'Data inserted successfully',
    'msg_update': 'Data updated successfully',
    'msg_delete': 'Data deleted successfully',
    'fields': [
        {'key': 'product_id', 'label': 'Product Id', 'kind': 'entry', 'pos': (0, 0),
         'store': 'int', 'auto': True},
        {'key': 'name', 'label': 'Name', 'kind': 'entry', 'pos': (0, 2), 'required': True},
        {'key': 'category_id', 'label': 'Category', 'kind': 'source', 'pos': (0, 4),
         'source': ('categories', 'category_id', 'name'), 'placeholder': 'Select Category',
         'display_key': 'category_name', 'required': True, 'msg': 'Please select a category'},
        {'key': 'supplier_id', 'label': 'Supplier', 'kind': 'source', 'pos': (1, 0),
         'source': ('suppliers', 'supplier_id', 'name'), 'placeholder': 'Select Supplier',
         'display_key': 'supplier_name', 'required': True, 'msg': 'Please select a supplier'},
        {'key': 'price', 'label': 'Selling Price', 'kind': 'entry', 'pos': (1, 2), 'required': True,
         'validate': 'number', 'positive': True, 'msg': 'Price must be a positive number',
         'store': 'float', 'format': 'money'},
        {'key': 'cost_price', 'label': 'Cost Price', 'kind': 'entry', 'pos': (1, 4),
         'required': False, 'validate': 'number', 'positive': True, 'msg': 'Cost must be a number',
         'store': 'float', 'format': 'money'},
        {'key': 'quantity', 'label': 'Quantity', 'kind': 'entry', 'pos': (2, 0), 'required': True,
         'validate': 'positive_int', 'msg': 'Quantity must be a whole number',
         'store': 'int', 'format': 'int'},
        {'key': 'reorder_level', 'label': 'Reorder Level', 'kind': 'entry', 'pos': (2, 2),
         'required': False, 'validate': 'positive_int', 'msg': 'Reorder level must be a whole number',
         'store': 'int', 'format': 'int'},
        {'key': 'description', 'label': 'Description', 'kind': 'text', 'pos': (2, 4),
         'width': 60, 'height': 3, 'colspan': 2, 'required': True},
    ],
}


def add_record(data):
    cleaned = crud.validate_data(PRODUCT_SPEC, data, 'add')
    if cleaned is None:
        return False
    if not crud.insert_row(PRODUCT_SPEC, cleaned):
        return False
    if cleaned.get('quantity'):
        movements.log_movement_committed(cleaned['product_id'], cleaned['quantity'], 'initial')
    return True


def update_record(data):
    cleaned = crud.validate_data(PRODUCT_SPEC, data, 'update')
    if cleaned is None:
        return False
    old = crud.query_one('SELECT quantity AS n FROM products WHERE product_id = ?',
                         (cleaned['product_id'],))
    if old is None:
        crud.messagebox.showerror('Error', f"No record found with that {PRODUCT_SPEC['pk_label']}")
        return False
    if not crud.update_row(PRODUCT_SPEC, cleaned):
        return False
    delta = (cleaned.get('quantity') or 0) - (old['n'] or 0)
    if delta:
        movements.log_movement_committed(cleaned['product_id'], delta, 'adjustment')
    return True


def delete_record(product_id):
    return crud.delete_row(PRODUCT_SPEC, product_id)


def add_product(product_id, name, category, supplier, price, quantity, description):
    return add_record({
        'product_id': product_id, 'name': name,
        'category_id': crud.lookup_id('categories', 'category_id', 'name', category),
        'supplier_id': crud.lookup_id('suppliers', 'supplier_id', 'name', supplier),
        'price': price, 'quantity': quantity, 'description': description})


def update_product(product_id, name, category, supplier, price, quantity, description):
    return update_record({
        'product_id': product_id, 'name': name,
        'category_id': crud.lookup_id('categories', 'category_id', 'name', category),
        'supplier_id': crud.lookup_id('suppliers', 'supplier_id', 'name', supplier),
        'price': price, 'quantity': quantity, 'description': description})


def delete_product(product_id):
    return delete_record(product_id)


def search_product(option, search_value):
    return crud.search_and_render(PRODUCT_SPEC, option, search_value)


def get_product_names():
    return [row['name'] for row in crud.query('SELECT name FROM products ORDER BY name')]


def get_product_details(name):
    row = crud.query_one('SELECT price, quantity FROM products WHERE name = ?', (name,))
    return (row['price'], row['quantity']) if row else None


def get_count():
    return crud.count_rows(PRODUCT_SPEC)


def export_product_csv():
    rows = crud.fetch_rows(PRODUCT_SPEC)
    records = [tuple(money_from_cents(row[key]) if key in ('price', 'cost_price')
                     else row[key]
                     for key in ('product_id', 'name', 'category_name',
                                 'supplier_name', 'price', 'cost_price',
                                 'quantity', 'reorder_level', 'description'))
               for row in rows]
    export_to_csv(None, ('Product Id', 'Name', 'Category', 'Supplier', 'Price',
                         'Cost Price', 'Quantity', 'Reorder Level', 'Description'),
                  records, 'products.csv')


product_treeview = None
product_frame = None


def product_form(window, on_close=None):
    global product_treeview, product_frame
    product_frame, product_treeview = crud.build_form(window, PRODUCT_SPEC, {
        'rows': lambda where=None, params=(): crud.fetch_rows(PRODUCT_SPEC, where, params),
        'add': add_record,
        'update': update_record,
        'delete': delete_record,
        'search': search_product,
        'count': get_count,
        'export_csv': export_product_csv,
    }, on_close=on_close)
    return product_frame
