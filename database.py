import sqlite3
import logging
from config import Config
from cryptography.fernet import Fernet

class DatabaseManager:
    """Управление базой данных SQLite для хранения данных арбитража и токенов"""
    
    def __init__(self, db_path=Config.DB_PATH):
        self.db_path = db_path
        self._initialize_db()
        self.cipher = Fernet(Fernet.generate_key())  # В продакшене использовать постоянный ключ из .env

    def _initialize_db(self):
        """Инициализация структуры базы данных"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Таблица для хранения арбитражных данных
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS arbitrage_opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nft_id TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                model TEXT NOT NULL,
                auction_end INTEGER NOT NULL,
                current_bid REAL NOT NULL,
                portals_price REAL NOT NULL,
                tonnel_price REAL NOT NULL,
                profit REAL NOT NULL,
                price_range TEXT NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Таблица для хранения токенов авторизации
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS auth_tokens (
                service TEXT PRIMARY KEY,
                encrypted_token TEXT NOT NULL,
                expires_at INTEGER
            )
            ''')
            
            # Индексы для оптимизации запросов
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_profit ON arbitrage_opportunities(profit)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_auction_end ON arbitrage_opportunities(auction_end)')
            
            conn.commit()

    def _get_connection(self):
        """Установка соединения с базой данных"""
        return sqlite3.connect(self.db_path, timeout=20)
    
    def _encrypt_token(self, token: str) -> str:
        """Шифрование токена перед сохранением"""
        return self.cipher.encrypt(token.encode()).decode()
    
    def _decrypt_token(self, encrypted_token: str) -> str:
        """Расшифровка токена при извлечении"""
        return self.cipher.decrypt(encrypted_token.encode()).decode()

    def save_auth_token(self, service: str, token: str, expires_at: int = None):
        """Сохранение токена авторизации в БД"""
        encrypted = self._encrypt_token(token)
        with self._get_connection() as conn:
            conn.execute('''
            INSERT OR REPLACE INTO auth_tokens (service, encrypted_token, expires_at)
            VALUES (?, ?, ?)
            ''', (service, encrypted, expires_at))
            conn.commit()

    def get_auth_token(self, service: str) -> str:
        """Получение токена авторизации из БД"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT encrypted_token FROM auth_tokens WHERE service = ?
            ''', (service,))
            row = cursor.fetchone()
            return self._decrypt_token(row[0]) if row else None

    def save_arbitrage_opportunities(self, opportunities: list):
        """Сохранение арбитражных возможностей в БД"""
        if not opportunities:
            return
            
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany('''
            INSERT OR REPLACE INTO arbitrage_opportunities (
                nft_id, name, model, auction_end, current_bid, 
                portals_price, tonnel_price, profit, price_range
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', opportunities)
            conn.commit()

    def get_arbitrage_opportunities(self, sort_by: str = 'profit', limit: int = 20):
        """Получение арбитражных возможностей из БД с сортировкой"""
        valid_sorts = {'profit': 'profit DESC', 'time': 'auction_end ASC'}
        sort_order = valid_sorts.get(sort_by, 'profit DESC')
        
        query = f'''
        SELECT 
            nft_id, name, model, auction_end, current_bid,
            portals_price, tonnel_price, profit, price_range
        FROM arbitrage_opportunities
        WHERE profit > ?
        ORDER BY {sort_order}
        LIMIT ?
        '''
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (Config.MIN_PROFIT, limit))
            return cursor.fetchall()
