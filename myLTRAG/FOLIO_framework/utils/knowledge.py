# knowledge.py
# imp: contains FAISS RAG and embedding model
import os
import csv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from config.Settings import config  # triggers load_dotenv()

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../dataset_example/FOLIO-fix.csv")
INDEX_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../knowledgeCache/faiss_index")


def build_vectorstore(embeddings) -> FAISS:
    if os.path.exists(INDEX_PATH):
        return FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
    texts, metadatas = [], []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            texts.append(row["input"])
            metadatas.append({"output": row["output"]})
    store = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    store.save_local(INDEX_PATH)
    return store


def retrieve(store: FAISS, query: str, k: int = 3) -> list[dict]:
    docs = store.similarity_search(query, k=k)
    return [{"Input": doc.page_content, "Output": doc.metadata["output"]} for doc in docs]


embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
vectorstore = build_vectorstore(embeddings)
