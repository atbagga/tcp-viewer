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

class TcpViewer:  # pylint: disable=too-many-instance-attributes
    """Viewer controller that populates a tree with current socket connections."""

    def __init__(self, root: tk.Tk, tree: ttk.Treeview) -> None:
        """Initialize the viewer and render the first set of rows."""
        self.root = root
        self.tree = tree
        # Track sort order for each column (True = ascending, False = descending)
        self.sort_orders = {}
        # Store original data for sorting
        self.connection_data = []
        # Store all displayed data including deleted entries for sorting
        self.displayed_data = []
        # Store previous data for diff highlighting
        self.previous_data = []
        # Track highlighted items for cleanup
        self.highlighted_items = []
        # Cache for hostname resolutions to avoid repeated lookups
        self.hostname_cache = {}
        # Filter settings
        self.current_filter = ""
        self.filtered_data = []
        # Auto-refresh settings
        self.auto_refresh_enabled = False
        self.auto_refresh_job = None
        self.auto_refresh_interval = 10000  # 10 seconds in milliseconds

        # Create search/filter frame
        search_frame = tk.Frame(root)
        search_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(search_frame, text="Filter:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=50)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind('<KeyRelease>', self._on_search_change)

        # Help button to show filter syntax
        self.help_btn = tk.Button(search_frame, text="?", command=self._show_filter_help)
        self.help_btn.pack(side=tk.LEFT, padx=2)

        # Create button frame
        button_frame = tk.Frame(root)
        button_frame.pack(pady=5)

        self.auto_refresh_btn = tk.Button(
            button_frame, text="Start Auto Refresh", command=self.toggle_auto_refresh
        )
        self.auto_refresh_btn.pack(padx=5)

        # Set up column sorting
        self._setup_column_sorting()
        # Configure tree tags for highlighting
        self._setup_tree_tags()
        self.update_connections()

    def _resolve_hostname(self, ip: str) -> str:
        """Resolve IP address to hostname with caching and very short timeout."""
        if not ip or ip in ("", "0.0.0.0", "127.0.0.1", "::1", "::", "localhost"):
            return ""

        # Skip private/local IP ranges to avoid unnecessary lookups
        if (ip.startswith("192.168.") or ip.startswith("10.") or
            ip.startswith("172.") or ip.startswith("169.254.")):
            return ""

        # Check cache first
        if ip in self.hostname_cache:
            return self.hostname_cache[ip]

        try:
            # Set a very short timeout for hostname resolution
            original_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(0.5)  # 0.5 second timeout
            hostname = socket.gethostbyaddr(ip)[0]
            self.hostname_cache[ip] = hostname
            return hostname
        except (socket.herror, socket.gaierror, socket.timeout, OSError):
            # Resolution failed, cache the failure
            self.hostname_cache[ip] = ""
            return ""
        finally:
            # Reset timeout to original value
            socket.setdefaulttimeout(original_timeout)

    def _setup_tree_tags(self) -> None:
        """Configure tree tags for highlighting changed values."""
        self.tree.tag_configure("added", background="lightgreen")     # New connections
        self.tree.tag_configure("changed", background="lightyellow")  # Changed connections
        self.tree.tag_configure("deleted", background="lightcoral")   # Deleted connections

    def _show_filter_help(self) -> None:
        """Show filter syntax help in a popup window."""
        help_text = """Filter Syntax:

Column Shortcuts:
• name: Process name (e.g., name:chrome)
• pid: Process ID (e.g., pid:1234)
• lip: Local IP (e.g., lip:127.0.0.1)
• lport: Local Port (e.g., lport:80)
• rip: Remote IP (e.g., rip:8.8.8.8)
• rport: Remote Port (e.g., rport:443)
• host: Hostname (e.g., host:google.com)
• status: Connection Status (e.g., status:ESTABLISHED)
• family: Address Family (e.g., family:AF_INET)
• type: Socket Type (e.g., type:SOCK_STREAM)

Examples:
• name:chrome
• rport:443
• status:ESTABLISHED
• lip:192.168

You can also type partial matches without prefixes.
"""

        popup = tk.Toplevel(self.root)
        popup.title("Filter Help")
        popup.geometry("400x300")

        text_widget = tk.Text(popup, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert("1.0", help_text)
        text_widget.config(state=tk.DISABLED)

    def _on_search_change(self, event=None) -> None:  # pylint: disable=unused-argument
        """Handle search box changes and apply filters."""
        self.current_filter = self.search_var.get().strip()
        self._apply_filter()

    def _apply_filter(self) -> None:
        """Apply current filter to the connection data."""
        if not self.current_filter:
            # No filter, show all data
            self._display_data(self.displayed_data)
            return

        # Parse filter string
        filter_terms = self._parse_filter(self.current_filter)

        # Filter the data
        filtered_data = []
        for row in self.displayed_data:
            if self._row_matches_filter(row, filter_terms):
                filtered_data.append(row)

        self.filtered_data = filtered_data
        self._display_data(filtered_data)

    def _parse_filter(self, filter_str: str) -> dict:
        """Parse filter string into column-value pairs."""
        # Column shorthand mappings
        column_mapping = {
            'name': 0,      # Process
            'pid': 1,       # ProcessId
            'lip': 2,       # LocalIP
            'lport': 3,     # LocalPort
            'rip': 4,       # RemoteIP
            'rport': 5,     # RemotePort
            'host': 6,      # Hostname
            'status': 7,    # Status
            'family': 8,    # Family
            'type': 9       # Type
        }

        filters = {}

        # Split by spaces and process each term
        terms = filter_str.lower().split()

        for term in terms:
            if ':' in term:
                # Column-specific filter
                key, value = term.split(':', 1)
                if key in column_mapping:
                    filters[column_mapping[key]] = value
            else:
                # General search across all columns
                filters['general'] = term

        return filters

    def _row_matches_filter(self, row: tuple, filters: dict) -> bool:
        """Check if a row matches the filter criteria."""
        for col_index, filter_value in filters.items():
            if col_index == 'general':
                # General search - check if any column contains the value
                row_text = ' '.join(str(val).lower() for val in row)
                if filter_value not in row_text:
                    return False
            else:
                # Column-specific search
                if col_index < len(row):
                    cell_value = str(row[col_index]).lower()
                    if filter_value not in cell_value:
                        return False
                else:
                    return False

        return True

    def _display_data(self, data: list) -> None:
        """Display the given data in the tree view."""
        # Clear tree
        self.tree.delete(*self.tree.get_children())
        self.highlighted_items.clear()

        # Add filtered data
        for row_data in data:
            item_id = self.tree.insert("", "end", values=row_data)

            # Check if this is a deleted, changed, or added entry and apply tags
            if any("(DELETED)" in str(val) for val in row_data):
                self.tree.item(item_id, tags=("deleted",))
                self.highlighted_items.append(item_id)
            else:
                change_type = self._get_change_type(row_data)
                if change_type == "added":
                    self.tree.item(item_id, tags=("added",))
                    self.highlighted_items.append(item_id)
                elif change_type == "changed":
                    self.tree.item(item_id, tags=("changed",))
                    self.highlighted_items.append(item_id)

    def toggle_auto_refresh(self) -> None:
        """Toggle between auto refresh and manual refresh modes."""
        if self.auto_refresh_enabled:
            # Stop auto refresh
            self.auto_refresh_enabled = False
            if self.auto_refresh_job:
                self.root.after_cancel(self.auto_refresh_job)
                self.auto_refresh_job = None
            self.auto_refresh_btn.config(text="Start Auto Refresh")
        else:
            # Start auto refresh
            self.auto_refresh_enabled = True
            self.auto_refresh_btn.config(text="Stop Auto Refresh")
            self._schedule_next_refresh()

    def _schedule_next_refresh(self) -> None:
        """Schedule the next auto refresh."""
        if self.auto_refresh_enabled:
            self.auto_refresh_job = self.root.after(
                self.auto_refresh_interval, self._auto_refresh_callback
            )

    def _auto_refresh_callback(self) -> None:
        """Callback function for auto refresh."""
        if self.auto_refresh_enabled:
            self.update_connections()
            self._schedule_next_refresh()

    def _setup_column_sorting(self) -> None:
        """Set up click handlers for column headers to enable sorting."""
        columns = ("Process", "ProcessId", "LocalIP", "LocalPort", "RemoteIP",
                   "RemotePort", "Hostname", "Status", "Family", "Type")
        for col in columns:
            # Initialize sort order to ascending
            self.sort_orders[col] = True
            # Bind column header click to sort function
            self.tree.heading(col, command=lambda c=col: self._sort_by_column(c))

    def _sort_by_column(self, col: str) -> None:
        """Sort the tree data by the specified column."""
        # Use filtered data if filter is active, otherwise use all displayed data
        data_to_sort = (self.filtered_data if self.current_filter and self.filtered_data
                        else self.displayed_data)

        if not data_to_sort:
            return

        # Toggle sort order
        self.sort_orders[col] = not self.sort_orders[col]
        reverse = not self.sort_orders[col]

        # Define column indices
        col_indices = {
            "Process": 0,
            "ProcessId": 1,
            "LocalIP": 2,
            "LocalPort": 3,
            "RemoteIP": 4,
            "RemotePort": 5,
            "Hostname": 6,
            "Status": 7,
            "Family": 8,
            "Type": 9
        }

        col_index = col_indices[col]

        # Sort the data based on column type
        if col in ("ProcessId", "LocalPort", "RemotePort"):
            # Numeric sorting for PID and Port columns
            def numeric_key(x):
                val = str(x[col_index]).replace(" (DELETED)", "")
                return int(val) if val and val.isdigit() else 0

            sorted_data = sorted(
                data_to_sort,
                key=numeric_key,
                reverse=reverse
            )
        else:
            # String sorting for other columns
            sorted_data = sorted(
                data_to_sort,
                key=lambda x: str(x[col_index]).replace(" (DELETED)", "").lower(),
                reverse=reverse
            )

        # Display the sorted data
        self._display_data(sorted_data)

        # Update column header to show sort direction
        direction = "↓" if reverse else "↑"
        self.tree.heading(col, text=f"{col} {direction}")

        # Reset other column headers
        for other_col in col_indices:
            if other_col != col:
                self.tree.heading(other_col, text=other_col)

    def update_connections(self) -> None:  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        """Refresh the table with current connections across all protocols."""
        # Store previous data for comparison
        self.previous_data = self.connection_data.copy()

        self.connection_data = []  # Reset the data store
        self.displayed_data = []  # Reset displayed data

        try:
            connections = psutil.net_connections(kind="all")
        except (psutil.Error, OSError) as err:
            # Display the error in the table instead of crashing
            error_row = ("Error", "", str(err), "", "", "", "", "", "", "")
            self.connection_data.append(error_row)
            self.displayed_data.append(error_row)
            self._apply_filter()
            return

        # Process current connections
        current_keys = set()

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

            # Extract local address and port
            # psutil returns laddr as a tuple (ip, port) for INET sockets;
            # on some versions it may be a namedtuple with .ip/.port
            if isinstance(laddr, tuple):
                local_ip, local_port = laddr[0], laddr[1]
            else:
                local_ip = getattr(laddr, "ip", "")
                local_port = getattr(laddr, "port", "")

            # Extract remote address and port
            raddr = getattr(conn, "raddr", None)
            if raddr:
                if isinstance(raddr, tuple):
                    remote_ip, remote_port = raddr[0], raddr[1]
                else:
                    remote_ip = getattr(raddr, "ip", "")
                    remote_port = getattr(raddr, "port", "")
            else:
                remote_ip = ""
                remote_port = ""

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

            # Resolve hostname for remote IP (if available) with safety checks
            hostname = self._resolve_hostname(remote_ip) if remote_ip else ""

            row_data = (process_name, pid, local_ip, local_port, remote_ip, remote_port,
                        hostname, status, family_name, sock_type_name)

            # Track current connection key (using local IP and port for now)
            connection_key = (local_ip, local_port)
            current_keys.add(connection_key)

            self.connection_data.append(row_data)
            self.displayed_data.append(row_data)

        # Find and add deleted connections to displayed data
        if self.previous_data:
            for prev_row in self.previous_data:
                prev_key = (prev_row[2], prev_row[3])  # LocalIP, LocalPort
                if prev_key not in current_keys:
                    # This connection was deleted, add it to displayed data
                    deleted_row = tuple(str(val) + " (DELETED)" if i == 0 else val
                                      for i, val in enumerate(prev_row))
                    self.displayed_data.append(deleted_row)

        # Reset column headers to remove sort indicators
        columns = ("Process", "ProcessId", "LocalIP", "LocalPort", "RemoteIP",
                   "RemotePort", "Hostname", "Status", "Family", "Type")
        for col in columns:
            self.tree.heading(col, text=col)

        # Apply current filter and display data
        self._apply_filter()

        # Schedule removal of highlighting after 5 seconds
        if self.highlighted_items:
            self.root.after(5000, self._remove_highlighting)

    def _get_change_type(self, new_row: tuple) -> str:
        """Determine if a row is new, changed, or existing."""
        if not self.previous_data:
            # First run, don't highlight anything
            return "existing"

        # Create a unique key for comparison (LocalIP + LocalPort combination)
        new_key = (new_row[2], new_row[3])  # LocalIP, LocalPort

        # Look for matching connection in previous data
        for prev_row in self.previous_data:
            prev_key = (prev_row[2], prev_row[3])  # LocalIP, LocalPort
            if new_key == prev_key:
                # Found matching connection, check if any values changed
                if new_row != prev_row:
                    return "changed"
                return "existing"

        # New connection (not found in previous data)
        return "added"

    def _is_row_changed(self, new_row: tuple) -> bool:
        """Check if a row is new or has changed compared to previous data."""
        if not self.previous_data:
            # First run, don't highlight anything
            return False

        # Create a unique key for comparison (LocalIP + LocalPort combination)
        # This helps identify the same connection across refreshes
        new_key = (new_row[2], new_row[3])  # LocalIP, LocalPort

        # Look for matching connection in previous data
        for prev_row in self.previous_data:
            prev_key = (prev_row[2], prev_row[3])  # LocalIP, LocalPort
            if new_key == prev_key:
                # Found matching connection, check if any values changed
                return new_row != prev_row

        # New connection (not found in previous data)
        return True

    def _remove_highlighting(self) -> None:
        """Remove highlighting from all highlighted items and remove deleted entries."""
        items_to_remove = []

        for item_id in self.highlighted_items:
            try:
                # Check if item still exists (might have been deleted by sorting)
                if self.tree.exists(item_id):
                    # Check if this is a deleted item
                    item_values = self.tree.item(item_id, 'values')
                    if any("(DELETED)" in str(val) for val in item_values):
                        # Remove deleted items from tree and displayed_data
                        items_to_remove.append(item_id)
                        # Remove from displayed_data
                        self.displayed_data = [row for row in self.displayed_data
                                             if not any("(DELETED)" in str(val) for val in row)]
                    else:
                        # Just remove highlighting for changed items
                        self.tree.item(item_id, tags=())
            except tk.TclError:
                # Item no longer exists, ignore
                pass

        # Remove deleted items from tree
        for item_id in items_to_remove:
            try:
                if self.tree.exists(item_id):
                    self.tree.delete(item_id)
            except tk.TclError:
                pass

        self.highlighted_items.clear()

    def refresh(self) -> None:
        """Public method to trigger a refresh externally if needed."""
        self.update_connections()

    def cleanup(self) -> None:
        """Clean up resources when the application is closing."""
        if self.auto_refresh_job:
            self.root.after_cancel(self.auto_refresh_job)
            self.auto_refresh_job = None
        # Clear any pending highlighting removal jobs
        self._remove_highlighting()

def create_gui() -> tuple[tk.Tk, ttk.Treeview]:
    """Create and return the Tk root window and configured Treeview widget."""
    root = tk.Tk()
    root.title("TCPViewer")

    columns = ("Process", "ProcessId", "LocalIP", "LocalPort", "RemoteIP",
               "RemotePort", "Hostname", "Status", "Family", "Type")
    tree = ttk.Treeview(root, columns=columns, show="headings")

    # Set column widths for better display
    column_widths = {
        "Process": 150,
        "ProcessId": 80,
        "LocalIP": 120,
        "LocalPort": 80,
        "RemoteIP": 120,
        "RemotePort": 80,
        "Hostname": 150,
        "Status": 100,
        "Family": 80,
        "Type": 80
    }

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=column_widths.get(col, 100))

    tree.pack(fill="both", expand=True)
    return root, tree

def main() -> None:
    """Entrypoint to create the UI and start the main loop."""
    root, tree = create_gui()
    # Create the viewer with required arguments
    viewer = TcpViewer(root, tree)

    # Set up cleanup on window close
    def on_closing():
        viewer.cleanup()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
