
from statschat.embedding.preprocess import PrepareVectorStore
from pathlib import Path
import toml

config = toml.load("statschat/config/main.toml")

prep = PrepareVectorStore(**config["db"], **config["preprocess"])

print("\nFINAL PATHS:")
print("original_faiss_db_root =", prep.original_faiss_db_root)
print("faiss_db_root =", prep.faiss_db_root)
