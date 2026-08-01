from datetime import datetime
from tkinter import *
from tkinter import ttk, messagebox
from tkcalendar import DateEntry

from app_log import logger
from database import (commit, execute, format_money, is_integrity_error, money_from_cents,
                      money_to_cents, next_id, query, query_one, rollback, to_iso_date)
from layout import (ACCENT, FIELD_BG, FONT_FAMILY, PRIMARY, ToolTip, resource_path, button,
                    export_to_csv, fs, is_number, is_positive_int, ph, pw, px, py, scale,
                    validate_email, validate_phone)

_frames = {}


def fetch_options(table, idcol, namecol):
    return [(row['id'], row['name']) for row in
            query(f'SELECT {idcol} AS id, {namecol} AS name FROM {table} ORDER BY {namecol}')]


def lookup_id(table, idcol, namecol, name):
    row = query_one(f'SELECT {idcol} AS id FROM {table} WHERE {namecol} = ? LIMIT 1', (name,))
    return row['id'] if row else None


def fetch_rows(spec, where=None, params=()):
    columns = ', '.join(spec.get('select_columns') or [column[0] for column in spec['columns']])
    sql = f"SELECT {columns} FROM {spec['table']} {spec.get('join', '')}"
    if where:
        sql += f' WHERE {where}'
    return [dict(row) for row in query(sql, params)]


def count_rows(spec):
    return query_one(f"SELECT COUNT(*) AS n FROM {spec['table']}")['n']


def insert_row(spec, data):
    try:
        columns = [key for key in spec['table_columns'] if key in data and data[key] is not None]
        if not columns:
            return False
        placeholders = ', '.join('?' for _ in columns)
        execute(f"INSERT INTO {spec['table']} ({', '.join(columns)}) VALUES ({placeholders})",
                tuple(data[key] for key in columns))
        commit()
        return True
    except Exception as exc:
        rollback()
        logger.exception('INSERT failed on %s', spec['table'])
        if is_integrity_error(exc):
            messagebox.showerror('Error', spec['unique_msg'])
        else:
            messagebox.showerror('Error', f'Database error: {exc}')
        return False


def update_row(spec, data):
    try:
        pk = spec['pk']
        sets = {key: value for key, value in data.items() if key != pk}
        columns = [key for key in spec['table_columns'] if key in sets and sets[key] is not None]
        if not columns:
            return False
        sql = f"UPDATE {spec['table']} SET {', '.join(column + ' = ?' for column in columns)} WHERE {pk} = ?"
        cursor = execute(sql, tuple(sets[key] for key in columns) + (data.get(pk),))
        commit()
        if cursor.rowcount == 0:
            rollback()
            messagebox.showerror('Error', f"No record found with that {spec['pk_label']}")
            return False
        return True
    except Exception as exc:
        rollback()
        logger.exception('UPDATE failed on %s', spec['table'])
        messagebox.showerror('Error', f'Database error: {exc}')
        return False


def delete_row(spec, pk_value):
    guard = spec.get('delete_guard')
    if guard:
        linked = query_one(f'SELECT COUNT(*) AS n FROM {guard[0]} WHERE {guard[1]} = ?',
                           (pk_value,))['n']
        if linked:
            messagebox.showerror('Error', spec.get(
                'delete_guard_msg', 'Cannot delete: this record is referenced by other records'))
            return False
    try:
        execute(f"DELETE FROM {spec['table']} WHERE {spec['pk']} = ?", (pk_value,))
        commit()
        return True
    except Exception as exc:
        rollback()
        logger.exception('DELETE failed on %s', spec['table'])
        if is_integrity_error(exc):
            messagebox.showerror('Error', 'Cannot delete: this record is referenced by other records')
        else:
            messagebox.showerror('Error', f'Database error: {exc}')
        return False


def export_csv(spec):
    filename, headers, keys = spec['csv']
    money_keys = {field['key'] for field in spec['fields'] if field.get('format') == 'money'}
    records = [tuple(money_from_cents(row[key]) if key in money_keys else row[key] for key in keys)
               for row in query(f"SELECT {', '.join(keys)} FROM {spec['table']}")]
    export_to_csv(None, headers, records, filename)


