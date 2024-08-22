from tkinter import *
from tkinter import ttk
from tkcalendar import DateEntry


#!Function Port
def employee_form():
    global back_image
    employee_frame=Frame(window,width=1470,height=567,bg='white')
    employee_frame.place(x=200,y=100)

    heading_label=Label(employee_frame,text='Employee Details',font=('times new roman',16,'bold'),bg='#0f4d7d',fg='white')
    heading_label.place(x=0,y=0,relwidth=1)

    back_image=PhotoImage(file='./images/back.png')
    back_button=Button(employee_frame,image=back_image,bd=0,cursor='hand2',bg='white',command=lambda: employee_frame.place_forget())
    back_button.place(x=10,y=30)

    top_frame=Frame(employee_frame,bg='white')
    top_frame.place(x=0,y=60,relwidth=1,height=235)

    search_frame=Frame(top_frame,bg='white')
    search_frame.pack()

    search_combobox=ttk.Combobox(search_frame,values=('Id','Name','Phone Number'),font=('times new roman',16),state='readonly',)
    search_combobox.set('Sort By')
    search_combobox.grid(row=0,column=0,padx=20)

    search_entry=Entry(search_frame,font=('times new roman',16),bg='lightyellow')
    search_entry.grid(row=0,column=1) 

    search_button=Button(search_frame,text='Search',font=('times new roman',12),width=10,cursor='hand2',fg='white',bg='#0f4d7d')
    search_button.grid(row=0,column=2,padx=20)

    show_button=Button(search_frame,text='Show All',font=('times new roman',12),width=10,cursor='hand2',fg='white',bg='#0f4d7d')
    show_button.grid(row=0,column=3)

    horizontal_scrollbar=Scrollbar(top_frame,orient=HORIZONTAL)
    vertical_scrollbar=Scrollbar(top_frame,orient=VERTICAL)

    employee_treeview=ttk.Treeview(top_frame,columns=('id','name','gender','email','number','Dob','salary','address','usertype','password'),show='headings',yscrollcommand=vertical_scrollbar.set,xscrollcommand=horizontal_scrollbar.set)
    horizontal_scrollbar.pack(side=BOTTOM,fill=X)
    vertical_scrollbar.pack(side=RIGHT,fill=Y,padx=(10,0))
    horizontal_scrollbar.config(command=employee_treeview.xview)
    vertical_scrollbar.config(command=employee_treeview.yview)
    employee_treeview.pack(pady=(10,0))

    employee_treeview.heading('id',text='EmpId')
    employee_treeview.heading('name',text='Name')
    employee_treeview.heading('gender',text='Gender')
    employee_treeview.heading('email',text='Email')
    employee_treeview.heading('number',text='Phone Number')
    employee_treeview.heading('Dob',text='Dob')
    employee_treeview.heading('salary',text='Salary')
    employee_treeview.heading('address',text='Address')
    employee_treeview.heading('usertype',text='User Type')
    employee_treeview.heading('password',text='Password')

    employee_treeview.column('id',width=120)
    employee_treeview.column('name',width=240)
    employee_treeview.column('gender',width=140)
    employee_treeview.column('email',width=260) 
    employee_treeview.column('salary',width=160)
    employee_treeview.column('number',width=200)
    employee_treeview.column('Dob',width=140)
    employee_treeview.column('address',width=180)
    employee_treeview.column('usertype',width=140)
    employee_treeview.column('password',width=140)

    detail_frame=Frame(employee_frame,bg='white')
    detail_frame.place(x=50,y=300)

    empid_label=Label(detail_frame,text="Id",font=('times new roman',16,'bold'),bg='white')
    empid_label.grid(row=0,column=0,padx=20,pady=10)
    empid_entry=Entry(detail_frame,font=('times new roman',16,'bold'),bg='lightyellow')
    empid_entry.grid(row=0,column=1,padx=20,pady=10)

    name_label=Label(detail_frame,text="Name",font=('times new roman',16,'bold'),bg='white')
    name_label.grid(row=0,column=2,padx=20,pady=10)
    name_entry=Entry(detail_frame,font=('times new roman',16,'bold'),bg='lightyellow')
    name_entry.grid(row=0,column=3,padx=20,pady=10)

    email_label=Label(detail_frame,text="Email",font=('times new roman',16,'bold'),bg='white')
    email_label.grid(row=0,column=4,padx=20,pady=10)
    email_entry=Entry(detail_frame,font=('times new roman',16,'bold'),bg='lightyellow')
    email_entry.grid(row=0,column=5,padx=20,pady=10) 

    gender_label=Label(detail_frame,text="Gender",font=('times new roman',16,'bold'),bg='white')
    gender_label.grid(row=1,column=0,padx=20,pady=10)
    gender_combobox=ttk.Combobox(detail_frame,values=('Male','Female'),font=('times new roman',16,'bold'),width=18,state='readonly')
    gender_combobox.set('Select Gender')
    gender_combobox.grid(row=1,column=1)

    dob_label = Label(detail_frame,text='Date of Birth',font=('times new roman',16,'bold'),bg='white')
    dob_label.grid(row=1,column=2,padx=20,pady=10)
    dob_date_entry=DateEntry(detail_frame,width=18,font=('times new roman',16,'bold'),state='readonly',date_pattern='dd/mm/yyyy',bg='white')
    dob_date_entry.grid(row=1,column=3)

    number_label=Label(detail_frame,text='Phone Number',font=('times new roman',16,'bold'),bg='white')
    number_label.grid(row=1,column=4,padx=20,pady=10)
    number_entry=Entry(detail_frame,font=('times new roman',16,'bold'),bg='lightyellow')
    number_entry.grid(row=1,column=5,padx=20,pady=10)

    salary_label=Label(detail_frame,text='Salary',font=('times new roman',16,'bold'),bg='white')
    salary_label.grid(row=2,column=0,padx=20,pady=10)
    salary_entry=Entry(detail_frame,font=('times new roman',16,'bold'),bg='lightyellow')
    salary_entry.grid(row=2,column=1,padx=20,pady=10)

    address_label=Label(detail_frame,text='Address',font=('times new roman',16,'bold'),bg='white')
    address_label.grid(row=2,column=2,padx=20,pady=10,sticky='w')
    address_text=Text(detail_frame,width=20,height=3,font=('times new roman',16,'bold'),bg='lightyellow')
    address_text.grid(row=2,column=3,padx=20,pady=10,rowspan=2)

    usertype_label=Label(detail_frame,text="User type",font=('times new roman',16,'bold'),bg='white')
    usertype_label.grid(row=2,column=4,padx=20,pady=10)
    usertype_combobox=ttk.Combobox(detail_frame,values=('Admin','Employee'),font=('times new roman',16,'bold'),width=18,state='readonly')
    usertype_combobox.set('Employee Type')
    usertype_combobox.grid(row=2,column=5)   

    password_label=Label(detail_frame,text='Password',font=('times new roman',16,'bold'),bg='white')
    password_label.grid(row=3,column=0,padx=20,pady=10)
    password_entry=Entry(detail_frame,font=('times new roman',16,'bold'),bg='lightyellow')
    password_entry.grid(row=3,column=1,padx=20,pady=10)    

    button_frame=Frame(employee_frame,bg='white')
    button_frame.place(x=400,y=530)

    add_button=Button(button_frame,text='Add',font=('times new roman',12),width=10,cursor='hand2',fg='white',bg='#0f4d7d')
    add_button.grid(row=0,column=0,padx=20)

    update_button=Button(button_frame,text='Update',font=('times new roman',12),width=10,cursor='hand2',fg='white',bg='#0f4d7d')
    update_button.grid(row=0,column=1,padx=20)
    
    delete_button=Button(button_frame,text='Delete',font=('times new roman',12),width=10,cursor='hand2',fg='white',bg='#0f4d7d')
    delete_button.grid(row=0,column=2,padx=20)

    clear_button=Button(button_frame,text='Clear',font=('times new roman',12),width=10,cursor='hand2',fg='white',bg='#0f4d7d')
    clear_button.grid(row=0,column=3,padx=20)


#*GUI PORT
window=Tk()

window.title("Dashboard")
window.geometry('1670x850+0+0')
window.resizable(0,0)
window.config(bg='white')

bg_image=PhotoImage(file='./images/inventory1.png')
titleLabel=Label(window,image=bg_image,compound=LEFT,text=" Inventory Managment System",font=('times new roman',40,'bold'),bg='#010c48',fg='white',anchor='w',padx=20)
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
employee_button=Button(leftFrame,image=employee_icon,compound=LEFT,text='Employees',font=('times new roman',20,'bold'),anchor='w',padx=10,command=employee_form)
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
