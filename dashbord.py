from tkinter import *


window=Tk()
window.title("Dashboard")
window.geometry('1270x668+0+0')
window.resizable(0,0)
window.config(bg='white')

bg_image=PhotoImage(file='./images/inventory1.png')
titleLabel=Label(window,image=bg_image,compound=LEFT,text=" Inventory Managment System",font=('times new roman',40,'bold'),bg='#010c48',fg='white',anchor='w',padx=20)
titleLabel.place(x=0,y=0,relwidth=1)

logoutButton=Button(window,text='Logout',font=('times new roman',20,'bold'),fg='#010c48',bg='white')
logoutButton.place(x=1100,y=10)

subtitleLabel=Label(window,text='Welcome, Admin\t\t Date: 16/08/2024\t\t Time: 12:36:17 pm',font=('times new roman',15),bg='#4d636d')
subtitleLabel.place(x=0,y=70,relwidth=1)

leftFrame=Frame(window)
leftFrame.place(x=0,y=102,width=200,height=550)

logoImage=PhotoImage(file='./images/logo.png')
imageLabel=Label(leftFrame,image=logoImage)
imageLabel.pack()

menuLabel=Label(leftFrame,text='Menu',font=('times new roman',20,),bg='#009688')
menuLabel.pack(fill=X)

employee_icon=PhotoImage(file='./images/employee (1).png')
employee_button=Button(leftFrame,image=employee_icon,compound=LEFT,text='Employees',font=('times new roman',20,'bold'),anchor='w')
employee_button.pack(fill=X)

supplier_icon=PhotoImage(file='./images/supplier.png')
supplier_button=Button(leftFrame,image=supplier_icon,compound=LEFT,text='Suppliers',font=('times new roman',20,'bold'),anchor='w')
supplier_button.pack(fill=X)

category_icon=PhotoImage(file='./images/category.png')
category_button=Button(leftFrame,image=category_icon,compound=LEFT,text='Categories',font=('times new roman',20,'bold'),anchor='w')
category_button.pack(fill=X)

products_icon=PhotoImage(file='./images/product.png')
products_button=Button(leftFrame,image=products_icon,compound=LEFT,text='Products',font=('times new roman',20,'bold'),anchor='w')
products_button.pack(fill=X)

sales_icon=PhotoImage(file='./images/sales.png')
sales_button=Button(leftFrame,image=sales_icon,compound=LEFT,text='Sales',font=('times new roman',20,'bold'),anchor='w')
sales_button.pack(fill=X)

exit_icon=PhotoImage(file='./images/exit.png')
exit_button=Button(leftFrame,image=exit_icon,compound=LEFT,text='Exit',font=('times new roman',20,'bold'),anchor='w')
exit_button.pack(fill=X)

window.mainloop()
