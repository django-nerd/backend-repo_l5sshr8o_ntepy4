"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models for the food ordering app.
Each Pydantic model represents a collection in MongoDB; the collection name is the
lowercase class name (e.g., MenuItem -> "menuitem").
"""

from pydantic import BaseModel, Field
from typing import Optional, List

class MenuItem(BaseModel):
    """Menu items available to order (collection: "menuitem")"""
    name: str = Field(..., description="Dish name")
    description: Optional[str] = Field(None, description="Short description of the dish")
    price: float = Field(..., ge=0, description="Price in dollars")
    image: Optional[str] = Field(None, description="Image URL")
    category: str = Field(..., description="Category like Pizza, Burger, Drinks, Desserts")
    spicy: Optional[bool] = Field(False, description="Is this dish spicy")
    vegetarian: Optional[bool] = Field(False, description="Is this dish vegetarian")

class OrderItem(BaseModel):
    item_id: str = Field(..., description="ID of the menu item")
    name: str = Field(..., description="Menu item name at time of order")
    price: float = Field(..., ge=0, description="Unit price at time of order")
    quantity: int = Field(..., ge=1, description="Quantity ordered")

class Order(BaseModel):
    """Customer orders (collection: "order")"""
    customer_name: str = Field(..., description="Customer full name")
    phone: str = Field(..., description="Contact number")
    address: str = Field(..., description="Delivery address")
    items: List[OrderItem] = Field(..., description="Items in the order")
    subtotal: float = Field(..., ge=0, description="Subtotal of items")
    delivery_fee: float = Field(0.0, ge=0, description="Delivery fee applied")
    total: float = Field(..., ge=0, description="Total amount to charge")
    status: str = Field("pending", description="Order status: pending, confirmed, preparing, out_for_delivery, delivered, cancelled")
