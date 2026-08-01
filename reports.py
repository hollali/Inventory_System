from datetime import date, datetime
from tkinter import *
from tkinter import ttk
from tkcalendar import DateEntry

import crud
from app_log import logger
from database import query, query_one
from layout import (FONT_FAMILY, PRIMARY, FIELD_BG, button, export_to_csv,
                    fs, ph, px, pw, py, scale)
import customers
import purchases

LOW_STOCK_THRESHOLD = 5


def low_stock_rows(threshold=LOW_STOCK_THRESHOLD):
    return [dict(row) for row in query(
        'SELECT p.product_id, p.name AS product, c.name AS category, '
        's.name AS supplier, p.quantity, p.reorder_level '
        'FROM products p '
        'LEFT JOIN categories c ON c.category_id = p.category_id '
        'LEFT JOIN suppliers s ON s.supplier_id = p.supplier_id '
        'WHERE p.quantity <= COALESCE(NULLIF(p.reorder_level, 0), ?) '
        'ORDER BY p.quantity, p.name',
        (threshold,))]


def low_stock_count(threshold=LOW_STOCK_THRESHOLD):
    row = query_one(
        'SELECT COUNT(*) AS n FROM products '
        'WHERE quantity <= COALESCE(NULLIF(reorder_level, 0), ?)',
        (threshold,))
    return row['n'] if row else 0


def sales_report_rows(start, end):
    return [dict(row) for row in query(
        'SELECT s.sale_id, s.invoice_number, p.name AS product, s.quantity, s.unit_price, '
        's.total, s.sale_date, s.customer, s.payment_mode '
        'FROM sales s LEFT JOIN products p ON p.product_id = s.product_id '
        'WHERE s.sale_date >= ? AND s.sale_date <= ? '
        'ORDER BY s.sale_date, s.sale_id',
        (start, end))]


def receipt_lines(invoice_number):
    return [dict(row) for row in query(
        'SELECT s.sale_id, s.invoice_number, p.name AS product, s.quantity, s.unit_price, '
        's.total, s.sale_date, s.customer, s.payment_mode '
        'FROM sales s LEFT JOIN products p ON p.product_id = s.product_id '
        'WHERE s.invoice_number = ? ORDER BY s.sale_id', (invoice_number,))]


def receipt_text(sale_id):
    row = query_one('SELECT sale_id, invoice_number, sale_date, customer, payment_mode '
                    'FROM sales WHERE sale_id = ?', (sale_id,))
    if not row:
        return None
    invoice = row['invoice_number']
    if invoice:
        lines = receipt_lines(invoice)
    else:
        lines = [dict(r) for r in query(
            'SELECT s.sale_id, s.invoice_number, p.name AS product, s.quantity, '
            's.unit_price, s.total, s.sale_date, s.customer, s.payment_mode '
            'FROM sales s LEFT JOIN products p ON p.product_id = s.product_id '
            'WHERE s.sale_id = ?', (sale_id,))]
    total = sum(line['total'] or 0 for line in lines)
    body = [
        'INVENTORY MANAGEMENT SYSTEM',
        '==============================',
        f'Invoice:      {row["invoice_number"] or "-"}',
        f'Date:         {row["sale_date"]}',
        f'Customer:     {row["customer"]}',
        f'Payment:      {row["payment_mode"]}',
        '------------------------------',
    ]
    for line in lines:
        body.append(f'{line["product"] or "-":<20} {line["quantity"]} x '
                    f'{line["unit_price"]:,.2f} = {line["total"]:,.2f}')
    body += [
        '------------------------------',
        f'Total:        {total:,.2f}',
        '==============================',
        'Thank you for your business!',
    ]
    return '\n'.join(body)


def _treeview(master, columns, widths, SX, SY, selectmode='browse'):
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('Treeview', background='white', foreground='black',
                    rowheight=max(25, py(SY, 25)), fieldbackground='white',
                    bordercolor='gray', borderwidth=1, relief='solid')
    style.configure('Treeview.Heading', font=(FONT_FAMILY, fs(SY, 11), 'bold'),
                    background='#f2f2f2', bordercolor='#d0d0d0', borderwidth=1, relief='solid')
    style.map('Treeview', background=[('selected', '#cce5ff')])

    frame = Frame(master, bg='white')
    vertical_scrollbar = Scrollbar(frame, orient=VERTICAL)
    tree = ttk.Treeview(frame, columns=columns, show='headings', selectmode=selectmode,
                        yscrollcommand=vertical_scrollbar.set)
    vertical_scrollbar.config(command=tree.yview)
    vertical_scrollbar.pack(side=RIGHT, fill=Y)
    tree.pack(fill=BOTH, expand=True)
    for column_id, width in zip(columns, widths):
        tree.heading(column_id, text=column_id.replace('_', ' ').title())
        tree.column(column_id, width=px(SX, width), anchor=CENTER)
    return frame, tree


