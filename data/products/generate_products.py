# base generated from Gemini: https://gemini.google.com/share/a064707c28b6
import json
import random
import datetime

# configuration
NUM_PRODUCTS = 10000
OUTPUT_FILE = "products.json"

# data pools
ADJECTIVES = [
    "Premium", "Sleek", "Durable", "Vintage", "Modern", "Eco-friendly", 
    "Compact", "Luxury", "Essential", "Pro", "Minimalist", "Industrial", 
    "Handcrafted", "Smart", "Ultra-light", "Heavy-duty", "Artisan", "Urban",
    "Retro", "Futuristic", "Nordic", "Organic", "Ergonomic"
]

# structure: category -> { subcategory: (min_price, max_price) }
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

# helper functions
def get_random_date():
    start_date = datetime.date(2023, 1, 1)
    end_date = datetime.date(2025, 12, 31)
    time_between = end_date - start_date
    days_between = time_between.days
    random_number_of_days = random.randrange(days_between)
    return (start_date + datetime.timedelta(days=random_number_of_days)).isoformat()

def generate_attributes(category, subcat):
    attr = {}
    
    if category == "Electronics":
        attr["warranty"] = random.choice(["1 Year", "2 Years", "Lifetime"])
        attr["power_rating"] = f"{random.randint(5, 100)}W"
        if subcat in ["Laptop", "Smartphone"]:
            attr["storage"] = random.choice(["128GB", "256GB", "512GB", "1TB"])
            attr["ram"] = random.choice(["8GB", "16GB", "32GB"])
            attr["screen_size"] = f"{random.randint(6, 16)} inches"
        elif subcat == "Headphones":
            attr["connectivity"] = "Bluetooth 5.3"
            attr["noise_cancellation"] = random.choice([True, False])
            attr["battery_life"] = f"{random.randint(10, 40)} hours"
            
    elif category == "Fashion":
        attr["material"] = random.choice(["Cotton", "Leather", "Polyester", "Denim", "Wool"])
        attr["style"] = random.choice(["Casual", "Formal", "Streetwear", "Athleisure"])
        attr["gender"] = random.choice(["Unisex", "Men", "Women"])
        
    elif category == "Home & Kitchen":
        attr["material"] = random.choice(["Wood", "Stainless Steel", "Ceramic", "Glass"])
        attr["dimensions"] = {
            "height": f"{random.randint(5, 80)} cm",
            "width": f"{random.randint(5, 80)} cm",
            "depth": f"{random.randint(5, 80)} cm"
        }
        attr["weight"] = f"{round(random.uniform(0.5, 20.0), 1)} kg"
        
    elif category == "Beauty":
        attr["volume"] = f"{random.choice([30, 50, 100, 250])} ml"
        attr["skin_type"] = random.choice(["All", "Oily", "Dry", "Sensitive"])
        attr["organic"] = random.choice([True, False])
        attr["cruelty_free"] = True
        
    elif category == "Books":
        attr["author"] = f"Author {random.choice(['A', 'B', 'C', 'D'])}{random.randint(1,100)}"
        attr["pages"] = random.randint(150, 900)
        attr["isbn"] = f"978-{random.randint(100000000, 999999999)}"
        attr["publisher"] = random.choice(["Penguin", "HarperCollins", "O'Reilly", "Random House"])

    return attr

# generate variants
def generate_variants(category, subcat, product_id):
    if category == "Fashion" or subcat in ["Rug", "Sofa"]:
        variants = []
        sizes = ["S", "M", "L", "XL"] if category == "Fashion" else ["Standard", "Large"]
        colors = ["Black", "White", "Navy", "Red", "Grey", "Beige"]
        
        # Create 3-5 variants per product
        for _ in range(random.randint(3, 5)):
            size = random.choice(sizes)
            color = random.choice(colors)
            variants.append({
                "sku": f"{product_id}-{size}-{color[:3].upper()}",
                "size": size,
                "color": color,
                "stock_level": random.randint(0, 50)
            })
        return variants
    return None

# main generator
products = []

for i in range(1, NUM_PRODUCTS + 1):
    cat = random.choice(list(CATEGORY_MAP.keys()))
    subcat = random.choice(list(CATEGORY_MAP[cat].keys()))
    
    # determine price
    price_range = CATEGORY_MAP[cat][subcat]
    price = round(random.uniform(price_range[0], price_range[1]), 2)
    
    # generate basic info
    adj = random.choice(ADJECTIVES)
    prod_id = f"prod_{i}"
    name = f"{adj} {subcat} {random.randint(100, 999)}"
    
    product = {
        "_id": prod_id,
        "name": name,
        "category": cat,
        "subcategory": subcat,
        "price": price,
        "description": f"Experience the {adj.lower()} quality of our {name}. Perfect for modern living.",
        "images": [f"{name.lower().replace(' ', '-')}_main.jpg", f"{name.lower().replace(' ', '-')}_side.jpg"],
        "rating": round(random.uniform(3.5, 5.0), 1),
        "review_count": random.randint(0, 500),
        "tags": [cat.lower(), subcat.lower(), adj.lower()],
        "release_date": get_random_date(),
        "attributes": generate_attributes(cat, subcat)
    }
    
    # handle variants vs simple stock
    variants = generate_variants(cat, subcat, prod_id)
    if variants:
        product["variants"] = variants
    else:
        product["stock_level"] = random.randint(0, 300)

    products.append(product)

# writing to json
with open(OUTPUT_FILE, 'w') as f:
    json.dump(products, f, indent=2)
print(f"generated {NUM_PRODUCTS} products in '{OUTPUT_FILE}'")