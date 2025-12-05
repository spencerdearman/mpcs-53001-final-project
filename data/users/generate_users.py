import psycopg2
from faker import Faker
import random

# configuration
DB_HOST = "localhost"
DB_NAME = "ecommerce_db"
DB_USER = "admin"
DB_PASS = "password"
DB_PORT = "5432"

def generate_users():
    print("connecting to postrgres")
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT)
        cur = conn.cursor()
    except Exception as e:
        print(f"error connecting to database: {e}")
        return

    fake = Faker()
    NUM_USERS = 1000

    print(f"generating {NUM_USERS} users")
    
    users_data = []
    for _ in range(NUM_USERS):
        email = fake.unique.email()
        password = fake.password(length=12)
        first_name = fake.first_name()
        last_name = fake.last_name()
        created_at = fake.date_time_between(start_date='-2y', end_date='now')
        
        users_data.append((email, password, first_name, last_name, created_at))

    insert_query = """
    INSERT INTO Users (email, password, first_name, last_name, created_at)
    VALUES (%s, %s, %s, %s, %s);
    """
    try:
        cur.executemany(insert_query, users_data)
        conn.commit()
        print(f"success! {NUM_USERS} users have been inserted.")
    except Exception as e:
        print(f"error inserting users: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

# generating the users
generate_users()
