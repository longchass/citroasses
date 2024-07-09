# database.py
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import uuid
import enum

# Database connection setup can be specified through docker environment variables
DB_USER = os.getenv("POSTGRES_USER", "admin")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "admin")
DB_NAME = os.getenv("POSTGRES_DB", "mydb")
DB_HOST = os.getenv("DB_HOST", "localhost")

SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

#We want to refactor the Base class to follow BCNF principles. We will create 3 new tables: sectors, transaction_types, and counterparties.

class CategoryEnum(enum.Enum):
    RETAIL = "Retail"
    GROCERIES = "Groceries"
    UTILITIES = "Utilities"

#made up some enum values for TransactionTypeEnum
class TransactionTypeEnum(enum.Enum):
    CARD_TRANSACTION = "CARD_TRANSACTION"
    BANK_TRANSFER = "BANK_TRANSFER"
    CASH_WITHDRAWAL = "CASH_WITHDRAWAL"

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Enum(CategoryEnum), unique=True, nullable=False)

class TransactionType(Base):
    __tablename__ = "transaction_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Enum(TransactionTypeEnum), unique=True, nullable=False)

class Counterparty(Base):
    __tablename__ = "counterparties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    amount = Column(Float, nullable=False)
    transaction_time_utc = Column(DateTime(timezone=True), nullable=False)
    
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    transaction_type_id = Column(Integer, ForeignKey('transaction_types.id'), nullable=False)
    counterparty_id = Column(Integer, ForeignKey('counterparties.id'), nullable=False)

    category = relationship("Category")
    transaction_type = relationship("TransactionType")
    counterparty = relationship("Counterparty")

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()