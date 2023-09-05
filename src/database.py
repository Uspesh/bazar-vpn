from pathlib import Path
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from .config import DB_NAME

Base = declarative_base()

url = Path(__file__).resolve().parent.parent / DB_NAME#'db.db'
db_url = f'sqlite:///{url}'

engine = create_engine(url=db_url)