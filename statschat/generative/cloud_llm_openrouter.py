import os
import logging
from functools import lru_cache
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
from langchain_community.vectorstores import FAISS
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain.output_parsers import PydanticOutputParser
from statschat.generative.prompts_cloud import EXTRACTIVE_PROMPT_PYDANTIC, STUFF_DOCUMENT_PROMPT
from statschat.generative.utils import deduplicator, time_decay, highlighter
from statschat.generative.response_model import LlmResponse
from langchain.chat_models import ChatOpenAI


class Inquirer:
    """
    A class for querying a local FAISS document database using OpenAI's language models
    and returning structured answers with supporting context.
    """

    def __init__(
        self,
        generative_model_name: str = "mistralai/mistral-7b-instruct", # meta-llama/Meta-Llama-3-8B-Instruct # openchat/openchat-3.5
        faiss_db_root: str = "data/db_langchain",
        faiss_db_root_latest: str = "data/db_langchain",
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        k_docs: int = 10,
        k_contexts: int = 3,
        similarity_threshold: float = 2.0,
        logger: logging.Logger = None,
        llm_temperature: float = 0.0,
        llm_max_tokens: int = 1024,
        verbose: bool = False,
        answer_threshold: float = 0.5,
        document_threshold: float = 0.9,
    ):
        """
        Initialize the Inquirer with model, database, and search configuration.
        """
        self.logger = logger or logging.getLogger(__name__)
        self.k_docs = k_docs
        self.k_contexts = k_contexts
        self.similarity_threshold = similarity_threshold
        self.answer_threshold = answer_threshold
        self.document_threshold = document_threshold
        self.verbose = verbose
        self.extractive_prompt = EXTRACTIVE_PROMPT_PYDANTIC
        self.stuff_document_prompt = STUFF_DOCUMENT_PROMPT
        self.llm_temperature = llm_temperature
        self.llm_max_tokens = llm_max_tokens

        # API KEY
        load_dotenv()
        sec_key = os.getenv("OPENROUTER_API_KEY")
        
        # API BASE
        api_base = os.getenv("OPENROUTER_BASE_URL")
  
        self.llm = ChatOpenAI(
            model=generative_model_name,  # or another OpenRouter-supported model
            openai_api_key=sec_key,
            openai_api_base=api_base,
            temperature=llm_temperature,
            max_tokens=llm_max_tokens,
        )

        embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name)

        self.db = FAISS.load_local(faiss_db_root, embeddings, allow_dangerous_deserialization=True)
        self.db_latest = FAISS.load_local(faiss_db_root_latest, embeddings, allow_dangerous_deserialization=True)

    @staticmethod
    def flatten_meta(d: dict) -> dict:
        """
        Flatten nested metadata from FAISS document results.

        Args:
            d (dict): Document dictionary with nested 'metadata' key.

        Returns:
            dict: Flattened dictionary with metadata merged.
        """
        return d | d.pop("metadata")

    def similarity_search(self, query: str, latest_filter: bool = True, return_dicts: bool = True) -> list[dict]:
        """
        Perform similarity search on FAISS database.

        Args:
            query (str): The search query.
            latest_filter (bool): Whether to use the latest version of the database.
            return_dicts (bool): Whether to return results as dictionaries.

        Returns:
            list[dict]: List of top matching documents with scores.
        """
        self.logger.info("Retrieving most relevant text chunks")
        db = self.db_latest if latest_filter else self.db
        top_matches = db.similarity_search_with_score(query=query, k=self.k_docs)
        top_matches = [x for x in top_matches if x[-1] <= self.similarity_threshold]

        if return_dicts:
            return [self.flatten_meta(doc[0].model_dump()) | {"score": float(doc[1])} for doc in top_matches]
        return top_matches

    def query_texts(self, query: str, docs: list[dict]) -> LlmResponse:
        """
        Query the language model with top documents and return structured response.

        Args:
            query (str): The user question.
            docs (list[dict]): List of top matching documents.

        Returns:
            LlmResponse: Parsed response from the language model.
        """
        if not docs:
            return LlmResponse(answer_provided=False, highlighting1=[], highlighting2=[], highlighting3=[])

        top_matches = [
            Document(
                page_content=text["page_content"],
                metadata={"doc_num": i + 1, "date": text["date"], "title": text["title"]},
            )
            for i, text in enumerate(docs[:self.k_contexts])
            if text["score"] <= 1.5 * docs[0]["score"]
        ]

        self.logger.info(f"Passing top {len(top_matches)} results for QA")

        chain = load_qa_with_sources_chain(
            self.llm,
            chain_type="stuff",
            prompt=self.extractive_prompt,
            document_prompt=self.stuff_document_prompt,
            verbose=self.verbose,
        )

        response = chain.invoke({"input_documents": top_matches, "question": query}, return_only_outputs=True)

        parser = PydanticOutputParser(pydantic_object=LlmResponse)
        try:
            if "output_text" in response:
                validated_answer = parser.parse(response["output_text"])
            elif "properties" in response:
                validated_answer = parser.parse(response["properties"])
            else:
                validated_answer = parser.parse(response)
        except Exception as e:
            self.logger.error(f"Cannot parse response: {e}")
            self.logger.error(f"response: {response}")
            return LlmResponse(
                answer_provided=False,
                highlighting1=[],
                highlighting2=[],
                highlighting3=[],
                reasoning=f"Cannot parse response: {e}\n\nresponse: {response}",
            )

        return validated_answer

    @lru_cache()
    def make_query(
        self,
        question: str,
        latest_filter: str = "on",
        highlighting: bool = True,
        latest_weight: float = 1,
    ) -> tuple[list[dict], str, LlmResponse]:
        """
        Perform full query pipeline: search, rerank, query LLM, and highlight.

        Args:
            question (str): The user question.
            latest_filter (str): Whether to use the latest database.
            highlighting (bool): Whether to apply highlighting to results.
            latest_weight (float): Weighting factor for recency.

        Returns:
            tuple: (documents, answer string, structured response)
        """
        self.logger.info(f"Search query: {question}")
        docs1 = self.similarity_search(question, latest_filter=latest_filter.lower() in ["on", "true"])

        if not docs1:
            return docs1, "", LlmResponse(answer_provided=False)

        docs = deduplicator(docs1, keys=["title", "date"])

        if latest_weight > 0:
            for doc in docs:
                doc["score"] = doc["score"] / time_decay(doc["date"], latest=latest_weight)
            docs.sort(key=lambda doc: doc["score"])
            self.logger.info(f"Weighted and reordered docs to latest with decay = {latest_weight}")

        for doc in docs:
            doc["score"] = round(doc["score"], 2)

        self.logger.info(f"Received {len(docs)} references with top distance {docs[0]['score'] if docs else 'Inf'}")

        validated_response = self.query_texts(question, docs)
        self.logger.info(f"QAPAIR - Question: {question}, Answer: {validated_response}")

        if highlighting:
            docs = highlighter(docs, validated_response=validated_response, logger=self.logger)

        if validated_response.answer_provided is False or docs[0]["score"] > self.answer_threshold:
            answer_str = (
                "No suitable answer found. However relevant information may be found in a PDF. "
                "Please check the link(s) provided."
            )
        else:
            answer_str = (
                "Most relevant quote from publications below: "
                + '<h4 class="ons-u-fs-xxl"> <div id="answer">'
                + validated_response.most_likely_answer
                + "</div> </h4>"
            )

        if docs[0]["score"] > self.document_threshold:
            docs.clear()
            docs.extend([
                "No suitable PDFs found. Please refer to context",
                "No context available. Please refer to response"
            ])

        return docs, answer_str, validated_response

