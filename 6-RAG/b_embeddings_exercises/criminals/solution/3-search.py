import cv2
from pathlib import Path
import chromadb
from insightface.app import FaceAnalysis

SCRIPT_DIR = Path(__file__).parent
CHROMA_DIR = str(SCRIPT_DIR / "chroma_db")
FACE_COLLECTION = "suspect_face_vectors"
QUERY_IMAGE = SCRIPT_DIR / "John-Doe.jpg"
TOP_K = 5


def get_face_embedding(image_path, app):
    img = cv2.imread(str(image_path))
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")
    faces = app.get(img)
    if not faces:
        raise ValueError(f"No face detected in: {image_path}")
    face = max(faces, key=lambda f: f.det_score)
    return face.normed_embedding.tolist()


def query_face_collection(embedding, top_k=TOP_K):
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = chroma_client.get_collection(name=FACE_COLLECTION)

    results = collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
        include=["metadatas", "distances"],
    )

    ids = results["ids"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]

    return ids, distances, metadatas


def show_results(ids, distances, metadatas):
    print(f"\nTop {len(ids)} matches:")
    print("-" * 40)
    for rank, (doc_id, distance, meta) in enumerate(zip(ids, distances, metadatas), start=1):
        similarity = 1 - distance  # cosine distance → similarity
        print(f"  {rank}. {doc_id}")
        print(f"     File   : {meta.get('file_name', 'N/A')}")
        print(f"     Score  : {similarity:.4f}")


def search_by_image(query_image_path=QUERY_IMAGE, top_k=TOP_K):
    app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
    app.prepare(ctx_id=-1, det_size=(640, 640))

    print(f"Extracting face embedding from: {query_image_path.name}")
    embedding = get_face_embedding(query_image_path, app)

    ids, distances, metadatas = query_face_collection(embedding, top_k)
    show_results(ids, distances, metadatas)


search_by_image()
