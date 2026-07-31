import crud
from layout import export_to_csv

PRODUCT_SPEC = {
    'table': 'products',
    'pk': 'product_id',
    'pk_label': 'Product Id',
    'title': 'Product Details',
    'frame_global': 'product_frame',
    'table_columns': ['product_id', 'name', 'category_id', 'supplier_id', 'price',
                      'quantity', 'description'],
    'columns': [
        ('product_id', 'Product Id', 100), ('name', 'Name', 250),
        ('category_name', 'Category', 180), ('supplier_name', 'Supplier', 180),
        ('price', 'Price', 120), ('quantity', 'Quantity', 100), ('description', 'Description', 400),
    ],
    'join': ('LEFT JOIN categories ON products.category_id = categories.category_id '
             'LEFT JOIN suppliers ON products.supplier_id = suppliers.supplier_id'),
    'select_columns': ['products.product_id', 'products.name',
                       'categories.name AS category_name', 'suppliers.name AS supplier_name',
                       'products.price', 'products.quantity', 'products.description'],
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
         'required': True, 'validate': 'positive_int', 'msg': 'Product ID must be a whole number',
         'store': 'int'},
        {'key': 'name', 'label': 'Name', 'kind': 'entry', 'pos': (0, 2), 'required': True},
        {'key': 'category_id', 'label': 'Category', 'kind': 'source', 'pos': (0, 4),
         'source': ('categories', 'category_id', 'name'), 'placeholder': 'Select Category',
         'display_key': 'category_name', 'required': True, 'msg': 'Please select a category'},
        {'key': 'supplier_id', 'label': 'Supplier', 'kind': 'source', 'pos': (1, 0),
         'source': ('suppliers', 'supplier_id', 'name'), 'placeholder': 'Select Supplier',
         'display_key': 'supplier_name', 'required': True, 'msg': 'Please select a supplier'},
        {'key': 'price', 'label': 'Price', 'kind': 'entry', 'pos': (1, 2), 'required': True,
         'validate': 'number', 'positive': True, 'msg': 'Price must be a positive number',
         'store': 'float', 'format': 'money'},
        {'key': 'quantity', 'label': 'Quantity', 'kind': 'entry', 'pos': (1, 4), 'required': True,
         'validate': 'positive_int', 'msg': 'Quantity must be a whole number',
         'store': 'int', 'format': 'int'},
        {'key': 'description', 'label': 'Description', 'kind': 'text', 'pos': (2, 0),
         'width': 60, 'height': 3, 'colspan': 3, 'required': True},
    ],
}


def add_record(data):
    cleaned = crud.validate_data(PRODUCT_SPEC, data, 'add')
    if cleaned is None:
        return False
    return crud.insert_row(PRODUCT_SPEC, cleaned)


def update_record(data):
    cleaned = crud.validate_data(PRODUCT_SPEC, data, 'update')
    if cleaned is None:
        return False
    return crud.update_row(PRODUCT_SPEC, cleaned)


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
    records = [tuple(row[key] for key in ('product_id', 'name', 'category_name',
                                          'supplier_name', 'price', 'quantity', 'description'))
               for row in rows]
    export_to_csv(None, ('Product Id', 'Name', 'Category', 'Supplier', 'Price',
                         'Quantity', 'Description'), records, 'products.csv')


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
