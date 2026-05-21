# Skill: Self-Healing & Failure Correction Manual

## Context Trigger Words
- "error", "crash", "DatabaseError", "traceback", "failed", "exception", "broken", "ocr", "tesseract", "easyocr"

## Automated Healing Protocols

### 1. SQLite Schema Mismatches
- **Symptom:** `pandas.errors.DatabaseError: Execution failed on sql '...': no such column: conversion_rate`
- **Resolution Path:**
  1. Verify the column names in `src/database.py` vs the sql query location.
  2. Identify if `conversion_rate` was renamed to `base_conversion_rate` (or vice versa).
  3. Run the database seed script: `python src/seed_activities.py` to recreate/update values.

### 2. Streamlit Page Config / UI Crashes
- **Symptom:** `StreamlitAPIException: set_page_config() can only be called once per app...`
- **Resolution Path:**
  1. Inspect the sub-page causing the crash (under `src/pages/`).
  2. Find and delete the duplicate `st.set_page_config` call.
  3. Ensure it only resides in `src/app.py`.

### 3. OCR and Scanned PDF Failures
- **Symptom:** `extract_pdf.py` exports 0 characters because the PDF is a scan, or `easyocr` installation fails due to Rust compilation errors.
- **Resolution Path:**
  1. Avoid installing high-risk heavy packages (`easyocr`, `torch`) via pip inside the sandbox if they fail.
  2. Fall back to extracting PDF text using `PyMuPDF` if native, or use the clean manual reference `Quy định chế độ làm việc đối với nhà giáo (Bản chuẩn toàn văn).md`.
  3. For OCR on Windows, recommend running `install_tesseract.ps1` to configure the system Tesseract binary.

### 4. Zero Lines Mutated
- **Symptom:** Execution runs successfully but `git diff` shows no files modified.
- **Resolution Path:**
  1. Inspect the source file path targets (verify if editing `src/` files directly or working on `app_build/` without syncing changes back).
  2. Check for write permissions.
