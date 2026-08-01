import crud
from database import query
import sales

RETURNS_SPEC = {
    'table': 'returns',
    'pk': 'return_id',
    'pk_label': 'Return Id',
    'title': 'Stock Returns',
    'frame_global': 'returns_frame',
    'table_columns': ['return_id', 'sale_id', 'product_id', 'quantity', 'unit_price',
                      'total', 'return_date', 'customer', 'invoice_number'],
    'columns': [
        ('return_id', 'Return Id', 90), ('invoice_number', 'Invoice', 110),
        ('sale_id', 'Sale', 80), ('product', 'Product', 200), ('quantity', 'Quantity', 90),
        ('unit_price', 'Unit Price', 110), ('total', 'Total', 110),
        ('return_date', 'Return Date', 120), ('customer', 'Customer', 170),
    ],
    'search': [('Id', 'r.return_id'), ('Invoice', 'r.invoice_number'),
               ('Sale', 'r.sale_id'), ('Product', 'p.name')],
    'unique_msg': 'Return ID must be unique',
    'no_selection_msg': 'Please select a return to delete',
    'delete_confirm': 'Are you sure you want to delete this return? Stock will be deducted.',
    'msg_insert': 'Return recorded and stock restored',
    'msg_update': 'Return updated successfully',
    'msg_delete': 'Return deleted and stock deducted',
    'fields': [
        {'key': 'return_id', 'label': 'Return Id', 'kind': 'entry', 'pos': (0, 0),
         'store': 'int', 'readonly': True},
        {'key': 'sale_id', 'label': 'Sale', 'kind': 'source', 'pos': (0, 2),
         'source': ('sales', 'sale_id', 'invoice_number'), 'placeholder': 'Select Sale',
         'display_key': 'sale_id', 'required': True, 'msg': 'Please select a sale'},
        {'key': 'available', 'label': '', 'kind': 'label', 'pos': (0, 4),
         'label_text': 'Returnable: -'},
        {'key': 'quantity', 'label': 'Quantity', 'kind': 'entry', 'pos': (1, 0),
         'required': True, 'validate': 'positive_int',
         'msg': 'Quantity must be a positive whole number', 'store': 'int', 'format': 'int'},
        {'key': 'return_date', 'label': 'Return Date', 'kind': 'date', 'pos': (1, 2),
         'required': True, 'store': 'date', 'default_today': True},
        {'key': 'customer', 'label': 'Customer', 'kind': 'label', 'pos': (1, 4),
         'label_text': ''},
    ],
}


def rows(where=None, params=()):
    sql = ('SELECT r.return_id, r.invoice_number, r.sale_id, p.name AS product, r.quantity, '
           'r.unit_price, r.total, r.return_date, r.customer '
           'FROM returns r LEFT JOIN products p ON p.product_id = r.product_id')
    if where:
        sql += f' WHERE {where}'
    return [dict(row) for row in query(sql, params)]


def add_record(data):
    return sales.record_return(data)


def update_record(data):
    return sales.update_return(data)


def delete_record(return_id):
    return sales.delete_return(return_id)


def search_return(option, search_value):
    if option == 'Search By':
        crud.messagebox.showerror('Error', 'Please select a search option')
        return
    if search_value == '':
        crud.messagebox.showerror('Error', 'Search field is required')
        return
    column = dict(RETURNS_SPEC['search']).get(option)
    if not column:
        crud.messagebox.showerror('Error', 'Please select a valid search option')
        return
    result = rows(where=f'{column} LIKE ?', params=(f'%{search_value}%',))
    crud.render_rows(RETURNS_SPEC['treeview'], RETURNS_SPEC, result)
    if not result:
        crud.messagebox.showinfo('No Records', 'No matching records found')


def get_count():
    return crud.count_rows(RETURNS_SPEC)


def get_total_refunded():
    return sum(row['total'] or 0 for row in query('SELECT total FROM returns'))


def export_return_csv():
    records = [tuple(row[key] for key in ('return_id', 'invoice_number', 'sale_id', 'product',
                                          'quantity', 'unit_price', 'total', 'return_date',
                                          'customer')) for row in rows()]
    from layout import export_to_csv
    export_to_csv(None, ('Return Id', 'Invoice', 'Sale Id', 'Product', 'Quantity',
                         'Unit Price', 'Total', 'Return Date', 'Customer'), records,
                  'returns.csv')


def _decorate(detail_frame, widgets, mode):
    field = next((f for f in RETURNS_SPEC['fields'] if f['key'] == 'sale_id'), None)
    options = []
    mapping = {}
    for r in query('SELECT s.sale_id, s.invoice_number, COALESCE(p.name, "-") AS product, '
                   's.quantity FROM sales s LEFT JOIN products p ON p.product_id = s.product_id '
                   'ORDER BY s.sale_id DESC'):
        label = f"{r['invoice_number']} — {r['product']} (qty {r['quantity']})"
        options.append(label)
        mapping[label] = r['sale_id']
    if field:
        field['_mapping'] = mapping
    widgets['sale_id'].config(values=options)

    def on_sale_select(event):
        name = widgets['sale_id'].get()
        if not name:
            return
        sale_id = mapping.get(name)
        if sale_id is None:
            return
        remaining = sales.returnable_quantity(sale_id)
        widgets['available'].config(text=f'Returnable: {remaining}')
        sale = query('SELECT customer FROM sales WHERE sale_id = ?', (sale_id,))
        widgets['customer'].config(text=(sale[0]['customer'] if sale else ''))

    widgets['sale_id'].bind('<<ComboboxSelected>>', on_sale_select)


RETURNS_SPEC['decorate'] = _decorate

return_treeview = None
return_frame = None


def return_form(window, on_close=None):
    global return_treeview, return_frame
    return_frame, return_treeview = crud.build_form(window, RETURNS_SPEC, {
        'rows': rows,
        'add': add_record,
        'update': update_record,
        'delete': delete_record,
        'search': search_return,
        'count': get_count,
        'export_csv': export_return_csv,
    }, on_close=on_close)
    return return_frame
