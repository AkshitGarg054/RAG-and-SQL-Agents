import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

model = genai.GenerativeModel("models/gemini-2.5-pro")
try:
    response = model.generate_content("Hello")
    print(response.text)
    print("SUCCESS: gemini-2.5-pro works!")
except Exception as e:
    print("FAILED with error:", e)
