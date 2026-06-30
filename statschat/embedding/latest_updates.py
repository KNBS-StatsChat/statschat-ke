import glob
import json
import os
from rapidfuzz import fuzz


def find_latest(dir) -> list[str]:
    """Find all 'latest' publications in document store
    Args:
        dir(str): main bulletins directory
    Returns:
        latest_filepaths(list): list of paths to documents
            currently flagged as 'latest=True'
    """
    latest_filepaths = []
    for filepath in glob.glob(f"{dir}/*.json"):
        # Check for "0000" in filename only, not full path
        filename = os.path.basename(filepath)
        if "0000" not in filename:
            with open(filepath) as f:
                latest = json.load(f)["latest"]
                if latest is True:
                    latest_filepaths.append(filepath)
    return latest_filepaths


def compare_latest(dir, latest_filepaths) -> tuple[list[str], list[str]]:
    """Compare inbound publications with those currently
    flagged as latest
    Args:
        dir(str): main bulletins directory
        latest_filepaths(list): list of paths to docs
        currently flagged as 'latest=True'
    Returns:
        new_latest(list): names of inbound publications which
            are more recent than others in the series
        former_latest(list): names of current publications
            no longer the most recent in their series
    """
    new_latest = []
    former_latest = []
    inbound_dir = f"{dir}/temp"
    for fp in glob.glob(f"{inbound_dir}/*.json"):
        fp = fp.split(inbound_dir)[-1].lstrip("/")

        for lf in latest_filepaths:
            lf = lf.split(dir)[-1].lstrip("/")
            if fuzz.ratio(fp, lf) > 75:
                new_latest.append(fp)
                former_latest.append(lf)

    new_latest = list(set(new_latest))
    former_latest = list(set(former_latest))

    return new_latest, former_latest


def unflag_former_latest(dir, former_latest) -> None:
    """Updates latest flags to False for publications
    no longer the latest in their series
    Args:
        dir(str): main bulletins directory
        former_latest(list): names of current publications
            no longer the most recent in their series
    """
    for fl in former_latest:
        filepath = f"{dir}/{fl}"
        with open(filepath, "r") as f:
            current_article_json = json.load(f)
            current_article_json["latest"] = False
            json_amend = json.dumps(current_article_json, indent=4)

        with open(filepath, "w") as outfile:
            outfile.write(json_amend)
    return None


def update_split_documents(split_dir, former_latest) -> None:
    """Updates latest flags to False for SPLIT publications
    no longer the latest in their series
    Args:
        dir(str): SPLIT bulletins directory
        former_latest(list): names of current publications
            no longer the most recent in their series (e.g., "2024-Economic-Survey.json")
    """
    for fl in former_latest:
        # Strip .json extension before taking first 60 characters
        # This ensures pattern matching works correctly with split files
        base_name = fl.replace(".json", "")
        split_docs = glob.glob(f"{split_dir}/{base_name[:60]}*.json")
        for sd in split_docs:
            with open(sd, "r") as f:
                one_split = json.load(f)
                one_split["latest"] = False
                json_amend = json.dumps(one_split, indent=4)

            with open(sd, "w") as outfile:
                outfile.write(json_amend)
    return None


def find_matching_chunks(db_dict: dict, docs: list[str]) -> list[str]:
    """Finds all chunk ids for entries in the vector store relating
    to the listed document names
    Args:
        db_dict(dict): dictionary representation of the FAISS db
        docs(list): list of document names for removal
    Returns:
        matched_chunks(list): list of chunk ids to be removed
            from the vector store"""
    matched_chunks = []
    for doc in docs:
        for k in db_dict.keys():
            if doc[:60] in db_dict[k].metadata["source"]:
                matched_chunks.append(k)
    return matched_chunks
