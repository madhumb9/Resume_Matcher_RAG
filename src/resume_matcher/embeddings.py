import os
from pathlib import Path

from dotenv import load_dotenv

from langchain_huggingface import (
    HuggingFaceEmbeddings,
    HuggingFaceEndpointEmbeddings
)

from langchain_chroma import Chroma


load_dotenv()


APP_ENV = os.getenv(
    "APP_ENV",
    "local"
)


BASE_DIR = Path(
    __file__
).resolve().parents[2]


if APP_ENV == "vercel":

    
    # CLOUD EMBEDDINGS
    

    embeddings = HuggingFaceEndpointEmbeddings(
        model=(
            "sentence-transformers/"
            "all-MiniLM-L6-v2"
        ),
        task="feature-extraction",
        huggingfacehub_api_token=os.getenv(
            "HUGGINGFACEHUB_API_TOKEN"
        )
    )

   
    # CHROMA CLOUD
   

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

    
    # LOCAL EMBEDDINGS
   

    embeddings = HuggingFaceEmbeddings(
        model_name=(
            "sentence-transformers/"
            "all-MiniLM-L6-v2"
        ),
        encode_kwargs={
            "normalize_embeddings": True
        }
    )

    
    # LOCAL CHROMA
    

    DB_PATH = BASE_DIR / "vector_db"

    vectorstore = Chroma(
        collection_name="resume_collection",
        persist_directory=str(
            DB_PATH
        ),
        embedding_function=embeddings
    )