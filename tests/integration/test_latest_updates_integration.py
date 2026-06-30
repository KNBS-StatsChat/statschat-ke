"""Integration test for latest_updates name matching and latest flag updates.

This test simulates inbound documents with similar names, exercises the
matching logic, and verifies that former latest documents are unflagged while
their split documents are also updated. It additionally checks that unrelated
series and non-matching split files remain untouched.
"""

import json

from statschat.embedding import latest_updates


def test_latest_updates_unflags_and_updates_splits(tmp_path):
    base_dir = tmp_path / "json_conversions"
    inbound_dir = base_dir / "temp"
    split_dir = tmp_path / "json_split"

    inbound_dir.mkdir(parents=True)
    split_dir.mkdir(parents=True)

    former_name = "2023-Economic-Survey.json"
    new_name = "2024-Economic-Survey.json"
    other_series_name = "2024-Statistical-Abstract.json"

    (base_dir / former_name).write_text(
        json.dumps({"title": "Economic Survey 2023", "latest": True})
    )
    (inbound_dir / new_name).write_text(
        json.dumps({"title": "Economic Survey 2024", "latest": True})
    )
    (base_dir / other_series_name).write_text(
        json.dumps({"title": "Statistical Abstract 2024", "latest": True})
    )

    split_base = former_name.replace(".json", "")
    split_paths = [
        split_dir / f"{split_base}_0.json",
        split_dir / f"{split_base}_1.json",
    ]
    for sp in split_paths:
        sp.write_text(
            json.dumps({"page_text": "chunk", "latest": True, "source": str(sp)})
        )
    unaffected_split = split_dir / "2019-Other-Report_0.json"
    unaffected_split.write_text(
        json.dumps(
            {"page_text": "chunk", "latest": True, "source": str(unaffected_split)}
        )
    )

    latest_filepaths = latest_updates.find_latest(str(base_dir))
    new_latest, former_latest = latest_updates.compare_latest(
        str(base_dir), latest_filepaths
    )

    assert new_name in new_latest
    assert former_name in former_latest
    assert other_series_name not in former_latest
    assert len(new_latest) == len(set(new_latest))
    assert len(former_latest) == len(set(former_latest))

    latest_updates.unflag_former_latest(str(base_dir), former_latest)
    updated = json.loads((base_dir / former_name).read_text())
    assert updated["latest"] is False

    latest_updates.update_split_documents(str(split_dir), former_latest)
    for sp in split_paths:
        split_doc = json.loads(sp.read_text())
        assert split_doc["latest"] is False

    assert json.loads(unaffected_split.read_text())["latest"] is True
