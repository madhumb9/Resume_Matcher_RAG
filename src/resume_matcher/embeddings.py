import os
from pathlib import Path

from dotenv import load_dotenv

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = BASE_DIR / "vector_db"

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    encode_kwargs={
        "normalize_embeddings": True
    }
)

vectorstore = Chroma(
    collection_name="resume_collection",
    persist_directory=str(DB_PATH),
    embedding_function=embeddings
)