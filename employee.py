from tkinter import *
from tkinter import ttk
from tkcalendar import DateEntry
from datetime import date
from tkinter import messagebox
import sqlite3

# Function to connect to SQLite database
def connect_database():
    try:
        connection = sqlite3.connect('inventory_system.db')
        cursor = connection.cursor()
    except:
        messagebox.showerror('Error', 'Connection Failed')
        return None, None

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employee_data (
            empid INTEGER PRIMARY KEY,
            name TEXT,
            gender TEXT,
            email TEXT,
            number TEXT,
            dob TEXT,
            salary TEXT,
            address TEXT,
            usertype TEXT,
            password TEXT
        )
    ''')
    connection.commit()
    return cursor, connection

# Load data into Treeview with masked passwords
def treeview_data():
    cursor, connection = connect_database()
    if not cursor or not connection:
        return

    cursor.execute('SELECT * FROM employee_data')
    employee_records = cursor.fetchall()
    employee_treeview.delete(*employee_treeview.get_children())

    for record in employee_records:
        masked_record = list(record)
        masked_record[9] = '•' * len(masked_record[9])  # Mask password
        employee_treeview.insert('', END, values=masked_record)

# Add new employee
def add_employee(empid, name, gender, email, number, dob, salary, address, usertype, password):
    if (empid == '' or name == '' or gender == 'Select Gender' or email == '' or number == '' or dob == ''
            or salary == '' or address == '\n' or usertype == 'Employee Type' or password == ''):
        messagebox.showerror('Error', 'All fields are required')
    else:
        cursor, connection = connect_database()
        if not cursor or not connection:
            return
        try:
            cursor.execute('''
                INSERT INTO employee_data 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (empid, name, gender, email, number, dob, salary, address, usertype, password))
            connection.commit()
            treeview_data()
            messagebox.showinfo('Success', 'Data inserted successfully')
        except sqlite3.IntegrityError:
            messagebox.showerror('Error', 'Employee ID must be unique')

# Clear input fields
def clear_fields(empid_entry, name_entry, gender_combobox, email_entry, number_entry, dob_date_entry,
                salary_entry, address_text, usertype_combobox, password_entry):
    empid_entry.delete(0, END)
    name_entry.delete(0, END)
    gender_combobox.set('Select Gender')
    email_entry.delete(0, END)
    number_entry.delete(0, END)
    dob_date_entry.delete(0, END)
    salary_entry.delete(0, END)
    address_text.delete(1.0, END)
    usertype_combobox.set('Employee Type')
    password_entry.delete(0, END)

