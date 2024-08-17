from tkinter import *


window=Tk()
window.title("Dashboard")
window.geometry('1270x700+0+0')
window.resizable(0,0)
window.config(bg='white')

bg_image=PhotoImage(file='inventory.png')
titleLabel=Label(window,image=bg_image,compound=LEFT,text="Inventory Managment System",font=('times new roman',40,'bold'),bg='#010c48',fg='white')
titleLabel.place(x=0,y=0)

window.mainloop()
