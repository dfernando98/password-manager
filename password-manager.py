from tkinter import *
from tkinter import ttk
from tkinter import simpledialog
import sqlite3

# Database code

# Establish connection with sqlite3 database
db = sqlite3.connect('password-manager.db')
cursor = db.cursor()

# Create table for masterpassword
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS masterpass(
id INTEGER PRIMARY KEY,
password TEXT NOT NULL);
"""
)

# Create table for website, username, password entries
cursor.execute("""
CREATE TABLE IF NOT EXISTS vault(
id INTEGER PRIMARY KEY,
website TEXT NOT NULL,
username TEXT NOT NULL,
password TEXT NOT NULL);
"""
)


def vaultScreen():
    for widgets in window.winfo_children():
      widgets.destroy()
    
    window.geometry("700x500")

    lbl = Label(window, anchor=CENTER, text="Password Vault")
    lbl.grid(column=1)

    lbl1 = Label(window, text="Website")
    lbl1.grid(row=1, column=0, padx=80)

    lbl2 = Label(window, text="Username")
    lbl2.grid(row=1, column=1, padx=80)

    lbl3 = Label(window, text="Password")
    lbl3.grid(row=1, column=2, padx=80)


    def addEntry():
        url = simpledialog.askstring("Input", "Enter URL/site name:")
        uname = simpledialog.askstring("Input", "Enter username:")
        pword = simpledialog.askstring("Input", "Enter password:")

        # Insert data into vault table
        cursor.execute("""
        INSERT INTO vault(
        website, username, )
        """
        
        )

    
    btn = Button(window, text="Add Entry", command=addEntry, anchor=CENTER)
    btn.pack()

    
def checkPassword():
    if txt.get() == txt1.get():
        # change to vaultScreen
        # add masterpassword into database
        
        vaultScreen()
    else:
        window.config(text="Passwords do not match")

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