import tkinter as tk
import tkinter.messagebox as tkmb

import testbase

import login
import dashboard

tkmb.showerror = lambda t, m: print('ERR:', m)
tkmb.showinfo = lambda t, m: print('INFO:', m)
tkmb.askyesno = lambda t, m: True


def walk(w, acc):
    acc.append(w)
    for c in w.winfo_children():
        walk(c, acc)
    return acc


def find(win, cls, text=None):
    return [w for w in walk(win, []) if w.winfo_class() == cls
            and (text is None or str(w.cget('text')) == text)]


root = tk.Tk()
root.geometry('+99999+99999')
root.update()

result = {}


def on_success(user):
    result['user'] = user
    dashboard.build_dashboard(root, user)
    result['built'] = True


login.show_login(root, on_success)
root.update()

entries = find(root, 'Entry')
emp_entry, pw_entry = entries[0], entries[1]
login_button = find(root, 'Button', 'Login')[0]

emp_entry.insert(0, '1')
pw_entry.insert(0, 'wrong')
login_button.invoke()
root.update()
assert 'user' not in result, 'login should have failed'
print('login rejects wrong password -> OK')

pw_entry.delete(0, 'end')
pw_entry.insert(0, 'admin123')
login_button.invoke()
root.update()
assert result.get('user') == {'empid': 1, 'name': 'Hollali Kelvin', 'usertype': 'Admin'}, result
assert result.get('built')
print('login accepts correct password -> OK')

menu_admin = [str(w.cget('text')) for w in find(root, 'Button')]
for expected in ('Employees', 'Suppliers', 'Categories', 'Products', 'Sales', 'Reports', 'Logout'):
    assert expected in menu_admin, menu_admin
print('admin sees all menus -> OK')

dashboard.build_dashboard(root, {'empid': 2, 'name': 'Ama Addai', 'usertype': 'Employee'})
root.update()
menu_emp = [str(w.cget('text')) for w in find(root, 'Button')]
assert 'Sales' in menu_emp, menu_emp
assert 'Logout' in menu_emp, menu_emp
for hidden in ('Employees', 'Suppliers', 'Categories', 'Products'):
    assert hidden not in menu_emp, menu_emp
print('employee sees only Sales -> OK')

for _ in range(login.FAIL_LIMIT):
    assert login.authenticate('2', 'wrong') is None
assert login.lockout_remaining('2') > 0, 'account should be locked'
assert login.authenticate('2', 'wrong') is None, 'locked account must reject even correct-looking attempts'
print('lockout after repeated failures -> OK')

print('ALL LOGIN TESTS PASSED')
root.destroy()
