#!/usr/bin/env python3
"""
PostgreSQL database setup script for long-running query demo.
Creates tables with large datasets for realistic slow queries.
"""

import psycopg2
from psycopg2 import sql
import os
from datetime import datetime

# Database connection parameters
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'longquery_demo'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres'),
    'port': int(os.getenv('DB_PORT', '5432'))
}

def create_database():
    """Create the database if it doesn't exist."""
    try:
        # Connect to default postgres database to create our database
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            database='postgres',
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port']
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_CONFIG['database'],))
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(
                sql.Identifier(DB_CONFIG['database'])
            ))
            print(f"Created database: {DB_CONFIG['database']}")
        else:
            print(f"Database {DB_CONFIG['database']} already exists")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error creating database: {e}")
        return False
    
    return True

def setup_tables():
    """Create tables and populate with sample data."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("Creating tables...")
        
        # Drop existing tables if they exist
        cursor.execute("DROP TABLE IF EXISTS orders CASCADE")
        cursor.execute("DROP TABLE IF EXISTS customers CASCADE")
        cursor.execute("DROP TABLE IF EXISTS products CASCADE")
        
        # Create customers table
        cursor.execute("""
            CREATE TABLE customers (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                email VARCHAR(100),
                city VARCHAR(50),
                country VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create products table
        cursor.execute("""
            CREATE TABLE products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                category VARCHAR(50),
                price DECIMAL(10,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create orders table
        cursor.execute("""
            CREATE TABLE orders (
                id SERIAL PRIMARY KEY,
                customer_id INT REFERENCES customers(id),
                product_id INT REFERENCES products(id),
                order_date DATE,
                amount DECIMAL(10,2),
                status VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        print("Tables created successfully")
        
        # Populate customers (100,000 records)
        print("Populating customers table...")
        cursor.execute("""
            INSERT INTO customers (name, email, city, country)
            SELECT 
                'Customer ' || i,
                'customer' || i || '@email.com',
                'City ' || (i % 100),
                'Country ' || (i % 20)
            FROM generate_series(1, 100000) i
        """)
        print("Customers table populated (100,000 records)")
        
        # Populate products (10,000 records)
        print("Populating products table...")
        cursor.execute("""
            INSERT INTO products (name, category, price)
            SELECT 
                'Product ' || i,
                'Category ' || (i % 50),
                (random() * 1000)::decimal(10,2)
            FROM generate_series(1, 10000) i
        """)
        print("Products table populated (10,000 records)")
        
        # Populate orders (1,000,000 records)
        print("Populating orders table (this may take a few minutes)...")
        cursor.execute("""
            INSERT INTO orders (customer_id, product_id, order_date, amount, status)
            SELECT 
                ((random() * 99999)::int + 1),
                ((random() * 9999)::int + 1),
                '2020-01-01'::date + (random() * 1460)::int,
                (random() * 1000)::decimal(10,2),
                CASE (random() * 3)::int 
                    WHEN 0 THEN 'pending'
                    WHEN 1 THEN 'completed'
                    ELSE 'cancelled'
                END
            FROM generate_series(1, 1000000)
        """)
        print("Orders table populated (1,000,000 records)")
        
        # Intentionally do NOT create indexes to keep queries slow
        print("Skipping index creation to ensure slow queries...")
        
        # Commit all changes
        conn.commit()
        cursor.close()
        conn.close()
        
        print("Database setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error setting up tables: {e}")
        return False

def get_sample_slow_queries():
    """Return a list of predefined slow queries for testing."""
    return [
        {
            "name": "Complex Aggregation by Country",
            "description": "Heavy aggregation across orders and customers (2-5 minutes)",
            "query": """
                SELECT 
                    c.country, 
                    COUNT(*) as total_orders,
                    AVG(o.amount) as avg_amount,
                    SUM(o.amount) as total_revenue,
                    COUNT(DISTINCT c.id) as unique_customers
                FROM orders o 
                JOIN customers c ON o.customer_id = c.id 
                WHERE o.order_date >= '2023-01-01'
                GROUP BY c.country 
                HAVING COUNT(*) > 1000
                ORDER BY total_revenue DESC;
            """
        },
        {
            "name": "Cartesian Product Analysis",
            "description": "Heavy cross join without proper indexing (5-15 minutes)",
            "query": """
                SELECT DISTINCT 
                    o1.customer_id, 
                    o1.amount, 
                    o2.amount,
                    ABS(o1.amount - o2.amount) as amount_diff
                FROM orders o1 
                CROSS JOIN orders o2 
                WHERE o1.amount > o2.amount 
                    AND o1.customer_id != o2.customer_id
                    AND ABS(o1.amount - o2.amount) < 10
                LIMIT 10000;
            """
        },
        {
            "name": "Recursive Fibonacci Calculation",
            "description": "CPU-intensive recursive calculation (3-10 minutes)",
            "query": """
                WITH RECURSIVE fibonacci(n, fib_n, fib_n1) AS (
                    SELECT 1, 0::bigint, 1::bigint
                    UNION ALL
                    SELECT n+1, fib_n1, fib_n + fib_n1 
                    FROM fibonacci 
                    WHERE n < 50000
                )
                SELECT MAX(n) as max_n, MAX(fib_n) as max_fibonacci 
                FROM fibonacci;
            """
        },
        {
            "name": "Complex Multi-table Join",
            "description": "Multi-way join with string operations (3-8 minutes)",
            "query": """
                SELECT 
                    c.country,
                    p.category,
                    COUNT(*) as order_count,
                    STRING_AGG(DISTINCT c.city, ', ') as cities,
                    AVG(o.amount * p.price) as avg_total_value
                FROM orders o
                JOIN customers c ON o.customer_id = c.id
                JOIN products p ON o.product_id = p.id
                WHERE o.order_date BETWEEN '2022-01-01' AND '2023-12-31'
                    AND c.country LIKE '%Country%'
                    AND p.price > 100
                GROUP BY c.country, p.category
                HAVING COUNT(*) > 100
                ORDER BY avg_total_value DESC, order_count DESC;
            """
        }
    ]

if __name__ == "__main__":
    print("Setting up PostgreSQL database for long-running query demo...")
    print(f"Target database: {DB_CONFIG['database']}")
    print("=" * 50)
    
    if create_database():
        if setup_tables():
            print("\n" + "=" * 50)
            print("Setup completed successfully!")
            print("\nSample slow queries available:")
            for i, query in enumerate(get_sample_slow_queries(), 1):
                print(f"{i}. {query['name']}: {query['description']}")
        else:
            print("Failed to set up tables")
    else:
        print("Failed to create database")