from openai import OpenAI
import json

# Set up your OpenAI API key
client = OpenAI(api_key='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')

def get_user_input():
    """
    Collects user input describing desired location attributes.
    """
    user_input = input("Please describe what you're looking for in a location (e.g., 'good schools, low crime, affordable housing'): ")
    return user_input

def query_llm(prompt):
    """
    Sends the user's input to the OpenAI API using the chat completion endpoint and returns the generated response.
    """
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an assistant that provides insights about real estate location, appreciation, turnover, proximity to things, and all things related to finding the right property."},
            {"role": "user", "content": f"Analyze the following requirements and find the best cities, then further best neighborhoods within those cities, and provide the reasons why they align. I want the top 3 options and main reasons each were recommended. I also want a detailed analysis of how each correlates to all of my preferences. Based on my input, also tell me the optimal house features I can afford or would be average in that area. Consider all of the following and outline it as it pertains to each neighborhood: School Quality, Rental Demand, Crime Rates, Job Growth, Flooding & Natural Disaster Risk, Insurance Costs, Property Turnover Rates, Local Amenities, Demographics, Tax Rates, Market Trends, Walkability, Commute Times, Neighborhood Development, Environmental Factors, Healthcare Access, Future Urban Planning, Short-term Rental Viability, Historical Appreciation Rates, Foreclosure Rates, Mortgage and Lending Environment, Utility Costs, Cultural and Recreational Opportunities, Community Involvement, Local Economic Health, Education Opportunities, Public Transport Accessibility, Energy Efficiency and Sustainability, HOA Regulations and Fees, Cultural Fit, Market Saturation, Buyer Incentives, Investment Return Projections, Long-Term Viability, Pet-Friendliness, Technology Infrastructure, Curb Appeal and Aesthetic Quality, Community Services, Vacancy Rates, Tourism Impact, Historical Significance, Things to Do, Nightlife and Entertainment, Family-Friendly Features, Good for Young Singles, Good for Older Residents, Starter Homes, Local Sports Teams and Events, Concerts and Cultural Events, Restaurant and Dining Options, Age Demographics, Economic Demographics, Health and Wellness, Seasonal Considerations, Social and Cultural Fit, Access to Shopping, Proximity to Parks and Outdoor Spaces, Neighborhood Safety. Finally, run a comparison between all of the results and weigh out which ones are stronger and weaker in certain areas than others:\n\n{json.dumps(prompt, indent=2)}"}
        ],
        max_tokens=4096
    )
    return response.choices[0].message.content.strip()

def query_llm_for_data_analysis(neighborhood_analysis):
    """
    Takes the LLM's neighborhood analysis response and sends it to another LLM call 
    to gather specific numerical data and comparisons for each recommended area.
    Returns consistent metrics each time.
    """
    structured_prompt = f"""
    Based on the following neighborhood analysis, I need you to provide specific numerical data for each area. 
    Please return the following metrics for each neighborhood:
    
    - Average House Cost
    - School Ratings (out of 10)
    - Average Demographics (Age, Income, etc.)
    - Average Insurance Cost (Annual)
    - Things to Do Rating (out of 10)
    - Job Growth Rate (Annual Percentage)
    - Crime Rates (per 1,000 residents)
    - Rental Demand (Vacancy Rate)
    - Walkability Score (out of 100)
    - Property Turnover Rate (Annual Percentage)
    
    Please structure the response in the following format:
    
    Neighborhood 1:
    - Average House Cost: $XXX,XXX
    - School Ratings: X/10
    - Average Demographics: Age: XX, Income: $XX,XXX
    - Average Insurance Cost: $X,XXX per year
    - Things to Do Rating: X/10
    - Job Growth Rate: X%
    - Crime Rates: X per 1,000 residents
    - Rental Demand: X% vacancy rate
    - Walkability Score: XX/100
    - Property Turnover Rate: X%
    
    Neighborhood 2:
    - [Same structure as above]
    
    Neighborhood 3:
    - [Same structure as above]
    
    Here is the neighborhood analysis to base the data on:
    {neighborhood_analysis}
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an assistant that gathers specific numerical data for real estate areas."},
            {"role": "user", "content": structured_prompt}
        ],
        max_tokens=4096
    )
    return response.choices[0].message.content.strip()

def main():
    """
    Main function to handle the process of gathering user input, processing it with OpenAI, 
    performing further analysis, and outputting the results.
    """
    try:
        # Step 1: Get user input
        user_input = get_user_input()

        # Step 2: Send input to OpenAI API for initial neighborhood analysis
        neighborhood_analysis = query_llm(user_input)
        print("Neighborhood Analysis:")
        print(neighborhood_analysis)

        # Step 3: Send neighborhood analysis to another LLM call to gather specific data
        detailed_data_analysis = query_llm_for_data_analysis(neighborhood_analysis)
        print("Detailed Data Analysis:")
        print(detailed_data_analysis)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
