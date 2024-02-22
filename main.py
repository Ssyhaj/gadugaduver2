import socket
import os
import tkinter
from threading import Thread
import signal


def keyboardInterruptHandler(signal, frame):
    if client_socket:
        dead = "DEAD"
        client_socket.send(dead.encode())
        client_socket.close()
    if top:
        top.destroy()
    os._exit(1)

signal.signal(signal.SIGINT, keyboardInterruptHandler)

def on_closing(event=None):
    if client_socket:
        dead = "DEAD"
        client_socket.send(dead.encode())
        client_socket.close()
    top.destroy()
    os._exit(1)

def raise_messages(frame):
    frame.tkraise()
    recipient = usr_name.get()

    if recipient == "":
        return

    if recipient in unread_messages.keys():
        del unread_messages[recipient]

    labelvar.set(recipient)
    msg_list.delete(0, tkinter.END)
    mode = "r+"
    if not(os.path.isfile("conversations/"+ my_username + "_" + recipient)):
        mode = "a+"
    with open("conversations/" + my_username + "_" + recipient, mode) as f:
        lines = f.readlines()
        for line in lines:
            msg_list.insert(tkinter.END, line[:-1])  # usunięcie znaku nowej lini
        f.close()

def raise_menu(frame, usr_list):
    frame.tkraise()
    usr_name.set("")
    refresh_menu()
    usr_list.bind("<Double-Button-1>", user_clicked)  # Przypisanie zdarzenia kliknięcia na liście użytkowników

def refresh_menu():
    usr_list.delete(0, tkinter.END)
    for user, unread_count in unread_messages.items():
        usr_list.insert(tkinter.END, f"{user} ({unread_count})")

def user_clicked(event):
    selection = usr_list.curselection()
    if selection:
        index = selection[0]
        username_with_count = usr_list.get(index)
        username = username_with_count.split(" ")[0]  # Wyodrębnienie nazwy użytkownika
        usr_name.set(username)  # Ustawienie nazwy użytkownika w polu tekstowym
        raise_messages(messages_frame)  # Rozpoczęcie konwersacji z wybranym użytkownikiem

def receive():
    while True:
        try:
            msg = client_socket.recv(1024).decode()
            if len(msg) == 0:
                continue

            (sender, message) = str(msg).split(" ", 1)
            message = sender + ": " + message

            with open("conversations/" + my_username + "_" + sender, "a+") as f:
                f.write(message + "\n")
                f.close()

            if sender != usr_name.get():
                if sender not in unread_messages.keys():
                    unread_messages[sender] = 0
                unread_messages[sender] += 1
                refresh_menu()
                continue
            msg_list.insert(tkinter.END, message)
            msg_list.see(tkinter.END)

        except OSError:
            break


def send(event=None):
    msg = my_msg.get()
    if msg == "":
        return
    my_msg.set("")
    entry_field.config(width=10)
    recipient = usr_name.get()
    msgf = "SEND " + recipient + " " + my_username + " " + msg
    client_socket.send(msgf.encode())

    msg = "Ty: " + msg
    msg_list.insert(tkinter.END, msg)

    msg_list.see(tkinter.END)

    with open("conversations/" + my_username + "_" + recipient, "a+") as f:
        f.write(msg + "\n")
        f.close()

hostname = "192.168.124.128" # ip serwera
port = 1234          #port serwera

my_username = input("Username: ")

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

client_socket.connect((hostname, port))

if not os.path.exists('conversations'):
    os.mkdir('conversations')

username = "LOGIN " + my_username
client_socket.send(username.encode())

def rgb_hack(rgb):
    return "#%02x%02x%02x" % rgb

top = tkinter.Tk()
top.iconbitmap('icon.ico')
top.title("Chat - " + my_username)

usr_name = ""
unread_messages = {}

messages_frame = tkinter.Frame(top)

my_msg = tkinter.StringVar()

scrollbar = tkinter.Scrollbar(messages_frame)
msg_list = tkinter.Listbox(messages_frame, height=15, width=50, yscrollcommand=scrollbar.set)
scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
msg_list.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
msg_list.pack()

messages_frame.grid(row=0, column=0, sticky="nsew")  # sticky="nsew" pozwoli na rozciąganie się ramki
messages_frame.config(bg=rgb_hack((220, 220, 220)))
labelvar = tkinter.StringVar()
label = tkinter.Label(messages_frame, textvariable=labelvar)
label.config(bg=rgb_hack((220, 220, 220)))
label.pack()

def update_entry_width(event=None):
    entry_width = len(my_msg.get()) + 5  # Adjust this value as needed for padding
    entry_field.config(width=entry_width)

entry_field = tkinter.Entry(messages_frame, textvariable=my_msg)
entry_field.bind("<Return>", send)
entry_field.bind("<KeyRelease>", update_entry_width)  # Bind the update function to key release event
entry_field.pack(fill=tkinter.X)

send_button = tkinter.Button(messages_frame, text="Wyslij", bg='blue', fg='white', command=send)
send_button.pack()
back_button = tkinter.Button(messages_frame, text="Wyjdz z rozmowy",  bg='blue', fg='white', command=lambda: raise_menu(menu_frame, usr_list))
back_button.pack()

menu_frame = tkinter.Frame(top)
usr_name = tkinter.StringVar()
usr_name.set("Type name of user")

menu_frame.grid(row=0, column=0, sticky="nsew")  # sticky="nsew" pozwoli na rozciąganie się ramki
menu_frame.config(bg=rgb_hack((220, 220, 220)))

scrollbar2 = tkinter.Scrollbar(menu_frame)
usr_list = tkinter.Listbox(menu_frame, height=15, width=50, yscrollcommand=scrollbar2.set)
scrollbar2.pack(side=tkinter.RIGHT, fill=tkinter.Y)
usr_list.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
usr_list.pack()

label_menu = tkinter.Label(menu_frame, text="Nazwa uzytkownika:")
label_menu.config(bg=rgb_hack((220, 220, 220)))
label_menu.pack()

name_field = tkinter.Entry(menu_frame, textvariable=usr_name)
name_field.pack(fill=tkinter.X)  # fill=tkinter.X pozwoli na rozciąganie się pola tekstowego wzdłuż osi X

name_button = tkinter.Button(menu_frame, text="Potwierdz", bg='blue', fg='white',command=lambda: raise_messages(messages_frame))
name_button.pack()

top.protocol("WM_DELETE_WINDOW", on_closing)

receive_thread = Thread(target=receive)
receive_thread.start()

raise_menu(menu_frame, usr_list)

# Konfiguracja rozciągania się ramki w oknie głównym
top.grid_rowconfigure(0, weight=1)
top.grid_columnconfigure(0, weight=1)

tkinter.mainloop()
