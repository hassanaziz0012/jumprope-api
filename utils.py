import hashlib
from sqlalchemy.orm import Session
from models.user_profile import UserProfile
from axiom_py.logging import AxiomHandler
import axiom_py
import logging

import sys

def setup_logger():
    # client = axiom_py.Client()
    # handler = AxiomHandler(client, dataset="jumprope-api-logs")
    # logging.getLogger().addHandler(handler)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Configure standard console logging to stdout
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

logger = setup_logger()

from fastapi import HTTPException

def sync_user_profile(db: Session, user_data):
    user = db.query(UserProfile).filter(UserProfile.sync_token == user_data.sync_token).first()
    if not user:
        raise HTTPException(status_code=404, detail="User account not found")
    for key, value in user_data.model_dump(exclude={'id'}).items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user

def get_obj_hash(sync_token: str, local_id: int) -> str:
    hash_input = f"{sync_token}{local_id}"
    return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
