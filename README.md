# AI Invoice Processor

Extract structured data from PDF invoices automatically using AI.

## The Problem

Processing invoices manually is slow, expensive, and error-prone. This tool automates the entire process — upload a PDF, get clean JSON back in seconds.

## How it works

1. Upload a PDF invoice via REST API
2. Text is extracted from the PDF
3. AI (Llama 3.3 via Groq) analyzes the document
4. Returns structured JSON with invoice data
5. Data is saved to a local database

## Quick Start

```bash
git clone https://github.com/tens1111/invoice-processor
cd invoice-processor
pip install -r requirements.txt
```

Create a `.env` file:
```
GROQ_API_KEY=your_key_here
```

Run:
```bash
uvicorn main:app --reload
```

Open http://localhost:8000/docs

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /upload | Upload PDF invoice |
| GET | /invoices | List all processed invoices |

## Get a free API key

Sign up at https://console.groq.com — no credit card required.
