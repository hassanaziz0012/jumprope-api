from sqlalchemy.orm import Session
from models.user_profile import UserProfile

def sync_user_profile(db: Session, user_data):
    user = db.query(UserProfile).filter(UserProfile.sync_token == user_data.sync_token).first()
    if user:
        for key, value in user_data.model_dump(exclude={'id'}).items():
            setattr(user, key, value)
    else:
        user = UserProfile(**user_data.model_dump(exclude={'id'}))
        db.add(user)
    db.commit()
    db.refresh(user)
    return user
