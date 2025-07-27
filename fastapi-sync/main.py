import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy import (
    create_engine,
    Integer,
    String,
    Text,
    Numeric,
    select,
    update,
    delete,
)
from sqlalchemy.orm import sessionmaker, declarative_base, mapped_column, Session
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# === ENVIRONMENT VARIABLES ===
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "postgres")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# === SQLALCHEMY SETUP ===
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
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

# Create tables on startup
Base.metadata.create_all(bind=engine)


# Dependency to get DB session
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# === ENDPOINTS ===
@app.get("/plain-text")
def plain_text():
    return PlainTextResponse(b"Hello, world!")


@app.get("/json")
def json_serialization():
    return JSONResponse({"message": "Hello, world from JSON serialization endpoint!"})


@app.post("/products", response_model=ProductOut)
def create_product(product: ProductCreate, session: Session = Depends(get_session)):
    db_product = Product(**product.model_dump())
    session.add(db_product)
    session.commit()
    session.refresh(db_product)
    return db_product


@app.get("/products/{id}", response_model=ProductOut)
def get_product(id: int, session: Session = Depends(get_session)):
    result = session.get(Product, id)
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")
    return result


@app.get("/products", response_model=List[ProductOut])
def list_products(
    limit: int = 100, offset: int = 0, session: Session = Depends(get_session)
):
    stmt = select(Product).limit(limit).offset(offset)
    result = session.execute(stmt)
    return result.scalars().all()


@app.put("/products/{id}", response_model=ProductOut)
def update_product(
    id: int, product: ProductUpdate, session: Session = Depends(get_session)
):
    db_product = session.get(Product, id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in product.model_dump(exclude_unset=True).items():
        setattr(db_product, field, value)
    session.commit()
    session.refresh(db_product)
    return db_product


@app.delete("/products/{id}")
def delete_product(id: int, session: Session = Depends(get_session)):
    db_product = session.get(Product, id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    session.delete(db_product)
    session.commit()
    return {"ok": True}


@app.get("/fortune", response_class=HTMLResponse)
def fortune_100(request: Request, session: Session = Depends(get_session)):
    stmt = select(Product).limit(100)
    result = session.execute(stmt)
    products = result.scalars().all()
    return templates.TemplateResponse(
        "fortune.html", {"request": request, "products": products}
    )