def validate_data(spec, data, mode):
    for field in spec['fields']:
        key = field['key']
        value = data.get(key)
        placeholder = field.get('placeholder')
        if value == placeholder:
            data[key] = None
            value = None

        required = field.get('required', False) or (field.get('required_add', False) and mode == 'add')
        if required and (value is None or str(value).strip() == ''):
            if field['kind'] in ('combobox', 'source'):
                messagebox.showerror('Error', field['msg'])
            else:
                messagebox.showerror('Error', 'All fields are required')
            return None

        if field.get('mask') and mode == 'update' and (value is None or str(value).strip() == ''):
            data.pop(key, None)
            continue

        if value is None or str(value).strip() == '':
            continue

        vtype = field.get('validate')
        if vtype == 'positive_int' and not is_positive_int(value):
            messagebox.showerror('Error', field['msg'])
            return None
        if vtype == 'number' and not is_number(value, positive=field.get('positive', False)):
            messagebox.showerror('Error', field['msg'])
            return None
        if vtype == 'email' and not validate_email(value):
            messagebox.showerror('Error', field['msg'])
            return None
        if vtype == 'phone' and not validate_phone(value):
            messagebox.showerror('Error', field['msg'])
            return None

        if field.get('store') == 'int':
            data[key] = int(str(value).strip())
        elif field.get('store') == 'float':
            if field.get('format') == 'money':
                data[key] = money_to_cents(value)
            else:
                data[key] = float(str(value).strip().replace(',', ''))
        elif field.get('store') == 'date':
            data[key] = to_iso_date(str(value).strip())
    return data


def format_value(field, value):
    if value is None:
        return ''
    if field and field.get('format') == 'money':
        try:
            return format_money(value)
        except (ValueError, TypeError):
            return str(value)
    if field and field.get('format') == 'int':
        try:
            return str(int(value))
        except (ValueError, TypeError):
            return str(value)
    return str(value)


def render_rows(treeview, spec, rows):
    keys = [column[0] for column in spec['columns']]
    fields = {field['key']: field for field in spec['fields']}
    treeview.delete(*treeview.get_children())
    for row in rows:
        values = []
        for key in keys:
            field = fields.get(key)
            if field and field.get('mask'):
                values.append('********')
            else:
                values.append(format_value(field, row.get(key)))
        treeview.insert('', END, values=values)
    spec['_rows'] = rows


def search_and_render(spec, option, value):
    if option == 'Search By':
        messagebox.showerror('Error', 'Please select a search option')
        return
    if value == '':
        messagebox.showerror('Error', 'Search field is required')
        return
    column = dict(spec['search']).get(option)
    if not column:
        messagebox.showerror('Error', 'Please select a valid search option')
        return
    rows = fetch_rows(spec, where=f'{column} LIKE ?', params=(f'%{value}%',))
    render_rows(spec['treeview'], spec, rows)
    if not rows:
        messagebox.showinfo('No Records', 'No matching records found')


def set_widget(widget, value):
    if widget.cget('state') == 'readonly':
        widget.config(state='normal')
        widget.delete(0, END)
        widget.insert(0, value)
        widget.config(state='readonly')
    else:
        widget.delete(0, END)
        widget.insert(0, value)


def _set_date(widget, value):
    if not value:
        widget._set_text('')
        return
    for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
        try:
            widget.set_date(datetime.strptime(str(value), fmt))
            return
        except (ValueError, TypeError):
            continue
    widget._set_text('')


def refresh_sources(spec, widgets):
    for field in spec['fields']:
        if field.get('kind') == 'source':
            options = fetch_options(*field['source'])
            field['_mapping'] = {name: option_id for option_id, name in options}
            widgets[field['key']].config(values=[name for _, name in options])


def collect(spec, widgets):
    data = {}
    for field in spec['fields']:
        key = field['key']
        widget = widgets[key]
        kind = field['kind']
        if kind in ('entry', 'combobox', 'source', 'date'):
            value = widget.get().strip()
        elif kind == 'text':
            value = widget.get(1.0, END).strip()
        else:
            continue
        if kind in ('combobox', 'source') and value == field.get('placeholder'):
            value = None
        data[key] = value

    for field in spec['fields']:
        if field.get('kind') == 'source':
            name = data.get(field['key'])
            if not name:
                data[field['key']] = None
            else:
                data[field['key']] = field['_mapping'].get(name)
    return data


def populate(spec, widgets, row):
    for field in spec['fields']:
        key = field['key']
        widget = widgets[key]
        kind = field['kind']
        if field.get('mask') or kind == 'label':
            continue
        value = row.get(field.get('display_key', key))
        if kind in ('combobox', 'source'):
            widget.set(format_value(field, value) if value not in (None, '') else field.get('placeholder', ''))
        elif kind == 'date':
            _set_date(widget, value)
        elif kind == 'text':
            widget.delete(1.0, END)
            widget.insert(1.0, format_value(field, value))
        elif kind == 'entry':
            set_widget(widget, format_value(field, value))


