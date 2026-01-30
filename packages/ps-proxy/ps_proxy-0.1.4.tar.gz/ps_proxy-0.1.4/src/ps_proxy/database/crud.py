from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .tables import Base, Proxies
from datetime import date
from loguru import logger


class Database:
    def __init__(self):
        try:
            self.engine = create_engine("sqlite:///ps_proxy.db")
            Base.metadata.create_all(self.engine)
            logger.info("Database connection initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def init_database(self):
        try:
            Session = sessionmaker(bind=self.engine)
            session = Session()
            return session
        except Exception as e:
            logger.error(f"Error initializing database session: {e}")
            raise
    
    def create_proxy(self,proxy:dict):
        session = None
        try:
            session = self.init_database()
            proxy_db = Proxies(
                proxy = str(proxy),
                date = date.today()
            )
            session.add(proxy_db)
            session.commit()
        except Exception as e:
            logger.error(f"Error creating proxy: {e}")
            if session:
                session.rollback()
            raise
        finally:
            if session:
                session.close()

    def read_proxy(self):
        session = None
        try:
            logger.debug("Reading proxies from database")
            session = self.init_database()
            proxy_list = session.query(Proxies).filter(
                Proxies.date == date.today()
            ).all()
            logger.info(f"Retrieved {len(proxy_list)} proxies from database")
            return proxy_list
        except Exception as e:
            logger.error(f"Error reading proxies: {e}")
            raise
        finally:
            if session:
                session.close()
    
    def delete_proxy(self,id:int):
        session = None
        try:
            session = self.init_database()
            proxy = session.query(Proxies).filter_by(id=id).first()
            if proxy is None:
                logger.warning(f"Proxy with id {id} not found")
                return
            session.delete(proxy)
            session.commit()
            logger.info(f"Proxy with id {id} deleted successfully")
        except Exception as e:
            logger.error(f"Error deleting proxy: {e}")
            if session:
                session.rollback()
            raise
        finally:
            if session:
                session.close()