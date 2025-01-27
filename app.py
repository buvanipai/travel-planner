import streamlit as st
from openai import OpenAI
import time

# Initialize the OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# System prompt for GPT
SYSTEM_PROMPT = (
    "You are an AI travel planner, Generate a highly personalized travel itinerary based on the users preferences. Your response must be structured and formatted as follows:\n"
    "1. Accommodation options: Provide options according to the given budget and location. Consider budget over location preference.\n"
    "2. Provide the day-day plan: include activities, meal recommendations (consider dietary preferences) and travel details between locations. Keep in mind the Interest Type to help provide better recommendations.\n"
    "3. Categorized info: break down the activities into categories (eg. adventure, relaxation, cultural) for replacements based on mood.\n"
    "4. Budget breakdown: Provide the budget estimates based on the plan in the currency provided as well as suggestions where money can be saved.\n"
    "5. Local Tips: share location based tips and suggestions about the destination/activities, including emergency contact details.\n"
    "6. Additionally, provide the best time to visit the location.\n"
    "While making the plans, you need to consider the users interests, accommodation preferences, mobility concerns (walk limit, wheelchair accessibility, etc.), time preference for the activity, travel pace, companion preference and if there are any partial or specific notes like \"offbeat places\" or prior commitments."
)

# Initialize session state variables
if "step" not in st.session_state:
    st.session_state["step"] = "general_details"
if "itinerary" not in st.session_state:
    st.session_state["itinerary"] = ""
if "additional_context" not in st.session_state:
    st.session_state["additional_context"] = ""

# App Title
st.title("AI Travel Planner")

# Step 1: General Details
if st.session_state["step"] == "general_details":
    st.header("Step 1: General Details")
    destination = st.text_input("Destination", "Paris")
    trip_duration = st.slider("Trip Duration (Days)", 1, 14, 3)
    budget = st.selectbox("Budget", ["Luxury", "Moderate", "Budget-Friendly"])
    currency = st.text_input("Currency (eg. USD, CAD, INR, etc.)", "")
    purpose = st.multiselect("Purpose of the trip", ["Leisure", "Business", "Family", "Adventure", "Cultural"])

    if st.button("Next: Add Preferences"):
        st.session_state["general_details"] = {
            "destination": destination,
            "trip_duration": trip_duration,
            "budget": budget,
            "currency": currency,
            "purpose": purpose,
        }
        st.session_state["step"] = "preferences"

# Step 2: Preferences
if st.session_state["step"] == "preferences":
    st.header("Step 2: Preferences")
    dietary = st.text_area("Dietary Preferences", "Vegetarian, vegan, etc.")
    interests = st.text_area("Interests", "Food, culture, adventure, etc.")
    accommodation = st.selectbox("Accommodation Type", ["Luxury", "Budget-friendly", "Central Location"])
    mobility = st.text_area("Mobility Concerns", "Wheelchair accessible, etc.")

    if st.button("Next: Add Activity Preferences"):
        st.session_state["preferences"] = {
            "dietary": dietary,
            "interests": interests,
            "accommodation": accommodation,
            "mobility": mobility,
        }
        st.session_state["step"] = "activity_preferences"

# Step 3: Activity Preferences
if st.session_state["step"] == "activity_preferences":
    st.header("Step 3: Activity Preferences")
    interest_type = st.selectbox("Type of Interest", ["Top-rated attractions", "Hidden gems"])
    time_preference = st.selectbox("Preferred Time for Activities", ["Morning", "Evening", "All-day"])
    travel_pace = st.radio("Travel Pace", ["Relaxed", "Moderate", "Packed"])
    companion = st.selectbox("Companion Type", ["Solo", "Family", "Group"])

    if st.button("Generate Initial Itinerary"):
        st.session_state["activity_preferences"] = {
            "interest_type": interest_type,
            "time_preference": time_preference,
            "travel_pace": travel_pace,
            "companion": companion,
        }

        # Prepare user input for OpenAI
        user_input = (
            f"Destination: {st.session_state['general_details']['destination']}\n"
            f"Trip Duration: {st.session_state['general_details']['trip_duration']} days\n"
            f"Budget: {st.session_state['general_details']['budget']} {st.session_state['general_details']['currency']}\n"
            f"Purpose: {st.session_state['general_details']['purpose']}\n"
            f"Dietary Preferences: {st.session_state['preferences']['dietary']}\n"
            f"Interests: {st.session_state['preferences']['interests']}\n"
            f"Accommodation: {st.session_state['preferences']['accommodation']}\n"
            f"Mobility Concerns: {st.session_state['preferences']['mobility']}\n"
            f"Interest Type: {st.session_state['activity_preferences']['interest_type']}\n"
            f"Time Preference: {st.session_state['activity_preferences']['time_preference']}\n"
            f"Travel Pace: {st.session_state['activity_preferences']['travel_pace']}\n"
            f"Companion Type: {st.session_state['activity_preferences']['companion']}\n"
        )

        # Generate itinerary using OpenAI
        with st.spinner("Generating your itinerary..."):
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_input},
                ],
                temperature=0.7,
                max_tokens=2048,
            )
            st.session_state["itinerary"] = response.choices[0].message.content
            st.session_state["step"] = "review"

# Step 4: Review and Refine
if st.session_state["step"] == "review":
    st.header("Your Initial Itinerary")
    st.markdown(st.session_state["itinerary"], unsafe_allow_html=True)

    st.subheader("Do you want to refine your itinerary or confirm it?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Refine Itinerary"):
            st.session_state["step"] = "refinement"

    with col2:
        if st.button("Confirm Itinerary"):
            st.success("Your itinerary has been finalized! You can copy or print it below.")
            st.session_state["step"] = "final"

# Step 5: Refinement
if st.session_state["step"] == "refinement":
    st.header("Refine Your Itinerary")
    additional_context = st.text_area("Add specific notes or preferences (e.g., add a day trip to a nearby city).")

    if st.button("Submit Refinement"):
        # Update refinement input
        st.session_state["additional_context"] = additional_context

        # Refine the itinerary using OpenAI
        with st.spinner("Refining your itinerary..."):
            refinement_prompt = (
                f"Here is the current itinerary:\n{st.session_state['itinerary']}\n\n"
                f"Refinement Notes: {st.session_state['additional_context']}\n\n"
                "Please refine the itinerary and include the requested changes."
            )

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": refinement_prompt},
                ],
                temperature=0.7,
                max_tokens=2048,
            )
            st.session_state["itinerary"] = response.choices[0].message.content
            st.session_state["step"] = "review"
            st.rerun()

# Step 6: Final Step
if st.session_state["step"] == "final":
    st.header("Finalized Itinerary")
    st.markdown(st.session_state["itinerary"], unsafe_allow_html=True)

    # Copy or Print Options
    if st.button("Copy Itinerary"):
        st.success("Use CTRL+C or CMD+C to copy it and CTRL+V or CMD+V to paste it where you need.")
    if st.button("Print Itinerary"):
        st.info("Use your browser's print function (CTRL+P or CMD+P) to print this itinerary.")