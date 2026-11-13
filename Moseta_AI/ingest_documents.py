
import os
import json
import numpy as np
import pymupdf

from sentence_transformers import SentenceTransformer


# ==========================================
# CONFIGURATION
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DOCS_FOLDER = os.path.join(BASE_DIR, "product_docs")
KB_FOLDER = os.path.join(BASE_DIR, "knowledge_base")

EMBEDDING_MODEL = "intfloat/multilingual-e5-small"

os.makedirs(DOCS_FOLDER, exist_ok=True)
os.makedirs(KB_FOLDER, exist_ok=True)


# ==========================================
# READ PDF DOCUMENTS
# ==========================================

def read_pdf(path):

    text = ""

    try:
        pdf = pymupdf.open(path)

        for page_number, page in enumerate(pdf, start=1):

            page_text = page.get_text("text")

            if page_text.strip():

                text += (
                    f"\nPage {page_number}\n"
                    f"{page_text}"
                )

        pdf.close()

    except Exception as error:

        print(f"Error reading {path}: {error}")
        return ""

    return text


# ==========================================
# SPLIT TEXT INTO CHUNKS
# ==========================================

def split_into_chunks(
    text,
    chunk_size=130,
    overlap=30
):

    words = text.split()

    chunks = []

    start = 0

    while start < len(words):

        end = start + chunk_size

        chunk = " ".join(words[start:end])

        if chunk.strip():
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


# ==========================================
# INGEST DOCUMENTS
# ==========================================

def main():

    all_chunks = []
    metadata = []

    pdf_files = [
        filename
        for filename in os.listdir(DOCS_FOLDER)
        if filename.lower().endswith(".pdf")
    ]

    if not pdf_files:

        print("\nNo PDF documents found!")

        print(
            "Add PDF files to the product_docs folder."
        )

        return

    print("\nFound PDF documents:", len(pdf_files))

    for filename in pdf_files:

        path = os.path.join(
            DOCS_FOLDER,
            filename
        )

        print("\nReading:", filename)

        text = read_pdf(path)

        if not text.strip():

            print("No readable text:", filename)
            continue

        chunks = split_into_chunks(text)

        for chunk_number, chunk in enumerate(chunks):

            all_chunks.append(chunk)

            metadata.append({

                "source": filename,

                "chunk_number": chunk_number,

                "text": chunk

            })

        print("Extracted chunks:", len(chunks))

    if not all_chunks:

        print("\nNo readable PDF content found.")
        print("Check whether your PDFs contain selectable text.")

        return

    # ======================================
    # LOAD EMBEDDING MODEL
    # ======================================

    print("\nLoading embedding model...")

    embedder = SentenceTransformer(
        EMBEDDING_MODEL,
        device="cpu"
    )

    # E5 requires passage prefix for documents

    passages = [

        "passage: " + chunk

        for chunk in all_chunks

    ]

    # ======================================
    # CREATE EMBEDDINGS
    # ======================================

    print("\nCreating embeddings...")

    embeddings = embedder.encode(

        passages,

        convert_to_numpy=True,

        normalize_embeddings=True,

        show_progress_bar=True

    )

    # ======================================
    # SAVE KNOWLEDGE BASE
    # ======================================

    np.save(

        os.path.join(
            KB_FOLDER,
            "embeddings.npy"
        ),

        embeddings

    )

    with open(

        os.path.join(
            KB_FOLDER,
            "metadata.json"
        ),

        "w",

        encoding="utf-8"

    ) as file:

        json.dump(

            metadata,

            file,

            ensure_ascii=False,

            indent=2

        )

    print("\n" + "=" * 45)

    print("KNOWLEDGE BASE CREATED SUCCESSFULLY!")

    print("PDF documents:", len(pdf_files))

    print("Total chunks:", len(all_chunks))

    print("Embedding dimensions:", embeddings.shape[1])

    print("Saved in:", KB_FOLDER)

    print("=" * 45)


if __name__ == "__main__":

    main()
