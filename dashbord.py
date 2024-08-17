from tkinter import *


window=Tk()
window.title("Dashboard")
window.geometry('1270x700+0+0')
window.resizable(0,0)
window.config(bg='white')

bg_image=PhotoImage(file='inventory1.png')
titleLabel=Label(window,image=bg_image,compound=LEFT,text=" Inventory Managment System",font=('times new roman',40,'bold'),bg='#010c48',fg='white',anchor='w',padx=20)
titleLabel.place(x=0,y=0,relwidth=1)

logoutButton=Button(window,text='Logout',font=('times new roman',20,'bold'),fg='#010c48',bg='white')
logoutButton.place(x=1100,y=10)

subtitleLabel=Label(window,text='Welcome, Admin\t\t Date: 16/08/2024\t\t Time: 12:36:17 pm',font=('times new roman',15),bg='#4d636d')
subtitleLabel.place(x=0,y=70,relwidth=1)

window.mainloop()
