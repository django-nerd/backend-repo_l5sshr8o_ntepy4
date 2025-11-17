import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents

app = FastAPI(title="SnackSprint API", version="1.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Demo fallback (when DB is not available)
# -----------------------------
DEMO_RESTAURANT = {
    "id": "demo-1",
    "name": "SnackSprint Diner",
    "description": "Burgers, bowls and bites delivered fast",
    "image": "https://images.unsplash.com/photo-1550547660-d9450f859349?w=1200",
    "cuisine": "American",
    "rating": 4.7,
}

DEMO_MENU = [
    {
        "id": "m1",
        "restaurant_id": DEMO_RESTAURANT["id"],
        "name": "Classic Burger",
        "description": "Juicy beef patty, cheddar, pickles",
        "price": 9.99,
        "image": "https://images.unsplash.com/photo-1550547660-2f9b63f1f7b0?w=1200",
        "is_veg": False,
        "spice_level": "Mild",
    },
    {
        "id": "m2",
        "restaurant_id": DEMO_RESTAURANT["id"],
        "name": "Veggie Bowl",
        "description": "Roasted veggies, quinoa, tahini",
        "price": 8.49,
        "image": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=1200",
        "is_veg": True,
        "spice_level": "Medium",
    },
    {
        "id": "m3",
        "restaurant_id": DEMO_RESTAURANT["id"],
        "name": "Spicy Chicken Wrap",
        "description": "Crispy chicken, chipotle mayo",
        "price": 10.49,
        "image": "https://images.unsplash.com/photo-1604908177076-9f2bf5f7955f?w=1200",
        "is_veg": False,
        "spice_level": "Hot",
    },
]


@app.get("/")
def read_root():
    return {"message": "SnackSprint backend is running"}


# Seed data endpoint (idempotent for demo)
@app.post("/seed")
def seed_demo_data():
    if db is None:
        # No-op when DB is not configured
        return {"ok": True, "mode": "demo"}
    try:
        restaurants = db["restaurant"].count_documents({}) if db else 0
        if restaurants == 0:
            rid = create_document(
                "restaurant",
                {
                    "name": DEMO_RESTAURANT["name"],
                    "description": DEMO_RESTAURANT["description"],
                    "image": DEMO_RESTAURANT["image"],
                    "cuisine": DEMO_RESTAURANT["cuisine"],
                    "rating": DEMO_RESTAURANT["rating"],
                },
            )
            rest_id = rid
            for itm in DEMO_MENU:
                doc = itm.copy()
                doc.pop("id", None)
                doc["restaurant_id"] = rest_id
                create_document("menuitem", doc)
        return {"ok": True, "mode": "db"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/restaurants")
def list_restaurants():
    # Fallback to demo if DB missing
    if db is None:
        return [DEMO_RESTAURANT]
    try:
        data = get_documents("restaurant")
        for d in data:
            d["id"] = str(d.pop("_id"))
        return data
    except Exception as e:
        # Fallback to demo on error
        return [DEMO_RESTAURANT]


@app.get("/menu/{restaurant_id}")
def list_menu(restaurant_id: str):
    # Fallback to demo if DB missing
    if db is None:
        return [m for m in DEMO_MENU if m["restaurant_id"] == restaurant_id]
    try:
        items = get_documents("menuitem", {"restaurant_id": restaurant_id})
        for i in items:
            i["id"] = str(i.pop("_id"))
        return items
    except Exception:
        # Fallback to demo on error
        return [m for m in DEMO_MENU if m["restaurant_id"] == restaurant_id]


class OrderItemPayload(BaseModel):
    item_id: str
    name: str
    price: float
    quantity: int


class OrderPayload(BaseModel):
    restaurant_id: str
    customer_name: str
    phone: str
    address: str
    notes: Optional[str] = None
    items: List[OrderItemPayload]


@app.post("/orders")
def create_order(payload: OrderPayload):
    try:
        total = sum(max(1, i.quantity) * float(i.price) for i in payload.items)
        order_doc = {
            "restaurant_id": payload.restaurant_id,
            "customer_name": payload.customer_name,
            "phone": payload.phone,
            "address": payload.address,
            "notes": payload.notes,
            "items": [i.model_dump() for i in payload.items],
            "total": round(total, 2),
            "status": "pending",
        }
        if db is None:
            # Demo mode: pretend success without persistence
            return {"ok": True, "order_id": "demo-order-1"}
        order_id = create_document("order", order_doc)
        return {"ok": True, "order_id": order_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, "name") else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception:
                response["database"] = "⚠️  Connected but Error"
        else:
            response["database"] = "ℹ️ Using demo mode (no database)"
    except Exception:
        response["database"] = "❌ Error"
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
