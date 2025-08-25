## TCP/UDP Connection Viewer (Tkinter)

Small desktop app to inspect current network connections on your machine using psutil, with a simple Tkinter UI.

It shows a table of local IP/port and connection status, with process name and id.

### Features

- Refresh on demand.
- Columns: IP, Port, Status (status may be '-' or N/A for UDP or when unavailable).
- Lightweight: one runtime dependency (psutil).

### Requirements

- Python 3.12 or newer.
- Windows, macOS, or Linux. Notes for Windows: some connection details may require elevated permissions.

### Quick start

You can run this project with either uv (recommended if you have it) or a plain venv + pip.

#### Option A: uv (if installed)

```powershell
# From the repo root
uv sync
uv run python main.py
```

#### Option B: venv + pip

```powershell
# From the repo root
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install psutil
python main.py
```

### Using the app

- Refresh: reloads the current list of connections.
- Table columns:
    - ProcessName: Process Name
    - ProcessId: Process Id
	- IP: Local IP address
	- Port: Local port
	- Status: Connection state (e.g., LISTEN, ESTABLISHED). For UDP, status is typically '-'.
    - Family: socket family like INET, V4, V6
    - Type: Stream vs DGRAM

### Troubleshooting

- Empty or partial list on Windows: Some details require Administrator privileges. Try running your terminal/VS Code as Administrator.
- Permission or AccessDenied errors from psutil: Same as above—elevated privileges are often needed to inspect all sockets.
- No output for UDP: UDP is connectionless; many entries won’t have a meaningful status.
- Python/psutil not found: Ensure your virtual environment is activated and psutil is installed.

### Project layout

- `main.py` — Tkinter UI and psutil integration.
- `pyproject.toml` — Project metadata and dependency declaration (for tooling like uv/PEP 621-aware tools).
- `uv.lock` — Lockfile for uv.

### Ideas and next steps

- Auto-refresh with a configurable interval.
- Filter by state (LISTEN/ESTABLISHED), by port range, or by process.
- Show remote address and PID/process name.
- Export to CSV.

Contributions and suggestions are welcome.
