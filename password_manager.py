import sqlite3, hashlib
from tkinter import *
from tkinter import simpledialog
from functools import partial
import uuid
import pyperclip
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
import secrets
import string

salt = b"2444"

def kdf():
    return PBKDF2HMAC(
        algorithm = hashes.SHA256(),
        length = 32,
        salt=salt,
        iterations = 480000
    )

encryptionKey = 0

def encrypt(message: bytes, key: bytes) -> bytes:
    return Fernet(key).encrypt(message)

def decrypt(message: bytes, token: bytes) -> bytes:
    return Fernet(token).decrypt(message)

# Generate Password function
# The secrets module will be used to generate a cryptographically safe password
# Adapted from secrets module documentation
def genPassword(length: int) -> str:
    return "".join(
        # Generates a password with lowercase and uppercase ascii letters, digits and punctuation marks
        secrets.choice(string.ascii_letters + string.digits + string.punctuation)
        for i in range(length)
    )

# Database code
with sqlite3.connect("password_manager.db") as db:
    cursor = db.cursor()

# Create table for masterpassword
cursor.execute("""
CREATE TABLE IF NOT EXISTS masterpassword(
id INTEGER PRIMARY KEY,
password TEXT NOT NULL,
recoveryKey TEXT NOT NULL);
"""
)

# Create table for list of passwords
cursor.execute("""
CREATE TABLE IF NOT EXISTS passwordlist(
id INTEGER PRIMARY KEY,
website TEXT NOT NULL,
username TEXT NOT NULL,
password TEXT NOT NULL);
"""
)

cursor.execute("""
CREATE TABLE IF NOT EXISTS masterkey(
id INTEGER PRIMARY KEY,
masterKeyPassword TEXT NOT NULL,
masterKeyRecoveryKey TEXT NOT NULL);
"""
)

# popUp function that asks for user input and returns answer
def popUp(text):
    answer = simpledialog.askstring("input", text)
    return answer

# Initiate tkinter window
window = Tk()
window.update()

window.title("Password Manager")

# Creates an sha256 hash of input and returns the hexadecimal converted representation of it
def hashPassword(input):
    hash1 = hashlib.sha256(input)
    hash1 = hash1.hexdigest()

    return hash1

def firstTimeScreen(hasMasterKey=None):
    for widget in window.winfo_children():
        widget.destroy()
    
    window.geometry('250x125')
    lbl = Label(window, text="Create a Master Password")
    lbl.config(anchor=CENTER)
    lbl.pack()

    txt = Entry(window, width=20, show="*")
    txt.pack()
    txt.focus()

    lbl1 = Label(window, text="Re-enter Password")
    lbl1.config(anchor=CENTER)
    lbl1.pack()

    txt1 = Entry(window, width=20, show="*")
    txt1.pack()

    def savePassword():
        if txt.get() == txt1.get():
            sql = "DELETE FROM masterpassword WHERE id = 1"

            cursor.execute(sql)

            hashedPassword = hashPassword(txt.get().encode())
            # Generate a random uuid key
            key = uuid.uuid4().hex
            hashedRecoveryKey = hashPassword(key.encode())

            insert_password = """INSERT INTO masterpassword(password, recoveryKey)
            VALUES(?, ?) """
            cursor.execute(insert_password, ((hashedPassword),(hashedRecoveryKey)))

            # Check if masterkey exists
            # If masterkey does exist, replace it by encrypting it with new password hasn and new recoverykey hash
            # If it does not, generate a masterkey and encrypt it with a new password hash and new recoverykey hash
            masterKey = hasMasterKey if hasMasterKey else genPassword(64)
            cursor.execute("SELECT * FROM masterkey")
            if cursor.fetchall():
                cursor.execute("DELETE FROM masterkey WHERE id = 1")
            
            insert_masterkey = """INSERT INTO masterkey(masterKeyPassword, masterKeyRecoveryKey)
            VALUES(?, ?) """
            cursor.execute(
                insert_masterkey,
                (
                    (encrypt(masterKey.encode(), base64.urlsafe_b64encode(kdf().derive(txt.get().encode())))),
                    (encrypt(masterKey.encode(), base64.urlsafe_b64encode(kdf().derive(key.encode()))))
                )
            )

            # Change encryptionKey to masterKey unencrypted by masterpassword
            global encryptionKey
            encryptionKey = base64.urlsafe_b64encode(kdf().derive(masterKey.encode()))

            db.commit()

            recoveryScreen(key)

        else:
            lbl.config(text="Passwords do not match")
    
    btn = Button(window, text="Save", command=savePassword)
    btn.pack(pady=5)

def recoveryScreen(key):
    for widget in window.winfo_children():
        widget.destroy()

    window.geometry('250x125')
    lbl = Label(window, text="Save this key to be able to recover account")
    lbl.config(anchor=CENTER)
    lbl.pack()

    lbl1 = Label(window, text=key)
    lbl1.config(anchor=CENTER)
    lbl1.pack()

    def copyKey():
        pyperclip.copy(lbl1.cget("text"))
    
    btn = Button(window, text="Copy Key", command=copyKey)
    btn.pack(pady=5)

    def done():
        managerScreen()

    btn = Button(window, text="Done", command=done)
    btn.pack(pady=5)

