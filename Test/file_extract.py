import json
import logging
import os
import re
import sys
import pdfplumber
import pypdfium2 as pdfium
import ollama

# Suppress noisy pdfminer font warnings
logging.getLogger("pdfminer").setLevel(logging.ERROR)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extracted')
MODEL = 'qwen3.5:4b'

IMAGE_EXTS = {".png", ".jpg", ".jpeg"}
SUPPORTED_EXTS = IMAGE_EXTS | {".pdf"}

# If a PDF yields fewer than this many characters, treat it as a scanned/image
# PDF and fall back to rendering its pages as images for the vision model.
MIN_PDF_TEXT_CHARS = 80

SCHEMA = {
    "full_name":       "Full name of the account holder or employee",
    "bank_account_id": "Bank account number, or BSB + account number",
    "address":         "Mailing or residential address",
    "ytd_income":      "Year-to-date (YTD) gross income from salary and wages. Use the value in the YTD column for the main salary/wages earnings line (for example 9844.15). Do NOT use the single pay-period amount, the YTD grand total that includes other/one-off earnings, or tax/super figures. Null if not a payslip.",
    "credit":          "Total credits or deposits received during the period",
    "liability":       "Total liabilities, debts, or outstanding balance owed (e.g. loan or credit card balance)",
}

# JSON schema passed to Ollama's structured-output `format` to force valid JSON
FORMAT_SCHEMA = {
    "type": "object",
    "properties": {key: {"type": ["string", "null"]} for key in SCHEMA},
    "required": list(SCHEMA),
}

SYSTEM_PROMPT = (
    "You are a financial document parser. "
    "Extract the requested fields from the provided document (a bank statement or payslip). "
    "Respond ONLY with a single valid JSON object. "
    "If a field cannot be found in the document, use null."
)

INSTRUCTION = (
    f"Extract the following fields and return them as JSON. "
    f"Use null for any field not present in the document:\n"
    f"{json.dumps(SCHEMA, indent=2)}"
)


def extract_pdf_text(path: str) -> str:
    pages = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return "\n\n".join(pages)


def render_pdf_to_images(path: str) -> list[bytes]:
    """Render each PDF page to PNG bytes for the vision model (scanned PDFs)."""
    images = []
    pdf = pdfium.PdfDocument(path)
    try:
        for page in pdf:
            bitmap = page.render(scale=2)  # ~144 dpi, good for OCR
            pil_image = bitmap.to_pil()
            from io import BytesIO
            buf = BytesIO()
            pil_image.save(buf, format="PNG")
            images.append(buf.getvalue())
    finally:
        pdf.close()
    return images


def build_message(path: str) -> dict:
    """Build the user message, branching on input type.

    Digital PDF  -> extract text with pdfplumber, send as text.
    Scanned PDF  -> render pages to images, send to vision model.
    Image        -> send the image directly to the vision model.
    """
    ext = os.path.splitext(path)[1].lower()

    if ext == ".pdf":
        pdf_text = extract_pdf_text(path)
        if len(pdf_text) >= MIN_PDF_TEXT_CHARS:
            print(f"  digital PDF — extracted {len(pdf_text)} chars of text")
            return {"role": "user", "content": f"{INSTRUCTION}\n\n--- DOCUMENT TEXT ---\n{pdf_text}"}
        print(f"  scanned PDF (only {len(pdf_text)} chars) — rendering pages as images")
        return {"role": "user", "content": INSTRUCTION, "images": render_pdf_to_images(path)}

    if ext in IMAGE_EXTS:
        print(f"  image ({ext}) — sending to vision model")
        return {"role": "user", "content": INSTRUCTION, "images": [path]}

    raise ValueError(f"Unsupported input type: {ext}")


def parse_json_response(raw: str) -> dict:
    # Strip markdown code fences if the model added them despite instructions
    cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
    return json.loads(cleaned)


def process_file(path: str) -> dict:
    print(f"\n=== {os.path.basename(path)} ===")
    user_message = build_message(path)

    raw_reply = ""
    for chunk in ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            user_message,
        ],
        think=False,                  # disable Qwen3 reasoning so content streams
        format=FORMAT_SCHEMA,         # constrain output to valid JSON
        options={"temperature": 0},   # deterministic output for financial data
        stream=True,
    ):
        token = chunk["message"]["content"]
        print(token, end="", flush=True)
        raw_reply += token
    print()

    try:
        result = parse_json_response(raw_reply)
    except json.JSONDecodeError as e:
        print(f"  !! Could not parse JSON: {e}")
        result = {key: None for key in SCHEMA}

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_name = os.path.splitext(os.path.basename(path))[0] + ".json"
    out_path = os.path.join(OUTPUT_DIR, out_name)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"  -> saved {out_path}")
    return result


def gather_inputs(target: str) -> list[str]:
    if os.path.isdir(target):
        files = [
            os.path.join(target, name)
            for name in sorted(os.listdir(target))
            if os.path.splitext(name)[1].lower() in SUPPORTED_EXTS
        ]
        return files
    return [target]


def main():
    if len(sys.argv) < 2:
        print("Usage: python ollama_extract.py <file-or-folder> [more files/folders ...]")
        sys.exit(1)

    targets = sys.argv[1:]
    files = []
    for t in targets:
        files.extend(gather_inputs(t))

    print(f"Processing {len(files)} file(s) with {MODEL} ...")
    for path in files:
        process_file(path)

    print("\nDone.")


if __name__ == "__main__":
    main()
