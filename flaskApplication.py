from flask import Flask, render_template, request, jsonify
import requests
import json
from openai import OpenAI

app = Flask(__name__)

# Set up OpenAI client
client = OpenAI(api_key='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')

# Configure your API keys
google_api_key = 'AIzaSyDUVWuxTmQ-Uou2LjvHky38cq0H6F-n-T4'

# Fixed location and radius
fixed_location = '27.9506,-82.4576'  # Example: Tampa, Florida
fixed_radius = '1500'  # 1500 meters

def get_places_data(keyword):
    url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
    params = {
        'location': fixed_location,
        'radius': fixed_radius,
        'keyword': keyword,
        'key': google_api_key
    }
    response = requests.get(url, params=params)
    return response.json()

def format_places_data(data):
    results = data.get('results', [])
    formatted_results = []
    for place in results:
        formatted_results.append({
            'name': place.get('name'),
            'address': place.get('vicinity'),
            'rating': place.get('rating'),
            'types': place.get('types'),
        })
    return formatted_results

def query_llm(data):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an assistant."},
            {"role": "user", "content": f"Analyze the following places data and provide insights:\n\n{json.dumps(data, indent=2)}"}
        ],
        max_tokens=150
    )
    return response.choices[0].message.content.strip()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/query', methods=['POST'])
def query():
    # Get the keyword from the form submission
    keyword = request.form['keyword']

    # Get data from Google Places API
    places_data = get_places_data(keyword)

    # Format data for LLM
    formatted_data = format_places_data(places_data)

    # Query LLM
    llm_response = query_llm(formatted_data)

    # Return response to the frontend
    return jsonify({
        'places': formatted_data,
        'llm_response': llm_response
    })

if __name__ == '__main__':
    app.run(debug=True)
