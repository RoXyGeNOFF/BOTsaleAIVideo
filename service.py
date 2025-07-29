from data import get_user, add_user, update_user, add_payment, get_all_users, get_payments
from datetime import datetime, timedelta

def grant_videos(telegram_id, count):
    user = get_user(telegram_id)
    if user:
        user.videos_left += count
        update_user(user)

def decrement_free_generation(telegram_id):
    user = get_user(telegram_id)
    if user and user.free_generations > 0:
        user.free_generations -= 1
        update_user(user)

def set_premium(telegram_id, days=30):
    user = get_user(telegram_id)
    if user:
        user.is_premium = True
        user.expires_at = datetime.now() + timedelta(days=days)
        update_user(user)

def remove_premium(telegram_id):
    user = get_user(telegram_id)
    if user:
        user.is_premium = False
        user.expires_at = None
        update_user(user)

def get_expiring_premium_users(days=3):
    users = get_all_users()
    now = datetime.now()
    soon = now + timedelta(days=days)
    return [u.telegram_id for u in users if u.is_premium and u.expires_at and now < u.expires_at <= soon]

def get_stats():
    payments = get_payments()
    total = sum(p.amount for p in payments if p.status == 'success')
    count = sum(1 for p in payments if p.status == 'success')
    users = len(set(p.telegram_id for p in payments if p.status == 'success'))
    return {"total_income": total, "payments_count": count, "unique_users": users} 