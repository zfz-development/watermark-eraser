from sqlalchemy.orm import Session
from app.models.point import PointLog, SignInLog
from app.models.user import User
from datetime import date, timedelta

def add_points(db, user_id, amount, ptype, detail, task_id=None):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return -1
    user.points += amount
    log = PointLog(user_id=user_id, amount=amount, type=ptype, detail=detail, task_id=task_id)
    db.add(log)
    db.commit()
    db.refresh(user)
    return user.points

def deduct_points(db, user_id, amount, detail, task_id=None):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False, 0
    if user.points < amount:
        return False, user.points
    user.points -= amount
    log = PointLog(user_id=user_id, amount=-amount, type="use", detail=detail, task_id=task_id)
    db.add(log)
    db.commit()
    db.refresh(user)
    return True, user.points

def get_consecutive_days(db, user_id):
    days = 0
    check_date = date.today()
    while True:
        log = db.query(SignInLog).filter(SignInLog.user_id == user_id, SignInLog.date == check_date).first()
        if log:
            days += 1
            check_date -= timedelta(days=1)
        else:
            break
    return days

def get_today_sign_in(db, user_id):
    return db.query(SignInLog).filter(SignInLog.user_id == user_id, SignInLog.date == date.today()).first() is not None

def get_points_logs(db, user_id, page=1, page_size=20):
    query = db.query(PointLog).filter(PointLog.user_id == user_id).order_by(PointLog.id.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "page": page, "page_size": page_size, "items": items}
