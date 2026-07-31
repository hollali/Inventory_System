import crud

CATEGORY_SPEC = {
    'table': 'categories',
    'pk': 'category_id',
    'pk_label': 'Category Id',
    'title': 'Category Details',
    'frame_global': 'category_frame',
    'table_columns': ['category_id', 'name', 'description'],
    'columns': [
        ('category_id', 'Category Id', 120), ('name', 'Name', 350),
        ('description', 'Description', 700),
    ],
    'search': [('Id', 'category_id'), ('Name', 'name')],
    'unique_msg': 'Category ID must be unique',
    'no_selection_msg': 'Please select a category to delete',
    'delete_confirm': 'Are you sure you want to delete this category?',
    'delete_guard': ('products', 'category_id'),
    'delete_guard_msg': 'Cannot delete: products are linked to this category. Remove or reassign them first.',
    'msg_insert': 'Data inserted successfully',
    'msg_update': 'Data updated successfully',
    'msg_delete': 'Data deleted successfully',
    'csv': ('categories.csv',
            ('Category Id', 'Name', 'Description'),
            ('category_id', 'name', 'description')),
    'fields': [
        {'key': 'category_id', 'label': 'Category Id', 'kind': 'entry', 'pos': (0, 0),
         'required': True, 'validate': 'positive_int',
         'msg': 'Category ID must be a whole number', 'store': 'int'},
        {'key': 'name', 'label': 'Name', 'kind': 'entry', 'pos': (0, 2), 'required': True},
        {'key': 'description', 'label': 'Description', 'kind': 'text', 'pos': (1, 0),
         'width': 60, 'height': 3, 'colspan': 3, 'required': True},
    ],
}


def add_record(data):
    cleaned = crud.validate_data(CATEGORY_SPEC, data, 'add')
    if cleaned is None:
        return False
    return crud.insert_row(CATEGORY_SPEC, cleaned)


def update_record(data):
    cleaned = crud.validate_data(CATEGORY_SPEC, data, 'update')
    if cleaned is None:
        return False
    return crud.update_row(CATEGORY_SPEC, cleaned)


def delete_record(category_id):
    return crud.delete_row(CATEGORY_SPEC, category_id)


def add_category(category_id, name, description):
    return add_record({'category_id': category_id, 'name': name, 'description': description})


def update_category(category_id, name, description):
    return update_record({'category_id': category_id, 'name': name, 'description': description})


def delete_category(category_id):
    return delete_record(category_id)


def search_category(option, search_value):
    return crud.search_and_render(CATEGORY_SPEC, option, search_value)


def get_category_names():
    return [row['name'] for row in crud.query(
        'SELECT name FROM categories ORDER BY name')]


def get_count():
    return crud.count_rows(CATEGORY_SPEC)


def export_category_csv():
    return crud.export_csv(CATEGORY_SPEC)


category_treeview = None
category_frame = None


def category_form(window, on_close=None):
    global category_treeview, category_frame
    category_frame, category_treeview = crud.build_form(window, CATEGORY_SPEC, {
        'rows': lambda where=None, params=(): crud.fetch_rows(CATEGORY_SPEC, where, params),
        'add': add_record,
        'update': update_record,
        'delete': delete_record,
        'search': search_category,
        'count': get_count,
        'export_csv': export_category_csv,
    }, on_close=on_close)
    return category_frame
