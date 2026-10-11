
from fastapi import FastAPI
from pydantic import BaseModel
app = FastAPI()


@app.get("/")
def home():
    return {"message": "AI Retail Automation Agent is running"}
@app.get("/products")
def get_products():
    return {
        "products": [
            {"id": 1, "name": "Milk", "price": 1.5},
            {"id": 2, "name": "Bread", "price": 0.5},
            {"id": 3, "name": "Rice", "price": 2.0}
        ]
    }
class Product(BaseModel):
    name: str
    price: float


@app.post("/products")
def add_product(product: Product):
    return {
        "message": "Product received successfully",
        "product": product
    }