from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./data/sql_app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={},
            pool_recycle=900,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
