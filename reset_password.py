#!/usr/bin/env python3
"""Reset an employee's password from the command line.

Usage:
    python3 reset_password.py <employee_id> [new_password]

If the new password is omitted, you will be prompted for it.
"""

import getpass
import sys

from database import commit, execute, hash_password, query_one


def main():
    args = sys.argv[1:]
    if not args:
        print('Usage: python3 reset_password.py <employee_id> [new_password]')
        sys.exit(1)

    try:
        employee_id = int(args[0])
    except ValueError:
        print('Error: employee id must be a whole number')
        sys.exit(1)

    password = args[1] if len(args) > 1 else getpass.getpass('New password: ')
    if len(args) <= 1:
        confirm = getpass.getpass('Confirm password: ')
        if password != confirm:
            print('Error: passwords do not match')
            sys.exit(1)

    if not password:
        print('Error: password cannot be empty')
        sys.exit(1)

    row = query_one('SELECT empid, name FROM employee_data WHERE empid = ?', (employee_id,))
    if not row:
        print(f'Error: no employee found with id {employee_id}')
        sys.exit(1)

    execute('UPDATE employee_data SET password = ? WHERE empid = ?',
            (hash_password(password), employee_id))
    commit()
    print(f'Password updated for {row["name"]} (id {employee_id})')


if __name__ == '__main__':
    main()
