import psutil
import socket
import tkinter as tk
from tkinter import ttk

# enum for selection between tcp and udp
class Protocol:
    TCP = 'tcp'
    UDP = 'udp'
    TCPV6 = 'tcp6'
    UDPV6 = 'udp6'

class tcp_view:
    def __init__(self, root, tree):
        self.root = root
        self.tree = tree
        self.refresh_btn = tk.Button(root, text="Refresh", command=self.update_connections)
        self.refresh_btn.pack()
        self.update_connections()

    def update_connections(self):
        self.tree.delete(*self.tree.get_children())
        try:
            connections = psutil.net_connections(kind='all')
        except Exception as e:
            # Display the error in the table instead of crashing
            self.tree.insert('', 'end', values=("Error", "", str(e)))
            return

        for conn in connections:
            laddr = getattr(conn, 'laddr', None)
            if not laddr:
                continue

            pid = getattr(conn, 'pid', None)
            process_name = ''
            if pid:
                try:
                    process = psutil.Process(pid)
                    process_name = process.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    process_name = ''   

            # psutil returns laddr as a tuple (ip, port) for INET sockets;
            # on some versions it may be a namedtuple with .ip/.port
            try:
                if isinstance(laddr, tuple):
                    ip, port = laddr[0], laddr[1]
                else:
                    ip, port = getattr(laddr, 'ip', ''), getattr(laddr, 'port', '')
            except Exception:
                continue

            status = getattr(conn, 'status', '')
            status = '-' if not status or str(status).upper() == 'NONE' else status

            fam = getattr(conn, 'family', '')
            family = socket.AddressFamily(fam)
            type = getattr(conn, 'type', '')
            type = socket.SocketKind(type)

            self.tree.insert('', 'end', values=(process_name, pid, ip, port, status, family._name_, type._name_))

def create_gui():
    root = tk.Tk()
    root.title("TCPViewer")

    tree = ttk.Treeview(root, columns=('Process', 'ProcessId', 'IP', 'Port', 'Status', 'Family', 'Type'), show='headings')
    for col in ('Process', 'ProcessId', 'IP', 'Port', 'Status', 'Family', 'Type'):
        tree.heading(col, text=col)
        tree.pack(fill='both', expand=True)
    return root, tree

root, tree = create_gui()

# Create the viewer with required arguments
viewer = tcp_view(root, tree)
root.mainloop()