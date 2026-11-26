import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_NAME'),
                host=os.getenv('DB_HOST'),
                port=os.getenv('DB_PORT')
            )
            await self.create_tables()
            print("✅ Database connected and tables created successfully!")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")

    async def create_tables(self):
        async with self.pool.acquire() as conn:
            # جدول کاربران
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT PRIMARY KEY,
                    first_name TEXT,
                    coins INT DEFAULT 0,
                    vip_expire_at TIMESTAMP DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')
            # جدول گروه‌ها
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS groups (
                    id BIGINT PRIMARY KEY,
                    title TEXT,
                    anti_link BOOLEAN DEFAULT FALSE,
                    anti_word BOOLEAN DEFAULT FALSE,
                    rules TEXT DEFAULT NULL
                );
            ''')
            # جدول اخطارها
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS warnings (
                    user_id BIGINT,
                    group_id BIGINT,
                    count INT DEFAULT 0,
                    PRIMARY KEY (user_id, group_id)
                );
            ''')

db = Database()
