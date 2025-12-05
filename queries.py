import psycopg2
import pymongo
from neo4j import GraphDatabase
from datetime import datetime, timedelta
import time
import argparse
import sys
import contextlib
import json
import redis

# postgres configuration
PG_HOST = "localhost"
PG_DB = "ecommerce_db"
PG_USER = "admin"
PG_PASS = "password"

# mongo configuration
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB_NAME = "ecommerce_db"

# neo4j configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "password")

# redis configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379

# postgres setup
def get_pg_conn():
    return psycopg2.connect(host=PG_HOST, database=PG_DB, 
                            user=PG_USER, password=PG_PASS)

# mongo setup
def get_mongo_db():
    client = pymongo.MongoClient(MONGO_URI)
    return client[MONGO_DB_NAME]

# neo4j setup
def get_neo4j_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

# redis setup
def get_redis_client():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# fetches a random user id to assign to sarah
def get_user_id():
    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM Users ORDER BY RANDOM() LIMIT 1;")
    user_id = cur.fetchone()[0]
    conn.close()
    return user_id

# queries
def query_1(limit=50):
    print("\nquery 1: retrieve all 'fashion' products with attributes")
    db = get_mongo_db()
    pipeline = [
        {"$match": {"category": "Fashion"}},
        {"$project": {"name": 1, "attributes": 1, "variants": 1}}
    ]
    
    results = list(db.products.aggregate(pipeline))
    display_results = results[:limit] if limit else results
    for p in display_results:
        print(f"product: {p.get('name')}, attributes: {p.get('attributes')}")
    print(f"(total {len(results)} items found)")

