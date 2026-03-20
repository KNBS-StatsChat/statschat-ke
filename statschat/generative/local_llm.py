"""Module to generates responses using a pre-trained locally run language model."""

import torch
import logging
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from transformers import AutoModelForCausalLM, AutoTokenizer
from pathlib import Path
import json
from functools import lru_cache
from statschat.generative.prompts_local import (
    _extractive_prompt,
    _core_prompt,
    _format_instructions,
)

# pip install 'accelerate>=0.26.0'
# install sentencepiece


@staticmethod
def flatten_meta(d):
    """Utility, raise metadata within nested dicts."""
    return d | d.pop("metadata")


@lru_cache(maxsize=1)
def _get_embeddings(
    embedding_model_name: str = "sentence-transformers/all-mpnet-base-v2",
) -> HuggingFaceEmbeddings:
    """Load embedding model once per process."""
    return HuggingFaceEmbeddings(model_name=embedding_model_name)


@lru_cache(maxsize=2)
def _load_faiss_cached(
    faiss_db_root: str,
    embedding_model_name: str = "sentence-transformers/all-mpnet-base-v2",
) -> FAISS:
    """Load FAISS index once per db path per process."""
    return FAISS.load_local(
        faiss_db_root,
        _get_embeddings(embedding_model_name),
        allow_dangerous_deserialization=True,
    )


@lru_cache(maxsize=1)
def _get_local_retrieval_config() -> dict[str, object]:
    """
    Read retrieval settings from main config with safe defaults.

    Keeps local retrieval aligned with the configurable search parameters
    used elsewhere in the project.
    """
    default = {
        "k_docs": 3,
        "similarity_threshold": 2.0,
        "embedding_model_name": "sentence-transformers/all-mpnet-base-v2",
    }
    try:
        from statschat import load_config

        config = load_config(name="main")
        search = config.get("search", {})
        db = config.get("db", {})

        k_docs = int(search.get("k_docs", default["k_docs"]))
        if k_docs < 1:
            k_docs = int(default["k_docs"])

        similarity_threshold = float(
            search.get("similarity_threshold", default["similarity_threshold"])
        )

        embedding_model_name = str(
            db.get("embedding_model_name", default["embedding_model_name"])
        )

        return {
            "k_docs": k_docs,
            "similarity_threshold": similarity_threshold,
            "embedding_model_name": embedding_model_name,
        }
    except Exception:
        return default


def similarity_search(
    query: str, latest_filter: bool = True, return_dicts: bool = True
) -> list[dict]:
    """
    Returns k document chunks with the highest relevance to the
    query

    Args:
        query (str): Question for which most relevant publications will
        be returned
        return_dicts: if True, data returned as dictionary, key = rank

    Returns:
        List[dict]: List of top k article chunks by relevance
    """

    logger = logging.getLogger(__name__)
    logger.info("Retrieving most relevant text chunks")
    faiss_db_root = "data/db_langchain"

    # Check directories exist in "SETUP" MODE to avoid error
    BASE_DIR = Path.cwd().joinpath("data")
    DB_LANGCHAIN_DIR = BASE_DIR.joinpath("db_langchain")
    DB_LANGCHAIN_LATEST_DIR = BASE_DIR.joinpath("db_langchain_latest")

    if DB_LANGCHAIN_LATEST_DIR.exists():
        faiss_db_root_latest = "data/db_langchain_latest"

    elif DB_LANGCHAIN_DIR.exists():
        faiss_db_root_latest = "data/db_langchain"

    retrieval_cfg = _get_local_retrieval_config()
    k_docs = int(retrieval_cfg["k_docs"])
    similarity_threshold = float(retrieval_cfg["similarity_threshold"])
    embedding_model_name = str(retrieval_cfg["embedding_model_name"])

    if latest_filter:
        db_latest = _load_faiss_cached(faiss_db_root_latest, embedding_model_name)
        top_matches = db_latest.similarity_search_with_score(query=query, k=k_docs)
    else:
        db = _load_faiss_cached(faiss_db_root, embedding_model_name)
        top_matches = db.similarity_search_with_score(query=query, k=k_docs)

    # filter to document matches with similarity scores less than...
    # i.e. closest cosine distances to query
    top_matches = [x for x in top_matches if x[-1] <= similarity_threshold]

    if return_dicts:
        return [
            flatten_meta(doc[0].model_dump()) | {"score": float(doc[1])}
            for doc in top_matches
        ]
    return top_matches


