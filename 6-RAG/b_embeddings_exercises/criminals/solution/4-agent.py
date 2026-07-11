"""
Criminal Search Agent — LangGraph RAG Agent

A police officer can search the criminal/missing-person database by:
  - Image file path  → face similarity search  (ArcFace  + ChromaDB)
  - Case description → text similarity search  (OpenAI embeddings + ChromaDB)
"""

import cv2
import chromadb
from pathlib import Path
from typing import Annotated, TypedDict
from dotenv import load_dotenv

from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from openai import OpenAI
from insightface.app import FaceAnalysis


# ── Configuration ─────────────────────────────────────────────────────────────

SCRIPT_DIR      = Path(__file__).parent
CHROMA_DIR      = str(SCRIPT_DIR / "chroma_db")
FACE_COLLECTION = "suspect_face_vectors"
CASE_COLLECTION = "case_report_vectors"
TOP_K           = 5

load_dotenv(dotenv_path=SCRIPT_DIR / "../../../../.env", override=True)


# ── ArcFace model — loaded once on first use ──────────────────────────────────

_face_analysis_app = None

def get_face_analysis_app() -> FaceAnalysis:
    """Return the InsightFace ArcFace model, initialising it on first call."""
    global _face_analysis_app
    if _face_analysis_app is None:
        _face_analysis_app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        _face_analysis_app.prepare(ctx_id=-1, det_size=(640, 640))
    return _face_analysis_app


# ── Face search — helpers ─────────────────────────────────────────────────────

def resolve_image_path(image_path: str) -> Path:
    """Return an absolute path, falling back to SCRIPT_DIR for bare filenames."""
    path = Path(image_path)
    if not path.is_absolute():
        path = SCRIPT_DIR / path
    return path


def extract_best_face_embedding(image_path: str) -> list[float]:
    """Read an image and return the ArcFace embedding of the most prominent face."""
    path = resolve_image_path(image_path)
    img = cv2.imread(str(path))
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {path}")
    faces = get_face_analysis_app().get(img)
    if not faces:
        raise ValueError(f"No face detected in: {path}")
    best_face = max(faces, key=lambda f: f.det_score)
    return best_face.normed_embedding.tolist()


def query_face_collection(embedding: list[float]) -> list[dict]:
    """Search ChromaDB for the top-K most similar face embeddings."""
    client     = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(name=FACE_COLLECTION)
    results    = collection.query(
        query_embeddings=[embedding],
        n_results=TOP_K,
        include=["metadatas", "distances"],
    )
    matches = []
    for rank, (doc_id, distance, meta) in enumerate(
        zip(results["ids"][0], results["distances"][0], results["metadatas"][0]), start=1
    ):
        matches.append({
            "rank":       rank,
            "file_name":  meta.get("file_name", "N/A"),
            "doc_id":     meta.get("doc_id", "N/A"),
            "similarity": round(1 - distance, 4),
        })
    return matches


def format_face_results(matches: list[dict], image_path: str) -> str:
    """Format face-search results as a readable string."""
    lines = [f"Top {len(matches)} face matches for '{Path(image_path).name}':"]
    for m in matches:
        lines.append(
            f"  {m['rank']}. {m['file_name']}  |  doc_id={m['doc_id']}  |  similarity={m['similarity']}"
        )
    return "\n".join(lines)


# ── Face search — tool ────────────────────────────────────────────────────────

@tool
def search_by_face(image_path: str) -> str:
    """
    Search for matching suspects by facial similarity.
    Use this tool when the user provides a path to an image file.
    Returns the top matching criminal or missing-person records.
    """
    embedding = extract_best_face_embedding(image_path)
    matches   = query_face_collection(embedding)
    return format_face_results(matches, image_path)


# ── Text search — helpers ─────────────────────────────────────────────────────

def embed_text_with_openai(text: str) -> list[float]:
    """Generate a vector embedding for text using OpenAI text-embedding-3-large."""
    client   = OpenAI()
    response = client.embeddings.create(model="text-embedding-3-large", input=text)
    return response.data[0].embedding


def query_case_collection(embedding: list[float]) -> list[dict]:
    """Search ChromaDB for the top-K most similar case descriptions."""
    client     = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_collection(name=CASE_COLLECTION)
    results    = collection.query(
        query_embeddings=[embedding],
        n_results=TOP_K,
        include=["metadatas", "distances"],
    )
    matches = []
    for rank, (doc_id, distance, meta) in enumerate(
        zip(results["ids"][0], results["distances"][0], results["metadatas"][0]), start=1
    ):
        matches.append({
            "rank":       rank,
            "file_name":  meta.get("file_name", "N/A"),
            "doc_id":     doc_id,
            "similarity": round(1 - distance, 4),
        })
    return matches


def format_case_results(matches: list[dict], description: str) -> str:
    """Format case-search results as a readable string."""
    short = description[:60] + "..." if len(description) > 60 else description
    lines = [f"Top {len(matches)} case matches for: \"{short}\""]
    for m in matches:
        lines.append(
            f"  {m['rank']}. {m['file_name']}  |  doc_id={m['doc_id']}  |  similarity={m['similarity']}"
        )
    return "\n".join(lines)


# ── Text search — tool ────────────────────────────────────────────────────────

@tool
def search_by_case_description(description: str) -> str:
    """
    Search for matching case reports using a text description.
    Use this tool when the user describes a crime, victim name, location,
    or any other case details.
    Returns the top matching criminal or missing-person case records.
    """
    embedding = embed_text_with_openai(description)
    matches   = query_case_collection(embedding)
    return format_case_results(matches, description)


# ── LangGraph agent ───────────────────────────────────────────────────────────

tools = [search_by_face, search_by_case_description]

SYSTEM_PROMPT = (
    "You are a criminal investigation assistant for law enforcement.\n"
    "You have two search tools:\n"
    "  - search_by_face            : use when the user provides an image file path.\n"
    "  - search_by_case_description: use when the user describes a crime, victim, or case details.\n"
    "Analyse the query carefully, call the appropriate tool, and present the results clearly."
)


class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


model = ChatOpenAI(model="gpt-4o").bind_tools(tools)


def call_model(state: State) -> dict:
    """Invoke the LLM with the full conversation history and return its response."""
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = model.invoke(messages)
    return {"messages": [response]}


def should_continue(state: State) -> str:
    """Route to the tool node if the LLM requested a tool call, otherwise end."""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END


def build_graph():
    """Assemble and compile the LangGraph ReAct agent."""
    workflow = StateGraph(State)

    workflow.add_node("llm",   call_model)
    workflow.add_node("tools", ToolNode(tools))

    workflow.add_edge(START, "llm")
    workflow.add_conditional_edges("llm", should_continue)
    workflow.add_edge("tools", "llm")

    return workflow.compile()


# ── Entry point ───────────────────────────────────────────────────────────────

agent = build_graph()


def run_query(query: str) -> str:
    """Run a single officer query through the agent and return the final answer."""
    final_state = agent.invoke({"messages": [("user", query)]})
    return final_state["messages"][-1].content


if __name__ == "__main__":
    print("Criminal Search Agent")
    print("=" * 50)
    print("Examples:")
    print("  Image search : search for the suspect in John-Doe.jpg")
    print("  Case search  : find cases involving a homicide near the river")
    print("  Type 'quit' to exit.")
    print()

    while True:
        query = input("Officer query > ").strip()
        if query.lower() in ("quit", "exit", "q"):
            break
        if not query:
            continue
        print()
        result = run_query(query)
        print(result)
        print()
