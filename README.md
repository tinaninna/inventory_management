# Inventory Management System

This project represents component and project Bill of Materials (BOM) requirements. It does not contain actual stock quantities, inventory transactions, reorder levels, purchase orders, or supplier data.

## Run locally

```powershell
backend\.venv\Scripts\uvicorn.exe backend.main:app --host 127.0.0.1 --port 8000
python -m http.server 5173 --directory frontend
```

Open `http://127.0.0.1:5173`. API documentation is at `http://127.0.0.1:8000/docs`.