def _center_dialog(dialog, window, width, height, SX, SY):
    dialog.update_idletasks()
    x = window.winfo_rootx() + max((window.winfo_width() - px(SX, width)) // 2, 0)
    y = window.winfo_rooty() + max((window.winfo_height() - py(SY, height)) // 2, 0)
    dialog.geometry(f'{px(SX, width)}x{py(SY, height)}+{x}+{y}')


def show_low_stock(window):
    SX, SY = scale(window)
    dialog = Toplevel(window)
    dialog.title('Low Stock Report')
    dialog.configure(bg='white')
    dialog.transient(window)
    dialog.grab_set()
    dialog.protocol('WM_DELETE_WINDOW', dialog.destroy)

    Label(dialog, text='Low Stock Report', font=(FONT_FAMILY, fs(SY, 16), 'bold'),
          bg=PRIMARY, fg='white').pack(fill=X)

    top = Frame(dialog, bg='white')
    top.pack(pady=py(SY, 10))
    Label(top, text='Fallback max stock level:', font=(FONT_FAMILY, fs(SY, 13), 'bold'),
          bg='white').pack(side=LEFT, padx=px(SX, 10))
    threshold_entry = Entry(top, font=(FONT_FAMILY, fs(SY, 13)), bg=FIELD_BG, width=6)
    threshold_entry.insert(0, str(LOW_STOCK_THRESHOLD))
    threshold_entry.pack(side=LEFT)

    Label(top, text='(per-product reorder level wins when set)', font=(FONT_FAMILY, fs(SY, 11)),
          bg='white', fg='#666666').pack(side=LEFT, padx=px(SX, 8))

    columns = ('product', 'category', 'supplier', 'quantity', 'reorder_level')
    widths = (280, 220, 220, 110, 120)
    tree_frame, tree = _treeview(dialog, columns, widths, SX, SY)
    tree_frame.pack(fill=BOTH, expand=True, padx=px(SX, 20), pady=py(SY, 5))

    summary_label = Label(dialog, bg='white', font=(FONT_FAMILY, fs(SY, 13), 'bold'))
    summary_label.pack(pady=py(SY, 5))

    def refresh():
        try:
            threshold = int(threshold_entry.get().strip())
        except ValueError:
            crud.messagebox.showerror('Error', 'Max stock level must be a whole number')
            return
        rows = low_stock_rows(threshold)
        tree.delete(*tree.get_children())
        for row in rows:
            tree.insert('', END, values=(row['product'], row['category'] or '',
                                         row['supplier'] or '', row['quantity'],
                                         row['reorder_level'] or ''))
        summary_label.config(
            text=f'{len(rows)} product(s) at or below their reorder level')

    def export():
        try:
            threshold = int(threshold_entry.get().strip())
        except ValueError:
            crud.messagebox.showerror('Error', 'Max stock level must be a whole number')
            return
        rows = low_stock_rows(threshold)
        export_to_csv(dialog, ('Product', 'Category', 'Supplier', 'Quantity', 'Reorder Level'),
                      [(row['product'], row['category'] or '', row['supplier'] or '',
                        row['quantity'], row['reorder_level'] or '') for row in rows],
                      'low_stock.csv')

    controls = Frame(dialog, bg='white')
    controls.pack(pady=py(SY, 10))
    button(controls, 'Generate', font_size=fs(SY, 11), command=refresh).pack(side=LEFT, padx=px(SX, 10))
    button(controls, 'Export CSV', font_size=fs(SY, 11), command=export).pack(side=LEFT, padx=px(SX, 10))
    button(controls, 'Close', font_size=fs(SY, 11), command=dialog.destroy).pack(side=LEFT, padx=px(SX, 10))

    dialog.bind('<Escape>', lambda e: dialog.destroy())
    refresh()
    _center_dialog(dialog, window, 920, 560, SX, SY)
    return dialog


def show_sales_report(window):
    SX, SY = scale(window)
    dialog = Toplevel(window)
    dialog.title('Sales Report')
    dialog.configure(bg='white')
    dialog.transient(window)
    dialog.grab_set()
    dialog.protocol('WM_DELETE_WINDOW', dialog.destroy)

    Label(dialog, text='Sales Report', font=(FONT_FAMILY, fs(SY, 16), 'bold'),
          bg=PRIMARY, fg='white').pack(fill=X)

    filters = Frame(dialog, bg='white')
    filters.pack(pady=py(SY, 10))
    Label(filters, text='From:', font=(FONT_FAMILY, fs(SY, 13), 'bold'),
          bg='white').pack(side=LEFT, padx=(px(SX, 10), 4))
    from_entry = DateEntry(filters, width=12, font=(FONT_FAMILY, fs(SY, 13)),
                           state='readonly', date_pattern='yyyy-mm-dd', bg='white')
    from_entry.pack(side=LEFT)
    Label(filters, text='To:', font=(FONT_FAMILY, fs(SY, 13), 'bold'),
          bg='white').pack(side=LEFT, padx=(px(SX, 16), 4))
    to_entry = DateEntry(filters, width=12, font=(FONT_FAMILY, fs(SY, 13)),
                         state='readonly', date_pattern='yyyy-mm-dd', bg='white')
    to_entry.pack(side=LEFT)

    now = date.today()
    from_entry.set_date(now.replace(day=1))
    to_entry.set_date(now)

    columns = ('sale_id', 'invoice_number', 'product', 'quantity', 'unit_price', 'total',
               'sale_date', 'customer', 'payment_mode')
    widths = (70, 100, 200, 80, 100, 110, 110, 180, 80)
    tree_frame, tree = _treeview(dialog, columns, widths, SX, SY)
    tree_frame.pack(fill=BOTH, expand=True, padx=px(SX, 20), pady=py(SY, 5))

    summary_label = Label(dialog, bg='white', font=(FONT_FAMILY, fs(SY, 13), 'bold'))
    summary_label.pack(pady=py(SY, 5))

    def refresh():
        start = from_entry.get()
        end = to_entry.get()
        rows = sales_report_rows(start, end)
        tree.delete(*tree.get_children())
        for row in rows:
            tree.insert('', END, values=(row['sale_id'], row['invoice_number'] or '',
                                         row['product'] or '', row['quantity'],
                                         f'{row["unit_price"]:,.2f}', f'{row["total"]:,.2f}',
                                         row['sale_date'], row['customer'],
                                         row['payment_mode']))
        revenue = sum(row['total'] or 0 for row in rows)
        summary_label.config(
            text=f'{len(rows)} sale(s) | Total revenue: {revenue:,.2f}')

    def export():
        start = from_entry.get()
        end = to_entry.get()
        rows = sales_report_rows(start, end)
        export_to_csv(dialog,
                      ('Sale Id', 'Invoice', 'Product', 'Quantity', 'Unit Price', 'Total',
                       'Sale Date', 'Customer', 'Payment'),
                      [(row['sale_id'], row['invoice_number'] or '', row['product'] or '',
                        row['quantity'], row['unit_price'], row['total'], row['sale_date'],
                        row['customer'], row['payment_mode']) for row in rows],
                      'sales_report.csv')

    controls = Frame(dialog, bg='white')
    controls.pack(pady=py(SY, 10))
    button(controls, 'Generate', font_size=fs(SY, 11), command=refresh).pack(side=LEFT, padx=px(SX, 10))
    button(controls, 'Export CSV', font_size=fs(SY, 11), command=export).pack(side=LEFT, padx=px(SX, 10))
    button(controls, 'Close', font_size=fs(SY, 11), command=dialog.destroy).pack(side=LEFT, padx=px(SX, 10))

    dialog.bind('<Escape>', lambda e: dialog.destroy())
    refresh()
    _center_dialog(dialog, window, 1020, 600, SX, SY)
    return dialog


def _pdf_escape(text):
    return (str(text).encode('latin-1', 'replace').decode('latin-1')
            .replace('\\', r'\\').replace('(', r'\(').replace(')', r'\)'))


def write_pdf_receipt(filepath, text):
    lines = [line.rstrip() for line in text.splitlines()]
    content = 'BT\n/F1 12 Tf\n14 TL\n50 760 Td\n'
    for line in lines:
        content += f'({_pdf_escape(line)}) Tj\nT*\n'
    content += 'ET\n'
    data = content.encode('latin-1', 'replace')
    objects = [
        b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] '
        b'/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>',
        f'<< /Length {len(data)} >>\nstream\n'.encode('latin-1') + data + b'\nendstream',
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
    ]
    out = bytearray(b'%PDF-1.4\n')
    offsets = []
    for index, obj in enumerate(objects, 1):
        offsets.append(len(out))
        out += f'{index} 0 obj\n'.encode('latin-1') + obj + b'\nendobj\n'
    xref = len(out)
    out += f'xref\n0 {len(objects) + 1}\n'.encode('latin-1')
    out += b'0000000000 65535 f \n'
    for off in offsets:
        out += f'{off:010d} 00000 n \n'.encode('latin-1')
    out += (f'trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n'
            f'startxref\n{xref}\n%%EOF\n').encode('latin-1')
    with open(filepath, 'wb') as f:
        f.write(bytes(out))


def show_receipt(window, sale_id):
    text = receipt_text(sale_id)
    if text is None:
        crud.messagebox.showerror('Error', f'No sale found with id {sale_id}')
        return None
    SX, SY = scale(window)
    dialog = Toplevel(window)
    dialog.title(f'Receipt - Sale #{sale_id}')
    dialog.configure(bg='white')
    dialog.transient(window)
    dialog.grab_set()
    dialog.protocol('WM_DELETE_WINDOW', dialog.destroy)

    Label(dialog, text='Receipt', font=(FONT_FAMILY, fs(SY, 16), 'bold'),
          bg=PRIMARY, fg='white').pack(fill=X)

    text_widget = Text(dialog, font=('Courier', fs(SY, 13)), bg='white', relief=SOLID,
                       borderwidth=1, state=NORMAL)
    text_widget.insert(1.0, text)
    text_widget.config(state=DISABLED)
    text_widget.pack(fill=BOTH, expand=True, padx=px(SX, 30), pady=py(SY, 15))

    def save():
        from tkinter import filedialog
        filepath = filedialog.asksaveasfilename(
            parent=dialog, defaultextension='.txt', initialfile=f'receipt_{sale_id}.txt',
            filetypes=[('Text files', '*.txt'), ('All files', '*.*')])
        if not filepath:
            return
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text + '\n')
            crud.messagebox.showinfo('Success', f'Receipt saved to:\n{filepath}')
        except Exception as exc:
            logger.exception('failed to save receipt')
            crud.messagebox.showerror('Error', f'Save failed: {exc}')

    def save_pdf():
        from tkinter import filedialog
        filepath = filedialog.asksaveasfilename(
            parent=dialog, defaultextension='.pdf', initialfile=f'receipt_{sale_id}.pdf',
            filetypes=[('PDF files', '*.pdf'), ('All files', '*.*')])
        if not filepath:
            return
        try:
            write_pdf_receipt(filepath, text)
            crud.messagebox.showinfo('Success', f'PDF receipt saved to:\n{filepath}')
        except Exception as exc:
            logger.exception('failed to save PDF receipt')
            crud.messagebox.showerror('Error', f'Save failed: {exc}')

    controls = Frame(dialog, bg='white')
    controls.pack(pady=py(SY, 10))
    button(controls, 'Save Receipt', font_size=fs(SY, 11), command=save).pack(side=LEFT, padx=px(SX, 10))
    button(controls, 'Save PDF', font_size=fs(SY, 11), command=save_pdf).pack(side=LEFT, padx=px(SX, 10))
    button(controls, 'Close', font_size=fs(SY, 11), command=dialog.destroy).pack(side=LEFT, padx=px(SX, 10))

    dialog.bind('<Escape>', lambda e: dialog.destroy())
    _center_dialog(dialog, window, 480, 520, SX, SY)
    return dialog


