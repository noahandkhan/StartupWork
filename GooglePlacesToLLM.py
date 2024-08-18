import requests
import openai
import json

# Configure your API keys
google_api_key = 'AIzaSyDUVWuxTmQ-Uou2LjvHky38cq0H6F-n-T4'
openai_api_key = 'your-openai-api-key'

# Set up OpenAI API key
openai.api_key = openai_api_key

def get_places_data(location='27.9506,-82.4576', radius='1500', keyword='Spicy Vegetarian Food'):
    url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
    params = {
        'location': location,
        'radius': radius,
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
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # Use the appropriate model
        messages=[
            {"role": "system", "content": "You are an assistant."},
            {"role": "user", "content": f"Analyze the following places data and provide insights:\n\n{json.dumps(data, indent=2)}"}
        ],
        max_tokens=150
    )
    return response.choices[0].message['content'].strip()

def main():
    # Get data from Google Places API
    places_data = get_places_data()
    
    # Format data for LLM
    formatted_data = format_places_data(places_data)
    
    # Query LLM
    llm_response = query_llm(formatted_data)
    
    # Print the LLM response
    print("LLM Response:")
    print(llm_response)

if __name__ == '__main__':
    main()
