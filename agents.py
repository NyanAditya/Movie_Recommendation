import os
import json
import requests
from dotenv import load_dotenv

# Load API keys
load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY") 

def analyze_preferences(user_input):
    """ Agent 1: Interprets user input and extracts structured preferences. """
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    system_prompt = """
    You are a movie preference extraction agent. 
    Analyze the user's input and extract the following parameters into a strict JSON format:
    {
        "genres": ["list", "of", "strings"],
        "mood": "string or null",
        "time_period": "string (e.g., '1980s', '2010s') or null",
        "language": "ISO 639-1 code (e.g., 'en', 'hi') or null"
    }
    Return ONLY valid JSON.
    """
    
    payload = {
        "model": "llama-3.1-8b-instant", 
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        "temperature": 0.1 
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status() 
        llm_output = response.json()['choices'][0]['message']['content']
        return json.loads(llm_output)
    except Exception as e:
        print(f"Error in Agent 1: {e}")
        return None

def get_tmdb_genre_id(genre_name):
    """ Helper function to map string genres to TMDB IDs. """
    genre_map = {
        "action": 28, "adventure": 12, "animation": 16, "comedy": 35,
        "crime": 80, "documentary": 99, "drama": 18, "family": 10751,
        "fantasy": 14, "history": 36, "horror": 27, "music": 10402,
        "mystery": 9648, "romance": 10749, "science fiction": 878,
        "sci-fi": 878, "thriller": 53, "war": 10752, "western": 37
    }
    return genre_map.get(genre_name.lower())

def search_movies(structured_query):
    """ Agent 2: Fetches movies from TMDB based on the structured query. """
    if not structured_query:
        return []

    url = "https://api.themoviedb.org/3/discover/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "sort_by": "popularity.desc", 
        "page": 1
    }

    if structured_query.get("language"):
        params["with_original_language"] = structured_query["language"]

    if structured_query.get("genres"):
        genre_ids = []
        for genre in structured_query["genres"]:
            gid = get_tmdb_genre_id(genre)
            if gid:
                genre_ids.append(str(gid))
        if genre_ids:
            params["with_genres"] = ",".join(genre_ids)

    time_period = structured_query.get("time_period")
    if time_period and "s" in time_period:
        try:
            decade_start = int(time_period.replace("s", ""))
            params["primary_release_date.gte"] = f"{decade_start}-01-01"
            params["primary_release_date.lte"] = f"{decade_start + 9}-12-31"
        except ValueError:
            pass 

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        movies = response.json().get('results', [])
        
        cleaned_movies = []
        for movie in movies[:10]: 
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
    """ Agent 3: Ranks movies using an LLM based on user mood. """
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
    
    user_content = f"User Request: '{user_input}'\n\nAvailable Movies: {json.dumps(movies)}"

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "temperature": 0.3 
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        llm_output = response.json()['choices'][0]['message']['content']
        return json.loads(llm_output)
    except Exception as e:
        print(f"Error during Recommendation Ranking: {e}")
        return None