REASON_LABELS = {
    'sale': 'Sale',
    'sale_update': 'Sale Updated',
    'sale_delete': 'Sale Deleted',
    'return': 'Return',
    'return_update': 'Return Updated',
    'return_delete': 'Return Deleted',
    'purchase': 'Purchase',
    'purchase_update': 'Purchase Updated',
    'purchase_delete': 'Purchase Deleted',
    'initial': 'Initial Stock',
    'adjustment': 'Adjustment',
}


def stock_movements_rows(start, end):
    return [dict(row) for row in query(
        'SELECT m.created_at, p.name AS product, m.quantity_delta, m.reason, '
        'm.reference_id, e.name AS user_name '
        'FROM stock_movements m '
        'LEFT JOIN products p ON p.product_id = m.product_id '
        'LEFT JOIN employee_data e ON e.empid = m.created_by '
        'WHERE date(m.created_at) >= ? AND date(m.created_at) <= ? '
        'ORDER BY m.movement_id DESC',
        (start, end))]


def show_stock_movements(window):
    SX, SY = scale(window)
    dialog = Toplevel(window)
    dialog.title('Stock Movements')
    dialog.configure(bg='white')
    dialog.transient(window)
    dialog.grab_set()
    dialog.protocol('WM_DELETE_WINDOW', dialog.destroy)

    Label(dialog, text='Stock Movements', font=(FONT_FAMILY, fs(SY, 16), 'bold'),
          bg=PRIMARY, fg='white').pack(fill=X)

    filters = Frame(dialog, bg='white')
    filters.pack(pady=py(SY, 10))
    Label(filters, text='From:', font=(FONT_FAMILY, fs(SY, 13), 'bold'),
          bg='white').pack(side=LEFT, padx=(px(SX, 10), 4))
    from_entry = DateEntry(filters, width=12, font=(FONT_FAMILY, fs(SY, 13)),
                           state='readonly', date_pattern='yyyy-mm-dd', bg='white')
    from_entry.pack(side=LEFT)
    Label(filters, text='To:', font=(FONT_FAMILY, fs(SY, 13), 'bold'),
          bg='white').pack(side=LEFT, padx=(px(SX, 16), 4))
    to_entry = DateEntry(filters, width=12, font=(FONT_FAMILY, fs(SY, 13)),
                         state='readonly', date_pattern='yyyy-mm-dd', bg='white')
    to_entry.pack(side=LEFT)

    now = date.today()
    from_entry.set_date(now.replace(day=1))
    to_entry.set_date(now)

    columns = ('created_at', 'product', 'quantity_delta', 'reason', 'reference_id', 'user_name')
    widths = (160, 200, 110, 130, 100, 160)
    tree_frame, tree = _treeview(dialog, columns, widths, SX, SY)
    tree_frame.pack(fill=BOTH, expand=True, padx=px(SX, 20), pady=py(SY, 5))

    summary_label = Label(dialog, bg='white', font=(FONT_FAMILY, fs(SY, 13), 'bold'))
    summary_label.pack(pady=py(SY, 5))

    def refresh():
        start = from_entry.get()
        end = to_entry.get()
        rows = stock_movements_rows(start, end)
        tree.delete(*tree.get_children())
        for row in rows:
            delta = row['quantity_delta']
            tree.insert('', END, values=(
                row['created_at'], row['product'] or '-',
                f'+{delta}' if delta > 0 else str(delta),
                REASON_LABELS.get(row['reason'], row['reason']),
                row['reference_id'] if row['reference_id'] is not None else '',
                row['user_name'] or '-'))
        summary_label.config(text=f'{len(rows)} movement(s)')

    def export():
        start = from_entry.get()
        end = to_entry.get()
        rows = stock_movements_rows(start, end)
        export_to_csv(dialog,
                      ('Date', 'Product', 'Quantity Change', 'Reason', 'Reference', 'User'),
                      [(row['created_at'], row['product'] or '', row['quantity_delta'],
                        REASON_LABELS.get(row['reason'], row['reason']),
                        row['reference_id'] if row['reference_id'] is not None else '',
                        row['user_name'] or '') for row in rows], 'stock_movements.csv')

    controls = Frame(dialog, bg='white')
    controls.pack(pady=py(SY, 10))
    button(controls, 'Generate', font_size=fs(SY, 11), command=refresh).pack(side=LEFT, padx=px(SX, 10))
    button(controls, 'Export CSV', font_size=fs(SY, 11), command=export).pack(side=LEFT, padx=px(SX, 10))
    button(controls, 'Close', font_size=fs(SY, 11), command=dialog.destroy).pack(side=LEFT, padx=px(SX, 10))

    dialog.bind('<Escape>', lambda e: dialog.destroy())
    refresh()
    _center_dialog(dialog, window, 1000, 580, SX, SY)
    return dialog


