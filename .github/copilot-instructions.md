# TCP Viewer - GitHub Copilot Instructions

TCP Viewer is a Python desktop application built with Tkinter that displays current TCP/UDP network connections using the psutil library. It provides a GUI interface for inspecting network connections on the local machine.

**ALWAYS REFERENCE THESE INSTRUCTIONS FIRST** and fallback to search or bash commands only when you encounter unexpected information that does not match the information here.

## Working Effectively

### Initial Setup and Dependencies
- **Python Version**: Requires Python 3.12 or newer (confirmed working with Python 3.12.3)
- **Core Dependency**: Only one runtime dependency - `psutil`
- **Development Dependencies**: `pylint` for code quality checking

### Build and Run Methods

#### Method 1: UV Package Manager (Recommended, but may not be available)
```bash
# Test if uv is available
which uv
# If uv is available:
uv sync                    # Install dependencies (~5-10 seconds)
uv run python main.py      # Run the application
```
**NOTE**: UV may not be available in all environments due to network restrictions or missing installation.

#### Method 2: Virtual Environment + Pip (Fallback Method - WORKS WITH INTERNET ACCESS)
```bash
# Create virtual environment (takes ~3 seconds)
python -m venv .venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\Activate.ps1

# Upgrade pip (takes ~2-3 seconds, requires internet)
python -m pip install --upgrade pip

# Install runtime dependency (takes ~6-8 seconds, requires internet)
pip install psutil

# Run the application
python main.py
```

**Network Requirements**: 
- Pip install commands require internet access to PyPI
- In environments with network restrictions, pip may fail with timeout errors
- If pip fails due to network issues, document the limitation in your instructions

### Linting and Code Quality
```bash
# Install pylint for development (takes ~8-10 seconds, requires internet)
pip install pylint

# Run pylint on all Python files (takes ~1-2 seconds)
pylint $(git ls-files '*.py')
# Alternative single file:
pylint main.py
```

**Note**: If pylint is not installed due to network issues, you can still validate syntax with:
```bash
python -m py_compile main.py
```

**Pylint Configuration**:
- Uses `.pylintrc` for configuration
- Max line length: 100 characters
- Ignores: venv, .venv, env, .env, __pycache__
- Good names: ip, pid
- Current code rating: 8.03/10 (has some style issues but functional)

### Validation and Testing

#### Import and Syntax Testing
```bash
# Test Python imports without GUI (useful for headless environments)
python -c "import psutil; print('✓ psutil imported successfully')"

# Test syntax compilation
python -m py_compile main.py
```

#### Application Testing
**IMPORTANT**: The application requires a graphical environment to run because it uses Tkinter. In headless environments, it will fail with:
```
ModuleNotFoundError: No module named 'tkinter'
```

**Manual Testing Scenarios** (when GUI is available):
1. **Launch Application**: Run `python main.py` and verify the GUI opens
2. **Basic Functionality**: Click "Refresh" button to reload connections
3. **Filter Testing**: Use the filter box with examples like:
   - `name:chrome` (filter by process name)
   - `lport:80` (filter by local port)
   - `status:ESTABLISHED` (filter by connection status)
4. **Auto-Refresh**: Test "Start Auto Refresh" button for continuous updates
5. **Sorting**: Click column headers to test sorting functionality
6. **Data Display**: Verify all columns show appropriate data:
   - Process name and PID
   - Local and remote IP/port
   - Connection status
   - Address family and socket type

## CI/CD Integration

### GitHub Actions Workflow
The repository includes `.github/workflows/pylint.yml` that:
- Runs on all pushes and pull requests
- Uses Python 3.12
- Installs dependencies: `pip install pylint psutil`
- Executes: `pylint $(git ls-files '*.py')`

### Pre-commit Validation
**Always run before committing changes**:

#### Network-Independent Validation (Always Available)
```bash
# Syntax check (no network required)
python -m py_compile main.py

# Basic structure check
ls -la main.py

# Python version verification
python --version
```

