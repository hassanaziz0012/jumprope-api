import hashlib
from sqlalchemy.orm import Session
from models.user_profile import UserProfile
from axiom_py.logging import AxiomHandler
import axiom_py
import logging

def setup_logger():
    client = axiom_py.Client()
    handler = AxiomHandler(client, dataset="jumprope-api-logs")
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)
    return logging.getLogger()

logger = setup_logger()

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

def get_obj_hash(sync_token: str, local_id: int) -> str:
    hash_input = f"{sync_token}{local_id}"
    return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
