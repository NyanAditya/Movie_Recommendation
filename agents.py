import os
import json
import requests
from dotenv import load_dotenv

# Load your API keys from the .env file
load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
# Make sure your .env file has this exact variable name: GROQ_API_KEY=your_key_here
GROQ_API_KEY = os.getenv("GROQ_API_KEY") 

def analyze_preferences(user_input):
    """
    Agent 1: Interprets user input and extracts structured preferences using Groq.
    """
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # The system prompt acts as our strict extraction rulebook
    system_prompt = """
    You are a movie preference extraction agent. 
    Analyze the user's input and extract the following parameters into a strict JSON format:
    {
        "genres": ["list", "of", "strings"],
        "mood": "string or null",
        "time_period": "string (e.g., '1980s', '2010s') or null",
        "language": "ISO 639-1 code (e.g., 'en', 'hi') or null"
    }
    Return ONLY valid JSON. Do not include any markdown formatting, conversational text, or explanations.
    """
    
    payload = {
        "model": "llama-3.1-8b-instant", # Updated to Groq's current fast model
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        # Removed the response_format parameter; Llama 3.1 is smart enough 
        # to output JSON based solely on our strict system prompt.
        "temperature": 0.1 
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status() 
        
        llm_output = response.json()['choices'][0]['message']['content']
        structured_data = json.loads(llm_output)
        return structured_data
        
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        # This is the magic line: it prints the exact reason Groq rejected the request
        print(f"Details from Groq: {e.response.text}") 
        return None
    except Exception as e:
        print(f"General Error: {e}")
        return None
    
# --- Placeholders for our next agents ---

def get_tmdb_genre_id(genre_name):
    """Helper function to map string genres to TMDB IDs."""
    # TMDB standard genre mappings
    genre_map = {
        "action": 28, "adventure": 12, "animation": 16, "comedy": 35,
        "crime": 80, "documentary": 99, "drama": 18, "family": 10751,
        "fantasy": 14, "history": 36, "horror": 27, "music": 10402,
        "mystery": 9648, "romance": 10749, "science fiction": 878,
        "sci-fi": 878, "thriller": 53, "war": 10752, "western": 37
    }
    return genre_map.get(genre_name.lower())

def search_movies(structured_query):
    """
    Agent 2: Fetches movies from TMDB based on the structured query from Agent 1.
    """
    if not structured_query:
        return []

    url = "https://api.themoviedb.org/3/discover/movie"
    
    # We build the query parameters dynamically based on what Agent 1 found
    params = {
        "api_key": TMDB_API_KEY,
        "sort_by": "popularity.desc", # Get the most popular matches first
        "page": 1
    }

    # 1. Handle Language
    if structured_query.get("language"):
        params["with_original_language"] = structured_query["language"]

    # 2. Handle Genres
    if structured_query.get("genres"):
        genre_ids = []
        for genre in structured_query["genres"]:
            gid = get_tmdb_genre_id(genre)
            if gid:
                genre_ids.append(str(gid))
        if genre_ids:
            # TMDB uses a comma-separated string for multiple genres
            params["with_genres"] = ",".join(genre_ids)

    # 3. Handle Time Period (Decades)
    time_period = structured_query.get("time_period")
    if time_period and "s" in time_period:
        try:
            # Extracts the year (e.g., '2010' from '2010s')
            decade_start = int(time_period.replace("s", ""))
            params["primary_release_date.gte"] = f"{decade_start}-01-01"
            params["primary_release_date.lte"] = f"{decade_start + 9}-12-31"
        except ValueError:
            pass # If the LLM returns something weird, we just ignore the date filter

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        # TMDB returns a list of movies under the 'results' key
        movies = response.json().get('results', [])
        
        # Let's clean up the data so Agent 3 doesn't get overwhelmed with useless fields
        cleaned_movies = []
        for movie in movies[:10]: # Just take the top 10 results to save LLM tokens later
            cleaned_movies.append({
                "title": movie.get("title"),
                "release_date": movie.get("release_date"),
                "overview": movie.get("overview"),
                "popularity": movie.get("popularity")
            })
            
        return cleaned_movies

    except requests.exceptions.RequestException as e:
        print(f"Error fetching from TMDB: {e}")
        return []
    
def rank_recommendations(movies, user_input):
    """ Agent 3: Ranks movies using an LLM based on user mood """
    if not movies:
        return {"recommendations": []}

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    system_prompt = """
    You are a movie recommendation expert. 
    I will give you a user's request and a list of movies fetched from a database.
    Your job is to select the top 3 best matches based on the user's specific mood and preferences.
    Return the result as strict JSON in this format:
    {
        "recommendations": [
            {
                "title": "Movie Title",
                "reason": "1-2 sentences explaining why this specifically fits the user's mood."
            }
        ]
    }
    Return ONLY valid JSON.
    """
    
    # We combine the user's original request and the TMDB data into one prompt
    user_content = f"User Request: '{user_input}'\n\nAvailable Movies: {json.dumps(movies)}"

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.3 # Slightly higher temperature here for better reasoning
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        llm_output = response.json()['choices'][0]['message']['content']
        return json.loads(llm_output)
        
    except Exception as e:
        print(f"Error during Recommendation Ranking: {e}")
        return None

# --- Quick Test Block ---
if __name__ == "__main__":
    test_input = "I'm stressed from studying algorithms all day and just want to watch a funny 2010s movie in Hindi."
    
    print("Testing Agent 1 (Extraction)...")
    preferences = analyze_preferences(test_input)
    print(f"Extracted: {preferences}\n")
    
    print("Testing Agent 2 (TMDB Search)...")
    movie_results = search_movies(preferences)
    print(f"Found {len(movie_results)} movies.\n")
    
    print("Testing Agent 3 (Ranking)...")
    final_recs = rank_recommendations(movie_results, test_input)
    print(json.dumps(final_recs, indent=2))