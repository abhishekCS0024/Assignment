import os
import time
import json
import re
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_neo4j import Neo4jVector
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
load_dotenv()

def clean_text(t: str):
    """Removes invalid UTF-8, surrogate pairs, broken emojis, null bytes."""
    if not isinstance(t, str):
        return ""
    t = t.replace("\x00", "")                                  
    t = t.encode("utf-8", "ignore").decode("utf-8")           
    t = re.sub(r"[\ud800-\udfff]", "", t)                     
    return t.strip()



embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

# Load your data
with open("enriched_posts.json", "r", encoding="utf-8") as f:
    posts_data = json.load(f)

# Create documents
documents = []
for i, post in enumerate(posts_data):
    post_text = clean_text(post.get("text", ""))
    if not post_text:
        continue
    
    doc = Document(
        page_content=post_text,
        metadata={
            "post_id": i,
            "engagement": int(post.get("engagement", 0)),
            "language": post.get("language", "Unknown"),
            "tags": post.get("tags", []),
            "tone": post.get("tone", "Neutral"),
            "line_count": int(post.get("line_count", 0)),
            "preview": post_text[:200]
        }
    )
    documents.append(doc)

# Split documents
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(documents)
chunks = [c for c in chunks if c.page_content.strip()]

# CREATE NEO4J VECTOR STORE 
vector_store = Neo4jVector.from_documents(
    documents=chunks,
    embedding=embeddings,
    url="neo4j+s://b41f27a4.databases.neo4j.io",
    username="neo4j",
    password="qJ5k8-WgK7QPU3fx6kgM7RyVRBSZg0Swn_5OjKDL8mE",
    database="neo4j",
    index_name="linkedin_posts_index",
    node_label="LinkedInPost",
    text_node_property="text",
    embedding_node_property="embedding",
    distance_strategy="COSINE",
    pre_delete_collection=True
)

# CREATE RETRIEVER 
retriever = vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 5}
)

print("Migration complete! Neo4j vector store ready.")