# Define a function to generate responses
def generate_response(
    question: str,
    model: str,
    tokenizer,
    max_new_tokens: int = 800,
) -> str:
    """
    Generate a response to the given question using the pre-trained model.

    Args:
        question (str): The input question to generate a response for.
        model (str): The model from huggingface that is being downloaded
        tokenizer (): Pretrained tokenizer from huggingface
        max_new_tokens (int): Maximum number of tokens to generate.

    Returns
        str: The generated response.
    """
    print("Generating input tokens...")
    encoded = tokenizer(question, return_tensors="pt")
    input_ids = encoded.input_ids.to(model.device)
    attention_mask = encoded.attention_mask.to(model.device)
    print("Generating response...")
    output = model.generate(
        input_ids,
        attention_mask=attention_mask,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id,
    )
    raw_response = tokenizer.decode(output[0], skip_special_tokens=True)
    return raw_response


# Define a function to format the response
def _extract_json_block(raw_response: str) -> str:
    """Try to extract the first JSON object from the response text."""
    start = raw_response.find("{")
    end = raw_response.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return raw_response
    return raw_response[start : end + 1]


def format_response(raw_response: str) -> dict:
    """
    Format the raw response from the model.

    Args:
        raw_response (str): The raw response from the model.

    Returns
        dict: The formatted response.
    """
    if "==ANSWER==" in raw_response:
        raw_response = raw_response.split("==ANSWER==")[1]
    clean_response = (
        raw_response.replace("“", '"')
        .replace("”", '"')
        .replace("‘", "'")
        .replace("’", "'")
        .strip()
    )
    clean_response = _extract_json_block(clean_response)
    try:
        validated_answer = json.loads(clean_response)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        validated_answer = {"error": f"Invalid JSON format: {e}"}
    return validated_answer