def stock_valuation_rows():
    return [dict(row) for row in query(
        'SELECT p.name AS product, c.name AS category, p.quantity, p.price, '
        'ROUND(p.quantity * p.price, 2) AS value '
        'FROM products p '
        'LEFT JOIN categories c ON c.category_id = p.category_id '
        'WHERE p.quantity > 0 ORDER BY value DESC')]


def _top_sellers():
    return [dict(row) for row in query(
        'SELECT p.name AS product, c.name AS category, SUM(s.quantity) AS units_sold, '
        'ROUND(SUM(s.total), 2) AS revenue '
        'FROM sales s JOIN products p ON p.product_id = s.product_id '
        'LEFT JOIN categories c ON c.category_id = p.category_id '
        'GROUP BY p.product_id ORDER BY revenue DESC')]


def _sales_by_employee():
    return [dict(row) for row in query(
        "SELECT COALESCE(e.name, '-') AS employee, "
        'COUNT(DISTINCT s.invoice_number) AS sales_count, '
        'SUM(-m.quantity_delta) AS units_sold, ROUND(SUM(s.total), 2) AS revenue '
        'FROM stock_movements m '
        'LEFT JOIN employee_data e ON e.empid = m.created_by '
        'LEFT JOIN sales s ON s.sale_id = m.reference_id '
        "WHERE m.reason = 'sale' GROUP BY m.created_by ORDER BY revenue DESC")]