# Main employee form
def employee_form(window):
    global back_image, employee_treeview

    employee_frame = Frame(window, width=1470, height=567, bg='white')
    employee_frame.place(x=200, y=100)

    heading_label = Label(employee_frame, text='Employee Details', font=('times new roman', 16, 'bold'), bg='#0f4d7d', fg='white')
    heading_label.place(x=0, y=0, relwidth=1)

    back_image = PhotoImage(file='./images/back.png')
    back_button = Button(employee_frame, image=back_image, bd=0, cursor='hand2', bg='white', command=lambda: employee_frame.place_forget())
    back_button.place(x=10, y=30)

    top_frame = Frame(employee_frame, bg='white')
    top_frame.place(x=0, y=60, relwidth=1, height=235)

    search_frame = Frame(top_frame, bg='white')
    search_frame.pack()

    search_combobox = ttk.Combobox(search_frame, values=('Id', 'Name', 'Phone Number'), font=('times new roman', 16), state='readonly')
    search_combobox.set('Sort By')
    search_combobox.grid(row=0, column=0, padx=20)

    search_entry = Entry(search_frame, font=('times new roman', 16), bg='lightyellow')
    search_entry.grid(row=0, column=1)

    search_button = Button(search_frame, text='Search', font=('times new roman', 12), width=10, cursor='hand2', fg='white', bg='#0f4d7d')
    search_button.grid(row=0, column=2, padx=20)

    show_button = Button(search_frame, text='Show All', font=('times new roman', 12), width=10, cursor='hand2', fg='white', bg='#0f4d7d', command=treeview_data)
    show_button.grid(row=0, column=3)

    horizontal_scrollbar = Scrollbar(top_frame, orient=HORIZONTAL)
    vertical_scrollbar = Scrollbar(top_frame, orient=VERTICAL)

    employee_treeview = ttk.Treeview(top_frame, columns=('empid', 'name', 'email', 'number', 'dob', 'gender', 'salary', 'address', 'usertype', 'password'), show='headings', yscrollcommand=vertical_scrollbar.set, xscrollcommand=horizontal_scrollbar.set)
    horizontal_scrollbar.pack(side=BOTTOM, fill=X)
    vertical_scrollbar.pack(side=RIGHT, fill=Y, padx=(10, 0))
    horizontal_scrollbar.config(command=employee_treeview.xview)
    vertical_scrollbar.config(command=employee_treeview.yview)
    employee_treeview.pack(pady=(10, 0))

    headings = ['Employee Id', 'Name', 'Email', 'Phone Number', 'Date of Birth', 'Gender', 'Salary', 'Address', 'User Type', 'Password']
    for col, head in zip(employee_treeview['columns'], headings):
        employee_treeview.heading(col, text=head)

    column_widths = [120, 240, 260, 200, 140, 140, 160, 180, 140, 140]
    for col, width in zip(employee_treeview['columns'], column_widths):
        employee_treeview.column(col, width=width)

    treeview_data()

    detail_frame = Frame(employee_frame, bg='white')
    detail_frame.place(x=50, y=300)

    empid_entry = Entry(detail_frame, font=('times new roman', 16, 'bold'), bg='lightyellow')
    name_entry = Entry(detail_frame, font=('times new roman', 16, 'bold'), bg='lightyellow')
    email_entry = Entry(detail_frame, font=('times new roman', 16, 'bold'), bg='lightyellow')
    gender_combobox = ttk.Combobox(detail_frame, values=('Male', 'Female'), font=('times new roman', 16, 'bold'), width=18, state='readonly')
    gender_combobox.set('Select Gender')
    dob_date_entry = DateEntry(detail_frame, width=18, font=('times new roman', 16, 'bold'), state='readonly', date_pattern='dd/mm/yyyy', bg='white')
    number_entry = Entry(detail_frame, font=('times new roman', 16, 'bold'), bg='lightyellow')
    salary_entry = Entry(detail_frame, font=('times new roman', 16, 'bold'), bg='lightyellow')
    address_text = Text(detail_frame, width=20, height=3, font=('times new roman', 16, 'bold'), bg='lightyellow')
    usertype_combobox = ttk.Combobox(detail_frame, values=('Admin', 'Employee'), font=('times new roman', 16, 'bold'), width=18, state='readonly')
    usertype_combobox.set('Employee Type')
    password_entry = Entry(detail_frame, font=('times new roman', 16, 'bold'), bg='lightyellow', show='*')

    labels = ['Employee Id', 'Name', 'Email', 'Gender', 'Date of Birth', 'Phone Number', 'Salary', 'Address', 'User type', 'Password']
    entries = [empid_entry, name_entry, email_entry, gender_combobox, dob_date_entry, number_entry,
            salary_entry, address_text, usertype_combobox, password_entry]
    positions = [(0, 0), (0, 2), (0, 4), (1, 0), (1, 2), (1, 4), (2, 0), (2, 2), (2, 4), (3, 0)]

    for label, pos in zip(labels, positions):
        Label(detail_frame, text=label, font=('times new roman', 16, 'bold'), bg='white').grid(row=pos[0], column=pos[1], padx=20, pady=10, sticky='w')

    entry_positions = [(0, 1), (0, 3), (0, 5), (1, 1), (1, 3), (1, 5), (2, 1), (2, 3), (2, 5), (3, 1)]
    for entry, pos in zip(entries, entry_positions):
        entry.grid(row=pos[0], column=pos[1], padx=20, pady=10)

    button_frame = Frame(employee_frame, bg='white')
    button_frame.place(x=400, y=530)

    Button(button_frame, text='Add', font=('times new roman', 12), width=10, cursor='hand2', fg='white', bg='#0f4d7d',
        command=lambda: add_employee(empid_entry.get(), name_entry.get(), gender_combobox.get(),
                                        email_entry.get(), number_entry.get(), dob_date_entry.get(),
                                        salary_entry.get(), address_text.get(1.0, END), usertype_combobox.get(),
                                        password_entry.get())).grid(row=0, column=0, padx=20)

    Button(button_frame, text='Update', font=('times new roman', 12), width=10, cursor='hand2', fg='white', bg='#0f4d7d').grid(row=0, column=1, padx=20)
    Button(button_frame, text='Delete', font=('times new roman', 12), width=10, cursor='hand2', fg='white', bg='#0f4d7d').grid(row=0, column=2, padx=20)
    Button(button_frame, text='Clear', font=('times new roman', 12), width=10, cursor='hand2', fg='white', bg='#0f4d7d',
        command=lambda: clear_fields(empid_entry, name_entry, gender_combobox, email_entry, number_entry,
                                        dob_date_entry, salary_entry, address_text, usertype_combobox,
                                        password_entry)).grid(row=0, column=3, padx=20)