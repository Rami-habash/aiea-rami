# knowledge.py
# NOTE: FAISS rag substitutes paper's FastGPT 
# also two vectorstores made for each of symbol + errfix = LTRAG 

import os

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
import csv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from config.Settings import config  # triggers load_dotenv()

_BASE = os.path.dirname(os.path.abspath(__file__))
TRANSLATION_CSV = os.path.join(_BASE, "../../dataset_example/FOLIO-translation.csv")
FIX_CSV = os.path.join(_BASE, "../../dataset_example/FOLIO-fix.csv")
TRANSLATION_INDEX = os.path.join(_BASE, "../knowledgeCache/faiss_translation")
FIX_INDEX = os.path.join(_BASE, "../knowledgeCache/faiss_fix")


def build_vectorstore(csv_path: str, index_path: str, embeddings) -> FAISS:
    if os.path.exists(index_path):
        return FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
    texts, metadatas = [], []
    # utf-8-sig: FOLIO-translation.csv carries a BOM, so the first column would
    # otherwise be read as "input" and KeyError on row["input"].
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            texts.append(row["input"])
            metadatas.append({"output": row["output"]})
    store = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    store.save_local(index_path)
    return store


def retrieve(store: FAISS, query: str, k: int = 3) -> list[dict]:
    docs = store.similarity_search(query, k=k)
    return [{"Input": doc.page_content, "Output": doc.metadata["output"]} for doc in docs]


embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
translation_store = build_vectorstore(TRANSLATION_CSV, TRANSLATION_INDEX, embeddings)
fix_store = build_vectorstore(FIX_CSV, FIX_INDEX, embeddings)
