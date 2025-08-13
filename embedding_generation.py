def get_openai_embedding(client, text):
    response = client.embeddings.create(input=text, model="text-embedding-3-small")
    embedding = response.data[0].embedding
    print("==== Generating embeddings... ====")
    return embedding

def generate_embeddings(client, chunked_documents):
    for doc in chunked_documents:
        print("==== Generating embeddings... ====")
        doc["embedding"] = get_openai_embedding(client, doc["text"])
    return chunked_documents
