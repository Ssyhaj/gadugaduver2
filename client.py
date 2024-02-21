import socket
import os
import tkinter
from threading import Thread
import signal


# wylogowanie użytkownika po wcisnięciu "ctrl + c"
def keyboardInterruptHandler(signal, frame):

    if client_socket:
        dead = "DEAD"
        client_socket.send(dead.encode())
        client_socket.close()
    if top:
        top.destroy()
    os._exit(1)


# obsługa sygnału "ctrl + c"
signal.signal(signal.SIGINT, keyboardInterruptHandler)


# wylogowanie użytkownika po wciśnięciu "X" GUI
def on_closing(event=None):

    if client_socket:
        dead = "DEAD"
        client_socket.send(dead.encode())
        client_socket.close()
    top.destroy()
    os._exit(1)


# GUI - przejście do okna konwersacji oraz wczytanie konwersacji
def raise_messages(frame):
    frame.tkraise()
    recipent = usr_name.get()

    if recipent == "":
        return

    if recipent in unread_messages.keys():
        del unread_messages[recipent]

    labelvar.set(recipent)
    msg_list.delete(0, tkinter.END)
    mode = "r+"
    if not(os.path.isfile("conversations/"+ my_username + "_" + recipent)):
        mode = "a+"
    with open("conversations/" + my_username + "_" + recipent, mode) as f:
        lines = f.readlines()
        for line in lines:
            msg_list.insert(tkinter.END, line[:-1])  # usunięcie znaku nowej lini
        f.close()


# GUI - przeście do okna Głównego
def raise_menu(frame):
    frame.tkraise()
    usr_name.set("")
    refresh_menu()


# GUI - odświeżenie okna Głównego w celu wyśletlenia nowych przychodzących wiadomości
def refresh_menu():
    usr_list.delete(0, tkinter.END)
    for user in unread_messages:
        usr_list.insert(tkinter.END, str(user) + " : " + str(unread_messages[user]))


# obsługa odbioru wiadomości
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

            # Wyświetlenie informacji o przychodzących wiadomościach jeśli konwersacja z użytkownikiem wysyłającym nie jest aktualnie otwarta
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


# obsługa wysyłania wiadomości
def send(event=None):
    msg = my_msg.get()
    if msg == "":
        return
    my_msg.set("")
    recipent = usr_name.get()
    # Przekształcenie wiadomości do postaci zrozumiałej dla serwera
    msgf = "SEND " + recipent + " " + my_username + " " + msg
    client_socket.send(msgf.encode())

    msg = "Ty: " + msg
    msg_list.insert(tkinter.END, msg)

    msg_list.see(tkinter.END)

    with open("conversations/" + my_username + "_" + recipent, "a+") as f:
        f.write(msg + "\n")
        f.close()


# Główny program

IP = "192.168.8.103" # ip serwera
PORT = 8011          #port serwera

my_username = input("Username: ") # wczytanie loginu użytkownika

# Utworzenie socketa
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Połączenie z serwerem
client_socket.connect((IP, PORT))

# Utworzenie folderu przechowującego konwersacje użytkowników
if not os.path.exists('conversations'):
    os.mkdir('conversations')

# Wysłanie informacji o zalagowaniu się użytkownika w postaci zrozumiałej dla serwera
username = "LOGIN " + my_username
client_socket.send(username.encode())


def rgb_hack(rgb):
    return "#%02x%02x%02x" % rgb

top = tkinter.Tk()
top.title("GG")

usr_name = ""
unread_messages = {}

messages_frame = tkinter.Frame(top)

my_msg = tkinter.StringVar()
my_msg.set("Czesc")

scrollbar = tkinter.Scrollbar(messages_frame)
msg_list = tkinter.Listbox(messages_frame, height=15, width=50, yscrollcommand=scrollbar.set)
scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
msg_list.pack(side=tkinter.LEFT, fill=tkinter.BOTH)
msg_list.pack()


messages_frame.grid(row=0, column=0)
messages_frame.config(bg=rgb_hack((220, 220, 220)))
labelvar = tkinter.StringVar()
label = tkinter.Label(messages_frame, textvariable=labelvar)
label.config(bg=rgb_hack((220, 220, 220)))
label.pack()

entry_field = tkinter.Entry(messages_frame, textvariable=my_msg)
entry_field.bind("<Return>", send)
entry_field.pack()


send_button = tkinter.Button(messages_frame, text="Wyślij", bg='black', fg='white', command=send)
send_button.pack()
back_button = tkinter.Button(messages_frame, text="Menu",  bg='black', fg='white', command=lambda: raise_menu(menu_frame))
back_button.pack()

menu_frame = tkinter.Frame(top)
usr_name = tkinter.StringVar()
usr_name.set("Type name of user")


menu_frame.grid(row=0, column=0)
menu_frame.config(bg=rgb_hack((220, 220, 220)))

scrollbar2 = tkinter.Scrollbar(menu_frame)
usr_list = tkinter.Listbox(menu_frame, height=15, width=50, yscrollcommand=scrollbar2.set)
scrollbar2.pack(side=tkinter.RIGHT, fill=tkinter.Y)
usr_list.pack(side=tkinter.LEFT, fill=tkinter.BOTH)
usr_list.pack()

label_menu = tkinter.Label(menu_frame, text="Nazwa użytkownika:")
label_menu.config(bg=rgb_hack((220, 220, 220)))
label_menu.pack()

name_field = tkinter.Entry(menu_frame, textvariable=usr_name)
name_field.pack()

name_button = tkinter.Button(menu_frame, text="Zatwierdź", bg='black', fg='white',command=lambda: raise_messages(messages_frame))
name_button.pack()

top.protocol("WM_DELETE_WINDOW", on_closing)

receive_thread = Thread(target=receive)
receive_thread.start()

raise_menu(menu_frame)
tkinter.mainloop()