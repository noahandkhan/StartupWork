import time
import openai

def query_llm_with_retry(data, retries=3, delay=60):
    for _ in range(retries):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an assistant."},
                    {"role": "user", "content": f"Analyze the following places data and provide insights:\n\n{json.dumps(data, indent=2)}"}
                ],
                max_tokens=150
            )
            return response.choices[0].message["content"].strip()
        except openai.error.RateLimitError as e:  # Catching rate limit errors specifically
            print(f"Rate limit exceeded, retrying in {delay} seconds...")
            time.sleep(delay)
        except openai.error.InvalidRequestError as e:  # Catching invalid request errors
            print(f"Invalid request: {e}")
            break
        except openai.error.AuthenticationError as e:  # Catching authentication errors
            print(f"Authentication error: {e}")
            break
        except Exception as e:  # Catching any other errors
            print(f"An unexpected error occurred: {e}")
            break
    raise Exception("Failed after multiple retries due to rate limits.")

def main():
    # Example data to be passed to the LLM
    data = {
        "name": "Example Place",
        "address": "123 Main St",
        "rating": 4.5,
        "types": ["restaurant", "food"]
    }

    try:
        llm_response = query_llm_with_retry(data)
        print("LLM Response:")
        print(llm_response)
    except Exception as e:
        print(f"Failed to get a response: {e}")

if __name__ == '__main__':
    main()
