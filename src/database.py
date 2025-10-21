"""
Database models and mock data for the A2A Audit & Compliance system.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import random
from faker import Faker
import os

Base = declarative_base()
fake = Faker()

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(50), unique=True, index=True)
    supplier_name = Column(String(200), index=True)
    supplier_country = Column(String(100), index=True)
    amount = Column(Float, index=True)
    currency = Column(String(3), default="EUR")
    transaction_date = Column(DateTime, index=True)
    payment_method = Column(String(50))  # WIRE, CHECK, CASH
    risk_category = Column(String(20))  # LOW, MEDIUM, HIGH, PEP
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Supplier(Base):
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_name = Column(String(200), unique=True, index=True)
    country = Column(String(100), index=True)
    risk_category = Column(String(20), index=True)
    is_pep = Column(Boolean, default=False)  # Politically Exposed Person
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    audit_id = Column(String(50), index=True)
    query = Column(Text)
    transactions_analyzed = Column(Integer)
    violations_found = Column(Integer)
    compliance_status = Column(String(20))
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class DatabaseManager:
    """Manages database operations and mock data generation."""
    
    def __init__(self, database_url: str = None):
        if database_url is None:
            # Use SQLite for development (ignore DATABASE_URL env var)
            database_url = "sqlite:///./audit_compliance.db"
        
        self.engine = create_engine(database_url)
        Base.metadata.create_all(bind=self.engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.session = SessionLocal()
    
    def generate_mock_data(self, num_transactions: int = 1000):
        """Generate mock transaction and supplier data."""
        print(f"Generating {num_transactions} mock transactions...")
        
        # High-risk countries for AML compliance
        high_risk_countries = [
            "North Korea", "Iran", "Syria", "Sudan", "Cuba", 
            "Afghanistan", "Myanmar", "Russia", "Belarus", "Venezuela"
        ]
        
        # Regular countries
        regular_countries = [
            "USA", "Germany", "France", "UK", "Canada", "Australia", 
            "Japan", "Netherlands", "Sweden", "Norway", "Switzerland"
        ]
        
        # Generate suppliers first
        suppliers = []
        for i in range(50):
            country = random.choice(high_risk_countries + regular_countries)
            risk_category = "HIGH" if country in high_risk_countries else random.choice(["LOW", "MEDIUM"])
            
            supplier = Supplier(
                supplier_name=fake.company(),
                country=country,
                risk_category=risk_category,
                is_pep=random.choice([True, False]) if risk_category == "HIGH" else False
            )
            suppliers.append(supplier)
            self.session.add(supplier)
        
        self.session.commit()
        
        # Generate transactions
        payment_methods = ["WIRE", "CHECK", "CASH"]
        
        for i in range(num_transactions):
            supplier = random.choice(suppliers)
            
            # Generate realistic transaction amounts with some high-value ones
            if random.random() < 0.05:  # 5% chance of high-value transaction
                amount = random.uniform(100000, 1000000)
            elif random.random() < 0.15:  # 15% chance of medium-value transaction
                amount = random.uniform(10000, 100000)
            else:  # 80% chance of low-value transaction
                amount = random.uniform(100, 10000)
            
            transaction = Transaction(
                transaction_id=f"TXN-{datetime.now().strftime('%Y%m%d')}-{i:06d}",
                supplier_name=supplier.supplier_name,
                supplier_country=supplier.country,
                amount=round(amount, 2),
                currency="EUR",
                transaction_date=fake.date_time_between(start_date='-1y', end_date='now'),
                payment_method=random.choice(payment_methods),
                risk_category=supplier.risk_category,
                description=fake.text(max_nb_chars=100)
            )
            self.session.add(transaction)
        
        self.session.commit()
        print(f"✅ Generated {num_transactions} transactions and {len(suppliers)} suppliers")
    
    def get_transactions(self, 
                        supplier_name: str = None,
                        min_amount: float = None,
                        max_amount: float = None,
                        start_date: datetime = None,
                        end_date: datetime = None,
                        risk_category: str = None,
                        country: str = None,
                        limit: int = 100):
        """Retrieve transactions based on filters."""
        query = self.session.query(Transaction)
        
        if supplier_name:
            query = query.filter(Transaction.supplier_name.ilike(f"%{supplier_name}%"))
        if min_amount is not None:
            query = query.filter(Transaction.amount >= min_amount)
        if max_amount is not None:
            query = query.filter(Transaction.amount <= max_amount)
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)
        if risk_category:
            query = query.filter(Transaction.risk_category == risk_category)
        if country:
            query = query.filter(Transaction.supplier_country == country)
        
        return query.limit(limit).all()
    
    def get_suppliers(self, country: str = None, risk_category: str = None):
        """Retrieve suppliers based on filters."""
        query = self.session.query(Supplier)
        
        if country:
            query = query.filter(Supplier.country == country)
        if risk_category:
            query = query.filter(Supplier.risk_category == risk_category)
        
        return query.all()
    
    def add_audit_log(self, audit_id: str, query: str, transactions_analyzed: int, 
                     violations_found: int, compliance_status: str, summary: str):
        """Add an audit log entry."""
        audit_log = AuditLog(
            audit_id=audit_id,
            query=query,
            transactions_analyzed=transactions_analyzed,
            violations_found=violations_found,
            compliance_status=compliance_status,
            summary=summary
        )
        self.session.add(audit_log)
        self.session.commit()
        return audit_log
    
    def get_audit_logs(self, limit: int = 50):
        """Retrieve recent audit logs."""
        return self.session.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    def close(self):
        """Close the database session."""
        self.session.close()

# Global database manager instance
db_manager = None

def get_db_manager():
    """Get the global database manager instance."""
    global db_manager
    if db_manager is None:
        # Force SQLite for development
        database_url = "sqlite:///./audit_compliance.db"
        db_manager = DatabaseManager(database_url)
    return db_manager

def init_database():
    """Initialize the database with mock data."""
    db = get_db_manager()
    # Check if we already have data
    existing_transactions = db.session.query(Transaction).count()
    if existing_transactions == 0:
        db.generate_mock_data(1000)
    else:
        print(f"Database already contains {existing_transactions} transactions")
    return db
