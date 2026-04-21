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

# --- HCI Feature: Reducing Cognitive Load (Quick Starts) ---
quick_start = st.pills(
    "Quick Starts", 
    ["🍿 Popcorn Night", "😭 Need a Cry", "🧠 Mind-Bending", "🎸 Musical Vibes", "💻 Tech Burnout Cure"]
)

# User Input Section
default_text = quick_start if quick_start else ""
user_input = st.text_area(
    "What are you looking to watch?", 
    value=default_text,
    placeholder="E.g., I'm stressed from studying algorithms all day and just want to watch a funny 2010s movie in Hindi...",
    height=100
)

# The Magic Button
if st.button("Find My Movie", type="primary"):
    if not user_input.strip():
        st.warning("Please type in your preferences or click a Quick Start pill first!")
    else:
        # --- HCI Feature: Visibility of System Status ---
        with st.status("Deploying Agents...", expanded=True) as status:
            
            # Agent 1
            st.write("🕵️‍♂️ Agent 1: Analyzing preferences...")
            preferences = analyze_preferences(user_input)
            
            if not preferences:
                status.update(label="Agent 1 encountered an error.", state="error", expanded=True)
                st.stop()
                
            with st.expander("See what Agent 1 extracted"):
                st.json(preferences)

            # Agent 2
            st.write("🔍 Agent 2: Searching global database...")
            movies = search_movies(preferences)
            
            # --- HCI Feature: Error Prevention & Recovery ---
            if not movies:
                status.update(label="No exact matches found.", state="error", expanded=True)
                st.warning("I couldn't find an exact match for those specific parameters.")
                st.info("💡 Try removing the time period, broadening your mood, or checking out popular trending movies instead!")
                st.stop()

            # Agent 3
            st.write("🧠 Agent 3: Ranking top choices...")
            final_recs = rank_recommendations(movies, user_input)
            
            if not final_recs or "recommendations" not in final_recs:
                status.update(label="Agent 3 encountered an error.", state="error", expanded=True)
                st.stop()

            status.update(label="Recommendations Ready!", state="complete", expanded=False)

        # --- Display Results ---
        st.success("Here are your top personalized picks!")
        
        for i, rec in enumerate(final_recs["recommendations"]):
            st.subheader(f"{i+1}. {rec.get('title', 'Unknown Title')}")
            
            # --- HCI Feature: Explainability & Transparency ---
            st.info(f"**Agent's Thought Process:** {rec.get('reason', 'No reason provided.')}")
            
            # --- HCI Feature: Feedback Loops ---
            feedback = st.feedback("thumbs", key=f"feedback_{i}")
            if feedback == 0:
                st.toast("Noted! I'll avoid movies like this in the future.")
            elif feedback == 1:
                st.toast("Great! I'll look for more like this.")
                
            st.divider()