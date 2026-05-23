import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def list_models():
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    print("--- Available Models ---")
    try:
        for model in client.models.list():
            print(f"Name: {model.name}, Display Name: {model.display_name}, Supported Actions: {model.supported_actions}")
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    list_models()