def _profit_by_product():
    return [dict(row) for row in query(
        'SELECT p.name AS product, c.name AS category, SUM(s.quantity) AS units_sold, '
        'ROUND(SUM((s.unit_price - COALESCE(p.cost_price, 0)) * s.quantity), 2) AS profit '
        'FROM sales s JOIN products p ON p.product_id = s.product_id '
        'LEFT JOIN categories c ON c.category_id = p.category_id '
        'GROUP BY p.product_id ORDER BY profit DESC')]


def _profit_by_category():
    return [dict(row) for row in query(
        'SELECT COALESCE(c.name, "Uncategorised") AS category, '
        'SUM(s.quantity) AS units_sold, '
        'ROUND(SUM((s.unit_price - COALESCE(p.cost_price, 0)) * s.quantity), 2) AS profit '
        'FROM sales s JOIN products p ON p.product_id = s.product_id '
        'LEFT JOIN categories c ON c.category_id = p.category_id '
        'GROUP BY c.category_id ORDER BY profit DESC')]


ANALYTICS_REPORTS = {
    'Top Sellers': {
        'columns': ('product', 'category', 'units_sold', 'revenue'),
        'widths': (260, 220, 110, 140),
        'rows': _top_sellers,
        'export_headers': ('Product', 'Category', 'Units Sold', 'Revenue'),
        'values': lambda r: (r['product'], r['category'] or '', r['units_sold'],
                             f'{r["revenue"]:,.2f}'),
    },
    'Sales by Employee': {
        'columns': ('employee', 'sales_count', 'units_sold', 'revenue'),
        'widths': (240, 120, 110, 140),
        'rows': _sales_by_employee,
        'export_headers': ('Employee', 'Sales Count', 'Units Sold', 'Revenue'),
        'values': lambda r: (r['employee'], r['sales_count'], r['units_sold'],
                             f'{r["revenue"]:,.2f}'),
    },
    'Profit by Product': {
        'columns': ('product', 'category', 'units_sold', 'profit'),
        'widths': (260, 220, 110, 140),
        'rows': _profit_by_product,
        'export_headers': ('Product', 'Category', 'Units Sold', 'Profit'),
        'values': lambda r: (r['product'], r['category'] or '', r['units_sold'],
                             f'{r["profit"]:,.2f}'),
    },
    'Profit by Category': {
        'columns': ('category', 'units_sold', 'profit'),
        'widths': (320, 130, 160),
        'rows': _profit_by_category,
        'export_headers': ('Category', 'Units Sold', 'Profit'),
        'values': lambda r: (r['category'], r['units_sold'], f'{r["profit"]:,.2f}'),
    },
}


def show_stock_valuation(window):
    SX, SY = scale(window)
    dialog = Toplevel(window)
    dialog.title('Stock Valuation')
    dialog.configure(bg='white')
    dialog.transient(window)
    dialog.grab_set()
    dialog.protocol('WM_DELETE_WINDOW', dialog.destroy)

    Label(dialog, text='Stock Valuation', font=(FONT_FAMILY, fs(SY, 16), 'bold'),
          bg=PRIMARY, fg='white').pack(fill=X)

    columns = ('product', 'category', 'quantity', 'price', 'value')
    widths = (280, 240, 120, 140, 160)
    tree_frame, tree = _treeview(dialog, columns, widths, SX, SY)
    tree_frame.pack(fill=BOTH, expand=True, padx=px(SX, 20), pady=py(SY, 10))

    summary_label = Label(dialog, bg='white', font=(FONT_FAMILY, fs(SY, 14), 'bold'))
    summary_label.pack(pady=py(SY, 5))

    def refresh():
        rows = stock_valuation_rows()
        tree.delete(*tree.get_children())
        for row in rows:
            tree.insert('', END, values=(row['product'], row['category'] or '',
                                         row['quantity'], f'{row["price"]:,.2f}',
                                         f'{row["value"]:,.2f}'))
        total = sum(row['value'] or 0 for row in rows)
        summary_label.config(text=f'Total inventory value: {total:,.2f}')

    def export():
        rows = stock_valuation_rows()
        export_to_csv(dialog, ('Product', 'Category', 'Quantity', 'Price', 'Value'),
                      [(row['product'], row['category'] or '', row['quantity'],
                        row['price'], row['value']) for row in rows],
                      'stock_valuation.csv')

    controls = Frame(dialog, bg='white')
    controls.pack(pady=py(SY, 10))
    button(controls, 'Refresh', font_size=fs(SY, 11), command=refresh).pack(side=LEFT, padx=px(SX, 10))
    button(controls, 'Export CSV', font_size=fs(SY, 11), command=export).pack(side=LEFT, padx=px(SX, 10))
    button(controls, 'Close', font_size=fs(SY, 11), command=dialog.destroy).pack(side=LEFT, padx=px(SX, 10))

    dialog.bind('<Escape>', lambda e: dialog.destroy())
    refresh()
    _center_dialog(dialog, window, 1000, 580, SX, SY)
    return dialog


