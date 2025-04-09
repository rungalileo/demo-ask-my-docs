from openai import OpenAI
from dotenv import load_dotenv
import os
import numpy as np

load_dotenv()

# Initialize OpenAI client at module level
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set.")
client = OpenAI(api_key=api_key)

# Recommended embedding model
EMBEDDING_MODEL = "text-embedding-3-small"

def ask_openai(
    user_content,
    system_content="You are a smart assistant", 
    model="gpt-4o-mini"
):
    # Removed client initialization from here
    # api_key = os.getenv("OPENAI_API_KEY")
    # client = OpenAI(api_key=api_key)
    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content},
            ]
        )
        output = response.choices[0].message.content.replace("```markdown", "").replace("```code", "").replace("```html", "").replace("```", "")
        return output
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return "Sorry, I encountered an error trying to get an answer."

# New function to get embeddings
def get_embeddings(texts: list[str], model=EMBEDDING_MODEL) -> list[np.ndarray]:
    """Generates embeddings for a list of texts using OpenAI.
    Args:
        texts (list[str]): A list of text strings to embed.
        model (str): The embedding model to use.
    Returns:
        list[np.ndarray]: A list of embeddings as numpy arrays.
    """
    try:
        # Replace newlines for better embedding performance
        texts = [text.replace("\n", " ") for text in texts]
        data = client.embeddings.create(input=texts, model=model).data
        return [np.array(embedding.embedding) for embedding in data]
    except Exception as e:
        print(f"Error calling OpenAI Embedding API: {e}")
        # Return empty list or handle error as appropriate
        return []