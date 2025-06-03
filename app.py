import streamlit as st
import asyncio
import json
from agent import travel_planner_agent, Runner, ItemHelpers, extract_cost_estimate

if 'agent_running' not in st.session_state:
    st.session_state.agent_running = False

st.set_page_config(
    page_title="AutoPlnr - Travel like a local",
    page_icon="✈️",
    layout="wide"
)

st.title("✈️ AutoPlnr - Travel like a local")
st.markdown("""
This app helps you plan your dream vacation on a budget. 
Enter your budget, trip duration, and preferred continent, and our AI agent will create a detailed travel itinerary for you.
""")

st.header("Trip Parameters")
col1, col2, col3 = st.columns(3)

with col1:
    budget = st.number_input("Total Budget (USD)", min_value=500, max_value=20000, value=3000, step=500)
    st.caption("Your total budget for the entire trip including accommodation, food, transportation, and activities.")

with col2:
    duration_weeks = st.slider("Trip Duration (Weeks)", min_value=1, max_value=8, value=2, step=1)
    st.caption(f"Your trip will be {duration_weeks} weeks ({duration_weeks * 7} days) long.")

with col3:
    continent_options = ["Europe", "Asia", "North America", "South America", "Africa", "Oceania"]
    continent = st.selectbox("Preferred Continent", options=continent_options, index=0)
    st.caption("Select the continent you'd like to visit.")

with st.expander("Additional Preferences (Optional)"):
    travel_style = st.multiselect(
        "Travel Style", 
        ["Adventure", "Cultural", "Relaxation", "Food & Culinary", "Nature", "Urban", "Historical"],
        default=["Cultural", "Food & Culinary"]
    )
    
    accommodation_type = st.multiselect(
        "Preferred Accommodation",
        ["Hostel", "Budget Hotel", "Mid-range Hotel", "Airbnb/Apartment", "Guesthouse"],
        default=["Hostel", "Budget Hotel", "Airbnb/Apartment"]
    )

async def run_agent(budget, duration_weeks, continent, travel_style=None, accommodation_type=None):
    try:
        msg = f"Plan a {duration_weeks}-week trip to {continent} with a budget of ${budget}."
        
        if travel_style:
            msg += f" I prefer {', '.join(travel_style)} travel experiences."
            
        if accommodation_type:
            msg += f" For accommodation, I prefer {', '.join(accommodation_type)}."

        input_items = [{"content": msg, "role": "user"}]

        result = await Runner.run(travel_planner_agent, input_items)
        return result, None
    except Exception as e:
        return None, str(e)

if st.button("Plan My Trip", type="primary", disabled=st.session_state.agent_running):
    # Set agent_running to True when processing starts
    st.session_state.agent_running = True
    with st.spinner("Planning your trip... This may take a few minutes as we research the best options for you."):
        travel_preferences = travel_style if 'travel_style' in locals() else None
        accommodation_preferences = accommodation_type if 'accommodation_type' in locals() else None
        
        result, error = asyncio.run(run_agent(
            budget, 
            duration_weeks, 
            continent,
            travel_preferences,
            accommodation_preferences
        ))

        if error:
            st.error(f"Error: {error}")
        else:
            st.header("Your Travel Itinerary")
            output = ItemHelpers.text_message_outputs(result.new_items)

            try:
                parsed_output = json.loads(output)
                itinerary = parsed_output.get("response", {})
                
                continent = itinerary.get("continent", continent)
                budget_amount = itinerary.get("budget", budget)
                duration = itinerary.get("duration_weeks", duration_weeks)
                destinations = itinerary.get("destinations", "")
                daily_plan = itinerary.get("daily_plan", "")
                budget_tips = itinerary.get("budget_tips", "")
                total_cost = itinerary.get("total_cost_estimate", 0.0)
                
                summary_col1, summary_col2 = st.columns(2)
                with summary_col1:
                    st.subheader("Trip Summary")
                    st.markdown(f"**Continent:** {continent}")
                    st.markdown(f"**Duration:** {duration} weeks")
                    st.markdown(f"**Budget:** ${budget_amount:,.2f}")
                    if total_cost > 0:
                        st.markdown(f"**Estimated Total Cost:** ${total_cost:,.2f}")
                        if total_cost <= budget_amount:
                            st.success(f"✅ Under budget by ${budget_amount - total_cost:,.2f}")
                        else:
                            st.warning(f"⚠️ Over budget by ${total_cost - budget_amount:,.2f}")
                
                st.subheader("Recommended Destinations")
                st.markdown(destinations)
                
                st.subheader("Day-by-Day Itinerary")
                st.markdown(daily_plan)
                
                with st.expander("Budget Travel Tips", expanded=True):
                    st.markdown(budget_tips)
                
                st.download_button(
                    label="Download Full Itinerary",
                    data=f"# TRAVEL ITINERARY\n\n## Trip Summary\n\nContinent: {continent}\nDuration: {duration} weeks\nBudget: ${budget_amount:,.2f}\nEstimated Cost: ${total_cost:,.2f}\n\n## Destinations\n\n{destinations}\n\n## Daily Itinerary\n\n{daily_plan}\n\n## Budget Tips\n\n{budget_tips}",
                    file_name="travel_itinerary.md",
                    mime="text/markdown"
                )
                
            except Exception as e:
                st.error(f"Error parsing the itinerary: {str(e)}")
                st.text_area("Raw Output", output, height=300)
        
        st.session_state.agent_running = False

st.markdown("---")
st.caption("Made with </> by Syed | syedhusain.com")