def show_sales_analytics(window):
    SX, SY = scale(window)
    dialog = Toplevel(window)
    dialog.title('Sales Analytics')
    dialog.configure(bg='white')
    dialog.transient(window)
    dialog.grab_set()
    dialog.protocol('WM_DELETE_WINDOW', dialog.destroy)

    Label(dialog, text='Sales Analytics', font=(FONT_FAMILY, fs(SY, 16), 'bold'),
          bg=PRIMARY, fg='white').pack(fill=X)

    top = Frame(dialog, bg='white')
    top.pack(pady=py(SY, 10))
    Label(top, text='Report:', font=(FONT_FAMILY, fs(SY, 13), 'bold'),
          bg='white').pack(side=LEFT, padx=px(SX, 10))
    report_var = StringVar(value='Top Sellers')
    report_combo = ttk.Combobox(top, textvariable=report_var, state='readonly',
                                values=list(ANALYTICS_REPORTS), width=20,
                                font=(FONT_FAMILY, fs(SY, 12)))
    report_combo.pack(side=LEFT)

    tree_frame = Frame(dialog, bg='white')
    tree_frame.pack(fill=BOTH, expand=True, padx=px(SX, 20), pady=py(SY, 5))

    summary_label = Label(dialog, bg='white', font=(FONT_FAMILY, fs(SY, 13), 'bold'))
    summary_label.pack(pady=py(SY, 5))

    tree = None

    def build_tree():
        nonlocal tree
        if tree is not None:
            tree.master.destroy()
        spec = ANALYTICS_REPORTS[report_var.get()]
        frame, new_tree = _treeview(dialog, spec['columns'], spec['widths'], SX, SY)
        frame.pack(fill=BOTH, expand=True, padx=px(SX, 20), pady=py(SY, 5))
        tree = new_tree
        return spec

    def refresh(event=None):
        spec = build_tree()
        rows = spec['rows']()
        for row in rows:
            tree.insert('', END, values=spec['values'](row))
        total_col = 'revenue' if 'revenue' in spec['columns'] else 'profit'
        total = sum(row.get(total_col) or 0 for row in rows)
        summary_label.config(text=f'{len(rows)} row(s) | Total {total_col}: {total:,.2f}')

    def export():
        spec = ANALYTICS_REPORTS[report_var.get()]
        rows = spec['rows']()
        export_to_csv(dialog, spec['export_headers'],
                      [spec['values'](row) for row in rows], 'analytics.csv')

    report_combo.bind('<<ComboboxSelected>>', refresh)

    controls = Frame(dialog, bg='white')
    controls.pack(pady=py(SY, 10))
    button(controls, 'Refresh', font_size=fs(SY, 11), command=refresh).pack(side=LEFT, padx=px(SX, 10))
    button(controls, 'Export CSV', font_size=fs(SY, 11), command=export).pack(side=LEFT, padx=px(SX, 10))
    button(controls, 'Close', font_size=fs(SY, 11), command=dialog.destroy).pack(side=LEFT, padx=px(SX, 10))

    dialog.bind('<Escape>', lambda e: dialog.destroy())
    refresh()
    _center_dialog(dialog, window, 1000, 580, SX, SY)
    return dialog


def reorder_rows(threshold=LOW_STOCK_THRESHOLD):
    return [dict(row) for row in query(
        'SELECT p.product_id, p.name AS product, s.name AS supplier, p.supplier_id, '
        'p.quantity, p.reorder_level, COALESCE(p.cost_price, 0) AS cost_price, '
        'MAX(2 * COALESCE(NULLIF(p.reorder_level, 0), ?) - p.quantity, 1) AS suggested_qty, '
        'ROUND(MAX(2 * COALESCE(NULLIF(p.reorder_level, 0), ?) - p.quantity, 1) * '
        'COALESCE(p.cost_price, 0), 2) AS suggested_cost '
        'FROM products p LEFT JOIN suppliers s ON s.supplier_id = p.supplier_id '
        'WHERE p.quantity <= COALESCE(NULLIF(p.reorder_level, 0), ?) '
        'ORDER BY p.quantity, p.name',
        (threshold, threshold, threshold))]


