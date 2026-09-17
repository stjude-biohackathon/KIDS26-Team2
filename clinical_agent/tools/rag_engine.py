import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from openai import AzureOpenAI

load_dotenv()

# 1. AI Foundry Client (for embeddings)
ai_client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_AI_FOUNDRY_ENDPOINT"),
    api_key=os.getenv("AZURE_AI_FOUNDRY_API_KEY"),
    api_version="2024-02-01" 
)

# 2. Azure AI Search Client (for retrieving notes)
search_client = SearchClient(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
    credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_API_KEY"))
)

def search_discharge_notes(search_term: str) -> str:
    """Performs hybrid vector + keyword search on clinical notes."""
    try:
        # Generate the embedding vector for the search string
        embedding_res = ai_client.embeddings.create(
            input=[search_term],
            model=os.getenv("AZURE_EMBEDDING_DEPLOYMENT")
        )
        query_vector = embedding_res.data[0].embedding
        
        # Configure the vectorized query
        # NOTE: Ensure "text_vector" exactly matches the vector field name in your Azure Search index
        vector_query = VectorizedQuery(
            vector=query_vector, 
            k_nearest_neighbors=3, 
            fields="content_vector" 
        )

        # Execute Hybrid Search
        results = search_client.search(
            search_text=search_term,
            vector_queries=[vector_query],
            top=3
        )
        
        notes = []
        for doc in results:
            note_id = doc.get("note_id", "N/A")
            # Adjust "content" to "text" if your Azure index schema uses a different name
            text = doc.get("content") or doc.get("text", "") 
            notes.append(f"[Note ID: {note_id}]\n{text.strip()}")
            
        return "\n\n---\n\n".join(notes) if notes else "No relevant notes found."
    except Exception as e:
        return f"Search Error: {str(e)}"