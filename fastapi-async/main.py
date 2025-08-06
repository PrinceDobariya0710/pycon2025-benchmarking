from contextlib import asynccontextmanager
import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, Body, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, UJSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, mapped_column
from sqlalchemy import Integer, String, Text, Numeric, select, update, delete
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# === ENVIRONMENT VARIABLES ===
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "postgres")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# === SQLALCHEMY SETUP ===
engine = create_async_engine(DATABASE_URL, echo=False, future=True)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

templates = Jinja2Templates(directory="templates")


# === SQLALCHEMY MODEL ===
class Product(Base):
    __tablename__ = "product"
    id = mapped_column(Integer, primary_key=True, index=True)
    name = mapped_column(String)
    description = mapped_column(Text)
    brand = mapped_column(String)
    category = mapped_column(String)
    price = mapped_column(Numeric)
    currency = mapped_column(String)
    stock = mapped_column(Integer)
    ean = mapped_column(String)
    color = mapped_column(String)
    size = mapped_column(String)
    availability = mapped_column(String)
    internal_id = mapped_column(String)


# === PYDANTIC MODELS ===
class ProductBase(BaseModel):
    name: str
    description: str
    brand: str
    category: str
    price: float
    currency: str
    stock: int
    ean: str
    color: str
    size: str
    availability: str
    internal_id: str


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    stock: Optional[int] = None
    ean: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    availability: Optional[str] = None
    internal_id: Optional[str] = None


class ProductOut(ProductBase):
    id: int

    class Config:
        from_attributes = True


# === FASTAPI APP ===
app = FastAPI()


# Dependency to get DB session
async def get_session():
    async with async_session() as session:
        yield session


# === ENDPOINTS ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Clean up the ML models and release the resources
    print("Cleaning up resources...")


@app.get("/plain-text")
async def plain_text():
    return PlainTextResponse(b"Hello, world!")


@app.get("/json")
async def json_serialization():
    return UJSONResponse({"message": "Hello, world from JSON serialization endpoint!"})


@app.post("/products", response_model=ProductOut)
async def create_product(
    product: ProductCreate, session: AsyncSession = Depends(get_session)
):
    db_product = Product(**product.model_dump())
    session.add(db_product)
    await session.commit()
    await session.refresh(db_product)
    return db_product


@app.get("/products/{id}", response_model=ProductOut)
async def get_product(id: int, session: AsyncSession = Depends(get_session)):
    result = await session.get(Product, id)
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")
    return result


@app.get("/products", response_model=List[ProductOut])
async def list_products(
    limit: int = 100, offset: int = 0, session: AsyncSession = Depends(get_session)
):
    stmt = select(Product).limit(limit).offset(offset)
    result = await session.execute(stmt)
    return result.scalars().all()


@app.put("/products/{id}", response_model=ProductOut)
async def update_product(
    id: int, product: ProductUpdate, session: AsyncSession = Depends(get_session)
):
    db_product = await session.get(Product, id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in product.model_dump(exclude_unset=True).items():
        setattr(db_product, field, value)
    await session.commit()
    await session.refresh(db_product)
    return db_product


@app.delete("/products/{id}")
async def delete_product(id: int, session: AsyncSession = Depends(get_session)):
    db_product = await session.get(Product, id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    await session.delete(db_product)
    await session.commit()
    return {"ok": True}


@app.get("/fortune", response_class=HTMLResponse)
async def fortune_100(request: Request, session: AsyncSession = Depends(get_session)):
    stmt = select(Product).limit(100)
    result = await session.execute(stmt)
    products = result.scalars().all()
    return templates.TemplateResponse(
        "fortune.html", {"request": request, "products": products}
    )
