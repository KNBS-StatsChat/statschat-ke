## How to Update the PDF Database

This guide explains how to add new KNBS PDF publications to the StatsChat database.

---

## Quick Start

### 1. Set the mode to UPDATE

Edit `statschat/config/main.toml`:

```toml
[preprocess]
mode = "UPDATE"  # Must be "UPDATE" not "SETUP"
```

### 2. Run the update script

```shell
python statschat/pdf_runner.py
```

That's it! The script will automatically:
- Scrape the latest PDFs from the KNBS website
- Compare with existing PDFs to find new ones
- Convert new PDFs to JSON
- Update the vector database
- Clean up temporary files

---

## Understanding SETUP vs UPDATE Mode

| Aspect | SETUP Mode | UPDATE Mode |
|--------|------------|-------------|
| **Purpose** | Initial database creation | Add new publications |
| **PDFs processed** | All PDFs in `pdf_downloads/` | Only new PDFs not already in database |
| **Directories used** | `pdf_downloads/`, `json_conversions/` | `latest_pdf_downloads/`, `latest_json_conversions/` |
| **Database action** | Creates new database | Appends to existing database |
| **When to use** | First-time setup or full rebuild | Regular updates (e.g., weekly/monthly) |

---

## How UPDATE Mode Works

UPDATE mode uses "latest_" prefixed directories as a staging area:

```
1. Download    → latest_pdf_downloads/
2. Convert     → latest_json_conversions/  
3. Split       → latest_json_split/
4. Merge       → Appends to main database
5. Cleanup     → Moves files to main folders, clears latest_ folders
```

This ensures the main database is only modified after successful processing.

---

## Detailed Steps (For Development/Debugging)

If you need to run the update process step-by-step (useful for debugging):

### Step 1: Download new PDFs

```shell
python statschat/pdf_processing/pdf_downloader.py
```

Downloads newest PDF files into `latest_pdf_downloads/`. Compares with existing PDFs and only keeps new ones.

### Step 2: Convert and embed

```shell
python statschat/embedding/preprocess.py
```

- Converts new PDFs to JSON (`latest_json_conversions/`)
- Splits JSON files (`latest_json_split/`)
- Updates the vector database

### Step 3: Merge files

```shell
python statschat/pdf_processing/merge_database_files.py
```

Moves files from `latest_*` directories to main directories:
- `latest_pdf_downloads/` → `pdf_downloads/`
- `latest_json_conversions/` → `json_conversions/`
- `latest_json_split/` → `json_split/`

Then clears the `latest_*` directories for the next run.

---

## How Duplicate Detection Works

**PDFs that have already been downloaded will NOT be downloaded again.**

The system tracks all downloaded PDFs in `pdf_downloads/url_dict.json`. Each entry contains:

```json
{
  "Report-Name.pdf": {
    "pdf_url": "https://www.knbs.or.ke/.../Report-Name.pdf",
    "report_page": "https://www.knbs.or.ke/reports/report-name/"
  }
}
```

### During UPDATE mode:

1. **Scrapes** PDF links from the KNBS website (pages 1-5 by default)
2. **Loads** existing URLs from `url_dict.json`
3. **Compares** each scraped URL against existing URLs
4. **Downloads only** PDFs whose URL is not already in the dictionary
5. **Exits early** if no new PDFs are found

### The comparison is based on:

- The **PDF URL** (e.g., `https://www.knbs.or.ke/.../report.pdf`)
- NOT the filename alone

This means:
- ✅ Same PDF won't be re-downloaded
- ✅ If KNBS uploads a new version with the same filename but different URL, it will be detected
- ✅ Efficient - only processes genuinely new publications

---

## Configuration Options

In `statschat/config/main.toml`:

```toml
[app]
page_start = 1    # Start page for KNBS website scraping (1 = newest)
page_end = 5      # End page (UPDATE mode typically only needs 1-5)
```

For UPDATE mode, pages 1-5 usually capture all recent publications. Increase `page_end` if you've missed several update cycles.

---

## Troubleshooting

**"No new PDFs to process"**
- This is normal if there are no new publications since last update
- Check the KNBS website to confirm new publications exist

**Tests failing with "No PDFs found in latest_pdf_downloads"**
- This is expected when `latest_*` directories are empty
- Tests will skip gracefully - this is not an error
- Run in SETUP mode or populate directories to run full tests

**Files stuck in latest_* directories**
- Run `merge_database_files.py` to complete the update cycle
- Or manually move files and clear the directories
