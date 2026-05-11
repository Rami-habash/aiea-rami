# knowledge.py
# FAISS rag for AR_LSAT
import os
import csv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from configparser import ConfigParser

file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../config.ini").replace("\\", "/")
cf = ConfigParser()
cf.read(file_path, encoding="utf-8")

DATASET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../dataset_example")
TRANSLATION_CSV = os.path.join(DATASET_DIR, "LSAT-translation.csv")
FIX_CSV = os.path.join(DATASET_DIR, "LSAT-fix.csv")
TRANSLATION_INDEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../knowledgeCache/faiss_translation")
FIX_INDEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../knowledgeCache/faiss_fix")


def build_vectorstore(csv_path: str, index_path: str, embeddings) -> FAISS:
    if os.path.exists(index_path):
        return FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
    texts, metadatas = [], []
    with open(csv_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            texts.append(row["input"])
            metadatas.append({"output": row["output"]})
    store = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
    os.makedirs(index_path, exist_ok=True)
    store.save_local(index_path)
    return store


def retrieve(store: FAISS, query: str, k: int = 3) -> list[dict]:
    docs = store.similarity_search(query, k=k)
    return [{"Input": doc.page_content, "Output": doc.metadata["output"]} for doc in docs]


_embedding_key = cf.get("API", "EMBEDDING_KEY")
embeddings = OpenAIEmbeddings(
    model=cf.get("API", "EMBEDDING_MODEL"),
    openai_api_key=os.getenv(_embedding_key, _embedding_key),
    openai_api_base=cf.get("API", "EMBEDDING_URL"),
)
translation_store = build_vectorstore(TRANSLATION_CSV, TRANSLATION_INDEX, embeddings)
fix_store = build_vectorstore(FIX_CSV, FIX_INDEX, embeddings)
