from langchain_huggingface import HuggingFaceEmbeddings
from langchain_neo4j import Neo4jVector

def retriever(query: str, k: int = 5):
    """Search LinkedIn posts - that's it"""
    
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    graph_store = Neo4jVector.from_existing_index(
        embedding=embeddings,
        url="neo4j+s://b41f27a4.databases.neo4j.io",
        username="neo4j",
        password="qJ5k8-WgK7QPU3fx6kgM7RyVRBSZg0Swn_5OjKDL8mE",
        index_name="linkedin_posts_index"
    )

    return graph_store.similarity_search(query, k=k)

