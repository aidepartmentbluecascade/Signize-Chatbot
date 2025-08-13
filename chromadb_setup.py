import chromadb
from chromadb.utils import embedding_functions

def initialize_chromadb(openai_key, path="chroma_persistent_storage", collection_name="document_qa_collection"):
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=openai_key, model_name="text-embedding-3-small"
    )
    chroma_client = chromadb.PersistentClient(path=path)
    collection = chroma_client.get_or_create_collection(
        name=collection_name, embedding_function=openai_ef
    )
    return collection