def clear_fields(spec, widgets):
    spec['selected'] = None
    for field in spec['fields']:
        widget = widgets[field['key']]
        kind = field['kind']
        if kind in ('combobox', 'source'):
            widget.set(field.get('placeholder', ''))
        elif kind == 'date':
            widget._set_text('')
        elif kind == 'text':
            widget.delete(1.0, END)
        elif kind == 'entry':
            set_widget(widget, '')
    if spec.get('on_clear'):
        spec['on_clear'](widgets)
    first = next((field for field in spec['fields']
                  if field['kind'] != 'label' and not field.get('auto')), None)
    if first:
        widgets[first['key']].focus_set()


def build_form(window, spec, ops, on_close=None):
    name = spec['frame_global']
    old = _frames.get(name)
    if old is not None:
        try:
            if old.winfo_exists():
                old.place_forget()
        except Exception:
            pass

    SX, SY = scale(window)
    frame = Frame(window, bg='white')
    frame.place(x=px(SX, 200), y=py(SY, 100), width=pw(SX, 1710), height=ph(SY, 700))

    Label(frame, text=spec['title'], font=(FONT_FAMILY, fs(SY, 16), 'bold'),
          bg=PRIMARY, fg='white').place(x=0, y=0, relwidth=1)

    def go_to_dashboard():
        frame.place_forget()
        if on_close:
            on_close()

    back_image = PhotoImage(file=resource_path('images/back.png'))
    back_button = Button(frame, image=back_image, bd=0, cursor='hand2', bg='white',
                         command=go_to_dashboard)
    back_button.image = back_image
    back_button.place(x=px(SX, 10), y=py(SY, 30))
    ToolTip(back_button, 'Back to dashboard')

    dashboard_button = Button(frame, text='Dashboard', font=(FONT_FAMILY, fs(SY, 12), 'bold'),
                              bd=0, cursor='hand2', bg='white', fg=PRIMARY,
                              activebackground='white', activeforeground=ACCENT,
                              command=go_to_dashboard)
    dashboard_button.place(x=px(SX, 60), y=py(SY, 32))
    ToolTip(dashboard_button, 'Return to the dashboard')

    top_frame = Frame(frame, bg='white')
    top_frame.place(x=0, y=py(SY, 60), relwidth=1, height=ph(SY, 380))

    search_frame = Frame(top_frame, bg='white')
    search_frame.pack()

    search_combobox = ttk.Combobox(search_frame, values=[label for label, _ in spec['search']],
                                   font=(FONT_FAMILY, fs(SY, 16)), state='readonly')
    search_combobox.set('Search By')
    search_combobox.grid(row=0, column=0, padx=px(SX, 20))

    search_entry = Entry(search_frame, font=(FONT_FAMILY, fs(SY, 16)), bg=FIELD_BG)
    search_entry.grid(row=0, column=1)

    def run_search():
        ops['search'](search_combobox.get(), search_entry.get())

    button(search_frame, 'Search', font_size=fs(SY, 12), command=run_search).grid(row=0, column=2, padx=px(SX, 20))
    search_entry.bind('<Return>', lambda e: run_search())

    def show_all():
        render_rows(treeview, spec, ops['rows']())

    button(search_frame, 'Show All', font_size=fs(SY, 12), command=show_all).grid(row=0, column=3)

    style = ttk.Style()
    style.theme_use('clam')
    style.configure('Treeview', background='white', foreground='black', rowheight=max(25, py(SY, 25)),
                    fieldbackground='white', bordercolor='gray', borderwidth=1, relief='solid')
    style.configure('Treeview.Heading', font=(FONT_FAMILY, fs(SY, 11), 'bold'), background='#f2f2f2',
                    bordercolor='#d0d0d0', borderwidth=1, relief='solid')
    style.map('Treeview', background=[('selected', '#cce5ff')])

    horizontal_scrollbar = Scrollbar(top_frame, orient=HORIZONTAL)
    vertical_scrollbar = Scrollbar(top_frame, orient=VERTICAL)

    treeview = ttk.Treeview(top_frame, columns=[column[0] for column in spec['columns']],
                            show='headings', yscrollcommand=vertical_scrollbar.set,
                            xscrollcommand=horizontal_scrollbar.set)
    horizontal_scrollbar.pack(side=BOTTOM, fill=X)
    vertical_scrollbar.pack(side=RIGHT, fill=Y, padx=(10, 0))
    horizontal_scrollbar.config(command=treeview.xview)
    vertical_scrollbar.config(command=treeview.yview)
    treeview.pack(pady=(10, 0), fill=X)

    for column_id, label, width in spec['columns']:
        treeview.heading(column_id, text=label)
        treeview.column(column_id, width=px(SX, width))

    spec['treeview'] = treeview

    def select_record(event):
        if not treeview.selection():
            return
        pk_value = treeview.item(treeview.selection()[0])['values'][0]
        for candidate in spec.get('_rows', []):
            if str(candidate.get(spec['pk'])) == str(pk_value):
                spec['selected'] = candidate.get(spec['pk'])
                break

    treeview.bind('<ButtonRelease-1>', select_record)
    treeview.bind('<Double-Button-1>', lambda e: do_update())

    def build_widgets(parent):
        widgets = {}
        for field in spec['fields']:
            key = field['key']
            kind = field['kind']
            row_index, col_index = field['pos']

            Label(parent, text=field['label'], font=(FONT_FAMILY, fs(SY, 16), 'bold'),
                  bg='white').grid(row=row_index, column=col_index,
                                   padx=px(SX, 20), pady=py(SY, 10),
                                   sticky='w' if kind == 'text' else '')

            if kind == 'entry':
                readonly = field.get('readonly') or field.get('auto')
                widget = Entry(parent, font=(FONT_FAMILY, fs(SY, 16), 'bold'), bg=FIELD_BG,
                               show='*' if field.get('mask') else '',
                               state='readonly' if readonly else 'normal')
            elif kind in ('combobox', 'source'):
                widget = ttk.Combobox(parent, font=(FONT_FAMILY, fs(SY, 16), 'bold'),
                                      width=field.get('width', 18), state='readonly')
            elif kind == 'date':
                widget = DateEntry(parent, width=18, font=(FONT_FAMILY, fs(SY, 16), 'bold'),
                                   state='readonly', date_pattern='yyyy-mm-dd', bg='white')
                widget._set_text('')
                if field.get('default_today'):
                    widget.set_date(datetime.now())
            elif kind == 'text':
                widget = Text(parent, width=field.get('width', 20),
                              height=field.get('height', 3), font=(FONT_FAMILY, fs(SY, 16), 'bold'),
                              bg=FIELD_BG)
            elif kind == 'label':
                widget = Label(parent, text=field.get('label_text', ''),
                               font=(FONT_FAMILY, fs(SY, 14), 'bold'), bg='white', fg=PRIMARY)
            else:
                continue

            widgets[key] = widget
            widget.grid(row=row_index, column=col_index + 1,
                        padx=px(SX, 20), pady=py(SY, 10),
                        rowspan=field.get('rowspan', 1), columnspan=field.get('colspan', 1),
                        sticky='w' if kind == 'text' else '')

            if kind == 'entry' and field.get('auto'):
                set_widget(widget, str(next_id(spec['table'], field['key'])))

            if kind in ('combobox', 'source'):
                if 'options' in field:
                    widget.config(values=field['options'])
                widget.set(field.get('placeholder', ''))
                if kind == 'combobox' and field.get('default'):
                    widget.set(field['default'])

        refresh_sources(spec, widgets)
        return widgets

    def open_dialog(mode):
        dialog = Toplevel(window)
        dialog.title(f"{spec['title']} - {'Add' if mode == 'add' else 'Update'}")
        dialog.configure(bg='white')
        dialog.resizable(False, False)
        dialog.transient(window)
        dialog.protocol('WM_DELETE_WINDOW', dialog.destroy)

        detail_frame = Frame(dialog, bg='white')
        detail_frame.pack(padx=px(SX, 20), pady=py(SY, 20))

        widgets = build_widgets(detail_frame)
        result = {'saved': False}

        def do_save():
            data = collect(spec, widgets)
            cleaned = validate_data(spec, data, mode)
            if cleaned is None:
                return
            ok = ops['add'](cleaned) if mode == 'add' else ops['update'](cleaned)
            if ok:
                result['saved'] = True
                dialog.destroy()

        if mode == 'update':
            pk_value = spec.get('selected')
            row = None
            for candidate in spec.get('_rows', []):
                if str(candidate.get(spec['pk'])) == str(pk_value):
                    row = candidate
                    break
            if row is None:
                dialog.destroy()
                return None
            populate(spec, widgets, row)

        button_frame = Frame(detail_frame, bg='white')
        button_frame.grid(row=99, column=0, columnspan=6, pady=py(SY, 10))

        save_button = button(button_frame, 'Save', font_size=fs(SY, 12), command=do_save)
        save_button.grid(row=0, column=0, padx=px(SX, 20))

        if mode == 'add':
            clear_button = button(button_frame, 'Clear', font_size=fs(SY, 12),
                                  command=lambda: clear_fields(spec, widgets))
            clear_button.grid(row=0, column=1, padx=px(SX, 20))
            cancel_column = 2
        else:
            cancel_column = 1

        cancel_button = button(button_frame, 'Cancel', font_size=fs(SY, 12), command=dialog.destroy)
        cancel_button.grid(row=0, column=cancel_column, padx=px(SX, 20))

        def bind_cancel(widget):
            widget.bind('<Escape>', lambda e: dialog.destroy())
            for child in widget.winfo_children():
                bind_cancel(child)

        bind_cancel(detail_frame)

        if spec.get('decorate'):
            spec['decorate'](detail_frame, widgets, mode)

        first = next((field for field in spec['fields']
                      if field['kind'] != 'label' and not field.get('auto')), None)
        if first:
            widgets[first['key']].focus_set()

        dialog.update_idletasks()
        x = window.winfo_rootx() + max((window.winfo_width() - dialog.winfo_reqwidth()) // 2, 0)
        y = window.winfo_rooty() + max((window.winfo_height() - dialog.winfo_reqheight()) // 2, 0)
        dialog.geometry(f'+{x}+{y}')
        dialog.grab_set()
        dialog.wait_window()
        return True if result['saved'] else None

    def do_add():
        if open_dialog('add'):
            messagebox.showinfo('Success', spec['msg_insert'])
            render_rows(treeview, spec, ops['rows']())

    def do_update():
        if spec.get('selected') is None:
            messagebox.showerror('Error', spec['no_selection_msg'])
            return
        if open_dialog('update'):
            messagebox.showinfo('Success', spec['msg_update'])
            render_rows(treeview, spec, ops['rows']())

    def do_delete():
        pk_value = spec.get('selected')
        if pk_value is None:
            messagebox.showerror('Error', spec['no_selection_msg'])
            return
        guard = spec.get('delete_guard')
        if guard:
            linked = query_one(f'SELECT COUNT(*) AS n FROM {guard[0]} WHERE {guard[1]} = ?',
                               (pk_value,))['n']
            if linked:
                messagebox.showerror('Error', spec.get(
                    'delete_guard_msg', 'Cannot delete: this record is referenced by other records'))
                return
        if not messagebox.askyesno('Confirm', spec['delete_confirm']):
            return
        if ops['delete'](pk_value):
            messagebox.showinfo('Success', spec['msg_delete'])
            spec['selected'] = None
            render_rows(treeview, spec, ops['rows']())

    action_frame = Frame(frame, bg='white')
    action_frame.place(x=px(SX, 400), y=py(SY, 560))

    column = 0
    add_button = button(action_frame, 'Add', font_size=fs(SY, 12), command=do_add)
    add_button.grid(row=0, column=column, padx=px(SX, 20))
    column += 1

    update_button = button(action_frame, 'Update', font_size=fs(SY, 12), command=do_update)
    update_button.grid(row=0, column=column, padx=px(SX, 20))
    column += 1

    delete_button = button(action_frame, 'Delete', font_size=fs(SY, 12), danger=True, command=do_delete)
    delete_button.grid(row=0, column=column, padx=px(SX, 20))
    column += 1

    export_button = button(action_frame, 'Export CSV', font_size=fs(SY, 12), command=ops['export_csv'])
    export_button.grid(row=0, column=column, padx=px(SX, 20))
    ToolTip(export_button, f'Export all {spec["title"].lower()} to a CSV file')
    column += 1

    for text, command, tooltip in ops.get('extra_buttons', []):
        extra_button = button(action_frame, text, font_size=fs(SY, 12), command=command)
        extra_button.grid(row=0, column=column, padx=px(SX, 20))
        if tooltip:
            ToolTip(extra_button, tooltip)
        column += 1

    render_rows(treeview, spec, ops['rows']())
    _frames[name] = frame
    return frame, treeview
