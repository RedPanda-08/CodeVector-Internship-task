from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional
import base64
import os

from fastapi.responses import HTMLResponse
from database import db
from datetime import datetime

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    yield
    await db.disconnect()

app = FastAPI(
    title="CodeVector High-Performance Product API", 
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def decode_cursor(cursor_str: str):
    """Decodes base64 string back into (created_at_datetime, last_seen_id)"""
    try:
        decoded = base64.b64decode(cursor_str.encode()).decode()
        created_at_str, id_str = decoded.split("|")
        created_at_dt = datetime.fromisoformat(created_at_str)
        return created_at_dt, int(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid cursor token supplied.")

def encode_cursor(created_at_dt, record_id: int) -> str:
    """Encodes the last item's values into a web-safe base64 string"""
    raw_str = f"{created_at_dt.isoformat()}|{record_id}"
    return base64.b64encode(raw_str.encode()).decode()

@app.get("/products")
async def get_products(
    category: str = Query(..., description="Filter products by exact category "),
    limit: int = Query(20, ge=1, le=100, description="Quantity of products per window frame"),
    cursor: Optional[str] = Query(None, description="The opaque pagination cursor token")
):

    query = """
        SELECT unique_id, name, category, price, created_at 
        FROM products 
        WHERE category = $1
    """
    params = [category]

    if cursor:
        created_at_limit, id_limit = decode_cursor(cursor)
        
        query += """
            AND (
                created_at < $2 
                OR (created_at = $2 AND unique_id < $3)
            )
        """
        params.extend([created_at_limit, id_limit])

    query += " ORDER BY created_at DESC, unique_id DESC LIMIT $4" if cursor else " ORDER BY created_at DESC, unique_id DESC LIMIT $2"
    params.append(limit)

    async with db.pool.acquire() as connection:
        rows = await connection.fetch(query, *params)
    
    products = [
        {
            "id": row["unique_id"],
            "name": row["name"],
            "category": row["category"],
            "price": float(row["price"]),
            "created_at": row["created_at"]
        }
        for row in rows
    ]

    next_cursor = None
    if len(products) == limit:
        last_item = rows[-1]
        next_cursor = encode_cursor(last_item["created_at"], last_item["unique_id"])

    return {
        "results": products,
        "count": len(products),
        "next_cursor": next_cursor
    }
@app.get("/", response_class=HTMLResponse)
async def read_index():
    html_content = os.path.join(os.path.dirname(__file__), "template", "index.html")

    with open(html_content, "r", encoding="utf-8") as f:
        return f.read()