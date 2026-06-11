# File Extraction Model

A local AI-powered tool that extracts structured financial data from bank statements, payslips, and related documents (PDF or image). It runs entirely on-device using [Ollama](https://ollama.com/) — no data leaves your machine.

---

## What it does

Given one or more PDFs or images, the script outputs a JSON file per document containing:

| Field | Description |
|---|---|
| `full_name` | Account holder or employee name |
| `bank_account_id` | Bank account number or BSB + account |
| `address` | Mailing or residential address |
| `ytd_income` | Year-to-date gross income (payslips only) |
| `credit` | Total credits / deposits for the period |
| `liability` | Total liabilities or outstanding balance |

Unsupported fields are returned as `null`.

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.10+ |
| [Ollama](https://ollama.com/download) | latest |
| Ollama model | `qwen2.5:7b` or any multimodal model |

### Python packages

```bash
pip install pdfplumber pypdfium2 ollama
```

---

## Setup

### 1. Install Ollama

Download and install from https://ollama.com/download, then pull the model used by the script:

```bash
ollama pull qwen2.5:4b
```

> The model name is set at the top of `Test/file_extract.py` as `MODEL`. Change it to match whatever model you have pulled locally (e.g. `llava`, `gemma3`, `mistral`). A multimodal model is required for scanned PDFs and image inputs.

### 2. Clone this repo

```bash
git clone https://github.com/maverick001/File_extraction_model.git
cd File_extraction_model
```

### 3. Install Python dependencies

```bash
pip install pdfplumber pypdfium2 ollama
```

---

## Usage

Run the script from the repo root (or any directory — output always goes to `Test/extracted/`):

```bash
python Test/file_extract.py <file-or-folder> [more files/folders ...]
```

### Examples

**Single file:**
```bash
python Test/file_extract.py "Samples/Payslip/08421_Payslip_15-AUG-2025.pdf"
```

**Entire folder:**
```bash
python Test/file_extract.py Samples/BankStatement
```

**Multiple folders at once:**
```bash
python Test/file_extract.py Samples/BankStatement Samples/Payslip Samples/Equifax
```

### Output

JSON files are written to `Test/extracted/<original-filename>.json`. Example:

```json
{
  "full_name": "Michael Gobbie",
  "bank_account_id": null,
  "address": "12 Example St, Sydney NSW 2000",
  "ytd_income": "9844.15",
  "credit": null,
  "liability": null
}
```

---

## Sample documents

The `Samples/` directory contains test documents organised by type:

```
Samples/
├── BankStatement/   # NAB, Mastercard statements (PDF + PNG)
├── Payslip/         # Various payslip formats (PDF + image)
└── Equifax/         # Credit report PDFs
```

> `Samples/ID/` is excluded from this repo for privacy reasons.

---

## How the script handles different inputs

| Input type | Behaviour |
|---|---|
| Digital PDF (text-selectable) | Text is extracted with `pdfplumber` and sent to the LLM as plain text — fast and accurate |
| Scanned PDF (image-only) | Pages are rendered to PNG at 144 dpi and sent to the vision model |
| PNG / JPG / JPEG | Image is sent directly to the vision model |

The threshold for switching from text to vision mode is controlled by `MIN_PDF_TEXT_CHARS` (default: 80 characters extracted).

---

## Project structure

```
File_extraction_model/
├── Test/
│   └── file_extract.py      # Main extraction script
├── Samples/
│   ├── BankStatement/
│   ├── Payslip/
│   └── Equifax/
├── .gitignore
└── README.md
```

---

## Troubleshooting

**`ollama.ResponseError: model not found`** — Run `ollama pull <model-name>` to download the model first.

**JSON parse errors** — The model occasionally wraps output in markdown fences despite instructions. The script strips these automatically; if it still fails, try a larger/different model.

**Scanned PDF renders blank** — Ensure `pypdfium2` is installed (`pip install pypdfium2`).
