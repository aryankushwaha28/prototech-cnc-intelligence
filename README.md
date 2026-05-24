# ProtoTech CNC Intelligence

Local-first MVP that accepts a DXF file and generates:

- A structured CNC quote
- A PDF quote
- A simulator-focused Fanuc-style `.nc` program

## Run Locally

```powershell
.venv\Scripts\python.exe scripts\generate_fixtures.py
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Open `http://127.0.0.1:8000`.

## Notes

Generated G-code is for simulator validation and estimating workflow only. A qualified machinist must review it before any production machine use.
