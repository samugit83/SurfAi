
from openai import OpenAI
import logging
import os
import traceback  
from typing import List
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")


def call_model(chat_history: str = None, model: str = "gpt-4o") -> str:
    client = OpenAI(
        api_key=OPENAI_API_KEY 
    )
    try:
        completion = client.chat.completions.create(
            model=model, 
            messages=chat_history
        )

        answer = completion.choices[0].message.content.strip()
        return answer
    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        logger.error(traceback.format_exc())  
        raise e
    

def create_embeddings(texts_to_embed: List[str], model: str = "text-embedding-ada-002") -> List[List[float]]: 
    client = OpenAI(
        api_key=OPENAI_API_KEY 
    )
    try:
        response = client.embeddings.create(
            model=model,
            input=texts_to_embed
        )
    except Exception as e:
        raise RuntimeError(f"Error while fetching embeddings from OpenAI: {e}")

    embeddings = [entry.embedding for entry in response.data]
    return embeddings