def resetScreen():
    for widget in window.winfo_children():
        widget.destroy()
    
    window.geometry('250x125')
    lbl = Label(window, text="Enter Recovery Key")
    lbl.config(anchor=CENTER)
    lbl.pack()

    txt = Entry(window, width=20)
    txt.pack()
    txt.focus()

    lbl1 = Label(window)
    lbl1.config(anchor=CENTER)
    lbl1.pack()

    def getRecoveryKey():
        recoveryKeyCheck = hashPassword(str(txt.get()).encode())
        cursor.execute(
            "SELECT * FROM masterpassword WHERE id = 1 AND recoveryKey = ?",
            [(recoveryKeyCheck)],
        )

        return cursor.fetchall()
    
    def checkRecoveryKey():
        recoveryKey = getRecoveryKey()

        if recoveryKey:
            # unencrypt masterKey and pass it to firstTimeScreen
            cursor.execute("SELECT * FROM masterkey")
            masterKeyEntry = cursor.fetchall()

            if masterKeyEntry:
                masterKeyRecoveryKey = masterKeyEntry[0][2]

                masterKey = decrypt(masterKeyRecoveryKey, base64.urlsafe_b64encode(kdf().derive(str(txt.get()).encode()))).decode()

                firstTimeScreen(masterKey)
            else:
                txt.delete(0, "end")
                lbl1.config(text="Wrong Key")
    
    btn = Button(window, text="Check Key", command=checkRecoveryKey)
    btn.pack(pady=5)

def loginScreen():
    for widget in window.winfo_children():
        widget.destroy()
    
    window.geometry('250x125')

    lbl = Label(window, text="Enter Master Password")
    lbl.config(anchor=CENTER)
    lbl.pack()

    txt = Entry(window, width=20, show="*")
    txt.pack()
    txt.focus()

    lbl1 = Label(window)
    lbl1.config(anchor=CENTER)
    lbl1.pack(side=TOP)

    def getMasterPassword():
        checkHashedPassword = hashPassword(txt.get().encode())

        cursor.execute(
            "SELECT * FROM masterpassword WHERE id = 1 AND password = ?",
            [(checkHashedPassword)],
        )
        return cursor.fetchall()
    
    def checkPassword():
        password = getMasterPassword()

        if password:
            # change encryptionKey to masterKey unencrypted by masterpassword
            cursor.execute("SELECT * FROM masterkey")
            masterKeyEntry = cursor.fetchall()
            if masterKeyEntry:
                masterKeyPassword = masterKeyEntry[0][1]

                masterKey = decrypt(masterKeyPassword, base64.urlsafe_b64encode(kdf().derive(txt.get().encode())))

                global encryptionKey
                encryptionKey = base64.urlsafe_b64encode(kdf().derive(masterKey))

                managerScreen()
            else:
                print("Master Key entry missing")
                exit()
        else:
            txt.delete(0, "end")
            lbl1.config(text="Wrong Password")
    
    def resetPassword():
        resetScreen()
    
    btn = Button(window, text="Submit", command=checkPassword)
    btn.pack(pady=5)

    btn = Button(window, text="Reset Password", command=resetPassword)
    btn.pack(pady=5)

def managerScreen():
    for widget in window.winfo_children():
        widget.destroy()

    def addEntry():
        text1 = "Website"
        text2 = "Username"
        text3 = "Password"
        website = encrypt(popUp(text1).encode(), encryptionKey)
        username = encrypt(popUp(text2).encode(), encryptionKey)
        password = encrypt(popUp(text3).encode(), encryptionKey)

        insert_fields = """INSERT INTO passwordlist(website, username, password)
        VALUES(?, ?, ?) """
        cursor.execute(insert_fields, (website, username, password))
        db.commit()

        managerScreen()
    
    def removeEntry(input):
        cursor.execute("DELETE FROM passwordlist WHERE id = ?", (input,))
        db.commit()
        managerScreen()
    
    window.geometry("750x550")
    window.resizable(height=None, width=None)
    lbl = Label(window, text="Password Manager")
    lbl.grid(column=1)

    btn = Button(window, text="+", command=addEntry)
    btn.grid(column=1, pady=10)

    lbl = Label(window, text="Website")
    lbl.grid(row=2, column=0, padx=80)
    lbl = Label(window, text="Username")
    lbl.grid(row=2, column=1, padx=80)
    lbl = Label(window, text="Password")
    lbl.grid(row=2, column=2, padx=80)

    cursor.execute("SELECT * FROM passwordlist")
    if cursor.fetchall != None:
        i = 0
        while True:
            cursor.execute("SELECT * FROM passwordlist")
            array = cursor.fetchall()

            if len(array) == 0:
                break

            lbl1 = Label(
                window, 
                text=(decrypt(array[i][1], encryptionKey)),
                font=("Helvetica", 12),
                )
            lbl1.grid(column=0, row=(i+3))

            lbl2 = Label(
                window, 
                text=(decrypt(array[i][2], encryptionKey)),
                font=("Helvetica", 12),
                )
            lbl2.grid(column=1, row=(i+3))

            lbl3 = Label(
                window, 
                text=(decrypt(array[i][3], encryptionKey)),
                font=("Helvetica", 12),
                )
            lbl3.grid(column=2, row=(i+3))

            btn = Button(
                window, text="Delete", command=partial(removeEntry, array[i][0])
            )
            btn.grid(column=3, row=(i+3), pady=10)

            i = i+1

            cursor.execute("SELECT * FROM passwordlist")
            if len(cursor.fetchall()) <= i:
                break

cursor.execute("SELECT * FROM masterpassword")
if cursor.fetchall():
    loginScreen()
else:
    firstTimeScreen()
window.mainloop()        

    
