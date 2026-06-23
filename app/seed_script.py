import os;
import random;
from datetime import datetime, timedelta, timezone
import psycopg2
from psycopg2.extras import execute_values
from faker import Faker
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

faker = Faker()
CATEGORIES = ["Electronics", "Clothing", "Books", "Sports", "Home", "Garden", "Toys"]

def run_seeder(total_count=200000, batch_size = 10000):
    connection = psycopg2.connect(DB_URL)
    cursor = connection.cursor()

    print("Database layout ready")
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS products (
                   unique_id SERIAL PRIMARY KEY,
                   name VARCHAR(255) NOT NULL,
                   category VARCHAR(50) NOT NULL,
                   price DECIMAL(10, 2) NOT NULL,
                   created_at TIMESTAMPTZ NOT NULL,
                   updated_at TIMESTAMPTZ NOT NULL
                    )
                """)
    connection.commit()
    print("Table created successfully")

    batch_data = []
    inserted_count = 0;
    base_time = datetime.now(timezone.utc)

    for i in range(total_count):
        created_at = base_time + timedelta(seconds = i*2)
        product = (
            f"{faker.word().capitalize()} {random.choice(['Pro','Max','Lite', 'Air', 'Plus'])}",
            random.choice(CATEGORIES),
            round(random.uniform(10.0, 1000.0), 2),
            created_at,
            created_at
        )
        batch_data.append(product)

        if len(batch_data) >= batch_size:
            execute_values(cursor,
                           "INSERT INTO products (name, category, price, created_at, updated_at) VALUES %s",
                           batch_data)
            connection.commit()
            inserted_count += len(batch_data)
            print(f"Inserted {inserted_count}/{total_count} records")
            batch_data = []
        
    if batch_data:
        execute_values(cursor,
                       "INSERT INTO products (name, category, price, created_at, updated_at) VALUES %s",
                       batch_data)
        connection.commit()
        cursor.close()
        connection.close()
        print(f"Inserted {total_count} records successfully")

if __name__ == "__main__":
    run_seeder()



