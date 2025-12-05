# base generated from Gemini: https://gemini.google.com/share/600de4cc1ff1
# had to modify to work with our schema
import psycopg2
from psycopg2 import extras
from pymongo import MongoClient
from faker import Faker
import random
from datetime import datetime, timedelta

# configuration
PG_HOST = "localhost"
PG_NAME = "ecommerce_db"
PG_USER = "admin"
PG_PASS = "password"
PG_PORT = "5432"

# mongo configuration
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB_NAME = "ecommerce_db"
MONGO_COLLECTION = "products"

NUM_ORDERS = 100000 
BATCH_SIZE = 10000

def get_pg_connection():
    return psycopg2.connect(host=PG_HOST, database=PG_NAME, user=PG_USER, password=PG_PASS, port=PG_PORT)

def populate_inventory(mongo_col, pg_conn, pg_cur):
    print("reading products from mongodb.")
    # fetch all products with relevant fields
    mongo_products = list(mongo_col.find({}, {"_id": 1, "variants": 1, "price": 1, "stock_level": 1}))
    
    inventory_data = []
    for prod in mongo_products:
        p_id = str(prod["_id"])
        if "variants" in prod and prod["variants"]:
            for variant in prod["variants"]:
                sku = variant.get("sku")
                if not sku:
                    sku = f"{p_id}-{variant.get('size')}-{variant.get('color')}"
                price = variant.get("price", prod.get("price", 0))
                stock = variant.get("stock_level", 0)
                inventory_data.append((sku, p_id, stock, price))
        else:
            sku = p_id
            price = prod.get("price", 0)
            stock = prod.get("stock_level", 0)
            inventory_data.append((sku, p_id, stock, price))

    print(f"inserting {len(inventory_data)} items into postgres inventory.")
    
    # create query for insertion
    query = """
        INSERT INTO Inventory (sku, mongo_product_id, stock_level, price)
        VALUES %s
        ON CONFLICT (sku) DO NOTHING;
    """
    try:
        extras.execute_values(pg_cur, query, inventory_data)
        pg_conn.commit()
    except Exception as e:
        print(f"error populating inventory: {e}")
        pg_conn.rollback()

    return inventory_data

def generate_orders(pg_conn, pg_cur, inventory_list):
    print("fetching User IDs.")
    pg_cur.execute("SELECT user_id FROM Users;")
    users = [row[0] for row in pg_cur.fetchall()]
    if not users:
        print("error: no users found. Run generate_users.py first.")
        return

    print(f"generating {NUM_ORDERS} orders.")
    fake = Faker()
    
    # pre-process inventory for fast lookup
    inv_lookup = [(item[0], item[1], float(item[3])) for item in inventory_list]

    for i in range(NUM_ORDERS):
        user_id = random.choice(users)
        order_date = fake.date_time_between(start_date='-1y', end_date='now')
        status = random.choice(['Pending', 'Shipped', 'Delivered', 'Returned'])
        
        # insert order header and get the id back (crucial for serial pk)
        pg_cur.execute("""
            INSERT INTO Orders (user_id, status, created_at, tax_amount, shipping_cost, total_amount)
            VALUES (%s, %s, %s, 0, 0, 0)
            RETURNING order_id;
        """, (user_id, status, order_date))
        
        order_id = pg_cur.fetchone()[0]
        
        # pick items
        num_items = random.randint(1, 5)
        selected_items = random.choices(inv_lookup, k=num_items)
        
        order_items_data = []
        order_total = 0
        
        for sku, mongo_id, price in selected_items:
            qty = random.randint(1, 3)
            # schema requires: order_id, sku, mongo_product_id, quantity, unit_price_at_purchase
            order_items_data.append((order_id, sku, mongo_id, qty, price))
            order_total += (price * qty)
            
        # insert items (batch insert for this specific order)
        item_query = """
            INSERT INTO Order_Items (order_id, sku, mongo_product_id, quantity, unit_price_at_purchase) 
            VALUES %s
        """
        extras.execute_values(pg_cur, item_query, order_items_data)

        # update order totals
        tax = order_total * 0.08
        shipping = 10.00 if order_total < 50 else 0.00
        final_total = order_total + tax + shipping
        
        pg_cur.execute("""
            UPDATE Orders SET tax_amount=%s, shipping_cost=%s, total_amount=%s WHERE order_id=%s
        """, (tax, shipping, final_total, order_id))

        # handle returns
        if status == 'Returned':
            item = random.choice(order_items_data)
            r_sku = item[1]
            r_qty = random.randint(1, item[3])
            r_price = item[4]
            refund = r_qty * r_price
            pg_cur.execute("""
                INSERT INTO Returns (order_id, sku, quantity, reason, refund_amount, status)
                VALUES (%s, %s, %s, %s, %s, 'Completed')
            """, (order_id, r_sku, r_qty, "Defective or Changed Mind", refund))

        # commit every batch size
        if i % BATCH_SIZE == 0:
            pg_conn.commit()
            print(f"generated {i} orders...")

    pg_conn.commit()
    print(f"finished. total orders: {NUM_ORDERS}")

def main():
    # connect to mongo
    try:
        mongo_client = MongoClient(MONGO_URI)
        mongo_db = mongo_client[MONGO_DB_NAME]
        mongo_col = mongo_db[MONGO_COLLECTION]
        print("connected to mongodb.")
    except Exception as e:
        print(f"mongo error: {e}")
        return

    # connect to postgres
    try:
        pg_conn = get_pg_connection()
        pg_cur = pg_conn.cursor()
        print("connected to postgres.")
    except Exception as e:
        print(f"postgres error: {e}")
        return

    # execution flow
    try:
        inventory_data = populate_inventory(mongo_col, pg_conn, pg_cur)
        if inventory_data:
            generate_orders(pg_conn, pg_cur, inventory_data)
            
    finally:
        if pg_cur: pg_cur.close()
        if pg_conn: pg_conn.close()
        if mongo_client: mongo_client.close()

# running script
main()
