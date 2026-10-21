from database import (
    get_top_selling_products,
    get_revenue_by_period,
    get_monthly_sales_trends,
    get_top_customers,
    get_sales_by_country,
    get_order_statistics,
    get_slow_moving_products,
    compare_product_sales,
)
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from database import search_product_sales
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
app.mount(
    "/frontend",
    StaticFiles(directory="frontend"),
    name="frontend"
)


@app.get("/dashboard")
def dashboard():
    return FileResponse("frontend/index.html")


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
  system_instruction="""
    You are an AI Retail Operations Assistant.

    STRICT RULES:

    1. Answer ONLY questions related to retail operations,
       sales, inventory, products, customers, revenue,
       business performance, and retail analytics.

    2. If a user asks about anything outside these topics,
       politely refuse and redirect them to retail questions.

    3. For unrelated questions, respond:
       "I am an AI Retail Assistant. I can only help
       with sales, products, inventory, customers,
       and retail business analysis."

    4. Use the available database tools when answering
       questions about actual business data.

    5. Never invent sales figures, customer records,
       inventory levels, or financial results.

    6. If the requested business information is unavailable,
       clearly explain that it is not available.

    7. Understand different ways of asking the same
       retail question, including different languages.
    """,
   
tools=[
    get_low_stock_products,
    get_inventory_summary,
    search_product_sales,
    get_top_selling_products,
    get_revenue_by_period,
    get_monthly_sales_trends,
    get_top_customers,
    get_sales_by_country,
    get_order_statistics,
    get_slow_moving_products,
    compare_product_sales,
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
@app.get("/analytics/summary")
def analytics_summary():
    return get_order_statistics()


@app.get("/analytics/top-products")
def analytics_top_products(limit: int = 10):
    return get_top_selling_products(limit=limit)