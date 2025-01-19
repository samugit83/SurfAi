import os
import openai
import chromadb
from dotenv import load_dotenv

# Load environment variables once when the module is imported
load_dotenv()

def retrieve_documents(query, k=5):
    """
    Retrieves the top-k most similar documents from the specified Chroma collection based on the query,
    using OpenAI embeddings and a persistent Chroma client.
    
    Args:
        query (str): The query string to search for.
        k (int): Number of top similar documents to retrieve.
        collection_name (str, optional): Name of the collection to query. Defaults to "general" if not provided.
        
    Returns:
        dict: A dictionary containing retrieved documents and their metadata.
    """
    openai.api_key = os.getenv("OPENAI_API_KEY")
    
    # Use the DB_PATH from environment or default to .chroma
    db_path = os.getenv("DB_PATH") or ".chroma"
    
    collection_name = "general"

    # Initialize a persistent Chroma client
    try:
        client = chromadb.PersistentClient(path=db_path)
    except TypeError as e:
        raise RuntimeError(f"Error initializing Chroma client: {e}")

    # Access the specified collection or create it if it doesn't exist
    collection = client.get_or_create_collection(name=collection_name)

    # Use OpenAI API to compute the embedding for the query
    try:
        response = openai.embeddings.create(
            model="text-embedding-ada-002",
            input=[query]
        )
    except Exception as e:
        raise RuntimeError(f"Error while fetching embedding from OpenAI: {e}")

    # Extract the query embedding from the response using .data attribute
    query_embedding = [response.data[0].embedding]

    # Query the collection for similar documents
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=k,
        include=["documents", "metadatas"]
    )

    print(results)

    return results
