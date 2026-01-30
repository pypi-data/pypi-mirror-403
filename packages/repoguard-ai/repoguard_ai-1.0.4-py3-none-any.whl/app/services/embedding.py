from dotenv import load_dotenv
load_dotenv()

from google import genai
import os


client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
def embed(text:list[str])->list[list[float]]:
    if not text:
        return []
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents= text
    )
    embeds=[]
    for e in result.embeddings:
        embeds.append(e.values)
    return embeds

