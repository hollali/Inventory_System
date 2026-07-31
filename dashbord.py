from tkinter import *
from tkinter import messagebox
from employee import employee_form
from suppliers import supplier_form
from categories import category_form
from products import product_form
from sales import sale_form
import employee
import suppliers
import categories
import products
import sales
import reports
import datetime
from layout import (setup_window, scale, px, py, pw, ph, fs, ToolTip, resource_path,
                    FONT_FAMILY, PRIMARY, PRIMARY_HOVER, ACCENT, ACCENT_HOVER,
                    CARD_EMPLOYEE, CARD_SUPPLIER, CARD_CATEGORY, CARD_PRODUCT, CARD_SALES)


def _quit(window):
    if messagebox.askyesno('Confirm', 'Are you sure you want to quit the application?'):
        window.destroy()


def build_dashboard(window, user):
    for widget in window.winfo_children():
        widget.destroy()

    from login import show_login

    is_admin = (user or {}).get('usertype') == 'Admin'

    bg_image = PhotoImage(file=resource_path('images/inventory1.png'))
    title_label = Label(window, image=bg_image, compound=LEFT,
                        text=' Inventory Management System',
                        font=(FONT_FAMILY, fs(1, 40), 'bold'), bg='#010c48', fg='white',
                        anchor='w', padx=20)
    title_label.image = bg_image
    title_label.place(x=0, y=0, relwidth=1)

    def logout():
        for widget in window.winfo_children():
            widget.destroy()
        show_login(window, lambda u: build_dashboard(window, u))

    logout_button = Button(window, text='Logout', font=(FONT_FAMILY, fs(1, 20), 'bold'),
                           fg='#010c48', bg='white', cursor='hand2', activebackground='#010c48',
                           activeforeground='white', bd=0, padx=20, command=logout)
    logout_button.place(x=px(1, 1720), y=py(1, 10))
    ToolTip(logout_button, 'Log out and return to the login screen')

    subtitle_label = Label(window, font=(FONT_FAMILY, fs(1, 15)), bg='#4d636d', fg='white')
    subtitle_label.place(x=0, y=py(1, 70), relwidth=1)

    user_name = (user or {}).get('name') or 'User'

    def update_datetime():
        try:
            now = datetime.datetime.now()
            subtitle_label.config(
                text=f'Welcome, {user_name}\t\t Date: {now.strftime("%d/%m/%Y")}'
                     f'\t\t Time: {now.strftime("%I:%M:%S %p")}')
        except Exception:
            return
        subtitle_label.after(1000, update_datetime)

    update_datetime()

    def menu_button(master, image, text, command, tooltip=None):
        button = Button(master, image=image, compound=LEFT, text=text,
                        font=(FONT_FAMILY, fs(1, 20), 'bold'), anchor='w', padx=10,
                        bd=0, bg='white', activebackground='#e0f2f1', activeforeground=ACCENT,
                        cursor='hand2', command=command)
        button.image = image
        button.pack(fill=X)
        if tooltip:
            ToolTip(button, tooltip)
        return button

    left_frame = Frame(window, bg='white')
    left_frame.place(x=0, y=py(1, 102), width=pw(1, 200), height=ph(1, 750))

    logo_image = PhotoImage(file=resource_path('images/logo.png'))
    image_label = Label(left_frame, image=logo_image)
    image_label.image = logo_image
    image_label.pack()

    menu_label = Label(left_frame, text='Menu', font=(FONT_FAMILY, fs(1, 20)), bg=ACCENT, fg='white')
    menu_label.pack(fill=X)

    icons = {
        'employee': PhotoImage(file=resource_path('images/employee (1).png')),
        'supplier': PhotoImage(file=resource_path('images/supplier.png')),
        'category': PhotoImage(file=resource_path('images/category.png')),
        'product': PhotoImage(file=resource_path('images/product.png')),
        'sales': PhotoImage(file=resource_path('images/sales.png')),
        'reports': PhotoImage(file=resource_path('images/bill_logo.png')),
        'exit': PhotoImage(file=resource_path('images/exit.png')),
    }

    if is_admin:
        menu_button(left_frame, icons['employee'], 'Employees',
                    lambda: employee_form(window, on_close=update_counts), 'Manage employees')
        menu_button(left_frame, icons['supplier'], 'Suppliers',
                    lambda: supplier_form(window, on_close=update_counts), 'Manage suppliers')
        menu_button(left_frame, icons['category'], 'Categories',
                    lambda: category_form(window, on_close=update_counts), 'Manage categories')
        menu_button(left_frame, icons['product'], 'Products',
                    lambda: product_form(window, on_close=update_counts), 'Manage products')
    menu_button(left_frame, icons['sales'], 'Sales',
                lambda: sale_form(window, on_close=update_counts), 'Record sales')
    menu_button(left_frame, icons['reports'], 'Reports',
                lambda: reports.show_reports_hub(window), 'Low stock and sales reports')
    menu_button(left_frame, icons['exit'], 'Exit', lambda: _quit(window), 'Quit the application')

    def stat_card(x, y, color, icon, title):
        frame = Frame(window, bg=color, bd=3, relief=RIDGE)
        frame.place(x=px(1, x), y=py(1, y), height=ph(1, 170), width=pw(1, 280))
        icon_label = Label(frame, image=icon, bg=color)
        icon_label.image = icon
        icon_label.pack(pady=py(1, 10))
        Label(frame, text=title, bg=color, fg='white', font=(FONT_FAMILY, fs(1, 15), 'bold')).pack()
        count_label = Label(frame, text='0', bg=color, fg='white', font=(FONT_FAMILY, fs(1, 30), 'bold'))
        count_label.pack()
        return count_label

    total_emp_icon = PhotoImage(file=resource_path('images/total_emp.png'))
    total_emp_count_label = stat_card(400, 125, CARD_EMPLOYEE, total_emp_icon, 'Total Employees')

    total_sup_icon = PhotoImage(file=resource_path('images/total_sup.png'))
    total_sup_count_label = stat_card(800, 125, CARD_SUPPLIER, total_sup_icon, 'Total Suppliers')

    total_cat_icon = PhotoImage(file=resource_path('images/total_cat.png'))
    total_cat_count_label = stat_card(400, 350, CARD_CATEGORY, total_cat_icon, 'Total Categories')

    total_products_icon = PhotoImage(file=resource_path('images/total_prod.png'))
    total_products_count_label = stat_card(800, 350, CARD_PRODUCT, total_products_icon, 'Total Products')

    total_sales_icon = PhotoImage(file=resource_path('images/total_sales.png'))
    total_sales_count_label = stat_card(1200, 125, CARD_SALES, total_sales_icon, 'Total Sales')

    total_lowstock_icon = PhotoImage(file=resource_path('images/total_prod.png'))
    low_stock_count_label = stat_card(1200, 350, '#e67e22', total_lowstock_icon, 'Low Stock Items')

    def update_counts():
        try:
            total_emp_count_label.config(text=employee.get_count())
            total_sup_count_label.config(text=suppliers.get_count())
            total_cat_count_label.config(text=categories.get_count())
            total_products_count_label.config(text=products.get_count())
            total_sales_count_label.config(text=sales.get_count())
            low_stock_count_label.config(text=reports.low_stock_count())
        except Exception:
            pass

    update_counts()


def main():
    window = Tk()
    setup_window(window, 'Inventory System Dashboard')

    icon_image = PhotoImage(file=resource_path('images/icon.png'))
    window.iconphoto(True, icon_image)
    window.icon_image = icon_image

    from login import show_login
    show_login(window, lambda user: build_dashboard(window, user))
    window.mainloop()


if __name__ == '__main__':
    main()
