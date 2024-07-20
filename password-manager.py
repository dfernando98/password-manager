from tkinter import *
from tkinter import ttk

def checkPassword():
    if txt.get() != txt1.get():
        lbl2.config(text="Passwords do not match")
    else:
        lbl2.config(text="")

window = Tk()
window.title("Password Manager")
window.geometry("350x150")

lbl = Label(window, text="Create a Master Password")
lbl.pack()

txt = Entry(window, show="*")
txt.pack()

lbl1 = Label(window, text="Re-Enter Password")
lbl1.pack()

txt1 = Entry(window, show="*")
txt1.pack()

lbl2 = Label(window)
lbl2.pack()

btn = Button(window, text="Submit", command=checkPassword)
btn.pack()


window.mainloop()