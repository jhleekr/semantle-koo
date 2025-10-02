from database import Base
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import Session
import hashlib
from datetime import datetime
from pytz import timezone

KST = timezone('Asia/Seoul')

class Data(Base):
    __tablename__ = "data"
    __table_args__ = {'extend_existing': True} 

    sid = Column(String(8), primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True))
    data = Column(String(100))


def d_new(db: Session):
    sid = hashlib.sha256(("!"+str(datetime.now(tz=KST).timestamp())).encode('utf-8')).hexdigest()[:8]
    while d_get(db, sid):
        sid = hashlib.sha256(("!"+str(datetime.now(tz=KST).timestamp())).encode('utf-8')).hexdigest()[:8]
    db_item = Data(sid=sid, timestamp=datetime.now(tz=KST), data="{}")
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return sid

def d_get(db: Session, sid: str):
    return db.query(Data).filter(Data.sid==sid).first()

def d_modify(db: Session, sid: str, d: str):
    db.query(Data).filter(Data.sid==sid).update({"data": d})
    db.commit()
    return

def d_all(db: Session):
    return db.query(Data).all()

def d_delete(db: Session, sid: str):
    db.query(Data).filter(Data.sid==sid).delete()
    db.commit()
    return
