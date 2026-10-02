import os
from pathlib import Path

from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEndpointEmbeddings


load_dotenv()


APP_ENV = os.getenv("APP_ENV", "local")

if os.getenv("VERCEL") == "1":
    APP_ENV = "vercel"


BASE_DIR = Path(
    __file__
).resolve().parents[2]


if APP_ENV == "vercel":

    # Hugging Face hosted embeddings
    embeddings = HuggingFaceEndpointEmbeddings(
        model=(
            "sentence-transformers/"
            "all-MiniLM-L6-v2"
        ),
        task="feature-extraction",
        huggingfacehub_api_token=os.getenv(
            "HF_TOKEN"
        )
    )

    # Chroma Cloud
    vectorstore = Chroma(
        collection_name="resume_collection",
        embedding_function=embeddings,
        chroma_cloud_api_key=os.getenv(
            "CHROMA_API_KEY"
        ),
        tenant=os.getenv(
            "CHROMA_TENANT"
        ),
        database=os.getenv(
            "CHROMA_DATABASE"
        )
    )

else:

    # Local Ollama embeddings
    from langchain_ollama import OllamaEmbeddings

    embeddings = OllamaEmbeddings(
        model=os.getenv(
            "OLLAMA_EMBEDDING_MODEL",
            "nomic-embed-text"
        )
    )

    # Local Chroma
    DB_PATH = BASE_DIR / "vector_db"

    vectorstore = Chroma(
        collection_name="resume_collection_768",
        persist_directory=str(
            DB_PATH
        ),
        embedding_function=embeddings
    )