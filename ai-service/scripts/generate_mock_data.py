import pandas as pd
import random
import psycopg2
import pymysql
from faker import Faker
from datetime import datetime

fake = Faker()
Faker.seed(42)
random.seed(42)

NUM_INTERACTIONS = 1000

EVENT_TYPES = [
    'VIEW', 'ADD_TO_CART', 'PURCHASE', 'SEARCH', 
    'CLICK_RELATED', 'WISHLIST', 'SHARE', 'REVIEW', 
    'RETURN', 'CHECKOUT_START'
]

# Database Configurations
PRODUCT_DB = {
    'dbname': 'product_db',
    'user': 'shop_user',
    'password': 'shop_password',
    'host': 'localhost',
    'port': '5434'
}

# MySQL uses different param names for pymysql
CUSTOMER_DB = {
    'db': 'customer_db',
    'user': 'shop_user',
    'password': 'shop_password',
    'host': 'localhost',
    'port': 3307
}

def get_product_slugs():
    try:
        conn = psycopg2.connect(**PRODUCT_DB)
        query = "SELECT slug FROM products"
        df = pd.read_sql(query, conn)
        conn.close()
        return df['slug'].tolist()
    except Exception as e:
        print(f"Error fetching product slugs: {e}")
        return []

def get_usernames():
    try:
        conn = pymysql.connect(**CUSTOMER_DB)
        query = "SELECT username FROM accounts_customuser"
        df = pd.read_sql(query, conn)
        conn.close()
        return df['username'].tolist()
    except Exception as e:
        print(f"Error fetching usernames: {e}")
        return []

def main():
    print("Fetching real data from databases...")
    products = get_product_slugs()
    users = get_usernames()

    if not products:
        print("Warning: No products found, using fallback.")
        products = ["macbook-pro-14-m3", "iphone-15-pro-max", "samsung-galaxy-s24-ultra"]
    
    if not users:
        print("Warning: No users found, using fallback.")
        users = [f"customer{i}" for i in range(1, 11)]

    print(f"Generating {NUM_INTERACTIONS} mock interactions...")
    interactions = []
    for _ in range(NUM_INTERACTIONS):
        user = random.choice(users)
        product = random.choice(products)
        event = random.choice(EVENT_TYPES)
        # Random timestamp in the last 30 days
        timestamp = fake.date_time_between(start_date='-30d', end_date='now')
        
        query = fake.word() if event == 'SEARCH' else ''
        
        interactions.append({
            'user_id': user,
            'product_id': product,
            'event_type': event,
            'timestamp': timestamp,
            'query': query
        })

    df = pd.DataFrame(interactions)
    df = df.sort_values(by='timestamp')
    output_file = 'interactions.csv'
    df.to_csv(output_file, index=False)
    print(f"[{len(df)}] records saved to {output_file}.")

if __name__ == '__main__':
    main()
