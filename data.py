import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DB_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg2://veo3user:veo3pass@db:5432/veo3")
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    telegram_id = Column(Integer, primary_key=True)
    is_premium = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=True)
    free_generations = Column(Integer, default=3)
    videos_left = Column(Integer, default=0)

class Payment(Base):
    __tablename__ = 'payments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer)
    amount = Column(Float)
    method = Column(String)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.now)

def init_db():
    Base.metadata.create_all(engine)

def get_user(telegram_id):
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    session.close()
    return user

def add_user(telegram_id):
    session = Session()
    if not session.query(User).filter_by(telegram_id=telegram_id).first():
        user = User(telegram_id=telegram_id, free_generations=3)
        session.add(user)
        session.commit()
    session.close()

def update_user(user):
    session = Session()
    session.merge(user)
    session.commit()
    session.close()

def get_all_users():
    session = Session()
    users = session.query(User).all()
    session.close()
    return users

def add_payment(telegram_id, amount, method, status):
    session = Session()
    payment = Payment(telegram_id=telegram_id, amount=amount, method=method, status=status)
    session.add(payment)
    session.commit()
    session.close()

def get_payments():
    session = Session()
    payments = session.query(Payment).all()
    session.close()
    return payments 