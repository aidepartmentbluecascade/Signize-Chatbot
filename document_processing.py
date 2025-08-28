import os
import PyPDF2
import io

def load_documents_from_directory(directory_path):
    print("==== Loading documents from directory ====")
    documents = []
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        
        if filename.endswith(".txt"):
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    documents.append({"id": filename, "text": file.read()})
                print(f"Loaded text file: {filename}")
            except Exception as e:
                print(f"Error loading text file {filename}: {e}")
                
        elif filename.endswith(".pdf"):
            try:
                with open(file_path, "rb") as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text_content = ""
                    
                    for page_num in range(len(pdf_reader.pages)):
                        page = pdf_reader.pages[page_num]
                        text_content += page.extract_text() + "\n"
                    
                    if text_content.strip():
                        documents.append({"id": filename, "text": text_content})
                        print(f"Loaded PDF file: {filename} ({len(pdf_reader.pages)} pages)")
                    else:
                        print(f"Warning: No text content found in PDF: {filename}")
                        
            except Exception as e:
                print(f"Error loading PDF file {filename}: {e}")
                
    print(f"Total documents loaded: {len(documents)}")
    return documents

def split_text(text, chunk_size=1000, chunk_overlap=20):
    """
    Split text into chunks with overlap, trying to break at sentence boundaries when possible
    """
    chunks = []
    start = 0
    
    # Clean up the text
    text = text.strip()
    
    while start < len(text):
        end = start + chunk_size
        
        # If we're not at the end of the text, try to find a good breaking point
        if end < len(text):
            # Look for sentence endings within the last 100 characters of the chunk
            search_start = max(start, end - 100)
            search_end = min(end + 100, len(text))
            
            # Find the last sentence ending in this range
            last_period = text.rfind('.', search_start, end)
            last_exclamation = text.rfind('!', search_start, end)
            last_question = text.rfind('?', search_start, end)
            last_newline = text.rfind('\n', search_start, end)
            
            # Find the best breaking point
            break_points = [last_period, last_exclamation, last_question, last_newline]
            valid_breaks = [p for p in break_points if p > start]
            
            if valid_breaks:
                best_break = max(valid_breaks)
                if best_break > start:
                    end = best_break + 1  # Include the punctuation
        
        chunk = text[start:end].strip()
        if chunk:  # Only add non-empty chunks
            chunks.append(chunk)
        
        start = end - chunk_overlap
        if start >= len(text):
            break
    
    return chunks

def preprocess_documents(documents, chunk_size=1000, chunk_overlap=20):
    print("==== Preprocessing documents into chunks ====")
    chunked_documents = []
    total_chunks = 0
    
    for doc in documents:
        chunks = split_text(doc["text"], chunk_size, chunk_overlap)
        print(f"Split {doc['id']} into {len(chunks)} chunks")
        
        for i, chunk in enumerate(chunks):
            chunked_documents.append({
                "id": f"{doc['id']}_chunk{i+1}", 
                "text": chunk,
                "source_file": doc['id']
            })
        total_chunks += len(chunks)
    
    print(f"Total chunks created: {total_chunks}")
    return chunked_documents
