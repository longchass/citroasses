# api.py
from fastapi import APIRouter, Depends, HTTPException, Security, Query
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session
from sqlalchemy import func
import re
from database import get_db, Transaction, Category, TransactionType, Counterparty, CategoryEnum, TransactionTypeEnum
import uuid
from datetime import datetime, date, timedelta
from typing import List, Optional
import os
from transformers import pipeline
from typing import List
import logging


router = APIRouter()

API_KEY = os.getenv("API_KEY", "1234")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
categories_list = ["Retail", "Groceries", "Utilities"]

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header   
    raise HTTPException(status_code=403, detail="Could not validate credentials")

def get_category_enum_from_counterpart(counterpartName: str) -> CategoryEnum:
    try:
        name_lower = counterpartName.lower()
        if re.search(r"(.+\s(Tech|Software|IT))|(.+\.com$)", name_lower):
            category = "Retail"
        elif re.search(r"(.+\s(Retail|Store))", name_lower):
            category = "Retail"
        elif re.search(r"(specsavers|newsagency|stores|lotteries|pharmacy|chemmart|chemist|mcdonald|cafe)", name_lower):
            category = "Retail"
        elif re.search(r"(bws|liquorland|dan murphycoles|woolworths|aldi|costco|iga|target|big w|bp|chemmart)", name_lower):
            category = "Groceries"
        else:
            category = "Uncategorized"
        return CategoryEnum[category.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid category")

def classify_store(store_name: str) -> str:
    # Perform zero-shot classification
    result = classifier(
        store_name,
        candidate_labels=categories_list,
        hypothesis_template="This store is an Australian {} store."
    )
    print(result['labels'][0])
    # Return the highest scoring category
    return result['labels'][0]


def get_category_enum_from_counterpart_nlp(counterpartName: str) -> CategoryEnum:
    try:
        category = classify_store(counterpartName)
        print(category)
        return CategoryEnum[category.upper()]
    except KeyError:
        raise HTTPException(status_code=400, detail="NLP classification failed")


#When the transaction category is defined, we will create a new category object in the database if it does not already exist.
@router.post("/transaction/")
async def create_transaction(
    transaction: dict,
    db: Session = Depends(get_db),
):
    category_enum = get_category_enum_from_counterpart_nlp(transaction['counterpartName'])

    # print(get_category_enum_from_counterpart_nlp(category_enum))
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

    return {"message": f" type {category_enum} transaction created successfully", "id": new_transaction.id}


#Basic get query to debug ignore START
#Get transaction by counterpart

@app.on_event("startup")
async def startup_event():
    current_dir = os.getcwd()
    logger.info(f"Current working directory: {current_dir}")
    
    # List contents of the current directory
    dir_contents = os.listdir(current_dir)
    logger.info(f"Contents of the current directory: {dir_contents}")
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
    category_enum = get_category_enum_from_counterpart(category)
    transactions = db.query(Transaction).join(Category).filter(Category.name == category_enum).all()
    return transactions
#Basic get query to debug ignore END


# 1. All categories with respective transaction count and total amount spent within a specific date range
@router.get("/categories/summary")
async def get_categories_summary(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
):
    logger.info(start_date, end_date)
    #parse the date range string as utc+11 AEST time
    start_date = datetime.strptime(str(start_date), "%Y-%m-%d")
    end_date = datetime.strptime(str(end_date), "%Y-%m-%d")
    logger.info(start_date, end_date)
    start_date = start_date.replace(tzinfo=timezone.utc).astimezone(timezone('Australia/Melbourne'))
    end_date = end_date.replace(tzinfo=timezone.utc).astimezone(timezone('Australia/Melbourne'))    
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
    logger.info(start_date, end_date)
    #parse the date range string as utc+11 AEST time
    start_date = datetime.strptime(str(start_date), "%Y-%m-%d")
    end_date = datetime.strptime(str(end_date), "%Y-%m-%d")
    logger.info(start_date, end_date)
    start_date = start_date.replace(tzinfo=timezone.utc).astimezone(timezone('Australia/Melbourne'))
    end_date = end_date.replace(tzinfo=timezone.utc).astimezone(timezone('Australia/Melbourne'))   
    category_enum = CategoryEnum[category.upper()]
    logger.info(category_enum)
    logger.info(Transaction.category == category_enum)
    summary = db.query(
        Transaction.category,
        func.count(Transaction.id).label('transaction_count'),
        func.sum(Transaction.amount).label('total_amount')
    ).filter(
        Transaction.transaction_time_utc >= start_date,
        Transaction.transaction_time_utc < end_date + timedelta(days=1),
        Category.name == category_enum
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
    logger.info(start_date, end_date)
    #parse the date range string as utc+11 AEST time
    start_date = datetime.strptime(str(start_date), "%Y-%m-%d")
    end_date = datetime.strptime(str(end_date), "%Y-%m-%d")
    logger.info(start_date, end_date)
    start_date = start_date.replace(tzinfo=timezone.utc).astimezone(timezone('Australia/Melbourne'))
    end_date = end_date.replace(tzinfo=timezone.utc).astimezone(timezone('Australia/Melbourne'))   
    category_enum = CategoryEnum[category.upper()]
    logger.info(category_enum)
    logger.info(Transaction.category == category_enum)
    counterparts = db.query(Counterparty.name).distinct().join(Transaction).filter(
        Transaction.category == category_enum,
        Transaction.transaction_time_utc >= start_date,
        Transaction.transaction_time_utc < end_date + timedelta(days=1)
    ).all()
    
    return [c.name for c in counterparts]