#### Network-Dependent Validation (When Internet Access Available)
```bash
# Import validation (requires psutil)
python -c "import psutil; print('Dependencies OK')"

# Code quality check (requires pylint)
pylint main.py
```

#### If Network/Dependencies Are Not Available
Document in commit message: "Code validated with syntax check only - network dependencies not available for full validation"

## Repository Structure

### Key Files
```
.
├── main.py              # Main application file (single file app)
├── pyproject.toml       # Python project configuration (PEP 621)
├── uv.lock             # UV package manager lock file
├── .pylintrc           # Pylint configuration
├── .python-version     # Python version (3.12)
├── README.md           # User documentation
├── .github/
│   └── workflows/
│       └── pylint.yml  # CI workflow for linting
└── .vscode/
    └── tasks.json      # VS Code tasks for development
```

### Application Architecture
- **Single File Application**: All code is in `main.py` (~582 lines)
- **Main Class**: `TcpViewer` - handles GUI and data management
- **GUI Framework**: Tkinter with ttk (TreeView widget)
- **Data Source**: psutil for network connection information
- **Features**: Filtering, sorting, auto-refresh, change highlighting

## Common Tasks and Troubleshooting

### Environment Issues
- **Missing tkinter**: Normal in headless environments - application cannot run
- **Permission errors on Windows**: Some connection details require Administrator privileges
- **Empty connection list**: Try running with elevated privileges
- **Network/PyPI access issues**: pip install may fail with timeout errors in restricted environments
- **UV not available**: UV package manager may not be installed or accessible

### Development Workflow
1. **Setup**: Use venv+pip method for maximum compatibility
2. **Code Changes**: Edit `main.py` directly
3. **Validation**: Run pylint and syntax checks
4. **Testing**: Manual GUI testing required (cannot be automated easily)

### Performance Notes
- **Virtual environment creation**: ~3 seconds
- **Dependency installation**: ~6-8 seconds for psutil, ~8-10 seconds for pylint
- **Linting**: ~1-2 seconds
- **Application startup**: Immediate (once GUI is available)

## Limitations and Constraints

### Technical Limitations
- **GUI Required**: Cannot run in headless environments
- **Platform Specific**: Some features require elevated privileges on Windows
- **Single File**: All application logic in one file (intentional design)

### Development Constraints
- **No Test Suite**: Application has no automated tests (manual testing only)
- **No Build Process**: Direct Python execution, no compilation step
- **Minimal Dependencies**: Intentionally kept simple with only psutil dependency

## Frequently Used Commands

### Quick Reference Commands
```bash
# Check if UV is available
which uv

# Verify Python version
python --version

# List Python files in repository
git ls-files '*.py'

# Check virtual environment status
ls -la .venv/

# Activate virtual environment (Linux/macOS)
source .venv/bin/activate

# Activate virtual environment (Windows)
.venv\Scripts\Activate.ps1

# Test basic imports without full dependencies
python -c "import sys; print('Python OK')"

# Check if tkinter is available (GUI requirement)
python -c "import tkinter; print('GUI available')" 2>/dev/null || echo "GUI not available (headless)"
```

### Repository Information Commands
```bash
# Show repository structure
find . -name "*.py" -o -name "*.toml" -o -name "*.yml" -o -name "*.md" | grep -v ".venv" | grep -v ".git"

# Check file sizes and modifications
ls -la *.py *.md *.toml

# View git status
git status

# Check current directory
pwd
```

## Tips for Effective Development

### Code Quality
- Follow existing code style (pylint configuration)
- Keep line length under 100 characters
- Use meaningful variable names for IP addresses and PIDs

### Feature Development
- All new features should be added to the `TcpViewer` class
- GUI components use tkinter/ttk
- Network data comes from `psutil.net_connections()`
- Maintain the single-file architecture

### Debugging
- Use pylint to catch common issues
- Test imports separately from GUI components
- Validate psutil functionality independently
- Remember that GUI testing requires manual verification