if __name__ == "__main__":
    from statschat import load_config

    """
    Run a sample query using the Inquirer class and print structured results.
    """
    # Initialize logger
    logger = logging.getLogger("statschat")
    logging.basicConfig(level=logging.INFO)

    # Load configuration from YAML or dict
    CONFIG = load_config(name="main")

    # Initialize the Inquirer with config
    inquirer = Inquirer(**CONFIG["db"], **CONFIG["search"], logger=logger)

    # Define your question
    question = "What was inflation in Kenya in December 2021?"

    # Run the query pipeline
    docs, answer, response = inquirer.make_query(
        question,
        latest_filter="off",
    )

    # Display results
    print("\n-------------------- ANSWER --------------------")
    print(answer)

    print("\n------------------ DOCUMENT -------------------")
    if isinstance(docs[0], dict) and "title" in docs[0] and "url" in docs[0] and "page_url" in docs[0]:
        document_url = docs[0]["url"]
        page_url = docs[0]["page_url"]
        document_title = docs[0]["title"]
        document_name = document_url.split("/")[-1].replace(".pdf", "")
        print(f"The document title is {document_title}.")
        print(f"The file name is {document_name}.")
        print(f"You can read more from the document at {page_url}.")
    else:
        print("No valid document metadata found.")

    print("\n------------------ CONTEXT INFO ------------------")
    print(docs)

    print("\n------------------ FULL RESPONSE -----------------")
    print(response)

    