# Example usage
if __name__ == "__main__":
    verbose = False

    # For a question, retreive the most relevant text chunks
    # question = "What is the leading cause of death in Kenya in 2023?"
    # question = "How is inflation calculated?"
    # question = "What was the population of Kenya in 2019?"
    # question = "What is the Kenya National Bureau of Statistics?"
    # question = "How many counties are there in Kenya?"
    # question = "What was Kenya's GDP growth rate in 2023?"
    # question = "What is the total area of Kenya?"
    # question = "How much did the economy expand in the third quarter of 2025?"
    # question = "What was inflation in Kenya in 2022?"
    # question = "What was Kenya's Consumer Price Index inflation rate in December 2022?"
    # question = "By how much did Kenya's GDP grow in 2024?"
    # question = "What proportion of women own agricultural land in Kenya?"
    question = "What percentage of national government revenue is allocated to the Equalization Funds each year?"

    # Get the most relevant text chunks
    relevant_texts = similarity_search(question, latest_filter=True)

    if len(relevant_texts) == 0:
        raise SystemExit(
            "No relevant documents were found for this question. Try rephrasing it or updating the vector store."
        )

    if len(relevant_texts) == 1:
        # Pad with a placeholder so downstream formatting still succeeds
        relevant_texts.append(
            {
                "page_content": "",
                "title": "(no additional relevant document)",
                "page_url": "",
                "date": "",
                "score": float("inf"),
            }
        )

    if verbose:
        print("Relevant text chunks retrieved:")
        for i, text in enumerate(relevant_texts):
            print(f"Rank {i + 1}: {text['page_content']} (Score: {text['score']})")

    # Extract the most relevant text chunk data
    key_context_1 = relevant_texts[0]["page_content"]
    key_title_1 = relevant_texts[0]["title"]
    key_url_1 = relevant_texts[0]["page_url"]
    key_date_1 = relevant_texts[0]["date"]
    result_score_1 = relevant_texts[0]["score"]

    key_context_2 = relevant_texts[1]["page_content"]
    key_title_2 = relevant_texts[1]["title"]
    key_url_2 = relevant_texts[1]["page_url"]
    key_date_2 = relevant_texts[1]["date"]
    result_score_2 = relevant_texts[1]["score"]

    # Choose your model (e.g., Mistral-7B, DeepSeek, Llama-3, etc.)
    MODEL_ID = "mistralai/Mistral-7B-Instruct-v0.3"  # Change this if needed

    # Load environment variables
    load_dotenv()

    # Load model and tokenizer
    print(f"Building the tokenizer for {MODEL_ID}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    print(f"Loading the model {MODEL_ID}...")
    print("If this is the first run, it will download ~15GB. Please be patient...")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.float16,  # Use float16 for efficiency if using a GPU
        device_map="auto",  # Automatically selects GPU if available
    )
    print("Model loaded successfully.")
    contexts_block = "\n\n".join(
        f"Context{i}: {str(text.get('page_content', '')).strip()}"
        for i, text in enumerate(relevant_texts[:3], start=1)
        if str(text.get("page_content", "")).strip()
    )
    specific_prompt = _extractive_prompt.format(
        QuestionPlaceholder=question,
        ContextsPlaceholder=contexts_block,
    )
    user_input = _core_prompt + specific_prompt + _format_instructions

    if verbose:
        print(user_input)

    raw_response = generate_response(user_input, model, tokenizer)
    formatted_response = format_response(raw_response)

    # Handle error case where JSON parsing failed
    if "error" in formatted_response:
        print("Note: Could not parse response as JSON. See raw response above.")
        print(f"\nQuestion: {question}")
        print("\nRelevant documents found:")
        print(f"  1. {key_title_1} (Score: {round(result_score_1, 2)})")
        print(f"     URL: {key_url_1}")
        print(f"  2. {key_title_2} (Score: {round(result_score_2, 2)})")
        print(f"     URL: {key_url_2}")
    elif (
        formatted_response.get("answer_provided")
        and result_score_1
        or result_score_2 < 0.5
    ):  # check
        print(f"Question: {question}")

        # If no suitable answer
        if formatted_response.get("most_likely_answer") is None:
            print(
                "Answer provided: No suitable answer found. However relevant information may be found in a PDF. Please check the link(s) provided."
            )
        else:
            print("Answer provided:", formatted_response["most_likely_answer"])

        print("Context from:", formatted_response["where_context_from"])
        print("Text:", formatted_response["context_reference"])

        print("These answers are based on the following:")
        print("RELEVANT PUBLICATIONS")
        print("(ONE)")
        print(f"Title: {key_title_1}")
        print(f"Date: {key_date_1}")
        print(f"URL: {key_url_1}")
        print(f"Score: {round(result_score_1, 2)}")

        print("(TWO)")
        print(f"Title: {key_title_2}")
        print(f"Date: {key_date_2}")
        print(f"URL: {key_url_2}")
        print(f"Score: {round(result_score_2, 2)}")

        print("(RESPONSE)")
        print(f"{formatted_response['reasoning']}")

    elif result_score_1 < 0.5:
        print(f"Question: {question}")
        print("Answer not provided, as the context found wasn't easily quotable.")
        print("There may be relevant information in the following publication:")
        print("This comes from:", formatted_response["context_from"])
        print(formatted_response["context_from_text"])

        print("These answers are based on the following:")
        print("(RELEVANT PUBLICATIONS)")
        print("(ONE)")
        print(f"Title: {key_title_1}")
        print(f"Date: {key_date_1}")
        print(f"URL: {key_url_1}")
        print(f"Score: {round(result_score_1, 2)}")
        print(f"This comes from: {key_context_1}")

        print("(TWO)")
        print(f"Title: {key_title_2}")
        print(f"Date: {key_date_2}")
        print(f"URL: {key_url_2}")
        print(f"Score: {round(result_score_2, 2)}")
        print(f"This comes from: {key_context_2}")

        print("(RESPONSE)")
        print(f"{formatted_response['reasoning']}")

    else:
        print("Answer not provided, and the context is not relevant.")

# No suitable answer found.However relevant information may be found in a PDF.Please check the link(s) provided.
