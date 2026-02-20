"""Migrate a saved FAISS vector store between directories.

Purpose
-------
In some local runs the embedding pipeline can persist the FAISS index under a
nested path like `data/data/db_langchain` (e.g. when `data_dir="data/"` is
combined with `faiss_db_root="data/db_langchain"`).

This script copies (default) or moves the LangChain FAISS artifacts so both the
embedding pipeline and the query path agree on a single location.

Typical usage
-------------
Copy nested -> canonical:

    /path/to/.venv/bin/python scripts/migrate_faiss_db.py \
        --src data/data/db_langchain --dst data/db_langchain

Move instead of copy:

    /path/to/.venv/bin/python scripts/migrate_faiss_db.py \
        --src data/data/db_langchain --dst data/db_langchain --move

Notes
-----
- This only migrates `index.faiss` and `index.pkl`.
- Use `--force` to overwrite destination files.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


FAISS_FILES = ("index.faiss", "index.pkl")


def _copy_or_move_file(src: Path, dst: Path, *, move: bool) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if move:
        shutil.move(str(src), str(dst))
    else:
        shutil.copy2(src, dst)


def migrate_faiss_db(*, src_dir: Path, dst_dir: Path, move: bool, force: bool) -> None:
    missing = [name for name in FAISS_FILES if not (src_dir / name).exists()]
    if missing:
        raise FileNotFoundError(
            f"Source directory is missing required files: {missing}. "
            f"src_dir={src_dir}"
        )

    dst_dir.mkdir(parents=True, exist_ok=True)

    for name in FAISS_FILES:
        src = src_dir / name
        dst = dst_dir / name

        if dst.exists() and not force:
            raise FileExistsError(
                f"Destination file already exists: {dst}. " "Use --force to overwrite."
            )

        if dst.exists() and force:
            dst.unlink()

        _copy_or_move_file(src, dst, move=move)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--src",
        type=Path,
        default=Path("data/data/db_langchain"),
        help="Source FAISS directory (contains index.faiss + index.pkl)",
    )
    parser.add_argument(
        "--dst",
        type=Path,
        default=Path("data/db_langchain"),
        help="Destination FAISS directory",
    )
    parser.add_argument(
        "--move",
        action="store_true",
        help="Move files instead of copying",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite destination files if they exist",
    )

    args = parser.parse_args()
    migrate_faiss_db(
        src_dir=args.src, dst_dir=args.dst, move=args.move, force=args.force
    )
    action = "Moved" if args.move else "Copied"
    print(f"{action} FAISS store: {args.src} -> {args.dst}")


if __name__ == "__main__":
    main()
