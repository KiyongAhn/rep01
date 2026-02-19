---
name: pdf_processor
description: Process PDF files - read, extract text/tables, merge, split, rotate pages, add watermarks, create new PDFs, and encrypt/decrypt
---

# PDF Processor Skill

Based on the [Anthropic official pdf skill](https://github.com/anthropics/skills/tree/main/skills/pdf).

## Purpose
Process PDF files: read/extract text and tables, merge multiple PDFs, split
pages, rotate, add watermarks, create new PDFs, and encrypt/decrypt.

## Parameters
- `operation`: The operation to perform. One of:
  - `extract_text` - Extract text from a PDF
  - `extract_tables` - Extract tables from a PDF
  - `extract_metadata` - Extract metadata (title, author, etc.)
  - `merge` - Merge multiple PDFs into one
  - `split` - Split a PDF into individual page files
  - `rotate` - Rotate pages in a PDF
  - `create` - Create a new PDF from content
  - `encrypt` - Add password protection
  - `add_watermark` - Add watermark to pages
- `input_path`: Path to the input PDF file (required for most operations).
- `input_paths`: List of PDF paths (for `merge` operation).
- `output_path`: Path for the output file.
- `pages`: (optional) List of page numbers to process (0-indexed). All pages if omitted.
- `rotation_degrees`: (optional) Degrees to rotate (for `rotate`). Default: 90.
- `content`: (optional) Dict with content for `create` operation:
  - `title`: Document title
  - `body`: List of paragraph strings
- `password`: (optional) Password string (for `encrypt`).
- `watermark_text`: (optional) Watermark text (for `add_watermark`).

## Output
Returns a dict with:
- `status`: `"success"` or `"error"`
- Operation-specific keys (e.g. `text`, `tables`, `metadata`, `output_path`, `page_count`)
