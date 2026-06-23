import os
from fastapi import FastAPI
import asyncpg
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

class Database:
    def __init__(self):
        self.pool:asyncpg.Pool = None

    async def connect(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=2,
                max_size=10,
                command_timeout=60,
            )
            print("Database connection was successful")
    
    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            print("Database connection closed")

db = Database()