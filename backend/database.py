from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./ashrag.db"

Base = declarative_base()

engine = create_engine(
    url= DATABASE_URL,
    connect_args={"check_same_thread" : False}
)

# print(engine)

sessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit = False
)


def get_db():
    db = sessionLocal()
    
    try:
        yield db
        
    finally:
        db.close()
        