# api.py
from fastapi import APIRouter, Depends, HTTPException, Security, Query
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db, Transaction, Category, TransactionType, Counterparty, CategoryEnum, TransactionTypeEnum
import uuid
from datetime import datetime, date, timedelta
from typing import List, Optional
import os

router = APIRouter()

API_KEY = os.getenv("API_KEY", "1234")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header   
    raise HTTPException(status_code=403, detail="Could not validate credentials")

def get_category_enum(category: str) -> CategoryEnum:
    try:
        return CategoryEnum[category.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid category")

#When the transaction category is defined, we will create a new category object in the database if it does not already exist.
@router.post("/transaction/{category}")
async def create_transaction(
    category: str,
    transaction: dict,
    db: Session = Depends(get_db),
):
    category_enum = get_category_enum(category)

    print("CHECK CATEGORY VALUES")
    print(get_category_enum("UNVALIDATED"))
    print(db.query(Category).filter(Category.name == category_enum).first())
    
    db_category = db.query(Category).filter(Category.name == category_enum).first()
    if not db_category:
        db_category = Category(name=category_enum)
        db.add(db_category)
        db.commit()

    db_transaction_type = db.query(TransactionType).filter(TransactionType.name == TransactionTypeEnum(transaction['transactionType'])).first()
    if not db_transaction_type:
        db_transaction_type = TransactionType(name=TransactionTypeEnum(transaction['transactionType']))
        db.add(db_transaction_type)
        db.commit()

    db_counterparty = db.query(Counterparty).filter(Counterparty.name == transaction['counterpartName']).first()
    if not db_counterparty:
        db_counterparty = Counterparty(name=transaction['counterpartName'])
        db.add(db_counterparty)
        db.commit()

    new_transaction = Transaction(
        transaction_id=uuid.UUID(transaction['transactionId']),
        amount=transaction['amount'],
        transaction_time_utc=datetime.fromisoformat(transaction['transactionTimeUtc'].replace('Z', '+00:00')),
        category_id=db_category.id,
        transaction_type_id=db_transaction_type.id,
        counterparty_id=db_counterparty.id
    )

    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    return {"message": f"{category.capitalize()} transaction created successfully", "id": new_transaction.id}


#Basic get query to debug ignore START
#Get transaction by counterpart
@router.get("/transactions/counterpartName/{counterparty_name}")
async def get_transactions_by_counterparty(
    counterparty_name: str,
    db: Session = Depends(get_db),
):
    transactions = db.query(Transaction).join(Counterparty).filter(Counterparty.name == counterparty_name).all()
    return transactions

#Get transaction by category
@router.get("/transactions/category/{category}")
async def get_transactions_by_category(
    category: str,
    db: Session = Depends(get_db),
):
    category_enum = get_category_enum(category)
    transactions = db.query(Transaction).join(Category).filter(category.name == category_enum).all()
    return transactions
#Basic get query to debug ignore END


# 1. All categories with respective transaction count and total amount spent within a specific date range
@router.get("/categories/summary")
async def get_categories_summary(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
):
    summary = db.query(
        Transaction.category,
        func.count(Transaction.id).label('transaction_count'),
        func.sum(Transaction.amount).label('total_amount')
    ).filter(
        Transaction.transaction_time_utc >= start_date,
        Transaction.transaction_time_utc < end_date + timedelta(days=1)
    ).group_by(Transaction.category).all()

    return [
        {
            "category": s.category.value,
            "transaction_count": s.transaction_count,
            "total_amount": float(s.total_amount)
        } for s in summary
    ]

# 2. Transactions per category within a specific date range
#Get transaction by category and date range
@router.get("/transactions/summary/{category}")
async def get_transactions_summary(
    category: str,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
):
    category_enum = get_category_enum(category)
    summary = db.query(
        Transaction.category,
        func.count(Transaction.id).label('transaction_count'),
        func.sum(Transaction.amount).label('total_amount')
    ).filter(
        Transaction.transaction_time_utc >= start_date,
        Transaction.transaction_time_utc < end_date + timedelta(days=1),
        category.name == category_enum
    ).group_by(Transaction.category).all()
    
    return [
        {
            "category": s.category.value,
            "transaction_count": s.transaction_count,
            "total_amount": float(s.total_amount)
        } for s in summary
    ]





# 3. Unique counterpart names per category within a specific date range
@router.get("/counterparts/category/{category}")
async def get_unique_counterparts_by_category(
    category: str,
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
):
    category_enum = get_category_enum(category)
    counterparts = db.query(Counterparty.name).distinct().join(Transaction).filter(
        Transaction.category == category_enum,
        Transaction.transaction_time_utc >= start_date,
        Transaction.transaction_time_utc < end_date + timedelta(days=1)
    ).all()
    
    return [c.name for c in counterparts]