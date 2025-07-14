import sqlite3
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(settings.DB_PATH)
        self._create_tables()

    def _create_tables(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS opportunities (
                    id INTEGER PRIMARY KEY,
                    auction_id TEXT UNIQUE,
                    gift_name TEXT,
                    model TEXT,
                    current_bid REAL,
                    portals_price REAL,
                    tonnel_price REAL,
                    profit REAL,
                    end_time INTEGER
                )
            """)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Database error: {e}")

    def save_opportunities(self, opportunities):
        try:
            cursor = self.conn.cursor()
            for opp in opportunities:
                cursor.execute("""
                    INSERT OR REPLACE INTO opportunities 
                    (auction_id, gift_name, model, current_bid, portals_price, tonnel_price, profit, end_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, opp)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Save error: {e}")

    def get_opportunities(self, sort_by="profit", filters=None):
        try:
            query = "SELECT * FROM opportunities WHERE profit > 0.1"
            params = []
            
            if filters:
                price_ranges = {
                    "1-5": (1, 5),
                    "5-10": (5, 10),
                    "10-25": (10, 25),
                    "25-50": (25, 50)
                }
                if filters in price_ranges:
                    low, high = price_ranges[filters]
                    query += " AND current_bid BETWEEN ? AND ?"
                    params.extend([low, high])
            
            if sort_by == "profit":
                query += " ORDER BY profit DESC"
            elif sort_by == "end_time":
                query += " ORDER BY end_time ASC"
            
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Fetch error: {e}")
            return []
