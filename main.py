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