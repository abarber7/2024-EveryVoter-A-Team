from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI

# Load environment variables from the .env file
load_dotenv()

# Ensure the API key is loaded
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("API key not found. Ensure OPENAI_API_KEY is set in your environment.")

# Initialize the model with the API key
model = ChatOpenAI(model="gpt-4", api_key=api_key)

# Generate the result from the model
result = model("generate six random and interesting candidates for a poll and print each candidate on a new line")

# Print the result
print(result.content)
