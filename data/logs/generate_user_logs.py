# base generated from Gemini: https://gemini.google.com/share/000057595518
import json
import random
import uuid
from datetime import datetime, timedelta

# configuration
NUM_LOGS = 500000
NUM_PRODUCTS = 10000
OUTPUT_FILE = "user_behavior_logs.json"

# shared data logic
CATEGORY_MAP = {
    "Electronics": {
        "Smartphone": (300, 1200), "Laptop": (800, 2500), 
        "Headphones": (50, 400), "Smart Watch": (150, 500), 
        "Camera": (400, 3000), "Monitor": (100, 800)
    },
    "Fashion": {
        "T-Shirt": (15, 50), "Jeans": (40, 150), 
        "Sneakers": (60, 250), "Jacket": (80, 400), 
        "Dress": (50, 200), "Watch": (100, 1000)
    },
    "Home & Kitchen": {
        "Blender": (30, 150), "Coffee Maker": (40, 300), 
        "Sofa": (300, 1500), "Desk Lamp": (20, 100), 
        "Rug": (50, 400), "Cookware Set": (100, 600)
    },
    "Beauty": {
        "Moisturizer": (15, 80), "Perfume": (50, 200), 
        "Lipstick": (10, 50), "Serum": (25, 120),
        "Shampoo": (10, 40)
    },
    "Books": {
        "Fiction": (10, 30), "Non-Fiction": (15, 40), 
        "Technical": (40, 120), "Art Book": (30, 100)
    }
}

# search terms
SEARCH_TERMS = [subcat for cat in CATEGORY_MAP for subcat in CATEGORY_MAP[cat]]
SEARCH_TERMS.extend(["gift for dad", "sale", "best sellers", "new arrivals"])

# devices
DEVICES = ["mobile", "desktop", "tablet"]
FILTERS = ["price_desc", "price_asc", "newest", "rating_4_plus", "none"]
PAYMENT_METHODS = ["credit_card", "paypal", "apple_pay"]

# helpers
def get_random_timestamp():
    end = datetime.utcnow()
    start = end - timedelta(days=30)
    random_date = start + (end - start) * random.random()
    return random_date.strftime("%Y-%m-%dT%H:%M:%SZ")

# product context
def get_random_product_context():
    cat = random.choice(list(CATEGORY_MAP.keys()))
    subcat = random.choice(list(CATEGORY_MAP[cat].keys()))
    price_range = CATEGORY_MAP[cat][subcat]
    price = round(random.uniform(price_range[0], price_range[1]), 2)
    return cat, subcat, price

# event detail generators
def get_view_product_details():
    cat, subcat, price = get_random_product_context()
    return {
        "product_id": f"prod_{random.randint(1, NUM_PRODUCTS)}",
        "category": cat,
        "subcategory": subcat,
        "price_at_view": price,
        "time_spent_seconds": random.randint(5, 300),
        "device": random.choice(DEVICES)
    }

# search details
def get_search_details():
    return {
        "query": random.choice(SEARCH_TERMS),
        "filters_applied": random.sample(FILTERS, k=random.randint(0, 2)),
        "results_count": random.randint(0, 150)
    }

# add to cart details
def get_add_to_cart_details():
    cat, subcat, price = get_random_product_context()
    return {
        "product_id": f"prod_{random.randint(1, NUM_PRODUCTS)}",
        "category": cat,
        "quantity": random.randint(1, 3),
        "price_unit": price,
        "currency": "USD"
    }

# remove from cart details
def get_remove_from_cart_details():
    return {
        "product_id": f"prod_{random.randint(1, NUM_PRODUCTS)}",
        "quantity_removed": 1
    }

# simulate a cart
def get_check_cart_status_details():
    num_items = random.randint(1, 5)
    total_val = 0
    for _ in range(num_items):
        _, _, price = get_random_product_context()
        total_val += price
        
    return {
        "total_items": num_items,
        "cart_value": round(total_val, 2),
        "currency": "USD"
    }

# click product
def get_click_product_details():
    return {
        "product_id": f"prod_{random.randint(1, NUM_PRODUCTS)}",
        "position_in_list": random.randint(1, 20),
        "source_page": random.choice(["search_results", "category_page", "recommendations"])
    }

# purchase completed
def get_purchase_completed_details():
    num_items = random.randint(1, 6)
    total_val = 0
    for _ in range(num_items):
        _, _, price = get_random_product_context()
        total_val += price

    return {
        "order_id": f"ord_{random.randint(10000, 99999)}",
        "total_amount": round(total_val, 2),
        "payment_method": random.choice(PAYMENT_METHODS),
        "items_count": num_items
    }

# main logic
EVENT_TYPES = {
    "view_product": get_view_product_details,
    "search": get_search_details,
    "add_to_cart": get_add_to_cart_details,
    "remove_from_cart": get_remove_from_cart_details,
    "check_cart_status": get_check_cart_status_details,
    "click_product": get_click_product_details,
    "purchase_completed": get_purchase_completed_details
}

# weights
EVENT_WEIGHTS = [0.45, 0.15, 0.10, 0.05, 0.10, 0.10, 0.05]

def generate_log():
    event_type = random.choices(list(EVENT_TYPES.keys()), weights=EVENT_WEIGHTS, k=1)[0]
    log_entry = {
        "_id": f"evt_{uuid.uuid4().hex}",
        "user_id": random.randint(1, 1000), 
        "session_id": f"sess_{uuid.uuid4().hex[:8]}",
        "timestamp": get_random_timestamp(),
        "event_type": event_type,
        "details": EVENT_TYPES[event_type]()
    }
    return log_entry

print(f"generating {NUM_LOGS} aligned user behavior logs.")

# writing to file
with open(OUTPUT_FILE, "w") as f:
    f.write("[")
    for i in range(NUM_LOGS):
        log = generate_log()
        json.dump(log, f)
        if i < NUM_LOGS - 1:
            f.write(",\n")
    f.write("]")
print(f"logs saved to '{OUTPUT_FILE}'")