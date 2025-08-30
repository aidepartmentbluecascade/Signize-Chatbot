def query_documents(collection, questions, n_results=2):
    print("Querying Chroma...")
    try:
        results = collection.query(query_texts=questions, n_results=n_results)
        relevant_chunk = [doc for sublist in results["documents"] for doc in sublist]
        print("Returned relevant chunks")
        return relevant_chunk
    except Exception as e:
        print("Chroma query failed:", e)
        return [""]  # return empty context to continue


def generate_response(client, question, relevant_chunk):
    context = "\n\n".join(relevant_chunk)
    prompt = (
        "You are an assistant for question-answering tasks. Use the following pieces of "
        "retrieved context to answer the question. If you don't know the answer, say that you "
        "don't know. Use three sentences maximum and keep the answer concise."
        "\n\nContext:\n" + context + "\n\nQuestion:\n" + question
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": prompt,
            },
            {
                "role": "user",
                "content": question,
            },
        ],
    )

    return response.choices[0].message.content
