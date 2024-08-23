from tkinter import *
from tkinter import ttk
from tkcalendar import DateEntry
from tkinter import messagebox
import pymysql

def connect_database():
    try:
        connection = pymysql.connect(host='localhost',user='root',password='Vendetta7080')
        cursor = connection.cursor()
    except:
        messagebox.showerror('Error','Connection Failed')
        return
    cursor.execute('CREATE DATABASE IF NOT EXISTS inventory_system')
    cursor.execute('USE inventory_system')
    cursor.execute('CREATE TABLE IF NOT EXISTS employee_data (id INT PRIMARY KEY, name VARCHAR(100),gender VARCHAR(50),email VARCHAR(100),number VARCHAR(15),Dob VARCHAR(30),salary VARCHAR(50),address VARCHAR(50),usertype VARCHAR(50),password VARCHAR(50))')

connect_database()    

#!Function Port
def employee_form(window):
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
