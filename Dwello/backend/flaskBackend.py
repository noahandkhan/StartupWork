from flask import Flask, request, jsonify
from openai import OpenAI
import json

app = Flask(__name__)

client = OpenAI(api_key='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')

def query_llm(prompt):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an assistant that provides insights about real estate location, appreciation, turnover, proximity to things, and all things related to finding the right property."},
            {"role": "user", "content": f"Analyze the following requirements and find the best cities, then further best neighborhoods within those cities, and provide the reasons why they align. I want the top 3 options and main reasons each were recommended. I also want a detailed analysis of how each correlates to all of my preferences. Based on my input, also tell me the optimal house features I can afford or would be average in that area. Consider all of the following and outline it as it pertains to each neighborhood:\n\n{json.dumps(prompt, indent=2)}"}
        ],
        max_tokens=4096
    )
    return response.choices[0].message.content.strip()

def query_llm_for_data_analysis(neighborhood_analysis):
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

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    user_input = data.get('input')

    neighborhood_analysis = query_llm(user_input)
    detailed_data_analysis = query_llm_for_data_analysis(neighborhood_analysis)

    return jsonify({
        'neighborhoodAnalysis': neighborhood_analysis,
        'detailedAnalysis': detailed_data_analysis
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
