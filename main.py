import psutil
import tkinter as tk
from tkinter import ttk

def update_connections():
    tree.delete(*tree.get_children())
    for conn in psutil.net_connections(kind='tcp'):
        tree.insert('', 'end', values=(conn.laddr.ip, conn.laddr.port, conn.status))

root = tk.Tk()
root.title("Simple TCP View")

tree = ttk.Treeview(root, columns=('IP', 'Port', 'Status'), show='headings')
for col in ('IP', 'Port', 'Status'):
    tree.heading(col, text=col)
tree.pack(fill='both', expand=True)

btn = tk.Button(root, text="Refresh", command=update_connections)
btn.pack()

update_connections()
root.mainloop()