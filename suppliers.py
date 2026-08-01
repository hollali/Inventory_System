import crud

SUPPLIER_SPEC = {
    'table': 'suppliers',
    'pk': 'supplier_id',
    'pk_label': 'Supplier Id',
    'title': 'Supplier Details',
    'frame_global': 'supplier_frame',
    'table_columns': ['supplier_id', 'name', 'contact_person', 'email', 'phone', 'address'],
    'columns': [
        ('supplier_id', 'Supplier Id', 100), ('name', 'Name', 250),
        ('contact_person', 'Contact Person', 220), ('email', 'Email', 280),
        ('phone', 'Phone', 180), ('address', 'Address', 300),
    ],
    'search': [('Id', 'supplier_id'), ('Name', 'name'), ('Phone', 'phone')],
    'unique_msg': 'Supplier ID must be unique',
    'no_selection_msg': 'Please select a supplier to delete',
    'delete_confirm': 'Are you sure you want to delete this supplier?',
    'delete_guard': ('products', 'supplier_id'),
    'delete_guard_msg': 'Cannot delete: products are linked to this supplier. Remove or reassign them first.',
    'msg_insert': 'Data inserted successfully',
    'msg_update': 'Data updated successfully',
    'msg_delete': 'Data deleted successfully',
    'csv': ('suppliers.csv',
            ('Supplier Id', 'Name', 'Contact Person', 'Email', 'Phone', 'Address'),
            ('supplier_id', 'name', 'contact_person', 'email', 'phone', 'address')),
    'fields': [
        {'key': 'supplier_id', 'label': 'Supplier Id', 'kind': 'entry', 'pos': (0, 0),
         'store': 'int', 'auto': True},
        {'key': 'name', 'label': 'Name', 'kind': 'entry', 'pos': (0, 2), 'required': True},
        {'key': 'contact_person', 'label': 'Contact Person', 'kind': 'entry', 'pos': (0, 4),
         'required': True},
        {'key': 'email', 'label': 'Email', 'kind': 'entry', 'pos': (1, 0), 'required': True,
         'validate': 'email', 'msg': 'Please enter a valid email address'},
        {'key': 'phone', 'label': 'Phone', 'kind': 'entry', 'pos': (1, 2), 'required': True,
         'validate': 'phone', 'msg': 'Please enter a valid phone number'},
        {'key': 'address', 'label': 'Address', 'kind': 'text', 'pos': (1, 4), 'rowspan': 2,
         'width': 20, 'height': 2, 'required': True},
    ],
}


def add_record(data):
    cleaned = crud.validate_data(SUPPLIER_SPEC, data, 'add')
    if cleaned is None:
        return False
    return crud.insert_row(SUPPLIER_SPEC, cleaned)


def update_record(data):
    cleaned = crud.validate_data(SUPPLIER_SPEC, data, 'update')
    if cleaned is None:
        return False
    return crud.update_row(SUPPLIER_SPEC, cleaned)


def delete_record(supplier_id):
    return crud.delete_row(SUPPLIER_SPEC, supplier_id)


def add_supplier(supplier_id, name, contact_person, email, phone, address):
    return add_record({'supplier_id': supplier_id, 'name': name,
                       'contact_person': contact_person, 'email': email,
                       'phone': phone, 'address': address})


def update_supplier(supplier_id, name, contact_person, email, phone, address):
    return update_record({'supplier_id': supplier_id, 'name': name,
                          'contact_person': contact_person, 'email': email,
                          'phone': phone, 'address': address})


def delete_supplier(supplier_id):
    return delete_record(supplier_id)


def search_supplier(option, search_value):
    return crud.search_and_render(SUPPLIER_SPEC, option, search_value)


def get_supplier_names():
    return [row['name'] for row in crud.query(
        'SELECT name FROM suppliers ORDER BY name')]


def get_count():
    return crud.count_rows(SUPPLIER_SPEC)


def export_supplier_csv():
    return crud.export_csv(SUPPLIER_SPEC)


supplier_treeview = None
supplier_frame = None


def supplier_form(window, on_close=None):
    global supplier_treeview, supplier_frame
    supplier_frame, supplier_treeview = crud.build_form(window, SUPPLIER_SPEC, {
        'rows': lambda where=None, params=(): crud.fetch_rows(SUPPLIER_SPEC, where, params),
        'add': add_record,
        'update': update_record,
        'delete': delete_record,
        'search': search_supplier,
        'count': get_count,
        'export_csv': export_supplier_csv,
    }, on_close=on_close)
    return supplier_frame
