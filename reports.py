from datetime import date, datetime
from tkinter import *
from tkinter import ttk
from tkcalendar import DateEntry

import crud
from database import query, query_one
from layout import (FONT_FAMILY, PRIMARY, FIELD_BG, button, export_to_csv,
                    fs, ph, px, pw, py, scale)

LOW_STOCK_THRESHOLD = 5


def low_stock_rows(threshold=LOW_STOCK_THRESHOLD):
    return [dict(row) for row in query(
        'SELECT p.product_id, p.name AS product, c.name AS category, '
        's.name AS supplier, p.quantity '
        'FROM products p '
        'LEFT JOIN categories c ON c.category_id = p.category_id '
        'LEFT JOIN suppliers s ON s.supplier_id = p.supplier_id '
        'WHERE p.quantity <= ? ORDER BY p.quantity, p.name',
        (threshold,))]


def low_stock_count(threshold=LOW_STOCK_THRESHOLD):
    row = query_one(
        'SELECT COUNT(*) AS n FROM products WHERE quantity <= ?', (threshold,))
    return row['n'] if row else 0


def sales_report_rows(start, end):
    return [dict(row) for row in query(
        'SELECT s.sale_id, p.name AS product, s.quantity, s.unit_price, s.total, '
        's.sale_date, s.customer '
        'FROM sales s LEFT JOIN products p ON p.product_id = s.product_id '
        'WHERE s.sale_date >= ? AND s.sale_date <= ? '
        'ORDER BY s.sale_date, s.sale_id',
        (start, end))]


def receipt_text(sale_id):
    row = query_one(
        'SELECT s.sale_id, p.name AS product, s.quantity, s.unit_price, s.total, '
        's.sale_date, s.customer '
        'FROM sales s LEFT JOIN products p ON p.product_id = s.product_id '
        'WHERE s.sale_id = ?', (sale_id,))
    if not row:
        return None
    total = row['total'] or 0
    return '\n'.join([
        'INVENTORY MANAGEMENT SYSTEM',
        '==============================',
        f'Sale ID:      {row["sale_id"]}',
        f'Date:         {row["sale_date"]}',
        f'Product:      {row["product"] or "-"}',
        f'Quantity:     {row["quantity"]}',
        f'Unit Price:   {row["unit_price"]:,.2f}',
        '------------------------------',
        f'Total:        {total:,.2f}',
        f'Customer:     {row["customer"]}',
        '==============================',
        'Thank you for your business!',
    ])


def _treeview(master, columns, widths, SX, SY):
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
    tree = ttk.Treeview(frame, columns=columns, show='headings',
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
    Label(top, text='Max stock level:', font=(FONT_FAMILY, fs(SY, 13), 'bold'),
          bg='white').pack(side=LEFT, padx=px(SX, 10))
    threshold_entry = Entry(top, font=(FONT_FAMILY, fs(SY, 13)), bg=FIELD_BG, width=6)
    threshold_entry.insert(0, str(LOW_STOCK_THRESHOLD))
    threshold_entry.pack(side=LEFT)

    columns = ('product', 'category', 'supplier', 'quantity')
    widths = (280, 240, 240, 120)
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
                                         row['supplier'] or '', row['quantity']))
        summary_label.config(
            text=f'{len(rows)} product(s) at or below stock level {threshold}')

    def export():
        try:
            threshold = int(threshold_entry.get().strip())
        except ValueError:
            crud.messagebox.showerror('Error', 'Max stock level must be a whole number')
            return
        rows = low_stock_rows(threshold)
        export_to_csv(dialog, ('Product', 'Category', 'Supplier', 'Quantity'),
                      [(row['product'], row['category'] or '', row['supplier'] or '',
                        row['quantity']) for row in rows], 'low_stock.csv')

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

    columns = ('sale_id', 'product', 'quantity', 'unit_price', 'total', 'sale_date', 'customer')
    widths = (80, 220, 90, 120, 120, 120, 220)
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
            tree.insert('', END, values=(row['sale_id'], row['product'] or '',
                                         row['quantity'], f'{row["unit_price"]:,.2f}',
                                         f'{row["total"]:,.2f}', row['sale_date'],
                                         row['customer']))
        revenue = sum(row['total'] or 0 for row in rows)
        summary_label.config(
            text=f'{len(rows)} sale(s) | Total revenue: {revenue:,.2f}')

    def export():
        start = from_entry.get()
        end = to_entry.get()
        rows = sales_report_rows(start, end)
        export_to_csv(dialog,
                      ('Sale Id', 'Product', 'Quantity', 'Unit Price', 'Total',
                       'Sale Date', 'Customer'),
                      [(row['sale_id'], row['product'] or '', row['quantity'],
                        row['unit_price'], row['total'], row['sale_date'], row['customer'])
                       for row in rows], 'sales_report.csv')

    controls = Frame(dialog, bg='white')
    controls.pack(pady=py(SY, 10))
    button(controls, 'Generate', font_size=fs(SY, 11), command=refresh).pack(side=LEFT, padx=px(SX, 10))
    button(controls, 'Export CSV', font_size=fs(SY, 11), command=export).pack(side=LEFT, padx=px(SX, 10))
    button(controls, 'Close', font_size=fs(SY, 11), command=dialog.destroy).pack(side=LEFT, padx=px(SX, 10))

    dialog.bind('<Escape>', lambda e: dialog.destroy())
    refresh()
    _center_dialog(dialog, window, 1020, 600, SX, SY)
    return dialog


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
            crud.messagebox.showerror('Error', f'Save failed: {exc}')

    controls = Frame(dialog, bg='white')
    controls.pack(pady=py(SY, 10))
    button(controls, 'Save Receipt', font_size=fs(SY, 11), command=save).pack(side=LEFT, padx=px(SX, 10))
    button(controls, 'Close', font_size=fs(SY, 11), command=dialog.destroy).pack(side=LEFT, padx=px(SX, 10))

    dialog.bind('<Escape>', lambda e: dialog.destroy())
    _center_dialog(dialog, window, 480, 520, SX, SY)
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
    button(body, 'Sales Report', font_size=fs(SY, 12),
           command=lambda: show_sales_report(window)).pack(fill=X, pady=py(SY, 6))
    button(body, 'Close', font_size=fs(SY, 12),
           command=dialog.destroy).pack(fill=X, pady=py(SY, 6))

    dialog.bind('<Escape>', lambda e: dialog.destroy())
    _center_dialog(dialog, window, 420, 300, SX, SY)
    return dialog
