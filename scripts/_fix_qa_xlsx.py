"""Temporary script to:
1. Inspect v2 file
2. Fix date prefixes & filenames in v2
3. Delete Q001/Q002 rows from both v1 and v2
4. Cross-check v2 against v1
5. Verify all filenames match pdf_downloads
"""

import os
import re

import openpyxl

BASE = "/Users/gregdunlop/projects2/statschat-ke"
V1_PATH = f"{BASE}/tests/accuracy/KNBS_Verified_QA_Examples_updated.xlsx"
V2_PATH = f"{BASE}/tests/accuracy/KNBS_Verified_QA_Examples_updated_v2.xlsx"
PDF_DIR = f"{BASE}/data/pdf_downloads"

DATE_PREFIX = re.compile(r"\d{4}/\d{2}/")
RENAME_MAP = {
    "2023-24-Kenya-Housing-Survey-Basic-Report.pdf": "2023-24-Kenya-Housing-Survey-Basic-Report1.pdf",
    "2023-24-Real-Estate-Survey-Report.pdf": "2023-24-Real-Estate-Survey-Report_1.pdf",
}

pdf_files = set(os.listdir(PDF_DIR))


def fix_cell(value):
    if not value or not isinstance(value, str):
        return value, False
    changed = False
    parts = value.split(";")
    fixed = []
    for part in parts:
        original = part
        part = DATE_PREFIX.sub("", part)
        for old_name, new_name in RENAME_MAP.items():
            part = part.replace(old_name, new_name)
        if part != original:
            changed = True
        fixed.append(part)
    return ";".join(fixed), changed


def get_col_indices(ws):
    headers = [cell.value for cell in ws[1]]
    return (
        headers.index("relevant_doc_ids") + 1,
        headers.index("evidence_locations") + 1,
        headers,
    )


def dump_rows(ws, label):
    """Print all rows for inspection."""
    headers = [cell.value for cell in ws[1]]
    doc_col = headers.index("relevant_doc_ids")
    ev_col = headers.index("evidence_locations")
    print(f"\n=== {label}: {ws.max_row - 1} data rows ===")
    for i, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        print(f"  Row {i}: {row[0]}  doc_ids={row[doc_col]}  ev_locs={row[ev_col]}")


def fix_date_prefixes(ws, label):
    """Strip date prefixes and apply renames. Returns change count."""
    doc_idx, ev_idx, _ = get_col_indices(ws)
    changes = 0
    for row_num in range(2, ws.max_row + 1):
        for col_idx in (doc_idx, ev_idx):
            cell = ws.cell(row=row_num, column=col_idx)
            new_val, changed = fix_cell(cell.value)
            if changed:
                col_name = "doc_ids" if col_idx == doc_idx else "ev_locs"
                qid = ws.cell(row=row_num, column=1).value
                print(
                    f"  {label} Row {row_num} ({qid}) {col_name}: {cell.value!r} -> {new_val!r}"
                )
                cell.value = new_val
                changes += 1
    return changes


def delete_rows_by_qid(ws, qids_to_delete):
    """Delete rows matching given query_ids. Deletes from bottom up."""
    rows_to_delete = []
    for row_num in range(2, ws.max_row + 1):
        qid = ws.cell(row=row_num, column=1).value
        if qid in qids_to_delete:
            rows_to_delete.append(row_num)
    for row_num in reversed(rows_to_delete):
        qid = ws.cell(row=row_num, column=1).value
        print(f"  Deleting row {row_num} ({qid})")
        ws.delete_rows(row_num)
    return len(rows_to_delete)


