# Handling Large .grd Files - Quick Guide

## IMPORTANT: Run Inspector First!

Before doing ANYTHING, you MUST identify the correct file format:

```bash
cd backend
python inspect_grd.py "your_file.grd"
```

This will show which format your file uses.

---

## Approach 1: Auto-Format Detection (Recommended)

The main parser now auto-detects format:

```bash
python app.py
# Upload file through web interface - it will auto-detect format
```

---

## Approach 2: Chunked Processing (For Very Large Files)

If your file is truly massive (>500MB) or causing memory issues:

```bash
cd backend
python chunked_grd_parser.py "your_file.grd"
```

This will:
- Process file in 500-row chunks
- Calculate statistics without loading entire file
- Export to CSV in chunks (memory efficient)

**Benefits:**
- Uses minimal RAM (only loads 500 rows at a time)
- Works on files of ANY size
- Shows progress as it processes

**When to use:**
- File size > 500MB
- Getting memory errors
- Want to process very high-resolution grids

---

## Your File (25MB) Analysis

Your file is 25MB with 6.3 million values.

**This is NOT a large file** - Python can handle this easily in memory.

**Possible structures:**

1. **Single high-res grid:** 2525 x 2525 cells
2. **Multiple timesteps:** 135 x 129 cells × many days
3. **Different format:** Need inspector to confirm

**Next step:** Run the inspector to reveal actual structure!

---

## Quick Commands

**1. Inspect format:**
```bash
python inspect_grd.py "rainfall.grd"
```

**2. Normal processing (auto-detect):**
```bash
python app.py
# Use web interface
```

**3. Chunked processing (if needed):**
```bash
python chunked_grd_parser.py "rainfall.grd"
```

---

## Common Error Solutions

**Error: "ncols=-999, nrows=-999"**
→ Wrong header format. Run inspector first!

**Error: "Memory error"**
→ File is truly huge. Use chunked_grd_parser.py

**Error: "Data size mismatch"**
→ Format detection failed. Share inspector output for help.
