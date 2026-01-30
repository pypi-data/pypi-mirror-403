from sqlalchemy.orm import declarative_base
from sqlalchemy import Column,Integer, String, Date
from loguru import logger

logger.debug("Loading database tables module")
Base= declarative_base()

class Proxies(Base):
    __tablename__ ="proxies"

    id = Column(Integer, primary_key=True,autoincrement=True)
    proxy = Column(String, nullable=False)
    date = Column(Date,nullable=False)