def query_2(user_id, limit=50):
    print(f"\nquery 2: last {limit if limit else 'all'} products viewed by sarah")
    db = get_mongo_db()
    six_months_ago = (datetime.utcnow() - timedelta(days=180)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    cursor = db.user_events.find(
        {
            "user_id": user_id, 
            "event_type": "view_product",
            "timestamp": {"$gte": six_months_ago}
        },
        {"details.product_id": 1, "timestamp": 1}
    ).sort("timestamp", -1)
    
    if limit:
        cursor = cursor.limit(limit)
        
    results = list(cursor)
    for r in results:
        print(f"viewed: {r['details'].get('product_id')} at {r['timestamp']}")

def query_3(limit=50):
    print("\nquery 3: check current stock level (low stock < 5)")
    conn = get_pg_conn()
    cur = conn.cursor()
    limit_clause = f"LIMIT {limit}" if limit else ""
    cur.execute(f"""
        SELECT sku, stock_level FROM Inventory 
        WHERE stock_level < 5 {limit_clause};
    """)
    for row in cur.fetchall():
        print(f"low stock warning: sku {row[0]} has only {row[1]} left.")
    conn.close()

def query_4(limit=50):
    print("\nquery 4: fashion products (blue or large)")
    db = get_mongo_db()
    query = {
        "category": "Fashion",
        "$or": [
            {"variants.color": "Blue"},
            {"variants.size": "L"},
            {"attributes.size": "L"}
        ]
    }
    results = list(db.products.find(query))
    display_results = results[:limit] if limit else results
    for p in display_results:
        print(f"product: {p.get('name')}, attributes: {p.get('attributes')}")
    
    count = db.products.count_documents(query)
    print(f"found {count} products matching criteria.")

def query_5(limit=50):
    print("\nquery 5: product page views (ordered by popularity)")
    db = get_mongo_db()
    pipeline = [
        {"$match": {"event_type": "view_product"}},
        {"$group": {"_id": "$details.product_id", "views": {"$sum": 1}}},
        {"$sort": {"views": -1}}
    ]
    if limit:
        pipeline.append({"$limit": limit})
    
    results = list(db.user_events.aggregate(pipeline))
    for r in results:
        print(f"product {r['_id']}: {r['views']} views")

def query_6(user_id, limit=50):
    print(f"\nquery 6: recent search terms for sarah (frequency & time of day)")
    db = get_mongo_db()
    pipeline = [
        {"$match": {"user_id": user_id, "event_type": "search"}},
        {"$project": {
            "query": "$details.query",
            "hour": {"$hour": {"$dateFromString": {"dateString": "$timestamp"}}}
        }},
        {"$project": {
            "query": 1,
            "time_of_day": {
                "$switch": {
                    "branches": [
                        {"case": {"$and": [{"$gte": ["$hour", 5]}, {"$lt": ["$hour", 12]}]}, "then": "Morning"},
                        {"case": {"$and": [{"$gte": ["$hour", 12]}, {"$lt": ["$hour", 17]}]}, "then": "Afternoon"},
                        {"case": {"$and": [{"$gte": ["$hour", 17]}, {"$lt": ["$hour", 21]}]}, "then": "Evening"}
                    ],
                    "default": "Night"
                }
            }
        }},
        {"$group": {
            "_id": {"query": "$query", "tod": "$time_of_day"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}}
    ]
    
    if limit:
        pipeline.append({"$limit": limit})
    results = list(db.user_events.aggregate(pipeline))
    for r in results:
        print(f"term: '{r['_id']['query']}', time: {r['_id']['tod']}, count: {r['count']}")

def query_7(limit=50):
    print("\nquery 7: fetch all carts (from redis)")
    r = get_redis_client()
    keys = list(r.scan_iter("cart:*"))
    print(f"total active carts in redis: {len(keys)}")
    
    display_keys = keys[:limit] if limit else keys
    for key in display_keys:
        cart = r.hgetall(key)
        items = json.loads(cart.get("items", "[]"))
        item_count = sum(item['quantity'] for item in items)
        
        print(f"cart ({key}): user {cart.get('user_id')} on {cart.get('device')} has {item_count} items. total: ${cart.get('total_amount')}")

def query_8(user_id, limit=50):
    print(f"\nquery 8: retrieve all orders for sarah")
    conn = get_pg_conn()
    cur = conn.cursor()
    limit_clause = f"LIMIT {limit}" if limit else ""
    query = f"""
        SELECT o.order_id, o.status, o.total_amount, s.shipping_method
        FROM Orders o LEFT JOIN Shipments s ON o.order_id = s.order_id
        WHERE o.user_id = %s {limit_clause};
    """
    cur.execute(query, (user_id,))
    rows = cur.fetchall()
    for r in rows:
        print(f"order {r[0]}: status={r[1]}, total=${r[2]}, ship={r[3]}")
    conn.close()

def query_9(user_id):
    print(f"\nquery 9: list items returned by sarah")
    conn = get_pg_conn()
    cur = conn.cursor()
    query = """
        SELECT r.return_id, r.sku, r.refund_amount, r.status FROM Returns r
        JOIN Orders o ON r.order_id = o.order_id WHERE o.user_id = %s;
    """
    cur.execute(query, (user_id,))
    rows = cur.fetchall()
    
    if rows:
        for r in rows:
            print(f"return {r[0]}: sku {r[1]}, refund ${r[2]}, status {r[3]}")
    else:
        print("no returns found for this user.")
    conn.close()

def query_10(user_id):
    print(f"\nquery 10: average days between purchases for sarah")
    conn = get_pg_conn()
    cur = conn.cursor()
    query = """
        SELECT AVG(EXTRACT(DAY FROM (o.created_at - (
            SELECT MAX(sub.created_at) FROM Orders sub 
            WHERE sub.user_id = o.user_id AND sub.created_at < o.created_at
        )))) FROM Orders o WHERE o.user_id = %s;
    """
    cur.execute(query, (user_id,))
    result = cur.fetchone()[0]
    print(f"average days: {result if result else 'n/a (not enough orders)'}")
    conn.close()

def query_11():
    print("\nquery 11: cart abandonment % (last 30 days)")
    db = get_mongo_db()
    carts = len(db.user_events.distinct("session_id", {"event_type": "add_to_cart"}))
    purchases = len(db.user_events.distinct("session_id", {"event_type": "purchase_completed"}))
    if carts > 0:
        abandoned = ((carts - purchases) / carts) * 100
        print(f"carts created: {carts}, purchases: {purchases}")
        print(f"abandonment rate: {abandoned:.2f}%")
    else:
        print("no cart activity found.")

def query_12(limit=3):
    print("\nquery 12: top 3 products purchased with 'headphones'")
    driver = get_neo4j_driver()
    limit_clause = f"LIMIT {limit}" if limit else ""
    query = f"""
        MATCH (target:Product) WHERE target.name CONTAINS 'Headphones'
        MATCH (target)<-[:CONTAINS]-(o:Order)-[:CONTAINS]->(other:Product)
        WHERE target <> other
        RETURN other.name, count(*) as frequency
        ORDER BY frequency DESC
        {limit_clause}
    """
    
    with driver.session() as session:
        results = session.run(query)
        data = list(results)
        if data:
            for r in data:
                print(f"product: {r['other.name']}, frequency: {r['frequency']}")
        else:
            print("no graph matches found (check if seed_graph.py ran successfully).")

def query_13(limit=50):
    print("\nquery 13: user lifetime stats (days since purchase, total count)")
    conn = get_pg_conn()
    cur = conn.cursor()
    
    limit_clause = f"LIMIT {limit}" if limit else ""
    query = f"""
        SELECT user_id, COUNT(order_id) as total_orders,
        EXTRACT(DAY FROM (NOW() - MAX(created_at))) as days_since_last
        FROM Orders GROUP BY user_id {limit_clause};
    """
    cur.execute(query)
    for r in cur.fetchall():
        print(f"user {r[0]}: {r[1]} orders, last purchased {r[2]} days ago")
    conn.close()

# query timer
def time_query(name, func, *args):
    start = time.time()
    try:
        func(*args)
        duration = time.time() - start
        status = "pass" if duration <= 2.0 else "fail"
        return name, duration, status
    except Exception as e:
        return name, 0.0, f"error: {e}"

# evaluation
def run_evaluation(limit=50):
    user_id = get_user_id()
    results = []
    results.append(time_query("query 1: fashion products", query_1, limit))
    results.append(time_query("query 2: recent views", query_2, user_id, limit))
    results.append(time_query("query 3: low stock", query_3, limit))
    results.append(time_query("query 4: fashion blue/large", query_4, limit))
    results.append(time_query("query 5: product popularity", query_5, limit))
    results.append(time_query("query 6: search terms", query_6, user_id, limit))
    results.append(time_query("query 7: fetch carts (redis)", query_7, limit))
    results.append(time_query("query 8: sarah orders", query_8, user_id, limit))
    results.append(time_query("query 9: returned items", query_9, user_id))
    results.append(time_query("query 10: avg days between purchases", query_10, user_id))
    results.append(time_query("query 11: cart abandonment", query_11))
    results.append(time_query("query 12: frequently bought together", query_12, limit))
    results.append(time_query("query 13: user lifetime stats", query_13, limit))
    
    print("\n===============================================================")
    print(f"{'query':<40} | {'time (s)':<10} | {'status':<10}")
    print("===============================================================")
    
    all_pass = True
    for name, duration, status in results:
        print(f"{name:<40} | {duration:<10.4f} | {status:<10}")
        if status != "pass":
            all_pass = False
            
    print("===============================================================")
    if all_pass:
        print("\nall queries passed the 2-second performance limit")
    else:
        print("\nsome queries failed performance or execution checks")

def execute_queries():
    parser = argparse.ArgumentParser(description="Run queries.")
    parser.add_argument("--export", help="Export output to file", type=str)
    args = parser.parse_args()
    limit = 50
    output_context = contextlib.nullcontext()
    if args.export:
        limit = None
        output_context = open(args.export, "w")

    # running the queries
    start_time = time.time()
    try:
        with output_context as f:
            if f:
                sys.stdout = f
            run_evaluation(limit)
    except Exception as e:
        print(f"\nerror evaluating queries: {e}")
    print(f"total execution time: {time.time() - start_time:.2f} seconds")

# executing the queries
execute_queries()
