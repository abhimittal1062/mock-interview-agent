# Python 3.11 Setup

Use Python 3.11 for this project. The current recommended version is:

```powershell
py -3.11 --version
```

Expected:

```text
Python 3.11.9
```

Recommended: create the virtual environment outside OneDrive to avoid Windows/OneDrive file-lock issues during large package installs:

```powershell
cd "C:\Users\dellc\OneDrive\Desktop\PROJECTS\mock-interview-agent"
py -3.11 -m venv C:\tmp\mock-interview-agent-venv311
C:\tmp\mock-interview-agent-venv311\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Run the app:

```powershell
python -m uvicorn app.main:app --reload
```

For DSA sample-test execution, install `g++` and make sure it is on `PATH`.
If it is not on `PATH`, set `CXX_COMPILER` in `.env`:

```env
CXX_COMPILER=C:\path\to\g++.exe
```

Open:

```text
http://127.0.0.1:8000
```

For VS Code:

1. Press `Ctrl+Shift+P`.
2. Select `Python: Select Interpreter`.
3. Choose `C:\tmp\mock-interview-agent-venv311\Scripts\python.exe`.

Notes:

- `runtime.txt` pins hosted environments to Python 3.11.9 where supported.
- `Dockerfile` already uses Python 3.11.
- Python 3.14 is not recommended for this project because some packages such as LangGraph and Playwright may not publish wheels for it yet.
