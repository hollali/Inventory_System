from tkinter import *
from employee import employee_form


#*GUI PORT
window=Tk()

window.title("Dashboard")
window.geometry('1670x850+0+0')
window.resizable(0,0)
window.config(bg='white')

bg_image=PhotoImage(file='./images/inventory1.png')
titleLabel=Label(window,image=bg_image,compound=LEFT,text=" Inventory Management System",font=('times new roman',40,'bold'),bg='#010c48',fg='white',anchor='w',padx=20)
titleLabel.place(x=0,y=0,relwidth=1)

logoutButton=Button(window,text='Logout',font=('times new roman',20,'bold'),fg='#010c48',bg='white')
logoutButton.place(x=1420,y=10)

subtitleLabel=Label(window,text='Welcome, Admin\t\t Date: 16/08/2024\t\t Time: 12:36:17 pm',font=('times new roman',15),bg='#4d636d')
subtitleLabel.place(x=0,y=70,relwidth=1)

leftFrame=Frame(window,bg='white')
leftFrame.place(x=0,y=102,width=200,height=650)

logoImage=PhotoImage(file='./images/logo.png')
imageLabel=Label(leftFrame,image=logoImage)
imageLabel.pack()

menuLabel=Label(leftFrame,text='Menu',font=('times new roman',20,),bg='#009688')
menuLabel.pack(fill=X)

employee_icon=PhotoImage(file='./images/employee (1).png')
employee_button=Button(leftFrame,image=employee_icon,compound=LEFT,text='Employees',font=('times new roman',20,'bold'),anchor='w',padx=10,command=lambda:employee_form(window))
employee_button.pack(fill=X)

supplier_icon=PhotoImage(file='./images/supplier.png')
supplier_button=Button(leftFrame,image=supplier_icon,compound=LEFT,text='Suppliers',font=('times new roman',20,'bold'),anchor='w',padx=10)
supplier_button.pack(fill=X)

category_icon=PhotoImage(file='./images/category.png')
category_button=Button(leftFrame,image=category_icon,compound=LEFT,text='Categories',font=('times new roman',20,'bold'),anchor='w',padx=10)
category_button.pack(fill=X)

products_icon=PhotoImage(file='./images/product.png')
products_button=Button(leftFrame,image=products_icon,compound=LEFT,text='Products',font=('times new roman',20,'bold'),anchor='w',padx=10)
products_button.pack(fill=X)

sales_icon=PhotoImage(file='./images/sales.png')
sales_button=Button(leftFrame,image=sales_icon,compound=LEFT,text='Sales',font=('times new roman',20,'bold'),anchor='w',padx=10)
sales_button.pack(fill=X)

exit_icon=PhotoImage(file='./images/exit.png')
exit_button=Button(leftFrame,image=exit_icon,compound=LEFT,text='Exit',font=('times new roman',20,'bold'),anchor='w',padx=10)
exit_button.pack(fill=X)

emp_frame=Frame(window,bg='#2C3E50',bd=3,relief=RIDGE)
emp_frame.place(x=400,y=125,height=170,width=280)
total_emp_icon=PhotoImage(file='./images/total_emp.png')
total_emp_icon_label=Label(emp_frame,image=total_emp_icon,bg='#2C3E50')
total_emp_icon_label.pack(pady=10)

total_emp_label=Label(emp_frame,text='Total Employees',bg='#2C3E50',fg='white',font=('times new roman',15,'bold'))
total_emp_label.pack()

total_emp_count_label=Label(emp_frame,text='0',bg='#2C3E50',fg='white',font=('times new roman',30,'bold'))
total_emp_count_label.pack()

sup_frame=Frame(window,bg='#8E44AD',bd=3,relief=RIDGE)
sup_frame.place(x=800,y=125,height=170,width=280)
total_sup_icon=PhotoImage(file='./images/total_sup.png')
total_sup_icon_label=Label(sup_frame,image=total_sup_icon,bg='#8E44AD')
total_sup_icon_label.pack(pady=10)

total_sup_label=Label(sup_frame,text='Total Suppliers',bg='#8E44AD',fg='white',font=('times new roman',15,'bold'))
total_sup_label.pack()

total_sup_count_label=Label(sup_frame,text='0',bg='#8E44Ad',fg='white',font=('times new roman',30,'bold'))
total_sup_count_label.pack()

cat_frame=Frame(window,bg='#27AE68',bd=3,relief=RIDGE)
cat_frame.place(x=400,y=350,height=170,width=280)
total_cat_icon=PhotoImage(file='./images/total_cat.png')
total_cat_icon_label=Label(cat_frame,image=total_cat_icon,bg='#27AE68')
total_cat_icon_label.pack(pady=10)

total_cat_label=Label(cat_frame,text='Total Categories',bg='#27AE68',fg='white',font=('times new roman',15,'bold'))
total_cat_label.pack()

total_cat_count_label=Label(cat_frame,text='0',bg='#27AE68',fg='white',font=('times new roman',30,'bold'))
total_cat_count_label.pack()

products_frame=Frame(window,bg='#28E',bd=3,relief=RIDGE)
products_frame.place(x=800,y=350,height=170,width=280)
total_products_icon=PhotoImage(file='./images/total_prod.png')
total_products_icon_label=Label(products_frame,image=total_products_icon,bg='#28E')
total_products_icon_label.pack(pady=10)

total_products_label=Label(products_frame,text='Total Products',bg='#28E',fg='white',font=('times new roman',15,'bold'))
total_products_label.pack()

total_products_count_label=Label(products_frame,text='0',bg='#28E',fg='white',font=('times new roman',30,'bold'))
total_products_count_label.pack()

sales_frame=Frame(window,bg='#8E444D',bd=3,relief=RIDGE)
sales_frame.place(x=1200,y=125,height=170,width=280)
total_sales_icon=PhotoImage(file='./images/total_sales.png')
total_sales_icon_label=Label(sales_frame,image=total_sales_icon,bg='#8E444D')
total_sales_icon_label.pack(pady=10)

total_sales_label=Label(sales_frame,text='Total Sales',bg='#8E444D',fg='white',font=('times new roman',15,'bold'))
total_sales_label.pack()

total_sales_count_label=Label(sales_frame,text='0',bg='#8E444D',fg='white',font=('times new roman',30,'bold'))
total_sales_count_label.pack()


window.mainloop()