def verify_filenames(ws, label):
    """Check all doc_ids match files in pdf_downloads."""
    doc_idx, ev_idx, _ = get_col_indices(ws)
    all_ok = True
    for row_num in range(2, ws.max_row + 1):
        qid = ws.cell(row=row_num, column=1).value
        for col_idx, col_name in [(doc_idx, "doc_id"), (ev_idx, "ev_loc")]:
            val = ws.cell(row=row_num, column=col_idx).value
            if not val:
                continue
            for part in val.split(";"):
                part = part.strip()
                fname = part.split(" p.")[0].split(":p.")[0].strip()
                if fname and fname not in pdf_files:
                    print(
                        f"  MISSING: {label} Row {row_num} ({qid}) {col_name} '{fname}'"
                    )
                    all_ok = False
    return all_ok


def cross_check(ws_v1, ws_v2):
    """Compare shared query_ids between v1 and v2."""

    def rows_by_qid(ws):
        headers = [cell.value for cell in ws[1]]
        doc_col = headers.index("relevant_doc_ids")
        ev_col = headers.index("evidence_locations")
        result = {}
        for row in ws.iter_rows(min_row=2, values_only=True):
            qid = row[0]
            if qid is None:
                continue
            result[qid] = (row[doc_col], row[ev_col])
        return result

    v1_data = rows_by_qid(ws_v1)
    v2_data = rows_by_qid(ws_v2)
    shared = set(v1_data) & set(v2_data)
    mismatches = 0
    for qid in sorted(shared):
        if v1_data[qid] != v2_data[qid]:
            print(f"  DIFF {qid}:")
            print(f"    v1 doc_ids: {v1_data[qid][0]}")
            print(f"    v2 doc_ids: {v2_data[qid][0]}")
            print(f"    v1 ev_locs: {v1_data[qid][1]}")
            print(f"    v2 ev_locs: {v2_data[qid][1]}")
            mismatches += 1
    v1_only = set(v1_data) - set(v2_data)
    v2_only = set(v2_data) - set(v1_data)
    if v1_only:
        print(f"  query_ids only in v1: {sorted(v1_only)}")
    if v2_only:
        print(f"  query_ids only in v2: {sorted(v2_only)}")
    return mismatches


# --- Main ---
print("=" * 60)
print("STEP 1: Fix date prefixes & filenames in v2")
print("=" * 60)
wb_v2 = openpyxl.load_workbook(V2_PATH)
ws_v2 = wb_v2.active
n = fix_date_prefixes(ws_v2, "v2")
print(f"  v2 changes: {n}")

print("\n" + "=" * 60)
print("STEP 2: Delete Q001/Q002 from both files")
print("=" * 60)
wb_v1 = openpyxl.load_workbook(V1_PATH)
ws_v1 = wb_v1.active
print("  v1:")
d1 = delete_rows_by_qid(ws_v1, {"Q001", "Q002"})
print(f"  v1 deleted: {d1}")
print("  v2:")
d2 = delete_rows_by_qid(ws_v2, {"Q001", "Q002"})
print(f"  v2 deleted: {d2}")

# Save immediately after mutations
wb_v1.save(V1_PATH)
print(f"\n  Saved v1: {V1_PATH}")
wb_v2.save(V2_PATH)
print(f"  Saved v2: {V2_PATH}")

print("\n" + "=" * 60)
print("STEP 3: Cross-check v2 against v1")
print("=" * 60)
m = cross_check(ws_v1, ws_v2)
if m == 0:
    print("  All shared query_ids match between v1 and v2")
else:
    print(f"  {m} mismatches found")

print("\n" + "=" * 60)
print("STEP 4: Verify all filenames match pdf_downloads")
print("=" * 60)
print("  v1:")
ok1 = verify_filenames(ws_v1, "v1")
print("  v1: ALL OK" if ok1 else "  v1: has MISSING files")
print("  v2:")
ok2 = verify_filenames(ws_v2, "v2")
print("  v2: ALL OK" if ok2 else "  v2: has MISSING files")

print("\n" + "=" * 60)
print("STEP 5: Final state")
print("=" * 60)
dump_rows(ws_v1, "v1 FINAL")
dump_rows(ws_v2, "v2 FINAL")
