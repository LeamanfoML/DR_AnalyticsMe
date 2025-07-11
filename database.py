import asyncio
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

class Deal(Base):
    __tablename__ = 'deals'
    id = Column(Integer, primary_key=True)
    gift_id = Column(String, nullable=False)
    source_market = Column(String, nullable=False)
    target_market = Column(String, nullable=False)
    buy_price = Column(Float, nullable=False)
    sell_price = Column(Float, nullable=False)
    profit = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return (f"<Deal(id={self.id}, gift_id='{self.gift_id}', "
                f"source='{self.source_market}', target='{self.target_market}', "
                f"profit={self.profit:.2f})>")

class Settings(Base):
    __tablename__ = 'settings'
    id = Column(Integer, primary_key=True)
    min_price = Column(Float, default=1.0)
    max_price = Column(Float, default=100.0)
    min_profit = Column(Float, default=0.1)
    tonnel_enabled = Column(Integer, default=1)
    portals_enabled = Column(Integer, default=1)
    resale_offset = Column(Float, default=0.01)

    def to_dict(self):
        return {
            'min_price': self.min_price,
            'max_price': self.max_price,
            'min_profit': self.min_profit,
            'tonnel_enabled': bool(self.tonnel_enabled),
            'portals_enabled': bool(self.portals_enabled),
            'resale_offset': self.resale_offset
        }

class AsyncDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)
        logger.info(f"Database initialized at {db_path}")

    async def _run_in_thread(self, func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, func, *args, **kwargs)

    async def save_deal(self, deal_data):
        """Асинхронное сохранение сделки в базу"""
        def sync_save():
            session = self.Session()
            try:
                deal = Deal(**deal_data)
                session.add(deal)
                session.commit()
                logger.info(f"Saved deal: {deal}")
                return deal.id
            except Exception as e:
                session.rollback()
                logger.error(f"Error saving deal: {e}")
                raise
            finally:
                self.Session.remove()
        
        return await self._run_in_thread(sync_save)

    async def get_settings(self):
        """Асинхронное получение настроек"""
        def sync_get():
            session = self.Session()
            try:
                settings = session.query(Settings).first()
                if not settings:
                    # Создаем настройки по умолчанию, если их нет
                    settings = Settings()
                    session.add(settings)
                    session.commit()
                    logger.info("Created default settings")
                return settings
            except Exception as e:
                logger.error(f"Error getting settings: {e}")
                raise
            finally:
                self.Session.remove()
        
        return await self._run_in_thread(sync_get)

    async def update_settings(self, new_settings):
        """Асинхронное обновление настроек"""
        def sync_update():
            session = self.Session()
            try:
                settings = session.query(Settings).first()
                if not settings:
                    settings = Settings(**new_settings)
                    session.add(settings)
                else:
                    for key, value in new_settings.items():
                        setattr(settings, key, value)
                session.commit()
                logger.info(f"Updated settings: {new_settings}")
                return True
            except Exception as e:
                session.rollback()
                logger.error(f"Error updating settings: {e}")
                return False
            finally:
                self.Session.remove()
        
        return await self._run_in_thread(sync_update)

    async def get_deals(self, limit=10):
        """Асинхронное получение последних сделок"""
        def sync_get():
            session = self.Session()
            try:
                deals = session.query(Deal).order_by(Deal.timestamp.desc()).limit(limit).all()
                return deals
            except Exception as e:
                logger.error(f"Error getting deals: {e}")
                return []
            finally:
                self.Session.remove()
        
        return await self._run_in_thread(sync_get)

    async def close(self):
        """Закрытие соединений с базой"""
        self.engine.dispose()
        logger.info("Database connections closed")

# Пример использования:
# db = AsyncDatabase('arbitrage.db')
# asyncio.run(db.save_deal({...}))
