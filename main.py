
from fastapi import HTTPException
from google.genai import errors
from database import get_inventory_summary
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from database import get_low_stock_products, get_inventory_summary

from database import get_products, add_product
from fastapi import FastAPI
from pydantic import BaseModel
app = FastAPI()



@app.get("/")
def home():
    return {"message": "AI Retail Automation Agent is running"}
@app.get("/products")
def list_products():
    products = get_products()

    return {
        "products": [
            {
                "id": product[0],
                "name": product[1],
                "price": product[2],
                "stock": product[3]
            }
            for product in products
        ]
    }
from pydantic import Field

class Product(BaseModel):
    name: str = Field(min_length=1)
    price: float = Field(gt=0)
    stock: int = Field(ge=0)

@app.post("/products")
def create_product(product: Product):
    add_product(product.name, product.price, product.stock)

    return {
        "message": "Product saved successfully",
        "product": product
    }

# Load Gemini API configuration
load_dotenv(override=True)

gemini_client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)



@app.post("/ai/chat")
def ai_chat(request: ChatRequest):
    try:
        chat = gemini_client.chats.create(
            model="gemini-3.8-flash",
            config=types.GenerateContentConfig(
                tools=[
                    get_low_stock_products,
                    get_inventory_summary
                ]
            )
        )

        response = chat.send_message(request.message)

        return {"response": response.text}

    except errors.ServerError as e:
        if e.code == 503:
            raise HTTPException(
                status_code=503,
                detail="Gemini is temporarily busy. Please try again later."
            )

        raise HTTPException(
            status_code=502,
            detail="Gemini service error."
        )


@app.get("/inventory/summary")
def inventory_summary():
    return get_inventory_summary()
