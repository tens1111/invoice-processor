from fastapi import FastAPI, File, UploadFile
import pdfplumber
from groq import Groq
import io
from dotenv import load_dotenv
import os
import json
from pydantic import BaseModel
from typing import Optional
import sqlite3
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

load_dotenv()


def init_db():
    conn = sqlite3.connect("invoices.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            invoice_number TEXT,
            invoice_date TEXT,
            vendor_name TEXT,
            client_name TEXT,
            total_amount REAL,
            currency TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


init_db()


class InvoiceData(BaseModel):
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    vendor_name: Optional[str] = None
    client_name: Optional[str] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = None


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/ui")
def ui():
    return FileResponse("static/index.html")


@app.get("/")
def root():
    return {"message": "Invoice Processor работает!"}


@app.post("/upload")
async def upload_invoice(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text()
        if not text.strip():
            return {"error": "Не удалось извлечь текст из PDF"}
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        message = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": f"""
Извлеки данные из этого документа и верни ТОЛЬКО JSON без лишних слов.
Нужные поля:
- invoice_number
- invoice_date
- vendor_name
- client_name
- total_amount
- currency
Документ:
{text}
"""}],
        )
        raw = message.choices[0].message.content
        clean = raw.replace("```json", "").replace("```", "").strip()
        parsed = InvoiceData(**json.loads(clean))
        conn = sqlite3.connect("invoices.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO invoices (filename, invoice_number, invoice_date, vendor_name, client_name, total_amount, currency)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            file.filename,
            parsed.invoice_number,
            parsed.invoice_date,
            parsed.vendor_name,
            parsed.client_name,
            parsed.total_amount,
            parsed.currency,
        ))
        conn.commit()
        conn.close()
        return {"filename": file.filename, "invoice_data": parsed}
    except json.JSONDecodeError:
        return {"error": "AI вернул некорректный JSON"}
    except Exception as e:
        return {"error": f"Ошибка: {str(e)}"}


@app.get("/invoices")
def get_invoices():
    conn = sqlite3.connect("invoices.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM invoices")
    columns = [desc[0] for desc in cursor.description]
    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return {"invoices": rows}
