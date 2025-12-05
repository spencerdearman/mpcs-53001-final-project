#!/bin/bash
# exit if a command exits with non-zero status
set -e

# environment setup
echo "-- setting up the environment --"

# clean and rebuild the docker containers
echo "-- cleaning and building docker containers --"
docker compose down -v
docker compose up -d --build

# create a new virtual environment if it doesn't exist
echo "-- creating a new virtual environment --"
if [ ! -d "env" ]; then
    python3 -m venv env
fi
source env/bin/activate

# install requirements
echo "-- installing requirements --"
pip install -r requirements.txt

# generate and organize json data
echo "-- generating json data --"
echo "generating products..."
python3 data/products/generate_products.py
echo "generating logs..."
python3 data/logs/generate_user_logs.py
# move products.json
if [ -f "products.json" ]; then
    mv products.json data/products/products.json
fi

# move user_behavior_logs.json
if [ -f "user_behavior_logs.json" ]; then
    mv user_behavior_logs.json data/logs/user_behavior_logs.json
fi

# initialize databases
echo "-- initializing databases --"
echo "-- loading data into mongo --"
python3 database/mongo/initialize_mongo.py
echo "-- loading postgres schema --"
cat database/postgres/schema.sql | docker compose exec -T postgres psql -U admin -d ecommerce_db
echo "-- generating users (sql insert) --"
python3 data/users/generate_users.py
echo "-- generating orders (sql insert) --"
python3 data/orders/generate_orders.py

# initialize graph
echo "-- initializing neo4j graph --"
python3 database/neo4j/initialize_neo4j.py

# initialize redis
echo "-- initializing redis sessions --"
python3 data/sessions/generate_sessions.py

echo "-- environment setup complete --"