import psycopg2
from neo4j import GraphDatabase
import pymongo
import sys

# configuration
PG_HOST = "localhost"
PG_DB = "ecommerce_db"
PG_USER = "admin"
PG_PASS = "password"

# mongo configuration
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB = "ecommerce_db"

# neo4j configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "password")

def initialize_graph():
    print("connecting to databases")
    try:
        # connect to postgres
        pg_conn = psycopg2.connect(host=PG_HOST, database=PG_DB, user=PG_USER, password=PG_PASS)
        pg_cur = pg_conn.cursor()

        # connect to mongo
        mongo_client = pymongo.MongoClient(MONGO_URI)
        mongo_db = mongo_client[MONGO_DB]
        products_col = mongo_db["products"]
        
        # connect to neo4j
        driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    except Exception as e:
        print(f"connection error: {e}")
        return

    # load products (nodes)
    print("fetching products from mongo")
    mongo_products = list(products_col.find({}, {"_id": 1, "name": 1, "category": 1}))
    
    print(f"loading {len(mongo_products)} products into neo4j")
    # query to create product nodes
    create_products_query = """
    UNWIND $batch AS row
    MERGE (p:Product {product_id: row.id})
    SET p.name = row.name, p.category = row.category
    """
    product_batch = [
        {"id": str(p["_id"]), "name": p.get("name", "Unknown"), "category": p.get("category", "General")} 
        for p in mongo_products
    ]
    
    with driver.session() as session:
        # clear old data
        session.run("MATCH (n) DETACH DELETE n")
        # create constraints for speed
        try:
            session.run("CREATE CONSTRAINT FOR (p:Product) REQUIRE p.product_id IS UNIQUE")
            session.run("CREATE CONSTRAINT FOR (u:User) REQUIRE u.user_id IS UNIQUE")
        except:
            pass 

        # batch insert products
        chunk_size = 5000
        for i in range(0, len(product_batch), chunk_size):
            chunk = product_batch[i:i + chunk_size]
            session.run(create_products_query, batch=chunk)
            print(f"   indexed {i + len(chunk)} products")

    # load orders (relationships)
    print("fetching orders from postgres")
    
    # getting user id, order id, and the product id from the order_items table
    sql_query = """
        SELECT o.user_id, o.order_id, i.mongo_product_id
        FROM Orders o JOIN Order_Items i ON o.order_id = i.order_id
        LIMIT 100000; 
    """
    pg_cur.execute(sql_query)
    rows = pg_cur.fetchall()
    print(f"syncing order-item relationships to neo4j")
    
    # group by order id to minimize db calls
    orders_map = {}
    for user_id, order_id, prod_id in rows:
        if order_id not in orders_map:
            orders_map[order_id] = {"user": user_id, "products": []}
        orders_map[order_id]["products"].append(prod_id)
    # convert to list for batching
    order_batch = []
    for oid, data in orders_map.items():
        order_batch.append({
            "oid": oid,
            "uid": data["user"],
            "pids": data["products"]
        })

    # query to draw the graph
    # (User)-[:PLACED]->(Order)-[:CONTAINS]->(Product)
    create_graph_query = """
    UNWIND $batch AS row
    MERGE (u:User {user_id: row.uid})
    MERGE (o:Order {order_id: row.oid})
    MERGE (u)-[:PLACED]->(o)
    WITH o, row
    UNWIND row.pids AS pid
    MATCH (p:Product {product_id: pid})
    MERGE (o)-[:CONTAINS]->(p)
    """
    with driver.session() as session:
        chunk_size = 1000
        total = 0
        for i in range(0, len(order_batch), chunk_size):
            chunk = order_batch[i:i + chunk_size]
            session.run(create_graph_query, batch=chunk)
            total += len(chunk)
            if total % 5000 == 0:
                print(f"synced {total} orders")

    print("graph populated!")
    driver.close()
    pg_cur.close()
    pg_conn.close()
    mongo_client.close()

# running the script
initialize_graph()
