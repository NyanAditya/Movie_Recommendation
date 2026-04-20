import streamlit as st
from agents import analyze_preferences, search_movies, rank_recommendations

# Set up the page configuration
st.set_page_config(
    page_title="Multi-Agent Movie Matcher",
    page_icon="🍿",
    layout="centered"
)

# App Header
st.title("🍿 Multi-Agent Movie Recommender")
st.markdown("""
Tell me what you are in the mood for! My AI agents will:
1. **Analyze** your specific preferences and mood.
2. **Search** a global database for the best matches.
3. **Rank** the top choices with personalized reasons.
""")
st.divider()

# User Input Section
user_input = st.text_area(
    "What are you looking to watch?", 
    placeholder="E.g., I'm stressed from studying algorithms all day and just want to watch a funny 2010s movie in Hindi...",
    height=100
)

# The Magic Button
if st.button("Find My Movie", type="primary"):
    if not user_input.strip():
        st.warning("Please type in your preferences first!")
    else:
        # --- Agent 1: Extraction ---
        with st.spinner("Agent 1 is analyzing your request..."):
            preferences = analyze_preferences(user_input)
            
        if not preferences:
            st.error("Agent 1 failed to process your request. Please try again.")
            st.stop()
            
        # Optional: Show the user what Agent 1 extracted (great for debugging/transparency)
        with st.expander("See what Agent 1 extracted"):
            st.json(preferences)

        # --- Agent 2: Database Search ---
        with st.spinner("Agent 2 is querying the TMDB database..."):
            movies = search_movies(preferences)
            
        if not movies:
            st.warning("Agent 2 couldn't find any movies matching those exact parameters. Try broadening your search!")
            st.stop()

        # --- Agent 3: Ranking ---
        with st.spinner("Agent 3 is reviewing the options and picking the best fits..."):
            final_recs = rank_recommendations(movies, user_input)
            
        if not final_recs or "recommendations" not in final_recs:
            st.error("Agent 3 encountered an issue ranking the movies.")
            st.stop()

        # --- Display Results ---
        st.success("Here are your top personalized picks!")
        
        for i, rec in enumerate(final_recs["recommendations"]):
            st.subheader(f"{i+1}. {rec.get('title', 'Unknown Title')}")
            st.write(f"**Why it fits:** {rec.get('reason', 'No reason provided.')}")
            st.divider()