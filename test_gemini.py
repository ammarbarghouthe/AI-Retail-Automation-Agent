
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from database import get_low_stock_products

load_dotenv(override=True)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is missing")

client = genai.Client(api_key=api_key)


chat = client.chats.create(
    model="gemini-3.8-flash",
    config=types.GenerateContentConfig(
        tools=[get_low_stock_products]
    )
)

response = chat.send_message(
    "Which products have fewer than 40 units in stock?"
)

print("Gemini response:")
print(response.text)


print(response.text)
