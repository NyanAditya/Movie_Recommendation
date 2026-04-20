import os
import json
import requests
from dotenv import load_dotenv

# Load your API keys from the .env file
load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
LLM_API_KEY = os.getenv("LLM_API_KEY")

def analyze_preferences(user_input):
    """
    Agent 1: Interprets user input and extracts structured preferences.
    """
    system_prompt = """
    You are a movie preference extraction agent. 
    Analyze the user's input and extract the following parameters into a strict JSON format:
    - genres (list of strings)
    - mood (string)
    - time_period (string, e.g., '1980s', '2010s', or null)
    - language (ISO 639-1 code, e.g., 'en', 'hi', or null)
    
    Return ONLY valid JSON. Do not include any other text.
    """
    
    # We will write the actual API call to the LLM here.
    # The LLM will return a JSON string, which we parse:
    # extracted_data = json.loads(llm_response)
    
    # return extracted_data
    pass

def search_movies(structured_query):
    """ Agent 2: Fetches movies from TMDB based on structured query """
    pass

def rank_recommendations(movies, user_input):
    """ Agent 3: Ranks movies using an LLM based on user mood """
    pass