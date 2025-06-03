import asyncio
import os
from agents import Agent, Runner, WebSearchTool, function_tool, ItemHelpers, trace
from openai import OpenAI
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timedelta



load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")



@function_tool
def research_destinations(continent: str, budget: float, duration_weeks: int):
    print(f"Researching travel destinations in {continent} for {duration_weeks} weeks with budget ${budget}...")

    client = OpenAI(api_key=OPENAI_API_KEY)

    response = client.responses.create(
        model="gpt-4o",
        input=[
            {"role": "user", "content": f"I want to travel to {continent} for {duration_weeks} weeks with a total budget of ${budget}. \n\n"
                                         f"Research and suggest 3-5 destinations that would fit my budget, including:\n"
                                         f"1. Best cities/countries to visit\n"
                                         f"2. Approximate cost breakdown (accommodation, food, transportation, activities)\n"
                                         f"3. Best time to visit\n"
                                         f"4. Must-see attractions\n"}
        ],
        max_output_tokens=3000
    )

    return response.output_text

@function_tool
def plan_itinerary(destinations: str, budget: float, duration_weeks: int):
    print(f"Planning detailed itinerary for {duration_weeks} weeks...")

    today = datetime.now()
    end_date = today + timedelta(weeks=duration_weeks)
    date_range = f"{today.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}"

    client = OpenAI(api_key=OPENAI_API_KEY)

    response = client.responses.create(
        model="gpt-4o",
        input=[
            {"role": "user", "content": f"Based on these destinations and information:\n{destinations}\n\n"
                                         f"Create a detailed day-by-day itinerary for a {duration_weeks}-week trip with a total budget of ${budget}.\n"
                                         f"Trip dates: {date_range}\n\n"
                                         f"For each day include:\n"
                                         f"1. Location/city\n"
                                         f"2. Accommodation details with approximate cost\n"
                                         f"3. Morning, afternoon, and evening activities with approximate costs\n"
                                         f"4. Transportation details with approximate costs\n"
                                         f"5. Food recommendations with approximate costs\n"
                                         f"6. Any travel tips for that specific location\n"
                                         f"7. Running total of expenses to ensure we stay within the ${budget} budget\n"}
        ],
        max_output_tokens=4000
    )

    return response.output_text

@function_tool
def get_budget_tips(destinations: str, budget: float):
    print(f"Getting budget travel tips for ${budget}...")

    client = OpenAI(api_key=OPENAI_API_KEY)

    response = client.responses.create(
        model="gpt-4o",
        input=[
            {"role": "user", "content": f"For these destinations:\n{destinations}\n\n"
                                         f"Provide specific budget travel tips to help me stay within my ${budget} total budget, including:\n"
                                         f"1. Money-saving accommodation strategies (hostels, guesthouses, Airbnb, etc.)\n"
                                         f"2. Affordable transportation options (public transit, budget airlines, etc.)\n"
                                         f"3. Eating on a budget (street food, markets, cooking)\n"
                                         f"4. Free or low-cost activities and attractions\n"
                                         f"5. Best times to visit for lower prices\n"
                                         f"6. Local budget travel hacks\n"}
        ],
        max_output_tokens=2500
    )

    return response.output_text


@dataclass
class TravelItinerary:
    continent: str
    budget: float
    duration_weeks: int
    destinations: str
    daily_plan: str
    budget_tips: str
    total_cost_estimate: float


travel_planner_agent = Agent(
    name="Travel Planner Agent",
    instructions="""You are an expert travel planner specializing in budget-friendly trips.
                    You help users plan detailed travel itineraries based on their budget, trip duration, and preferred continent.
                    You will research suitable destinations within budget, create a day-by-day itinerary, and provide budget travel tips.
                    You should ensure the total estimated cost of the trip stays within the user's budget.
                    You may search the web for up-to-date information on destinations, accommodations, transportation, and activities.
                    Your itineraries should be realistic, practical, and include specific details on costs, accommodations, and activities.""",
    model="gpt-4o",
    tools=[research_destinations,
           plan_itinerary,
           get_budget_tips,
           WebSearchTool(),
           ],
    output_type=TravelItinerary,
)


def extract_cost_estimate(itinerary_text: str) -> float:
    try:
        import re
        cost_patterns = [
            r"Total estimated cost:?\s*\$([\d,]+(?:\.\d+)?)",
            r"Total cost:?\s*\$([\d,]+(?:\.\d+)?)",
            r"Total budget:?\s*\$([\d,]+(?:\.\d+)?)",
            r"Total expenses:?\s*\$([\d,]+(?:\.\d+)?)"
        ]
        
        for pattern in cost_patterns:
            matches = re.search(pattern, itinerary_text, re.IGNORECASE)
            if matches:
                return float(matches.group(1).replace(',', ''))
        
        return 0.0
    except Exception as e:
        print(f"Error extracting cost estimate: {str(e)}")
        return 0.0


async def main(budget: float = 3000, duration_weeks: int = 2, continent: str = "Europe"):
    msg = f"Plan a {duration_weeks}-week trip to {continent} with a budget of ${budget}."

    input_items = [{"content": msg, "role": "user"}]

    with trace("Planning travel itinerary"):
        result = await Runner.run(travel_planner_agent, input_items)
        output = ItemHelpers.text_message_outputs(result.new_items)
        print("Generated Itinerary:\n", output)
        return output


if __name__ == "__main__":
    asyncio.run(main(budget=3000, duration_weeks=2, continent="Europe"))







