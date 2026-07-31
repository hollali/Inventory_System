import crud
from database import hash_password

EMPLOYEE_SPEC = {
    'table': 'employee_data',
    'pk': 'empid',
    'pk_label': 'Employee Id',
    'title': 'Employee Details',
    'frame_global': 'employee_frame',
    'table_columns': ['empid', 'name', 'email', 'number', 'dob', 'gender', 'salary',
                      'address', 'usertype', 'password'],
    'columns': [
        ('empid', 'Employee Id', 80), ('name', 'Name', 220), ('email', 'Email', 230),
        ('number', 'Phone Number', 150), ('dob', 'Date of Birth', 110), ('gender', 'Gender', 80),
        ('salary', 'Salary', 100), ('address', 'Address', 150), ('usertype', 'User Type', 110),
        ('password', 'Password', 90),
    ],
    'search': [('Id', 'empid'), ('Name', 'name'), ('Phone Number', 'number')],
    'unique_msg': 'Employee ID must be unique',
    'no_selection_msg': 'Please select an employee to delete',
    'delete_confirm': 'Are you sure you want to delete this employee?',
    'msg_insert': 'Data inserted successfully',
    'msg_update': 'Data updated successfully',
    'msg_delete': 'Data deleted successfully',
    'csv': ('employees.csv',
            ('Employee Id', 'Name', 'Email', 'Phone Number', 'Date of Birth', 'Gender',
             'Salary', 'Address', 'User Type'),
            ('empid', 'name', 'email', 'number', 'dob', 'gender', 'salary', 'address', 'usertype')),
    'fields': [
        {'key': 'empid', 'label': 'Employee Id', 'kind': 'entry', 'pos': (0, 0), 'required': True,
         'validate': 'positive_int', 'msg': 'Employee ID must be a whole number', 'store': 'int'},
        {'key': 'name', 'label': 'Name', 'kind': 'entry', 'pos': (0, 2), 'required': True},
        {'key': 'email', 'label': 'Email', 'kind': 'entry', 'pos': (0, 4), 'required': True,
         'validate': 'email', 'msg': 'Please enter a valid email address'},
        {'key': 'gender', 'label': 'Gender', 'kind': 'combobox', 'pos': (1, 0),
         'options': ['Male', 'Female'], 'placeholder': 'Select Gender', 'required': True,
         'msg': 'Please select a gender'},
        {'key': 'dob', 'label': 'Date of Birth', 'kind': 'date', 'pos': (1, 2),
         'required': True, 'store': 'date'},
        {'key': 'number', 'label': 'Phone Number', 'kind': 'entry', 'pos': (1, 4), 'required': True,
         'validate': 'phone', 'msg': 'Please enter a valid phone number'},
        {'key': 'salary', 'label': 'Salary', 'kind': 'entry', 'pos': (2, 0), 'required': True,
         'validate': 'number', 'msg': 'Salary must be a number', 'store': 'float', 'format': 'money'},
        {'key': 'address', 'label': 'Address', 'kind': 'text', 'pos': (2, 2), 'rowspan': 2,
         'required': True},
        {'key': 'usertype', 'label': 'User Type', 'kind': 'combobox', 'pos': (2, 4),
         'options': ['Admin', 'Employee'], 'placeholder': 'Employee Type', 'required': True,
         'msg': 'Please select a user type'},
        {'key': 'password', 'label': 'Password', 'kind': 'entry', 'pos': (3, 0),
         'required_add': True, 'mask': True},
    ],
}


def add_record(data):
    cleaned = crud.validate_data(EMPLOYEE_SPEC, data, 'add')
    if cleaned is None:
        return False
    cleaned['password'] = hash_password(cleaned['password'])
    return crud.insert_row(EMPLOYEE_SPEC, cleaned)


def update_record(data):
    cleaned = crud.validate_data(EMPLOYEE_SPEC, data, 'update')
    if cleaned is None:
        return False
    if 'password' in cleaned:
        cleaned['password'] = hash_password(cleaned['password'])
    return crud.update_row(EMPLOYEE_SPEC, cleaned)


def delete_record(empid):
    return crud.delete_row(EMPLOYEE_SPEC, empid)


def add_employee(empid, name, email, number, dob, gender, salary, address, usertype, password):
    return add_record({'empid': empid, 'name': name, 'email': email, 'number': number, 'dob': dob,
                       'gender': gender, 'salary': salary, 'address': address,
                       'usertype': usertype, 'password': password})


def update_employee(empid, name, email, number, dob, gender, salary, address, usertype, password):
    return update_record({'empid': empid, 'name': name, 'email': email, 'number': number,
                          'dob': dob, 'gender': gender, 'salary': salary, 'address': address,
                          'usertype': usertype, 'password': password})


def delete_employee(empid):
    return delete_record(empid)


def search_employee(option, search_value):
    return crud.search_and_render(EMPLOYEE_SPEC, option, search_value)


def get_count():
    return crud.count_rows(EMPLOYEE_SPEC)


def export_employee_csv():
    return crud.export_csv(EMPLOYEE_SPEC)


employee_treeview = None
employee_frame = None


def employee_form(window, on_close=None):
    global employee_treeview, employee_frame
    employee_frame, employee_treeview = crud.build_form(window, EMPLOYEE_SPEC, {
        'rows': lambda where=None, params=(): crud.fetch_rows(EMPLOYEE_SPEC, where, params),
        'add': add_record,
        'update': update_record,
        'delete': delete_record,
        'search': search_employee,
        'count': get_count,
        'export_csv': export_employee_csv,
    }, on_close=on_close)
    return employee_frame
