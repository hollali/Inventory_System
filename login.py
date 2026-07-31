from tkinter import *
from tkinter import messagebox

from database import query_one, verify_password
from layout import (FONT_FAMILY, PRIMARY, PRIMARY_DARK, ACCENT, ACCENT_HOVER,
                    DANGER, DANGER_HOVER, FIELD_BG, fs, px, py, resource_path)


def authenticate(employee_id, password):
    employee_id = str(employee_id or '').strip()
    if not employee_id or not password:
        return None
    row = query_one(
        'SELECT empid, name, usertype, password FROM employee_data WHERE empid = ?',
        (employee_id,))
    if not row:
        return None
    if not verify_password(password, row['password']):
        return None
    return {'empid': row['empid'], 'name': row['name'], 'usertype': row['usertype']}


def show_login(window, on_success):
    login_frame = Frame(window, bg=PRIMARY_DARK)
    login_frame.place(x=0, y=0, relwidth=1, relheight=1)

    card = Frame(login_frame, bg='white', bd=3, relief=RIDGE)
    card.place(relx=0.5, rely=0.5, anchor=CENTER)

    logo = PhotoImage(file=resource_path('images/logo.png'))
    logo_label = Label(card, image=logo, bg='white')
    logo_label.image = logo
    logo_label.pack(pady=(py(1, 30), py(1, 10)))

    Label(card, text='Inventory Management System', font=(FONT_FAMILY, fs(1, 22), 'bold'),
          bg='white', fg=PRIMARY).pack()

    Label(card, text='Sign in to continue', font=(FONT_FAMILY, fs(1, 14)),
          bg='white', fg='#666666').pack(pady=(py(1, 4), py(1, 20)))

    Label(card, text='Employee ID', font=(FONT_FAMILY, fs(1, 14), 'bold'), bg='white',
          fg='#333333').pack(anchor='w', padx=px(1, 40))

    empid_entry = Entry(card, font=(FONT_FAMILY, fs(1, 14)), bg=FIELD_BG)
    empid_entry.pack(fill=X, padx=px(1, 40), pady=py(1, 6), ipady=py(1, 4))

    Label(card, text='Password', font=(FONT_FAMILY, fs(1, 14), 'bold'), bg='white',
          fg='#333333').pack(anchor='w', padx=px(1, 40), pady=(py(1, 12), 0))

    password_entry = Entry(card, font=(FONT_FAMILY, fs(1, 14)), show='*', bg=FIELD_BG)
    password_entry.pack(fill=X, padx=px(1, 40), pady=py(1, 6), ipady=py(1, 4))

    def do_login(event=None):
        employee_id = empid_entry.get()
        password = password_entry.get()
        if not employee_id.strip() or not password:
            messagebox.showerror('Error', 'Please enter your Employee ID and password')
            return
        user = authenticate(employee_id, password)
        if user is None:
            messagebox.showerror('Login Failed', 'Invalid Employee ID or password')
            password_entry.delete(0, END)
            return
        login_frame.destroy()
        on_success(user)

    login_button = Button(card, text='Login', font=(FONT_FAMILY, fs(1, 15), 'bold'),
                          bg=ACCENT, fg='white', activebackground=ACCENT_HOVER,
                          activeforeground='white', cursor='hand2', relief=FLAT,
                          padx=px(1, 60), pady=py(1, 6), command=do_login)
    login_button.pack(pady=py(1, 20))

    quit_button = Button(card, text='Quit', font=(FONT_FAMILY, fs(1, 13), 'bold'),
                         bg=DANGER, fg='white', activebackground=DANGER_HOVER,
                         activeforeground='white', cursor='hand2', relief=FLAT,
                         padx=px(1, 60), pady=py(1, 4),
                         command=window.destroy)
    quit_button.pack(pady=(0, py(1, 24)))

    password_entry.bind('<Return>', do_login)
    empid_entry.bind('<Return>', lambda e: password_entry.focus_set())
    empid_entry.focus_set()

    return login_frame
