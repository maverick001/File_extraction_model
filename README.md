# File Extraction Model

A local AI-powered tool that extracts structured financial data from bank statements, payslips, and related documents (PDF or image). It runs entirely on-device using [Ollama](https://ollama.com/) — no data leaves your machine.

---

## What it does

Given one or more PDFs or PNG/JPG files, the script outputs a JSON file per document containing:

| Field | Description |
|---|---|
| `full_name` | Account holder or employee name |
| `bank_account_id` | Bank account number or BSB + account |
| `address` | Mailing or residential address |
| `ytd_income` | Year-to-date gross income (payslips only) |
| `credit` | Total credits / deposits for the period |
| `liability` | Total liabilities or outstanding balance |

Fields that can't be found are returned as `null`.

---

## Prerequisites

| Requirement | Version / Notes |
|---|---|
| Python | 3.10+ |
| `tkinter` | Bundled with Python on Windows/macOS. On Linux: `sudo apt install python3-tk` |
| [Ollama](https://ollama.com/download) | latest |
| Ollama model | `qwen3.5:4b` (must be multimodal for image/scanned-PDF support) |

> The model name is set at the top of `Test/file_extract.py` as the `MODEL` constant
> (currently `qwen3.5:4b`). If you pull a different model, update `MODEL` to match.
> A **multimodal** model is required for scanned PDFs and image inputs.

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/maverick001/File_extraction_model.git
cd File_extraction_model
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

> On Linux, also install the tkinter system package if you want the interactive
> file picker: `sudo apt install python3-tk`.

### 3. Install Ollama and pull the model

Download and install Ollama from https://ollama.com/download, then pull the model
referenced by `MODEL`:

```bash
ollama pull qwen3.5:4b
```

Make sure the Ollama service is running (it starts automatically after install;
you can verify with `ollama list`).

---

## Usage

The script can be run **interactively** (a file-picker window) or with **command-line
arguments**. Output always goes to `Test/extracted/`.

### Interactive mode (no arguments)

```bash
python Test/file_extract.py
```

A small launcher window opens with two choices:

- **Select Files** — pick one or more individual documents.
- **Select Folder** — process every supported file (`.pdf`, `.png`, `.jpg`, `.jpeg`)
  in a folder.

### Command-line mode

Pass any mix of files and folders. Folders are scanned for supported files.

```bash
python Test/file_extract.py <file-or-folder> [more files/folders ...]
```

**Single file:**
```bash
python Test/file_extract.py "Samples/Customer_1/blake payslip 1.png"
```

**Entire folder:**
```bash
python Test/file_extract.py Samples/Customer_1
```

**Multiple folders at once:**
```bash
python Test/file_extract.py Samples/Customer_1 Samples/Customer_2
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

Sample documents live under `Samples/`. For privacy, **most sample folders are
excluded from version control** — only the `Samples/Customer_*` folders are committed,
so those are the ones you'll have after cloning:

```
Samples/
├── Customer_1/   # payslips (PNG)
└── Customer_2/   # bank statement (PNG)
```

> `.gitignore` ignores everything under `Samples/` except `Samples/Customer_*`.
> Drop your own test documents into any `Samples/Customer_*` folder (or anywhere
> on disk) and point the script at them.

---

## How the script handles different inputs

| Input type | Behaviour |
|---|---|
| Digital PDF (text-selectable) | Text is extracted with `pdfplumber` and sent to the LLM as plain text — fast and accurate |
| Scanned PDF (image-only) | Pages are rendered to PNG at ~144 dpi and sent to the vision model |
| PNG / JPG / JPEG | Image is sent directly to the vision model |

The threshold for switching from text to vision mode is controlled by
`MIN_PDF_TEXT_CHARS` (default: 80 characters extracted).

---

## Project structure

```
File_extraction_model/
├── Test/
│   ├── file_extract.py      # Main extraction script
│   └── extracted/           # JSON output (created on first run)
├── Samples/
│   ├── Customer_1/
│   └── Customer_2/
├── .gitignore
└── README.md
```

---

## Troubleshooting

**`ollama.ResponseError: model not found`** — Run `ollama pull <model-name>` to download the model first, and confirm `MODEL` in `file_extract.py` matches what you pulled.

**Launcher window doesn't open / `ModuleNotFoundError: No module named 'tkinter'`** — Install tkinter (`sudo apt install python3-tk` on Linux). On Windows/macOS it ships with the official Python installer. You can always skip the GUI by passing files/folders as command-line arguments.

**JSON parse errors** — The model occasionally wraps output in markdown fences despite instructions. The script strips these automatically; if it still fails, try a larger/different model.

**Scanned PDF renders blank** — Ensure `pypdfium2` is installed (`pip install pypdfium2`).
