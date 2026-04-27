# init_db.py
import sqlite3

connection = sqlite3.connect('database.db')

with open('schema.sql') as f:
    connection.executescript(f.read())

cur = connection.cursor()

cur.execute("INSERT INTO users (username, password, is_admin, is_seller) VALUES ('admin', 'password', 1, 1)")
cur.execute("INSERT INTO users (username, password, is_admin, is_seller) VALUES ('alice', 'password1', 0, 1)")
cur.execute("INSERT INTO users (username, password, is_admin, is_seller) VALUES ('bob', 'letmein', 0, 0)")

cur.execute("INSERT INTO products (name, price, description, seller_name) VALUES ('Classic T-Shirt', 15.99, 'A comfortable, 100% cotton t-shirt.', 'alice')")
cur.execute("INSERT INTO products (name, price, description, seller_name) VALUES ('Stylish Mug', 9.99, 'A ceramic mug, perfect for your morning coffee.', 'alice')")
cur.execute("INSERT INTO products (name, price, description, seller_name) VALUES ('Laptop Stand', 34.99, 'Adjustable aluminium stand for any laptop.', 'admin')")

connection.commit()
connection.close()

print("Vulnerable database initialised with sample data.")
