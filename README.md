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

## Deploy Live

This repo includes a `Dockerfile` and `render.yaml` for Render.

1. Push the repo to GitHub.
2. Open Render and choose **New > Blueprint**.
3. Connect this repo: `aryankushwaha28/prototech-cnc-intelligence`.
4. Render will detect `render.yaml` and create the web service.
5. Use a paid `starter` web service for an always-on public URL. Free services may sleep.
6. Optional: add `ANTHROPIC_API_KEY` in Render environment variables to enable Claude analysis.

The public app URL will look like:

```text
https://prototech-cnc-intelligence.onrender.com
```

## Notes

Generated G-code is for simulator validation and estimating workflow only. A qualified machinist must review it before any production machine use.