def show_reorder_picker(window):
    SX, SY = scale(window)
    dialog = Toplevel(window)
    dialog.title('Reorder & Purchase')
    dialog.configure(bg='white')
    dialog.transient(window)
    dialog.grab_set()
    dialog.protocol('WM_DELETE_WINDOW', dialog.destroy)

    Label(dialog, text='Reorder & Purchase', font=(FONT_FAMILY, fs(SY, 16), 'bold'),
          bg=PRIMARY, fg='white').pack(fill=X)

    top = Frame(dialog, bg='white')
    top.pack(pady=py(SY, 10))
    Label(top, text='Fallback max stock level:', font=(FONT_FAMILY, fs(SY, 13), 'bold'),
          bg='white').pack(side=LEFT, padx=px(SX, 10))
    threshold_entry = Entry(top, font=(FONT_FAMILY, fs(SY, 13)), bg=FIELD_BG, width=6)
    threshold_entry.insert(0, str(LOW_STOCK_THRESHOLD))
    threshold_entry.pack(side=LEFT)
    Label(top, text='(per-product reorder level wins when set)',
          font=(FONT_FAMILY, fs(SY, 11)), bg='white', fg='#666666').pack(side=LEFT, padx=px(SX, 8))

    columns = ('product', 'supplier', 'quantity', 'reorder_level', 'suggested_qty',
               'cost_price', 'suggested_cost')
    widths = (250, 200, 90, 110, 120, 100, 120)
    tree_frame, tree = _treeview(dialog, columns, widths, SX, SY, selectmode='extended')
    tree_frame.pack(fill=BOTH, expand=True, padx=px(SX, 20), pady=py(SY, 5))

    summary_label = Label(dialog, bg='white', font=(FONT_FAMILY, fs(SY, 13), 'bold'))
    summary_label.pack(pady=py(SY, 5))

    displayed_rows = []

    def refresh():
        try:
            threshold = int(threshold_entry.get().strip())
        except ValueError:
            crud.messagebox.showerror('Error', 'Max stock level must be a whole number')
            return
        displayed_rows.clear()
        rows = reorder_rows(threshold)
        tree.delete(*tree.get_children())
        for row in rows:
            tree.insert('', END, values=(row['product'], row['supplier'] or '-',
                                         row['quantity'], row['reorder_level'] or '',
                                         row['suggested_qty'], f'{row["cost_price"]:,.2f}',
                                         f'{row["suggested_cost"]:,.2f}'))
            displayed_rows.append(row)
        cost = sum(row['suggested_cost'] for row in rows)
        summary_label.config(
            text=f'{len(rows)} product(s) need restock | estimated cost: {cost:,.2f}')

    def create_purchases():
        selected = tree.selection()
        if not selected:
            crud.messagebox.showerror('Error', 'Please select at least one product to purchase')
            return
        created = 0
        for iid in selected:
            row = displayed_rows[tree.index(iid)]
            ok = purchases.create_purchase(row['product_id'], row['suggested_qty'],
                                           row['cost_price'], row['supplier_id'],
                                           date.today().isoformat())
            created += 1 if ok else 0
        crud.messagebox.showinfo(
            'Success', f'{created} purchase record(s) created and stock received')
        refresh()

    def export():
        try:
            threshold = int(threshold_entry.get().strip())
        except ValueError:
            crud.messagebox.showerror('Error', 'Max stock level must be a whole number')
            return
        rows = reorder_rows(threshold)
        export_to_csv(dialog, ('Product', 'Supplier', 'Quantity', 'Reorder Level',
                               'Suggested Qty', 'Unit Cost', 'Suggested Cost'),
                      [(row['product'], row['supplier'] or '', row['quantity'],
                        row['reorder_level'] or '', row['suggested_qty'],
                        row['cost_price'], row['suggested_cost']) for row in rows],
                      'reorder_list.csv')

    controls = Frame(dialog, bg='white')
    controls.pack(pady=py(SY, 10))
    button(controls, 'Create Purchases', font_size=fs(SY, 11),
           command=create_purchases).pack(side=LEFT, padx=px(SX, 10))
    button(controls, 'Export CSV', font_size=fs(SY, 11), command=export).pack(side=LEFT, padx=px(SX, 10))
    button(controls, 'Close', font_size=fs(SY, 11), command=dialog.destroy).pack(side=LEFT, padx=px(SX, 10))

    dialog.bind('<Escape>', lambda e: dialog.destroy())
    refresh()
    _center_dialog(dialog, window, 1020, 560, SX, SY)
    return dialog


def show_customer_balances(window):
    SX, SY = scale(window)
    dialog = Toplevel(window)
    dialog.title('Customer Balances')
    dialog.configure(bg='white')
    dialog.transient(window)
    dialog.grab_set()
    dialog.protocol('WM_DELETE_WINDOW', dialog.destroy)

    Label(dialog, text='Outstanding Customer Credit', font=(FONT_FAMILY, fs(SY, 16), 'bold'),
          bg=PRIMARY, fg='white').pack(fill=X)

    columns = ('name', 'phone', 'credit_limit', 'balance')
    widths = (260, 200, 140, 160)
    tree_frame, tree = _treeview(dialog, columns, widths, SX, SY)
    tree_frame.pack(fill=BOTH, expand=True, padx=px(SX, 20), pady=py(SY, 10))

    summary_label = Label(dialog, bg='white', font=(FONT_FAMILY, fs(SY, 13), 'bold'))
    summary_label.pack(pady=py(SY, 5))

    def refresh():
        rows = customers.customer_balances_rows()
        tree.delete(*tree.get_children())
        for row in rows:
            tree.insert('', END, values=(row['name'], row['phone'] or '',
                                         f'{row["credit_limit"] or 0:,.2f}',
                                         f'{row["balance"]:,.2f}'))
        total = sum(row['balance'] or 0 for row in rows)
        summary_label.config(
            text=f'{len(rows)} customer(s) on credit | Total outstanding: {total:,.2f}')

    def export():
        rows = customers.customer_balances_rows()
        export_to_csv(dialog, ('Customer', 'Phone', 'Credit Limit', 'Outstanding Balance'),
                      [(row['name'], row['phone'] or '', row['credit_limit'] or 0,
                        row['balance'] or 0) for row in rows],
                      'customer_balances.csv')

    controls = Frame(dialog, bg='white')
    controls.pack(pady=py(SY, 10))
    button(controls, 'Refresh', font_size=fs(SY, 11), command=refresh).pack(side=LEFT, padx=px(SX, 10))
    button(controls, 'Export CSV', font_size=fs(SY, 11), command=export).pack(side=LEFT, padx=px(SX, 10))
    button(controls, 'Close', font_size=fs(SY, 11), command=dialog.destroy).pack(side=LEFT, padx=px(SX, 10))

    dialog.bind('<Escape>', lambda e: dialog.destroy())
    refresh()
    _center_dialog(dialog, window, 800, 520, SX, SY)
    return dialog


