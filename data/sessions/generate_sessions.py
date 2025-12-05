# base generated from Gemini: https://gemini.google.com/share/4b1fd1f88388
import redis
import json
import random
import time
from faker import Faker

# configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379
NUM_SESSIONS = 500
fake = Faker()

def get_redis_client():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def generate_sessions():
    r = get_redis_client()
    print(f"connecting to redis at {REDIS_HOST}:{REDIS_PORT}")
    
    # clear existing sessions to avoid stale data
    print("clearing existing 'cart:*' keys...")
    for key in r.scan_iter("cart:*"):
        r.delete(key)

    print(f"generating {NUM_SESSIONS} active sessions...")
    
    devices = ['laptop', 'tablet', 'mobile', 'desktop']
    
    for _ in range(NUM_SESSIONS):
        # simulate a session
        session_id = fake.uuid4()
        user_id = random.randint(1, 1000)
        device = random.choice(devices)
        
        # create a cart with 1-5 items
        cart_items = []
        num_items = random.randint(1, 5)
        total_amount = 0.0
        
        for _ in range(num_items):
            product_id = random.randint(1, 10000)
            qty = random.randint(1, 3)
            price = round(random.uniform(10.0, 500.0), 2)
            
            item = {
                "product_id": product_id,
                "quantity": qty,
                "price": price,
                "name": f"Product {product_id}"
            }
            cart_items.append(item)
            total_amount += (price * qty)

        # store in redis as a hash
        cart_key = f"cart:{session_id}"
        cart_data = {
            "user_id": user_id,
            "device": device,
            "items": json.dumps(cart_items),
            "total_amount": round(total_amount, 2),
            "last_active": int(time.time())
        }
        r.hset(cart_key, mapping=cart_data)
        r.expire(cart_key, 3600)

    print("session generation complete.")

# generating sessions
try:
    generate_sessions()
except Exception as e:
    print(f"error generating sessions: {e}")
