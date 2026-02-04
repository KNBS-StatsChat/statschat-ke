import json
from pathlib import Path


def test_audit_downloads_flags_missing_and_extra(tmp_path, monkeypatch):
    # Arrange: fake workspace CWD so the script uses tmp_path/data and tmp_path/outputs
    monkeypatch.setattr("pathlib.Path.cwd", lambda: tmp_path)
    monkeypatch.setattr(
        "statschat.load_config",
        lambda *a, **k: {"preprocess": {"mode": "UPDATE"}},
    )

    data_dir = tmp_path / "data" / "pdf_downloads"
    data_dir.mkdir(parents=True)

    # url_dict references file1 + file2; only file1 exists
    (data_dir / "url_dict.json").write_text(
        json.dumps(
            {
                "file1.pdf": {
                    "pdf_url": "https://example.com/file1.pdf",
                    "report_page": "https://example.com/report1",
                },
                "file2.pdf": {
                    "pdf_url": "https://example.com/file2.pdf",
                    "report_page": "https://example.com/report2",
                },
            }
        )
    )

    (data_dir / "file1.pdf").write_bytes(b"%PDF-1.4 valid")
    (data_dir / "extra.pdf").write_bytes(b"%PDF-1.4 extra")
    (data_dir / "zero.pdf").write_bytes(b"")
    (data_dir / "html.pdf").write_bytes(b"<html>not a pdf")

    # Act
    from statschat.pdf_processing.audit_downloads import main

    out_path = main()

    # Assert
    payload = json.loads(Path(out_path).read_text())
    assert payload["mode"] == "UPDATE"
    assert payload["directories"], "Expected at least one audited directory"

    findings = payload["directories"][0]["findings"]
    reasons = {(f["filename"], f["reason"]) for f in findings}

    assert ("file2.pdf", "missing_on_disk") in reasons
    assert ("extra.pdf", "extra_on_disk") in reasons
    assert ("zero.pdf", "zero_byte") in reasons
    assert ("html.pdf", "non_pdf_magic") in reasons