def _revenue_by_date():
    return [dict(row) for row in query(
        'SELECT sale_date AS day, SUM(total) AS revenue '
        'FROM sales GROUP BY sale_date ORDER BY sale_date')]


def show_charts(window):
    SX, SY = scale(window)
    try:
        import matplotlib
        matplotlib.use('TkAgg')
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.figure import Figure
    except ImportError:
        crud.messagebox.showerror(
            'Error', 'Matplotlib is not installed.\nInstall it with: pip install matplotlib')
        return None

    revenue = _revenue_by_date()
    top = _top_sellers()
    if not revenue and not top:
        crud.messagebox.showinfo('Charts', 'No sales data to chart yet.')
        return None

    dialog = Toplevel(window)
    dialog.title('Sales Charts')
    dialog.configure(bg='white')
    dialog.transient(window)
    dialog.grab_set()
    dialog.protocol('WM_DELETE_WINDOW', dialog.destroy)

    Label(dialog, text='Sales Charts', font=(FONT_FAMILY, fs(SY, 16), 'bold'),
          bg=PRIMARY, fg='white').pack(fill=X)

    canvas_frame = Frame(dialog, bg='white')
    canvas_frame.pack(fill=BOTH, expand=True, padx=px(SX, 20), pady=py(SY, 10))

    figure = Figure(figsize=(11, 5), dpi=90)
    if revenue:
        ax1 = figure.add_subplot(1, 2, 1)
        days = [r['day'] for r in revenue]
        amounts = [r['revenue'] or 0 for r in revenue]
        ax1.bar(days, amounts, color='#0f4d7d')
        ax1.set_title('Revenue by Day')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Revenue')
        ax1.tick_params(axis='x', rotation=45)
    if top:
        ax2 = figure.add_subplot(1, 2, 2)
        sellers = [r['product'] for r in top[:5]]
        seller_revenue = [r['revenue'] or 0 for r in top[:5]]
        ax2.barh(sellers[::-1], seller_revenue[::-1], color='#2ca089')
        ax2.set_title('Top 5 Products by Revenue')
        ax2.set_xlabel('Revenue')
        ax2.set_ylabel('Product')
    figure.tight_layout()

    canvas = FigureCanvasTkAgg(figure, master=canvas_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=BOTH, expand=True)

    controls = Frame(dialog, bg='white')
    controls.pack(pady=py(SY, 10))
    button(controls, 'Close', font_size=fs(SY, 12), command=dialog.destroy).pack()
    dialog.bind('<Escape>', lambda e: dialog.destroy())
    _center_dialog(dialog, window, 1000, 620, SX, SY)
    return dialog


def show_reports_hub(window):
    SX, SY = scale(window)
    dialog = Toplevel(window)
    dialog.title('Reports')
    dialog.configure(bg='white')
    dialog.transient(window)
    dialog.grab_set()
    dialog.protocol('WM_DELETE_WINDOW', dialog.destroy)

    Label(dialog, text='Reports', font=(FONT_FAMILY, fs(SY, 16), 'bold'),
          bg=PRIMARY, fg='white').pack(fill=X)

    body = Frame(dialog, bg='white')
    body.pack(padx=px(SX, 40), pady=py(SY, 25))
    button(body, 'Low Stock Report', font_size=fs(SY, 12),
           command=lambda: show_low_stock(window)).pack(fill=X, pady=py(SY, 6))
    button(body, 'Reorder & Purchase', font_size=fs(SY, 12),
           command=lambda: show_reorder_picker(window)).pack(fill=X, pady=py(SY, 6))
    button(body, 'Sales Report', font_size=fs(SY, 12),
           command=lambda: show_sales_report(window)).pack(fill=X, pady=py(SY, 6))
    button(body, 'Stock Movements', font_size=fs(SY, 12),
           command=lambda: show_stock_movements(window)).pack(fill=X, pady=py(SY, 6))
    button(body, 'Stock Valuation', font_size=fs(SY, 12),
           command=lambda: show_stock_valuation(window)).pack(fill=X, pady=py(SY, 6))
    button(body, 'Customer Balances', font_size=fs(SY, 12),
           command=lambda: show_customer_balances(window)).pack(fill=X, pady=py(SY, 6))
    button(body, 'Sales Analytics', font_size=fs(SY, 12),
           command=lambda: show_sales_analytics(window)).pack(fill=X, pady=py(SY, 6))
    button(body, 'Close', font_size=fs(SY, 12),
           command=dialog.destroy).pack(fill=X, pady=py(SY, 6))

    dialog.bind('<Escape>', lambda e: dialog.destroy())
    _center_dialog(dialog, window, 420, 480, SX, SY)
    return dialog
