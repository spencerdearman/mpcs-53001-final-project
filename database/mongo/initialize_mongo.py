import json
import pymongo
import os

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "ecommerce_db"
PRODUCTS_FILE = "data/products/products.json" 
LOGS_FILE = "data/logs/user_behavior_logs.json"

def initialize_mongo():
    print("connecting to mongodb")
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    # load the products
    if os.path.exists(PRODUCTS_FILE):
        print(f"reading {PRODUCTS_FILE}")
        with open(PRODUCTS_FILE, "r") as f:
            product_data = json.load(f)
        
        print(f"inserting {len(product_data)} products")
        db.products.drop()
        db.products.insert_many(product_data)
        print("products loaded successfully.")

        # create index for faster lookups
        db.products.create_index("_id")
    else:
        print(f"error: could not find {PRODUCTS_FILE}")

    # load the user logs
    if os.path.exists(LOGS_FILE):
        print(f"reading {LOGS_FILE}")
        with open(LOGS_FILE, "r") as f:
            log_data = json.load(f)
            
        print(f"inserting {len(log_data)} logs")
        db.user_events.drop() 
        
        # batch insert
        batch_size = 5000
        for i in range(0, len(log_data), batch_size):
            batch = log_data[i:i + batch_size]
            db.user_events.insert_many(batch)
            if i % 50000 == 0:
                print(f"inserted {i} logs")
        print("logs loaded successfully.")
    else:
        print(f"error: could not find {LOGS_FILE}")

    client.close()

# running the script
initialize_mongo()
