
import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

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
    if user:
        return {
            "telegram_id": user.telegram_id,
            "is_premium": user.is_premium,
            "expires_at": user.expires_at.isoformat() if user.expires_at else None,
            "free_generations": user.free_generations,
            "videos_left": user.videos_left
        }
    return None

def add_user(telegram_id):
    session = Session()
    if not session.query(User).filter_by(telegram_id=telegram_id).first():
        user = User(telegram_id=telegram_id, free_generations=3)
        session.add(user)
        session.commit()
    session.close()

def update_subscription(telegram_id, days=30):
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if user:
        user.is_premium = True
        user.expires_at = datetime.now() + timedelta(days=days)
        session.commit()
    session.close()

def remove_premium(telegram_id):
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if user:
        user.is_premium = False
        user.expires_at = None
        session.commit()
    session.close()

def decrement_free_generation(telegram_id):
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if user and user.free_generations > 0:
        user.free_generations -= 1
        session.commit()
    session.close()

def get_users_with_expiring_premium(days=3):
    session = Session()
    now = datetime.now()
    soon = now + timedelta(days=days)
    users = session.query(User).filter(User.is_premium == True, User.expires_at != None).all()
    result = []
    for user in users:
        if user.expires_at and now < user.expires_at <= soon:
            result.append(user.telegram_id)
    session.close()
    return result

def get_all_users():
    session = Session()
    users = session.query(User).all()
    result = [
        {"telegram_id": u.telegram_id, "is_premium": u.is_premium, "expires_at": u.expires_at.isoformat() if u.expires_at else None}
        for u in users
    ]
    session.close()
    return result

def add_videos(telegram_id, count):
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if user:
        user.videos_left += count
        session.commit()
    session.close()

def decrement_video(telegram_id):
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    if user and user.videos_left > 0:
        user.videos_left -= 1
        session.commit()
    session.close()

def add_payment(telegram_id, amount, method, status):
    session = Session()
    payment = Payment(telegram_id=telegram_id, amount=amount, method=method, status=status)
    session.add(payment)
    session.commit()
    session.close()

def get_payments():
    session = Session()
    payments = session.query(Payment).all()
    result = [
        {
            "id": p.id,
            "telegram_id": p.telegram_id,
            "amount": p.amount,
            "method": p.method,
            "status": p.status,
            "created_at": p.created_at.isoformat() if p.created_at else None
        }
        for p in payments
    ]
    session.close()
    return result

def get_payments_stats():
    session = Session()
    from sqlalchemy import func
    total = session.query(func.sum(Payment.amount)).filter(Payment.status == 'success').scalar() or 0
    count = session.query(func.count(Payment.id)).filter(Payment.status == 'success').scalar() or 0
    users = session.query(func.count(func.distinct(Payment.telegram_id))).filter(Payment.status == 'success').scalar() or 0
    session.close()
    return {"total_income": total, "payments_count": count, "unique_users": users}
