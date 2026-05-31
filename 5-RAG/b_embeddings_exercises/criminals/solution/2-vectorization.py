import os
import shutil
import sqlite3
import cv2
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from insightface.app import FaceAnalysis
import chromadb

SCRIPT_DIR = Path(__file__).parent
DB_NAME = str(SCRIPT_DIR / "posters.db")
CHROMA_DIR = str(SCRIPT_DIR / "chroma_db")

FACE_COLLECTION = "suspect_face_vectors"
CASE_COLLECTION = "case_report_vectors"


def build_face_index(db_name, collection):
    app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=-1, det_size=(640, 640))

    conn = sqlite3.connect(db_name)
    rows = conn.execute("SELECT id, doc_id, file_path FROM document_assets").fetchall()
    conn.close()

    ids, embeddings, metadatas = [], [], []

    for asset_id, doc_id, file_path in rows:
        img_path = Path(file_path)
        img = cv2.imread(str(img_path))
        if img is None:
            print(f"  Skipping unreadable: {img_path.name}")
            continue
        faces = app.get(img)
        if not faces:
            print(f"  No face detected: {img_path.name}")
            continue
        face = max(faces, key=lambda f: f.det_score)
        ids.append(str(asset_id))
        embeddings.append(face.normed_embedding.tolist())
        metadatas.append({"file_name": img_path.name, "asset_id": asset_id, "doc_id": doc_id})
        print(f"  Embedded face: {img_path.name} (asset_id={asset_id}, doc_id={doc_id})")

    if ids:
        collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas)
        print(f"Stored {len(ids)} face embeddings in '{FACE_COLLECTION}'")


def build_text_index(db_name, collection):
    client = OpenAI()
    conn = sqlite3.connect(db_name)
    rows = conn.execute("SELECT id, file_name, full_text FROM documents").fetchall()
    conn.close()

    ids, embeddings, metadatas = [], [], []

    for doc_id, file_name, full_text in rows:
        if not full_text:
            continue
        response = client.embeddings.create(
            model="text-embedding-3-large",
            input=full_text,
        )
        ids.append(str(doc_id))
        embeddings.append(response.data[0].embedding)
        metadatas.append({"file_name": file_name, "text": full_text})
        print(f"  Embedded text: {file_name}")

    if ids:
        collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas)
        print(f"Stored {len(ids)} text embeddings in '{CASE_COLLECTION}'")


def vectorize_all():
    load_dotenv(dotenv_path=SCRIPT_DIR / '../../../../.env', override=True)

    chroma_path = Path(CHROMA_DIR)
    if chroma_path.exists():
        shutil.rmtree(chroma_path)
        print("Cleared existing ChromaDB.")

    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)

    face_collection = chroma_client.get_or_create_collection(
        name=FACE_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )
    text_collection = chroma_client.get_or_create_collection(
        name=CASE_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )

    print("=== Building face index (ArcFace) ===")
    build_face_index(DB_NAME, face_collection)

    print("\n=== Building text index (text-embedding-3-large) ===")
    build_text_index(DB_NAME, text_collection)

    print("\nDone.")


vectorize_all()
