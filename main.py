"""Simple Tkinter viewer for current TCP/UDP connections using psutil."""

from __future__ import annotations

import socket
import tkinter as tk
from tkinter import ttk

import psutil

# enum for selection between tcp and udp
class Protocol:  # pylint: disable=too-few-public-methods
    """Protocol constants for psutil kinds (kept for future filtering options)."""

    TCP = "tcp"
    UDP = "udp"
    TCPV6 = "tcp6"
    UDPV6 = "udp6"

class TcpViewer:
    """Viewer controller that populates a tree with current socket connections."""

    def __init__(self, root: tk.Tk, tree: ttk.Treeview) -> None:
        """Initialize the viewer and render the first set of rows."""
        self.root = root
        self.tree = tree
        self.refresh_btn = tk.Button(
            root, text="Refresh", command=self.update_connections
        )
        self.refresh_btn.pack()
        self.update_connections()

    def update_connections(self) -> None:
        """Refresh the table with current connections across all protocols."""
        self.tree.delete(*self.tree.get_children())
        try:
            connections = psutil.net_connections(kind="all")
        except (psutil.Error, OSError) as err:
            # Display the error in the table instead of crashing
            self.tree.insert("", "end", values=("Error", "", str(err)))
            return

        for conn in connections:
            laddr = getattr(conn, "laddr", None)
            if not laddr:
                continue

            pid = getattr(conn, "pid", None)
            process_name = ""
            if pid:
                try:
                    process = psutil.Process(pid)
                    process_name = process.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    process_name = ""

            # psutil returns laddr as a tuple (ip, port) for INET sockets;
            # on some versions it may be a namedtuple with .ip/.port
            if isinstance(laddr, tuple):
                ip, port = laddr[0], laddr[1]
            else:
                ip = getattr(laddr, "ip", "")
                port = getattr(laddr, "port", "")

            status = getattr(conn, "status", "") or "-"
            status = "-" if str(status).upper() == "NONE" else status

            family_val = getattr(conn, "family", None)
            try:
                family_name = socket.AddressFamily(family_val).name  # type: ignore[arg-type]
            except (ValueError, AttributeError, TypeError):
                family_name = str(family_val)

            sock_type_val = getattr(conn, "type", None)
            try:
                sock_type_name = socket.SocketKind(sock_type_val).name  # type: ignore[arg-type]
            except (ValueError, AttributeError, TypeError):
                sock_type_name = str(sock_type_val)

            self.tree.insert(
                "",
                "end",
                values=(process_name, pid, ip, port, status, family_name, sock_type_name),
            )

    def refresh(self) -> None:
        """Public method to trigger a refresh externally if needed."""
        self.update_connections()

def create_gui() -> tuple[tk.Tk, ttk.Treeview]:
    """Create and return the Tk root window and configured Treeview widget."""
    root = tk.Tk()
    root.title("TCPViewer")

    columns = ("Process", "ProcessId", "IP", "Port", "Status", "Family", "Type")
    tree = ttk.Treeview(root, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
    tree.pack(fill="both", expand=True)
    return root, tree

def main() -> None:
    """Entrypoint to create the UI and start the main loop."""
    root, tree = create_gui()
    # Create the viewer with required arguments
    _viewer = TcpViewer(root, tree)
    root.mainloop()


if __name__ == "__main__":
    main()
