def upsert_documents_into_db(collection, chunked_documents):
    for doc in chunked_documents:
        print("==== Inserting chunks into db;;; ====")
        collection.upsert(
            ids=[doc["id"]], documents=[doc["text"]], embeddings=[doc["embedding"]]
        )
