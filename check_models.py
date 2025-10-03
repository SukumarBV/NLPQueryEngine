import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load the .env file from the backend folder
dotenv_path = os.path.join(os.path.dirname(__file__), 'backend', '.env')
load_dotenv(dotenv_path=dotenv_path)

try:
    # Configure the API with your key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in backend/.env file.")
    else:
        genai.configure(api_key=api_key)

        print("Finding models that support 'generateContent'...\n")
        
        found_model = False
        # List all available models
        for m in genai.list_models():
            # Check if the 'generateContent' method is supported
            if 'generateContent' in m.supported_generation_methods:
                print(f"✔️ Found compatible model: {m.name}")
                found_model = True
        
        if not found_model:
            print("❌ No compatible models found. Please check your API key and project settings in Google AI Studio.")

except Exception as e:
    print(f"An error occurred: {e}")