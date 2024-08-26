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
    
    response = client.chat.completions.create(model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are an assistant that provides insights about real estate location, appreciation, turnover, proximity, and all things related to finding the right property."},
        {"role": "user", "content": f"Analyze the following requirements and find the best cities, then further best neighborhoods within those cities, and provide the reasons why they allign:\n\n{json.dumps(prompt, indent=2)}"}
    ],
    max_tokens=150)
    return response.choices[0].message.content.strip()

def main():
    """
    Main function to handle the process of gathering user input,
    processing it with OpenAI, and outputting the result.
    """
    try:
        # Step 1: Get user input
        user_input = get_user_input()

        # Step 2: Send input to OpenAI API and get the response
        generated_response = query_llm(user_input)
        print("OpenAI API response:")
        print(generated_response)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
