# Passport PDF Generation System

**Purpose:** Generate PDF scans from passport photos
**Location:** `../../../passport/` (relative to Claude Tools root)
**Status:** Utility script for document processing

---

## ⚠️ Complete Files Location

Full system files are located in:
```
C:\Users\tnguyen24_mantu\OneDrive\Claude Tools\passport\
```

**This README is a navigation guide only.**

---

## System Overview

Simple Python utility to:
1. Convert passport photos (HEIC format) to JPEG previews
2. Generate PDF scans from passport images
3. Optimize file size for digital storage/transmission

---

## Files in Passport Folder

### Script
**`create_passport_pdf.py`**
- Python script for PDF generation
- Handles HEIC to JPG conversion
- Creates optimized PDF output

### Input Files
- `IMG_9918.HEIC` - Original passport photo (HEIC format)
- `IMG_9918_preview.jpg` - JPEG preview
- `Photos-1-001.zip` - Archived photo backup

### Output
- `passport_scan.pdf` - Generated PDF scan

---

## File Size

PDF output is optimized:
- **File size:** Compressed for reasonable file size (check actual size in folder)
- **Format:** Standard PDF compatible with most viewers
- **Quality:** Balanced for readability vs file size

---

## Usage

```bash
cd "C:\Users\tnguyen24_mantu\OneDrive\Claude Tools\passport"
python create_passport_pdf.py
```

Expected output: `passport_scan.pdf`

---

## Related Systems

**Not related to:**
- Glass cutting systems (Oceanside/Bullseye)
- FEIE tax tracking
- Wildcats SEO content

**This is a standalone utility** for personal document management.

---

**Last Updated:** Based on file timestamps in folder
**Type:** Utility script (not an ongoing business system)
